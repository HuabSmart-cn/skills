---
name: interact-prd-document
description: >
  Reference for writing prototype-centered interactive PRDs. Use for 可交互 PRD,
  交互式 PRD, 原型式 PRD, prototype-first PRD, left-prototype/right-document
  layouts, and requests where one persistent clickable prototype is the primary
  review surface. Owns product reasoning, requirement structure, business rules,
  feature depth, and prototype-content correspondence. HTML structure, visual
  styling, responsive behavior, and interaction templates are provided by the
  html-report skill.
---

# Interactive PRD Document

## Relationship to Parent Skill

This reference inherits all writing and routing constraints from `doc-writing-guide`. It defines the content logic for prototype-centered interactive PRDs, not the HTML template or visual system. Do not load `prd-document.md` in parallel unless a shared classification rule is genuinely needed; where the two conflict, this reference wins.

## Responsibility Boundary

This file owns:

- requirement reasoning, evidence classification, assumptions, and open questions;
- product contract definition, P0/P1/P2 scoping, role/object/state modeling;
- right-side PRD tab content expectations and feature-section depth;
- prototype-content correspondence, stable feature IDs, and business-rule consistency;
- content anti-patterns and content-level quality gates.

This file does not own:

- split-screen HTML shell, phone/browser frame markup, CSS variables, theme palettes, typography, responsive layout, mode-switching JavaScript, tab-switching JavaScript, data-link event implementation, resize-handle behavior, or accessibility implementation details.

For those structure and style requirements, invoke the `html-report` skill. Do not read `html-report` internal reference files directly from this content skill; `html-report` is responsible for loading its own scenario references.

## When to Use This Reference

Use this reference instead of plain `prd-document` when:

- User explicitly requests a 可交互 PRD, 交互式 PRD, interactive PRD, 原型式 PRD, or prototype-first PRD.
- User requests a left-prototype/right-document, split-screen, prototype-persistent, or prototype-requirement-linked layout.
- User says the prototype should be the main review surface and the requirement text should support it.
- User expects one complete prototype to carry a multi-page or multi-state core flow while linked requirements remain available beside it.

Do not use when:

- Requirement is purely strategy/data/policy and has no UI or operational flow.
- User explicitly requests text-only `.md`, `.docx`, or PDF output and does not ask for an interactive companion.
- Requirement has only one simple page with no interaction flow.
- User wants a conventional top-to-bottom PRD whose functional chapters each embed their own interactive demo; that belongs to `prd-document.md`.

## Core Principles

1. **Prototype as review surface**: The prototype is the primary way readers inspect screens, flows, states, and requirement mappings.
2. **Prototype-document linkage**: Every meaningful prototype area must correspond to a right-side requirement section through stable feature IDs.
3. **Dual reading contexts**: Support both quick product review through the prototype and implementation-oriented reading through the requirement document.
4. **Requirement fidelity**: Never invent critical business facts. Mark assumptions as `[假设，待确认]` and unknown values as `[待确认]`.
5. **State fidelity**: Key actions must change visible product state. A button that only displays an alert does not count as a functional prototype behavior.
6. **Progressive depth**: Let users understand the product at three levels: product summary, clickable flow, and implementation-ready rules.
7. **Decision over description**: A PRD must state what the product will do under concrete conditions. Avoid merely describing pages or repeating the user's feature list.
8. **Core flow over feature inventory**: Build the smallest complete user journey first. Secondary features must not dilute the main task or appear in the prototype without a clear role.

## Requirement Reasoning Before Prototyping

The prototype is the primary review surface, but it must be derived from product reasoning rather than visual improvisation. Complete the following analysis internally before designing screens.

### Evidence, Judgment, and Unknowns

Classify every important input into one of four categories:

| Category | Meaning | How to Use |
|---|---|---|
| Confirmed fact | Explicitly supplied by the user or supported by a named source | May support decisions directly |
| Product judgment | A design decision derived from confirmed context | State the reasoning when the decision materially affects scope or flow |
| Assumption | A plausible condition needed to continue | Mark `[假设，待确认]`; do not present it as user-provided truth |
| Open question | Missing information that could change permissions, money movement, compliance, or the core flow | Mark `[待确认]`; ask only when proceeding would create a fundamentally different product |

Do not fabricate research sample sizes, conversion rates, SLA values, fees, legal conclusions, or user preferences. When the user supplies evidence, connect it to a specific design response instead of placing it in a decorative background paragraph.

**Decision chain:**

```text
Evidence or observed problem
→ affected user and moment
→ product decision
→ prototype behavior
→ requirement rule
→ observable outcome
```

Every major feature should be traceable through this chain.

### Define the Product Contract

Before expanding features, determine:

1. **Primary user and core job**: one primary operator and the outcome they must complete.
2. **Trigger**: what event or need starts the flow.
3. **Completion condition**: what visible or persisted state means the job is done.
4. **Trust model**: what the user must understand or believe before taking consequential action.
5. **System responsibility**: what the product guarantees, records, calculates, routes, or communicates.
6. **User responsibility**: what users must provide, confirm, or resolve.

For multi-role products, identify the shared object that connects roles, such as an order, ticket, application, task, case, or document. Define who can change that object's state and under what conditions.

### Scope the Smallest Complete Journey

Prioritize by journey completeness rather than by number of features:

| Priority | Definition |
|---|---|
| P0 | Required to enter, complete, or recover the core journey |
| P1 | Removes a major operational burden or trust barrier after P0 works |
| P2 | Optimization, personalization, growth, convenience, or advanced administration |

The default prototype demonstrates all P0 behavior and only the P1 behavior needed to understand the product. Mention relevant P2 ideas briefly only if the user asks for future scope. Do not create screens for speculative features merely to make the product appear complete.

Use a short internal scope test for each proposed feature:

- Which user problem does it resolve?
- Where does it enter the core journey?
- What breaks if it is removed?
- Is it a requirement, an assumption, or an implementation idea?

### Model Roles, Objects, and States

For products with multiple actors or consequential workflows, derive three linked models:

**Role model**

| Role | Goal | Can See | Can Change | Restricted From |
|---|---|---|---|---|
| Example | Complete assigned work | Assigned records | Status and owned fields | Other teams' private data |

**Object model**

| Object | Created By | Key Fields | Lifecycle Owner | Related Objects |
|---|---|---|---|---|
| Example | User | ID, status, amount | Platform | Payment, dispute |

**State model**

| Current State | Trigger | Preconditions | Next State | User Feedback | Failure Recovery |
|---|---|---|---|---|---|
| Example | Draft | Submit | Required fields valid | Pending review | Confirmation and timestamp | Keep draft and show field errors |

Do not output these tables mechanically. Use them to prevent contradictions across screens, permissions, labels, and requirement sections. Include a table only when readers need it.

### Identify Consequential Decisions

Apply extra depth when an action changes money, ownership, permissions, public visibility, compliance status, or irreversible data. For each consequential action define:

- actor and authorization;
- required confirmation;
- idempotency or duplicate-action handling;
- success evidence and audit record;
- cancellation or reversal rules;
- timeout and retry behavior;
- notification recipients;
- manual fallback or escalation.

This applies especially to payments, refunds, approvals, publishing, deletion, account changes, AI-generated decisions, and dispute handling.

---

## Product Blueprint Before Rendering

Before asking `html-report` to render the interactive PRD, derive a compact blueprint from the request:

| Blueprint Item | Required Decision |
|---|---|
| Primary user | Who operates the product and in what context |
| Core job | The one outcome the prototype must make possible |
| Happy path | Entry → key action → confirmation/result |
| Completion condition | The state that proves the core job has finished |
| Shared object | The order, ticket, task, case, document, or other object whose lifecycle drives the flow |
| Key screens | Usually 3–7 screens or major states; merge trivial screens |
| Critical states | Default, loading, empty, success, error, disabled, or permission-limited as relevant |
| P0 scope | Features required to complete and recover the core journey |
| Requirement modules | Stable feature IDs used by both prototype and document |
| Visual direction context | Product domain, user context, density, and brand cues passed to `html-report`; do not define CSS here |

Do not expose this blueprint as a generic planning chapter. Use it to keep the prototype, copy, and requirements internally consistent.

## Output Content Architecture

The final deliverable should follow the prototype-centered PRD paradigm:

- Left side: one persistent interactive prototype that demonstrates the core journey.
- Right side: tab-based PRD content whose feature sections map to prototype elements.
- Document mode: a long-form PRD view for reading and review outside the split layout.
- Linkage: stable feature IDs connect prototype elements and requirement sections.

The exact HTML shell, frame markup, CSS, JavaScript, responsive behavior, and visual polish are owned by the `html-report` skill.

## Right-Side PRD Content

The interactive paradigm changes the delivery format, not the amount of information. The right-side tabbed document must still cover the core content any standard PRD should have.

### PRD Module Inventory

| Module | Required? | Notes |
|---|---|---|
| Background | Required, concise | Who, why now, current pain; concrete scenario over abstract summary |
| Goals | Required | Qualitative or quantitative; do not fabricate metrics; mark unknowns `[TBD]` |
| Market / competitive | Conditional | Only when user provides info or it materially affects design |
| Glossary | Conditional | Only when proprietary terms appear |
| User stories | Conditional | Only for multi-role products or non-obvious scenarios |
| Functional detail | Required core | Linked feature modules; this should occupy most of the right panel |
| Acceptance / milestones / staffing / metrics / non-goals | Default off | Add only when the user explicitly asks |

Good functional detail matters more than stacking professional-looking sections that do not help design or engineering.

### Tab Structure

Use 3-5 tabs. Minimum: Overview + at least one middle tab + Detail, so the right panel does not look sparse. Do not create empty tabs, but actively use justified middle tabs such as research, user analysis, product design, or information architecture when content exists.

| Tab ID | Tab Name | Carries | Notes |
|---|---|---|---|
| `tab-overview` | Overview / 概览 | Background, goals, scope, glossary when needed | Required |
| `tab-research` | Custom | Market, user analysis, competitive analysis, user stories, or product design | Add when content exists |
| `tab-detail` | Detail / 需求详情 | Functional detail | Required; bulk of content |
| `tab-rules` | Rules / 规则与异常 | Cross-module permissions, states, calculations, boundaries | Add when shared rules would otherwise repeat |
| `tab-metrics` | Metrics & Tracking | Data metrics and instrumentation | Only if user explicitly asks |
| `tab-plan` | Schedule & Milestones | Iteration, milestones, staffing | Only if user explicitly asks |

### Content Expectations by Tab

**Overview / 概览**

- Lead with the observed problem and affected user moment.
- Connect evidence to the selected product response.
- State the primary user, core job, completion condition, and P0 scope.
- Separate confirmed facts, product judgments, assumptions, and open questions.
- Avoid generic claims such as “提升体验” or “打造闭环”; describe the actual change in user or system behavior.
- Do not place document title or metadata such as version, date, or status badge inside the Overview tab. Those belong to the fixed top bar and Text Mode header.
- The Overview tab must not be sparse. Include at least 2-3 substantive paragraphs covering background, goals, and scope. If information is limited, add target user profile or core value proposition.

**Research / Product Design middle tabs**

- Show the core journey before listing screens.
- Explain why each major screen or state exists in that journey.
- For multi-role products, make handoffs and ownership changes explicit.
- Identify the shared business object and its lifecycle.
- Keep navigation and information architecture subordinate to task completion.

**Detail / 需求详情**

- Organize by user task or business capability, not by arbitrary visual regions.
- Give every feature a stable name used consistently in the prototype.
- Explain decisions that are not obvious from the interface.
- Avoid repeating the same rules in multiple feature cards; move shared rules to `tab-rules`.
- This tab is the PRD core. It should carry most requirement detail and be dense enough for downstream implementation.

**Rules / 规则与异常**

- Consolidate cross-module field, permission, calculation, timing, notification, and status rules.
- Cover only realistic exceptions that alter user decisions or system state.
- Distinguish recoverable errors, blocked actions, and cases requiring manual intervention.
- For consequential actions, define confirmation, audit evidence, reversal, retry, and escalation.

## Left-Side Prototype Content

Each prototype must include:

- all pages needed for the core flow, not every conceivable settings or administrative page;
- navigation logic that makes the user's journey understandable;
- realistic sample data and product-native labels;
- meaningful states such as default, loading, empty, success, error, disabled, or permission-limited;
- stable feature IDs that map to right-side requirement sections;
- visible feedback for local interactions through state, copy, motion, or focus changes;
- reversible exploration through back, close, reset, or edit actions.

### Prototype Positioning and Boundaries

| It is | It is not |
|---|---|
| Hi-fi clickable demo of the core user flow | A wireframe or greyscale sketch |
| The primary review surface pulled out of functional detail | A code deliverable or runnable project |
| A self-contained product review artifact | A CDN/API/build-tool dependent project |
| Covers all pages required by the core flow | Every conceivable settings or admin page |

### Page Completeness Constraints

1. Every `onclick="navigate('page-xxx')"` must have a corresponding `.page#page-xxx`. No click-does-nothing dead ends.
2. Every feature module mentioned in Detail must have a reachable prototype page or state.
3. All visually clickable elements such as buttons, cards, list items, nav menus, and tab bar items must bind to valid behavior. No dead buttons.
4. Purely decorative elements may be inert, but anything with hover effects or `cursor: pointer` must respond.
5. If a feature is outside MVP scope but has a UI entry point, show a deliberate unavailable-state response; never leave it silently unresponsive.

### Interaction State Model

Use a small conceptual state model rather than disconnected one-off behaviors. The visible UI must always be derivable from product state such as current page, selected object, filters, form values, submission status, permissions, and active workflow step.

Buttons must perform realistic transitions such as adding a record, applying a filter, opening details, validating a form, or changing status. Avoid `alert()` as the primary response.

### Prototype Copy

- Use concise, product-native labels and realistic sample values.
- Maintain one name for each object across navigation, fields, tables, and requirement text.
- Include helper text and errors where users could reasonably hesitate.
- Never use Lorem ipsum, “示例标题 1”, repeated placeholder cards, or unexplained dummy metrics.

## Right Panel: Feature Section Structure

Each functional module in the "需求详情" Tab is wrapped in a `.feature-section` card:

```html
<div class="feature-section" id="feature-xxx">
    <h3>Feature Name</h3>
    <p>Purpose and user value in concrete terms.</p>
    <table>
        <tr><th>User Action</th><th>System Response</th><th>Business Rules</th></tr>
        <tr><td>...</td><td>...</td><td>...</td></tr>
    </table>
</div>
```

**Requirements:**
- Each `.feature-section` must have a unique `id` matching its `data-link` reference
- Start with page layout and interaction flow, then cover trigger → processing → result → state change
- Include detailed rules, field rules, permissions, exceptions, and dependencies only where relevant
- Prefer compact tables for enumerated rules and prose for causal logic
- Separate confirmed requirements from assumptions and open questions
- Depth is judged by ambiguity removed, not a fixed word count

### Requirement Detail Pattern

For each linked feature, include enough of the following to let design and engineering continue:

1. **Page layout**: what regions/components the current page or module contains, and what responsibility each region carries.
2. **Interaction flow**: user action chain using concrete sequence wording such as "User clicks A → fills B → submits → system responds with C".
3. **Detailed rules**: a `<ul>` list where each item starts with a clear rule label plus explanation. Cover business logic, validation, boundaries, and exceptions.
4. **Field rules table**: only when the module involves a form with 5 or more fields.
5. **State transition table**: only when the module involves multi-state transitions.
6. **Permission table**: only when the module involves multi-role differences.
7. **Prototype mapping**: which screen/component demonstrates the behavior.

The combined interaction flow and detailed rules of each feature card should be substantial enough to remove implementation ambiguity. As a practical floor, target at least 50 English words or 80 Chinese characters for those two parts combined. Do not stuff all content into a three-column table; tables are for enumerable field/state/permission rules, not for explaining causal business logic.

### Text-Prototype Mapping Rules

| Rule | Description |
|---|---|
| Mapping direction | Prototype `data-link="feature-xxx"` maps to text `id="feature-xxx"` |
| Uniqueness | The same feature ID must not be duplicated across multiple text cards |
| One page, many links | A single prototype page may contain multiple `data-link`s for different regions |
| Text Mode embedding | A prototype page should appear only in the primary or first matched feature section |
| No-link pages | Splash, loading, and transitional pages without `data-link` may be omitted from Text Mode |

Do not mechanically render all six as subheadings. Choose the clearest mix of prose, tables, and state diagrams.

### Rule Coverage by Product Type

Use the relevant rule families; do not force all of them into every PRD.

| Product Pattern | Rules That Usually Matter |
|---|---|
| Forms and submission | Required fields, validation timing, draft retention, duplicate submission, edit window |
| Lists and search | Default sorting, filter combination, pagination, empty results, stale data |
| Workflow and approval | Role authority, state transitions, withdrawal, rejection reason, audit history |
| Marketplace and transaction | Inventory/availability, price changes, payment state, cancellation, refund, dispute |
| Messaging and collaboration | Delivery state, read state, permissions, mentions, attachment limits, moderation |
| AI-assisted product | Input context, suggestion vs automatic action, confidence/fallback, user correction, traceability |
| Dashboard and analytics | Metric definition, time range, refresh timing, data latency, drill-down, no-data state |
| Multi-tenant SaaS | Tenant boundary, role scope, configuration inheritance, export, operation logs |

### Content Anti-Patterns

Reject and rewrite the following:

- **Page inventory disguised as requirements**: “页面包含搜索栏、卡片和按钮” without behavior or rules.
- **Feature-list paraphrase**: repeating the user's requested capabilities without resolving how they work together.
- **Happy-path-only specification**: no validation, blocked state, cancellation, retry, or recovery for important actions.
- **UI-driven business logic**: inventing rules because a component exists rather than deriving components from product rules.
- **False precision**: fabricated percentages, limits, SLAs, fees, or time estimates.
- **Universal completeness**: adding login, settings, notifications, admin panels, and analytics to every product by habit.
- **Duplicated truth**: defining the same status, permission, or calculation differently in multiple modules.
- **Technical leakage**: database schemas, frameworks, endpoints, or storage choices unless the user explicitly requests technical design.

---

## Workflow

1. Separate confirmed evidence, product judgments, assumptions, and open questions.
2. Define primary user, core job, trigger, completion condition, shared object, and trust model.
3. Scope the smallest complete P0 journey and identify meaningful P1 support.
4. Model relevant roles, objects, permissions, and state transitions.
5. Build the product blueprint and stable feature IDs.
6. Design the happy path plus meaningful blocked, alternate, and recovery states.
7. Write adaptive document tabs and implementation-ready feature details.
8. Pass visual direction context to the `html-report` skill without defining CSS in this file.
9. Verify prototype-content mapping and cross-module consistency by reviewing code structure.
10. Revise contradictions before final delivery. Do not open the HTML in a browser for validation.

## Quality Self-Check

All checks below are **static content reviews** performed by reading the generated code and text. Do NOT open the HTML file in a browser, launch a dev server, or use browser_use tools to validate the output.

| # | Check Item | Pass Criteria |
|---|---|---|
| 1 | Feature mapping | Every feature section in 需求详情 has at least one corresponding prototype area and stable feature ID |
| 2 | Navigation target integrity | Every `navigate('page-xxx')` reference has a corresponding planned page or state |
| 3 | Content realism | Labels and sample data fit the product; no Lorem ipsum, repeated placeholders, or invented critical metrics |
| 4 | Requirement depth | Each linked feature covers page layout, interaction flow, rules, states, and boundaries without fixed-length padding |
| 5 | Adaptive document | Core tabs are complete; optional tabs appear only when justified; no empty or boilerplate chapters |
| 6 | Evidence traceability | Major product decisions connect to supplied evidence, explicit product judgment, or marked assumption |
| 7 | Core journey integrity | The P0 journey has a clear trigger and completion condition; every included P0 feature supports completion or recovery |
| 8 | Cross-module consistency | Roles, object names, statuses, calculations, and permissions do not contradict across prototype and document |
| 9 | No fabrication | Unconfirmed numbers, fees, conversion rates, or business rules are marked `[TBD]`; AI-inferred items are marked `[Assumption, TBD]` |
| 10 | Consequential actions | Money, permission, publishing, deletion, approval, and similar actions define confirmation, evidence, retry/reversal, and escalation as relevant |

## Related Skills

| Skill | Relationship |
|---|---|
| `prd-document` | Alternative route for conventional document-first PRDs; do not blend by default |
| `doc-writing-guide` | Root parent; provides intent interpretation, routing, and writing constraints |
| `html-report` | Must be invoked for split-screen structure, frame templa

... [Content truncated, total 25,114 chars] ...