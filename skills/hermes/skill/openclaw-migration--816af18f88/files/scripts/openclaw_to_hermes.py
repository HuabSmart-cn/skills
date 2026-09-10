#!/usr/bin/env python3
"""OpenClaw -> Hermes migration helper.

This script migrates the parts of an OpenClaw user footprint that map cleanly
into Hermes Agent, archives selected unmapped docs for manual review, and
reports exactly what was skipped and why.
"""

from __future__ import annotations

import argparse
import errno
import hashlib
import json
import os
import re
import shutil
import tempfile
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

try:
    import yaml
except Exception:  # pragma: no cover - handled at runtime
    yaml = None


ENTRY_DELIMITER = "\n§\n"
DEFAULT_MEMORY_CHAR_LIMIT = 2200
DEFAULT_USER_CHAR_LIMIT = 1375
SKILL_CATEGORY_DIRNAME = "openclaw-imports"
SKILL_CATEGORY_DESCRIPTION = (
    "Skills migrated from an OpenClaw workspace."
)
SKILL_CONFLICT_MODES = {"skip", "overwrite", "rename"}
SUPPORTED_SECRET_TARGETS=***REDACTED***
    "TELEGRAM_BOT_TOKEN",
    "OPENROUTER_API_KEY",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "ELEVENLABS_API_KEY",
    "VOICE_TOOLS_OPENAI_KEY",
}
WORKSPACE_INSTRUCTIONS_FILENAME = "AGENTS" + ".md"
MIGRATION_OPTION_METADATA: Dict[str, Dict[str, str]] = {
    "soul": {
        "label": "SOUL.md",
        "description": "Import the OpenClaw persona file into Hermes.",
    },
    "workspace-agents": {
        "label": "Workspace instructions",
        "description": "Copy the OpenClaw workspace instructions file into a chosen workspace.",
    },
    "memory": {
        "label": "MEMORY.md",
        "description": "Import long-term memory entries into Hermes memories.",
    },
    "user-profile": {
        "label": "USER.md",
        "description": "Import user profile entries into Hermes memories.",
    },
    "messaging-settings": {
        "label": "Messaging settings",
        "description": "Import Hermes-compatible messaging settings such as allowlists and working directory.",
    },
    "secret-settings": ***REDACTED***
        "label": "Allowlisted secrets",
        "description": "Import the small allowlist of Hermes-compatible secrets when explicitly enabled.",
    },
    "command-allowlist": {
        "label": "Command allowlist",
        "description": "Merge OpenClaw exec approval patterns into Hermes command_allowlist.",
    },
    "skills": {
        "label": "User skills",
        "description": "Copy OpenClaw skills into ~/.hermes/skills/openclaw-imports/.",
    },
    "tts-assets": {
        "label": "TTS assets",
        "description": "Copy compatible workspace TTS assets into ~/.hermes/tts/.",
    },
    "discord-settings": {
        "label": "Discord settings",
        "description": "Import Discord bot token and allowlist into Hermes .env.",
    },
    "slack-settings": {
        "label": "Slack settings",
        "description": "Import Slack bot/app tokens and allowlist into Hermes .env.",
    },
    "whatsapp-settings": {
        "label": "WhatsApp settings",
        "description": "Import WhatsApp allowlist into Hermes .env.",
    },
    "signal-settings": {
        "label": "Signal settings",
        "description": "Import Signal account, HTTP URL, and allowlist into Hermes .env.",
    },
    "provider-keys": {
        "label": "Provider API keys",
        "description": "Import model provider API keys into Hermes .env (requires --migrate-secrets).",
    },
    "model-config": {
        "label": "Default model",
        "description": "Import the default model setting into Hermes config.yaml.",
    },
    "tts-config": {
        "label": "TTS configuration",
        "description": "Import TTS provider and voice settings into Hermes config.yaml.",
    },
    "shared-skills": {
        "label": "Shared skills",
        "description": "Copy shared OpenClaw skills from ~/.openclaw/skills/ into Hermes.",
    },
    "daily-memory": {
        "label": "Daily memory files",
        "description": "Merge daily memory entries from workspace/memory/ into Hermes MEMORY.md.",
    },
    "archive": {
        "label": "Archive unmapped docs",
        "description": "Archive compatible-but-unmapped docs for later manual review.",
    },
    "mcp-servers": {
        "label": "MCP servers",
        "description": "Import MCP server definitions from OpenClaw into Hermes config.yaml.",
    },
    "plugins-config": {
        "label": "Plugins configuration",
        "description": "Archive OpenClaw plugin configuration and installed extensions for manual review.",
    },
    "cron-jobs": {
        "label": "Cron / scheduled tasks",
        "description": "Import cron job definitions. Archive for manual recreation via 'hermes cron'.",
    },
    "hooks-config": {
        "label": "Hooks and webhooks",
        "description": "Archive OpenClaw hook configuration (internal hooks, webhooks, Gmail integration).",
    },
    "agent-config": {
        "label": "Agent defaults and multi-agent setup",
        "description": "Import agent defaults (compaction, context, thinking) into Hermes config. Archive multi-agent list.",
    },
    "gateway-config": {
        "label": "Gateway configuration",
        "description": "Import gateway port and auth settings. Archive full gateway config for manual setup.",
    },
    "session-config": {
        "label": "Session configuration",
        "description": "Archive advanced session settings; automatic reset timers are not imported.",
    },
    "full-providers": {
        "label": "Full model provider definitions",
        "description": "Import custom model providers (baseUrl, apiType, headers) into Hermes custom_providers.",
    },
    "deep-channels": {
        "label": "Deep channel configuration",
        "description": "Import extended channel settings (Matrix, Mattermost, IRC, group configs). Archive complex settings.",
    },
    "browser-config": {
        "label": "Browser configuration",
        "description": "Import browser automation settings into Hermes config.yaml.",
    },
    "tools-config": {
        "label": "Tools configuration",
        "description": "Import tool settings (exec timeout, sandbox, web search) into Hermes config.yaml.",
    },
    "approvals-config": {
        "label": "Approval rules",
        "description": "Import approval mode and rules into Hermes config.yaml approvals section.",
    },
    "memory-backend": {
        "label": "Memory backend configuration",
        "description": "Archive OpenClaw memory backend settings (QMD, vector search, citations) for manual review.",
    },
    "skills-config": {
        "label": "Skills registry configuration",
        "description": "Archive per-skill enabled/config/env settings from OpenClaw skills.entries.",
    },
    "ui-identity": {
        "label": "UI and identity settings",
        "description": "Archive OpenClaw UI theme, assistant identity, and display preferences.",
    },
    "logging-config": {
        "label": "Logging and diagnostics",
        "description": "Archive OpenClaw logging and diagnostics configuration.",
    },
}
MIGRATION_PRESETS: Dict[str, set[str]] = {
    "user-data": {
        "soul",
        "workspace-agents",
        "memory",
        "user-profile",
        "messaging-settings",
        "command-allowlist",
        "skills",
        "tts-assets",
        "discord-settings",
        "slack-settings",
        "whatsapp-settings",
        "signal-settings",
        "model-config",
        "tts-config",
        "shared-skills",
        "daily-memory",
        "archive",
        "mcp-servers",
        "agent-config",
        "session-config",
        "browser-config",
        "tools-config",
        "approvals-config",
        "deep-channels",
        "full-providers",
        "plugins-config",
        "cron-jobs",
        "hooks-config",
        "memory-backend",
        "skills-config",
        "ui-identity",
        "logging-config",
        "gateway-config",
    },
    "full": set(MIGRATION_OPTION_METADATA),
}


# ───────────────────────────────────────────────────────────────────────
# Item shape constants — kept stable for downstream consumers of report.json.
# Inspired by OpenClaw's src/plugin-sdk/migration.ts so both sides speak the
# same vocabulary.  Values intentionally match the strings already produced
# by this script (migrated/archived/skipped/conflict/error) so the addition
# is backward-compatible.
# ───────────────────────────────────────────────────────────────────────
STATUS_MIGRATED = "migrated"
STATUS_ARCHIVED = "archived"
STATUS_SKIPPED = "skipped"
STATUS_CONFLICT = "conflict"
STATUS_ERROR = "error"
STATUS_PLANNED = "planned"

REASON_TARGET_EXISTS = "Target exists and overwrite is disabled"
REASON_BLOCKED_BY_APPLY_CONFLICT = "blocked by earlier apply conflict"


@dataclass
class ItemResult:
    kind: str
    source: Optional[str]
    destination: Optional[str]
    status: str
    reason: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    sensitive: bool = False


def parse_selection_values(values: Optional[Sequence[str]]) -> List[str]:
    parsed: List[str] = []
    for value in values or ():
        for part in str(value).split(","):
            part = part.strip().lower()
            if part:
                parsed.append(part)
    return parsed


def resolve_selected_options(
    include: Optional[Sequence[str]] = None,
    exclude: Optional[Sequence[str]] = None,
    preset: Optional[str] = None,
) -> set[str]:
    include_values = parse_selection_values(include)
    exclude_values = parse_selection_values(exclude)
    valid = set(MIGRATION_OPTION_METADATA)
    preset_name = (preset or "").strip().lower()

    if preset_name and preset_name not in MIGRATION_PRESETS:
        raise ValueError(
            "Unknown migration preset: "
            + preset_name
            + ". Valid presets: "
            + ", ".join(sorted(MIGRATION_PRESETS))
        )

    unknown = (set(include_values) - {"all"} - valid) | (set(exclude_values) - {"all"} - valid)
    if unknown:
        raise ValueError(
            "Unknown migration option(s): "
            + ", ".join(sorted(unknown))
            + ". Valid options: "
            + ", ".join(sorted(valid))
        )

    if preset_name:
        selected = set(MIGRATION_PRESETS[preset_name])
    elif not include_values or "all" in include_values:
        selected = set(valid)
    else:
        selected = set(include_values)

    if "all" in exclude_values:
        selected.clear()
    selected -= (set(exclude_values) - {"all"})
    return selected


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def resolve_secret_input(value: ***REDACTED***
    """Resolve an OpenClaw SecretInput value to a plain string.

    SecretInput can be:
    ***REDACTED***
    - An env template: "${OPENROUTER_API_KEY}"
    - A SecretRef object: ***REDACTED***
    """
    if isinstance(value, str):
        # Check for env template: "${VAR_NAME}"
        m = re.match(r"^\$\{(\w+)\}$", value.strip())
        if m and env:
            return env.get(m.group(1), "").strip() or None
        return value.strip() or None
    if isinstance(value, dict):
        source = value.get("source", "")
        ref_id = value.get("id", "")
        if source == "env" and ref_id and env:
            return env.get(ref_id, "").strip() or None
        # File/exec sources can't be resolved here — return None
    return None


class ConfigReadError(RuntimeError):
    """An existing config file is present but cannot be read or parsed.

    Signals that a read-modify-write round trip must be abandoned: the caller
    has no idea what the file holds, so writing a merged result back would
    replace real settings with only the keys it merged.
    """


def load_yaml_file(path: Path) -> Dict[str, Any]:
    """Load a YAML mapping, distinguishing "absent" from "unreadable".

    Every config.yaml caller here reads the file, merges a section into it and
    writes the whole mapping straight back.  Collapsing a present-but-unreadable
    file to ``{}`` therefore destroys it: a YAML syntax error, a permission
    problem or a broken mount would make the migration replace every setting
    the user had with only the section it merged, and still report ``migrated``.

    - Absent, or present but empty -> ``{}``; first-time creation still works.
    - Present but unreadable, unparseable, or not a mapping -> raise
      :class:`ConfigReadError` so the caller refuses and leaves the file
      byte-identical.

    ``yaml is None`` (PyYAML not installed) still yields ``{}``: nothing can be
    written in that state either, since :func:`dump_yaml_file` raises.
    """
    if yaml is None or not path.exists():
        return {}
    try:
        # errors="replace" means read_text() cannot raise UnicodeDecodeError;
        # OSError covers races like the file disappearing or being unreadable.
        raw = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        raise ConfigReadError(
            f"Refusing to overwrite {path}: the existing file cannot be read "
            f"({exc}). Fix the file permissions or move it aside first."
        ) from exc
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise ConfigReadError(
            f"Refusing to overwrite {path}: the existing file is not valid YAML "
            f"({exc}). Fix it with `hermes config edit` (or move it aside), then "
            f"re-run the migration."
        ) from exc
    # An empty file parses to None — a legitimate state with nothing to lose.
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ConfigReadError(
            f"Refusing to overwrite {path}: expected the existing file to hold a "
            f"YAML mapping but found {type(data).__name__}. Fix it with "
            f"`hermes config edit` (or move it aside), then re-run the migration."
        )
    return data


def dump_yaml_file(path: Path, data: Dict[str, Any]) -> None:
    """Write ``data`` as YAML via temp file + fsync + atomic rename.

    Only ever reached after :func:`load_yaml_file` has successfully read the
    same path, so the mapping being written is the real file's content plus the
    merged section — never a silently-empty stand-in.  Writing atomically means
    an interrupted migration cannot leave a truncated config.yaml behind.

    Inlined rather than importing ``utils.atomic_write_text``: this script is
    standalone and runs with only the stdlib on its path.  The symlink and
    cross-device handling mirrors ``utils.atomic_replace``: a plain
    ``os.replace`` onto a symlinked config.yaml would replace the *link* with a
    regular file, silently detaching managed deployments that symlink
    ``~/.hermes/config.yaml`` into a dotfiles repo or profile package.
    """
    if yaml is None:
        raise RuntimeError("PyYAML is required to update Hermes config.yaml")
    ensure_parent(path)
    target = os.path.realpath(str(path)) if os.path.islink(str(path)) else str(path)
    fd, tmp_path = tempfile.mkstemp(
        dir=os.path.dirname(target) or ".", prefix=".tmp_", suffix=".yaml"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(yaml.safe_dump(data, sort_keys=False, allow_unicode=False))
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.replace(tmp_path, target)
        except OSError as exc:
            # Cross-device or bind-mount deployments cannot rename into place.
            if exc.errno not in (errno.EXDEV, errno.EBUSY):
                raise
            shutil.copyfile(tmp_path, target)
            try:
                shutil.copystat(tmp_path, target)
            except OSError:
                pass
            # fsync the copied target so the durability claim holds on the
            # cross-device path too (mirrors utils.atomic_replace, including
            # its swallow — a failed fsync must not report the already-copied
            # write as failed).
            try:
                target_fd = os.open(target, os.O_RDONLY)
                try:
                    os.fsync(target_fd)
                finally:
                    os.close(target_fd)
            except OSError:
                pass
            os.unlink(tmp_path)
    except BaseException:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def parse_env_file(path: Path) -> Dict[str, str]:
    if not path.exists():
        return {}
    data: Dict[str, str] = {}
    try:
        # errors="replace" means read_text() cannot raise UnicodeDecodeError;
        # OSError covers races like the file disappearing or being unreadable.
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return {}
    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        data[key.strip()] = value.strip()
    return data


def save_env_file(path: Path, data: Dict[str, str]) -> None:
    ensure_parent(path)
    lines = [f"{key}={value}" for key, value in data.items()]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def backup_existing(path: Path, backup_root: Path) -> Optional[Path]:
    if not path.exists():
        return None
    rel = Path(*path.parts[1:]) if path.is_absolute() and len(path.parts) > 1 else path
    dest = backup_root / rel
    ensure_parent(dest)
    if path.is_dir():
        shutil.copytree(path, dest, dirs_exist_ok=True)
    else:
        shutil.copy2(path, dest)
    return dest


# ── Brand rewriting ─────────────────────────────────────────
# Replace OpenClaw brand names with Hermes in migrated text so that
# memory entries, user profiles, SOUL.md, and workspace instructions
# read as self-referential to the new agent identity.
#
# Case-preserving: ``OpenClaw`` → ``Hermes`` (prose), but lowercase matches
# like ``openclaw`` → ``hermes`` (so filesystem paths like ``~/.openclaw``
# become ``~/.hermes`` — the real Hermes home — not the broken ``~/.Hermes``).
_REBRAND_PATTERNS: List[Tuple[re.Pattern, str]] = [
    (re.compile(r'\bOpen[\s-]?Claw\b', re.IGNORECASE), 'Hermes'),
    (re.compile(r'\bClawdBot\b', re.IGNORECASE), 'Hermes'),
    (re.compile(r'\bMoltBot\b', re.IGNORECASE), 'Hermes'),
]


def _case_preserving_replacement(replacement: str):
    """Return a re.sub replacement fn that lowercases the result when the
    matched text was all-lowercase.

    Keeps ``OpenClaw`` → ``Hermes`` but maps ``openclaw`` → ``hermes`` so a
    filesystem path like ``~/.openclaw/config.yaml`` rewrites to
    ``~/.hermes/config.yaml`` (the real Hermes home) instead of the broken
    ``~/.Hermes/config.yaml``.
    """
    def _sub(match: "re.Match[str]") -> str:
        matched = match.group(0)
        if matched and matched.islower():
            return replacement.lower()
        return replacement
    return _sub


def rebrand_text(text: str) -> str:
    """Replace OpenClaw / ClawdBot / MoltBot brand names with Hermes.

    Preserves case so filesystem-path matches (lowercase) don't become
    capitalized directory names that don't exist.
    """
    for pattern, replacement in _REBRAND_PATTERNS:
        text = pattern.sub(_case_preserving_replacement(replacement), text)
    return text


def parse_existing_memory_entries(path: Path) -> List[str]:
    """Parse a DESTINATION Hermes memory store (memories/MEMORY.md, USER.md).

    Splits on ``ENTRY_DELIMITER`` only, matching ``MemoryStore._parse_entries``
    in ``tools/memory_tool.py``: a store with no delimiter is ONE intact entry.
    Do NOT fall back to :func:`extract_markdown_entries` — it is the *source*
    parser (workspace/MEMORY.md and friends), it drops fenced code blocks and
    table rows and splits a block into one entry per bullet, and the merged
    result is written back over the destination.
    """
    if not path.exists():
        return []
    raw = read_text(path)
    if not raw.strip():
        return []
    return [e.strip() for e in raw.split(ENTRY_DELIMITER) if e.strip()]


def extract_markdown_entries(text: str) -> List[str]:
    entries: List[str] = []
    headings: List[str] = []
    paragraph_lines: List[str] = []

    def context_prefix() -> str:
        filtered = [h for h in headings if h and not re.search(r"\b(MEMORY|USER|SOUL|AGENTS|TOOLS|IDENTITY)\.md\b", h, re.I)]
        return " > ".join(filtered)

    def flush_paragraph() -> None:
        nonlocal paragraph_lines
        if not paragraph_lines:
            return
        text_block = " ".join(line.strip() for line in paragraph_lines).strip()
        paragraph_lines = []
        if not text_block:
            return
        prefix = context_prefix()
        if prefix:
            entries.append(f"{prefix}: {text_block}")
        else:
            entries.append(text_block)

    in_code_block = False
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()

        if stripped.startswith("```"):
            in_code_block = not in_code_block
            flush_paragraph()
            continue
        if in_code_block:
            continue

        heading_match = re.match(r"^(#{1,6})\s+(.*\S)\s*$", stripped)
        if heading_match:
            flush_paragraph()
            level = len(heading_match.group(1))
            text_value = heading_match.group(2).strip()
            while len(headings) >= level:
                headings.pop()
            headings.append(text_value)
            continue

        bullet_match = re.match(r"^\s*(?:[-*]|\d+\.)\s+(.*\S)\s*$", line)
        if bullet_match:
            flush_paragraph()
            content = bullet_match.group(1).strip()
            prefix = context_prefix()
            entries.append(f"{prefix}: {content}" if prefix else content)
            continue

        if not stripped:
            flush_paragraph()
            continue

        if stripped.startswith("|") and stripped.endswith("|"):
            flush_paragraph()
            continue

        paragraph_lines.append(stripped)

    flush_paragraph()

    deduped: List[str] = []
    seen = set()
    for entry in entries:
        normalized = normalize_text(entry)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(entry.strip())
    return deduped


def merge_entries(
    existing: Sequence[str],
    incoming: Sequence[str],
    limit: int,
) -> Tuple[List[str], Dict[str, int], List[str]]:
    merged = list(existing)
    seen = {normalize_text(entry) for entry in existing if entry.strip()}
    stats = {"existing": len(existing), "added": 0, "duplicates": 0, "overflowed": 0}
    overflowed: List[str] = []

    current_len = len(ENTRY_DELIMITER.join(merged)) if merged else 0

    for entry in incoming:
        normalized = normalize_text(entry)
        if not normalized:
            continue
        if normalized in seen:
            stats["duplicates"] += 1
            continue

        candidate_len = len(entry) if not merged else current_len + len(ENTRY_DELIMITER) + len(entry)
        if candidate_len > limit:
            stats["overflowed"] += 1
            overflowed.append(entry)
            continue

        merged.append(entry)
        seen.add(normalized)
        current_len = candidate_len
        stats["added"] += 1

    return merged, stats, overflowed


def relative_label(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


# ───────────────────────────────────────────────────────────────────────
# Secret redaction for migration reports.
#
# The report JSON persists to disk inside the migration output directory and
# frequently ends up in bug reports or support channels.  Anything that looks
# like a credential — by key name or by value shape — is replaced with
# "[redacted]" before the report is written.
#
# Modelled on OpenClaw's src/plugin-sdk/migration.ts so both migration tools
# redact consistently.  Pure function — safe to call on any plain-data dict.
# ───────────────────────────────────────────────────────────────────────
REDACTED_MIGRATION_VALUE = "[redacted]"

_SECRET_KEY_MARKERS = ***REDACTED***
    "accesstoken",
    "apikey",
    "authorization",
    "bearertoken",
    "clientsecret",
    "cookie",
    "credential",

... [Content truncated, total 146,509 chars] ...