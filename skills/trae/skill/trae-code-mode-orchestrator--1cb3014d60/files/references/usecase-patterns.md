# Use Case Patterns

Task-type decision trees and workflow shapes for Code Mode routing. Each section describes a category of user requests, whether Code Mode helps, and what the orchestration looks like.

---

## Category 1: Multi-Source Information Gathering

**Example queries:**
- "搜索 8 个招标平台，收集法律信息化相关招标信息"
- "从 6 个新闻源抓取深圳重点新闻，评分排序输出表格"
- "搜索多个关键词的 GitHub Trending 项目，去重后生成日报"

**Code Mode?** ✅ YES — when there are ≥3 sources/keywords AND results need dedup/scoring/filtering.

**Why it helps:**
- Fan-out WebSearch/WebFetch across sources in parallel
- JS deduplication by URL/title
- Scoring/sorting logic in JS
- Structured output assembly

**Workflow shape:**
```
Define source list (URLs, keywords, platforms)
    → Fan-out: search/fetch each source (Promise.all)
    → Normalize: extract {title, url, date, source} from each result
    → Deduplicate: by URL or title hash
    → Filter: by date range, keyword match, exclusion rules
    → Score/Sort: by freshness, relevance, source priority
    → Output: structured JSON or formatted report
```

**NOT Code Mode** when: only 1-2 sources, no dedup needed, or the "analysis" is purely LLM reasoning (sentiment, summarization).

---

## Category 2: Local Script Execution + Validation

**Example queries:**
- "运行 /workspace/fetch_news.py，检查输出文件是否生成"
- "执行数据处理脚本，验证 result.json 包含预期字段"
- "跑 build 脚本，检查 exit code，失败则读 log"

**Code Mode?** ✅ YES — when there's a run → check → branch flow.

**Why it helps:**
- Shell call + parse exit code/output
- Conditional: success → validate artifact, failure → read error log
- Retry logic for flaky scripts

**Workflow shape:**
```
Run script via Shell
    → Parse exit code and stdout
    → If success: read output file, validate structure
    → If failure: read log file, report error details
    → Optionally retry (bounded, max 2-3 times)
    → Report: status + artifacts + validation results
```

**NOT Code Mode** when: the script is the entire task (just "run this script" with no follow-up validation), or the user just wants to see the output.

---

## Category 3: File Batch Processing

**Example queries:**
- "读取目录下所有 JSON 文件，提取 title 字段，汇总成一个列表"
- "检查 workspace 中 10 个 markdown 文件是否包含 ## Summary 章节"
- "对比两个目录的文件列表，找出差异"

**Code Mode?** ✅ YES — iteration over file list with uniform logic.

**Why it helps:**
- Shell/Glob to list files → JS array operations
- Parallel Read of multiple files
- Extract/transform/validate each file's content in JS
- Aggregate findings

**Workflow shape:**
```
List files (Shell find or Glob)
    → Parse file list into array
    → Fan-out Read (bounded, max 20 files)
    → For each: extract target field/section via JS string/JSON operations
    → Aggregate: counts, missing items, anomalies
    → Output: summary with per-file status
```

**NOT Code Mode** when: only 1-2 files, or the task is "read this file and explain it" (that's LLM work).

---

## Category 4: Artifact Generation with Validation

**Example queries:**
- "生成 HTML 报告保存到 /workspace，验证包含所有预期章节"
- "创建 Excel 方案文件，检查行数和必填字段"
- "生成配置文件并验证 JSON 格式正确"

**Code Mode?** ✅ YES — when Write + Read-back validation is needed.

**Why it helps:**
- Assemble content in JS from gathered data
- Write via tools.Write
- Immediately read back and validate (sections present, non-empty, correct format)
- Structured validation report

**Workflow shape:**
```
Gather data (from earlier steps or tool calls)
    → Assemble content in JS (string building, JSON construction)
    → Write to target path
    → Read back and validate:
        - File non-empty
        - Required sections/fields present
        - Size within expected range
    → Report: artifact path + validation results
```

**NOT Code Mode** when: the content generation IS the hard part (writing a 2000-word essay). Code Mode handles the mechanical write+validate, not the creative generation.

---

## Category 5: Health Check / Service Readiness

**Example queries:**
- "检查 dev server 是否启动，没启动则启动它，等待 ready"
- "验证 3 个 API endpoint 是否可达"
- "确认 build 产物存在且非空"

**Code Mode?** ✅ YES — check → act → poll pattern.

**Why it helps:**
- Shell commands to check process/port status
- Conditional: running → report OK, not running → start → poll readiness
- Bounded polling with max attempts

**Workflow shape:**
```
Check current state (Shell: curl, test, pgrep, etc.)
    → If healthy: report OK
    → If not: take corrective action (start service)
    → Poll for readiness (bounded, max 3-5 checks)
    → Report: final state + actions taken
```

---

## Category 6: Configuration/Data Comparison

**Example queries:**
- "对比 PPE 和 PROD 的 TCC 配置差异"
- "读取两个 JSON 配置文件，列出 key 级别差异"
- "比较两个目录下同名文件的 hash 值"

**Code Mode?** ✅ YES — read two sources + JS diff logic.

**Why it helps:**
- Read both sources
- JS object comparison (key diff, value diff)
- Structured diff output

**Workflow shape:**
```
Read source A (file, API output, config dump)
    → Read source B
    → Parse both to JS objects
    → Compare: missing keys, value differences, type mismatches
    → Output: structured diff report
```

---

## Categories That Do NOT Benefit from Code Mode

### Pure Content Generation
- "写一篇 2000 字的分析报告"
- "生成每日知识点推送"
- "撰写舆情摘要"

→ The bottleneck is LLM thinking, not tool orchestration.

### Single-Shot Queries
- "查一下小米股价"
- "搜索 AI 最新新闻"
- "这个文件里写了什么"

→ One tool call, no orchestration needed.

### Real-Time / Persistent Monitoring
- "每小时监控价格"
- "持续监控舆情"

→ Exec runs once and exits. It cannot maintain persistent loops or cron-like scheduling. The scheduling layer is external.

---

## Quick Decision Matrix

| User Request Pattern | Code Mode? | Primary Reason |
|---------------------|------------|----------------|
| Search N keywords + dedup + report | ✅ | Fan-out + aggregation |
| Run script + validate output | ✅ | Conditional + validation |
| Read N files + extract + summarize | ✅ | Loop + transform |
| Generate file + verify contents | ✅ | Write + validate gate |
| Compare two configs/datasets | ✅ | Read + JS diff |
| Check service + start if needed | ✅ | Conditional + polling |
| Write a long article/report | ❌ | LLM generation, not orchestration |
| Query a single data point | ❌ | One tool call |
| Continuous monitoring | ❌ | Exec runs once |
| "Execute my project tasks" | ❌ | Too vague |
