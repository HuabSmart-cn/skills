#!/usr/bin/env python3
"""Read-only DOCX QA audit for journal-format runs.

The audit intentionally stays structural. Rendering is handled by render_docx.py.
This script records the package evidence needed to catch common regressions:
section/page layout drift, direct formatting that can override role styles,
numbering/style references, and media/OLE/relationship preservation.
"""

import argparse
import json
import os
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter

W_NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
R_NS = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
PKG_REL_NS = 'http://schemas.openxmlformats.org/package/2006/relationships'
WP_NS = 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing'
A_NS = 'http://schemas.openxmlformats.org/drawingml/2006/main'
M_NS = 'http://schemas.openxmlformats.org/officeDocument/2006/math'

NS = {
    'w': W_NS,
    'r': R_NS,
    'pr': PKG_REL_NS,
    'wp': WP_NS,
    'a': A_NS,
    'm': M_NS,
}

EMU_PER_INCH = 914400

HEADING_STYLE_RE = re.compile(r'^(?:heading|head)\s*([1-9])$|^(?:[678]heading)([1-3])$', re.I)
NUMBERED_HEADING_RE = re.compile(r'^\s*(\d+(?:\.\d+)*)\s+\S+')
FIELD_UPDATE_TYPES = {'PAGE', 'NUMPAGES', 'TOC', 'REF', 'PAGEREF', 'SEQ'}

KEY_PARTS = [
    '[Content_Types].xml',
    'word/document.xml',
    'word/styles.xml',
    'word/numbering.xml',
    'word/settings.xml',
    'word/fontTable.xml',
    'word/theme/theme1.xml',
]


def qn(ns, local):
    return f'{{{ns}}}{local}'


def read_xml(zf, name):
    try:
        return ET.fromstring(zf.read(name))
    except KeyError:
        return None


def attr(el, local, default=None):
    if el is None:
        return default
    return el.get(qn(W_NS, local), default)


def para_text(p):
    return ''.join(t.text or '' for t in p.findall('.//w:t', NS))


def local_name(tag):
    return tag.split('}', 1)[-1] if '}' in tag else tag


def attrs_dict(el):
    if el is None:
        return {}
    return {local_name(k): v for k, v in el.attrib.items()}


def xml_child_profile(parent, child_name):
    child = parent.find(f'w:{child_name}', NS) if parent is not None else None
    return attrs_dict(child)


def paragraph_style_id(p):
    p_pr = p.find('w:pPr', NS)
    p_style = p_pr.find('w:pStyle', NS) if p_pr is not None else None
    return attr(p_style, 'val', '')


def load_style_spacing_map(styles_root):
    if styles_root is None:
        return {}
    result = {}
    for style in styles_root.findall('w:style', NS):
        if attr(style, 'type') != 'paragraph':
            continue
        style_id = attr(style, 'styleId')
        if not style_id:
            continue
        p_pr = style.find('w:pPr', NS)
        spacing = p_pr.find('w:spacing', NS) if p_pr is not None else None
        if spacing is not None:
            result[style_id] = attrs_dict(spacing)
    return result


def paragraph_high_inline_content_kinds(p):
    kinds = set()
    for node in p.iter():
        lname = local_name(node.tag)
        if lname in ('drawing', 'pict'):
            kinds.add(lname)
        elif lname in ('object', 'OLEObject', 'objectEmbed', 'control'):
            kinds.add('ole_object')
        elif lname in ('oMath', 'oMathPara') or node.tag.startswith(f'{{{M_NS}}}'):
            kinds.add('omml')
    return sorted(kinds)


def effective_spacing_attrs(p, style_spacing_map):
    p_pr = p.find('w:pPr', NS)
    direct = p_pr.find('w:spacing', NS) if p_pr is not None else None
    if direct is not None:
        return attrs_dict(direct), 'direct'
    style_id = paragraph_style_id(p)
    if style_id and style_spacing_map.get(style_id):
        return dict(style_spacing_map[style_id]), f'style:{style_id}'
    return {}, None


def inches_from_emu(value):
    if value in (None, ''):
        return None
    try:
        return round(int(value) / EMU_PER_INCH, 3)
    except Exception:
        return None


def heading_level_from_style(style_id):
    if not style_id:
        return None
    normalized = re.sub(r'[\s_\-]+', '', style_id).lower()
    match = re.search(r'heading([1-9])$', normalized) or re.search(r'head([1-9])$', normalized)
    if match:
        return int(match.group(1))
    match = re.match(r'[678]heading([1-3])$', normalized)
    if match:
        return int(match.group(1))
    return None


def numbered_heading_level(text):
    match = NUMBERED_HEADING_RE.match(text or '')
    if not match:
        return None
    return match.group(1).count('.') + 1


def iter_paragraphs(root):
    if root is None:
        return []
    return root.findall('.//w:p', NS)


def iter_content_parts(zf):
    for name in zf.namelist():
        if not name.startswith('word/') or not name.endswith('.xml'):
            continue
        base = name.rsplit('/', 1)[-1]
        if base == 'document.xml':
            yield name
        elif base.startswith('header') and base.endswith('.xml'):
            yield name
        elif base.startswith('footer') and base.endswith('.xml'):
            yield name
        elif base in ('footnotes.xml', 'endnotes.xml'):
            yield name


def rels_path_for_part(part_name):
    directory, base = part_name.rsplit('/', 1)
    return f'{directory}/_rels/{base}.rels'


def load_rels_map(zf, part_name):
    rels_name = rels_path_for_part(part_name)
    if rels_name not in zf.namelist():
        return {}
    try:
        root = ET.fromstring(zf.read(rels_name))
    except Exception:
        return {}
    rels = {}
    for rel in root.findall(f'{{{PKG_REL_NS}}}Relationship'):
        rid = rel.get('Id')
        target = rel.get('Target')
        rel_type = rel.get('Type')
        if rid:
            rels[rid] = {'target': target, 'type': rel_type}
    return rels


def section_audit(doc_root):
    sections = []
    if doc_root is None:
        return sections
    for idx, sect in enumerate(doc_root.findall('.//w:sectPr', NS), start=1):
        pg_sz = sect.find('w:pgSz', NS)
        pg_mar = sect.find('w:pgMar', NS)
        cols = sect.find('w:cols', NS)
        header_refs = sect.findall('w:headerReference', NS)
        footer_refs = sect.findall('w:footerReference', NS)
        sections.append({
            'index': idx,
            'page_size': {
                'w': attr(pg_sz, 'w'),
                'h': attr(pg_sz, 'h'),
                'orient': attr(pg_sz, 'orient'),
            },
            'margins': {
                key: attr(pg_mar, key)
                for key in ('top', 'right', 'bottom', 'left', 'header', 'footer', 'gutter')
            },
            'columns': {
                'num': attr(cols, 'num', '1'),
                'space': attr(cols, 'space'),
                'equalWidth': attr(cols, 'equalWidth'),
            },
            'headers': [
                {'type': attr(h, 'type'), 'rid': h.get(qn(R_NS, 'id'))}
                for h in header_refs
            ],
            'footers': [
                {'type': attr(f, 'type'), 'rid': f.get(qn(R_NS, 'id'))}
                for f in footer_refs
            ],
        })
    return sections


def formatting_audit(doc_root):
    paragraphs = list(iter_paragraphs(doc_root))
    direct_paragraphs = 0
    direct_runs = 0
    style_counts = Counter()
    font_counts = Counter()
    numbered_paragraphs = 0
    examples = {
        'direct_paragraph_formatting': [],
        'direct_run_formatting': [],
        'heading_like_not_heading_style': [],
    }

    for idx, p in enumerate(paragraphs, start=1):
        text = para_text(p).strip()
        p_pr = p.find('w:pPr', NS)
        p_style = p_pr.find('w:pStyle', NS) if p_pr is not None else None
        style_id = attr(p_style, 'val', '')
        if style_id:
            style_counts[style_id] += 1
        direct_p = False
        if p_pr is not None:
            for tag in ('w:ind', 'w:spacing', 'w:jc', 'w:tabs', 'w:pBdr', 'w:shd'):
                if p_pr.find(tag, NS) is not None:
                    direct_p = True
                    break
            if p_pr.find('w:numPr', NS) is not None:
                numbered_paragraphs += 1
                direct_p = True
        if direct_p:
            direct_paragraphs += 1
            if len(examples['direct_paragraph_formatting']) < 12:
                examples['direct_paragraph_formatting'].append({
                    'paragraph_index': idx,
                    'style_id': style_id,
                    'text': text[:120],
                })

        heading_like = (
            text
            and len(text) <= 90
            and not re.search(r'[。.;；]$', text)
            and re.match(r'^(?:\d+(?:\.\d+)*\s+|[一二三四五六七八九十]+、|[（(]?[一二三四五六七八九十]+[）)]).+', text)
        )
        if heading_like and not re.search(r'heading|head|title', style_id, re.I):
            if len(examples['heading_like_not_heading_style']) < 12:
                examples['heading_like_not_heading_style'].append({
                    'paragraph_index': idx,
                    'style_id': style_id,
                    'text': text[:120],
                })

        for r in p.findall('w:r', NS):
            r_pr = r.find('w:rPr', NS)
            if r_pr is None:
                continue
            r_text = ''.join(t.text or '' for t in r.findall('.//w:t', NS)).strip()
            direct_r = False
            for child in list(r_pr):
                local = child.tag.split('}')[-1]
                if local in ('rFonts', 'sz', 'szCs', 'b', 'i', 'color', 'u', 'vertAlign', 'position', 'spacing', 'highlight', 'shd'):
                    direct_r = True
                if local == 'rFonts':
                    for key in ('ascii', 'hAnsi', 'eastAsia', 'cs', 'asciiTheme', 'hAnsiTheme', 'eastAsiaTheme'):
                        value = attr(child, key)
                        if value:
                            font_counts[value] += max(len(r_text), 1)
            if direct_r:
                direct_runs += 1
                if len(examples['direct_run_formatting']) < 12:
                    examples['direct_run_formatting'].append({
                        'paragraph_index': idx,
                        'run_text': r_text[:80],
                    })

    return {
        'paragraph_count': len(paragraphs),
        'numbered_paragraphs': numbered_paragraphs,
        'direct_paragraph_formatting_paragraphs': direct_paragraphs,
        'direct_run_formatting_runs': direct_runs,
        'styles_by_paragraph_count': dict(style_counts.most_common(25)),
        'fonts_by_direct_run_char_count': dict(font_counts.most_common(25)),
        'examples': examples,
    }


def border_profile(container, path):
    borders = container.find(path, NS) if container is not None else None
    if borders is None:
        return {}
    return {
        side: attrs_dict(borders.find(f'w:{side}', NS))
        for side in ('top', 'bottom', 'left', 'right', 'insideH', 'insideV')
        if borders.find(f'w:{side}', NS) is not None
    }


def border_is_visible(attrs):
    val = (attrs or {}).get('val')
    return bool(val and val not in ('nil', 'none'))


def cell_border_profile(tc):
    tc_pr = tc.find('w:tcPr', NS) if tc is not None else None
    return border_profile(tc_pr, 'w:tcBorders')


def cell_grid_span(tc):
    tc_pr = tc.find('w:tcPr', NS) if tc is not None else None
    grid_span = tc_pr.find('w:gridSpan', NS) if tc_pr is not None else None
    try:
        return max(1, int(attr(grid_span, 'val', '1') or '1'))
    except Exception:
        return 1


def cell_has_vertical_merge(tc):
    tc_pr = tc.find('w:tcPr', NS) if tc is not None else None
    return tc_pr is not None and tc_pr.find('w:vMerge', NS) is not None


def row_effective_column_count(tr):
    return sum(cell_grid_span(tc) for tc in tr.findall('w:tc', NS))


def row_has_merge_topology(tr):
    return any(
        cell_grid_span(tc) > 1 or cell_has_vertical_merge(tc)
        for tc in tr.findall('w:tc', NS)
    )


def row_cell_texts(tr):
    return [para_text(tc).strip() for tc in tr.findall('w:tc', NS)]


def text_looks_numeric_data(text):
    compact = re.sub(r'\s+', '', text or '')
    if not compact:
        return False
    if re.fullmatch(r'[+-]?\d+(?:\.\d+)?%?', compact):
        return True
    if re.fullmatch(r'[+-]?\d+(?:\.\d+)?(?:±|~|-|—|–|至|到)[+-]?\d+(?:\.\d+)?%?', compact):
        return True
    if re.fullmatch(r'[×xX√/\\-]+', compact):
        return True
    return False


def row_feature_for_header_inference(row, max_cols):
    texts = row_cell_texts(row)
    nonempty = [text for text in texts if text]
    cell_count = max(1, len(texts))
    avg_cell_len = sum(len(text) for text in nonempty) / max(1, len(nonempty))
    numeric_cells = sum(1 for text in nonempty if text_looks_numeric_data(text))
    numeric_ratio = numeric_cells / float(max(1, len(nonempty)))
    text = ' '.join(nonempty)
    labelish_re = re.compile(
        r'^(Top\s*\d+|Acc(?:uracy)?|Precision|Recall|F1|AP|mAP|P@\d+|R@\d+|'
        r'准确率|精确率|召回率|分类方法|姿态维度|目标|指标|方法|维度|类别|模型|数据集|'
        r'均值|标准差|Mean|Std\.?|Dataset|Method|Metric|Category|Dimension)$',
        re.I,
    )
    labelish_cells = sum(1 for text in nonempty if labelish_re.match(text.strip()))
    has_sentence_punct = bool(re.search(r'[。；;.!?？]', text))
    return {
        'text': text,
        'nonempty_cells': len(nonempty),
        'cell_count': cell_count,
        'effective_cols': row_effective_column_count(row),
        'max_cols': max_cols,
        'avg_cell_len': avg_cell_len,
        'numeric_cells': numeric_cells,
        'numeric_ratio': numeric_ratio,
        'labelish_ratio': labelish_cells / float(max(1, len(nonempty))),
        'has_merge_topology': row_has_merge_topology(row),
        'has_spanning_group_cell': any(cell_grid_span(tc) > 1 for tc in row.findall('w:tc', NS)),
        'raw_cell_count_below_grid': cell_count < max_cols,
        'has_sentence_punct': has_sentence_punct,
        'is_short_label_row': bool(nonempty) and avg_cell_len <= 18 and not has_sentence_punct,
        'is_data_like': (
            numeric_cells >= 2
            or numeric_ratio >= 0.5
            or (numeric_cells >= 1 and avg_cell_len > 18)
        ),
    }


def infer_three_line_header_row_info(rows):
    if len(rows) <= 1:
        return {'count': 1 if rows else 0, 'features': [], 'reason': 'single_or_empty_table'}
    max_cols = max(row_effective_column_count(row) for row in rows) or 1
    features = [row_feature_for_header_inference(row, max_cols) for row in rows[: min(4, len(rows))]]
    header_count = 1
    reasons = ['first_row_header']
    for idx, feature in enumerate(features[1:], start=1):
        if idx >= len(rows) - 1:
            break
        if not feature['text']:
            continue
        prev = features[idx - 1] if idx - 1 < len(features) else {}
        next_feature = features[idx + 1] if idx + 1 < len(features) else {}
        merge_continuation = bool(prev.get('has_merge_topology') or feature['has_merge_topology'])
        grouped_header_continuation = (
            feature['is_short_label_row']
            and (
                merge_continuation
                or prev.get('has_spanning_group_cell')
                or prev.get('raw_cell_count_below_grid')
            )
            and (
                not next_feature
                or next_feature.get('is_data_like')
                or next_feature.get('avg_cell_len', 99) > feature.get('avg_cell_len', 0)
            )
        )
        likely_subheader = (
            feature['is_short_label_row']
            and (
                merge_continuation
                or feature['labelish_ratio'] >= 0.5
                or (next_feature and next_feature.get('is_data_like') and feature['numeric_cells'] == 0)
                or grouped_header_continuation
            )
        )
        if likely_subheader:
            header_count = idx + 1
            reasons.append(f'row_{idx}_subheader')
            continue
        if feature['is_data_like']:
            reasons.append(f'row_{idx}_data_like_stop')
        break
    return {
        'count': max(1, min(header_count, len(rows) - 1)),
        'features': features,
        'reason': ','.join(reasons),
    }


def visible_cell_side_count(row, side):
    count = 0
    cells = row.findall('w:tc', NS)
    for tc in cells:
        if border_is_visible(cell_border_profile(tc).get(side)):
            count += 1
    return count


def visible_cell_vertical_border_count(rows):
    count = 0
    for row in rows:
        for tc in row.findall('w:tc', NS):
            borders = cell_border_profile(tc)
            if any(border_is_visible(borders.get(side)) for side in ('left', 'right', 'insideV')):
                count += 1
    return count


def audit_three_line_border_integrity(rows, borders):
    if not rows:
        return []
    issues = []
    header_info = infer_three_line_header_row_info(rows)
    header_rows = header_info.get('count') or 1
    header_bottom_index = max(0, header_rows - 1)
    first_cells = rows[0].findall('w:tc', NS)
    header_bottom_cells = rows[header_bottom_index].findall('w:tc', NS)
    final_cells = rows[-1].findall('w:tc', NS)
    visible_vertical = any(border_is_visible(borders.get(side)) for side in ('left', 'right', 'insideV')) or visible_cell_vertical_border_count(rows)
    visible_horizontal = any(border_is_visible(borders.get(side)) for side in ('top', 'bottom', 'insideH')) or any(
        visible_cell_side_count(row, 'top') or visible_cell_side_count(row, 'bottom')
        for row in rows
    )
    likely_three_line = visible_horizontal and not visible_vertical
    if not likely_three_line:
        return []
    if first_cells and not border_is_visible(borders.get('top')) and visible_cell_side_count(rows[0], 'top') < len(first_cells):
        issues.append({
            'type': 'three_line_top_rule_incomplete',
            'message': 'possible three-line table is missing complete first-row top cell borders',
            'expected_cells': len(first_cells),
            'visible_cells': visible_cell_side_count(rows[0], 'top'),
        })
    if header_bottom_cells and visible_cell_side_count(rows[header_bottom_index], 'bottom') < len(header_bottom_cells):
        issues.append({
            'type': 'three_line_header_bottom_rule_incomplete',
            'message': 'possible three-line table is missing the bottom rule under the final inferred header row',
            'header_rows': header_rows,
            'header_inference_reason': header_info.get('reason'),
            'expected_cells': len(header_bottom_cells),
            'visible_cells': visible_cell_side_count(rows[header_bottom_index], 'bottom'),
        })
    if header_rows > 1:
        for sep_idx in range(0, header_bottom_index):
            cells = rows[sep_idx].findall('w:tc', NS)
            if cells and visible_cell_side_count(rows[sep_idx], 'bottom') < len(cells):
                issues.append({
                    'type': 'three_line_multi_header_separator_incomplete',
                    'message': 'multi-row header lacks a horizontal separator between header levels',
                    'separator_after_row': sep_idx + 1,
                    'header_rows': header_rows,
                    'expected_cells': len(cells),
                    'visible_cells': visible_cell_side_count(rows[sep_idx], 'bottom'),
                })
    if final_cells and not border_is_visible(borders.get('bottom')) and visible_cell_side_count(rows[-1], 'bottom') < len(final_cells):
        issues.append({
            'type': 'three_line_bottom_rule_incomplete',
            'message': 'possible three-line table is missing complete final-row bottom cell borders',
            'expected_cells': len(final_cells),
            'visible_cells': visible_cell_side_count(rows[-1], 'bottom'),
        })
    return issues


def table_geometry_audit(doc_root):
    if doc_root is None:
        return {'table_count': 0, 'issue_count': 0, 'issues': [], 'tables': []}
    tables = []
    issues = []
    for table_idx, tbl in enumerate(doc_root.findall('.//w:tbl', NS), start=1):
        tbl_pr = tbl.find('w:tblPr', NS)
        tbl_grid = tbl.find('w:tblGrid', NS)
        rows = tbl.findall('w:tr', NS)
        grid = [
            int(col.get(qn(W_NS, 'w'), '0') or '0')
            for col in (tbl_grid.findall('w:gridCol', NS) if tbl_grid is not None else [])
        ]
        tbl_w = xml_child_profile(tbl_pr, 'tblW')
        tbl_ind = xml_child_profile(tbl_pr, 'tblInd')
        tbl_layout = xml_child_profile(tbl_pr, 'tblLayout')
        tbl_cell_mar = attrs_dict(tbl_pr.find('w:tblCellMar', NS)) if tbl_pr is not None and tbl_pr.find('w:tblCellMar', NS) is not None else {}
        table_issues = []
        width_value = int(tbl_w.get('w', '0') or '0') if tbl_w else 0
        width_type = tbl_w.get('type')
        if width_type in ('dxa', 'pct') and width_value and grid and width_type == 'dxa':
            delta = abs(sum(grid) - width_value)
            if delta > 36:
                table_issues.append({
                    'type': 'grid_width_mismatch',
                    'message': 'tblGrid sum differs from explicit tblW',
                    'tblW': width_value,
                    'grid_sum': sum(grid),
                })
        if width_type in (None, 'auto') or width_value == 0:
            table_issues.append({
                'type': 'auto_or_missing_table_width',
                'message': 'table width is auto/missing; width may render differently across Word engines',
                'tblW': tbl_w,
            })
        row_profiles = []
        for row_idx, tr in enumerate(rows, start=1):
            cells = tr.findall('w:tc', NS)
            cell_widths = []
            merged_cells = 0
            tc_margin_profiles = []
            cell_border_count = 0
            for tc in cells:
                tc_pr = tc.find('w:tcPr', NS)
                tc_w = xml_child_profile(tc_pr, 'tcW')
                if tc_w:
                    try:
                        cell_widths.append(int(tc_w.get('w', '0') or '0'))
                    except Exception:
                        cell_widths.append(0)
                else:
                    cell_widths.append(0)
                if tc_pr is not None and any(tc_pr.find(f'w:{name}', NS) is not None for name in ('gridSpan', 'hMerge', 'vMerge')):
                    merged_cells += 1
                if tc_pr is not None and tc_pr.find('w:tcBorders', NS) is not None:
                    cell_border_count += 1
                tc_mar = tc_pr.find('w:tcMar', NS) if tc_pr is not None else None
                if tc_mar is not None:
                    tc_margin_profiles.append({
                        side: attrs_dict(tc_mar.find(f'w:{side}', NS))
                        for side in ('top', 'bottom', 'start', 'end', 'left', 'right')
                        if tc_mar.find(f'w:{side}', NS) is not None
                    })
            if grid and len(cell_widths) >= len(grid) and not merged_cells:
                comparable = cell_widths[:len(grid)]
                if any(abs((comparable[i] or 0) - grid[i]) > 36 for i in range(len(grid))):
                    table_issues.append({
                        'type': 'cell_width_grid_mismatch',
                        'message': 'row cell widths differ from tblGrid column widths',
                        'row': row_idx,
                        'grid': grid,
                        'cell_widths': comparable,
                    })
            row_profiles.append({
                'row': row_idx,
                'cells': len(cells),
                'merged_cells': merged_cells,
                'cell_widths': cell_widths[:12],
                'has_header_flag': tr.find('w:trPr/w:tblHeader', NS) is not None,
                'cell_border_count': cell_border_count,
                'cell_margin_profiles': tc_margin_profiles[:3],
            })
        borders = border_profile(tbl_pr, 'w:tblBorders')
        vertical_line_evidence = bool(
            borders.get('insideV') or borders.get('left') or borders.get('right') or
            any(r.get('cell_border_count') for r in row_profiles)
        )
        horizontal_line_evidence = bool(
            borders.get('top') or borders.get('bottom') or borders.get('insideH') or
            any(r.get('cell_border_count') for r in row_profiles)
        )
        if not borders and not any(r.get('cell_border_count') for r in row_profiles):
            table_issues.append({
                'type': 'no_explicit_table_borders',
                'message': 'table has no explicit tblBorders/tcBorders evidence',
            })
        table_issues.extend(audit_three_line_border_integrity(rows, borders))
        table_profile = {
            'index': table_idx,
            'rows': len(rows),
            'grid_columns': len(grid),
            'grid_widths': grid[:20],
            'grid_sum': sum(grid),
            'tblW': tbl_w,
            'tblInd': tbl_ind,
            'tblLay

... [Content truncated, total 39,057 chars] ...