#!/usr/bin/env python3
"""
Extract text-first PDF format evidence for DOCX formatting.

This script does not treat PDF as a Word template. It first checks whether the
PDF is a selectable-text format guide, such as author instructions or submission
guidelines. Explicit text rules are the only style rules written to rules JSON.
Coordinate/layout evidence may select the single-column or double-column
fallback variant, but it must not define fonts, sizes, color, spacing, or other
Word style properties.

- evidence JSON for audit/debug;
- optional rules JSON that can be passed to format_docx.py --rules-json.

Tools are optional and are used when available:
- PyMuPDF / fitz: span-level fonts, sizes, colors, flags, coordinates.
- pdfplumber: character/table-line evidence.
- pdftotext: layout text and text-extraction sanity check.
- pdffonts: embedded/substituted font inventory.
- mutool: structural metadata when available.
"""

import argparse
import collections
import json
import math
import os
import re
import shutil
import statistics
import subprocess
import sys


ROLE_ORDER = [
    'title',
    'author',
    'affiliation',
    'abstract',
    'keywords',
    'heading1',
    'heading2',
    'heading3',
    'body',
    'figure_caption',
    'table_caption',
    'references_heading',
    'reference_item',
    'equation',
    'english_title',
    'english_author',
    'english_affiliation',
    'english_abstract',
    'english_keywords',
]

TEXT_RULE_ROLE_ORDER = [
    'references_heading',
    'reference_item',
    'figure_caption',
    'table_caption',
    'english_keywords',
    'english_abstract',
    'english_title',
    'english_author',
    'english_affiliation',
    'metadata',
    'citation_format',
    'keywords',
    'abstract',
    'heading1',
    'heading2',
    'heading3',
    'title',
    'author',
    'affiliation',
    'body',
]

SIZE_MAP = {
    '初号': 84, '小初': 72, '一号': 52, '小一': 48, '二号': 44, '小二': 36,
    '三号': 32, '小三': 30, '四号': 28, '小四': 24, '五号': 21, '小五': 18,
    '六号': 15, '小六': 13, '七号': 11, '八号': 10,
}

FONT_WORDS = [
    'Times New Roman', 'Arial', 'Calibri', 'Cambria', 'Courier New',
    '宋体', '黑体', '楷体', '仿宋', '微软雅黑', 'SimSun', 'SimHei', 'KaiTi', 'FangSong',
]

FORMAT_GUIDE_MARKERS = [
    '投稿须知', '来稿要求', '投稿指南', '作者指南', '撰稿要求', '写作模板',
    '模板要求', '格式要求', '论文格式', '参考文献格式', '参考文献引用须知',
    'Instructions for Authors', 'Author Guidelines', 'Manuscript Preparation',
]

TEXT_RULE_MARKERS = [
    '正文', '题名', '标题', '摘要', '关键词', '作者', '单位', '图题', '图注',
    '表题', '表注', '参考文献', '三线表', '公式', '上标', '字号', '字体',
    '行距', '悬挂缩进', '首行缩进', 'Times New Roman', '宋体', '黑体',
]

DECORATIVE_WATERMARK_RE = re.compile(
    r'^(样\s*例|示\s*例|样\s*张|sample|draft|watermark|proof|copy)$',
    re.I,
)


def run_cmd(cmd, timeout=30):
    exe = shutil.which(cmd[0])
    if not exe:
        return {'available': False, 'command': cmd, 'output': '', 'error': 'not found'}
    try:
        result = subprocess.run(
            [exe] + cmd[1:],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
        )
        return {
            'available': True,
            'command': [exe] + cmd[1:],
            'returncode': result.returncode,
            'output': result.stdout,
            'error': result.stderr,
        }
    except Exception as exc:
        return {'available': True, 'command': [exe] + cmd[1:], 'output': '', 'error': str(exc)}


def safe_import(name):
    try:
        return __import__(name)
    except Exception:
        return None


def normalize_font_name(font):
    font = str(font or '').strip()
    if '+' in font and re.match(r'^[A-Z]{6}\+', font):
        font = font.split('+', 1)[1]
    replacements = {
        'TimesNewRomanPSMT': 'Times New Roman',
        'TimesNewRomanPS-BoldMT': 'Times New Roman',
        'TimesNewRomanPS-ItalicMT': 'Times New Roman',
        'TimesNewRomanPS-BoldItalicMT': 'Times New Roman',
        'TimesNewRoman': 'Times New Roman',
        'SimSun': '宋体',
        'SimSun-ExtB': '宋体',
        'SimHei': '黑体',
        'KaiTi': '楷体',
        'FangSong': '仿宋',
    }
    if font in replacements:
        return replacements[font]
    return font


def font_family(font):
    font = normalize_font_name(font)
    for token in ('-BoldItalic', '-BoldOblique', '-Italic', '-Oblique', '-Bold', ',Bold', ',Italic'):
        ***REDACTED***
    for token in ('BoldItalic', 'BoldOblique', 'Italic', 'Oblique', 'Bold'):
        ***REDACTED***
    return font.strip('- ,') or normalize_font_name(font)


def contains_cjk(text):
    return bool(re.search(r'[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]', text or ''))


def contains_latin(text):
    return bool(re.search(r'[A-Za-z]', text or ''))


def text_kind(text):
    if contains_cjk(text):
        return 'cjk'
    if contains_latin(text):
        return 'latin'
    return 'other'


def is_bold_font(font):
    return bool(re.search(r'(bold|black|heavy|semibold|demibold)', str(font or ''), re.I))


def is_italic_font(font):
    return bool(re.search(r'(italic|oblique)', str(font or ''), re.I))


def color_to_hex(value):
    if value is None:
        return None
    try:
        value = int(value)
    except Exception:
        return None
    return f'{value & 0xFFFFFF:06X}'


def clean_text(text):
    return re.sub(r'\s+', ' ', str(text or '')).strip()


def clean_pdf_text_for_rules(text):
    text = str(text or '').replace('\r', '\n')
    text = re.sub(r'[ \t]+', ' ', text)
    return re.sub(r'\n{3,}', '\n\n', text).strip()


def extract_plain_text_from_pymupdf(pdf_path, max_pages=None):
    fitz = safe_import('fitz')
    if fitz is None:
        return '', {'available': False, 'error': 'PyMuPDF/fitz not importable'}
    try:
        doc = fitz.open(pdf_path)
    except Exception as exc:
        return '', {'available': True, 'error': str(exc)}
    try:
        limit = min(len(doc), max_pages or len(doc))
        pages = []
        for idx in range(limit):
            pages.append(doc[idx].get_text('text') or '')
        text = clean_pdf_text_for_rules('\n'.join(pages))
        return text, {'available': True, 'page_count': len(doc), 'extracted_pages': limit, 'char_count': len(text)}
    finally:
        doc.close()


def split_rule_sentences(text):
    normalized = clean_pdf_text_for_rules(text)
    parts = re.split(r'(?<=[。！？；;])\s*|\n+', normalized)
    merged = []
    buf = ''
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if len(part) < 18 and re.match(r'^\d+(?:\.\d+)*\s*\S+', part):
            if buf:
                merged.append(buf.strip())
            buf = part
            continue
        if buf and len(buf) < 80:
            buf = f'{buf} {part}'
        else:
            if buf:
                merged.append(buf.strip())
            buf = part
    if buf:
        merged.append(buf.strip())
    return [item for item in merged if item]


def format_guide_score(text):
    haystack = text or ''
    marker_hits = sum(1 for marker in FORMAT_GUIDE_MARKERS if re.search(re.escape(marker), haystack, re.I))
    rule_hits = sum(1 for marker in TEXT_RULE_MARKERS if re.search(re.escape(marker), haystack, re.I))
    section_hits = len(re.findall(r'\b\d+(?:\.\d+)*\s*(?:来稿要求|插图|照片|表|公式|参考文献|摘要|关键词|题目|作者|单位)', haystack))
    return marker_hits * 3 + min(rule_hits, 12) + section_hits * 2


def normalize_text_for_rules(text):
    return re.sub(r'\s+', '', text or '').lower()


def role_from_text_rule(text):
    if re.search(
        r'^(?:author\s+guidelines|instructions?\s+for\s+authors?|author\s+instructions?|'
        r'manuscript\s+preparation|submission\s+guidelines?)\s*$',
        (text or '').strip(),
        re.I,
    ):
        return None
    normalized = normalize_text_for_rules(text)
    if any(key in normalized for key in ('文章正文', '正文', 'bodytext', 'maintext', 'mainbody')):
        return 'body'
    checks = [
        ('references_heading', ['参考文献标题', 'referencesheading']),
        ('reference_item', ['参考文献格式', '参考文献', 'references', '文献']),
        ('figure_caption', ['图题', '图注', 'figurecaption']),
        ('table_caption', ['表题', '表注', 'tablecaption']),
        ('english_keywords', ['英文关键词', 'englishkeywords']),
        ('english_abstract', ['英文摘要', 'englishabstract']),
        ('english_title', ['英文题名', '英文标题', 'englishtitle']),
        ('english_author', ['英文作者', 'englishauthor']),
        ('english_affiliation', ['英文单位', '英文机构', 'englishaffiliation']),
        ('metadata', ['中图分类号', '文献标志码', '文章编号', 'pacs']),
        ('citation_format', ['引用格式', 'citationformat']),
        ('keywords', ['关键词', '关键字', 'keywords']),
        ('abstract', ['摘要', 'abstract']),
        ('heading1', ['一级标题', '1级标题', 'heading1']),
        ('heading2', ['二级标题', '2级标题', 'heading2']),
        ('heading3', ['三级标题', '3级标题', 'heading3']),
        ('title', ['题名', '标题', '论文题目', '题目', 'title']),
        ('author', ['作者', 'author']),
        ('affiliation', ['单位', '机构', 'affiliation']),
        ('body', ['正文', '文章正文', 'body', 'maintext']),
    ]
    for role, keys in checks:
        if any(key.lower() in normalized for key in keys):
            return role
    return None


def parse_size_from_text_rule(text):
    for name, half_point in SIZE_MAP.items():
        if name in text:
            return str(half_point)
    arabic_size_map = {
        '0': 84, '1': 52, '2': 44, '3': 32, '4': 28,
        '5': 21, '6': 15, '7': 11, '8': 10,
    }
    match = re.search(r'(小)?\s*([1-8])\s*号', text)
    if match:
        small, num = match.groups()
        if small:
            small_map = {'1': 48, '2': 36, '3': 30, '4': 24, '5': 18, '6': 13}
            return str(small_map.get(num, arabic_size_map[num]))
        return str(arabic_size_map[num])
    match = re.search(r'(\d+(?:\.\d+)?)\s*(?:-|–|—)?\s*(?:pt|磅|point(?:s)?(?:\s+font)?)', text, re.I)
    if match:
        return str(int(round(float(match.group(1)) * 2)))
    return None


def parse_fonts_from_text_rule(text):
    fonts = {}
    for font in FONT_WORDS:
        if font.lower() not in text.lower():
            continue
        if re.search(r'(英|西|latin|ascii|hansi)[^。；;，,]{0,12}' + re.escape(font), text, re.I):
            fonts['ascii'] = font
            fonts['hAnsi'] = font
        elif re.search(re.escape(font) + r'[^。；;，,]{0,12}(英|西|latin|ascii|hansi)', text, re.I):
            fonts['ascii'] = font
            fonts['hAnsi'] = font
        elif re.search(r'(中|中文|汉字|eastAsia)[^。；;，,]{0,12}' + re.escape(font), text, re.I):
            fonts['eastAsia'] = font
        elif re.search(re.escape(font) + r'[^。；;，,]{0,12}(中|中文|汉字|eastAsia)', text, re.I):
            fonts['eastAsia'] = font
        elif re.search(r'[A-Za-z]', font):
            fonts.setdefault('ascii', font)
            fonts.setdefault('hAnsi', font)
        else:
            fonts.setdefault('eastAsia', font)
    return fonts


def parse_alignment_from_text_rule(text):
    if re.search(r'居中|居中对齐|align(?:ed|ment)?\s*[:=]?\s*center|center(?:ed)?\s+align', text, re.I):
        return 'center'
    if re.search(r'两端对齐|align(?:ed|ment)?\s*[:=]?\s*justify|justified', text, re.I):
        return 'both'
    if re.search(r'右对齐|居右|align(?:ed|ment)?\s*[:=]?\s*right|right(?:-|\s+)?align(?:ed|ment)?', text, re.I):
        return 'right'
    if re.search(r'左对齐|居左|align(?:ed|ment)?\s*[:=]?\s*left|left(?:-|\s+)?align(?:ed|ment)?', text, re.I):
        return 'left'
    return None


def parse_bold_from_text_rule(text):
    if re.search(r'不加粗|非加粗|not\s+bold', text, re.I):
        return False
    if re.search(r'加粗|bold', text, re.I):
        return True
    return None


def parse_line_spacing_from_text_rule(text):
    match = re.search(r'(?:固定值|exact(?:ly)?)\s*(\d+(?:\.\d+)?)\s*(?:磅|pt)', text, re.I)
    if match:
        return {'line': str(int(round(float(match.group(1)) * 20))), 'lineRule': 'exact'}
    match = re.search(r'(\d+(?:\.\d+)?)\s*(?:倍行距|倍)', text)
    if match:
        return {'line': str(int(round(float(match.group(1)) * 240))), 'lineRule': 'auto'}
    if re.search(r'1\.?5\s*(?:倍行距|倍)|一倍半', text):
        return {'line': '360', 'lineRule': 'auto'}
    if re.search(r'单倍行距|single\s+line', text, re.I):
        return {'line': '240', 'lineRule': 'auto'}
    return {}


def parse_indent_from_text_rule(text):
    if re.search(r'悬挂缩进\s*2\s*(?:字符|字)', text):
        return {'left': '420', 'hanging': '420'}
    match = re.search(r'悬挂缩进\s*(\d+(?:\.\d+)?)\s*(?:磅|pt)', text, re.I)
    if match:
        hanging = str(int(round(float(match.group(1)) * 20)))
        return {'left': hanging, 'hanging': hanging}
    if re.search(r'首行缩进\s*2\s*(?:字符|字)', text):
        return {'firstLine': '420'}
    match = re.search(r'首行缩进\s*(\d+(?:\.\d+)?)\s*(?:磅|pt)', text, re.I)
    if match:
        return {'firstLine': str(int(round(float(match.group(1)) * 20)))}
    return {}


def text_rule_has_format_property(text):
    return bool(
        parse_size_from_text_rule(text)
        or parse_fonts_from_text_rule(text)
        or parse_alignment_from_text_rule(text)
        or parse_bold_from_text_rule(text) is not None
        or parse_line_spacing_from_text_rule(text)
        or parse_indent_from_text_rule(text)
        or re.search(r'三线表|上标|公式.*编号|编号.*公式|图题|表题', text)
    )


def merge_rule_property(current, key, value):
    if isinstance(value, dict) and isinstance(current.get(key), dict):
        current[key].update(value)
    else:
        current[key] = value


def merge_rule_into_role(roles, role, rule):
    current = roles.setdefault(role, {})
    for key, value in (rule or {}).items():
        merge_rule_property(current, key, value)


def merge_visual_supplement_into_text_rules(text_rules, visual_rules):
    merged = json.loads(json.dumps(text_rules or {}, ensure_ascii=False))
    supplement = {}
    # Coarse visual may identify roles and broad alignment only. Typography,
    # emphasis, indentation, and spacing must come from explicit text rules
    # or fallback.
    allowed_visual_keys = {'align'}
    for role, visual_rule in (visual_rules or {}).items():
        current = merged.setdefault(role, {})
        role_supplement = {}
        for key, value in (visual_rule or {}).items():
            if key in ('source', 'confidence'):
                continue
            if key not in allowed_visual_keys:
                continue
            if key not in current and value not in (None, ''):
                current[key] = value
                role_supplement[key] = value
        if role_supplement:
            if not current.get('source'):
                current['source'] = 'pdf_visual_supplement'
            if current.get('source') == 'pdf_visual_supplement':
                current['confidence'] = 'low'
            current.setdefault('visual_supplement', {}).update(role_supplement)
            supplement[role] = role_supplement
    return merged, supplement


def parse_prose_rule_sentence(sentence):
    role = role_from_text_rule(sentence)
    if not role or not text_rule_has_format_property(sentence):
        return None, None
    rule = {'source': 'pdf_text_rules', 'confidence': 'medium'}
    size = parse_size_from_text_rule(sentence)
    fonts = parse_fonts_from_text_rule(sentence)
    align = parse_alignment_from_text_rule(sentence)
    bold = parse_bold_from_text_rule(sentence)
    line_spacing = parse_line_spacing_from_text_rule(sentence)
    indent = parse_indent_from_text_rule(sentence)
    if size:
        rule['size'] = size
    if fonts:
        rule['fonts'] = fonts
    if align:
        rule['align'] = align
    if bold is not None:
        rule['bold'] = bold
    if line_spacing:
        rule['spacing'] = line_spacing
    if indent:
        rule['indent'] = indent
    if role == 'table_caption' and re.search(r'表.*(上方|上面|置于表上)', sentence):
        rule['caption_position'] = 'above'
    if role == 'figure_caption' and re.search(r'图.*(下方|下面|置于图下)', sentence):
        rule['caption_position'] = 'below'
    return role, rule


def add_multi_role_text_rules(sentence, roles, matched):
    if re.search(r'图题.*表题|表题.*图题|图和表|图、表|图表', sentence):
        shared = {'source': 'pdf_text_rules', 'confidence': 'medium'}
        if re.search(r'中英文对照|中、英文对照|Chinese\s+and\s+English', sentence, re.I):
            shared['bilingual'] = True
        if len(shared) > 2:
            for role in ('figure_caption', 'table_caption'):
                merge_rule_into_role(roles, role, shared)
            matched.append({
                'role': 'figure_caption/table_caption',
                'text': sentence[:500],
                'rule': shared,
            })
    if re.search(r'表采用三线表|三线表', sentence):
        merge_rule_into_role(roles, 'table_caption', {'source': 'pdf_text_rules', 'confidence': 'medium'})


def parse_structural_postprocess_rule(sentence):
    text = sentence or ''
    normalized = re.sub(r'\s+', ' ', text).strip()
    clauses = [
        clause.strip()
        for clause in re.split(r'(?<=[。；;])\s*|(?<=[.!?])\s+(?=[A-Z])', text)
        if clause.strip()
    ] or [text]
    structural = {}
    operations = []

    def add_structural(section, key, value):
        structural.setdefault(section, {})[key] = value

    def add_op(op):
        op.setdefault('source', 'explicit_pdf_text_rule')
        op.setdefault('source_text', normalized[:500])
        operations.append(op)

    if re.search(r'(tables?|表(?:格)?)[^。；;]{0,80}(after|following|at\s+the\s+end|参考文献后|文后|置于文后|放在文后)', text, re.I) or re.search(r'(after|following)[^。；;]{0,40}(references?)[^。；;]{0,40}(tables?)', text, re.I):
        add_structural('placement', 'tables_after_references', True)
        add_op({'type': 'move_tables_after_references', 'include_caption': True})
    if re.search(r'(figures?|illustrations?|图(?:片|件)?)[^。；;]{0,80}(after|following|at\s+the\s+end|参考文献后|文后|置于文后|放在文后)', text, re.I) or re.search(r'(after|following)[^。；;]{0,40}(references?)[^。；;]{0,40}(figures?)', text, re.I):
        add_structural('placement', 'figures_after_references', True)
        add_op({'type': 'move_figures_after_references', 'include_caption': True})

    if re.search(r'(citation|reference citation|引用|引文|文献标注|参考文献.*引用)', text, re.I):
        citation_rule = {}
        if re.search(r'(within|in|用|置于)?\s*(parentheses|round brackets|圆括号|圆括弧|小括号)|\(\s*\d+\s*\)', text, re.I):
            citation_rule['marker'] = 'parentheses'
        if re.search(r'italic|italics|斜体', text, re.I):
            citation_rule['italic'] = True
        if re.search(r'superscript|上标', text, re.I):
            citation_rule['superscript'] = True
        if citation_rule.get('marker'):
            structural['citation_format'] = citation_rule
            op = {'type': 'normalize_body_citations', 'to': 'parentheses'}
            if citation_rule.get('italic') is not None:
                op['italic'] = bool(citation_rule.get('italic'))
            if citation_rule.get('superscript') is not None:
                op['superscript'] = bool(citation_rule.get('superscript'))
            add_op(op)

    reference_prefix_clause = next((
        clause for clause in clauses
        if re.search(r'(reference list|bibliography|参考文献(?:列表|条目)?)[^。；;.!?]{0,80}(prefix|number|numbers|numbered|numbering|number style|编号|序号)', clause, re.I)
        and not re.search(r'(citation numbers?|reference citations?|body citations?|正文引用|引文|文献标注)', clause, re.I)
    ), None)
    if reference_prefix_clause:
        style = None
        if re.search(r'round|parentheses|圆括号|小括号|\(\s*1\s*\)', reference_prefix_clause, re.I):
            style = 'round'
        elif re.search(r'square|brackets|方括号|\[\s*1\s*\]', reference_prefix_clause, re.I):
            style = 'square'
        elif re.search(r'plain|bare|arabic\s+(?:number|numbers|numerals?)|阿拉伯数字|^1\s', reference_prefix_clause, re.I):
            style = 'plain'
        if style:
            structural['reference_prefix'] = {'style': style}
            add_op({'type': 'normalize_reference_prefixes', 'style': style, 'renumber': False, 'add_missing': False})

    fig_match = re.search(r'(figure legends?|figure captions?|figures?|图题|图注)[^。；;]{0,80}(?:begin|start|prefix|标为|编号为|写作|采用)[^。；;]{0,40}(Fig\.|Figure|图)\s*\.?\s*1?\s*([:：.]?)', text, re.I)
    if fig_match:
        prefix = fig_match.group(2)
        separator = fig_match.group(3) or ':'
        if prefix.lower().startswith('fig'):
            prefix = 'Fig.' if prefix.lower().startswith('fig.') or prefix.lower() == 'fig' else 'Figure'
        structural['figure_caption'] = {'prefix': prefix, 'separator': separator}
        add_op({'type': 'normalize_figure_captions', 'prefix': prefix, 'separator': separator, 'first_sentence_bold': False})

    if re.search(r'(figure legends?|figure captions?|图题|图注)[^。；;]{0,80}(first sentence|第一句|首句)[^。；;]{0,40}(bold|加粗)', text, re.I):
        structural.setdefault('figure_caption', {})['first_sentence_bold'] = True
        add_op({'type': 'normalize_figure_captions', 'first_sentence_bold': True})
    if re.search(r'(table legends?|table captions?|表题|表注)[^。；;]{0,80}(first sentence|第一句|首句)[^。；;]{0,40}(bold|加粗)', text, re.I):
        structural.setdefault('table_caption', {})['first_sentence_bold'] = True
        add_op({'type': 'normalize_table_captions', 'first_sentence_bold': True})

    table_match = re.search(r'(table legends?|table captions?|tables?|表题|表注)[^。；;]{0,80}(?:begin|start|prefix|标为|编号为|写作|采用)[^。；;]{0,40}(Table|Tab\.|表)\s*\.?\s*1?\s*([:：.]?)', text, re.I)
    if table_match:
        prefix = table_match.group(2)
        separator = table_match.group(3) or ':'
        if prefix.lower().startswith('tab'):
            prefix = 'Table'
        structural['table_caption'] = {'prefix': prefix, 'separator': separator}
        add_op({'type': 'normalize_table_captions', 'prefix': prefix, 'separator': separator, 'first_sentence_bold': False})

    if any(
        re.search(r'(references?|reference list|bibliography|参考文献)[^。；;.!?]{0,80}(sequential|consecutive|按顺序|连续编号|依次编号|顺序编号)', clause, re.I)
        and not re.search(r'(citation numbers?|reference citations?|body citations?|正文引用|引文|文献标注)', clause, re.I)
        for clause in clauses
    ):
        structural.setdefault('reference_prefix', {})['renumber'] = True
        add_op({'type': 'normalize_reference_prefixes', 'style': 'plain_dot', 'renumber': True, 'add_missing': False})

    return structural, operations


def merge_structural_rule(current, update):
    for key, value in (update or {}).items():
        if isinstance(value, dict) and isinstance(current.get(key), dict):
            current[key].update(value)
        else:
            current[key] = value


def merge_postprocess_operation(operations, op):
    if not isinstance(op, dict):
        return
    marker = json.dumps(op, ensure_ascii=False, sort_keys=True)
    existing = {json.dumps(item, ensure_ascii=False, sort_keys=True) for item in operations}
    if marker not in existing:
        operations.append(op)


def extract_text_format_rules(text):
    score = format_guide_score(text)
    sentences = split_rule_sentences(text)
    roles = {}
    matched = []
    structural = {}
    postprocess_operations = []
    for sentence in sentences:
        role, rule = parse_prose_rule_sentence(sentence)
        if role and rule:
            merge_rule_into_role(roles, role, rule)
            matched.append({'role': role, 'text': sentence[:500], 'rule': rule})
        add_multi_role_text_rules(sentence, roles, matched)
        structural_rule, ops = parse_structural_postprocess_rule(sentence)
        if structural_rule:
            merge_structural_rule(structural, structural_rule)
            matched.append({'role': 'postprocess', 'text': sentence[:500], 'rule': structural_rule})
        for op in ops:
            merge_postprocess_operation(postprocess_operations, op)
        if re.search(r'三线表', sentence):
            structural.setdefault('table', {})['border_model'] = 'three_line'
            matched.append({'role': 'table_body', 'text': sentence[:500], 'rule': {'table_border_model': 'three_line'}})
        if re.search(r'公式.*(?:编号|阿拉伯数字)|(?:编号|阿拉伯数字).*公式', sentence):
            structural.setdefault('equation', {})['numbering'] = 'arabic_parentheses_right'
            matched.append({'role': 'equation', 'text': sentence[:500], 'rule': {'numbering': 'arabic_parentheses_right'}})
        if re.search(r'参考文献.*上标|文献号.*上标|引用参考文献.*上标', sentence):
            structural.setdefault('superscript', {})['reference_citation'] = True
            matched.append({'role': 'body', 'text': sentence[:500], 'rule': {'reference_citation_superscript': True}})
        if re.search(r'文献.*(?:按正文中引文出现|先后顺序|出现的先后顺序)', sentence):
            structural.setdefault('reference_numbering', {})['order'] = 'citation_order'
    is_text_guide = (
        (score >= 8 and (len(matched) >= 2 or bool(roles)))
        or bool(roles)
        or bool(postprocess_operations)
    )
    rules_json = {
        '_meta': {
            'source_type': 'text_rules' if is_tex

... [Content truncated, total 67,250 chars] ...