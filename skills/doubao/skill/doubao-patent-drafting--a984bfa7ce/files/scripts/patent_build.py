#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""专利申请文件审阅稿编译器（单文件、纯标准库、兼容 Python 3.8）。

用法：
    python3 scripts/patent_build.py build --draft draft.md --out output/
    python3 scripts/patent_build.py selftest        （或 --selftest）

draft.md 合同见 SKILL.md；机械检查为 C1-C20。stdout 最后一行固定为：
    PATENT_BUILD: PASS 输出=<docx路径> 检查=<n项通过>
    PATENT_BUILD: FAIL 报告=<report路径>

附图文件约定（draft.md 合同本身不含图片路径字段，属本脚本的补充约定，
非设计文档条款，如需变更请同步告知 SKILL.md 撰写方）：
    真实附图按图号存放在 <draft.md 同级目录>/figures/ 下，文件名为
    「N.png」「N.jpg」「N.jpeg」之一（N 为图号，从 1 开始），可用
    --figures-dir 覆盖该目录。找不到对应文件视为构建失败，不会假装已嵌入。

draft.md 编码约定（同为本脚本的补充约定）：
    draft.md 必须是 UTF-8 编码（可带或不带 BOM）。非 UTF-8 编码（如 GBK/ANSI）
    一律判定为构建失败并给出中文提示，不做静默的乱码替换。
    若 --out 指定的路径已存在但不是目录（与输出目录同名的普通文件），
    同样直接判定失败，不依赖文件系统异常的裸报错。

机械检查 C11 与散文 Markdown 规范化（同为本脚本的补充约定，非设计文档条款）：
    豆包撰写 draft.md 时偶尔会在"散文型"文本——审阅说明的撰写结论/待确认
    事项/边界与免责、说明书各节正文、说明书摘要——里混入行内 Markdown 标记
    （行首 #、成对 **/__、行首 -/*/+ 列表符、``` 代码围栏等），原样渲染进
    docx 会被专家视为格式缺陷。本脚本在"解析之后、写入 docx 之前"对上述散文
    区域自动清理这些标记（不改 draft.md 原文件），并新增 C11 检查：命中即判
    定为 WARN（不阻断构建，因为渲染层已自动清理），在 stdout 的「提示【C11】」
    中列出被清理的具体行与标记类别，便于下次直接产出干净稿。权利要求书区
    （「N. 」编号具语义）与案件头字段行不在清理与检测范围内。

权利要求书条目间空行（同为本脚本的补充约定，非设计文档条款）：
    权利要求书条目之间若留有空行（下一处非空行以「N. 」开头），解析层静默
    忽略该空行，解析结果与不留空行时完全一致，C2 只报一条 WARN 提示下次不要
    留空行，不阻断构建；但若空行出现在同一条权利要求文本中间、把它劈成两截
    （空行后一行不以「N. 」开头），仍判定为 C2 FAIL。

机械检查 C12：发明内容/实用新型内容与权利要求整句照抄检测（同为本脚本的补充
约定，非设计文档条款）：
    专家评测反复点名的失分模式——说明书"发明内容"/"实用新型内容"部分大段
    复制粘贴权利要求原文、不加任何连接语（references/writing-style.md 已有
    文字规则禁止此事，但过去一直没有脚本兜底）。本检查把每条权利要求按中文
    句号/分号切分为子句，过滤掉长度 <25 字的必然重复短子句（如"其特征在
    于"），发明内容/实用新型内容正文做同样切分后逐句比对；比对前分别剥离从
    权引用前缀「根据权利要求N所述的…，其特征在于，」（权利要求侧）与
    「进一步地」等引导词（发明内容侧），只有剥离后去除首尾空白逐字完全一致
    才算命中——像"为解决上述技术问题，本发明提供一种…"这种带连接语、只是
    复述独立权利要求技术方案的规范写法不会被误判。命中数量占权利要求候选
    子句总数比例 ≥60% 判 FAIL，30%~60% 判 WARN，<30% 不报（详见 check_c12）。

机械检查 C13：内部工具名泄漏检测（同为本脚本的补充约定，非设计文档条款）：
    法律文书正文不得出现本 skill 的内部工具、文件名或审计编码痕迹（脚本名 patent_build.py、
    draft.md、SKILL.md、sub-skills、writing-style.md、doubao-patent-drafting、
    stdout 契约字样 PATENT_BUILD:、selftest、修稿报告、P0/P1、A/B/C/D 级等）。扫描范围覆盖全部
    将渲染进 docx 的正文文本——审阅说明（撰写结论/待确认事项/边界与免责）、
    说明书摘要、权利要求书、说明书各节正文；案件头字段行不在扫描范围内（该
    字段的取值合法性另由 C1/C5 等检查覆盖，不与本检查重复）。命中词表任一
    子串即判定为 FAIL，不设 WARN 降级——这是文书事故，不是可以留到下次改进
    的机械噪音（详见 check_c13）。

机械检查 C16-C18：C16 统一公式符号并拦截未定义变量；C17 检查附图标记重名和
仅在标记表出现、正文未使用的编号；C18 在测试或性能状态仍待确认时，拦截
“明显优于”“从根本上解决”等证据强度过高的结论。三项均为 FAIL 级。

draft.md 历史快照（同为本脚本的补充约定，非设计文档条款）：
    构建整体 PASS 且 docx 成功生成后，脚本会把当次 draft.md 原样复制一份到
    <out_dir>/history/draft-<时间戳>.md（时间戳来自 time.strftime，同一秒内
    重复构建自动加序号后缀避免覆盖旧快照），便于事后追溯某次 docx 产出对应
    的源稿版本。快照写入用 try/except 包裹：目录不可写等原因导致快照失败时，
    只在 stdout 打印一行提示，不影响本次构建的 PASS 结论与返回码；stdout 最
    后一行仍固定为 PATENT_BUILD 结论行（详见 _snapshot_draft_history）。
"""

import argparse
import datetime
import re
import struct
import sys
import time
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# =====================================================================
# 第一段：解析 draft.md
# =====================================================================

@dataclass(frozen=True)
class Line:
    no: int
    text: str


@dataclass(frozen=True)
class Claim:
    number: Optional[int]
    text: str
    line_no: int


@dataclass(frozen=True)
class PendingItem:
    level: str
    event: str
    impact: str
    line_no: int


@dataclass(frozen=True)
class SpecSection:
    title: str
    heading_line_no: int
    lines: List[Line]

    def text(self) -> str:
        return "".join(l.text.strip() for l in self.lines if l.text.strip())


REQUIRED_H1 = ["案件头", "审阅说明", "说明书摘要", "权利要求书", "说明书"]
REQUIRED_REVIEW_H2 = ["撰写结论", "待确认事项", "边界与免责"]
CONTENT_TITLE_BY_CASE_TYPE = {"发明": "发明内容", "实用新型": "实用新型内容"}

FIELD_LINE_RE = re.compile(r"^-\s*([^:：]+?)\s*[:：]\s*(.*)$")
DRAWING_STATUS_RE = re.compile(
    r"^真实附图(\d+)幅$|^规划图名(\d+)条$|^无$|^真实附图(\d+)幅[＋+]规划图名(\d+)条$")
MARKER_ENTRY_RE = re.compile(r"^(\d+)\s*[=＝]\s*(\S.*)$")
CLAIM_START_RE = re.compile(r"^(\d+)\.\s*(.*)$")
PENDING_ITEM_RE = re.compile(r"^-\s*\[(本次定稿前需要确认|正式提交前建议确认)\]\s*(.+)$")
PENDING_LEVEL_BY_LABEL = {
    "本次定稿前需要确认": "P0",
    "正式提交前建议确认": "P1",
}
PENDING_LABEL_BY_LEVEL = {level: label for label, level in PENDING_LEVEL_BY_LABEL.items()}


@dataclass
class Draft:
    source_path: str
    parse_notes: List[str] = field(default_factory=list)

    h1_order: List[str] = field(default_factory=list)

    case_header_fields: Dict[str, Tuple[str, int]] = field(default_factory=dict)
    unparsed_header_lines: List[Line] = field(default_factory=list)
    case_type: Optional[str] = None
    invention_name: Optional[str] = None
    subject_entity: Optional[str] = None  # 主题实体（阶段一按整机口径登记，C19 比对）
    drawing_status_raw: Optional[str] = None
    drawing_mode: Optional[str] = None  # "real" | "planned" | "mixed" | "none" | None(非法)
    drawing_count: int = 0  # 附图说明应列出的总图数（mixed = 真实+规划）
    real_figure_count: int = 0  # 需要嵌入 docx 的真实图数（图1..M，v7 实测：仅有部分外观图的案件必须能混合声明）
    marker_table_raw: Optional[str] = None
    marker_table: Dict[int, str] = field(default_factory=dict)
    marker_table_bad_entries: List[str] = field(default_factory=list)

    review_h2_order: List[str] = field(default_factory=list)
    conclusion_lines: List[Line] = field(default_factory=list)
    pending_items: List[PendingItem] = field(default_factory=list)
    boundary_lines: List[Line] = field(default_factory=list)

    abstract_lines: List[Line] = field(default_factory=list)

    claims_present: bool = False
    claims: List[Claim] = field(default_factory=list)
    claims_body_lines: List[Line] = field(default_factory=list)
    claims_leading_orphan: List[Line] = field(default_factory=list)
    claims_interior_blank_line_nos: List[int] = field(default_factory=list)
    claims_blank_separator_line_nos: List[int] = field(default_factory=list)

    spec_h2_order: List[str] = field(default_factory=list)
    spec_sections: Dict[str, SpecSection] = field(default_factory=dict)

    def abstract_text(self) -> str:
        return "".join(l.text.strip() for l in self.abstract_lines if l.text.strip())

    def all_spec_lines(self) -> List[Line]:
        result: List[Line] = []
        for title in self.spec_h2_order:
            section = self.spec_sections.get(title)
            if section:
                result.extend(section.lines)
        return result

    def spec_full_text(self) -> str:
        return "".join(l.text.strip() for l in self.all_spec_lines() if l.text.strip())


def _heading_level(line_text: str) -> Tuple[Optional[int], Optional[str]]:
    m = re.match(r"^(#{1,6})[ \t]+(.*\S)[ \t]*$", line_text)
    if not m:
        return None, None
    return len(m.group(1)), m.group(2).strip()


def _split_by_level(lines: List[Line], level: int) -> List[Tuple[str, int, List[Line]]]:
    """按标题层级切分为 [(标题, 标题所在行号, 内容行列表)]；内容行含更深层标题原文。"""
    sections: List[Tuple[str, int, List[Line]]] = []
    title: Optional[str] = None
    heading_no = 0
    body: List[Line] = []
    for line in lines:
        lvl, text = _heading_level(line.text)
        if lvl == level:
            if title is not None:
                sections.append((title, heading_no, body))
            title, heading_no, body = text, line.no, []
        else:
            if title is not None:
                body.append(line)
    if title is not None:
        sections.append((title, heading_no, body))
    return sections


def _parse_case_header(content: List[Line], draft: Draft) -> None:
    for line in content:
        if not line.text.strip():
            continue
        m = FIELD_LINE_RE.match(line.text.strip())
        if not m:
            draft.unparsed_header_lines.append(line)
            continue
        key, value = m.group(1).strip(), m.group(2).strip()
        draft.case_header_fields[key] = (value, line.no)

    if "案件类型" in draft.case_header_fields:
        draft.case_type = draft.case_header_fields["案件类型"][0]
    if "发明名称" in draft.case_header_fields:
        draft.invention_name = draft.case_header_fields["发明名称"][0]
    if "主题实体" in draft.case_header_fields:
        draft.subject_entity = draft.case_header_fields["主题实体"][0]
    if "附图状态" in draft.case_header_fields:
        raw = draft.case_header_fields["附图状态"][0]
        draft.drawing_status_raw = raw
        m = DRAWING_STATUS_RE.match(raw)
        if m:
            if raw == "无":
                draft.drawing_mode, draft.drawing_count = "none", 0
            elif m.group(1) is not None:
                draft.drawing_mode, draft.drawing_count = "real", int(m.group(1))
                draft.real_figure_count = int(m.group(1))
            elif m.group(2) is not None:
                draft.drawing_mode, draft.drawing_count = "planned", int(m.group(2))
            else:
                real, planned = int(m.group(3)), int(m.group(4))
                draft.drawing_mode = "mixed"
                draft.real_figure_count = real
                draft.drawing_count = real + planned
    if "附图标记表" in draft.case_header_fields:
        raw = draft.case_header_fields["附图标记表"][0]
        draft.marker_table_raw = raw
        if raw != "无":
            for piece in re.split(r"[,，、]", raw):
                piece = piece.strip()
                if not piece:
                    continue
                m = MARKER_ENTRY_RE.match(piece)
                if m:
                    draft.marker_table[int(m.group(1))] = m.group(2).strip()
                else:
                    draft.marker_table_bad_entries.append(piece)


def _parse_review_note(content: List[Line], draft: Draft) -> None:
    h2_sections = _split_by_level(content, 2)
    draft.review_h2_order = [t for t, _, _ in h2_sections]
    for title, _, body in h2_sections:
        if title == "撰写结论":
            draft.conclusion_lines = body
        elif title == "待确认事项":
            for line in body:
                stripped = line.text.strip()
                if not stripped:
                    continue
                m = PENDING_ITEM_RE.match(stripped)
                if not m:
                    draft.parse_notes.append(
                        "待确认事项 第{}行 无法识别：{}".format(line.no, stripped)
                    )
                    continue
                label, rest = m.group(1), m.group(2)
                level = PENDING_LEVEL_BY_LABEL[label]
                if "：" in rest:
                    event, impact = rest.split("：", 1)
                elif ":" in rest:
                    event, impact = rest.split(":", 1)
                else:
                    event, impact = rest, ""
                draft.pending_items.append(
                    PendingItem(level=level, event=event.strip(), impact=impact.strip(), line_no=line.no)
                )
        elif title == "边界与免责":
            draft.boundary_lines = body


def _parse_claims(content: List[Line], draft: Draft) -> None:
    """解析权利要求书正文。

    条目之间的空行（空行之后的下一处非空行以「N. 」开头，是新条目的起点）按
    补充约定静默吞掉：不计入任何权项文本，解析结果与不留空行时完全一致；只是
    把行号记入 claims_blank_separator_line_nos，供 check_c2 报一条 WARN 提示。
    若空行出现在同一条权项文本中间——空行之后的下一处非空行不是以「N. 」开头
    （即只是被空行打断的续行）——判定为真正的文本断裂，行号记入
    claims_interior_blank_line_nos，供 check_c2 报 FAIL。
    """
    draft.claims_present = True
    start, end = 0, len(content)
    while start < end and not content[start].text.strip():
        start += 1
    while end > start and not content[end - 1].text.strip():
        end -= 1
    body = content[start:end]
    draft.claims_body_lines = body

    number: Optional[int] = None
    text_parts: List[str] = []
    claim_line_no = 0
    saw_first_number = False

    def flush() -> None:
        if number is not None:
            draft.claims.append(Claim(number=number, text="".join(text_parts), line_no=claim_line_no))

    n = len(body)
    i = 0
    while i < n:
        line = body[i]
        stripped = line.text.strip()
        if not stripped:
            blank_run = [line.no]
            j = i + 1
            while j < n and not body[j].text.strip():
                blank_run.append(body[j].no)
                j += 1
            # body 的首尾空行已在上面裁掉，因此这里 j < n 恒成立：空行之后必有
            # 非空内容可供判断——要么是下一条「N. 」，要么是被打断的续行。
            next_stripped = body[j].text.strip()
            if saw_first_number and CLAIM_START_RE.match(next_stripped):
                draft.claims_blank_separator_line_nos.extend(blank_run)
            else:
                draft.claims_interior_blank_line_nos.extend(blank_run)
            i = j
            continue
        m = CLAIM_START_RE.match(stripped)
        if m:
            flush()
            saw_first_number = True
            number, claim_line_no = int(m.group(1)), line.no
            text_parts = [m.group(2)]
        elif not saw_first_number:
            draft.claims_leading_orphan.append(line)
        else:
            text_parts.append(stripped)
        i += 1
    flush()


def _parse_specification(content: List[Line], draft: Draft) -> None:
    h2_sections = _split_by_level(content, 2)
    draft.spec_h2_order = [t for t, _, _ in h2_sections]
    for title, no, body in h2_sections:
        draft.spec_sections[title] = SpecSection(title=title, heading_line_no=no, lines=body)


def parse_draft(text: str, source_path: str) -> Draft:
    draft = Draft(source_path=source_path)
    raw_lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    lines = [Line(i + 1, t) for i, t in enumerate(raw_lines)]

    h1_sections = _split_by_level(lines, 1)
    draft.h1_order = [t for t, _, _ in h1_sections]
    for title, _, body in h1_sections:
        if title == "案件头":
            _parse_case_header(body, draft)
        elif title == "审阅说明":
            _parse_review_note(body, draft)
        elif title == "说明书摘要":
            draft.abstract_lines = body
        elif title == "权利要求书":
            _parse_claims(body, draft)
        elif title == "说明书":
            _parse_specification(body, draft)
    return draft


# =====================================================================
# 第 1.5 段：散文文本 Markdown 规范化（渲染前清理 与 C11 检查共用同一实现）
# =====================================================================

_MD_FENCE_RE = re.compile(r"^[ \t]*```")
_MD_HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(\S.*)$")
_MD_LIST_RE = re.compile(r"^([-*+])[ \t]+(\S.*)$")
_MD_BOLD_RE = re.compile(r"\*\*(.+?)\*\*|__(.+?)__")
_MD_ITALIC_RE = re.compile(r"(?<!\*)\*([^*\n]+)\*(?!\*)|(?<!_)_([^_\n]+)_(?!_)")
_MD_CODE_RE = re.compile(r"`([^`\n]+)`")
_MD_NUM_LIST_SPACE_RE = re.compile(r"^(\d+)\.[ \t]{2,}(\S.*)$")

MD_HIT_LABELS = {
    "heading": "标题标记（行首 #）",
    "list": "列表标记（行首 -/*/+）",
    "bold": "加粗标记（**/__）",
    "italic": "斜体标记（*/_）",
    "code": "行内代码标记（`）",
    "fence": "代码围栏标记（```）",
}


def normalize_prose_markdown(text: str) -> Tuple[str, List[str]]:
    """清理散文型文本中残留的行内 Markdown 标记，返回（清理后文本, 命中类别列表）。

    调用方必须只传入"散文"区域文本（审阅说明撰写结论/待确认事项/边界与免责、
    说明书摘要、说明书各节正文）：权利要求书内「N. 」编号是语义编号，案件头
    字段行另有专门语法，两者都不得经过本函数处理。

    命中类别（用于 C11 提示与 MD_HIT_LABELS 对照）：
        heading 行首 #{1,6}（去标记，原文按普通段落保留）
        list    行首 -/*/+ 列表符（转换为「・」前缀，保留原缩进文字）
        bold    成对 **x**/__x__ （去标记保留 x）
        italic  成对 *x*/_x_ （去标记保留 x；不成对的孤立 */_ 不处理）
        code    成对反引号 `x`（去标记保留 x）
        fence   独占一行的 ``` 代码围栏（整行清空，不渲染空段落）
    行首「N. 」数字列表在非权利要求区仅做多余空格归一，不计入命中类别（不算
    Markdown 残留缺陷，属于纯粹的空白整理）。
    """
    hits: List[str] = []
    s = text

    if _MD_FENCE_RE.match(s):
        return "", ["fence"]

    m = _MD_HEADING_RE.match(s)
    if m:
        hits.append("heading")
        s = m.group(2)

    m = _MD_LIST_RE.match(s)
    if m:
        hits.append("list")
        s = "・" + m.group(2)

    if _MD_BOLD_RE.search(s):
        hits.append("bold")
        s = _MD_BOLD_RE.sub(lambda mo: mo.group(1) if mo.group(1) is not None else mo.group(2), s)

    italic_replaced = _MD_ITALIC_RE.sub(
        lambda mo: mo.group(1) if mo.group(1) is not None else mo.group(2), s)
    if italic_replaced != s:
        hits.append("italic")
    s = italic_replaced

    if _MD_CODE_RE.search(s):
        hits.append("code")
        s = _MD_CODE_RE.sub(r"\1", s)

    m = _MD_NUM_LIST_SPACE_RE.match(s)
    if m:
        s = "{}. {}".format(m.group(1), m.group(2))

    return s, hits


# =====================================================================
# 第二段：机械检查 C1-C12
# =====================================================================

@dataclass(frozen=True)
class Issue:
    check: str
    severity: str  # FAIL | WARN
    location: str
    problem: str
    fix: str


def check_c1(draft: Draft) -> List[Issue]:
    """结构：案件头字段齐全；必需章节存在且顺序正确；案件类型与内容标题匹配。"""
    issues: List[Issue] = []

    for note in draft.parse_notes:
        issues.append(Issue(
            "C1", "FAIL", "审阅说明/待确认事项", note,
            "待确认事项仅使用“本次定稿前需要确认”或“正式提交前建议确认”两类对外标签，"
            "不要使用 P0/P1 等内部代码。"))

    for line in draft.unparsed_header_lines:
        issues.append(Issue("C1", "FAIL", "案件头 第{}行".format(line.no),
                             "无法识别的案件头字段行：「{}」。".format(line.text.strip()),
                             "按「- 字段: 值」格式书写，字段名与冒号之间不要多余符号。"))

    required_fields = ["案件类型", "发明名称", "主题实体", "附图状态", "附图标记表"]
    for f in required_fields:
        if f not in draft.case_header_fields or not draft.case_header_fields[f][0].strip():
            issues.append(Issue("C1", "FAIL", "案件头",
                                 "缺少必填字段「{}」。".format(f),
                                 "在「# 案件头」下补充「- {}: <值>」一行。".format(f)))

    if draft.case_type is not None and draft.case_type not in ("发明", "实用新型"):
        issues.append(Issue("C1", "FAIL", "案件头/案件类型",
                             "案件类型取值「{}」不合法。".format(draft.case_type),
                             "案件类型只能是「发明」或「实用新型」二者之一。"))

    if draft.drawing_status_raw is not None and draft.drawing_mode is None:
        issues.append(Issue("C1", "FAIL", "案件头/附图状态",
                             "附图状态取值「{}」不合法。".format(draft.drawing_status_raw),
                             "附图状态写「真实附图N幅」「规划图名N条」「无」之一；既有真实图又有规划图时写"
                             "「真实附图M幅+规划图名N条」（真实图占图1..M，按图号存 figures/ 目录）。"))

    if draft.marker_table_bad_entries:
        issues.append(Issue("C1", "FAIL", "案件头/附图标记表",
                             "附图标记表中以下条目无法解析：{}。".format("、".join(draft.marker_table_bad_entries)),
                             "每条标记须写成「编号=名称」，多条之间用逗号或顿号分隔，例如「1=柜体, 7=玻璃门」。"))

    if draft.h1_order != REQUIRED_H1:
        issues.append(Issue("C1", "FAIL", "draft.md 章节结构",
                             "顶级章节应依次为 {}，实际为 {}。".format(REQUIRED_H1, draft.h1_order),
                             "按 draft.md 合同固定骨架调整章节的增删与顺序（不得缺项、多项或错序）。"))

    if draft.review_h2_order != REQUIRED_REVIEW_H2:
        issues.append(Issue("C1", "FAIL", "审阅说明 子章节",
                             "「审阅说明」下子章节应依次为 {}，实际为 {}。".format(REQUIRED_REVIEW_H2, draft.review_h2_order),
                             "补齐「## 撰写结论」「## 待确认事项」「## 边界与免责」三节且保持该顺序。"))

    if draft.case_type in CONTENT_TITLE_BY_CASE_TYPE and draft.drawing_mode is not None:
        expected = ["发明名称", "技术领域", "背景技术", CONTENT_TITLE_BY_CASE_TYPE[draft.case_type]]
        if draft.drawing_mode in ("real", "planned", "mixed"):
            expected.append("附图说明")
        expected.append("具体实施方式")
        if draft.spec_h2_order != expected:
            other_title = "实用新型内容" if draft.case_type == "发明" else "发明内容"
            hint = ""
            if other_title in draft.spec_h2_order:
                hint = "案件类型为「{}」，说明书标题应使用「{}」而非「{}」。".format(
                    draft.case_type, CONTENT_TITLE_BY_CASE_TYPE[draft.case_type], other_title)
            else:
                hint = "按案件类型与附图状态调整「说明书」下子标题的增删与顺序。"
            issues.append(Issue("C1", "FAIL", "说明书 子章节",
                                 "「说明书」下子章节应依次为 {}，实际为 {}。".format(expected, draft.spec_h2_order),
                                 hint))
    return issues


def check_c2(draft: Draft) -> List[Issue]:
    """权项格式：编号连续从1起；每项恰好一个句尾句号；无项目符号/链接。

    条目之间的空行不再判为 FAIL：解析层已静默忽略（结果与不留空行时完全一致），
    这里改报一条 WARN 提示下次不要留空行。但空行把同一条权项文本从中间劈成两截
    （空行后一行不以「N. 」开头）时，仍是真正的断裂，判 FAIL。
    """
    issues: List[Issue] = []
    if not draft.claims_present:
        return issues

    if draft.claims_leading_orphan:
        first = draft.claims_leading_orphan[0]
        issues.append(Issue("C2", "FAIL", "权利要求书 第{}行".format(first.no),
                             "权利要求书正文首行不是编号权利要求：「{}」。".format(first.text.strip()),
                             "删除编号之外的说明文字，权利要求书应直接以「1. 」开始逐条列出。"))

    for no in draft.claims_interior_blank_line_nos:
        issues.append(Issue("C2", "FAIL", "权利要求书 第{}行".format(no),
                             "权利要求书内部出现空行，把一条权利要求的正文打断成了两截"
                             "（空行后一行不是以「N. 」开头的新条目）。",
                             "删除该空行，把被打断的正文重新接续为同一条完整陈述。"))

    if draft.claims_blank_separator_line_nos:
        line_list = "、".join(str(no) for no in draft.claims_blank_separator_line_nos)
        issues.append(Issue("C2", "WARN", "权利要求书 第{}行".format(line_list),
                             "权利要求书条目间存在空行（第{}行），已自动忽略；解析结果与不留空行时完全一致。".format(line_list),
                             "下次书写时权项之间请不要留空行，各条应前后相接、连续排列。"))

    for line in draft.claims_body_lines:
        stripped = line.text.strip()
        if not stripped:
            continue
        if re.match(r"^[-*+•·]\s", stripped):
            issues.append(Issue("C2", "FAIL", "权利要求书 第{}行".format(line.no),
                                 "出现项目符号：「{}」。".format(stripped),
                                 "权利要求书只能用「N. 」阿拉伯数字编号，不得使用项目符号。"))
        if re.search(r"\[[^\]]*\]\([^)]*\)", stripped):
            issues.append(Issue("C2", "FAIL", "权利要求书 第{}行".format(line.no),
                                 "出现 Markdown 链接语法：「{}」。".format(stripped),
                                 "权利要求书为纯文本陈述，删除链接语法。"))

    numbers = [c.number for c in draft.claims]
    expected = list(range(1, len(numbers) + 1))
    if numbers != expected:
        issues.append(Issue("C2", "FAIL", "权利要求书",
                             "权利要求编号应从 1 开始连续排列，实际序列为 {}。".format(numbers),
                             "重新核对权利要求编号，确保连续、不跳号、不重复。"))

    for claim in draft.claims:
        count = claim.text.count("。")
        ends_ok = claim.text.rstrip().endswith("。")
        if count != 1 or not ends_ok:
            issues.append(Issue("C2", "FAIL", "权利要求书 第{}行（第{}项）".format(claim.line_no, claim.number),
                                 "本条应恰好包含一个句尾中文句号，实际检测到 {} 个句号，且{}。".format(
                                     count, "末尾是句号" if ends_ok else "末尾不是句号"),
                                 "将本条改写为一段完整陈述，仅在结尾使用一个「。」，条内并列请用顿号、逗号或分号。"))
    return issues


DEP_REF_RE = re.compile(r"^根据权利要求([0-9、，,至或任一项中\s]+?)所述的([^，,。；;]+)[，,]")
INDEP_SUBJECT_RE = re.compile(r"^一种([^，,。；;]+)[，,]")


def _parse_ref_numbers(clause: str) -> List[int]:
    range_m = re.search(r"(\d+)\s*至\s*(\d+)", clause)
    if range_m:
        lo, hi = int(range_m.group(1)), int(range_m.group(2))
        if lo <= hi:
            return list(range(lo, hi + 1))
    return [int(n) for n in re.findall(r"\d+", clause)]


def _claim_profile(claim: Claim) -> Dict:
    m = DEP_REF_RE.match(claim.text)
    if m:
        return {"dependent": True, "refs": _parse_ref_numbers(m.group(1)), "subject": m.group(2).strip()}
    m2 = INDEP_SUBJECT_RE.match(claim.text)
    if m2:
        return {"dependent": False, "refs": [], "subject": m2.group(1).strip()}
    return {"dependent": False, "refs": [], "subject": None}


def _subject_consistent(a: Optional[str], b: Optional[str]) -> bool:
    if a is None or b is None:
        return True
    return a == b or a.endswith(b) or b.endswith(a)


def check_c3(draft: Draft) -> List[Issue]:
    """引用关系：从权引用编号<自身编号且存在；主题词一致；多引用从权不引用多引用从权。"""
    issues: List[Issue] = []
    if not draft.claims:
        return issues
    profiles = {c.number: _claim_profile(c) for c in draft.claims if c.number is not None}

    for claim in draft.claims:
        if claim.number is None:
            continue
        profile = profiles[claim.number]
        if not profile["dependent"]:
            continue
        loc = "权利要求书 第{}行（第{}项）".format(claim.line_no, claim.number)
        refs = profile["refs"]
        if not refs:
            issues.append(Issue("C3", "FAIL", loc,
                                 "本条以「根据权利要求…所述的」引用他项，但未能解析出被引用的编号。",
                                 "使用标准句式「根据权利要求N所述的<主题>」「…N或M所述的…」「…N至M中任一项所述的…」。"))
            continue
        for ref in refs:
            if ref >= claim.number:
                issues.append(Issue("C3", "FAIL", loc,
                                     "第{}项引用了第{}项，引用编号必须小于本项编号。".format(claim.number, ref),
                                     "改为引用编号更小的在先权利要求，或调整权利要求排列顺序。"))
                continue
            if ref not in profiles:
                issues.append(Issue("C3", "FAIL", loc,
                                     "第{}项引用的权利要求{}不存在。".format(claim.number, ref),
                                     "核对权利要求编号，删除或修正无效引用。"))
                continue
            ref_subject = profiles[ref]["subject"]
            if not

... [Content truncated, total 94,319 chars] ...