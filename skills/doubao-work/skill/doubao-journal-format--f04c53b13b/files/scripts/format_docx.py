#!/usr/bin/env python3
"""
DOCX Journal Format Tool - 期刊排版工具
Apply journal template styles to a target DOCX document while preserving all content.

Features:
- Page setup (margins, paper size, columns)
- Headers & footers replacement
- Normal style font/size/alignment
- Document settings, font table, theme
- Preserves all content: formulas, images, OLE objects, tables
- Chinese/English bilingual font support

Usage:
    python3 format_docx.py --template template.docx --target paper.docx --output output.docx
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import glob
import xml.etree.ElementTree as ET
import zipfile
from functools import lru_cache

# WordprocessingML namespace
W_NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
R_NS = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
PKG_REL_NS = 'http://schemas.openxmlformats.org/package/2006/relationships'
M_NS = 'http://schemas.openxmlformats.org/officeDocument/2006/math'
WP_NS = 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing'
A_NS = 'http://schemas.openxmlformats.org/drawingml/2006/main'
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
FALLBACK_OOXML_SPEC_PATH = os.path.join(SKILL_DIR, 'assets', 'fallback_ooxml_spec.json')

ROLE_STYLE_IDS = {
    'title': '1title',
    'author': '2author',
    'affiliation': '3affiliation',
    'abstract': '4abstract',
    'keywords': '5keywords',
    'heading1': '6heading1',
    'heading2': '7heading2',
    'heading3': '8heading3',
    'body': '9body',
    'figure_caption': '10figurecaption',
    'table_caption': '11tablecaption',
    'references_heading': '12referencesheading',
    'reference_item': '13referenceitem',
    'equation': '14equation',
    'english_title': '15englishtitle',
    'english_author': '16englishauthor',
    'english_affiliation': '17englishaffiliation',
    'english_abstract': '18englishabstract',
    'english_keywords': '19englishkeywords',
    'metadata': '20metadata',
    'citation_format': '21citationformat',
}

ROLE_DISPLAY_NAMES = {
    'title': '1title',
    'author': '2author',
    'affiliation': '3affiliation',
    'abstract': '4abstract',
    'keywords': '5keywords',
    'heading1': '6heading1',
    'heading2': '7heading2',
    'heading3': '8heading3',
    'body': '9body',
    'figure_caption': '10figurecaption',
    'table_caption': '11tablecaption',
    'references_heading': '12referencesheading',
    'reference_item': '13referenceitem',
    'equation': '14equation',
    'english_title': '15englishtitle',
    'english_author': '16englishauthor',
    'english_affiliation': '17englishaffiliation',
    'english_abstract': '18englishabstract',
    'english_keywords': '19englishkeywords',
    'metadata': '20metadata',
    'citation_format': '21citationformat',
}

TEXT_RULE_PRIORITY = (
    'user_rules > extracted_text_rules > source_column_detection_for_fallback_variant > '
    'bundled_OOXML_fallback > legacy_dictionary_fallback'
)
SOURCE_EVIDENCE_PRIORITIES = {
    'docx_template': (
        'user_rules > template_text_rules > representative_template_direct_format > '
        'template_style_xml > bundled_OOXML_fallback > legacy_dictionary_fallback'
    ),
    'native_docx_template': (
        'user_rules > template_text_rules > representative_template_direct_format > '
        'template_style_xml > bundled_OOXML_fallback > legacy_dictionary_fallback'
    ),
    'converted_docx_template': (
        'user_rules > converted_text_rules > source_column_detection_for_fallback_variant > bundled_OOXML_fallback > legacy_dictionary_fallback'
    ),
    'pdf_visual_inference': (
        'user_rules > extracted_text_rules > pdf_column_detection_for_fallback_variant > bundled_OOXML_fallback > legacy_dictionary_fallback'
    ),
    'pdf_text_visual_hybrid': (
        'user_rules > extracted_pdf_text_rules > pdf_column_detection_for_fallback_variant > bundled_OOXML_fallback > legacy_dictionary_fallback'
    ),
    'text_rules': (
        'user_rules > extracted_text_rules > bundled_OOXML_fallback > legacy_dictionary_fallback'
    ),
    'plain_text_rules': (
        'user_rules > extracted_text_rules > bundled_OOXML_fallback > legacy_dictionary_fallback'
    ),
    'ocr_text_rules': (
        'user_rules > extracted_text_rules > source_column_detection_for_fallback_variant > bundled_OOXML_fallback > legacy_dictionary_fallback'
    ),
    'image_text_rules': (
        'user_rules > extracted_text_rules > source_column_detection_for_fallback_variant > bundled_OOXML_fallback > legacy_dictionary_fallback'
    ),
    'website_text_rules': (
        'user_rules > extracted_text_rules > source_column_detection_for_fallback_variant > bundled_OOXML_fallback > legacy_dictionary_fallback'
    ),
    'screenshot_text_rules': (
        'user_rules > extracted_text_rules > source_column_detection_for_fallback_variant > bundled_OOXML_fallback > legacy_dictionary_fallback'
    ),
    'visual_template': (
        'user_rules > extracted_text_rules > source_column_detection_for_fallback_variant > bundled_OOXML_fallback > legacy_dictionary_fallback'
    ),
    'blank_carrier_template': (
        'user_rules > extracted_text_rules > bundled_OOXML_fallback_materialized_into_blank_carrier > legacy_dictionary_fallback'
    ),
}
LEGACY_WORD_EXTENSIONS = {'.doc', '.dot'}
STYLE_SPEC_VERSION = '1.9'
REFERENCE_NUMBERING_MAP_VERSION = '1.2'
WEAK_EXTERNAL_STYLE_SOURCE_TYPES = {
    'converted_docx_template',
    'pdf_visual_inference',
    'pdf_text_visual_hybrid',
    'ocr_text_rules',
    'image_text_rules',
    'website_text_rules',
    'screenshot_text_rules',
    'text_rules',
    'plain_text_rules',
    'blank_carrier_template',
}
LOW_CONFIDENCE_STYLE_SHELL_SOURCE_TYPES = WEAK_EXTERNAL_STYLE_SOURCE_TYPES | {
    'visual_template',
}
LOW_CONFIDENCE_FORMAT_SOURCE_TYPES = LOW_CONFIDENCE_STYLE_SHELL_SOURCE_TYPES | {
    'visual_template',
    'pdf_visual',
}
OOXML_FALLBACK_SOURCE_TYPES = WEAK_EXTERNAL_STYLE_SOURCE_TYPES | {
    'visual_template',
}
NON_DOCX_TEXT_ONLY_SOURCE_TYPES = {
    'converted_docx_template',
    'pdf_visual_inference',
    'pdf_text_visual_hybrid',
    'visual_template',
    'ocr_text_rules',
    'image_text_rules',
    'website_text_rules',
    'screenshot_text_rules',
    'text_rules',
    'plain_text_rules',
}
WEBSITE_FORMAT_SOURCE_TYPES = {
    'website_text_rules',
}
DOCX_TEXT_RULE_COMPLETION_SOURCE_TYPES = {
    'docx_template',
    'native_docx_template',
}
VISUAL_CENTER_DEFAULT_ROLES = {
    'title', 'english_title',
    'author', 'english_author',
    'affiliation', 'english_affiliation',
}
ABSTRACT_KEYWORD_ROLES = {
    'abstract', 'keywords', 'english_abstract', 'english_keywords',
}
ABSTRACT_KEYWORD_LABEL_PATTERN = (
    r'(?:'
    r'摘\s*要|关键词|关键字|'
    r'Abstract|ABSTRACT|Keywords?|KEYWORDS?|Key\s*words?|KEY\s*WORDS?'
    r')'
)
ABSTRACT_KEYWORD_LABEL_RE = re.compile(
    r'^\s*(?:[\[【〔「『（(]\s*)?(' + ABSTRACT_KEYWORD_LABEL_PATTERN + r')'
    r'(?:\s*[\]】〕」』）)])?\s*(?:[:：]\s*)?',
    re.I,
)

CANONICAL_STYLE_CANDIDATES = {
    'title': ['IOPTitle', 'Titledocument', 'TitleDocument', 'Title'],
    'author': ['Authors', 'Author'],
    'affiliation': ['Affiliation', 'AdressLines', 'AddressLines', 'Affiliations'],
    'abstract': ['Abstract'],
    'keywords': ['KeyWords', 'Keywords', 'Keyword', 'KeyWord'],
    'heading1': ['IOPH1', 'Head1', 'Heading1'],
    'heading2': ['IOPH2', 'Head2', 'Heading2'],
    'heading3': ['IOPH3', 'Head3', 'Heading3'],
    'body': ['Para', 'BodyText', 'BodyTextIndent', 'Normal'],
    'figure_caption': ['FigureCaption', 'CaptionFigure', 'Caption'],
    'table_caption': ['TableCaption', 'CaptionTable', 'TableTitle', 'Caption'],
    'references_heading': ['ReferenceHead', 'ACMRefHead', 'Heading1'],
    'reference_item': ['IOPRefs', 'Bibentry', 'BibEntry', 'References', 'Bibliography'],
    'equation': ['DisplayFormula', 'Equation', 'Formula'],
    'english_title': ['EnglishTitle', 'TitleEnglish'],
    'english_author': ['EnglishAuthors', 'AuthorsEnglish'],
    'english_affiliation': ['EnglishAffiliation', 'AffiliationEnglish'],
    'english_abstract': ['EnglishAbstract', 'AbstractEnglish'],
    'english_keywords': ['EnglishKeywords', 'KeywordsEnglish'],
    'metadata': ['Metadata'],
    'citation_format': ['CitationFormat'],
}

ROLE_EQUIVALENTS = {
    'title': ['english_title'],
    'author': ['english_author'],
    'affiliation': ['english_affiliation'],
    'abstract': ['english_abstract'],
    'keywords': ['english_keywords'],
    'english_title': ['title'],
    'english_author': ['author'],
    'english_affiliation': ['affiliation'],
    'english_abstract': ['abstract'],
    'english_keywords': ['keywords'],
}


def abstract_keyword_label_role(text):
    match = ABSTRACT_KEYWORD_LABEL_RE.match(text or '')
    if not match:
        return None
    label_raw = match.group(1) or ''
    label = re.sub(r'\s+', '', label_raw).lower()
    if label in ('摘要',):
        return 'abstract'
    if label in ('关键词', '关键字'):
        return 'keywords'
    if label == 'abstract':
        return 'english_abstract'
    if label in ('keyword', 'keywords', 'keyword', 'keywords', 'keywords'):
        return 'english_keywords'
    return None


SIZE_MAP = {
    '初号': 84,
    '小初': 72,
    '一号': 52,
    '小一': 48,
    '二号': 44,
    '小二': 36,
    '三号': 32,
    '小三': 30,
    '四号': 28,
    '小四': 24,
    '五号': 21,
    '小五': 18,
    '六号': 15,
    '小六': 13,
    '七号': 11,
    '八号': 10,
}

FONT_WORDS = [
    'Times New Roman', 'Times Roman', 'Arial', 'Calibri',
    '宋体', '黑体', '楷体', '楷体_GB2312', '仿宋', '仿宋_GB2312',
    '微软雅黑', '等线', 'SimSun', 'SimHei', 'KaiTi', 'FangSong',
]

DEFAULT_REFERENCE_HANGING_INDENT = '420'
DEFAULT_REFERENCE_INDENT = {
    'left': DEFAULT_REFERENCE_HANGING_INDENT,
    'hanging': DEFAULT_REFERENCE_HANGING_INDENT,
}

BASE_PARAGRAPH_FALLBACK = {
    'align': 'left',
    'spacing': {'before': '0', 'after': '0', 'line': '240', 'lineRule': 'auto'},
}

LANGUAGE_FALLBACKS = {
    'zh': {
        'title': {
            'fonts': {'eastAsia': '黑体', 'ascii': 'Times New Roman', 'hAnsi': 'Times New Roman'},
            'size': '32', 'bold': True, 'align': 'center',
            'spacing': {'before': '240', 'after': '120', 'line': '360', 'lineRule': 'auto'},
        },
        'author': {
            'fonts': {'eastAsia': '宋体', 'ascii': 'Times New Roman', 'hAnsi': 'Times New Roman'},
            'size': '21', 'align': 'center',
        },
        'affiliation': {
            'fonts': {'eastAsia': '宋体', 'ascii': 'Times New Roman', 'hAnsi': 'Times New Roman'},
            'size': '18', 'align': 'center',
        },
        'abstract': {
            'fonts': {'eastAsia': '宋体', 'ascii': 'Times New Roman', 'hAnsi': 'Times New Roman'},
            'size': '21', 'align': 'both',
        },
        'keywords': {
            'fonts': {'eastAsia': '宋体', 'ascii': 'Times New Roman', 'hAnsi': 'Times New Roman'},
            'size': '21', 'align': 'left',
        },
        'heading1': {
            'fonts': {'eastAsia': '黑体', 'ascii': 'Times New Roman', 'hAnsi': 'Times New Roman'},
            'size': '28', 'bold': True, 'align': 'center',
            'spacing': {'before': '240', 'after': '120', 'line': '360', 'lineRule': 'auto'},
        },
        'heading2': {
            'fonts': {'eastAsia': '黑体', 'ascii': 'Times New Roman', 'hAnsi': 'Times New Roman'},
            'size': '24', 'bold': True, 'align': 'left',
            'spacing': {'before': '180', 'after': '60', 'line': '360', 'lineRule': 'auto'},
        },
        'heading3': {
            'fonts': {'eastAsia': '黑体', 'ascii': 'Times New Roman', 'hAnsi': 'Times New Roman'},
            'size': '21', 'bold': True, 'align': 'left',
            'spacing': {'before': '120', 'after': '60', 'line': '360', 'lineRule': 'auto'},
        },
        'body': {
            'fonts': {'eastAsia': '宋体', 'ascii': 'Times New Roman', 'hAnsi': 'Times New Roman'},
            'size': '21', 'align': 'both', 'indent': {'firstLine': '420'},
            'spacing': {'before': '0', 'after': '0', 'line': '360', 'lineRule': 'auto'},
        },
        'figure_caption': {
            'fonts': {'eastAsia': '宋体', 'ascii': 'Times New Roman', 'hAnsi': 'Times New Roman'},
            'size': '18', 'align': 'center',
        },
        'table_caption': {
            'fonts': {'eastAsia': '宋体', 'ascii': 'Times New Roman', 'hAnsi': 'Times New Roman'},
            'size': '18', 'align': 'center',
        },
        'references_heading': {
            'fonts': {'eastAsia': '黑体', 'ascii': 'Times New Roman', 'hAnsi': 'Times New Roman'},
            'size': '24', 'bold': True, 'align': 'center',
        },
        'reference_item': {
            'fonts': {'eastAsia': '宋体', 'ascii': 'Times New Roman', 'hAnsi': 'Times New Roman'},
            'size': '18', 'align': 'both', 'indent': DEFAULT_REFERENCE_INDENT,
        },
        'english_title': {
            'fonts': {'eastAsia': '宋体', 'ascii': 'Times New Roman', 'hAnsi': 'Times New Roman'},
            'size': '24', 'bold': True, 'align': 'center',
        },
        'english_author': {
            'fonts': {'eastAsia': '宋体', 'ascii': 'Times New Roman', 'hAnsi': 'Times New Roman'},
            'size': '18', 'align': 'center',
        },
        'english_affiliation': {
            'fonts': {'eastAsia': '宋体', 'ascii': 'Times New Roman', 'hAnsi': 'Times New Roman'},
            'size': '18', 'align': 'center',
        },
        'english_abstract': {
            'fonts': {'eastAsia': '宋体', 'ascii': 'Times New Roman', 'hAnsi': 'Times New Roman'},
            'size': '21', 'align': 'both',
        },
        'english_keywords': {
            'fonts': {'eastAsia': '宋体', 'ascii': 'Times New Roman', 'hAnsi': 'Times New Roman'},
            'size': '21', 'align': 'left',
        },
        'metadata': {
            'fonts': {'eastAsia': '宋体', 'ascii': 'Times New Roman', 'hAnsi': 'Times New Roman'},
            'size': '18', 'align': 'left',
        },
        'citation_format': {
            'fonts': {'eastAsia': '宋体', 'ascii': 'Times New Roman', 'hAnsi': 'Times New Roman'},
            'size': '18', 'align': 'left',
        },
        'equation': {
            'fonts': {'eastAsia': '宋体', 'ascii': 'Times New Roman', 'hAnsi': 'Times New Roman'},
            'size': '21', 'align': 'center',
            'spacing': {'before': '0', 'after': '0', 'line': '360', 'lineRule': 'auto'},
        },
    },
    'en': {
        'title': {
            'fonts': {'ascii': 'Times New Roman', 'hAnsi': 'Times New Roman', 'eastAsia': 'SimSun'},
            'size': '32', 'bold': True, 'align': 'center',
        },
        'author': {
            'fonts': {'ascii': 'Times New Roman', 'hAnsi': 'Times New Roman', 'eastAsia': 'SimSun'},
            'size': '24', 'align': 'center',
        },
        'affiliation': {
            'fonts': {'ascii': 'Times New Roman', 'hAnsi': 'Times New Roman', 'eastAsia': 'SimSun'},
            'size': '20', 'align': 'center',
        },
        'abstract': {
            'fonts': {'ascii': 'Times New Roman', 'hAnsi': 'Times New Roman', 'eastAsia': 'SimSun'},
            'size': '21', 'align': 'both',
        },
        'keywords': {
            'fonts': {'ascii': 'Times New Roman', 'hAnsi': 'Times New Roman', 'eastAsia': 'SimSun'},
            'size': '21', 'align': 'left',
        },
        'heading1': {
            'fonts': {'ascii': 'Times New Roman', 'hAnsi': 'Times New Roman', 'eastAsia': 'SimSun'},
            'size': '24', 'bold': True, 'align': 'left',
        },
        'heading2': {
            'fonts': {'ascii': 'Times New Roman', 'hAnsi': 'Times New Roman', 'eastAsia': 'SimSun'},
            'size': '22', 'bold': True, 'align': 'left',
        },
        'heading3': {
            'fonts': {'ascii': 'Times New Roman', 'hAnsi': 'Times New Roman', 'eastAsia': 'SimSun'},
            'size': '20', 'bold': True, 'align': 'left',
        },
        'body': {
            'fonts': {'ascii': 'Times New Roman', 'hAnsi': 'Times New Roman', 'eastAsia': 'SimSun'},
            'size': '24', 'align': 'both',
        },
        'figure_caption': {
            'fonts': {'ascii': 'Times New Roman', 'hAnsi': 'Times New Roman', 'eastAsia': 'SimSun'},
            'size': '18', 'align': 'center',
        },
        'table_caption': {
            'fonts': {'ascii': 'Times New Roman', 'hAnsi': 'Times New Roman', 'eastAsia': 'SimSun'},
            'size': '18', 'align': 'center',
        },
        'references_heading': {
            'fonts': {'ascii': 'Times New Roman', 'hAnsi': 'Times New Roman', 'eastAsia': 'SimSun'},
            'size': '24', 'bold': True, 'align': 'left',
        },
        'reference_item': {
            'fonts': {'ascii': 'Times New Roman', 'hAnsi': 'Times New Roman', 'eastAsia': 'SimSun'},
            'size': '20', 'align': 'left', 'indent': DEFAULT_REFERENCE_INDENT,
        },
        'english_title': {
            'fonts': {'ascii': 'Times New Roman', 'hAnsi': 'Times New Roman', 'eastAsia': 'SimSun'},
            'size': '32', 'bold': True, 'align': 'center',
        },
        'english_author': {
            'fonts': {'ascii': 'Times New Roman', 'hAnsi': 'Times New Roman', 'eastAsia': 'SimSun'},
            'size': '24', 'align': 'center',
        },
        'english_affiliation': {
            'fonts': {'ascii': 'Times New Roman', 'hAnsi': 'Times New Roman', 'eastAsia': 'SimSun'},
            'size': '20', 'align': 'center',
        },
        'english_abstract': {
            'fonts': {'ascii': 'Times New Roman', 'hAnsi': 'Times New Roman', 'eastAsia': 'SimSun'},
            'size': '21', 'align': 'both',
        },
        'english_keywords': {
            'fonts': {'ascii': 'Times New Roman', 'hAnsi': 'Times New Roman', 'eastAsia': 'SimSun'},
            'size': '21', 'align': 'left',
        },
        'metadata': {
            'fonts': {'ascii': 'Times New Roman', 'hAnsi': 'Times New Roman', 'eastAsia': 'SimSun'},
            'size': '20', 'align': 'left',
        },
        'citation_format': {
            'fonts': {'ascii': 'Times New Roman', 'hAnsi': 'Times New Roman', 'eastAsia': 'SimSun'},
            'size': '20', 'align': 'left',
        },
    },
}

DIRECT_RPR_TAGS = {
    'rFonts', 'sz', 'szCs', 'b', 'bCs', 'i', 'iCs', 'color', 'highlight',
    'shd', 'u', 'smallCaps', 'caps', 'strike', 'dstrike', 'kern', 'spacing',
    'position', 'fitText', 'em', 'lang',
}

SUPERSCRIPT_MAP_VERSION = '1.0'
SUPERSCRIPT_MARKER_RE = r'(?:\d{1,2}|[*†‡§])'
EQUATION_LAYOUT_MAP_VERSION = '1.0'
TABLE_FORMAT_MAP_VERSION = '1.1'
TABLE_THREE_LINE_BORDER = {'val': 'single', 'sz': '8', 'space': '0', 'color': '000000'}
TABLE_THREE_LINE_BORDER_THICK = {'val': 'single', 'sz': '12', 'space': '0', 'color': '000000'}
TABLE_THREE_LINE_HEADER_SEPARATOR_BORDER = {'val': 'single', 'sz': '6', 'space': '0', 'color': '000000'}
TABLE_BORDER_NONE = {'val': 'none'}
REFERENCE_ITEM_DEFAULT_INDENT_TWIPS = '420'

DIRECT_PPR_TAGS = {
    'jc', 'spacing', 'ind', 'rPr', 'contextualSpacing', 'keepNext',
    'keepLines', 'widowControl', 'outlineLvl', 'tabs', 'textAlignment',
}

TABLE_PR_FORMAT_TAGS = {
    'tblStyle', 'tblpPr', 'tblOverlap', 'bidiVisual', 'tblStyleRowBandSize',
    'tblStyleColBandSize', 'jc', 'tblCellSpacing', 'tblInd',
    'tblBorders', 'shd', 'tblCellMar', 'tblLook',
}

TABLE_ROW_FORMAT_TAGS = {
    'tblHeader', 'cantSplit', 'trHeight', 'jc', 'hidden', 'tblCellSpacing',
    'cnfStyle', 'divId',
}

TABLE_CELL_FORMAT_TAGS = {
    'tcW', 'tcBorders', 'shd', 'noWrap',
    'tcMar', 'textDirection', 'tcFitText', 'vAlign', 'hideMark',
}

TABLE_CELL_TOPOLOGY_TAGS = {'gridSpan', 'hMerge', 'vMerge'}

# All common OOXML namespaces
ALL_NAMESPACES = {
    'wpc': 'http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas',
    'cx': 'http://schemas.microsoft.com/office/drawing/2014/chartex',
    'cx1': 'http://schemas.microsoft.com/office/drawing/2015/9/8/chartex',
    'mc': 'http://schemas.openxmlformats.org/markup-compatibility/2006',
    'o': 'urn:schemas-microsoft-com:office:office',
    'r': R_NS,
    'm': 'http://schemas.openxmlformats.org/officeDocument/2006/math',
    'v': 'urn:schemas-microsoft-com:vml',
    'wp14': 'http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing',
    'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
    'w10': 'urn:schemas-microsoft-com:office:word',
    'w': W_NS,
    'w14': 'http://schemas.microsoft.com/office/word/2010/wordml',
    'w15': 'http://schemas.microsoft.com/office/word/2012/wordml',
    'w16se': 'http://schemas.microsoft.com/office/word/2015/wordml/symex',
    'wpg': 'http://schemas.microsoft.com/office/word/2010/wordprocessingGroup',
    'wpi': 'http://schemas.microsoft.com/office/word/2010/wordprocessingInk',
    'wne': 'http://schemas.microsoft.com/office/word/2006/wordml',
    'wps': 'http://schemas.microsoft.com/office/word/2010/wordprocessingShape',
}

# Register all namespaces to preserve them on output
for prefix, uri in ALL_NAMESPACES.items():
    ET.register_namespace(prefix, uri)


def w(tag):
    """Get fully qualified Word tag."""
    return f'{{{W_NS}}}{tag}'


def r(tag):
    """Get fully qualified Relationship tag."""
    return f'{{{R_NS}}}{tag}'


def pkg_rel(tag):
    """Get fully qualified package relationship tag."""
    return f'{{{PKG_REL_NS}}}{tag}'


def local_name(tag):
    """Return local XML tag name without namespace."""
    return tag.split('}')[-1] if '}' in tag else tag


def is_legacy_word_path(path):
    return os.path.splitext(str(path))[1].lower() in LEGACY_WORD_EXTENSIONS


def legacy_word_warning(path, role):
    ext = os.path.splitext(str(path))[1].lower()
    return (
        f"{role} file is legacy Word {ext}: {path}. "
        "Legacy .doc/.dot is not an OpenXML package and has no directly inspectable "
        "word/styles.xml. Conversion to .docx may flatten styles into direct formatting, "
        "lose template-only definitions, or differ from Microsoft Word's final display. "
        "Convert it to a temporary .docx when possible, treat the converted evidence as "
        "lower confidence, and recommend a native .docx/.dotx source-format file or "
        "explicit text formatting instructions in the final notes. Stop only if conversion and other extraction routes produce "
        "no usable formatting evidence."
    )


def find_word_converter():
    candidates = [
        'soffice',
        'libreoffice',
        '/Applications/LibreOffice.app/Contents/MacOS/soffice',
    ]
    for candidate in candidates:
        if os.path.isabs(candidate):
            if os.path.exists(candidate):
                return candidate
        else:
            found = shutil.which(candidate)
            if found:
                return found
    return None


def convert_legacy_word_to_docx(path, tmpdir, role):
    converter = find_word_converter()
    if not converter:
        raise RuntimeError(
            f"{legacy_word_warning(path, role)} No LibreOffice/soffice converter was found."
        )
    out_dir = os.path.join(tmpdir, f'{role}_legacy_docx')
    os.makedirs(out_dir, exist_ok=True)
    cmd = [
        converter,
        '--headless',
        '--convert-to',
        'docx',
        '--outdir',
        out_dir,
        path,
    ]
    print(f"Converting legacy Word {role} to temporary DOCX with {os.path.basename(converter)}...")
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"Legacy Word conversion failed for {path}: {result.stderr.strip() or result.stdout.strip()}"
        )
    converted = os.path.join(out_dir, os.path.splitext(os.path.basename(path))[0] + '.docx')
    if not os.path.exists(converted):
        candidates = [
            os.path.join(out_dir, name)
            for name in os.listdir(out_dir)
            if name.lower().endswith('.docx')
        ]
        if len(candidates) == 1:
            converted = candidates[0]
    if not os.path.exists(converted) or not zipfile.is_zipfile(converted):
        raise RuntimeError(f"Legacy Word conversion did not produce a valid DOCX for {path}")
    return converted


def classify_libreoffice_failure(stdout, stderr, returncode):
    combined = f"{stdout or ''}\n{stderr or ''}"
    if returncode == 0:
        return None
    if 'source file could not be loaded' in combined:
        return 'libreoffice_source_load_failed'
    if 'Error: source file could not be loaded' in combined:
        return 'libreoffice_source_load_failed'
    if 'General Error' in combined:
        return 'libreoffice_general_error'
    if 'SfxBaseModel::impl_store' in combined or 'store' in combined.lower():
        return 'libreoffice_export_failed'
    return 'libreoffice_conversion_failed'


def run_libreoffice_compatibility_qa(docx_path, output_dir):
    """Check whether LibreOffice can load the final DOCX and e

... [Content truncated, total 492,439 chars] ...