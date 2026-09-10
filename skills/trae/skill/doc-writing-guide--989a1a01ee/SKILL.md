---
name: doc-writing-guide
description: >
  Primary skill for document and content writing. Triggers on PRD, product
  requirements, MVP spec, feature spec, tech proposal, research report,
  competitive analysis, manuals, and any structured written deliverable.
  Governs intent interpretation, genre & format selection, writing-style
  calibration, content structuring, visual generation guidance, and
  sub-scenario routing to specialized references (e.g., PRD routes to
  references/prd-document.md).
---

## 1. Interpret Intent Before Writing

Your primary goal is to understand the *spirit* of the user's request, not just the literal words.

### 1.1 Intake Analysis

On receiving a writing task, actively analyze the prompt:

1. **Purpose** — What is the underlying goal? (inform, persuade, educate, entertain, sell, document)
2. **Audience** — Who will read this? (executives, engineers, general public, domain experts, students)
3. **Tone & Mood** — What emotional register fits? (formal, conversational, authoritative, playful, sober)
4. **Scope** — Is this a quick draft, a polished deliverable, or an iterative collaboration?
5. **Constraints** — Word count, language, format (Markdown, PDF, DOCX, Lark doc), branding requirements.

### 1.2 Persona Adoption

Based on the analysis above, creatively adopt the most appropriate writing persona. Do not default to a neutral, safe style. Strive for a result that reflects the user's true intent, even if not explicitly stated.

- Be bold — if context calls for a witty critic, patient teacher, enthusiastic evangelist, or sober analyst, embody that persona.
- When the user's preference is unclear, default to **rich, comprehensive, and well-structured content** — unless the user explicitly requests brevity.

### 1.3 Clarification Threshold

Ask clarifying questions **only** when ambiguity would lead to a fundamentally different deliverable. For minor uncertainties, make a reasonable assumption, state it, and proceed.

---

## 2. Genre & Format Selection

Before writing, determine the most appropriate genre and reference style.

### 2.1 Genre Identification

| Genre                         | Typical Triggers                                | Key Characteristics                                    |
| ----------------------------- | ----------------------------------------------- | ------------------------------------------------------ |
| **Academic / Research Paper** | "paper", "study", "literature review"           | Formal, evidence-based, structured sections, citations |
| **Technical Documentation**   | "docs", "API guide", "README", "specification"  | Precise, task-oriented, code examples, clear hierarchy |
| **Blog Post / Article**       | "blog", "article", "post", "write about"        | Engaging lead, conversational, opinion-allowed         |
| **News / Journalism**         | "news", "report on event", "coverage"           | Inverted pyramid, attribution, neutral tone            |
| **Opinion / Essay**           | "essay", "opinion", "argue", "perspective"      | Thesis-driven, persuasive, personal voice              |
| **Tutorial / How-to**         | "tutorial", "guide", "how to", "step by step"   | Progressive disclosure, practical, hands-on            |
| **Marketing / Copy**          | "landing page", "copy", "campaign", "pitch"     | Benefit-focused, concise, call-to-action               |
| **Creative / Narrative**      | "story", "narrative", "creative writing"        | Show-don't-tell, vivid prose, character/scene-driven   |
| **Internal Memo / Brief**     | "memo", "brief", "internal", "summary for team" | Direct, action-oriented, audience-aware                |
| **Product Requirements**      | "PRD", "requirements", "spec", "user stories"   | Structured, unambiguous, acceptance criteria           |

### 2.2 Reference Style Calibration

Identify classic works, renowned publications, or established writing styles relevant to the target genre. Use these as **inspiration** — blend, modify, or transcend them as needed.

Examples:

- Travel guide → adopt **Lonely Planet**'s narrative warmth and practical specificity.
- Technical deep-dive → channel **Stripe's engineering blog** clarity and progressive depth.
- Business analysis → reference **Harvard Business Review**'s analytical rigor with accessible language.
- Product launch → emulate **Apple Newsroom**'s concise, benefit-led storytelling.

### 2.3 Multi-Format Awareness & Default Artifact Routing

**Default artifact rule for report-type tasks** (research reports, whitepapers, PRDs, proposals, competitive analyses, feasibility studies, technical documents, and any structured written deliverable):

> **Default → `html-report` skill.** Unless the user **explicitly** states that the final deliverable must be a `.docx` or `.pdf` file, route the artifact production to the `html-report` skill (which produces a self-contained HTML report). Keywords that trigger format-specific routing:
> - `.docx` / Word / DOCX → route to `docx` skill
> - `.pdf` / PDF → route to `pdf` skill
>
> Vague requests like "write a report", "draft a PRD", "do a research report" **without** mentioning a specific file format → always use the `html-report` skill as the artifact format.

When the output format **is** explicitly specified (PDF, DOCX, Lark doc, Markdown, webpage), adapt formatting conventions accordingly and delegate format-specific rendering to the appropriate sub-Skill or tool Skill (e.g., `pdf`, `docx`, `pptx`).

***

## 3. Language to Avoid

### 3.1 Anti-Patterns in Task Descriptions

When delegating to agents or planning content, **never** use checklist-style, corporate-jargon, or workaholic language in task descriptions:

❌ **Prohibited phrasing:**

- "可操作", "可执行", "检查清单", "可参考", "定期复盘", "x 天行动计划"
- "actionable checklist", "30-day action plan", "weekly review cadence"
- Framing human experiences as optimizable workflows

❌ **Do NOT write task descriptions like this:**

> 面向职场与高校的普通读者，围绕"吸引力—社交拓展—沟通—约会—推进关系—复盘"的完整路径设计。
> 每章给出可落地动作与话术示例，避免空泛理论。读完即可开干。
> 建议配合"30 天行动计划"和"每周复盘"，在 4–8 周内感受到明显变化。

✅ **Instead, phrase naturally:**

> 在探讨如何"脱单"之前，我们首先需要明白，这并非一场狩猎游戏，而是一场向内探索、而后向外连接的旅程。市面上充斥着太多关于"技巧"和"套路"的讨论，仿佛爱情是一场可以通过公式计算和策略部署来赢得的战役。然而，这种观念恰恰是通往真挚关系的最大障碍。

### 3.2 Anti-Patterns in Content Body

| Avoid                                              | Prefer                                                   |
| -------------------------------------------------- | -------------------------------------------------------- |
| Imperative checklists disguised as prose           | Descriptive, explanatory language                        |
| Translationese (stiff literal translations)        | Idiomatic, natural phrasing in the target language       |
| Excessive jargon without context                   | Technical terms introduced with brief inline explanation |
| Over-compressed bullet storms                      | Flowing paragraphs where logical flow matters            |
| Empty superlatives ("world-class", "cutting-edge") | Specific, evidence-backed claims                         |
| Formulaic section stubs ("参考资料", "致谢", "附件列表")     | Include only if explicitly requested or genuinely needed |
| Rhetorical or persuasive section headings          | Descriptive, neutral headings stating what the section covers |
| Stiff, bureaucratic, or overly abstract wording ("进行赋能", "实现闭环", "显式标注") | Plain, conversational phrasing a non-specialist can parse on first read |
| Coinage overload — stacking self-invented abstract nouns ("飞轮", "入口层", "会话层", "协作语义") | Max ONE coined abstraction per paragraph; replace the rest with concrete descriptions of what actually happens |
| Saying the same conclusion 3 times in different words across sections (intro summary ≈ core judgment ≈ conclusion) | State a conclusion ONCE in its canonical location; other sections may reference it but must add new evidence or angle, never just rephrase |

### 3.3 Sections to Avoid Unless Requested

Do NOT create these sections by default — only include them when the user explicitly asks:

- "图表与附件" / "附件列表"
- "参考资料" / "References" / "Bibliography"
- "致谢" / "Acknowledgments"
- "数据源" / "Data Sources"
- "XX清单" / "XX Checklist"

### 3.4 Paragraph-Level Anti-Patterns

| Rule | Description | Violation Example |
| ---- | ----------- | ----------------- |
| **No heading-echo** | A section's first sentence must NOT restate or explain what the heading already says. Open with a fact, data point, or decision. | ❌ "本章介绍用户增长策略。" / "This section covers the authentication flow." |
| **No meta-narration** | Never use self-referential narration that describes what the text is about to do. Jump straight into substance. | ❌ "下面我们来看…" / "接下来将详细分析…" / "Let us now examine…" |
| **No "manifesto" openers** | Do not open a paragraph or article with "这不是一篇…而是…" / "真正的问题不是…而是…" / "本文试图…". Readers judge the text by its content, not by the author's self-positioning. | ❌ "这不是一篇并购新闻解读，而是一篇从浏览器热议反推公司成长逻辑的复盘。" |
| **No insight-escalation frames** | Eliminate rhetorical "not X but Y" structures whose sole purpose is to sound profound. State the real judgment directly without the contrast crutch. Common offenders: "真正的X不是……而是……", "这不仅仅是……更是……", "最后比拼的是……", "不应只是X，而应Y", "本质上不是X，而是Y". | ❌ "这次活动不应只是送券，而应围绕核心价值设计成…" → ✅ "活动以一次有效使用触发即时奖励，把奖品和产品价值感绑定。" |
| **One-statement rule** | A conclusion may appear in full exactly ONCE in its canonical section. Other sections that reference it must contribute new evidence or a new angle — never merely rephrase. | ❌ Intro says "A是核心壁垒", body says "A构成关键护城河", conclusion says "A最终成为不可替代的优势" |

### 3.5 Sentence-Level Anti-Patterns

| Rule | Description | Fix |
| ---- | ----------- | --- |
| **No dummy-verb structures** | Eliminate "进行"/"开展"/"实施" + noun patterns. Use the verb directly. | "进行分析" → "分析"；"开展调研" → "调研"；"实施优化" → "优化" |
| **No unverifiable "确保"** | When "确保" is followed by an unverifiable goal, replace with a measurable criterion. | ❌ "确保用户体验良好" → ✅ "页面加载 ≤ 2s，操作反馈 ≤ 200ms" |
| **No empty intensifiers** | Delete "非常"/"极其"/"highly"/"extremely"/"significantly" when not followed by quantitative evidence. | ❌ "显著提升了效率" → ✅ "处理时间从 4.2s 降至 1.1s" |

### 3.6 Formatting Discipline

| Rule | Description |
| ---- | ----------- |
| **Bold scope** | Bold is reserved for: proper nouns, tool/command names, and critical warnings. Do NOT use bold for rhetorical emphasis in running prose — rely on sentence structure to convey importance. Limit: ≤ 3 bold spans per section. |
| **No bold+italic stacking** | `***text***` is forbidden. |
| **No emoji unless requested** | Documents must not contain emoji or decorative Unicode symbols unless the user explicitly asks. (✅❌⚠️ are permitted only in checklist/diagnostic contexts within the skill itself, not in user-facing deliverables.) |
| **No punctuation in headings** | Markdown headings must not end with periods, colons, or question marks (exception: genuine question headings). |

***

## 4. Content Structure

### 4.1 Structure Selection

Based on the genre and purpose, determine the most appropriate delivery approach:

| Approach       | Best For                                                          | Characteristics                                                                   |
| -------------- | ----------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| **Structured** | Technical docs, reports, tutorials, PRDs                          | Clear sections, headings, numbered steps, organized frameworks                    |
| **Narrative**  | Feature articles, travel guides, opinion pieces, creative content | Storytelling flow, scene-setting, character/example-driven                        |
| **Free-form**  | Personal essays, creative writing, exploratory thought pieces     | Organic idea development, flexible organization                                   |
| **Hybrid**     | Complex deliverables, long-form analysis                          | Strategic blend — e.g., narrative intro → structured body → reflective conclusion |

### 4.2 Key Principles

- **Substance over format** — structure serves content, never constrains it.
- **Never pre-impose components** — do NOT instruct agents to follow a rigid outline (e.g., "must contain Introduction, Background, Summary, Conclusion") before content development. The optimal structure emerges as insights develop.
- **Soft guidance over hard templates** — provide inspirational references (e.g., "refer to *Stripe's engineering blog* for structure inspiration") rather than prescriptive section lists.
- **Adapt to complexity** — a simple answer needs no headings; a 5,000-word analysis needs clear hierarchy.

### 4.3 Formatting Guidelines

| Element             | Guideline                                                                                                              |
| ------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| **Headings**        | Brief, concise, functional — convey the section's purpose at a glance                                                  |
| **Emphasis**        | Strategic use of **bold** for key concepts, principles, data points. Avoid over-bolding                                |
| **Visual elements** | Callouts, tables, inline code, diagrams — embedded naturally within text flow                                          |
| **Paragraphs**      | 3–8 sentences for most content; shorter for high-impact points                                                         |
| **Lists**           | Use when information is naturally list-like (options, features, steps, pros/cons). For extended analysis, prefer prose |
| **Transitions**     | Make logical flow explicit — "Building on this…", "In contrast…", "This raises the question of…"                       |

### 4.4 Richtext Formatting (Lark/Feishu Documents)

When writing `lark.md` documents, reference the `Lark/Feishu Markdown Writing Styles Guide` in the knowledge base and make full use of rich lark.md syntax features — callouts, grids, code blocks, tables, and embedded visual elements.

---

## 5. Visual Generation Guide

### 5.1 When to Generate Visuals

- User explicitly requests charts, diagrams, or illustrations, **OR**
- Content involves ≥3 comparable data points (numbers, percentages, metrics) where a chart conveys the relationship faster than prose, **OR**
- A trend, ranking, or proportion is being described in text that would take fewer words with a visual, **OR**
- A process, architecture, or relationship would be clearer as a diagram than as prose.

**Bias toward visualization**: When in doubt whether data warrants a chart, prefer generating one. A simple bar or line chart that reinforces the text is better than a paragraph of numbers that readers must mentally parse.

### 5.2 Constraints

- Chart data must be sourced and accurate — no interpolation of missing intervals, no fabricated numbers.
- Place visuals immediately after the relevant analysis paragraph, not grouped in an appendix.
- Caption every visual with a clear, descriptive label.

### 5.3 Type Selection

| Purpose                        | Default Type                                       |
| ------------------------------ | -------------------------------------------------- |
| Trend over time                | Line chart                                         |
| Magnitude comparison           | Bar chart                                          |
| Proportion breakdown           | Pie (≤6 slices) / Stacked bar                      |
| Multi-dimensional relationship | Scatter / Radar                                    |
| Process / Decision flow        | Flowchart (Graphviz or PlantUML)                   |
| System architecture            | Architecture diagram (Graphviz)                    |
| Sequential interaction         | Sequence diagram (PlantUML)                        |
| Timeline / Schedule            | Gantt chart (PlantUML)                             |
| Structured comparison          | Table (preferred over chart when data is discrete) |

### 5.4 Integration Principles

- **Seamless embedding** — weave visuals into text flow rather than clustering them in a separate section.
- **Visual–text correspondence** — every chart or diagram must be referenced and explained in the surrounding prose.
- **Accessibility** — provide alt-text or descriptive captions so content is understandable without the visual.

---

## 6. Sub-Scenario Routing

Route to the matched reference based on the writing task's genre, purpose, and deliverable type. Each reference inherits all constraints from this parent and adds domain-specific templates, structures, quality gates, and workflow steps.

> **Invocation method**: When routing to a sub-scenario, **Read** the corresponding reference file from `references/` in this skill's directory (e.g., `references/prd-document.md`) and follow the instructions within. Do NOT attempt to recall the reference content from memory — always load the file to ensure the full, up-to-date instructions are applied.

### 6.1 Routing Table

| Reference | File | Route When |
|-----------|------|------------|
| `interact-prd-document` | `references/interact-prd-document.md` | User asks for the prototype-centered interactive PRD paradigm: a persistent clickable prototype as the primary review surface, paired with linked requirement text. Evaluate explicit signals for this row first. This reference owns content logic; for HTML structure, visual system, and interaction templates, invoke the `html-report` skill rather than reading its internal reference files directly. |
| `prd-document` | `references/prd-document.md` | User asks for a conventional chapter-based PRD. HTML output may and usually should contain interactive prototype demos embedded inside functional requirement sections. |

### 6.2 Routing Decision Rules

Apply these rules in order. Stop at the first matching rule.

1. **Explicit paradigm signal → prototype-centered interactive PRD.** Route to `interact-prd-document.md` when the prompt says any equivalent of:
   - 可交互 PRD、交互式 PRD、interactive PRD、原型式 PRD、prototype-first PRD
   - 以原型为核心、原型优先、原型是主体、先体验再看需求
   - 左侧原型右侧文档、左右结构、分屏 PRD、原型常驻
   - 原型和需求联动、点击原型定位需求、双向联动、预览/文本模式切换
2. **Explicit artifact description → prototype-centered interactive PRD.** Route to `interact-prd-document.md` when the user asks for one self-contained HTML artifact whose main experience is clicking through a complete product prototype while reading linked requirements beside it. The literal phrase “可交互 PRD” is sufficient; do not downgrade it to the conventional PRD route.
3. **Prototype-centered review intent → interactive PRD.** Route to `interact-prd-document.md` when the user emphasizes reviewing screens, flows, and states through one prominent persistent prototype, even if they do not name the left/right layout.
4. **Embedded-demo intent → conventional PRD.** Route to `prd-document.md` when the user wants a normal PRD structure with background, goals, and functional requirement chapters, with interactive demos embedded inside the relevant chapters or modules.
5. **Generic PRD → conventional PRD.** If the prompt only says PRD/需求文档/产品需求/功能说明, route to `prd-document.md`. Its default HTML output can still contain interactive prototypes; “interactive” is not exclusive to the prototype-centered reference.
6. **Format constraints.** Explicit text-only Markdown, DOCX, or PDF routes to `prd-document.md` unless the user also requests a separate interactive HTML companion.
7. **Tie-break by document architecture.** Ask which architecture the user wants only when both are equally plausible and the choice would materially change the deliverable. Otherwise, use explicit wording; if none exists, default to the conventional chapter-based PRD.
8. **Fall through to this skill.** If no reference matches, handle the task directly using §1–§5.
9. **Compound tasks.** Route each distinct deliverable independently.

### 6.3 Routing Examples

| User Request | Route | Reason |
|---|---|---|
| “写一个会员积分 PRD” | `prd-document` | Generic PRD with no prototype signal |
| “写一个会员积分 PRD，每个功能章节配可点击 Demo” | `prd-document` | Conventional chapters with embedded demos |
| “做一个会员积分可交互 PRD，以完整原型为主体，右侧联动需求” | `interact-prd-document` | Explicit prototype-centered paradigm |
| “给客服工作台做左右分屏 PRD，点击页面定位对应规则” | `interact-prd-document` | Persistent prototype and linked document |
| “输出客服工作台 PRD，纯文字 Markdown，不要原型” | `prd-document` | Explicit static override |
| “用 HTML 写完整 PRD，在需求详情中嵌入高保真原型” | `prd-document` | Embedded prototype inside conventional PRD |
