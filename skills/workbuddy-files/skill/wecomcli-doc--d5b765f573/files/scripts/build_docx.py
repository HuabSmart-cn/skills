"""build_docx.py — Generate a .docx file from a JSONL spec.

Each line of the input file is a single command::

    {"action": "<function_name>", "params": {...}}

Workflow::

    1. 读 JSONL → 一次性按 ``references/doc-create.md`` 做参数校验
       （action 取值 / params 字段名 / 类型 / 取值范围）。
       任何偏差立即抛 ``TypeError``（"类型错误，无法执行"）。
    2. 校验通过后，再创建 docx 并按 action 派发到 ``DocxBuilder``。
    3. 通过本地文件系统写出 ``.docx``，输出路径自动选取于
       ``WECOMAGENT_WRITABLE_DIRS`` 的第一个目录；同名文件会追加
       ``_1`` / ``_2`` … 后缀避免覆盖。

Usage::

    python build_docx.py <spec.jsonl>
"""

from __future__ import annotations

import argparse
import base64
import functools
import io
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Iterator, NamedTuple

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Cm, Emu, Pt, RGBColor

# ===========================================================================
# Constants & lookups
# ===========================================================================

_PARAGRAPH_ALIGN = {
    "left": WD_ALIGN_PARAGRAPH.LEFT,
    "center": WD_ALIGN_PARAGRAPH.CENTER,
    "right": WD_ALIGN_PARAGRAPH.RIGHT,
    "justify": WD_ALIGN_PARAGRAPH.JUSTIFY,
}

_TABLE_ALIGN = {
    "left": WD_TABLE_ALIGNMENT.LEFT,
    "center": WD_TABLE_ALIGNMENT.CENTER,
    "right": WD_TABLE_ALIGNMENT.RIGHT,
}

EMU_PER_DXA = 635                  # 1 dxa = 1/20 pt = 635 EMU
DEFAULT_TABLE_TOTAL_DXA = 9072     # ~6.30 in, A4 content-area width
DEFAULT_LINE_DXA_NORMAL = 312
DEFAULT_LINE_DXA_HEADING = 408

# Table-level frame uses a thin theme-default line; per-cell borders
# use a soft gray, applied to every cell so the grid stays consistent
# on renderers that ignore table-level borders.
DEFAULT_TABLE_BORDER_COLOR_HEX = "auto"
DEFAULT_TABLE_BORDER_SIZE = 4
DEFAULT_CELL_BORDER_COLOR_HEX = "CBCDD1"
DEFAULT_CELL_BORDER_SIZE = 6

# --- XSD ordering anchors --------------------------------------------------
# Each tuple lists the children that the new element must appear *before*,
# per the OOXML schema. ``_set_unique_child`` inserts the new element ahead
# of the first sibling found.


def _anchors_after(tag: str, order: tuple) -> tuple:
    """Return the slice of ``order`` strictly after ``tag``."""
    return order[order.index(tag) + 1:]


# CT_PPrBase: shared by snapToGrid (pos 21) and spacing (pos 22) —
# every sibling listed comes after both.
_PPR_SPACING_ANCHORS = (
    qn("w:contextualSpacing"),
    qn("w:jc"),
    qn("w:outlineLvl"),
)

# CT_TblPr order (relevant prefix).
_TBL_PR_ORDER = (
    qn("w:tblW"),
    qn("w:jc"),
    qn("w:tblCellSpacing"),
    qn("w:tblInd"),
    qn("w:tblBorders"),
    qn("w:shd"),
    qn("w:tblLayout"),
    qn("w:tblLook"),
)
_TBL_PR_TBLW_ANCHORS = _anchors_after(qn("w:tblW"), _TBL_PR_ORDER)
_TBL_PR_BORDERS_ANCHORS = _anchors_after(qn("w:tblBorders"), _TBL_PR_ORDER)
_TBL_PR_LAYOUT_ANCHORS = _anchors_after(qn("w:tblLayout"), _TBL_PR_ORDER)

# CT_TcPrInner order (relevant prefix).
_TC_PR_ORDER = (
    qn("w:tcBorders"),
    qn("w:shd"),
    qn("w:noWrap"),
    qn("w:tcMar"),
    qn("w:textDirection"),
    qn("w:tcFitText"),
    qn("w:vAlign"),
    qn("w:hideMark"),
    qn("w:headers"),
)
_TC_PR_BORDERS_ANCHORS = _anchors_after(qn("w:tcBorders"), _TC_PR_ORDER)
_TC_PR_SHD_ANCHORS = _anchors_after(qn("w:shd"), _TC_PR_ORDER)
_TC_PR_MAR_ANCHORS = _anchors_after(qn("w:tcMar"), _TC_PR_ORDER)
_TC_PR_VALIGN_ANCHORS = _anchors_after(qn("w:vAlign"), _TC_PR_ORDER)


class _HeadingPreset(NamedTuple):
    style_name: str
    size_pt: int
    color_hex: str
    alignment: str | None


# Title 24pt → H1 18pt → H2 16pt → H3 14pt → H4 12pt → H5/H6 11pt.
_DEFAULT_HEADINGS: tuple[_HeadingPreset, ...] = (
    _HeadingPreset("Title",     24, "1A1A1A", "center"),
    _HeadingPreset("Subtitle",  18, "5C5C5C", "center"),
    _HeadingPreset("Heading 1", 18, "1A1A1A", None),
    _HeadingPreset("Heading 2", 16, "1A1A1A", None),
    _HeadingPreset("Heading 3", 14, "1A1A1A", None),
    _HeadingPreset("Heading 4", 12, "1A1A1A", None),
    _HeadingPreset("Heading 5", 11, "1A1A1A", None),
    _HeadingPreset("Heading 6", 11, "1A1A1A", None),
)

# 6 位十六进制颜色字符串，可选前缀 '#'。供 _hex_to_rgb / 上游校验复用。
_HEX_COLOR_RE = re.compile(r"^#?[0-9A-Fa-f]{6}$")


# ===========================================================================
# Exceptions
# ===========================================================================


class SpecTypeError(TypeError):
    """JSONL 参数校验失败抛出，等同 ``TypeError``，附带行号上下文。"""


# Backwards-compatible alias for any existing caller that imports SpecError.
SpecError = SpecTypeError


# ===========================================================================
# JSONL spec validation — 上游一次性校验（基于 references/doc-create.md）
# ===========================================================================
#
# 校验范围严格对齐 doc-create.md 中描述的 4 个 action 及其 params。
# 任何偏差均抛出 ``SpecTypeError``（继承自 ``TypeError``），由 main()
# 统一捕获并转成 "类型错误，无法执行" 提示。

# 段落 style 仅支持以下内置样式（doc-create.md：列表样式 + Subtitle）。
ALLOWED_PARAGRAPH_STYLES: frozenset[str] = frozenset({
    "List Bullet", "List Bullet 2", "List Bullet 3",
    "List Number", "List Number 2", "List Number 3",
    "Subtitle",
})

# 段落级对齐枚举。
ALLOWED_ALIGNMENTS: frozenset[str] = frozenset({
    "left", "center", "right", "justify",
})

# run / cell 对象支持的字段及类型（与 doc-create.md 中表格一致）。
# (int, float) 元组用于 "数字" 类（运行时显式排除 bool）。
RUN_FIELD_TYPES: dict[str, Any] = {
    "text": str,
    "bold": bool,
    "italic": bool,
    "underline": bool,
    "color_hex": str,
    "size_pt": (int, float),
    "font": str,
    "east_asia_font": str,
}

# add_heading.level 取值范围（doc-create.md：0=Title，1~4=章节标题）。
HEADING_LEVEL_MIN: int = 0
HEADING_LEVEL_MAX: int = 4

# 结构化输入上限：在校验阶段尽早拒绝异常输入，避免下游构建 / 序列化
MAX_COMMANDS: int = 5000              # 单份 JSONL 的命令条数上限
MAX_TEXT_CHARS: int = 20000           # 段落 text / run.text 单字段长度上限
MAX_RUNS_PER_PARAGRAPH: int = 200     # 单段 runs 数组长度上限
MAX_TABLE_ROWS: int = 10000            # 单表行数上限
MAX_TABLE_COLS: int = 50              # 单行列数上限
MAX_CELL_TEXT_CHARS: int = 5000       # 表格 cell（字符串或 run.text）长度上限


def _spec_raise(ctx: str, msg: str) -> None:
    raise SpecTypeError(f"{ctx}: {msg}")


def _spec_type_name(expected: Any) -> str:
    if isinstance(expected, type):
        return expected.__name__
    if isinstance(expected, tuple):
        return " | ".join(t.__name__ for t in expected if isinstance(t, type))
    return str(expected)


def _spec_check_type(value: Any, expected: Any, ctx: str, name: str) -> None:
    """对值做基础类型检查；显式拒绝 bool 充当 int/float。"""
    if expected is int:
        if isinstance(value, bool) or not isinstance(value, int):
            _spec_raise(ctx, f"参数 '{name}' 类型错误，期望 int，实际 {type(value).__name__}")
        return
    if expected is bool:
        if not isinstance(value, bool):
            _spec_raise(ctx, f"参数 '{name}' 类型错误，期望 bool，实际 {type(value).__name__}")
        return
    if isinstance(expected, tuple) and int in expected and float in expected:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            _spec_raise(ctx, f"参数 '{name}' 类型错误，期望 number，实际 {type(value).__name__}")
        return
    if not isinstance(value, expected):
        _spec_raise(
            ctx,
            f"参数 '{name}' 类型错误，期望 {_spec_type_name(expected)}，"
            f"实际 {type(value).__name__}",
        )


def _spec_check_hex_color(value: Any, ctx: str, name: str) -> None:
    if not (isinstance(value, str) and _HEX_COLOR_RE.match(value)):
        _spec_raise(
            ctx,
            f"参数 '{name}' 必须是 6 位十六进制颜色字符串"
            f"（如 'FF0000' 或 '#FF0000'），实际为 {value!r}",
        )


def _spec_validate_run_object(
    obj: Any,
    ctx: str,
    max_text_chars: int = MAX_TEXT_CHARS,
) -> None:
    """校验一个 run / table-cell 对象（字段集合相同）。

    ``max_text_chars`` 控制 ``text`` 字段的长度上限：段落里的 run 沿用
    ``MAX_TEXT_CHARS``；表格 cell 上下文则收窄到 ``MAX_CELL_TEXT_CHARS``。
    """
    if not isinstance(obj, dict):
        _spec_raise(ctx, f"必须是 JSON 对象（dict），实际 {type(obj).__name__}")

    unknown = set(obj) - set(RUN_FIELD_TYPES)
    if unknown:
        _spec_raise(
            ctx,
            f"包含未知字段 {sorted(unknown)}；允许字段: {sorted(RUN_FIELD_TYPES)}",
        )

    for fname, expected in RUN_FIELD_TYPES.items():
        if fname not in obj:
            continue
        _spec_check_type(obj[fname], expected, ctx, fname)

    if "text" in obj and len(obj["text"]) > max_text_chars:
        _spec_raise(
            ctx,
            f"参数 'text' 长度 {len(obj['text'])} 超过上限 {max_text_chars} 字符",
        )

    if "color_hex" in obj:
        _spec_check_hex_color(obj["color_hex"], ctx, "color_hex")

    if "size_pt" in obj:
        size = obj["size_pt"]
        if size < 1 or size > 819:
            _spec_raise(ctx, f"参数 'size_pt' 必须在 [1, 819] 范围内，实际为 {size}")


def _spec_validate_add_paragraph(params: dict, ctx: str) -> None:
    allowed = {"text", "runs", "style", "alignment"}
    unknown = set(params) - allowed
    if unknown:
        _spec_raise(
            ctx,
            f"add_paragraph 含未知参数 {sorted(unknown)}；允许参数: {sorted(allowed)}",
        )

    if "text" in params:
        _spec_check_type(params["text"], str, ctx, "text")
        if len(params["text"]) > MAX_TEXT_CHARS:
            _spec_raise(
                ctx,
                f"参数 'text' 长度 {len(params['text'])} 超过上限 "
                f"{MAX_TEXT_CHARS} 字符",
            )

    if "runs" in params:
        runs = params["runs"]
        if not isinstance(runs, list):
            _spec_raise(ctx, f"参数 'runs' 必须是数组，实际 {type(runs).__name__}")
        if len(runs) > MAX_RUNS_PER_PARAGRAPH:
            _spec_raise(
                ctx,
                f"参数 'runs' 数量 {len(runs)} 超过上限 "
                f"{MAX_RUNS_PER_PARAGRAPH}",
            )
        for i, r in enumerate(runs):
            _spec_validate_run_object(r, f"{ctx}.runs[{i}]")

    if "style" in params:
        style = params["style"]
        if not isinstance(style, str) or style not in ALLOWED_PARAGRAPH_STYLES:
            _spec_raise(
                ctx,
                f"参数 'style' 必须是 {sorted(ALLOWED_PARAGRAPH_STYLES)} 之一，"
                f"实际为 {style!r}",
            )

    if "alignment" in params:
        align = params["alignment"]
        if not isinstance(align, str) or align not in ALLOWED_ALIGNMENTS:
            _spec_raise(
                ctx,
                f"参数 'alignment' 必须是 {sorted(ALLOWED_ALIGNMENTS)} 之一，"
                f"实际为 {align!r}",
            )


def _spec_validate_add_heading(params: dict, ctx: str) -> None:
    allowed = {"text", "level"}
    unknown = set(params) - allowed
    if unknown:
        _spec_raise(
            ctx,
            f"add_heading 含未知参数 {sorted(unknown)}；允许参数: {sorted(allowed)}",
        )

    if "text" in params:
        _spec_check_type(params["text"], str, ctx, "text")

    if "level" in params:
        level = params["level"]
        if isinstance(level, bool) or not isinstance(level, int):
            _spec_raise(ctx, f"参数 'level' 必须是整数，实际为 {type(level).__name__}")
        if not (HEADING_LEVEL_MIN <= level <= HEADING_LEVEL_MAX):
            _spec_raise(
                ctx,
                f"参数 'level' 必须在 [{HEADING_LEVEL_MIN}, {HEADING_LEVEL_MAX}] 之间"
                f"（0=封面主标题 Title，1~4=一~四级章节标题），实际为 {level}",
            )


def _spec_validate_add_table(params: dict, ctx: str) -> None:
    allowed = {"data"}
    unknown = set(params) - allowed
    if unknown:
        _spec_raise(
            ctx,
            f"add_table 含未知参数 {sorted(unknown)}；仅支持参数: {sorted(allowed)}",
        )

    if "data" not in params:
        _spec_raise(ctx, "add_table 缺少必填参数 'data'")

    data = params["data"]
    if not isinstance(data, list):
        _spec_raise(ctx, f"参数 'data' 必须是二维数组，实际 {type(data).__name__}")
    if not data:
        _spec_raise(ctx, "参数 'data' 不能为空数组")
    if len(data) > MAX_TABLE_ROWS:
        _spec_raise(
            ctx,
            f"参数 'data' 行数 {len(data)} 超过上限 {MAX_TABLE_ROWS}",
        )

    for ri, row in enumerate(data):
        if not isinstance(row, list):
            _spec_raise(
                ctx,
                f"参数 'data[{ri}]' 必须是数组（一行 cells），实际 {type(row).__name__}",
            )
        if len(row) > MAX_TABLE_COLS:
            _spec_raise(
                ctx,
                f"参数 'data[{ri}]' 列数 {len(row)} 超过上限 {MAX_TABLE_COLS}",
            )
        for ci, cell in enumerate(row):
            cell_ctx = f"{ctx}.data[{ri}][{ci}]"
            if isinstance(cell, str):
                if len(cell) > MAX_CELL_TEXT_CHARS:
                    _spec_raise(
                        cell_ctx,
                        f"cell 文本长度 {len(cell)} 超过上限 "
                        f"{MAX_CELL_TEXT_CHARS} 字符",
                    )
                continue
            if isinstance(cell, dict):
                _spec_validate_run_object(
                    cell, cell_ctx, max_text_chars=MAX_CELL_TEXT_CHARS,
                )
                continue
            _spec_raise(
                cell_ctx,
                f"cell 必须是字符串或 dict（单 run 对象），实际 {type(cell).__name__}",
            )


def _spec_validate_add_page_break(params: dict, ctx: str) -> None:
    if params:
        _spec_raise(ctx, f"add_page_break 不接受任何参数，实际为 {params!r}")


# action 名称 → 校验函数；同时充当 "合法 action 集合"。
_SPEC_ACTION_VALIDATORS: dict[str, Any] = {
    "add_paragraph":  _spec_validate_add_paragraph,
    "add_heading":    _spec_validate_add_heading,
    "add_table":      _spec_validate_add_table,
    "add_page_break": _spec_validate_add_page_break,
}


def _spec_validate_command(cmd: Any, line_no: int) -> tuple[str, dict]:
    """校验单条 JSONL 命令，返回 ``(action, params)`` 便于派发器复用。"""
    ctx = f"Line {line_no}"

    if not isinstance(cmd, dict):
        _spec_raise(ctx, f"每行必须是 JSON 对象，实际 {type(cmd).__name__}")

    extra = set(cmd) - {"action", "params"}
    if extra:
        _spec_raise(ctx, f"命令仅允许 'action' / 'params' 字段，多余字段: {sorted(extra)}")

    if "action" not in cmd:
        _spec_raise(ctx, "缺少必填字段 'action'")

    action = cmd["action"]
    if not isinstance(action, str):
        _spec_raise(ctx, f"'action' 必须是字符串，实际 {type(action).__name__}")
    if action not in _SPEC_ACTION_VALIDATORS:
        _spec_raise(
            ctx,
            f"未知的 action {action!r}，允许的 action: {sorted(_SPEC_ACTION_VALIDATORS)}",
        )

    params = cmd.get("params", {})
    if not isinstance(params, dict):
        _spec_raise(ctx, f"'params' 必须是 JSON 对象，实际 {type(params).__name__}")

    _SPEC_ACTION_VALIDATORS[action](params, f"{ctx} action='{action}'")
    return action, params


# ===========================================================================
# Sandboxed local IO helpers
# ===========================================================================
#
# 所有 fs 读写都限制在
# ``WECOMAGENT_READABLE_DIRS`` / ``WECOMAGENT_WRITABLE_DIRS`` 限定
# （JSON 数组：``[{"path": "/abs/dir", "label": "..."}]``）。

ENV_READABLE = "WECOMAGENT_READABLE_DIRS"
ENV_WRITABLE = "WECOMAGENT_WRITABLE_DIRS"

# 读入 / 写出文件的大小硬上限：30 MiB。
# - 读入：避免一次性把巨型 JSONL 拉进内存撑爆进程；
# - 写出：避免生成过大的 .docx 写入磁盘（base64 后体积更大）。
MAX_FILE_SIZE_BYTES = 30 * 1024 * 1024


@functools.lru_cache(maxsize=None)
def _parse_roots(env_name: str) -> tuple[str, ...]:
    """Parse a JSON-array env var into a tuple of realpath roots (cached)."""
    raw = os.environ.get(env_name, "")
    if not raw:
        raise RuntimeError(f"环境变量 {env_name} 未设置或为空")
    parsed = json.loads(raw)
    if not isinstance(parsed, list):
        raise RuntimeError(
            f"{env_name} 必须是 JSON 数组，实际为 {type(parsed).__name__}"
        )
    roots: list[str] = []
    for it in parsed:
        if isinstance(it, str):
            it = json.loads(it)
        if not isinstance(it, dict):
            raise RuntimeError(
                f"{env_name} 元素必须是 dict 或 dict 的 JSON 字符串，"
                f"实际为 {type(it).__name__}"
            )
        p = it.get("path")
        if not isinstance(p, str) or not p.strip():
            raise RuntimeError(f"{env_name} 元素缺少有效的 path 字段: {it!r}")
        roots.append(os.path.realpath(p.strip()))
    if not roots:
        raise RuntimeError(f"环境变量 {env_name} 解析后为空")
    return tuple(roots)


def _reject_relative_segments(path: str) -> None:
    """Reject path strings that include ``.`` or ``..`` segments such as
    ``./foo``, ``../bar`` or ``/abs/path/../x``.

    Although ``os.path.realpath`` would silently normalize these away,
    accepting them would bypass the contract that callers must hand in
    explicit, fully-qualified paths inside the sandboxed roots — and
    could be abused to escape the intended directory in edge cases where
    symlinks are present.
    """
    if not path:
        return
    for seg in path.replace("\\", "/").split("/"):
        if seg in (".", ".."):
            raise ValueError(
                f"路径不允许包含 './' 或 '../' 这类相对路径片段: {path!r}"
            )


def _ensure_within(path: str, env_name: str) -> str:
    """Realpath ``path`` and ensure it lies within one of ``env_name``'s roots."""
    if not path:
        raise ValueError("path 不能为空")
    _reject_relative_segments(path)
    real = os.path.realpath(path)
    roots = _parse_roots(env_name)
    for root in roots:
        try:
            common = os.path.commonpath([real, root])
        except ValueError:
            continue
        if common == root:
            return real
    raise PermissionError(
        f"路径越权: {real} 不在 {env_name} 范围 {roots} 之内"
    )


def _read_text(path: str) -> str:
    """Read a UTF-8 text file from an allowed readable directory.

    最多读取 ``MAX_FILE_SIZE_BYTES + 1`` 字节，以便在不把超大文件
    整体载入内存的前提下判断是否超限。
    """
    real = _ensure_within(path, ENV_READABLE)
    with open(real, "rb") as f:
        data = f.read(MAX_FILE_SIZE_BYTES + 1)
    if len(data) > MAX_FILE_SIZE_BYTES:
        raise ValueError(
            f"输入文件过大：{path!r} "
            f"超过上限 {MAX_FILE_SIZE_BYTES} 字节（30 MiB）"
        )
    return data.decode("utf-8")


def _write_b64(path: str, data_b64: str, overwrite: bool = False) -> None:
    """Write a base64-encoded binary blob to an allowed writable directory.

    这里在写入前对路径做 ``os.path.islink`` 检查并显式拒绝：
      - 检查 ``path``（原始入参）：拦截 "目标位置本身就是软链" 的常见情况；
      - 检查 ``real``（realpath 结果）：作为防御纵深，覆盖悬挂软链 /
        竞态等 realpath 仍可能返回软链的边缘情况。
    """
    real = _ensure_within(path, ENV_WRITABLE)
    if os.path.islink(path) or os.path.islink(real):
        raise PermissionError(
            f"拒绝写入符号链接以避免跨目录覆盖: {path!r}"
        )
    data = base64.b64decode(data_b64, validate=True)
    if len(data) > MAX_FILE_SIZE_BYTES:
        raise ValueError(
            f"输出文件过大：解码后 {len(data)} 字节，"
            f"超过上限 {MAX_FILE_SIZE_BYTES} 字节（30 MiB）"
        )

    parent = os.path.dirname(real)
    os.makedirs(parent, exist_ok=True)

    # 创建父目录后再次解析路径，防止目录在检查和写入之间变为软链。
    real = _ensure_within(path, ENV_WRITABLE)
    if os.path.islink(path) or os.path.islink(real):
        raise PermissionError(
            f"拒绝写入符号链接以避免跨目录覆盖: {path!r}"
        )

    mode = "wb" if overwrite else "xb"
    with open(real, mode) as f:
        f.write(data)


# ===========================================================================
# Generic OOXML helpers
# ===========================================================================
#
# 注：颜色 / 数值 / 取值合法性已在上游 _spec_validate_command 阶段校验，
# 此处不再重复检查；下游 helpers 仅负责生成 OOXML 元素。


def _hex_to_rgb(color_hex: str) -> RGBColor:
    s = color_hex.lstrip("#")
    return RGBColor(int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))


def _set_unique_child(parent, tag, new_el, insert_before=()) -> None:
    """Replace any existing ``tag`` children of ``parent`` with ``new_el``,
    inserting ahead of the first sibling listed in ``insert_before`` (the
    XSD ordering constraint). Falls back to append."""
    for existing in parent.findall(tag):
        parent.remove(existing)
    for sibling_tag in insert_before:
        sibling = parent.find(sibling_tag)
        if sibling is not None:
            sibling.addprevious(new_el)
            return
    parent.append(new_el)


def _set_east_asia_font(rPr, font_name: str) -> None:
    """Set ``w:eastAsia`` on the rFonts child of ``rPr`` (creating it if needed)."""
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.insert(0, rFonts)
    rFonts.set(qn("w:eastAsia"), font_name)


def _strip_theme_color(element) -> None:
    """Remove ``themeColor``/``themeTint``/``themeShade`` from every
    ``w:color`` under ``element``.

    Built-in heading styles ship with theme-tinted colors that many
    renderers prefer over the explicit ``w:val``, leaking the accent
    color (typically blue) instead of the requested RGB.
    """
    color_tag = qn("w:color")
    color_attrs = (qn("w:themeColor"), qn("w:themeTint"), qn("w:themeShade"))
    for color_el in element.iter(color_tag):
        for key in color_attrs:
            if key in color_el.attrib:
                del color_el.attrib[key]


def _force_color_on_rpr(rPr, color_hex: str) -> None:
    """Replace any ``<w:color>`` under ``rPr`` with a plain ``w:val`` one
    (no theme attributes)."""
    for existing in rPr.findall(qn("w:color")):
        rPr.remove(existing)
    color_el = OxmlElement("w:color")
    color_el.set(qn("w:val"), color_hex.lstrip("#").upper())
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is not None:
        rFonts.addnext(color_el)
    else:
        rPr.insert(0, color_el)


def _apply_run_format(run, spec: dict) -> None:
    """Apply formatting from a run-spec dict to a python-docx Run."""
    if spec.get("bold"):
        run.bold = True
    if spec.get("italic"):
        run.italic = True
    if spec.get("underline"):
        run.underline = True
    if "color_hex" in spec:
        run.font.color.rgb = _hex_to_rgb(spec["color_hex"])
    if "size_pt" in spec:
        run.font.size = Pt(spec["size_pt"])
    if "font" in spec:
        run.font.name = spec["font"]
    if "east_asia_font" in spec:
        _set_east_asia_font(run._element.get_or_add_rPr(), spec["east_asia_font"])


def _make_borders_el(wrapper_tag: str, sides: tuple, color_hex: str, size: int):
    """Build a ``<w:tblBorders>`` / ``<w:tcBorders>`` element with all
    sides sharing the same single-line style, size and color."""
    inner = "".join(
        f'<w:{s} w:val="single" w:sz="{size}" w:color="{color_hex}"/>'
        for s in sides
    )
    return parse_xml(f'<w:{wrapper_tag} {nsdecls("w")}>{inner}</w:{wrapper_tag}>')


# ===========================================================================
# DocxBuilder — every public method (no leading underscore) is a JSONL action
# ===========================================================================


class DocxBuilder:
    """Each public method (no leading underscore) is callable as an `action`.

    所有方法不再做内部参数校验，调用方（``_dispatch``）保证传入的参数
    已通过上游 ``_spec_validate_command`` 检查。
    """

    def __init__(self) -> None:
        self.doc: Any = None  # python-docx Document

    # -- 0. Default initialization -----------------------------------------

    def _init_defaults(self) -> None:
        """Run document + page + Normal + heading defaults. Called once by
        ``run_jsonl`` before any user action; spec-level setup_* overrides win."""
        self._create_document()
        self.setup_page()
        self.setup_normal_style()
        for preset in _DEFAULT_HEADINGS:
            self.setup_heading_style(
                style_name=preset.style_name,
                size_pt=preset.size_pt,
                color_hex=preset.color_hex,
                alignment=preset.alignment,
            )

    # -- 1. Document lifecycle --------------------------------------------

    def _create_document(self) -> None:
        # Underscore-prefixed: not exposed as a JSONL action — calling it
        # twice would replace ``self.doc`` and drop everything written so far.
        self.doc = Document()
        settings = self.doc.settings.element
        zoom = settings.find(qn("w:zoom"))
        if zoom is not None and zoom.get(qn("w:percent")) is None:
            zoom.set(qn("w:percent"), "100")

    def save(self, path: str) -> None:
        """Persist the document to the local filesystem.

        ``overwrite=False`` enforces the "never clobber an existing .docx"
        guarantee that ``_pick_output_path`` makes when picking the filename.

        在编码 / 写入之前校验序列化后的 docx 体积不得超过
        ``MAX_FILE_SIZE_BYTES``；超限直接抛 ``ValueError`` 中止保存。
        """
        buf = io.BytesIO()
        self.doc.save(buf)
        size = buf.tell()
        if size > MAX_FILE_SIZE_BYTES:
            raise ValueError(
                f"输出文件过大：序列化后 {size} 字节，"
                f"超过上限 {MAX_FILE_SIZE_BYTES} 字节（30 MiB）"
            )
        data_b64 = base64.b64encode(buf.getvalue()

... [Content truncated, total 47,709 chars] ...