---
name: integrated-three-statement-model
description: |
  Build, complete, or update institutional-quality three-statement financial models in Excel. Use when asked to fill out model templates, complete existing model frameworks, populate partially built Income Statement / Balance Sheet / Cash Flow models, link integrated financial statements, or develop a full assumption-driven model for company modeling, interview cases, or equity research style forecasts.
---

# Integrated Three-Statement Model Skill

Use this skill when the task involves building, completing, populating, linking, or updating a three-statement financial model in Excel.

Common triggers include requests to:

- fill in a 3-statement model template
- complete a partially built Income Statement / Balance Sheet / Cash Flow framework
- populate a financial model with historical or forecast data
- link the three statements within an existing template
- fix statement articulation so cash flow, balance sheet, and retained earnings tie correctly
- update an existing financial model with new forecast periods or revised assumptions
- build a full three-statement model for company modeling, interview cases, or equity research style forecasts

This skill applies in two common situations:

1. Existing template completion
Populate and complete an existing three-statement model template, including missing data,
formulas, schedules, forecast sections, and statement linkages.

When working from an existing template, preserve the user's template structure by default.
Do not force unnecessary new tabs or structural expansion unless the user explicitly asks for
a fuller rebuild or the current template is too incomplete to support proper linkage, cash
articulation, or balance validation.

2. Full model build or major rebuild
Build a complete, formula-linked, assumption-driven model with the full structure required
for a deliverable integrated model.

If no usable template exists, or if the user asks for a complete rebuild, use the full model structure defined in this skill.

In all cases, the final workbook must be formula-linked, assumption-driven, visually disciplined, and balanced before delivery.

The model must also show real market judgment and business sense. The operating structure, forecast inputs, and final numbers should reflect a defendable view of the market, the company, the business model, and how the business actually makes money. Do not choose assumptions mechanically; choose them in a way that shows market insight and company understanding.

## 1. Required workbook structure

For full builds or major rebuilds, create these sheets in this order:

1. `Raw Data`
2. `Operating Drivers`
3. `Income Statement`
4. `Supporting Schedules`
5. `Balance Sheet`
6. `Cash Flow`

Notes:

- Use the historical and forecast years required by the user. If the user does not specify a year range, use the latest 5 historical periods if available and forecast the next 3 years.
- For existing template completion, use the existing workbook structure where possible and apply the relevant logic, standards, and validation rules from this skill without forcing a full rebuild into these exact six tabs.
- `Cash Flow` must include both historical years and forecast years. Historical cash flow rows should direct-link to `Raw Data`, while forecast years should remain modeled.
- Build `Operating Drivers`, not a generic one-line revenue growth tab.
- All model sheets must include a complete set of relevant line items and schedules required for the business, statement articulation, and balance validation. Do not omit any important line item that is necessary for operating analysis, forecast logic, cash flow construction, balance sheet linkage, or model checks.
- Do not create a separate `Model Check` tab by default. The required balance control should live on `Balance Sheet` through the visible `Balance Check` row. Add a standalone `Model Check` tab only if the user explicitly asks for it.
- If a forecast line is formula-driven, such as revenue and key cost items, it must be calculated by formula and colored black, don't hardcode it

## 2. Non-negotiable output standards

### 2.1 Number formatting

- Percentages: always `0.0%`
- Financial statement values: integers only
- Zero values on statement-style tabs must display as `-` via cell number format, not by hand-typing `-`
- Recommended non-percent statement number format: `#,##0;(#,##0);-`
- Do not default to `wrap text` or custom row-height adjustments unless the user explicitly asks for them
- Do not keep financial statement line items at one decimal or more
- Operating assumptions and KPIs such as AR Days, Inventory Days, ASP, take rate, and utilization may retain one decimal where useful
- Units, stores, subscribers, capacity, and headcount: default to integer unless decimals are truly required

### 2.2 Visual hierarchy for line items

Do not left-align every line item at the same level. Use hierarchy so summary rows are obvious.

Required hierarchy:

- Section headers: full-width dark navy bar, white bold font
- Major subtotal / primary output rows: bold, no indent
- Standard line items: regular weight, one indent level
- Supporting detail rows: regular or gray helper style, two indent levels if needed
- YoY / margin / ratio rows: gray, smaller font, italic
- Each section bar must extend only to the last visible column of the table or block directly below it.

Label layout rules:

- Major rows examples: `Total Revenue`, `Gross Profit`, `Operating Income`, `EBT`, `Net Income`, `Total Current Assets`, `Total Assets`, `Total Liabilities`, `Total Equity`
- Key summary rows such as `Total COGS`, `Gross Profit`, `EBITDA`, `EBIT`, `Pre-tax Profit`, and `Net Income` should carry a black top border across the active table width only
- Detail rows examples: `Product A Revenue`, `SG&A`, `Accounts Receivable`, `Long-Term Debt`
- Helper rows examples: `YoY %`, `% of Revenue`, `Days`, `Mix %`
- Helper rows such as `YoY %`, `% of Revenue`, `Days`, and `Mix %` must be italic across the ful row, including the values. Do not affect other font treatments.

### 2.3 Header color style

Use:

- Primary dark navy: `#122B49`
- Secondary dark navy: `#16365C`
- White text on dark headers
- Minimal use of light blue fills; prefer dark bars for top headers and section bands

Recommended application:

- Sheet title row: `#122B49`, white bold
- Year row: `#122B49`, white bold
- Major section bars: `#16365C`, white bold
- Regular cells: white background
- Pure cross-sheet pull-through links: green font
- Hardcodes: blue font
- Calculated values: black font
- Helper rows: gray italic

## 3. Three-color rule

- Pure cross-sheet pull-through references: green
- Hardcodes / manual assumptions: blue
- In-sheet formulas and historical data: black
- Any formula that combines references with arithmetic, including `SheetA!X +/- SheetB!Y`, is black. This is especially common on `Cash Flow`.
- Example: `=-('Balance Sheet'!H12-'Balance Sheet'!G12)` is black, not green, because it is a calculation using cross-sheet references rather than a pure pull-through link.
- Historical source data on `Raw Data` should be black. Historical values on other sheets should be green if they are pure cross-sheet pull-through references and black if they are calculated.

`Formula-driven statement outputs` means any forecast-period cell on `Income Statement`, `Supporting Schedules`, `Balance Sheet`, or `Cash Flow` that is calculated by Excel formulas. These cells must be black, not blue.

Never hardcode inside calculation blocks.

Do not write formulas such as `='Operating Drivers'!H13*0.075` or `=Revenue*12%`.

If a percentage, ratio, margin, day count, mix, tax rate, or any other driver is used in a calculation, it must come from a visible assumption cell or assumptions row. The formula should point to that cell, not to a literal number typed directly into the formula.

## 3.1 Units and currency labeling

- Every main model sheet must show visible units and reporting currency.
- At minimum, each of `Raw Data`, `Operating Drivers`, `Income Statement`, `Supporting Schedules`, `Balance Sheet`, and `Cash Flow` must clearly indicate the currency and unit convention near the title or header area.
- Use explicit currency labels such as `¥`, `USD`, `HKD`, or other relevant reporting currency. Do not leave currency implicit.
- Use explicit unit labels such as `mn` when statement values are displayed in millions.
- The displayed currency and unit convention must remain consistent within each sheet unless a specific block is clearly labeled otherwise.
- Before using any cells in addition, subtraction, multiplication, or division, you must confirm that the referenced values use the same unit scale. Never mix scaled values such as billions, millions, or thousands in the same calculation unless they are first converted to a common unit basis.

## 3.2 Sign treatment consistency

Apply the same sign treatment to each line item in both historical and forecast periods. A value may flip sign, but the treatment logic should remain consistent.

## 3.3 Forecast outputs must be driver-based

All forecast line items must be calculated from explicit assumptions and formulas. Do not hardcode a forecast value first and then work backward to the driver. Forecast logic should be transparent enough that growth rates and other key KPIs can be reviewed directly to judge whether the output is reasonable. For example, if revenue growth is 10%, forecast revenue should equal prior-period revenue multiplied by `(1 + growth rate)`. Do not set 2025 revenue to 2M when 2024 revenue is 1M and then derive growth of 100% from that output.

## 4. Raw Data sheet

`Raw Data` is the anchor sheet. Historical data must match the source exactly，as the three statement historicals will refer to Raw Data

Required contents:

- Historical Income Statement
- Historical Balance Sheet
- Historical Cash Flow
- Key operating data pulled from filings, investor presentations, earnings releases, or other provided materials

If the user uploads raw data, copy the historical raw data into `Raw Data` without deleting historical line structure. If the user does not upload raw data, build `Raw Data` yourself from filings or other sourced historical financial information.
If the user specifies historical years, use exactly those years in `Raw Data`. If the user does not specify, use the latest 5 historical periods if available.
`Raw Data` must never include forecast years. It is strictly for historical periods only.

Do not round or reclassify historical numbers unless the source itself does so.

## 5. Operating Drivers sheet

`Operating Drivers` and `Supporting Schedules` must be fully built for all required model years before the three statements are finalized, otherwise statement linkage and articulation will break.

### 5.1 Core philosophy

When the user specifies sales/revenue forecast breakdown metrics, you must follow those requested dimensions exactly. You may add supplementary breakdowns only if they do not conflict with the user's stated structure and materially improve the model.
If the user does not specify sales/revenue forecast breakdown metrics, do not forecast revenue with a single growth-rate line, you can refer to the method below

Here are some default expectation:

- forecast by product line
- forecast by business segment
- forecast by geography
- forecast by channel
- forecast by customer cohort / unit economics / capacity where relevant

The goal is not a cosmetic driver tree. The goal is to deliver a business model that is explainable and defendable. Do necessary deep research to understand the business and push the operating breakdown as far as the source data can support.

### 5.2 Driver design requirements

For each company, choose the most detailed defensible driver stack available. Examples:

- Auto / EV: deliveries by model, ASP by model, accessory / services / battery / financing revenue, region mix
- SaaS: customers x ARPU, gross retention, net retention, new logo adds, product mix, geography mix
- Retail: stores by format, same-store sales, new stores, mature store productivity, region mix
- Industrials: capacity x utilization x yield x price, end-market mix, geography mix
- Consumer platform: MAU / DAU, conversion, take rate, order frequency, AOV, services mix

### 5.3 Mandatory structure

Build the driver sheet in this order:

1. `Revenue Bridge`
2. `Business / Product detail`, with the deepest defensible breakdown available
3. `Geography detail`
4. `Key operating KPIs`
5. `Growth Catalysts`
6. `Assumptions`

All active driver blocks must include the full set of model years required for the build. Do not leave historical or forecast years missing if those years are referenced by the statements or schedules. If a line is part of the modeled build, every required historical year and every required forecast year must be present across that row or block.

### 5.4 Growth catalysts must be explicit

Every forecast block must state what is driving it. Do not rely on unexplained rates.

For each major revenue line, include a short catalyst row or note covering:

- what changed
- why it changed
- source or evidence
- how long the effect lasts
- whether it is cyclical, structural, or one-off

Good examples:

- new model launch timing
- region expansion
- distribution build-out
- capacity ramp
- pricing reset
- product mix shift
- regulation / subsidy change
- margin-accretive software / services attach

Bad examples:

- `2026 growth = 15%`
- `margin improves gradually`

### 5.5 Assumption block requirements

Every hardcoded input must have a matching assumptions table with these columns:

- `Line Item`
- `2022A`
- `2023A`
- `2024A`
- `2025E`
- `2026E`
- `2027E`
- `Source`
- `Rationale`

Rules:

- Hardcoded values must be soft-coded into dedicated assumption cells or rows, not typed directly into downstream formulas
- Historical columns in assumption tables are mandatory where the item can be calculated from history
- Historical columns should be formula-derived, not hardcoded, so the reader can see the historical setup and trend
- Forecast-year cells in the assumptions table are blue only when they are true manual inputs
- If the model uses more forecast years, extend the same structure
- If a historical value is not calculable, leave a clearly labeled blank or `N/A`, not a silent gap
- Do not apply this blue-hardcode rule to formula-driven statement outputs. If a forecast line is formula-driven, it must be calculated by formula and coloered black.

### 5.6 Other items simplified treatment

By default, use simplified treatment for non-core balance sheet, cash flow, and equity items rather than building separate schedules.

This applies to items such as:

- `Other Current Assets`
- `Other Long-Term Assets`
- `Other Current Liabilities`
- `Other Non-Current Liabilities`
- `OCI`
- `Other Financing Activities`

Default treatment:

- historical periods must direct-link to source data
- forecast periods should use one simple visible driver
- preferred driver is `% of revenue`
- if `% of revenue` is not appropriate, use historical average or flat balance
- each item should use only one forecast method
- place these forecast drivers on `Operating Drivers` by default unless the user explicitly asks for a fuller build

Required rules:

- do not use these items as balancing plugs
- do not model the same item both on the balance sheet and as a separate manual cash flow adjustment
- if an item is forecast on the balance sheet, cash flow should reflect only the period-to-period change in that balance where relevant
- keep the treatment consistent across forecast periods unless a specific rationale is shown

Special cases:

- `OCI` must remain in equity and must not be rolled into retained earnings
- `Other Financing Activities` should remain small and stable; if it becomes large, flag it for review rather than forcing a detailed build by default

Exception rule:

Only build a separate schedule if:

- the user explicitly asks for it, or
- the item is large enough to distort balance sheet, cash flow, tax, debt, lease, or equity roll-forward logic

## 6. Income Statement rules

Required rows:

- Revenue
- COGS
- Gross Profit
- SG&A
- R&D
- D&A split if available
- Other Operating Income / Expense
- Operating Income
- Interest Income
- Interest Expense
- Equity Income / Loss from Affiliates
- Other Non-Operating Items
- EBT
- Tax
- Net Income to Company
- Minority Interest
- Net Income

Required helper rows:

- YoY for Revenue, Gross Profit, Operating Income, Net Income
- Margin rows for Gross Margin, Operating Margin, Net Margin

### 6.1 Core statement formulas

Use these formulas as the default statement logic unless the source presentation requires a more specific industry treatment:

- `Gross Profit = Net Revenue - Cost of Revenue`
- always calculate gross profit from net revenue, not gross revenue, if the company reports returns, allowances, or discounts separately
- `Gross Margin = Gross Profit / Net Revenue`
- `Operating Margin = Operating Income / Net Revenue`
- `Net Margin = Net Income / Net Revenue`
- if a tax schedule uses NOLs, `Taxable Income = EBT - NOL Utilized`
- if a tax schedule uses NOLs, `Taxes Payable = MAX(0, Taxable Income * Tax Rate)`

## 7. Supporting Schedules rules

`Operating Drivers` and `Supporting Schedules` must be fully built for all required model years before the three statements are finalized, otherwise statement linkage and articulation will break.

`Supporting Schedules` must include all forecast items that drive balance or cash articulation.

Any supporting schedule that feeds the statements must include all required years used by the model. Do not build a schedule with missing historical years or missing forecast years if downstream formulas reference those periods. A partially filled schedule that leaves blank year columns in an active modeled block is not acceptable.

Minimum required schedules:

1. PPE / Depreciation
2. Intangibles / Amortization
3. Debt / Interest
4. Equity / SBC / external financing schedule if required

Any hardcoded driver used inside `Supporting Schedules` must have a visible basis and reason. Do not leave schedule hardcodes as unexplained blue numbers. Place compact `Source` and `Rationale` support next to the hardcoded schedule inputs or in a clearly adjacent assumptions strip on the same sheet.

### 7.1 Amortization is mandatory

Do not omit amortization.

If intangibles exist or the company reports amortization, create:

- Opening Intangibles
- Additions
- Amortization
- Impairment / write-down if relevant
- Closing Intangibles

Formula logic:

`Closing Intangibles = Opening Intangibles + Additions - Amortization - Impairment`

Income Statement linkage:

- `Amortization Expense` must feed the Income Statement

Cash Flow linkage:

- amortization is non-cash and must be added back in CFO

Balance Sheet linkage:

- ending intangibles must match the balance sheet

### 7.1A Schedule year coverage is mandatory

For every active schedule block:

- include the full set of required historical years where the model shows historical statements for that line
- include the full set of forecast years where the model uses the schedule to drive forecast statements
- do not leave blank cells inside active year ranges unless the item is explicitly not applicable and clearly labeled
- if a line is intentionally unavailable historically, show a clearly labeled blank or `N/A`, not a silent gap that can be mistaken for a missing link

### 7.2 Depreciation and amortization

Prefer separate rows for depreciation and amortization whenever source data allows.

If source only gives combined D&A:

- use combined historical line
- still create a forecast split if the business has identifiable intangibles
- document the split assumption explicitly

### 7.3 PPE / Depreciation formula logic

Minimum formula structure:

- `Ending Gross PP&E = Beginning Gross PP&E + Capex`
- `Ending Accumulated Depreciation = Beginning Accumulated Depreciation + Depreciation Expense`
- `Net PP&E = Gross PP&E - Accumulated Depreciation`

Linkage rules:

- `Capex` must flow to `Cash Flow` investing as a negative cash item
- `Depreciation Expense` must feed the Income Statement
- `Net PP&E` must tie to the Balance Sheet

### 7.4 Debt / Interest formula logic

Minimum formula structure:

- `Ending Debt = Beginning Debt + New Borrowings - Repayments`
- `Interest Expense = Average Debt * Interest Rate`, unless the model intentionally uses beginning or ending debt to avoid circularity

Linkage rules:

- debt issuance and repayments must tie to `Cash Flow` financing
- ending debt must tie to the Balance Sheet debt balances
- if current maturities are material, split `Current Portion of Debt` and `Long-Term Debt` explicitly on the Balance Sheet

### 7.5 NOL / Deferred Tax schedule when relevant

If the company has losses, NOL balances, or deferred tax assets linked to tax loss carryforwards, build a visible schedule.

Minimum formula structure:

- `Ending NOL = Beginning NOL + NOL Generated - NOL Utilized`
- `NOL Generated = ABS(EBT)` when `EBT < 0`, otherwise `0`
- `NOL Utilized = MIN(Beginning NOL, Utilization Limit)` when `EBT > 0`
- `Taxable Income = EBT - NOL Utilized`
- `Taxes Payable = MAX(0, Taxable Income * Tax Rate)`
- `Deferred Tax Asset = Ending NOL * Tax Rate`
- `Delta DTA = Current DTA - Prior DTA`

Linkage rules:

- ending deferred tax asset must tie to the Balance Sheet if the line is modeled
- `Delta DTA` must be treated consistently on `Cash Flow`

## 8. Balance Sheet rules

Balance Sheet must be built from forecast drivers and schedules, not by plugging random balances.

Required articulation logic:

- `Retained Earnings = Prior Retained Earnings + Net Income to Company - Dividends`
- `Ending Cash = Prior Cash + CFO + CFI + CFF`
- `Total Assets = Total Liabilities + Total Equity`

Use helper assumptions where relevant:

- AR days
- inventory days
- AP days
- deferred revenue as % revenue
- other assets / liabilities as % revenue or specific drivers

### 8.1 Working capital roll-forward logic

Use explicit schedule logic for operating working capital balances:

- `Ending AR = Prior AR + Revenue - Cash Collections`
- `DSO = (AR / Revenue) * 365`
- `Ending Inventory = Prior Inventory + Purchases - COGS`
- `DIO = (Inventory / COGS) * 365`
- `Ending AP = Prior AP + Purchases - Cash Payments`
- `DPO = (AP / COGS) * 365`
- `Net Working Capital = AR + Inventory - AP`, unless company-specific operating liabilities require a broader NWC definition

Balance Sheet placement rules:

- `Accounts Receivable` and `Inventory` should tie from the working capital schedule into current assets
- `Accounts Payable` should tie from the working capital schedule into current liabilities
- if modeled, `Current Portion of Debt` should be shown in current liabilities and `Long-Term Debt` in non-current liabilities
- if modeled, `Deferred Tax Asset` should tie from the tax schedule into the appropriate Balance Sheet asset line based on the reporting presentation

Avoid double-counting subtotal rows inside total formulas.

## 9. Cash Flow rules

### 9.1 Scope

`Cash Flow` must display both historical years and forecast years.

Historical cash flow rows should direct-link to `Raw Data` by year. Forecast cash flow rows should be modeled on the `Cash Flow` sheet using the normal indirect-method build.

### 9.2 Construction method

Use indirect method.

Recommended structure:

1. Net income
2. Non-cash add-backs
3. Working capital changes
4. CFO subtotal
5. Capex / investment items
6. CFI subtotal
7. Debt / equity / lease / dividend items
8. CFF subtotal
9. FX / other
10. Net change in cash
11. Ending cash

### 9.3 Core line formulas

Use these formulas as the default indirect-method cash flow build:

- `CFO = Net Income + D&A + other non-cash add-backs - Delta Working Capital`, with working capital changes broken out by line item
- `CFI = -Capex +/- other investing cash flows`
- `CFF = Debt Issuance - Debt Repayment + Equity Issuance - Dividends +/- other financing cash flows`
- `Net Change in Cash = CFO + CFI + CFF`
- `Ending Cash = Beginning Cash + Net Change in Cash`

Working capital cash flow direction should follow the schedule balances:

- `Delta AR = Current AR - Prior AR`; cash flow effect is `-Delta AR`
- `Delta Inventory = Current Inventory - Prior Inventory`; cash flow effect is `-Delta Inventory`
- `Delta AP = Current AP - Prior AP`; cash flow effect is `+Delta AP`
- if a deferred tax asset schedule is modeled, an increase in `DTA` is a use of cash and a decrease in `DTA` is a source of cash

### 9.4 Sign convention

When the model does not balance, check cash flow signs first and verify that the sign treatment of all key line items is correct.

Default sign rules:

- Operating current asset increase: cash outflow = `-(Current - Prior)`
- Operat

... [Content truncated, total 45,530 chars] ...