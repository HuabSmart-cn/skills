#!/usr/bin/env python3
"""Deterministically check literal delivery constraints and final claims.

The contract records only constraints explicitly requested by the user.
Supported checks:
  - required files and exact filenames
  - XLSX exact/required sheet names, exact headers, row counts, formulas, charts
  - DOCX required text and minimum table count
  - bounded item lists and required item fields
  - target eligibility of recommendations
  - source/computed/artifact/summary value agreement
"""

import argparse
import csv
import json
import math
import os
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

NS = {
    "m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
}


def norm(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def fail(errors):
    print(json.dumps({"ok": False, "errors": errors}, ensure_ascii=False, indent=2))
    raise SystemExit(2)


def shared_strings(zf):
    try:
        root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
    except KeyError:
        return []
    return ["".join(node.itertext()) for node in root.findall("m:si", NS)]


def cell_position(reference):
    match = re.fullmatch(r"([A-Z]+)(\d+)", reference or "")
    if not match:
        raise ValueError(f"invalid cell reference: {reference}")
    col = 0
    for char in match.group(1):
        col = col * 26 + ord(char) - 64
    return int(match.group(2)) - 1, col - 1


def workbook_info(path):
    with zipfile.ZipFile(path) as zf:
        root = ET.fromstring(zf.read("xl/workbook.xml"))
        rels = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
        targets = {
            node.attrib["Id"]: node.attrib["Target"]
            for node in rels
        }
        strings = shared_strings(zf)
        sheets = {}
        for sheet in root.find("m:sheets", NS):
            name = sheet.attrib["name"]
            target = targets[sheet.attrib[f"{{{NS['r']}}}id"]]
            target = target.lstrip("/")
            if not target.startswith("xl/"):
                target = "xl/" + target
            xml = ET.fromstring(zf.read(target))
            rows = []
            formulas = []
            formula_cells = {}
            cells = {}
            for row in xml.findall(".//m:sheetData/m:row", NS):
                row_cells = {}
                for cell in row.findall("m:c", NS):
                    kind = cell.attrib.get("t")
                    value_node = cell.find("m:v", NS)
                    inline = cell.find("m:is", NS)
                    formula = cell.find("m:f", NS)
                    if formula is not None:
                        formulas.append(cell.attrib.get("r", ""))
                    if inline is not None:
                        value = "".join(inline.itertext())
                    elif value_node is None:
                        value = ""
                    elif kind == "s":
                        value = strings[int(value_node.text)]
                    else:
                        value = value_node.text or ""
                    row_index, col_index = cell_position(cell.attrib.get("r", ""))
                    if formula is not None:
                        formula_cells[(row_index, col_index)] = norm(formula.text)
                    row_cells[col_index] = norm(value)
                    cells[(row_index, col_index)] = norm(value)
                if row_cells:
                    values = [""] * (max(row_cells) + 1)
                    for col_index, value in row_cells.items():
                        values[col_index] = value
                else:
                    values = []
                rows.append(values)
            sheets[name] = {
                "rows": rows,
                "formulas": formulas,
                "formula_cells": formula_cells,
                "cells": cells,
            }
        charts = sum(
            1 for name in zf.namelist()
            if name.startswith("xl/charts/chart") and name.endswith(".xml")
        )
    return {"sheets": sheets, "charts": charts}


def docx_info(path):
    with zipfile.ZipFile(path) as zf:
        root = ET.fromstring(zf.read("word/document.xml"))
    text = "\n".join(
        norm("".join(node.itertext()))
        for node in root.findall(".//w:p", NS)
        if norm("".join(node.itertext()))
    )
    return {"text": text, "tables": len(root.findall(".//w:tbl", NS))}


def formula_cell_position(reference):
    return cell_position(str(reference or "").replace("$", ""))


def numeric_cell_value(sheet, position, stack=None):
    stack = set(stack or ())
    if position in stack:
        raise ValueError("circular formula reference")
    raw = sheet["cells"].get(position, "")
    if raw != "":
        return float(str(raw).replace(",", ""))
    formula = sheet.get("formula_cells", {}).get(position, "")
    formula = str(formula or "").lstrip("=").strip()
    round_match = re.fullmatch(r"ROUND\((.+),\s*(-?\d+)\)", formula, re.IGNORECASE)
    digits = None
    if round_match:
        formula = round_match.group(1).strip()
        digits = int(round_match.group(2))
    match = re.fullmatch(
        r"\s*(\$?[A-Z]+\$?\d+)\s*([+\-*/])\s*(\$?[A-Z]+\$?\d+)\s*",
        formula,
    )
    if not match:
        raise ValueError(f"unsupported or empty formula at {position}: {formula!r}")
    left = numeric_cell_value(
        sheet, formula_cell_position(match.group(1)), stack | {position}
    )
    right = numeric_cell_value(
        sheet, formula_cell_position(match.group(3)), stack | {position}
    )
    result = {
        "+": left + right,
        "-": left - right,
        "*": left * right,
        "/": left / right,
    }[match.group(2)]
    return round(result, digits) if digits is not None else result


def canonical_metric_label(value):
    text = norm(value).lower()
    text = re.sub(r"[（(][^）)]*[）)]", "", text)
    text = re.sub(r"[\s_:：/]+", "", text)
    text = re.sub(r"^总(?=(消耗|点击|曝光|引入|转化|订单|金额|数量))", "", text)
    return text


def authoritative_two_column_metrics(info):
    metrics = {}
    for sheet_name, sheet in info["sheets"].items():
        rows = sheet["rows"]
        if not rows or len(rows[0]) < 2:
            continue
        if canonical_metric_label(rows[0][0]) != "指标":
            continue
        if canonical_metric_label(rows[0][1]) not in {"数值", "值"}:
            continue
        for row_index, row in enumerate(rows[1:], 1):
            if len(row) < 2 or not norm(row[0]):
                continue
            try:
                value = numeric_cell_value(sheet, (row_index, 1))
            except (ValueError, ZeroDivisionError):
                continue
            label = canonical_metric_label(row[0])
            metrics.setdefault(label, []).append((sheet_name, value, norm(row[0])))
    return metrics


def output_metric_values(info, labels):
    found = {}
    for sheet_name, sheet in info["sheets"].items():
        for position, value in sheet["cells"].items():
            label = canonical_metric_label(value)
            if label not in labels:
                continue
            try:
                metric_value = numeric_cell_value(sheet, (position[0], position[1] + 1))
            except (ValueError, ZeroDivisionError):
                continue
            found.setdefault(label, []).append((sheet_name, metric_value, norm(value)))
    return found


def validate_authoritative_metrics(contract_base, source_specs, output_specs, errors):
    source_metrics = {}
    for spec in source_specs:
        path = contract_base / spec["path"]
        if path.suffix.lower() != ".xlsx":
            continue
        try:
            metrics = authoritative_two_column_metrics(workbook_info(path))
        except (OSError, KeyError, ValueError, zipfile.BadZipFile, ET.ParseError) as exc:
            errors.append(f"authoritative source scan failed for {spec['path']}: {exc}")
            continue
        for label, values in metrics.items():
            source_metrics.setdefault(label, []).extend(values)
    unambiguous = {
        label: values[0]
        for label, values in source_metrics.items()
        if len(values) == 1
    }
    if not unambiguous:
        return
    for spec in output_specs:
        path = contract_base / spec["path"]
        if path.suffix.lower() != ".xlsx" or not path.is_file():
            continue
        try:
            found = output_metric_values(workbook_info(path), set(unambiguous))
        except (OSError, KeyError, ValueError, zipfile.BadZipFile, ET.ParseError) as exc:
            errors.append(f"output metric scan failed for {spec['path']}: {exc}")
            continue
        for label, values in found.items():
            source_sheet, source_value, source_label = unambiguous[label]
            for output_sheet, output_value, output_label in values:
                tolerance = max(1e-9, abs(source_value) * 1e-9)
                if abs(output_value - source_value) > tolerance:
                    errors.append(
                        "authoritative metric mismatch: "
                        f"{spec['path']}!{output_sheet} {output_label!r}={output_value} "
                        f"but source {source_sheet} {source_label!r}={source_value}"
                    )


def source_lookup(contract_base, lookup):
    path = contract_base / lookup["path"]
    info = workbook_info(path)
    sheet_name = lookup.get("sheet")
    candidates = []
    for name, sheet in info["sheets"].items():
        if sheet_name and name != sheet_name:
            continue
        for position, value in sheet["cells"].items():
            if norm(value) == norm(lookup["label"]):
                candidates.append((name, position))
    if len(candidates) != 1:
        raise ValueError(
            f"source label {lookup.get('label')!r} matched {len(candidates)} cells"
        )
    name, (row, col) = candidates[0]
    offset = lookup.get("value_offset", [0, 1])
    value = info["sheets"][name]["cells"].get((row + int(offset[0]), col + int(offset[1])), "")
    if value == "":
        raise ValueError(f"source value adjacent to {lookup.get('label')!r} is empty")
    try:
        return float(value)
    except ValueError:
        return value


def tabular_records(contract_base, source):
    path = contract_base / source["path"]
    kind = source.get("type", path.suffix.lower().lstrip("."))
    if kind == "csv":
        encoding = source.get("encoding", "utf-8-sig")
        with open(path, encoding=encoding, newline="") as handle:
            return list(csv.DictReader(handle))
    if kind == "xlsx":
        info = workbook_info(path)
        sheet_name = source.get("sheet")
        if sheet_name not in info["sheets"]:
            raise ValueError(f"target source sheet not found: {sheet_name!r}")
        rows = [row for row in info["sheets"][sheet_name]["rows"] if any(row)]
        header_row = int(source.get("header_row", 1)) - 1
        if len(rows) <= header_row:
            raise ValueError("target source header row is missing")
        headers = rows[header_row]
        records = []
        for row in rows[header_row + 1:]:
            padded = row + [""] * max(0, len(headers) - len(row))
            records.append(dict(zip(headers, padded)))
        return records
    raise ValueError(f"unsupported target source type: {kind!r}")


def predicate_matches(value, predicate):
    operation = predicate.get("op", "regex")
    if operation == "regex":
        return re.search(predicate["pattern"], norm(value), re.IGNORECASE) is not None
    if operation == "not_regex":
        return re.search(predicate["pattern"], norm(value), re.IGNORECASE) is None
    if operation == "equals":
        return norm(value) == norm(predicate.get("value"))
    if operation == "in":
        return norm(value) in {norm(item) for item in predicate.get("values", [])}
    if operation in {"min", "max", "between"}:
        number = float(str(value).replace(",", ""))
        if operation == "min":
            return number >= float(predicate["value"])
        if operation == "max":
            return number <= float(predicate["value"])
        return float(predicate["min"]) <= number <= float(predicate["max"])
    raise ValueError(f"unsupported target predicate operation: {operation!r}")


def artifact_lookup_matches(contract_base, lookup, source_display_value):
    path = contract_base / lookup["path"]
    info = workbook_info(path)
    sheet_name = lookup.get("sheet")
    if sheet_name not in info["sheets"]:
        raise ValueError(f"recommendation artifact sheet not found: {sheet_name!r}")
    search_value = norm(source_display_value)
    if not search_value:
        raise ValueError("recommendation source display value is empty")
    match_mode = lookup.get("match", "contains")
    matches = []
    for position, value in info["sheets"][sheet_name]["cells"].items():
        cell_value = norm(value)
        if (
            (match_mode == "contains" and search_value in cell_value)
            or (match_mode == "equals" and search_value == cell_value)
        ):
            matches.append(position)
    if not matches:
        raise ValueError(
            f"{search_value!r} not found in final recommendation area {sheet_name!r}"
        )
    return matches


def decision_sheet_candidates(path):
    """Return sheets whose names explicitly denote final actions or advice."""
    info = workbook_info(path)
    pattern = re.compile(
        r"(建议|决策|行动|策略|recommend(?:ation)?s?|decision|action)",
        re.IGNORECASE,
    )
    return [name for name in info["sheets"] if pattern.search(norm(name))]


def numeric_intervals(text):
    """Extract explicit closed numeric ranges from one decision row."""
    pattern = re.compile(
        r"(?<![\d.])(\d+(?:\.\d+)?)\s*(?:-|–|—|~|～|至|到)\s*"
        r"(\d+(?:\.\d+)?)(?![\d.])"
    )
    intervals = []
    for lower, upper in pattern.findall(norm(text)):
        lo, hi = float(lower), float(upper)
        interval = (min(lo, hi), max(lo, hi))
        if interval not in intervals:
            intervals.append(interval)
    return intervals


def interval_overlap(left, right):
    return max(left[0], right[0]) < min(left[1], right[1])


def validate_decision_output(contract_base, decision_output, errors):
    """Check that the declared area is the actual advice area and is coherent."""
    path = contract_base / decision_output["path"]
    try:
        candidates = decision_sheet_candidates(path)
        info = workbook_info(path)
    except (OSError, KeyError, ValueError, zipfile.BadZipFile, ET.ParseError) as exc:
        errors.append(f"decision output lookup failed: {exc}")
        return
    declared = decision_output["sheet"]
    if len(candidates) == 1 and declared != candidates[0]:
        errors.append(
            f"decision_output points to {declared!r}, but the workbook's unique "
            f"explicit decision/advice sheet is {candidates[0]!r}"
        )
        return
    if declared not in info["sheets"]:
        errors.append(f"decision output sheet not found: {declared!r}")
        return

    negative_words = re.compile(
        r"(避开|避免|不建议|不进入|停止|淘汰|排除|"
        r"\bavoid\b|\bexclude\b|\bdo\s+not\b|\bstop\b)",
        re.IGNORECASE,
    )
    positive_words = re.compile(
        r"(入门|品质|主推|优先|推荐|进入|布局|定价|"
        r"\brecommend\b|\benter\b|\btarget\b|\bfocus\b)",
        re.IGNORECASE,
    )
    negative, positive = [], []
    for row in info["sheets"][declared]["rows"]:
        row_text = " | ".join(norm(value) for value in row if norm(value))
        intervals = numeric_intervals(row_text)
        if not intervals:
            continue
        if negative_words.search(row_text):
            negative.extend((interval, row_text) for interval in intervals)
        elif positive_words.search(row_text):
            positive.extend((interval, row_text) for interval in intervals)
    reported = set()
    for neg_interval, neg_text in negative:
        for pos_interval, pos_text in positive:
            key = (neg_interval, pos_interval, neg_text, pos_text)
            if interval_overlap(neg_interval, pos_interval) and key not in reported:
                reported.add(key)
                errors.append(
                    "decision contradiction: an avoid/exclude range "
                    f"{neg_interval} overlaps a recommended/target range "
                    f"{pos_interval}; revise the final decision instead of "
                    f"leaving both claims. Negative row={neg_text!r}; "
                    f"positive row={pos_text!r}"
                )


def validate_recommendations(contract_base, target_scope, recommendations, errors):
    scope_markers = (
        "decision_target_quote",
        "source",
        "predicates",
        "decision_output",
        "target_subset",
        "decisions",
    )
    declared_scope = any(target_scope.get(key) for key in scope_markers)
    if target_scope.get("required") is False and declared_scope:
        errors.append(
            "target_scope cannot be disabled after target-specific scope or "
            "decision evidence has been declared; fix the evidence/output instead"
        )
    if not recommendations:
        if target_scope.get("required") is True or declared_scope:
            errors.append(
                "target-specific scope is declared but recommendations are empty; "
                "do not remove recommendations to bypass validation"
            )
        return
    source = target_scope.get("source") if isinstance(target_scope, dict) else None
    predicates = target_scope.get("predicates", []) if isinstance(target_scope, dict) else []
    if target_scope.get("required") is True and (not isinstance(source, dict) or not predicates):
        errors.append(
            "required target_scope must include source and machine-checkable predicates"
        )
        return
    decision_quote = norm(target_scope.get("decision_target_quote"))
    if target_scope.get("required") is True and not decision_quote:
        errors.append("required target_scope must include decision_target_quote")
        return
    decision_output = target_scope.get("decision_output")
    if target_scope.get("required") is True and not isinstance(decision_output, dict):
        errors.append(
            "required target_scope must include one decision_output for the area "
            "that directly answers the decision question"
        )
        return
    if isinstance(decision_output, dict):
        if not norm(decision_output.get("path")) or not norm(decision_output.get("sheet")):
            errors.append("target_scope.decision_output requires path and sheet")
            return
        validate_decision_output(contract_base, decision_output, errors)
    for predicate in predicates:
        source_quote = norm(predicate.get("source_quote"))
        if not source_quote:
            errors.append("each target predicate must include source_quote")
        elif source_quote not in decision_quote:
            errors.append(
                f"target predicate quote {source_quote!r} is not part of "
                "decision_target_quote; ranking/filter rules cannot replace target eligibility"
            )
    if not source:
        return
    key_field = source.get("key_field")
    if not norm(key_field):
        errors.append("target_scope.source.key_field is required")
        return
    display_field = source.get("display_field")
    if not norm(display_field):
        errors.append("target_scope.source.display_field is required")
        return
    try:
        records = tabular_records(contract_base, source)
    except (OSError, KeyError, ValueError, zipfile.BadZipFile, ET.ParseError) as exc:
        errors.append(f"target source lookup failed: {exc}")
        return
    for item in recommendations:
        item_id = item.get("id", "?")
        key_value = item.get("key_value")
        if not norm(key_value):
            errors.append(f"recommendation {item_id}: key_value is required")
            continue
        matches = [row for row in records if norm(row.get(key_field)) == norm(key_value)]
        if len(matches) != 1:
            errors.append(
                f"recommendation {item_id}: source key matched {len(matches)} rows"
            )
            continue
        row = matches[0]
        for predicate in predicates:
            field = predicate.get("field")
            if not norm(field):
                errors.append(f"recommendation {item_id}: predicate field is missing")
                continue
            try:
                passed = predicate_matches(row.get(field, ""), predicate)
            except (KeyError, TypeError, ValueError, re.error) as exc:
                errors.append(f"recommendation {item_id}: invalid predicate: {exc}")
                continue
            if not passed:
                errors.append(
                    f"recommendation {item_id}: source field {field!r} "
                    f"value {row.get(field, '')!r} fails target predicate"
                )
        try:
            artifact_lookup_matches(
                contract_base, decision_output, row.get(display_field, "")
            )
        except (OSError, KeyError, ValueError, zipfile.BadZipFile, ET.ParseError) as exc:
            errors.append(f"recommendation {item_id}: artifact lookup failed: {exc}")

    subset = target_scope.get("target_subset")
    if target_scope.get("required") is True and not isinstance(subset, dict):
        errors.append(
            "required target_scope must include target_subset evidence before decisions"
        )
    elif isinstance(subset, dict):
        if not norm(subset.get("path")) or not norm(subset.get("sheet")):
            errors.append("target_scope.target_subset requires path and sheet")
        if int(subset.get("rows", 0)) <= 0:
            errors.append("target_scope.target_subset rows must be positive")

    decisions = target_scope.get("decisions", [])
    if target_scope.get("required") is True and not decisions:
        errors.append(
            "required target_scope must register every final target-specific "
            "range, tier, avoid, and recommendation decision"
        )
    for decision in decisions:
        decision_id = decision.get("id", "?")
        if decision.get("basis_scope") != "target_subset":
            errors.append(
                f"decision {decision_id}: basis_scope must be target_subset"
            )
        if not norm(decision.get("evidence")):
            errors.append(f"decision {decision_id}: target-subset evidence is required")


def compare_values(claim, errors, contract_base):
    label = claim.get("label", "unnamed claim")
    tolerance = claim.get("tolerance", 0)
    values = [claim.get(k) for k in ("source_value", "computed_value", "artifact_value", "summary_value")]
    if any(v is None for v in values):
        errors.append(f"{label}: missing one of source/computed/artifact/summary values")
        return
    authority = claim.get("authority", "source_field")
    if authority == "source_field":
        lookup = claim.get("source_lookup")
        if not isinstance(lookup, dict):
            errors.append(f"{label}: source_field claim requires source_lookup")
            return
        try:
            actual_source = source_lookup(contract_base, lookup)
        except (OSError, KeyError, ValueError, zipfile.BadZipFile, ET.ParseError) as exc:
            errors.append(f"{label}: source lookup failed: {exc}")
            return
        if isinstance(actual_source, (int, float)) and isinstance(values[0], (int, float)):
            if abs(float(actual_source) - float(values[0])) > tolerance:
                errors.append(
                    f"{label}: registered source_value {values[0]!r} "
                    f"!= actual source value {actual_source!r}"
                )
                return
        elif norm(actual_source) != norm(values[0]):
            errors.append(
                f"{label}: registered source_value {values[0]!r} "
                f"!= actual source value {actual_source!r}"
            )
            return
        anchor = actual_source
    else:
        anchor = values[1]
    for value in values:
        if isinstance(anchor, (int, float)) and isinstance(value, (int, float)):
            if not math.isfinite(float(value)) or abs(float(anchor) - float(value)) > tolerance:
                errors.append(f"{label}: cross-layer mismatch {values}")
                return
        elif norm(anchor) != norm(value):
            errors.append(f"{label}: cross-layer mismatch {values}")
            return


CN_DIGITS = {
    "零": 0,
    "一": 1,
    "二": 2,
    "两": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
}


def explicit_count(value):
    text 

... [Content truncated, total 37,709 chars] ...