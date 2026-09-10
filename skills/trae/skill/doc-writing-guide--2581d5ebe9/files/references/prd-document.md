---
name: prd-document
description: >
  Sub-Skill for dynamically generating Product Requirements Documents (PRDs).
  Dynamically determines PRD depth and structure based on product stage, business scenario, and complexity.
  Core focus: Functional Requirements Detail (tables + interactive prototype Demo) to ensure engineers can develop directly.
  Inherits intent interpretation, genre selection, writing style, and visualization guidance from doc-writing-guide.
---

# PRD Document

## Relationship to Parent Skill

This Skill inherits all constraints from `doc-writing-guide` (intent interpretation, genre selection, language to avoid, content structure principles, visualization generation guide). The following content extends the parent.

## Default Output Format

- No format specified → use `html-report` skill to produce HTML deliverable.
- User explicitly requests `.docx` / `.pdf` / `.md` → route to corresponding format skill.

## Page Color Scheme (applies to HTML output)

Automatically match color scheme based on Dimension A (Industry Domain). When user hasn't specified a style preference, follow the table below:

| Industry Domain | Style Keywords |
|-----------------|----------------|
| Finance | Steady, trustworthy, professional |
| Healthcare | Clean, professional, reassuring |
| E-commerce/Retail | Energetic, conversion-driven, eye-catching |
| Education | Friendly, growth-oriented, clear |
| Hardware/IoT | Techy, precise, modern |
| Manufacturing/Industrial | Solid, functional, industrial |
| Entertainment/Gaming | Creative, dynamic, youthful |
| Government/Public | Formal, authoritative, dignified |
| General Software | Neutral, modern, minimalist |

**Usage Rules:**

- Primary color applies to: page header/sidebar, H1 headings, primary buttons, link color
- Accent color applies to: background base, card backgrounds, hover states, secondary info areas
- Text color unified: heading text on white backgrounds uses primary color
- If the user explicitly specifies a color preference in conversation, user preference overrides industry default

---

## Core Principles

1. The core goal of a PRD is to enable downstream roles (UX, Engineer, Market, etc.) to understand the feature and execute their tasks. Don't pursue length — pursue information density. Every paragraph, table, and Demo must be useful.
2. Unless the user requests it, do not generate acceptance criteria, milestones, iteration roadmaps, or other chapters that "look professional" but provide no direct help.
3. In functional requirements, prioritize outputting interactive prototypes (HTML/CSS/JS) so readers can understand requirements through interaction, then accompany with detailed text descriptions.
4. When critical information is missing, ask the user for clarification.

---

## Workflow

```
Step 1: Based on requirement classification, determine requirement type and complexity
Step 2: Based on PRD module structure, determine which chapters to write
Step 3: Targeted elicitation — ask clarifying questions when info is insufficient (max 2 rounds)
Step 4: Write PRD based on available content
Step 5: Quality self-check — internal check before output (not shown to user)
```

---

## Requirement Classification

### Requirement Type

Classify the user's query across the following three independent dimensions (select one per dimension, combinations allowed):

**Dimension A: Industry Domain** (determines compliance requirements and domain terminology)

| Category | Scope |
|----------|-------|
| Finance | Banking, insurance, securities, payments, lending |
| Healthcare | Pharma, devices, internet healthcare, health management |
| E-commerce/Retail | E-commerce platforms, new retail, O2O, supply chain |
| Education | K12, vocational education, online learning platforms |
| Hardware/IoT | Consumer electronics, smart devices, industrial hardware |
| Manufacturing/Industrial | Production manufacturing, industrial software, MES/ERP |
| Entertainment/Gaming | Content platforms, social, gaming, live streaming |
| Government/Public | Government digitization, smart cities, public services |
| General Software | Tools, productivity, not tied to a specific industry |

**Dimension B: Business Model** (determines functional complexity and role decomposition)

| Category | Characteristics | PRD Impact |
|----------|----------------|------------|
| toC | Serving individual consumers | Focus on interaction experience, light permissions, growth metrics |
| toB | Serving enterprise customers | Focus on role permissions, multi-tenancy, delivery and configuration |
| toG | Serving government/public institutions | Focus on compliance auditing, formal writing style, acceptance criteria |
| Platform | Connecting multiple parties (e.g., buyers & sellers, providers & consumers) | Multiple role perspectives equally important, balancing interests |

**Dimension C: Organization Type** (determines document style and process norms)

| Category | Characteristics | PRD Impact |
|----------|----------------|------------|
| Internet company | Agile iteration, flat structure | Concise and direct, efficiency-focused, light on process |
| Traditional enterprise/SOE | Hierarchical, process-oriented | Formal and complete, heavy on approval flows, requires org structure |
| Startup | Limited resources, rapid validation | Focus on MVP, hypothesis validation, light on non-core modules |

### Requirement Complexity

Determine document depth based on requirement scope:

| Requirement Scope | Complexity | Typical Length |
|-------------------|------------|----------------|
| 0-to-1 product | Heavyweight | 10+ pages |
| New module | Light or Medium (**default**) | 2–10 pages |
| Small iteration | Light or Medium (**default**) | 2–10 pages |

---

## PRD Module Structure

### Module Overview

| Module | Light | Medium (default) | Heavyweight |
|--------|-------|-------------------|-------------|
| Requirement Background | Required (brief) | Required | Required (full) |
| Requirement Objectives | Merge into Background | Merge into Background | Required (full) |
| Market/Competitive Analysis | Omit | As needed (when user mentions competitors or product has clear competitors) | Required (full market analysis + competitive comparison) |
| User Stories | Omit | Omit | As needed |
| Glossary | Omit | Omit | As needed |
| **Functional Requirements Detail** | **Required** | **Required** | **Required** |
| Tracking & Metrics | Omit | Omit | As needed |
| Staffing & Timeline | Omit | Omit | As needed |

### Industry-Specific Modules (include only when industry matches)

Include only when the requirement clearly matches the corresponding industry, presented in concise form:

- **AI Products**: Accuracy definition, evaluation system, fallback mechanisms
- **Finance/Compliance**: Regulatory basis, permission matrix, audit requirements
- **Hardware Products**: Hardware specs, production testing, after-sales process
- **Enterprise SaaS**: Tenant isolation, role permissions, integration APIs

> Industry-specific content should not be over-elaborated; describe as needed based on the specific requirement.

### Default-OFF Modules (generate only when user explicitly requests)

The following modules are **never generated proactively** unless the user explicitly states the need:

| Module | Trigger Condition |
|--------|-------------------|
| Non-goals | User explicitly says "need to define non-goals" |
| Acceptance Criteria | User explicitly says "need acceptance criteria" or requirement involves finance/compliance with strict regulation |
| Iteration Plan | User explicitly says "need iteration plan" or "plan future versions" |
| Operations Plan | User explicitly says "need operations plan" or the solution is operations-related |

> **Core logic:** Small and medium requirements don't need these "professional-looking" chapters that provide no practical help for development. Writing good functional requirements detail matters more than anything.

### User Custom Module Handling

Users may mention content outside the predefined module list in their query. Processing rules:

- Based on the user's description, assess the amount of content and its relationship to existing chapters to decide whether a new chapter is needed.
- If a new chapter is needed, arrange it flexibly within the PRD structure.
- If not needed, flexibly insert it into existing modules.

---

# Writing Guide for Each PRD Module

## Writing Style

- **Plain language first**: Use everyday wording; avoid jargon like "empower", "leverage", "synergy", "end-to-end"
- **PRD describes "what", not "how"**: Do not specify technical implementation (database types, programming languages, framework choices)
- **Prototype first**: For product interactions, prioritize HTML interactive Demos; use wireframes as needed
- **No fabrication**: Mark unconfirmed data as `[To be confirmed]`; mark AI inferences as `[Assumption — to be confirmed]`
- **Chapter hierarchy**: Top-level chapters are the modules mentioned below; second-level chapters are sub-modules within them.

---

## Requirement Background

- Business trigger source (who raised it, why now)
- Current user pain points (use concrete scenarios, not abstract summaries)
- This section should ideally include `[Data-backed]` / `[Research-backed]` / `[PM judgment]` annotations

---

## Requirement Objectives

Based on the requirement scenario and the user's query, decide how to write objectives. Generally there are two types: qualitative and quantitative. If the user hasn't provided quantitative objectives, establish qualitative objectives based on the scenario.

**Note: "Qualitative" and "quantitative" are definitions for understanding only — they don't need to be labeled in the PRD.**

**Qualitative objectives** — Based on user insights or business needs; applicable to pre-launch products or products where data analysis is difficult. Even qualitative objectives should be quantified as much as possible.

> **Good example:**
> User research (N=2000) shows the top 3 factors affecting purchase decisions are A (30%) / B (20%) / C (10%). This requirement strengthens factor A's exposure on the product detail page to stimulate purchase intent.
>
> **Bad example:**
> This requirement uses various methods to stimulate purchase intent and improve conversion rate.

**Quantitative objectives** — For launched, stable products where data metric changes can be estimated. Use the new requirement as an input action, and forward-derive output value changes (not reverse-decompose from macro metrics).

> **Good example:**
> Current course completion rate is 80%. Among non-completing users, 10% experience XX problem. This requirement optimizes XX, expected to raise completion rate to 85%.

---

## Market Analysis & Competitive Analysis

### Market Analysis

Applicable to 0-to-1 products or heavyweight requirements. Describe target market size, growth trends, policy/technology windows, and entry timing.

### Competitive Analysis

**Core Approach:**

Competitive analysis is not about listing information — it's about extracting methodology from information. The value-creation path is:

```
Information (enumerate features/pages) → Knowledge (classify, identify patterns) → Methodology (abstract reusable strategies)
```

Through competitive analysis and summarization, extract competitor methodology, apply it to your product's context, and find actionable insights.

**Analysis Perspectives (use in combination, don't just look at the surface):**

| Perspective | Description |
|-------------|-------------|
| Product front & back end | Don't just look at what the C-end pages look like; also analyze traffic strategies, distribution logic, recommendation strategies, cold-start strategies |
| Multi-functional view | Product, operations, finance, and brand all influence product design (e.g., a free tool's ad strategy stems from monetization constraints) |
| Time perspective | Is the competitor at MVP stage, growth stage, or profitability stage? Each stage has different priorities |

**Output Format:**

1. **Conclusion first** — The answer to your core question, methodology abstracted from competitor practices
2. **Evidence support** — Only show key evidence that supports your conclusion; no need to be exhaustive
3. **Tabular comparison** — Use tables to show core differences between competitors
4. Annotate sources and timeliness when using web search
5. Competitive analysis doesn't need to be long — just answer the core question

---

## User Stories

- Target user personas (role, usage frequency, pain severity)
- Core usage scenarios (sorted by priority)
- Role differences (if multi-role, distinguish each role's perspective and needs)

---

## Glossary

If the requirement introduces new specialized terms, define and explain them to avoid inconsistent naming and unclear references.

Product design must ensure: **Every term is understandable to users, and the name for the same object is always consistent.**

> Simple requirements and team-internal conventions don't need separate explanation. This module is not mandatory.

---

## Functional Requirements Detail (The Absolute Core of the PRD)

> ⚠️ **This is the PRD's most important chapter and must comprise 50%+ of total content.**

Functional requirements detail has two structural styles; choose one based on requirement characteristics:

**Style Selection Rules:**
- ≥3 functional modules with independent interactions → Style 1 (each module with its own prototype)
- Features can be listed flat, modules are tightly coupled, or total count ≤5 → Style 2 (one large table + overall prototype)

### Style 1: Organized by Function + Interactive Demo

Suitable for scenarios with multiple functional modules where each module needs independent prototype presentation. Every functional module must have a corresponding prototype; prototypes must correspond one-to-one with the logic descriptions below — no omissions allowed.

Organize by page/functional module sections. Each module contains the following content (output in this order):

**1) Interactive Prototype Demo**

Place at the top of each module so readers first understand the requirement through interaction.

**2) Page Layout (required)**

- Describe what regions/areas the current page or module is composed of, and what responsibility and task each region carries
- Help readers establish structural understanding before reading detailed logic

**3) Business Logic (required)**

- Based on the interactive prototype above, clearly describe the current module's: user trigger conditions → processing rules → output results → state changes
- Use complete sentences, not fragmented bullets

**4) Interaction Logic (as needed)**

- If the prototype is already interactive, this can be omitted.
- If the prototype is static, write out system feedback for each operation: user action → system response → page/state change.

**5) Field Rules (as needed)**

| Field Name | Type | Required | Length/Range | Default |
|------------|------|----------|--------------|---------|
| Example field | Text | Yes | 2-30 chars | None |

**6) State Transitions (as needed, low priority)**
Include only when the functional module involves state transitions.
| Current State | Allowed Operations | Next State | Trigger Condition |
|---------------|-------------------|------------|-------------------|
| Pending Review | Approve/Reject | Approved/Rejected | Reviewer action |

**7) Permission Logic (as needed, low priority)**
Include only when the functional module involves role-based permissions.
| Role | Visible Scope | Operable Content | Data Isolation |
|------|---------------|------------------|----------------|
| Admin | All | All operations | None |
| Regular User | Own only | View/edit own only | Isolated by user |

**8) Boundary & Exceptions (as needed, low priority)**
- Handling for network errors, concurrency conflicts, empty data, insufficient permissions, etc.

---

### Style 2: Feature Detail Table + Interactive Demo

Suitable for scenarios where features can be listed flat and a single large table provides a full overview.

**Feature Detail Table:**
| # | Feature Module | Prototype Demo | Feature Description (≥150 words, including business logic + interaction flow + key rules) |
|---|----------------|----------------|------------------------------------------------------------------------------------------|
| 1 | Module name | Embedded interactive Demo | What the feature does → how users operate → how the system responds → what business rules apply |

**Requirements:**

- Each row's "Feature Description" column must be ≥150 words, including: what it does + how to interact + what rules apply
  - Can use paragraph narration
  - Can also use itemized points
- Enumerate **all** feature points for the product/page — no omissions allowed

---

### Interactive Prototype Demo (common to both styles)

> **When PRD is output in HTML format, every functional module must embed an interactive prototype Demo.**

**Requirements:**

1. **Implemented in HTML/CSS/JS**, embedded directly in the document — users can interact upon opening the HTML
2. **Visual requirements**: Approximate real product layout and styling, not crude wireframes
3. **Correspondence**: Every area in the Demo must correspond one-to-one with the feature description text, linked via annotation numbers

**Prototype must include:**

- All functional areas with boundary markers
- Field positions with constraint annotations
- Action buttons with their states (enabled/disabled/loading)
- At least 2 states displayed (e.g., normal + empty state, or default + post-action state)

**Fallback for non-HTML output:**

- Mermaid flowcharts/state diagrams (suitable for logical relationships)
- ASCII wireframes (suitable for simple layouts)

---

## Quality Self-Check (internal execution, not output to user)

All checks below are **static content reviews** performed by reading the generated code and text. Do NOT open the HTML file in a browser, launch a dev server, or use browser_use tools to validate the output.

After generation, internally check the following 3 items. If any fail, revise until they pass:

| # | Check Item | Pass Criteria |
|---|-----------|---------------|
| 1 | **Feature description sufficient** | Each functional module's detail description paragraph ≥150 words and contains the complete trigger → processing → result chain; no features described in just one sentence |
| 2 | **Prototypes complete** | Every functional module has a corresponding prototype |
| 3 | **No redundant chapters** | Did not generate acceptance criteria, milestones, iteration plans, or other OFF modules the user didn't request |

---

## Related Skills

| Skill | Relationship |
|-------|-------------|
| `html-report` | PRD's default output format, handles HTML rendering and interaction |
| `/comparison-analysis` | Can be called first for reference data during competitive research |
