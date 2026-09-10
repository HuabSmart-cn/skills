"""
Helper for running LibreOffice (soffice) in environments where AF_UNIX
sockets may be blocked (e.g., sandboxed VMs). Detects the restriction at
runtime, but compiles and applies the LD_PRELOAD shim only after explicit
SHEETAGENT_ENABLE_LO_SOCKET_SHIM opt-in.

Usage:
    from office.soffice import run_soffice, get_soffice_env

    # Option 1 – run soffice directly
    result = run_soffice(["--headless", "--convert-to", "pdf", "input.docx"])

    # Option 2 – get env dict for your own subprocess calls
    env = get_soffice_env()
    subprocess.run(["soffice", ...], env=env)
"""

import contextlib
import os
import platform
import shutil
import socket
import stat
import subprocess
import tempfile
import threading
from collections.abc import Iterable
from pathlib import Path


SOFFICE_NOT_FOUND = (
    "LibreOffice executable not found in PATH or common installation locations"
)
SOCKET_SHIM_OPT_IN_ENV = "SHEETAGENT_ENABLE_LO_SOCKET_SHIM"


def _common_soffice_paths(system=None) -> list[Path]:
    """返回平台常见的 LibreOffice 可执行文件位置。"""
    system = system or platform.system()
    if system == "Darwin":
        return [
            Path("/Applications/LibreOffice.app/Contents/MacOS/soffice"),
            Path.home() / "Applications/LibreOffice.app/Contents/MacOS/soffice",
        ]
    if system == "Windows":
        install_roots = [
            Path(root) / "LibreOffice/program/soffice.exe"
            for root in (
                os.environ.get("ProgramFiles"),
                os.environ.get("ProgramFiles(x86)"),
            )
            if root
        ]
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            install_roots.append(
                Path(local_app_data) / "Programs/LibreOffice/program/soffice.exe"
            )
        return install_roots
    return [
        Path("/usr/bin/soffice"),
        Path("/usr/local/bin/soffice"),
        Path("/snap/bin/libreoffice"),
    ]


def find_soffice():
    """从 PATH 和各平台常见安装目录解析 LibreOffice 可执行文件。"""
    for command in ("soffice", "soffice.exe", "libreoffice"):
        resolved = shutil.which(command)
        if resolved:
            return resolved
    for candidate in _common_soffice_paths():
        if candidate.is_file():
            return str(candidate)
    return None


def _socket_shim_enabled() -> bool:
    return os.environ.get(SOCKET_SHIM_OPT_IN_ENV, "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def get_soffice_env() -> dict:
    env = os.environ.copy()
    env["SAL_USE_VCLPLUGIN"] = "svp"

    if platform.system() == "Linux" and _needs_shim():
        if not _socket_shim_enabled():
            raise RuntimeError(
                "AF_UNIX sockets are unavailable; LibreOffice socket shim is disabled. "
                f"Set {SOCKET_SHIM_OPT_IN_ENV}=1 only after explicit user or platform "
                "authorization to compile and LD_PRELOAD the native shim."
            )
        shim = _ensure_shim()
        env["LD_PRELOAD"] = str(shim)

    return env


def run_soffice(args: Iterable[str], **kwargs) -> subprocess.CompletedProcess:
    args = list(args)
    executable = find_soffice()
    if executable is None:
        raise FileNotFoundError(SOFFICE_NOT_FOUND)
    with contextlib.ExitStack() as stack:
        if not any(str(a).startswith("-env:UserInstallation") for a in args):
            profile = stack.enter_context(
                tempfile.TemporaryDirectory(prefix="sheetagent-lo-profile-")
            )
            args = [f"-env:UserInstallation={Path(profile).as_uri()}"] + args
        return subprocess.run([executable] + args, env=get_soffice_env(), **kwargs)

_SHIM_WORKDIR = None
_SHIM_LOCK = threading.Lock()


def _needs_shim() -> bool:
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.close()
        return False
    except OSError:
        return True


def _ensure_shim() -> Path:
    global _SHIM_WORKDIR

    with _SHIM_LOCK:
        if _SHIM_WORKDIR is not None:
            return Path(_SHIM_WORKDIR.name) / "lo_socket_shim.so"

        gcc = shutil.which("gcc")
        if gcc is None:
            raise RuntimeError(
                "gcc not found; install gcc to build the explicitly enabled LibreOffice "
                f"socket shim, or unset {SOCKET_SHIM_OPT_IN_ENV} to keep it disabled"
            )

        workdir = tempfile.TemporaryDirectory(prefix="sheetagent-lo-shim-")
        workdir_path = Path(workdir.name)
        os.chmod(workdir_path, 0o700)
        src = workdir_path / "lo_socket_shim.c"
        shim = workdir_path / "lo_socket_shim.so"

        try:
            src.write_text(_SHIM_SOURCE, encoding="utf-8")
            subprocess.run(
                [gcc, "-shared", "-fPIC", "-o", str(shim), str(src), "-ldl"],
                check=True,
                capture_output=True,
            )
            shim_stat = shim.stat()
            if not stat.S_ISREG(shim_stat.st_mode) or shim_stat.st_uid != os.getuid():
                raise OSError("compiled LibreOffice socket shim failed validation")
            os.chmod(shim, 0o700)
        except Exception:
            workdir.cleanup()
            raise

        _SHIM_WORKDIR = workdir
        return shim



_SHIM_SOURCE = r"""
#define _GNU_SOURCE
#include <dlfcn.h>
#include <errno.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/socket.h>
#include <unistd.h>

static int (*real_socket)(int, int, int);
static int (*real_socketpair)(int, int, int, int[2]);
static int (*real_listen)(int, int);
static int (*real_accept)(int, struct sockaddr *, socklen_t *);
static int (*real_close)(int);
static int (*real_read)(int, void *, size_t);

/* Per-FD bookkeeping (FDs >= 1024 are passed through unshimmed). */
static int is_shimmed[1024];
static int peer_of[1024];
static int wake_r[1024];            /* accept() blocks reading this */
static int wake_w[1024];            /* close()  writes to this      */
static int listener_fd = -1;        /* FD that received listen()    */

__attribute__((constructor))
static void init(void) {
    real_socket     = dlsym(RTLD_NEXT, "socket");
    real_socketpair = dlsym(RTLD_NEXT, "socketpair");
    real_listen     = dlsym(RTLD_NEXT, "listen");
    real_accept     = dlsym(RTLD_NEXT, "accept");
    real_close      = dlsym(RTLD_NEXT, "close");
    real_read       = dlsym(RTLD_NEXT, "read");
    for (int i = 0; i < 1024; i++) {
        peer_of[i] = -1;
        wake_r[i]  = -1;
        wake_w[i]  = -1;
    }
}

/* ---- socket ---------------------------------------------------------- */
int socket(int domain, int type, int protocol) {
    if (domain == AF_UNIX) {
        int fd = real_socket(domain, type, protocol);
        if (fd >= 0) return fd;
        /* socket(AF_UNIX) blocked – fall back to socketpair(). */
        int sv[2];
        if (real_socketpair(domain, type, protocol, sv) == 0) {
            if (sv[0] >= 0 && sv[0] < 1024) {
                is_shimmed[sv[0]] = 1;
                peer_of[sv[0]]    = sv[1];
                int wp[2];
                if (pipe(wp) == 0) {
                    wake_r[sv[0]] = wp[0];
                    wake_w[sv[0]] = wp[1];
                }
            }
            return sv[0];
        }
        errno = EPERM;
        return -1;
    }
    return real_socket(domain, type, protocol);
}

/* ---- listen ---------------------------------------------------------- */
int listen(int sockfd, int backlog) {
    if (sockfd >= 0 && sockfd < 1024 && is_shimmed[sockfd]) {
        listener_fd = sockfd;
        return 0;
    }
    return real_listen(sockfd, backlog);
}

/* ---- accept ---------------------------------------------------------- */
int accept(int sockfd, struct sockaddr *addr, socklen_t *addrlen) {
    if (sockfd >= 0 && sockfd < 1024 && is_shimmed[sockfd]) {
        /* Block until close() writes to the wake pipe. */
        if (wake_r[sockfd] >= 0) {
            char buf;
            real_read(wake_r[sockfd], &buf, 1);
        }
        errno = ECONNABORTED;
        return -1;
    }
    return real_accept(sockfd, addr, addrlen);
}

/* ---- close ----------------------------------------------------------- */
int close(int fd) {
    if (fd >= 0 && fd < 1024 && is_shimmed[fd]) {
        int was_listener = (fd == listener_fd);
        is_shimmed[fd] = 0;

        if (wake_w[fd] >= 0) {              /* unblock accept() */
            char c = 0;
            write(wake_w[fd], &c, 1);
            real_close(wake_w[fd]);
            wake_w[fd] = -1;
        }
        if (wake_r[fd] >= 0) { real_close(wake_r[fd]); wake_r[fd]  = -1; }
        if (peer_of[fd] >= 0) { real_close(peer_of[fd]); peer_of[fd] = -1; }

        if (was_listener)
            _exit(0);                        /* conversion done – exit */
    }
    return real_close(fd);
}
"""



if __name__ == "__main__":
    import sys
    result = run_soffice(sys.argv[1:])
    sys.exit(result.returncode)
