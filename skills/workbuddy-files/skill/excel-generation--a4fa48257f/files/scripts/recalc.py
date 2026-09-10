"""
Excel Formula Recalculation Script

openpyxl 写入的公式只是字符串、不带缓存值，未重算前任何读取缓存值的程序
（load_workbook(data_only=True)、pandas、微信/邮件等附件预览器）都会读到 None。
本脚本按三层降级补齐缓存值：

  1. LibreOffice 重算（隔离 profile，权威引擎）
  2. 纯 Python formulas 引擎求值 + 回填 <v>（LibreOffice 不可用时）
  3. 静态结构分析（两个引擎都不可用时；此时无法产出缓存值，返回 error）

对外契约不随引擎变化：成功返回 status/total_errors/total_formulas/error_summary，
失败返回 error。engine 字段标明本次实际使用的引擎。
"""

import contextlib
import importlib
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
import zipfile
from io import BytesIO
from pathlib import Path

from office.soffice import SOFFICE_NOT_FOUND, find_soffice, get_soffice_env

from openpyxl import load_workbook
from openpyxl.formula import Tokenizer
from openpyxl.worksheet.formula import ArrayFormula

MACRO_LIBRARY = "SheetAgent"
MACRO_MODULE = "Recalculate"
MACRO_FILENAME = "Recalculate.xba"

# 单个错误类型最多返回的坐标数量，避免响应过大。
MAX_LOCATIONS = 100

# formulas 只在显式授权时才允许按需安装；限制安装时长，避免离线环境
# 中 recalc 长时间无输出。
FORMULAS_REQUIREMENT = "formulas>=1.3.0,<2"
FORMULAS_INSTALL_TIMEOUT = 60

# soffice 不在 PATH 时的统一提示。
SOFFICE_MISSING = SOFFICE_NOT_FOUND

# 匹配外部工作簿引用，如 [1]Sheet1!A1 或 '[1]Sheet 1'!A1。
EXTERNAL_REF_RE = re.compile(r"""(?<![\w"\[])'?\[\d+\][^!"\[\]]*'?!""")

EXCEL_ERRORS = (
    "#VALUE!",
    "#DIV/0!",
    "#REF!",
    "#NAME?",
    "#NULL!",
    "#NUM!",
    "#N/A",
)

# ``formulas`` 会把部分动态/传统数组函数静默折叠成左上角单值（例如
# TRANSPOSE(A1:A2) 得到 [[A1]]），仅看计算结果的 shape 无法识别数据已丢失。
# Python 降级层必须在求值前拒绝这些已知的多值函数；LibreOffice 路径不受影响。
MULTI_CELL_FUNCTIONS = frozenset(
    {
        "BYCOL",
        "BYROW",
        "CHOOSECOLS",
        "CHOOSEROWS",
        "DROP",
        "EXPAND",
        "FILTER",
        "FREQUENCY",
        "GROWTH",
        "HSTACK",
        "LINEST",
        "LOGEST",
        "MAKEARRAY",
        "MAP",
        "MINVERSE",
        "MMULT",
        "MUNIT",
        "RANDARRAY",
        "SCAN",
        "SEQUENCE",
        "SORT",
        "SORTBY",
        "TAKE",
        "TEXTSPLIT",
        "TOCOL",
        "TOROW",
        "TRANSPOSE",
        "TREND",
        "UNIQUE",
        "VSTACK",
        "WRAPCOLS",
        "WRAPROWS",
    }
)
DIRECT_RANGE_FORMULA_RE = re.compile(
    r"^=\s*(?:(?:'[^']+'|[A-Za-z_][\w.]*)!)?"
    r"\$?[A-Z]{1,3}\$?\d+:\$?[A-Z]{1,3}\$?\d+\s*$",
    re.IGNORECASE,
)

# spreadsheetml 主命名空间，注入缓存值时定位 <c>/<f>/<v> 节点。
SML_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
PKG_RELS_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
DOC_RELS_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


RECALCULATE_MACRO = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE script:module PUBLIC "-//OpenOffice.org//DTD OfficeDocument 1.0//EN" "module.dtd">
<script:module xmlns:script="http://openoffice.org/2000/script" script:name="Recalculate" script:language="StarBasic">
    Sub RecalculateAndSave()
      ThisComponent.calculateAll()
      ThisComponent.store()
      Dim markerFile As Integer
      markerFile = FreeFile
      Open ConvertFromURL("{completion_marker_uri}") For Output As #markerFile
      Print #markerFile, "complete"
      Close #markerFile
      ThisComponent.close(True)
    End Sub
</script:module>"""

BASIC_LIBRARIES = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE library:libraries PUBLIC "-//OpenOffice.org//DTD OfficeDocument 1.0//EN" "libraries.dtd">
<library:libraries
    xmlns:library="http://openoffice.org/2000/library"
    xmlns:xlink="http://www.w3.org/1999/xlink">
  <library:library library:name="Standard" library:link="false"/>
  <library:library library:name="SheetAgent" library:link="false"/>
</library:libraries>"""

BASIC_LIBRARY = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE library:library PUBLIC "-//OpenOffice.org//DTD OfficeDocument 1.0//EN" "library.dtd">
<library:library
    xmlns:library="http://openoffice.org/2000/library"
    library:name="SheetAgent"
    library:readonly="false"
    library:passwordprotected="false">
  <library:element library:name="Recalculate"/>
</library:library>"""


def setup_libreoffice_macro(profile_dir, completion_marker):
    basic_dir = Path(profile_dir) / "user" / "basic"
    macro_dir = basic_dir / MACRO_LIBRARY
    try:
        macro_dir.mkdir(parents=True, exist_ok=True)
        (basic_dir / "script.xlc").write_text(BASIC_LIBRARIES, encoding="utf-8")
        (macro_dir / "script.xlb").write_text(BASIC_LIBRARY, encoding="utf-8")
        (macro_dir / MACRO_FILENAME).write_text(
            RECALCULATE_MACRO.format(
                completion_marker_uri=Path(completion_marker).resolve().as_uri()
            ),
            encoding="utf-8",
        )
        return True
    except OSError:
        return False


def external_links_at_risk(filename):
    """探测工作簿中引用外部工作簿、且缓存值已丢失的公式单元格。

    openpyxl 存盘会剥离外部链接的缓存值，重算后这些单元格会变成 #NAME? 并
    永久删除外部链接。返回存在数据损坏风险的单元格坐标列表。
    """
    try:
        with zipfile.ZipFile(filename) as archive:
            names = archive.namelist()
    except (zipfile.BadZipFile, OSError):
        return []
    if not any(n.startswith("xl/externalLinks/") for n in names):
        return []

    with contextlib.ExitStack() as stack:
        formulas = load_workbook(filename, data_only=False)
        stack.callback(formulas.close)
        values = load_workbook(filename, data_only=True)
        stack.callback(values.close)

        external_names = [
            name
            for name, dn in formulas.defined_names.items()
            if isinstance(getattr(dn, "value", None), str)
            and EXTERNAL_REF_RE.search(dn.value)
        ]
        name_re = (
            re.compile(r"\b(" + "|".join(re.escape(n) for n in external_names) + r")\b")
            if external_names
            else None
        )

        at_risk = []
        for sheet in formulas.sheetnames:
            ws = formulas[sheet]
            if not hasattr(ws, "iter_rows"):
                continue
            cached = values[sheet]
            for row in ws.iter_rows():
                for cell in row:
                    formula = _formula_text(cell)
                    if formula is None:
                        continue
                    reaches_out = EXTERNAL_REF_RE.search(formula) or (
                        name_re and name_re.search(formula)
                    )
                    if reaches_out and cached[cell.coordinate].value is None:
                        at_risk.append(f"{sheet}!{cell.coordinate}")
        return at_risk


def _register_namespaces(xml_bytes):
    """注册文档中出现的所有命名空间前缀，避免 ElementTree 改写为 ns0。"""
    for _event, (prefix, uri) in ET.iterparse(BytesIO(xml_bytes), events=["start-ns"]):
        with contextlib.suppress(ValueError):
            ET.register_namespace(prefix, uri)


def _sheet_xml_paths(contents):
    """返回 {sheet 名大写: sheet XML 在包内的路径}。

    经 workbook.xml + rels 解析真实映射，而非假定 sheetN.xml 的序号顺序
    （删除/重排 sheet 后序号与顺序并不一致）。
    """
    wb_path, rels_path = "xl/workbook.xml", "xl/_rels/workbook.xml.rels"
    if wb_path not in contents or rels_path not in contents:
        return {}

    _register_namespaces(contents[wb_path])
    sheets_el = ET.fromstring(contents[wb_path]).find(f"{{{SML_NS}}}sheets")
    if sheets_el is None:
        return {}

    sheet_rid = {}
    for el in sheets_el.findall(f"{{{SML_NS}}}sheet"):
        name = el.get("name")
        rid = el.get(f"{{{PKG_RELS_NS}}}id") or el.get(f"{{{DOC_RELS_NS}}}id")
        if name and rid:
            sheet_rid[name] = rid

    _register_namespaces(contents[rels_path])
    rid_target = {}
    for rel in ET.fromstring(contents[rels_path]):
        rid, target = rel.get("Id"), rel.get("Target")
        if rid and target:
            rid_target[rid] = (
                target.lstrip("/") if target.startswith("/") else f"xl/{target}"
            )

    return {
        name.upper(): rid_target[rid]
        for name, rid in sheet_rid.items()
        if rid in rid_target
    }


def _inject_cached_values(filename, cache_map):
    """把求值结果作为缓存值写入公式单元格，公式本身保持不变。

    直接改写 sheet XML，在 <f> 旁补齐 <v>，使读取缓存值的程序能拿到数值；
    同时保留 <f>，Excel/WPS 打开后仍可编辑并自动重算。
    返回成功写入的 ``{(SHEET_NAME_UPPER, COORD)}`` 集合。
    """
    if not cache_map:
        return set()

    with zipfile.ZipFile(filename) as zin:
        names = zin.namelist()
        contents = {name: zin.read(name) for name in names}

    sheet_paths = _sheet_xml_paths(contents)
    if not sheet_paths:
        return set()

    by_sheet = {}
    for (sheet_name, coord), value in cache_map.items():
        by_sheet.setdefault(sheet_name.upper(), {})[coord] = value

    modified_keys = set()
    for sheet_upper, cell_values in by_sheet.items():
        xml_path = sheet_paths.get(sheet_upper)
        if not xml_path or xml_path not in contents:
            continue

        raw = contents[xml_path]
        _register_namespaces(raw)
        root = ET.fromstring(raw)
        sheet_data = root.find(f"{{{SML_NS}}}sheetData")
        if sheet_data is None:
            continue

        modified = False
        for row_el in sheet_data.findall(f"{{{SML_NS}}}row"):
            for cell_el in row_el.findall(f"{{{SML_NS}}}c"):
                coord = cell_el.get("r")
                if coord not in cell_values:
                    continue
                # 只回填公式单元格；无 <f> 说明是常量，不应改写。
                if cell_el.find(f"{{{SML_NS}}}f") is None:
                    continue

                value = cell_values[coord]
                v_el = cell_el.find(f"{{{SML_NS}}}v")
                if v_el is None:
                    v_el = ET.SubElement(cell_el, f"{{{SML_NS}}}v")

                if isinstance(value, str) and value in EXCEL_ERRORS:
                    cell_el.set("t", "e")
                    v_el.text = value
                elif isinstance(value, bool):
                    cell_el.set("t", "b")
                    v_el.text = "1" if value else "0"
                elif isinstance(value, (int, float)):
                    cell_el.attrib.pop("t", None)
                    v_el.text = repr(float(value))
                else:
                    cell_el.set("t", "str")
                    v_el.text = str(value)
                modified = True
                modified_keys.add((sheet_upper, coord))

        if modified:
            buf = BytesIO()
            ET.ElementTree(root).write(buf, xml_declaration=True, encoding="UTF-8")
            contents[xml_path] = buf.getvalue()

    if not modified_keys:
        return set()

    # 先写临时文件再原子替换，避免中途失败留下损坏的 xlsx。
    out = BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zout:
        for name in names:
            zout.writestr(name, contents[name])

    tmp_path = f"{filename}.recalc-tmp"
    try:
        with open(tmp_path, "wb") as fh:
            fh.write(out.getvalue())
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_path, filename)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(tmp_path)
        raise
    return modified_keys


def _formula_text(cell):
    """返回单元格公式文本；兼容普通公式字符串与 OOXML ArrayFormula。"""
    value = cell.value
    if isinstance(value, ArrayFormula):
        text = value.text
        return text if isinstance(text, str) and text.startswith("=") else None
    if isinstance(value, str) and value.startswith("="):
        return value
    return None


def _formula_cells(filename):
    """返回 ``[(sheet_name, coordinate, formula_text, is_array), ...]``。"""
    wb = load_workbook(filename, data_only=False)
    try:
        cells = []
        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            if not hasattr(ws, "iter_rows"):
                continue
            for row in ws.iter_rows():
                for cell in row:
                    formula = _formula_text(cell)
                    if formula is not None:
                        cells.append(
                            (
                                sheet_name,
                                cell.coordinate,
                                formula,
                                isinstance(cell.value, ArrayFormula),
                            )
                        )
        return cells
    finally:
        wb.close()


def _multi_cell_formula_risks(formula_cells):
    """返回 Python 降级层无法安全生成完整缓存的公式位置。"""
    risks = []
    for sheet_name, coord, formula, is_array in formula_cells:
        try:
            functions = {
                token.value[:***REDACTED***
                .upper()
                .removeprefix("_XLFN.")
                .removeprefix("_XLWS.")
                for token in Tokenizer(formula).items
                if token.type =***REDACTED***
            }
        except Exception:  # noqa: BLE001 - 非法公式交给引擎/静态分析报告
            functions = set()
        if (
            is_array
            or functions.intersection(MULTI_CELL_FUNCTIONS)
            or DIRECT_RANGE_FORMULA_RE.match(formula)
        ):
            risks.append(f"{sheet_name}!{coord}")
    return risks


def _load_formulas(allow_install=False):
    """导入 formulas；仅在显式授权时按需安装一次并重试。

    返回 (module_or_None, error_or_None)。pip 输出必须被捕获，否则会污染 main()
    约定的纯 JSON stdout。
    """
    try:
        return importlib.import_module("formulas"), None
    except ImportError:
        pass

    if not allow_install:
        return (
            None,
            f"{FORMULAS_REQUIREMENT} is not installed; install it manually, or rerun "
            "with --allow-install after the user or platform explicitly authorizes "
            "downloading Python packages",
        )

    cmd = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--quiet",
        "--disable-pip-version-check",
        "--only-binary=:all:",
        FORMULAS_REQUIREMENT,
    ]
    try:
        subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            timeout=FORMULAS_INSTALL_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        return (
            None,
            f"timed out after {FORMULAS_INSTALL_TIMEOUT}s installing "
            f"{FORMULAS_REQUIREMENT}",
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        detail = getattr(exc, "stderr", None)
        detail = detail.strip() if isinstance(detail, str) else ""
        suffix = f": {detail}" if detail else f": {exc}"
        return None, f"failed to install {FORMULAS_REQUIREMENT}{suffix}"

    importlib.invalidate_caches()
    try:
        return importlib.import_module("formulas"), None
    except ImportError as exc:
        return None, f"installed {FORMULAS_REQUIREMENT} but import still failed: {exc}"


def _extract_single_formula_value(values):
    """从 formulas 结果中提取单值。

    纯 Python 标量没有 size，直接返回；NumPy 标量和单元素数组
    通过 item() 转成原生值。返回值的第二项标明它是否为多值结果。
    """
    size = getattr(values, "size", None)
    if size is None:
        return values, False

    if int(size) != 1:
        return None, True

    item = getattr(values, "item", None)
    if callable(item):
        return item(), False
    return values[0, 0], False


def _recalc_with_formulas(filename, allow_install=False):
    """第二层：用纯 Python formulas 引擎求值并回填缓存值。

    返回 (error_or_None, total_errors, error_summary)。
    """
    try:
        formula_cells = _formula_cells(filename)
    except Exception as exc:  # noqa: BLE001
        return f"failed to enumerate formula cells: {exc}", 0, {}
    expected = {
        (sheet_name.upper(), coord): f"{sheet_name}!{coord}"
        for sheet_name, coord, _formula, _is_array in formula_cells
    }

    multi_cell_risks = _multi_cell_formula_risks(formula_cells)
    if multi_cell_risks:
        shown = multi_cell_risks[:MAX_LOCATIONS]
        return (
            "Python formulas fallback cannot safely cache multi-cell/dynamic-array "
            "formulas without changing Excel spill semantics: "
            + ", ".join(shown)
            + (
                f" (+{len(multi_cell_risks) - len(shown)} more)"
                if len(multi_cell_risks) > len(shown)
                else ""
            ),
            0,
            {},
        )

    formulas, dependency_error = _load_formulas(allow_install=allow_install)
    if dependency_error:
        return dependency_error, 0, {}

    try:
        os.environ.setdefault("TQDM_DISABLE", "1")
        solution = formulas.ExcelModel().loads(filename).finish().calculate()
    except Exception as exc:  # noqa: BLE001 - 引擎内部异常一律降级到静态分析
        return f"formulas engine failed: {exc}", 0, {}

    stem = Path(filename).name.upper()
    key_re = re.compile(rf"^'\[{re.escape(stem)}\](.+?)'!([A-Z]+\d+)$")

    error_details = {err: [] for err in EXCEL_ERRORS}
    total_errors = 0
    cache_map = {}
    multi_value_results = []

    for key, cell in solution.items():
        matched = key_re.match(str(key).upper())
        if not matched:
            continue
        sheet_name, coord = matched.group(1), matched.group(2)
        formula_key = (sheet_name, coord)
        if formula_key not in expected:
            continue

        try:
            value, is_multi_value = _extract_single_formula_value(cell.value)
        except (
            AttributeError,
            IndexError,
            KeyError,
            TypeError,
            ValueError,
            OverflowError,
        ):
            return (
                f"formulas engine returned an unreadable result for "
                f"{expected[formula_key]}",
                0,
                {},
            )
        if is_multi_value:
            multi_value_results.append(expected[formula_key])
            continue

        text = str(value)
        hit = next((err for err in EXCEL_ERRORS if err in text), None)
        if hit is None and isinstance(value, float):
            # 引擎用 inf/nan 表达除零与无效运算，需映射回 Excel 错误码。
            if math.isinf(value):
                hit = "#DIV/0!"
            elif math.isnan(value):
                hit = "#VALUE!"

        if hit:
            error_details[hit].append(f"{sheet_name}!{coord}")
            total_errors += 1
            cache_map[(sheet_name, coord)] = hit
            continue

        if isinstance(value, (int, float, str, bool)):
            cache_map[formula_key] = value

    if multi_value_results:
        shown = multi_value_results[:MAX_LOCATIONS]
        return (
            "formulas engine produced multi-cell/array results that cannot be safely "
            "cached without changing Excel spill semantics: "
            + ", ".join(shown)
            + (
                f" (+{len(multi_value_results) - len(shown)} more)"
                if len(multi_value_results) > len(shown)
                else ""
            ),
            0,
            {},
        )

    missing = [location for key, location in expected.items() if key not in cache_map]
    if missing:
        shown = missing[:MAX_LOCATIONS]
        return (
            "formulas engine did not produce a scalar cached value for every formula: "
            + ", ".join(shown)
            + (f" (+{len(missing) - len(shown)} more)" if len(missing) > len(shown) else ""),
            0,
            {},
        )

    try:
        injected = _inject_cached_values(filename, cache_map)
    except Exception as exc:  # noqa: BLE001 - 回填失败等同于没重算
        return f"failed to write cached values: {exc}", 0, {}

    not_injected = [location for key, location in expected.items() if key not in injected]
    if not_injected:
        shown = not_injected[:MAX_LOCATIONS]
        return (
            "failed to write cached values for every formula: "
            + ", ".join(shown)
            + (
                f" (+{len(not_injected) - len(shown)} more)"
                if len(not_injected) > len(shown)
                else ""
            ),
            0,
            {},
        )

    return None, total_errors, _build_error_summary(error_details)


def _static_analyze(filename):
    """第三层：无可用引擎时的结构检查（括号配平、引用的 sheet 是否存在）。

    只能发现结构性问题，**无法产出缓存值**，故调用方必须按失败处理。
    """
    error_details = {}
    sheet_ref_re = re.compile(r"(?:'([^']+)'|([A-Za-z_][\w.]*))!")

    wb = load_workbook(filename, data_only=False)
    try:
        sheet_names = set(wb.sheetnames)
        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            if not hasattr(ws, "iter_rows"):
                continue
            for row in ws.iter_rows():
                for cell in row:
                    formula = _formula_text(cell)
                    if formula is None:
                        continue
                    location = f"{sheet_name}!{cell.coordinate}"
                    if formula.count("(") != formula.count(")"):
                        error_details.setdefault("syntax_error", []).append(location)
                        continue
                    for matched in sheet_ref_re.finditer(formula):
                        ref = matched.group(1) or matched.group(2)
                        if ref not in sheet_names:
                            error_details.setdefault("#REF!", []).append(location)
                            break
    finally:
        wb.close()

    total = sum(len(v) for v in error_details.values())
    return total, _build_error_summary(error_details)


def _build_error_summary(error_details):
    summary = {}
    for err_type, locations in error_details.items():
        if not locations:
            continue
        entry = {"count": len(locations), "locations": locations[:MAX_LOCATIONS]}
        if len(locations) > MAX_LOCATIONS:
            entry["locations_truncated"] = len(locations) - MAX_LOCATIONS
        summary[err_type] = entry
    return summary


def _count_formulas(filename):
    return len(_formula_cells(filename))


def recalc(filename, timeout=30, force=False, allow_install=False):
    """三层降级重算：LibreOffice → formulas 回填 → 静态分析。

    engine 字段标明实际使用的引擎；第三层无法产出缓存值，按失败返回 error。
    """
    if not Path(filename).exists():
        return {"error": f"File {filename} does not exist"}
    if timeout <= 0:
        return {"error": "Timeout must be greater than zero"}

    abs_path = str(Path(filename).absolute())

    if not os.access(abs_path, os.W_OK):
        return {
            "error": f"{filename} is not writable; recalculation rewrites the file in place"
        }

    if not force:
        try:
            at_risk = external_links_at_risk(filename)
        except Exception as exc:  # noqa: BLE001 - 探测失败不应阻断，交由调用方处理
            return {"error": f"Could not inspect {filename} for external links: {exc}"}
        if at_risk:
            shown = at_risk[:MAX_LOCATIONS]
            # 这是有意拒绝而非引擎故障：降级重算同样会解析外链并写成 #NAME?，
            # 因此绝不能借降级绕过本闸门。
            return {
                "error": (
                    "Refusing to recalculate: this workbook links to another workbook, and "
                    f"{len(at_risk)} linked cell(s) have lost their cached value (openpyxl strips "
                    "these on save). Recalculating would resolve them to #NAME? and delete the "
                    "external links for good. Copy those cells' values from the original file "
                    "before saving, or pass --force to accept the loss. Charts and conditional "
                    "formats can hold external references too, so this list may not be exhaustive."
                ),
                "external_link_cells": shown,
                "external_link_cells_truncated": max(0, len(at_risk) - len(shown)),
            }

    try:
        formula_count = _count_formulas(abs_path)
    except Exception as exc:  # noqa: BLE001
        return {"error": f"Failed to read workbook: {exc}"}

    if formula_count == 0:
        return {
            "status": "success",
            "total_errors": 0,
            "total_formulas": 0,
            "error_summary": {},
            "engine": "none",
        }

    # 第一层：LibreOffice（权威引擎）
    lo_error = _recalc_with_libreoffice(filename, abs_path, timeout)
    if lo_error is None:
        try:
            total_errors, error_summary = _scan_cached_errors(filename)
        except Exception as exc:  # noqa: BLE001
            return {"error": str(exc)}
        return {
            "status": "success" if total_errors == 0 else "errors_found",
            "total_errors": total_errors,
            "total_formulas": formula_count,
            "error_summary": error_summary,
            "engine": "libreoffice",
        }

    # 第二层：纯 Python formulas 引擎求值 + 回填缓存值
    fml_error, total_errors, error_summary = _recalc_with_formulas(
        abs_path, allow_install=allow_install
    )
    if fml_error is None:
        return {
            "status": "success" if total_errors == 0 else "errors_found",
            "total_errors": total_errors,
            "total_formulas": formula_count,
            "error_summary": error_summary,
            "engine": "formulas",
            "libreoffice_error": lo_error,
        }

    # 第三层

... [Content truncated, total 31,904 chars] ...