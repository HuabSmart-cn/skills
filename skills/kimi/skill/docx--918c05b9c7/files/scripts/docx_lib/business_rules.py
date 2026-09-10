"""
business_rules.py - Package checks and conservative fixes not covered by XSD.

Checks:
  - gridCol/tcW width consistency (table not skewed)
  - Image cx/cy proportional scaling (not distorted)
  - Comments file and document anchor sync integrity
  - Section margin heuristic
  - mc:Ignorable namespace consistency
  - Bookmark/comment marker ID uniqueness

Auto-fixes:
  - Absolute → relative relationship paths
  - Content type normalization
"""

import random
import struct
from pathlib import Path
from xml.etree import ElementTree as ET

from .constants import A_NS, R_NS, W14_NS, W15_NS, W_NS, WP_NS

RELS_NS = 'http://schemas.openxmlformats.org/package/2006/relationships'
CT_NS = 'http://schemas.openxmlformats.org/package/2006/content-types'
MC_NS = 'http://schemas.openxmlformats.org/markup-compatibility/2006'
W16CID_NS = 'http://schemas.microsoft.com/office/word/2016/wordml/cid'
W16CEX_NS = 'http://schemas.microsoft.com/office/word/2018/wordml/cex'
OFFICE_DOC_REL = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument'
IMAGE_REL = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/image'
COMMENTS_REL = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments'
COMMENTS_EXT_REL = 'http://schemas.microsoft.com/office/2011/relationships/commentsExtended'
COMMENTS_IDS_REL = 'http://schemas.microsoft.com/office/2016/09/relationships/commentsIds'
COMMENTS_EXTENSIBLE_REL = 'http://schemas.microsoft.com/office/2018/08/relationships/commentsExtensible'
PEOPLE_REL = 'http://schemas.microsoft.com/office/2011/relationships/people'

_LATIN_ONLY_FONT_NAMES = {
    'arial',
    'calibri',
    'cambria',
    'courier new',
    'georgia',
    'helvetica',
    'times new roman',
    'verdana',
}


def _contains_cjk(text):
    return any(
        '\u3400' <= char <= '\u4dbf'
        or '\u4e00' <= char <= '\u9fff'
        or '\uf900' <= char <= '\ufaff'
        for char in text
    )


def check_cjk_run_fonts(root):
    """Warn when an explicitly-fonted CJK run cannot select a CJK face."""
    missing_east_asia = 0
    latin_east_asia = {}
    for run in root.findall('.//{%s}r' % W_NS):
        text = ''.join(node.text or '' for node in run.findall('.//{%s}t' % W_NS))
        if not _contains_cjk(text):
            continue
        run_properties = run.find('{%s}rPr' % W_NS)
        if run_properties is None:
            continue
        fonts = run_properties.find('{%s}rFonts' % W_NS)
        if fonts is None:
            continue
        east_asia = (fonts.get('{%s}eastAsia' % W_NS) or '').strip()
        if not east_asia:
            missing_east_asia += 1
        elif east_asia.casefold() in _LATIN_ONLY_FONT_NAMES:
            latin_east_asia[east_asia] = latin_east_asia.get(east_asia, 0) + 1

    warnings = []
    if missing_east_asia:
        warnings.append(
            f"DOCX_FONT: {missing_east_asia} explicitly-fonted CJK run(s) omit w:eastAsia; "
            "declare a CJK font or verify the intended style inheritance"
        )
    for font_name, count in sorted(latin_east_asia.items()):
        warnings.append(
            f"DOCX_FONT: {count} CJK run(s) explicitly set w:eastAsia='{font_name}', "
            "a Latin-only font; use an explicit CJK eastAsia face"
        )
    return warnings


def check_table_grid_consistency(root):
    """Check table gridCol and tcW width consistency.

    Args:
        root: ElementTree root of document.xml

    Returns:
        List of error strings
    """
    errors = []
    tables = root.findall('.//{%s}tbl' % W_NS)

    for tbl_idx, tbl in enumerate(tables, 1):
        tbl_grid = tbl.find('{%s}tblGrid' % W_NS)
        if tbl_grid is None:
            errors.append(f"TABLE[{tbl_idx}]: missing tblGrid (required for proper rendering)")
            continue

        grid_cols = tbl_grid.findall('{%s}gridCol' % W_NS)
        grid_widths = []
        for gc in grid_cols:
            w_val = gc.get('{%s}w' % W_NS)
            try:
                grid_widths.append(int(w_val) if w_val else None)
            except ValueError:
                grid_widths.append(None)

        first_row = tbl.find('{%s}tr' % W_NS)
        if first_row is None:
            continue

        cells = first_row.findall('{%s}tc' % W_NS)
        col_idx = 0
        for cell in cells:
            if col_idx >= len(grid_widths):
                break
            tc_pr = cell.find('{%s}tcPr' % W_NS)
            if tc_pr is None:
                col_idx += 1
                continue

            tc_w = tc_pr.find('{%s}tcW' % W_NS)
            if tc_w is None:
                col_idx += 1
                continue

            tc_type = tc_w.get('{%s}type' % W_NS)
            if tc_type not in (None, '', 'dxa'):
                col_idx += 1
                continue

            span_count = 1
            grid_span = tc_pr.find('{%s}gridSpan' % W_NS)
            if grid_span is not None:
                try:
                    span_count = int(grid_span.get('{%s}val' % W_NS, '1'))
                except ValueError:
                    span_count = 1

            if col_idx + span_count > len(grid_widths):
                break
            expected_widths = grid_widths[col_idx:col_idx + span_count]
            if any(w is None for w in expected_widths):
                col_idx += span_count
                continue
            expected_width = sum(expected_widths)

            tc_width = tc_w.get('{%s}w' % W_NS)
            if tc_width and expected_width:
                try:
                    tc_width_int = int(tc_width)
                except ValueError:
                    errors.append(f"TABLE[{tbl_idx}]: tc[{col_idx}].tcW is not numeric")
                    col_idx += span_count
                    continue
                if abs(tc_width_int - expected_width) > expected_width * 0.05:
                    errors.append(
                        f"TABLE[{tbl_idx}]: gridCol[{col_idx}..{col_idx + span_count - 1}] sum={expected_width} != tc[{col_idx}].tcW={tc_width_int} (will skew)"
                    )
            col_idx += span_count

    return errors


def _parse_xml(path):
    try:
        return ET.parse(path), None
    except ET.ParseError as exc:
        return None, f"XML: {path.name}: {exc}"


def get_image_dimensions(data):
    """Read actual image dimensions from binary data (supports PNG/JPEG).

    Args:
        data: bytes - Raw image file data

    Returns:
        Tuple (width, height) or (None, None) if unable to parse
    """
    try:
        if data[:8] == b'\x89PNG\r\n\x1a\n':
            width, height = struct.unpack('>II', data[16:24])
            return width, height

        if data[:2] == b'\xff\xd8':
            i = 2
            while i < len(data) - 9:
                if data[i] == 0xff:
                    marker = data[i+1]
                    if marker in (0xc0, 0xc2):
                        height, width = struct.unpack('>HH', data[i+5:i+9])
                        return width, height
                    elif marker == 0xd9:
                        break
                    elif marker in (0xd0, 0xd1, 0xd2, 0xd3, 0xd4, 0xd5, 0xd6, 0xd7, 0x01, 0x00):
                        i += 2
                    else:
                        length = struct.unpack('>H', data[i+2:i+4])[0]
                        i += 2 + length
                else:
                    i += 1
    except Exception:
        pass
    return None, None


def check_image_aspect_ratio(root, extract_dir):
    """Check if image display dimensions match actual image file aspect ratio.

    Args:
        root: ElementTree root of document.xml
        extract_dir: Path to extracted docx directory

    Returns:
        List of error strings
    """
    errors = []
    extract_dir = Path(extract_dir)

    # Parse document.xml.rels
    rels_map = {}
    rels_path = extract_dir / 'word' / '_rels' / 'document.xml.rels'
    if rels_path.exists():
        rels_tree = ET.parse(rels_path)
        rels_root = rels_tree.getroot()
        for rel in rels_root.findall('.//{http://schemas.openxmlformats.org/package/2006/relationships}Relationship'):
            rid = rel.get('Id')
            target = rel.get('Target')
            if rid and target:
                if not target.startswith('/'):
                    target = 'word/' + target
                else:
                    target = target[1:]
                rels_map[rid] = target

    drawings = root.findall('.//{%s}drawing' % W_NS)

    for img_idx, drawing in enumerate(drawings, 1):
        extent = drawing.find('.//{%s}extent' % WP_NS)
        if extent is None:
            continue

        cx = extent.get('cx')
        cy = extent.get('cy')
        if not cx or not cy:
            continue

        cx_val = int(cx)
        cy_val = int(cy)
        if cy_val == 0:
            continue

        display_ratio = cx_val / cy_val

        blip = drawing.find('.//{%s}blip' % A_NS)
        if blip is None:
            continue

        embed_id = blip.get('{%s}embed' % R_NS)
        if not embed_id or embed_id not in rels_map:
            continue

        image_path = extract_dir / rels_map[embed_id]
        if not image_path.exists():
            continue

        data = image_path.read_bytes()
        actual_width, actual_height = get_image_dimensions(data)
        if actual_width is None or actual_height is None or actual_height == 0:
            continue

        actual_ratio = actual_width / actual_height

        if abs(display_ratio - actual_ratio) / actual_ratio > 0.05:
            filename = image_path.name
            errors.append(
                f"IMAGE[{img_idx}] {filename}: display={display_ratio:.2f} != actual={actual_ratio:.2f} (distorted)"
            )

    return errors


def check_comments_integrity(extract_dir):
    """Check comments 4-file sync integrity.

    Args:
        extract_dir: Path to extracted docx directory

    Returns:
        List of error strings
    """
    errors = []
    extract_dir = Path(extract_dir)

    has_comments = (extract_dir / 'word' / 'comments.xml').exists()
    has_comments_extended = (extract_dir / 'word' / 'commentsExtended.xml').exists()
    has_comments_ids = (extract_dir / 'word' / 'commentsIds.xml').exists()
    has_comments_extensible = (extract_dir / 'word' / 'commentsExtensible.xml').exists()

    if has_comments:
        comments_tree, parse_error = _parse_xml(extract_dir / 'word' / 'comments.xml')
        if parse_error:
            return [f"XML: word/comments.xml: {parse_error.split(': ', 1)[-1]}"]
        comments_root = comments_tree.getroot()
        comments = comments_root.findall('.//{%s}comment' % W_NS)

        comment_ids = {}
        comment_para_ids = set()
        for idx, comment in enumerate(comments):
            comment_id = comment.get('{%s}id' % W_NS)
            if comment_id:
                if comment_id in comment_ids:
                    errors.append(
                        f"COMMENTS: duplicate comment w:id='{comment_id}' (first at index {comment_ids[comment_id]})"
                    )
                else:
                    comment_ids[comment_id] = idx

            para = comment.find('{%s}p' % W_NS)
            if para is not None:
                para_id = para.get('{%s}paraId' % W14_NS)
                if para_id:
                    comment_para_ids.add(para_id)

        if comment_para_ids:
            if not has_comments_extended:
                errors.append("COMMENTS: has threaded replies but missing commentsExtended.xml")
            if not has_comments_ids:
                errors.append("COMMENTS: has threaded replies but missing commentsIds.xml")

            if has_comments_extended:
                ext_tree, parse_error = _parse_xml(extract_dir / 'word' / 'commentsExtended.xml')
                if parse_error:
                    errors.append(f"XML: word/commentsExtended.xml: {parse_error.split(': ', 1)[-1]}")
                    ext_tree = None
                if ext_tree is not None:
                    ext_root = ext_tree.getroot()
                    ext_para_ids = set()
                    for idx, elem in enumerate(ext_root.findall('.//{%s}commentEx' % W15_NS)):
                        para_id = elem.get('{%s}paraId' % W15_NS)
                        if para_id:
                            if para_id in ext_para_ids:
                                errors.append(f"COMMENTS: duplicate commentsExtended paraId '{para_id}'")
                            else:
                                ext_para_ids.add(para_id)
                    for para_id in sorted(comment_para_ids - ext_para_ids):
                        errors.append(f"COMMENTS: commentsExtended.xml missing paraId '{para_id}'")
                    for para_id in sorted(ext_para_ids - comment_para_ids):
                        errors.append(f"COMMENTS: commentsExtended.xml has orphan paraId '{para_id}'")

                    for elem in ext_root.findall('.//{%s}commentEx' % W15_NS):
                        parent_id = elem.get('{%s}paraIdParent' % W15_NS)
                        if parent_id and parent_id not in comment_para_ids:
                            errors.append(
                                f"COMMENTS: commentsExtended.xml paraIdParent '{parent_id}' has no matching comment"
                            )

            if has_comments_ids:
                ids_tree, parse_error = _parse_xml(extract_dir / 'word' / 'commentsIds.xml')
                if parse_error:
                    errors.append(f"XML: word/commentsIds.xml: {parse_error.split(': ', 1)[-1]}")
                    ids_tree = None
                if ids_tree is not None:
                    ids_root = ids_tree.getroot()
                    ids_para_ids = {
                        elem.get('{%s}paraId' % W16CID_NS)
                        for elem in ids_root.findall('.//{%s}commentId' % W16CID_NS)
                        if elem.get('{%s}paraId' % W16CID_NS)
                    }
                    durable_ids = {}
                    durable_ids_by_para_id = {}
                    for idx, elem in enumerate(ids_root.findall('.//{%s}commentId' % W16CID_NS)):
                        para_id = elem.get('{%s}paraId' % W16CID_NS)
                        durable_id = elem.get('{%s}durableId' % W16CID_NS)
                        if durable_id:
                            if durable_id in durable_ids:
                                errors.append(f"COMMENTS: duplicate durableId '{durable_id}'")
                            else:
                                durable_ids[durable_id] = idx
                            if para_id:
                                durable_ids_by_para_id[para_id] = durable_id
                    for para_id in sorted(comment_para_ids - ids_para_ids):
                        errors.append(f"COMMENTS: commentsIds.xml missing paraId '{para_id}'")
                    for para_id in sorted(ids_para_ids - comment_para_ids):
                        errors.append(f"COMMENTS: commentsIds.xml has orphan paraId '{para_id}'")

                    if has_comments_extensible:
                        cex_tree, parse_error = _parse_xml(extract_dir / 'word' / 'commentsExtensible.xml')
                        if parse_error:
                            errors.append(f"XML: word/commentsExtensible.xml: {parse_error.split(': ', 1)[-1]}")
                        else:
                            cex_ids = set()
                            for elem in cex_tree.getroot().findall('.//{%s}commentExtensible' % W16CEX_NS):
                                durable_id = elem.get('{%s}durableId' % W16CEX_NS)
                                if durable_id:
                                    if durable_id in cex_ids:
                                        errors.append(f"COMMENTS: duplicate commentsExtensible durableId '{durable_id}'")
                                    else:
                                        cex_ids.add(durable_id)
                            known_durable_ids = set(durable_ids)
                            for durable_id in sorted(cex_ids - known_durable_ids):
                                errors.append(f"COMMENTS: commentsExtensible.xml has orphan durableId '{durable_id}'")
                            for durable_id in sorted(known_durable_ids - cex_ids):
                                errors.append(f"COMMENTS: commentsExtensible.xml missing durableId '{durable_id}'")

    return errors


def check_section_margins(root):
    """Check section margins for potential issues.

    Detects:
    - Zero margins on non-cover/backcover sections (likely bug)
    - Last section with zero margins affecting body content

    Args:
        root: ElementTree root of document.xml

    Returns:
        List of warning strings
    """
    warnings = []

    # Find all sectPr elements
    # sectPr can be in: body > sectPr (last section) or p > pPr > sectPr (section breaks)
    body = root.find('.//{%s}body' % W_NS)
    if body is None:
        return warnings

    sections = []

    # Section breaks within paragraphs
    for para in body.findall('.//{%s}p' % W_NS):
        pPr = para.find('{%s}pPr' % W_NS)
        if pPr is not None:
            sectPr = pPr.find('{%s}sectPr' % W_NS)
            if sectPr is not None:
                sections.append(('inline', sectPr))

    # Final section at body end
    final_sectPr = body.find('{%s}sectPr' % W_NS)
    if final_sectPr is not None:
        sections.append(('final', final_sectPr))

    if len(sections) < 2:
        # Single section document, no issue
        return warnings

    # Check each section's margins
    MIN_MARGIN_TWIPS = 360  # 0.25 inch minimum for body content

    for idx, (sect_type, sectPr) in enumerate(sections):
        pgMar = sectPr.find('{%s}pgMar' % W_NS)
        if pgMar is None:
            continue

        # Get margin values
        margins = {
            'top': pgMar.get('{%s}top' % W_NS, '1440'),
            'bottom': pgMar.get('{%s}bottom' % W_NS, '1440'),
            'left': pgMar.get('{%s}left' % W_NS, '1440'),
            'right': pgMar.get('{%s}right' % W_NS, '1440'),
        }

        # Convert to int, handle negative values
        try:
            margin_values = {k: abs(int(v)) for k, v in margins.items()}
        except ValueError:
            continue

        # Check if all margins are zero or very small
        all_zero = all(v < MIN_MARGIN_TWIPS for v in margin_values.values())

        if all_zero:
            # First section (cover) and last section (backcover) can have zero margins
            is_first = (idx == 0)
            is_last = (idx == len(sections) - 1 and sect_type == 'final')

            if is_last and len(sections) > 2:
                # Final section with zero margins might affect preceding content
                # if there are sections between first and last without their own sectPr
                warnings.append(
                    "MARGIN: final section has zero margins - may affect body content if intermediate sections lack sectPr"
                )
            elif not is_first and not is_last:
                # Middle section with zero margins is likely a bug
                warnings.append(
                    f"MARGIN: section[{idx+1}] has zero margins (top={margin_values['top']}, left={margin_values['left']}) - body content may touch page edges"
                )

    return warnings


def check_namespace_declarations(extract_dir):
    """Check that mc:Ignorable namespace prefixes are declared on the root element.

    Args:
        extract_dir: Path to extracted docx directory

    Returns:
        List of error strings
    """
    import re
    errors = []
    extract_dir = Path(extract_dir)

    xml_files = [
        extract_dir / 'word' / 'document.xml',
        extract_dir / 'word' / 'styles.xml',
        extract_dir / 'word' / 'settings.xml',
    ]

    for xml_path in xml_files:
        if not xml_path.exists():
            continue

        try:
            tree = ET.parse(xml_path)
        except ET.ParseError:
            continue

        root = tree.getroot()
        ignorable = root.get(f'{{{MC_NS}}}Ignorable', '')
        if not ignorable:
            continue

        # ET doesn't expose xmlns declarations, parse raw XML header
        declared_prefixes = set()
        try:
            raw = xml_path.read_bytes()[:4096].decode('utf-8', errors='replace')
            root_match = re.search(r'<\w+:?\w+\s([^>]+?)/?>', raw)
            if root_match:
                for m in re.finditer(r'xmlns:(\w+)\s*=\s*"[^"]*"', root_match.group(1)):
                    declared_prefixes.add(m.group(1))
        except Exception:
            continue

        for prefix in ignorable.split():
            if prefix not in declared_prefixes:
                fname = xml_path.relative_to(extract_dir)
                errors.append(
                    f"NAMESPACE: {fname} mc:Ignorable lists '{prefix}' but xmlns:{prefix} not declared"
                )

    return errors


def check_id_uniqueness(root):
    """Check that bookmark and comment marker IDs are unique.

    Args:
        root: ElementTree root of document.xml

    Returns:
        List of error strings
    """
    errors = []

    for elem_name in ('bookmarkStart', 'bookmarkEnd', 'commentRangeStart', 'commentRangeEnd', 'commentReference'):
        seen = {}
        for elem in root.iter(f'{{{W_NS}}}{elem_name}'):
            id_val = elem.get(f'{{{W_NS}}}id')
            if id_val is None:
                continue
            if id_val in seen:
                errors.append(
                    f"ID: duplicate {elem_name} w:id='{id_val}' (first at index {seen[id_val]})"
                )
            else:
                seen[id_val] = len(seen)

    return errors


# ============================================================
# OPC package-level auto-fixes
# ============================================================

_PART_CONTENT_TYPES = {
    '/word/document.xml': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml',
    '/word/styles.xml': 'application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml',
    '/word/settings.xml': 'application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml',
    '/word/numbering.xml': 'application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml',
    '/word/footnotes.xml': 'application/vnd.openxmlformats-officedocument.wordprocessingml.footnotes+xml',
    '/word/endnotes.xml': 'application/vnd.openxmlformats-officedocument.wordprocessingml.endnotes+xml',
    '/word/comments.xml': 'application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml',
    '/word/commentsExtended.xml': 'application/vnd.openxmlformats-officedocument.wordprocessingml.commentsExtended+xml',
    '/word/commentsIds.xml': 'application/vnd.openxmlformats-officedocument.wordprocessingml.commentsIds+xml',
    '/word/commentsExtensible.xml': 'application/vnd.openxmlformats-officedocument.wordprocessingml.commentsExtensible+xml',
    '/word/fontTable.xml': 'application/vnd.openxmlformats-officedocument.wordprocessingml.fontTable+xml',
    '/word/theme/theme1.xml': 'application/vnd.openxmlformats-officedocument.theme+xml',
    '/docProps/core.xml': 'application/vnd.openxmlformats-package.core-properties+xml',
    '/docProps/app.xml': 'application/vnd.openxmlformats-officedocument.extended-properties+xml',
}


def fix_relationship_paths(extract_dir):
    """Convert absolute relationship targets to relative paths.

    OOXML (ECMA-376 Part 2) requires relative paths in .rels files.
    Some SDK versions generate absolute paths (starting with '/'),
    which Word rejects but WPS tolerates.

    Returns:
        Number of fixes made
    """
    fixes = 0
    extract_dir = Path(extract_dir)

    for rels_path in extract_dir.rglob('*.rels'):
        try:
            tree = ET.parse(rels_path)
        except ET.ParseError:
            continue

        modified = False
        rels_dir = rels_path.parent.parent

        for rel in tree.getroot():
            if rel.tag != f'{{{RELS_NS}}}Relationship':
                continue

            target = rel.get('Target', '')
            target_mode = rel.get('TargetMode', '')

            if target_mode == 'External' or not target.startswith('/'):
                continue

            abs_path = target[1:]
            try:
                target_full = extract_dir / abs_path
                rel_path = target_full.relative_to(rels_dir)
                new_target = str(rel_path).replace('\\', '/')
            except ValueError:
                new_target = abs_path

            rel.set('Target', new_target)
            modified = True
            fixes += 1

        if modified:
            ET.register_namespace('', RELS_NS)
            tree.write(rels_path, encoding='UTF-8', xml_declaration=True)

    return fixes


def fix_content_types(extract_dir):
    """Normal

... [Content truncated, total 47,534 chars] ...