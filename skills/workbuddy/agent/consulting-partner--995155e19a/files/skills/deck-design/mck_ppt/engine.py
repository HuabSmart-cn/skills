# Copyright 2024-2026 Kaku Li (https://github.com/likaku)
# Licensed under the Apache License, Version 2.0 — see LICENSE and NOTICE.
# Part of "Mck-ppt-design-skill" (McKinsey PPT Design Framework).
# NOTICE: This file must be retained in all copies or substantial portions.
#
"""MckEngine — The presentation engine that wraps python-pptx with high-level layout methods.

Usage:
    eng = MckEngine(total_slides=30)
    eng.cover(title='Title', subtitle='Sub')
    eng.toc(items=[('1','Topic','Desc'), ...])
    eng.save('output/deck.pptx')

Every layout method creates one slide and auto-increments page numbers.
"""
import math
import os
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn

from .constants import *
from .core import (
    _clean_shape, set_ea_font,
    add_text, add_rect, add_hline, add_oval, add_image_placeholder,
    add_action_title, add_source, add_page_number, add_bottom_bar,
    add_block_arc, add_color_legend, draw_harvey_ball,
    full_cleanup,
)


class MckEngine:
    """Presentation engine with high-level layout methods."""

    def __init__(self, total_slides=30):
        self.prs = Presentation()
        self.prs.slide_width = SW
        self.prs.slide_height = SH
        self._blank_layout = self.prs.slide_layouts[6]
        self._page = 0
        self.total = total_slides

    # ─── internal ──────────────────────────────
    def _ns(self):
        """Create new blank slide, increment page counter."""
        self._page += 1
        return self.prs.slides.add_slide(self._blank_layout)

    def _footer(self, s, source=None):
        """Add source + page number (common to most content slides)."""
        if source:
            add_source(s, source)
        add_page_number(s, self._page, self.total)

    # ═══════════════════════════════════════════
    # STRUCTURE LAYOUTS (#1, #5, #6, #7, #36)
    # ═══════════════════════════════════════════

    def cover(self, title, subtitle='', author='', date='', cover_image=None):
        """#1 Executive cover — full-bleed navy hero with optional image field.

        Parameters
        ----------
        cover_image : str or None
            - None  : 使用深海军蓝几何封面，保证默认输出也具备成品感
            - 'auto': 调用腾讯混元 API 自动生成封面图
            - 路径   : 使用指定图片，并保留左侧高对比信息区
        """
        s = self._ns()

        img_path = None
        if cover_image == 'auto':
            from .cover_image import generate_cover_image
            img_path = generate_cover_image(title)
        elif cover_image and os.path.isfile(cover_image):
            img_path = cover_image

        # Warm executive cover: clean full-bleed dark canvas.
        # Layout uses fixed vertical positions to prevent overlap regardless of
        # title length — everything has a predictable slot.
        add_rect(s, 0, 0, SW, SH, NAVY)
        if img_path:
            s.shapes.add_picture(img_path, Inches(7.6), 0, Inches(5.733), SH)
        # No right-side panel or stripe — keep it clean and uncluttered.

        text_left = Inches(1.1)
        text_width = Inches(7.4)

        # Fixed title zone: y=2.2, max height=2.0
        title_y = Inches(2.2)
        title_max_h = Inches(2.0)
        add_text(s, text_left, title_y, text_width, title_max_h,
                 title, font_size=COVER_TITLE_SIZE, font_name=FONT_HEADER,
                 font_color=WHITE, bold=True)

        # Fixed accent bar at y=4.4
        add_rect(s, text_left, Inches(4.4), Inches(2.0), Inches(0.04), ACCENT_BLUE)

        # Fixed subtitle zone: y=4.7
        if subtitle:
            add_text(s, text_left, Inches(4.7), text_width, Inches(0.55),
                     subtitle, font_size=Pt(18), font_color=PALE_BLUE)

        # Fixed metadata zone: y=5.8
        meta_y = Inches(5.8)
        if author:
            add_text(s, text_left, meta_y, text_width, Inches(0.3),
                     author, font_size=SMALL_SIZE, font_color=WHITE)
            meta_y += Inches(0.4)
        if date:
            add_text(s, text_left, meta_y, text_width, Inches(0.3),
                     date, font_size=SMALL_SIZE, font_color=MED_GRAY)

        return s

    def section_divider(self, section_label, title, subtitle=''):
        """#5 Section Divider — warm dark transition with fixed layout zones."""
        s = self._ns()
        add_rect(s, 0, 0, SW, SH, NAVY)
        # Bottom warm accent strip
        add_rect(s, 0, Inches(7.1), SW, Inches(0.4), ACCENT_BLUE)
        # Section label at fixed y=2.8
        add_text(s, Inches(1.2), Inches(2.8), Inches(10), Inches(0.35),
                 section_label.upper(), font_size=Pt(11),
                 font_color=MED_GRAY, bold=True, font_name=FONT_HEADER)
        # Title at fixed y=3.3, max height 1.6
        add_text(s, Inches(1.2), Inches(3.3), Inches(10), Inches(1.6),
                 title, font_size=Pt(32), font_color=WHITE,
                 bold=True, font_name=FONT_HEADER)
        if subtitle:
            add_text(s, Inches(1.2), Inches(5.1), Inches(10), Inches(0.55),
                     subtitle, font_size=BODY_SIZE, font_color=PALE_BLUE)
        add_page_number(s, self._page, self.total, color=MED_GRAY)
        return s

    def toc(self, title='目录', items=None, source=''):
        """#6 Table of Contents — numbered items with descriptions.
        items: list of (num, title, description)
        """
        s = self._ns()
        add_action_title(s, title)
        iy = Inches(1.5)
        for num, item_title, desc in (items or []):
            add_oval(s, LM, iy, str(num))
            add_text(s, LM + Inches(0.7), iy, Inches(4.0), Inches(0.4),
                     item_title, font_size=SUB_HEADER_SIZE, font_color=NAVY, bold=True)
            add_text(s, Inches(5.5), iy + Inches(0.05), Inches(6.5), Inches(0.4),
                     desc, font_size=BODY_SIZE, font_color=MED_GRAY)
            iy += Inches(0.7)
            add_hline(s, LM, iy, CW, LINE_GRAY)
            iy += Inches(0.3)
        self._footer(s, source)
        return s

    def closing(self, title, message='', source_text=''):
        """#36 Closing / Thank You slide."""
        s = self._ns()
        add_rect(s, 0, 0, SW, Inches(0.05), NAVY)
        add_text(s, Inches(1.5), Inches(2.0), Inches(10.3), Inches(1.0),
                 title, font_size=SECTION_TITLE_SIZE, font_color=NAVY,
                 bold=True, font_name=FONT_HEADER, alignment=PP_ALIGN.CENTER)
        add_hline(s, Inches(5.5), Inches(3.3), Inches(2.3), NAVY, Pt(1.5))
        if message:
            add_text(s, Inches(1.5), Inches(3.8), Inches(10.3), Inches(2.0),
                     message, font_size=SUB_HEADER_SIZE, font_color=DARK_GRAY,
                     alignment=PP_ALIGN.CENTER)
        add_hline(s, LM, Inches(6.8), CW, NAVY, Pt(2))
        if source_text:
            add_text(s, Inches(1), Inches(6.2), Inches(11), Inches(0.4),
                     source_text, font_size=SMALL_SIZE, font_color=MED_GRAY,
                     alignment=PP_ALIGN.CENTER)
        return s

    # ═══════════════════════════════════════════
    # DATA LAYOUTS (#8, #9, #10, #11, #12, #23)
    # ═══════════════════════════════════════════

    def big_number(self, title, number, unit='', description='',
                   detail_items=None, source='', bottom_bar=None):
        """#8 Big Number — large stat with context.
        detail_items: list[str] bullet points shown below.
        bottom_bar: (label, text) or None.
        """
        s = self._ns()
        add_action_title(s, title)
        # Navy big number box
        box_w = Inches(3.5)
        add_rect(s, LM, CONTENT_TOP + Inches(0.1), box_w, Inches(1.8), NAVY)
        add_text(s, LM + Inches(0.2), CONTENT_TOP + Inches(0.2), box_w - Inches(0.4), Inches(0.8),
                 str(number), font_size=COVER_TITLE_SIZE, font_color=WHITE, bold=True,
                 font_name=FONT_HEADER, alignment=PP_ALIGN.CENTER)
        if unit:
            add_text(s, LM + Inches(0.2), CONTENT_TOP + Inches(1.0), box_w - Inches(0.4), Inches(0.7),
                     unit, font_size=SMALL_SIZE, font_color=WHITE, alignment=PP_ALIGN.CENTER)
        # Right description
        if description:
            right_x = Inches(5.0)
            right_w = Inches(7.5)
            add_text(s, right_x, CONTENT_TOP + Inches(0.2), right_w, Inches(2.5),
                     description if isinstance(description, list) else [description],
                     font_size=BODY_SIZE, line_spacing=Pt(10))
        # Detail area
        if detail_items:
            add_rect(s, LM, Inches(4.5), CW, Inches(2.2), BG_GRAY)
            add_text(s, LM + Inches(0.3), Inches(4.6), Inches(1.8), Inches(0.4),
                     '解决路径' if not unit else '详细说明',
                     font_size=BODY_SIZE, font_color=NAVY, bold=True)
            add_text(s, LM + Inches(0.3), Inches(5.1), CW - Inches(0.6), Inches(1.4),
                     detail_items, font_size=BODY_SIZE, line_spacing=Pt(8))
        if bottom_bar:
            add_bottom_bar(s, bottom_bar[0], bottom_bar[1])
        self._footer(s, source)
        return s

    def two_stat(self, title, stats, detail_items=None, source=''):
        """#9 Two-Stat Comparison — two big numbers side by side.
        stats: list of (number, label, is_navy:bool)
        """
        s = self._ns()
        add_action_title(s, title)
        sw_stat = Inches(5.5)
        sg = Inches(0.733)
        for i, (big, label, is_navy) in enumerate(stats):
            sx = LM + (sw_stat + sg) * i
            fill = NAVY if is_navy else BG_GRAY
            bc = WHITE if is_navy else NAVY
            sc = WHITE if is_navy else DARK_GRAY
            add_rect(s, sx, Inches(1.5), sw_stat, Inches(2.0), fill)
            add_text(s, sx + Inches(0.3), Inches(1.6), sw_stat - Inches(0.6), Inches(0.9),
                     str(big), font_size=COVER_TITLE_SIZE, font_color=bc, bold=True,
                     font_name=FONT_HEADER, alignment=PP_ALIGN.CENTER)
            add_text(s, sx + Inches(0.3), Inches(2.6), sw_stat - Inches(0.6), Inches(0.5),
                     label, font_size=BODY_SIZE, font_color=sc, alignment=PP_ALIGN.CENTER)
        if detail_items:
            add_text(s, LM, Inches(4.0), CW, Inches(2.5),
                     detail_items, font_size=BODY_SIZE, line_spacing=Pt(8))
        self._footer(s, source)
        return s

    def metric_cards(self, title, cards, source=''):
        """#12 Metric Cards — 3-4 accent-colored cards.
        cards: list of (letter, card_title, description, accent_color, light_bg)
               or (letter, card_title, description) — auto-colors from ACCENT_PAIRS.
        """
        s = self._ns()
        add_action_title(s, title)
        n = len(cards)
        card_w = (CW - Inches(0.2) * (n - 1)) / n
        card_g = Inches(0.2)
        for i, card in enumerate(cards):
            if len(card) == 5:
                letter, ctitle, desc, accent, light = card
            else:
                letter, ctitle, desc = card[:3]
                accent, light = NAVY, BG_GRAY
            cx = LM + (card_w + card_g) * i
            add_rect(s, cx, CONTENT_TOP + Inches(0.1), card_w, Inches(4.8), light)
            add_rect(s, cx, CONTENT_TOP + Inches(0.1), card_w, Inches(0.06), accent)
            add_oval(s, cx + card_w / 2 - Inches(0.225), CONTENT_TOP + Inches(0.3),
                     str(letter), bg=accent)
            add_text(s, cx + Inches(0.2), CONTENT_TOP + Inches(0.9), card_w - Inches(0.4), Inches(0.4),
                     ctitle, font_size=SUB_HEADER_SIZE, font_color=accent,
                     bold=True, alignment=PP_ALIGN.CENTER)
            add_hline(s, cx + Inches(0.4), CONTENT_TOP + Inches(1.4),
                      card_w - Inches(0.8), LINE_GRAY)
            add_text(s, cx + Inches(0.2), CONTENT_TOP + Inches(1.6), card_w - Inches(0.4), Inches(2.5),
                     desc if isinstance(desc, list) else desc,
                     font_size=BODY_SIZE, alignment=PP_ALIGN.LEFT, line_spacing=Pt(8))
        self._footer(s, source)
        return s

    def data_table(self, title, headers, rows, col_widths=None, source='',
                   bottom_bar=None):
        """#11 Data Table — header row + data rows with separators.
        headers: list[str], rows: list[list[str]], col_widths: list[Inches] or auto.
        """
        s = self._ns()
        add_action_title(s, title)
        n = len(headers)
        if col_widths is None:
            col_widths = [CW / n] * n
        hdr_y = CONTENT_TOP + Inches(0.1)
        cx = LM
        for hdr, cw in zip(headers, col_widths):
            add_text(s, cx, hdr_y, cw, Inches(0.4), hdr,
                     font_size=BODY_SIZE, font_color=MED_GRAY, bold=True)
            cx += cw
        add_hline(s, LM, hdr_y + Inches(0.45), CW, BLACK, Pt(1.0))
        # --- adaptive row height ---
        row_start_y = hdr_y + Inches(0.55)
        bottom_limit = (BOTTOM_BAR_Y - Inches(0.15)) if bottom_bar else (SOURCE_Y - Inches(0.1))
        avail_h = bottom_limit - row_start_y
        n_rows = len(rows)
        row_h = min(Inches(0.95), avail_h / n_rows) if n_rows > 0 else Inches(0.95)
        # shrink font when rows are compact
        row_font = SMALL_SIZE if row_h >= Inches(0.6) else Pt(10)
        for ri, row in enumerate(rows):
            ry = row_start_y + row_h * ri
            cx = LM
            for val, cw in zip(row, col_widths):
                add_text(s, cx, ry, cw, row_h, val, font_size=row_font)
                cx += cw
            add_hline(s, LM, ry + row_h, CW, LINE_GRAY)
        if bottom_bar:
            add_bottom_bar(s, bottom_bar[0], bottom_bar[1])
        self._footer(s, source)
        return s

    def table_insight(self, title, headers, rows, insights,
                      col_widths=None, insight_title='启示：',
                      source='', bottom_bar=None):
        """Table + right insight panel — McKinsey editorial layout.

        Left ~60%: data table with header row + horizontal-line separated rows.
                   Each row is list[str] matching headers.
                   Supports **bold** markup within cell text.
        Middle: double-chevron arrow icon bridging table → insight.
        Right ~32%: "启示：" title + decorative line + bullet insights.

        Parameters
        ----------
        headers : list[str] — column headers for the table.
        rows : list[list[str]] — each inner list maps to headers.
        insights : list[str] — insight bullet points (shown on the right panel).
        col_widths : list[Inches] or None — custom widths for table columns.
        insight_title : str — title for the right panel (default '启示：').
        """
        import re
        s = self._ns()
        add_action_title(s, title)

        # ── Layout geometry ──
        table_w = Inches(7.2)               # left table area width
        chevron_zone = Inches(0.7)           # middle zone for chevron icon
        insight_w = CW - table_w - chevron_zone  # right insight panel width
        table_x = LM
        chevron_x = LM + table_w             # chevron zone left edge
        insight_x = LM + table_w + chevron_zone

        # ── NO vertical separator line — chevron icon separates visually ──

        # ── Table: header row ──
        n_cols = len(headers)
        if col_widths is None:
            col_widths = [table_w / n_cols] * n_cols
        hdr_y = CONTENT_TOP + Inches(0.1)
        cx = table_x
        for hdr, cw in zip(headers, col_widths):
            add_text(s, cx, hdr_y, cw, Inches(0.4), hdr,
                     font_size=BODY_SIZE, font_color=BLACK, bold=True)
            cx += cw
        add_hline(s, table_x, hdr_y + Inches(0.45), table_w, BLACK, Pt(1.0))

        # ── Table: data rows ──
        row_start_y = hdr_y + Inches(0.55)
        bottom_limit = (BOTTOM_BAR_Y - Inches(0.15)) if bottom_bar else (SOURCE_Y - Inches(0.1))
        avail_h = bottom_limit - row_start_y
        n_rows = len(rows)
        row_h = min(Inches(1.55), avail_h / n_rows) if n_rows > 0 else Inches(1.55)
        row_font = BODY_SIZE if row_h >= Inches(1.0) else SMALL_SIZE

        for ri, row in enumerate(rows):
            ry = row_start_y + row_h * ri
            cx = table_x
            for ci, (val, cw) in enumerate(zip(row, col_widths)):
                # First column (label): bold, vertically centered
                if ci == 0:
                    add_text(s, cx, ry, cw, row_h, val,
                             font_size=SUB_HEADER_SIZE, font_color=BLACK, bold=True,
                             anchor=MSO_ANCHOR.MIDDLE)
                else:
                    # Support **bold** markup in cell text
                    lines = val if isinstance(val, list) else val.split('\n')
                    txBox = s.shapes.add_textbox(cx, ry, cw, row_h)
                    tf = txBox.text_frame
                    tf.word_wrap = True
                    tf.auto_size = None
                    bodyPr = tf._txBody.find(qn('a:bodyPr'))
                    bodyPr.set('anchor', 'ctr')
                    for attr in ['lIns', 'tIns', 'rIns', 'bIns']:
                        bodyPr.set(attr, '45720')
                    for li, line in enumerate(lines):
                        p = tf.paragraphs[0] if li == 0 else tf.add_paragraph()
                        p.space_before = Pt(3) if li > 0 else Pt(0)
                        p.space_after = Pt(0)
                        p.line_spacing = Pt(row_font.pt * 1.35)
                        segments = re.split(r'(\*\*.*?\*\*)', line)
                        for seg in segments:
                            if seg.startswith('**') and seg.endswith('**'):
                                run = p.add_run()
                                run.text = seg[2:-2]
                                run.font.size = row_font
                                run.font.name = FONT_BODY
                                run.font.color.rgb = BLACK
                                run.font.bold = True
                                set_ea_font(run, FONT_EA)
                            elif seg:
                                run = p.add_run()
                                run.text = seg
                                run.font.size = row_font
                                run.font.name = FONT_BODY
                                run.font.color.rgb = DARK_GRAY
                                run.font.bold = False
                                set_ea_font(run, FONT_EA)
                cx += cw
            # Row separator line
            add_hline(s, table_x, ry + row_h, table_w, LINE_GRAY)

        # ── Middle: double-chevron arrow icon ──
        # Vertically centered in the content area, between table and insights
        content_mid_y = CONTENT_TOP + avail_h * 0.42
        chev_size = Inches(0.5)
        chev_shape = s.shapes.add_shape(
            MSO_SHAPE.CHEVRON,
            chevron_x + (chevron_zone - chev_size) // 2,
            content_mid_y,
            chev_size, chev_size)
        chev_shape.fill.solid()
        chev_shape.fill.fore_color.rgb = DARK_GRAY
        chev_shape.line.fill.background()
        _clean_shape(chev_shape)

        # ── Right insight panel ──
        n_insights = len(insights)
        if n_insights > 0:
            insight_area_top = CONTENT_TOP + Inches(0.1)

            # Gray background rectangle for the entire insight panel
            bg_pad = Inches(0.1)  # small padding around the bg
            bg_bottom = bottom_limit + Inches(0.05)
            add_rect(s, insight_x - bg_pad, insight_area_top - bg_pad,
                     insight_w + bg_pad * 2, bg_bottom - insight_area_top + bg_pad * 2,
                     BG_GRAY)

            # "启示：" title (no decorative line above)
            title_y = insight_area_top + Inches(0.1)
            add_text(s, insight_x, title_y, insight_w, Inches(0.45),
                     insight_title,
                     font_size=SUB_HEADER_SIZE, font_color=BLACK, bold=True)

            # Bullet insights — compact, with round bullet •
            bullet_start_y = title_y + Inches(0.55)
            bullet_spacing = Inches(0.15)  # gap between bullets
            # Calculate available height for all insights
            insight_bottom = bottom_limit
            insight_avail = insight_bottom - bullet_start_y
            block_h = (insight_avail - bullet_spacing * (n_insights - 1)) / n_insights if n_insights > 1 else insight_avail

            for ii, ins in enumerate(insights):
                by = bullet_start_y + ii * (block_h + bullet_spacing)

                # Round bullet •
                add_text(s, insight_x, by,
                         Inches(0.25), block_h, '•',
                         font_size=BODY_SIZE, font_color=BLACK, bold=True)
                # Insight text
                add_text(s, insight_x + Inches(0.3), by,
                         insight_w - Inches(0.35), block_h, ins,
                         font_size=BODY_SIZE, font_color=DARK_GRAY,
                         line_spacing=Pt(8))

        if bottom_bar:
            add_bottom_bar(s, bottom_bar[0], bottom_bar[1])
        self._footer(s, source)
        return s

    def scorecard(self, title, items, source=''):
        """#23 Scorecard — items with progress bars.
        items: list of (name, score_str, pct_float_0_to_1)
        """
        s = self._ns()
        add_action_title(s, title)
        headers = ['技术领域', '评分', '成熟度']
        add_text(s, LM, CONTENT_TOP + Inches(0.1), Inches(4.0), Inches(0.4),
                 headers[0], font_size=BODY_SIZE, font_color=MED_GRAY, bold=True)
        add_text(s, Inches(5.0), CONTENT_TOP + Inches(0.1), Inches(1.5), Inches(0.4),
                 headers[1], font_size=BODY_SIZE, font_color=MED_GRAY, bold=True)
        add_text(s, Inches(7.0), CONTENT_TOP + Inches(0.1), Inches(5.5), Inches(0.4),
                 headers[2], font_size=BODY_SIZE, font_color=MED_GRAY, bold=True)
        add_hline(s, LM, CONTENT_TOP + Inches(0.55), CW, BLACK, Pt(1.0))
        bar_max = Inches(5.0)
        ry = CONTENT_TOP + Inches(0.7)
        for name, score, pct in items:
            add_text(s, LM, ry, Inches(4.0), Inches(0.5), name, font_size=BODY_SIZE)
            add_text(s, Inches(5.0), ry, Inches(1.5), Inches(0.5), score,
                     font_size=BODY_SIZE, font_color=NAVY, bold=True)
            add_rect(s, Inches(7.0), ry + Inches(0.05), bar_max, Inches(0.4), BG_GRAY)
            bar_color = NAVY if pct >= 0.7 else ACCENT_ORANGE if pct >= 0.5 else ACCENT_RED
            add_rect(s, Inches(7.0), ry + Inches(0.05), Inches(5.0 * pct), Inches(0.4), bar_color)
            ry += Inches(0.55)
            add_hline(s, LM, ry, CW, LINE_GRAY)
            ry += Inches(0.1)
        self._footer(s, source)
        return s

    # ═══════════════════════════════════════════
    # FRAMEWORK LAYOUTS (#13, #15, #16, #18)
    # ═══════════════════════════════════════════

    def matrix_2x2(self, title, quadrants, axis_labels=None, source='',
                   bottom_bar=None):
        """#13 2×2 Matrix — four quadrants.
        quadrants: list of 4 (label, bg_color, description).
        axis_labels: (x_label, y_label) or None.
        """
        s = self._ns()
        add_action_title(s, title)
        grid_l = LM + Inches(1.8)
        grid_t = Inches(1.45)
        cell_w = Inches(4.5)
        cell_h = Inches(2.0)
        cell_gap = Inches(0.15)
        if axis_labels:
            add_text(s, LM, grid_t + cell_h - Inches(0.25), Inches(1.6), Inches(0.7),
                     axis_labels[1], font_size=BODY_SIZE, font_color=NAVY,
                     bold=True, alignment=PP_ALIGN.CENTER)
            add_text(s, grid_l + cell_w - Inches(0.45), grid_t + 2 * cell_h + cell_gap + Inches(0.03),
                     Inches(3.6), Inches(0.28),
                     axis_labels[0], font_size=BODY_SIZE, font_color=NAVY,
                     bold=True, alignment=PP_ALIGN.CENTER)
        for qi, (label, bg, desc) in enumerate(quadrants):
            row, col = qi // 2, qi % 2
            qx = grid_l + col * (cell_w + cell_gap)
            qy = grid_t + row * (cell_h + cell_gap)
            add_rect(s, qx, qy, cell_w, cell_h, bg)
            add_text(s, qx + Inches(0.2), qy + Inches(0.1), cell_w - Inches(0.4), Inches(0.32),
                     label, font_size=BODY_SIZE, font_color=NAVY, bold=True)
            add_text(s, qx + Inches(0.2), qy + Inches(0.46), cell_w - Inches(0.4), cell_h - Inches(0.56),
                     desc, font_size=Pt(11), font_color=DARK_GRAY)
        if bottom_bar:
            bar_y = Inches(6.26)
            add_rect(s, LM, bar_y, CW, Inches(0.56), BG_GRAY)
            add_text(s, LM + Inches(0.28), bar_y, Inches(1.5), Inches(0.56),
                     bottom_bar[0], font_size=BODY_SIZE, font_color=NAVY,
                     bold=True, anchor=MSO_ANCHOR.MIDDLE)
            add_text(s, LM + Inches(1.95), bar_y, C

... [Content truncated, total 162,557 chars] ...