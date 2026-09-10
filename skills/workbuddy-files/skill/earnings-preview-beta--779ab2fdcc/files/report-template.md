# HTML Report Template Reference

Use this template as the foundation for the single-company earnings preview HTML report. Customize the data, charts, and narrative content based on the research gathered in Phases 1-5.

## HTML Structure

The report is a single self-contained HTML file with:
- Embedded CSS (no external stylesheets)
- Chart.js loaded from CDN for interactive charts
- Print-friendly styles via `@media print`
- Responsive layout that works on screens and in print
- Target: 4-5 printed pages

## Complete Template

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Earnings Preview — [COMPANY] ([TICKER]) — [DATE]</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js" integrity="sha384-vsrfeLOOY6KuIYKDlmVH5UiBmgIdB1oEf7p01YgWHuqmOHfZr374+odEv96n9tNC" crossorigin="anonymous"></script>
  <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-annotation@3.1.0/dist/chartjs-plugin-annotation.min.js" integrity="sha384-3N9GHhCtN3CQef6tNfqgZlv7sQLYIkcChN+uaTZ7xVdzKYp/SjBNPxa92+hM7EAY" crossorigin="anonymous"></script>
  <style>
    /* ── Reset & Base ── */
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    html { font-size: 15px; }
    body {
      font-family: 'Arial Narrow', Arial, sans-serif;
      color: #1a1a2e;
      background: #fff;
      line-height: 1.6;
    }

    /* ── Layout ── */
    .page {
      max-width: 1100px;
      margin: 0 auto;
      padding: 40px 48px;
    }
    .page-break {
      page-break-before: always;
      border-top: 2px solid #1a1a4e;
      margin-top: 48px;
      padding-top: 32px;
    }

    /* ── Header / Cover ── */
    .cover-header {
      border-bottom: 3px solid #1a1a4e;
      padding-bottom: 16px;
      margin-bottom: 24px;
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
    }
    .cover-header .brand {
      font-size: 24px;
      font-weight: bold;
      color: #1a1a4e;
      letter-spacing: 2px;
      text-transform: uppercase;
    }
    .cover-header .sector {
      font-size: 13px;
      color: #555;
    }
    .cover-header .date {
      font-size: 14px;
      color: #333;
      text-align: right;
    }
    .report-title {
      font-size: 26px;
      font-weight: bold;
      color: #1a1a2e;
      margin: 20px 0 16px 0;
      line-height: 1.3;
    }

    /* ── Executive Thesis ── */
    .executive-summary {
      font-size: 14px;
      line-height: 1.65;
      color: #222;
      margin-bottom: 16px;
    }
    .executive-summary p {
      margin-bottom: 10px;
      text-align: justify;
    }
    .executive-summary ul {
      margin: 8px 0 10px 20px;
      font-size: 13.5px;
    }
    .executive-summary ul li {
      margin-bottom: 5px;
      line-height: 1.5;
    }
    blockquote {
      border-left: 3px solid #b0b8c8;
      padding: 6px 14px;
      margin: 8px 0 8px 12px;
      font-style: italic;
      color: #444;
      background: #f9fafb;
      font-size: 12.5px;
      line-height: 1.5;
    }

    /* ── Section Headings ── */
    h2.section-title {
      font-size: 18px;
      font-weight: 700;
      color: #1a1a4e;
      border-bottom: 2px solid #1a1a4e;
      padding-bottom: 5px;
      margin: 28px 0 14px 0;
    }
    h3.subsection-title {
      font-size: 14px;
      font-weight: 600;
      color: #1a1a4e;
      margin: 16px 0 8px 0;
    }
    h4.figure-title {
      font-size: 12px;
      font-weight: 600;
      color: #444;
      margin: 14px 0 6px 0;
    }

    /* ── Tables ── */
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 12px;
      margin: 10px 0 16px 0;
    }
    thead th {
      background: #1a1a4e;
      color: #fff;
      padding: 7px 10px;
      text-align: left;
      font-weight: 600;
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    tbody td {
      padding: 6px 10px;
      border-bottom: 1px solid #e0e0e0;
    }
    tbody tr:nth-child(even) {
      background: #f9fafb;
    }
    tbody tr:hover {
      background: #eef0f5;
    }
    .num { text-align: right; font-variant-numeric: tabular-nums; }
    .pos { color: #0d7a3e; font-weight: 600; }
    .neg { color: #c0392b; font-weight: 600; }
    .neutral { color: #555; }
    .highlight-row { background: #e8eaf6 !important; font-weight: 600; }

    /* ── Chart Containers ── */
    .chart-row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
      margin: 12px 0 20px 0;
    }
    .chart-container {
      position: relative;
      background: #fafbfc;
      border: 1px solid #e8e8e8;
      border-radius: 4px;
      padding: 14px;
    }
    .chart-container canvas {
      max-height: 260px;
    }
    .chart-full {
      grid-column: 1 / -1;
    }

    /* ── Compact Lists ── */
    .key-metrics ul, .themes ul, .news-list ul {
      margin: 6px 0 6px 18px;
      font-size: 13px;
      line-height: 1.55;
    }
    .key-metrics li, .themes li, .news-list li {
      margin-bottom: 5px;
    }

    /* ── Data Reference Links ── */
    a.data-ref {
      color: #1a1a4e;
      text-decoration: none;
      border-bottom: 1px dotted transparent;
      transition: border-color 0.15s;
    }
    a.data-ref:hover {
      border-bottom-color: #1a1a4e;
    }

    /* ── Appendix ── */
    .appendix table {
      font-size: 10.5px;
    }
    .appendix thead th {
      font-size: 10px;
      padding: 5px 8px;
    }
    .appendix tbody td {
      padding: 4px 8px;
      font-size: 10.5px;
      vertical-align: top;
      line-height: 1.45;
    }
    .appendix .ref-id {
      font-weight: 600;
      color: #1a1a4e;
      white-space: nowrap;
    }
    .appendix .source-detail {
      font-size: 10px;
      color: #444;
    }
    .appendix .source-detail .formula {
      font-family: 'Courier New', monospace;
      font-size: 9.5px;
      color: #555;
    }
    .appendix .source-detail .excerpt {
      font-style: italic;
      color: #555;
    }
    .appendix .source-detail .src-label {
      font-weight: 600;
      color: #1a1a4e;
      font-size: 9.5px;
    }
    .appendix .source-detail a.data-ref {
      font-weight: 600;
    }
    .appendix a.src-url {
      color: #3366cc;
      text-decoration: underline;
      font-size: 10px;
      word-break: break-all;
    }
    .appendix a.src-url:hover {
      color: #1a1a4e;
    }
    .appendix .transcript-ref {
      font-weight: 600;
      color: #1a1a4e;
      font-size: 10px;
    }
    .appendix-group {
      font-size: 11px;
      font-weight: 700;
      color: #1a1a4e;
      background: #f0f1f5;
      padding: 4px 8px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    /* ── Source / Footer ── */
    .source {
      font-size: 10px;
      color: #999;
      margin-top: 3px;
      font-style: italic;
    }
    .ai-disclaimer {
      background-color: #fff3cd;
      border: 1px solid #ffc107;
      border-radius: 4px;
      padding: 4px 10px;
      font-size: 11px;
      font-weight: 600;
      color: #664d03;
      text-align: center;
      margin-bottom: 12px;
    }
    .page-footer {
      border-top: 2px solid #1a1a4e;
      padding-top: 10px;
      margin-top: 32px;
      text-align: center;
    }
    .page-footer .footer-disclaimer {
      font-size: 11px;
      font-weight: 600;
      color: #664d03;
      background-color: #fff3cd;
      border: 1px solid #ffc107;
      border-radius: 4px;
      padding: 4px 10px;
      display: inline-block;
      margin-bottom: 4px;
    }
    .page-footer .footer-meta {
      font-size: 10px;
      color: #888;
    }

    /* ── Print Styles ── */
    @media print {
      body { font-size: 11px; }
      .page { padding: 16px; max-width: none; }
      .chart-container { break-inside: avoid; }
      table { break-inside: avoid; }
      .page-break { margin-top: 0; }
      .no-print { display: none; }
    }
  </style>
</head>
<body>
<div class="page">

  <!-- ════════════════════════════════════════════ -->
  <!-- PAGE 1: COVER & THESIS                       -->
  <!-- ════════════════════════════════════════════ -->
  <div class="ai-disclaimer">Analysis is AI-generated — please confirm all outputs</div>
  <div class="cover-header">
    <div>
      <div class="brand">Earnings Preview</div>
      <div class="sector">[Industry] | [TICKER]</div>
    </div>
    <div class="date">[Full Date]</div>
  </div>

  <h1 class="report-title">[Company Name] ([TICKER]) [Q# FY####] Earnings Preview: [Thematic Subtitle]</h1>

  <div class="executive-summary">
    <!-- Executive thesis: 2-3 short paragraphs + bullet points.
         What we expect, our EPS estimate vs consensus, guidance expectations,
         key metrics to watch, what would move the stock, key debates.
         Weave in 3-4 management quotes as blockquotes where they support the thesis.
         Do NOT create a separate "Key Management Quotes" section. -->

    <p>[Opening 1-2 sentences: what we expect from this print.]</p>

    <ul>
      <li><strong>EPS:</strong> We estimate <a href="#ref-1" class="data-ref">$X.XX</a> vs consensus <a href="#ref-2" class="data-ref">$X.XX</a>, [rationale]</li>
      <li><strong>Revenue:</strong> We estimate <a href="#ref-3" class="data-ref">$XX.XB</a> vs consensus <a href="#ref-4" class="data-ref">$XX.XB</a>, [rationale]</li>
      <li><strong>Guidance:</strong> [What to expect on forward guidance]</li>
      <li><strong>Key metric:</strong> [Most important sub-headline metric to watch]</li>
      <li><strong>Stock catalyst:</strong> [What would move the stock up/down post-print]</li>
      <li><strong>Key debate:</strong> [What bulls and bears disagree on]</li>
    </ul>

    <blockquote>"[Key management quote supporting a thesis point]" — [Speaker], [Q# FY####] Earnings Call</blockquote>

    <p>[1-2 sentences tying it together — your overall read on the setup.]</p>

    <blockquote>"[Another supporting quote]" — [Speaker], [Q# FY####] Earnings Call</blockquote>
  </div>

  <!-- ════════════════════════════════════════════ -->
  <!-- PAGE 2: ESTIMATES, THEMES & NEWS             -->
  <!-- ════════════════════════════════════════════ -->
  <div class="page-break">

    <!-- Consensus Estimates Table (Figure label inline) -->
    <h2 class="section-title">Consensus Estimates — [Q# FY####]</h2>
    <h4 class="figure-title">[Q# FY####] Consensus Estimates</h4>
    <table>
      <thead>
        <tr>
          <th>Metric</th>
          <th class="num">Consensus</th>
          <th class="num">Our Estimate</th>
          <th class="num">y/y Change</th>
        </tr>
      </thead>
      <tbody>
        <tr><td>Revenue</td><td class="num"><a href="#ref-N" class="data-ref">$[XX.X]B</a></td><td class="num"><a href="#ref-N" class="data-ref">$[XX.X]B</a></td><td class="num [pos|neg]"><a href="#ref-N" class="data-ref">[+/-X.X%]</a></td></tr>
        <tr><td>Diluted EPS</td><td class="num"><a href="#ref-N" class="data-ref">$[X.XX]</a></td><td class="num"><a href="#ref-N" class="data-ref">$[X.XX]</a></td><td class="num [pos|neg]"><a href="#ref-N" class="data-ref">[+/-X.X%]</a></td></tr>
        <tr><td>Gross Margin</td><td class="num"><a href="#ref-N" class="data-ref">[XX.X%]</a></td><td class="num"><a href="#ref-N" class="data-ref">[XX.X%]</a></td><td class="num [pos|neg]"><a href="#ref-N" class="data-ref">[+/-XXbps]</a></td></tr>
        <tr><td>Operating Income</td><td class="num"><a href="#ref-N" class="data-ref">$[X.X]B</a></td><td class="num"><a href="#ref-N" class="data-ref">$[X.X]B</a></td><td class="num [pos|neg]"><a href="#ref-N" class="data-ref">[+/-X.X%]</a></td></tr>
        <!-- Add 2-3 company-specific KPIs below (e.g., comp sales, eComm growth, membership revenue) -->
        <tr><td>[Company KPI 1]</td><td class="num">[Value]</td><td class="num">[Value]</td><td class="num [pos|neg]">[Change]</td></tr>
        <tr><td>[Company KPI 2]</td><td class="num">[Value]</td><td class="num">[Value]</td><td class="num [pos|neg]">[Change]</td></tr>
      </tbody>
    </table>
    <div class="source">Source: Kensho, S&P Capital IQ</div>

    <!-- Key Metrics Beyond Headline EPS -->
    <h3 class="subsection-title">Key Metrics Beyond Headline EPS</h3>
    <div class="key-metrics">
      <ul>
        <li><strong>[Metric 1]:</strong> [What consensus/management expects, why it matters. Be specific with numbers.]</li>
        <li><strong>[Metric 2]:</strong> [Details]</li>
        <li><strong>[Metric 3]:</strong> [Details]</li>
        <!-- 3-5 items -->
      </ul>
    </div>

    <!-- Themes to Watch -->
    <h3 class="subsection-title">Themes to Watch</h3>
    <div class="themes">
      <ul>
        <li><strong>[Theme 1]:</strong> [1-2 sentences max. Forward-looking, specific.]</li>
        <li><strong>[Theme 2]:</strong> [Details]</li>
        <li><strong>[Theme 3]:</strong> [Details]</li>
        <!-- 3-5 themes -->
      </ul>
    </div>

    <!-- Recent News & Developments -->
    <h3 class="subsection-title">Recent News & Developments</h3>
    <div class="news-list">
      <ul>
        <li><strong>[Date]:</strong> [Headline] — [Brief impact assessment, one line]</li>
        <li><strong>[Date]:</strong> [Headline] — [Impact]</li>
        <li><strong>[Date]:</strong> [Headline] — [Impact]</li>
        <!-- 3-5 material items from last 60 days -->
      </ul>
    </div>
    <div class="source">Source: Kensho</div>

  </div>

  <!-- ════════════════════════════════════════════ -->
  <!-- PAGES 3-5: FIGURES                           -->
  <!-- All charts and tables, numbered sequentially -->
  <!-- ════════════════════════════════════════════ -->
  <div class="page-break">
    <h2 class="section-title">Financial & Competitive Analysis</h2>

    <!-- Figure 1: Quarterly Revenue & Diluted EPS -->
    <div class="chart-row">
      <div class="chart-container">
        <h4 class="figure-title">Figure 1: Quarterly Revenue & Diluted EPS</h4>
        <canvas id="chart-rev-eps"></canvas>
        <div class="source">Source: S&P Capital IQ</div>
      </div>

      <!-- Figure 2: Margin Trends -->
      <div class="chart-container">
        <h4 class="figure-title">Figure 2: Margin Trends (Gross & Operating %)</h4>
        <canvas id="chart-margins"></canvas>
        <div class="source">Source: S&P Capital IQ</div>
      </div>
    </div>

    <!-- Figure 3: Revenue Growth y/y % -->
    <div class="chart-row">
      <div class="chart-container chart-full">
        <h4 class="figure-title">Figure 3: Revenue Growth y/y (%)</h4>
        <canvas id="chart-rev-growth" style="max-height: 200px;"></canvas>
        <div class="source">Source: S&P Capital IQ</div>
      </div>
    </div>

    <!-- Figure 4: Business Segment Revenue -->
    <h4 class="figure-title">Figure 4: Business Segment Revenue</h4>
    <table>
      <thead>
        <tr>
          <th>Segment</th>
          <th class="num">Latest Q Rev ($M)</th>
          <th class="num">% of Total</th>
          <th class="num">y/y Change</th>
        </tr>
      </thead>
      <tbody>
        <!-- Populate from segment data. Color-code y/y change with pos/neg classes. -->
      </tbody>
    </table>
    <div class="source">Source: S&P Capital IQ</div>
  </div>

  <!-- Page break for stock & competitor charts -->
  <div class="page-break">

    <!-- Figure 5: 1-Year Stock Price with Earnings Dates -->
    <div class="chart-row">
      <div class="chart-container chart-full">
        <h4 class="figure-title">Figure 5: 1-Year Stock Price with Earnings Dates</h4>
        <canvas id="chart-price-annotated" style="max-height: 300px;"></canvas>
        <div class="source">Source: S&P Capital IQ</div>
      </div>
    </div>

    <!-- Figure 6: Stock Performance vs. Competitors (Indexed to 100) -->
    <div class="chart-row">
      <div class="chart-container chart-full">
        <h4 class="figure-title">Figure 6: Stock Performance vs. Competitors — 1 Year (Indexed to 100)</h4>
        <canvas id="chart-comp-perf" style="max-height: 300px;"></canvas>
        <div class="source">Source: S&P Capital IQ</div>
      </div>
    </div>
  </div>

  <div class="page-break">

    <!-- Figure 7: LTM P/E vs. Competitors -->
    <div class="chart-row">
      <div class="chart-container chart-full">
        <h4 class="figure-title">Figure 7: LTM P/E vs. Competitors</h4>
        <canvas id="chart-pe-comp" style="max-height: 280px;"></canvas>
        <div class="source">Source: S&P Capital IQ</div>
      </div>
    </div>

    <!-- Figure 8: Competitor Comparison Table -->
    <h4 class="figure-title">Figure 8: Competitor Comparison</h4>
    <table>
      <thead>
        <tr>
          <th>Ticker</th>
          <th>Company</th>
          <th class="num">Mkt Cap ($B)</th>
          <th class="num">LTM P/E</th>
          <th class="num">NTM P/E</th>
          <th class="num">YTD %</th>
          <th class="num">1-Yr %</th>
        </tr>
      </thead>
      <tbody>
        <!-- Highlight the subject company row with class="highlight-row" -->
      </tbody>
    </table>
    <div class="source">Source: S&P Capital IQ</div>
  </div>

  <!-- ════════════════════════════════════════════ -->
  <!-- APPENDIX: DATA SOURCES & CALCULATIONS        -->
  <!-- ════════════════════════════════════════════ -->
  <div class="page-break appendix" id="appendix">
    <div class="ai-disclaimer">Analysis is AI-generated — please confirm all outputs</div>
    <h2 class="section-title">Appendix: Data Sources & Calculations</h2>
    <p style="font-size: 11px; color: #666; margin-bottom: 12px;">
      Every claim in this report is hyperlinked to its entry below. Click any highlighted text to jump here.
    </p>
    <table>
      <thead>
        <tr>
          <th style="width: 40px;">Ref</th>
          <th style="width: 170px;">Fact</th>
          <th style="width: 75px;">Value</th>
          <th>Source & Derivation</th>
        </tr>
      </thead>
      <tbody>
        <!-- Group: Quarterly Financials -->
        <tr><td colspan="4" class="appendix-group">Quarterly Financials</td></tr>
        <tr id="ref-1">
          <td class="ref-id">1</td>
          <td>[Q# FY#### Revenue]</td>
          <td class="num">$[XX.X]B</td>
          <td class="source-detail">
            <span class="src-label">S&P Capital IQ</span> — get_financial_line_item_from_identifiers(identifier='[TICKER]', line_item='revenue', period_type='quarterly', period='[Q# FY####]')
          </td>
        </tr>
        <tr id="ref-2">
          <td class="ref-id">2</td>
          <td>[Q# FY#### Diluted EPS]</td>
          <td class="num">$[X.XX]</td>
          <td class="source-detail">
            <span class="src-label">S&P Capital IQ</span> — get_financial_line_item_from_identifiers(identifier='[TICKER]', line_item='diluted_eps', period_type='quarterly', period='[Q# FY####]')
          </td>
        </tr>
        <tr id="ref-3">
          <td class="ref-id">3</td>
          <td>[Q# FY#### Gross Profit]</td>
          <td class="num">$[XX.X]B</td>
          <td class="source-detail">
            <span class="src-label">S&P Capital IQ</span> — get_financial_line_item_from_identifiers(identifier='[TICKER]', line_item='gross_profit', period_type='quarterly', period='[Q# FY####]')
          </td>
        </tr>
        <tr id="ref-4">
          <td class="ref-id">4</td>
          <td>[Q# FY#### Gross Margin]</td>
          <td class="num">[XX.X%]</td>
          <td class="source-detail">
            <span class="formula"><a href="#ref-3" class="data-ref">Gross Profit $XX.XB</a> / <a href="#ref-1" class="data-ref">Revenue $XX.XB</a> = XX.X%</span><br>
            <span class="src-label">S&P Capital IQ</span> (calculated)
          </td>
        </tr>
        <tr id="ref-5">
          <td class="ref-id">5</td>
          <td>[Q# FY#### Revenue y/y Growth]</td>
          <td class="num">[+/-X.X%]</td>
          <td class="source-detail">
            <span class="formula">(<a href="#ref-1" class="data-ref">[Q# FY## Rev $XX.XB]</a> - <a href="#ref-N" class="data-ref">[Q# FY## Rev $XX.XB]</a>) / <a href="#ref-N" class="data-ref">[Q# FY## Rev $XX.XB]</a> = X.X%</span><br>
            <span class="src-label">S&P Capital IQ</span> (calculated)
          </td>
        </tr>
        <!-- Continue for all financial data points... -->

        <!-- Group: Valuation -->
        <tr><td colspan="4" class="appendix-group">Valuation</td></tr>
        <tr id="ref-N">
          <td class="ref-id">[N]</td>
          <td>Current Stock Price — [TICKER]</td>
          <td class="num">$[XXX.XX]</td>
          <td class="source-detail">
            <span class="src-label">S&P Capital IQ</span> — get_prices_from_identifiers(identifier='[TICKER]', periodicity='day')
          </td>
        </tr>
        <tr id="ref-N">
          <td class="ref-id">[N]</td>
          <td>Market Cap — [TICKER]</td>
          <td class="num">$[XXX.X]B</td>
          <td class="source-detail">
            <span class="src-label">S&P Capital IQ</span> — get_capitalization_from_identifiers(identifier='[TICKER]', capitalization='market_cap')
          </td>
        </tr>
        <tr id="ref-N">
          <td class="ref-id">[N]</td>
          <td>LTM P/E — [TICKER]</td>
          <td class="num">[XX.X]x</td>
          <td class="source-detail">
            <span class="formula"><a href="#ref-20" class="data-ref">Price $XXX.XX</a> / (<a href="#ref-8" class="data-ref">Q1 EPS $X.XX</a> + <a href="#ref-9" class="data-ref">Q2 EPS $X.XX</a> + <a href="#ref-10" class="data-ref">Q3 EPS $X.XX</a> + <a href="#ref-11" class="data-ref">Q4 EPS $X.XX</a>) = XX.Xx</span><br>
            <span class="src-label">S&P Capital IQ</span> (calculated)
          </td>
        </tr>
        <tr id="ref-N">
          <td class="ref-id">[N]</td>
          <td>NTM P/E — [TICKER]</td>
          <td class="num">[XX.X]x</td>
          <td class="source-detail">
            <span class="formula"><a href="#ref-20" class="data-ref">Price $XXX.XX</a> / (<a href="#ref-N" class="data-ref">Q4'25E $X.XX</a> + <a href="#ref-N" class="data-ref">Q1'26E $X.XX</a> + <a href="#ref-N" class="data-ref">Q2'26E $X.XX</a> + <a href="#ref-N" class="data-ref">Q3'26E $X.XX</a>) = XX.Xx</span><br>
            <span class="src-label">S&P Capital IQ</span> — get_consensus_estimates_from_identifiers(identifier='[TICKER]', period_type='quarterly', num_periods_forward=4). NTM EPS = sum of next 4 quarterly consensus mean EPS estimates.
          </td>
        </tr>

        <!-- Group: Transcript Claims -->
        <tr><td colspan="4" class="appendix-group">Transcript Claims</td></tr>
        <tr id="ref-N">
          <td class="ref-id">[N]</td>
          <td>[Fact, e.g., "Management guided comp sales +3-4%"]</td>
          <td class="num">N/A</td>
          <td class="source-detail">
            <span class="excerpt">"We expect comp sales growth of 3-4% in Q4, driven by continued strength in grocery and health &amp; wellness."</span><br>
            <span class="src-label">Source:</span> <span class="transcript-ref">[Q# FY#### Earnings Call Transcript]</span> (key_dev_id: [ID]) — [Speaker Name], [Title]
          </td>
        </tr>

        <!-- Group: Estimates & Consensus -->
        <tr><td colspan="4" class="appendix-group">Estimates & Consensus</td></tr>
        <tr id="ref-N">
          <td class="ref-id">[N]</td>
          <td>Consensus EPS — [Q# FY####]</td>
          <td class="num">$[X.XX]</td>
          <td class="source-detail">
            <span class="excerpt">"Consensus EPS estimate of $X.XX, revised up from $X.XX over the past 90 days."</span><br>
            <a href="https://[source-url-from-kensho-search]" target="_blank" class="src-url">[Source Title / Publication Name]</a><br>
            <span class="src-label">Query:</span> search("[TICKER] earnings estimates consensus EPS revenue upcoming quarter")
          </td>
        </tr>

        <!-- Group: News & Analyst Commentary -->
        <tr><td colspan="4" class="appendix-group">News & Analyst Commentary</td></tr>
        <tr id="ref-N">
          <td class="ref-id">[N]</td>
          <td>[e.g., "Barclays upgraded to Overweight"]</td>
          <td class="num">N/A</td>
          <td class="source-detail">
            <span class="excerpt">"Barclays upgraded WMT to Overweight with a $210 price target, citing accelerating eCommerce momentum."</span><br>
            <a href="https://[source-url-from-kensho-search]" target="_blank" class="src-url">[Source Title / Publication, Date]</a><br>
            <span class="src-label">Query:</span> search("[TICKER] analyst ratings price target upgrades downgrades")
          </td>
        </tr>

        <!-- Group: Stock Performance -->
        <tr><td colspan="4" class="appendix-group">Stock Performance</td></tr>
        <tr id="ref-N">
          <td class="ref-id">[N]</td>
          <td>YTD Return — [TICKER]</td>
          <td class="num">[+/-X.X%]</td>
          <td c

... [Content truncated, total 43,950 chars] ...