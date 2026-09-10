# Exec Patterns

Reusable JavaScript **structural templates** for TRAE Code Mode.

> ⚠️ **These are structure examples, NOT copy-paste code.**
>
> - Tool names (`WebSearch`, `Shell`, `Read`, `Write`, etc.) are **illustrative placeholders**. Your actual environment may use completely different names.
> - Parameter keys (`query`, `file_path`, `command`, etc.) are also illustrative. Real schemas vary.
> - **Always run Pattern 0 first** to discover actual tool names and param schemas via `ALL_TOOLS`.
> - When writing real code: substitute the actual names/params from `ALL_TOOLS` into the structural pattern.

## Pattern 0: Tool Discovery (Always Run First)

This is the **only pattern you run verbatim**. All other patterns require adapting tool names/params to match what this returns.

```js
// Run this as your FIRST Exec call — output tells you real tool names and params
const schema = ALL_TOOLS.map(t => ({
  name: t.name,
  desc: t.description?.slice(0, 100),
  params: t.parameters?.properties
    ? Object.entries(t.parameters.properties).map(([k, v]) => `${k}${v.required ? '*' : ''}:${v.type}`)
    : []
}));
text(schema);
```

**After reading the output**, you know:
- Which tool handles web searching (might be `WebSearch`, `WebFetch`, etc.)
- Which tool handles file I/O (might be `Read`/`Write`, etc.)
- Which tool runs shell commands (might be `Shell`, `RunCommand`, etc.)
- The exact parameter names each tool expects

Only then proceed to write orchestration code using the real names.

## Pattern 1: Parallel Fan-Out with Error Isolation

Use when: N independent read-only calls on a known list of inputs.

> Adapt: replace `tools.WebSearch` with your actual search tool name, and `{ query: kw, num: 5 }` with the real params from ALL_TOOLS.

```js
// Structure: parallel fan-out with per-item error isolation
// TODO: replace SEARCH_TOOL and {PARAMS} with real names from ALL_TOOLS
const keywords = ["AI framework 2026", "LLM agent toolkit", "code generation open source"];
const MAX_PARALLEL = 10;

const results = await Promise.all(
  keywords.slice(0, MAX_PARALLEL).map(async (kw) => {
    try {
      const r = await tools.WebSearch({ query: kw, num: 5 });
      return { keyword: kw, ok: true, data: r };
    } catch (e) {
      return { keyword: kw, ok: false, error: String(e) };
    }
  })
);

const succeeded = results.filter(r => r.ok);
const failed = results.filter(r => !r.ok);

text({
  status: failed.length === 0 ? "completed" : "partial",
  total: keywords.length,
  succeeded: succeeded.length,
  failed: failed.map(f => ({ keyword: f.keyword, error: f.error })),
  data: succeeded.map(s => ({ keyword: s.keyword, results: s.data }))
});
```

## Pattern 2: Sequential Pipeline with Data Dependency

Use when: step B needs transformed output from step A.

> Adapt: replace `tools.Read`, `tools.WebFetch` with your actual file-read and URL-fetch tool names and params.

```js
// Example: read config → extract URLs → fetch each → summarize
const config = await tools.Read({ file_path: "/workspace/sources.json" });
const parsed = JSON.parse(typeof config === "string" ? config : config.content || "[]");
const urls = parsed.filter(item => item.url && item.enabled).map(item => item.url);

const fetched = [];
for (const url of urls.slice(0, 10)) {
  try {
    const page = await tools.WebFetch({ url });
    fetched.push({ url, ok: true, length: (page?.content || page || "").length });
  } catch (e) {
    fetched.push({ url, ok: false, error: String(e) });
  }
}

text({
  status: "completed",
  urls_found: urls.length,
  fetched: fetched.length,
  details: fetched
});
```

## Pattern 3: Conditional Branching

Use when: next action depends on previous result.

> Adapt: replace `tools.Read`, `tools.Write` with actual file I/O tool names. Check if your read tool throws on missing files or returns null/empty.

```js
// Example: check if output file exists, create if not
let existing;
try {
  existing = await tools.Read({ file_path: "/workspace/report.md" });
} catch (e) {
  existing = null;
}

if (existing) {
  // File exists — append or validate
  const content = typeof existing === "string" ? existing : existing.content || "";
  const hasHeader = content.includes("# Daily Report");
  text({ action: "skip_creation", reason: "file_exists", has_header: hasHeader });
} else {
  // File doesn't exist — create it
  await tools.Write({
    file_path: "/workspace/report.md",
    content: "# Daily Report\n\nGenerated: " + new Date().toISOString() + "\n"
  });
  // Validate
  const check = await tools.Read({ file_path: "/workspace/report.md" });
  text({ action: "created", valid: !!(check && (check.content || check).length > 10) });
}
```

## Pattern 4: Shell + Parse + Act

Use when: run a command, parse its structured output, take follow-up actions.

> Adapt: replace `tools.Shell` with your actual command-execution tool. Check its params (might be `command`, `cmd`, `script`, etc.) and return shape (`output`, `stdout`, or raw string).

```js
// Example: list files, filter by pattern, read matching ones
const ls = await tools.Shell({ command: "find /workspace/data -name '*.json' -mtime -1", description: "Find recent JSON files" });
const output = typeof ls === "string" ? ls : ls.output || ls.stdout || "";
const files = output.trim().split("\n").filter(f => f.endsWith(".json"));

if (files.length === 0) {
  text({ status: "completed", message: "No recent JSON files found" });
  exit();
}

// Read first 5 files in parallel
const contents = await Promise.all(
  files.slice(0, 5).map(async (f) => {
    try {
      const c = await tools.Read({ file_path: f.trim() });
      return { file: f, ok: true, data: JSON.parse(typeof c === "string" ? c : c.content || "{}") };
    } catch (e) {
      return { file: f, ok: false, error: String(e) };
    }
  })
);

text({
  status: "completed",
  files_found: files.length,
  files_read: contents.filter(c => c.ok).length,
  summary: contents.filter(c => c.ok).map(c => ({ file: c.file, keys: Object.keys(c.data) }))
});
```

## Pattern 5: Bounded Retry

Use when: a read-only operation may transiently fail.

> Adapt: the `retry` helper is pure JS logic — works with any tool. Replace `tools.WebFetch` with your actual URL-fetching tool.

```js
async function retry(fn, label, maxAttempts = 3) {
  for (let i = 1; i <= maxAttempts; i++) {
    try {
      return { ok: true, label, value: await fn(), attempt: i };
    } catch (e) {
      if (i === maxAttempts) return { ok: false, label, error: String(e), attempts: i };
    }
  }
}

const result = await retry(
  () => tools.WebFetch({ url: "https://example.com/api/status" }),
  "fetch_status"
);

text(result);
```

## Pattern 6: Deduplication and Scoring

Use when: multiple sources return overlapping results that need merging.

> Adapt: this pattern is pure JS data processing — no tool calls. Works regardless of what tools produced the input data. Adjust field names (`title`, `url`, `snippet`) to match your actual tool response shapes.

```js
// After fan-out search, deduplicate by URL and score by freshness
const allResults = []; // populated by earlier fan-out

// Flatten
const items = allResults
  .filter(r => r.ok)
  .flatMap(r => (r.data?.results || []).map(item => ({
    title: item.title,
    url: item.url,
    snippet: item.snippet,
    source_keyword: r.keyword
  })));

// Deduplicate by URL
const seen = new Set();
const unique = items.filter(item => {
  if (seen.has(item.url)) return false;
  seen.add(item.url);
  return true;
});

// Sort (example: by title length as proxy — real scoring would use dates/relevance)
unique.sort((a, b) => (b.snippet?.length || 0) - (a.snippet?.length || 0));

text({
  total_raw: items.length,
  after_dedup: unique.length,
  top_10: unique.slice(0, 10)
});
```

## Pattern 7: Artifact Generation + Validation

Use when: create a file then verify it meets requirements.

> Adapt: replace `tools.Write`/`tools.Read` with actual file I/O tools. Adjust params to match real schema.

```js
// Generate markdown report
const reportLines = ["# Analysis Report", "", `Generated: ${new Date().toISOString()}`, ""];
// ... populate reportLines from earlier data gathering ...
reportLines.push("## Summary", "", "Total items analyzed: 42");

const reportPath = "/workspace/analysis_report.md";
await tools.Write({ file_path: reportPath, content: reportLines.join("\n") });

// Validate
const written = await tools.Read({ file_path: reportPath });
const content = typeof written === "string" ? written : written.content || "";
const checks = [
  { name: "non_empty", pass: content.length > 50 },
  { name: "has_title", pass: content.includes("# Analysis Report") },
  { name: "has_summary", pass: content.includes("## Summary") },
];

text({
  status: checks.every(c => c.pass) ? "completed" : "partial",
  artifact: reportPath,
  validation: checks
});
```

## Pattern 8: Command Polling (Long-Running Process)

Use when: a shell command takes time and you need to check its status.

> Adapt: replace `tools.Shell` with actual command tool. Check whether it supports `run_in_background`/`timeout` params — not all environments do.

```js
// Start a background command
const start = await tools.Shell({
  command: "python3 /workspace/process_data.py --output /workspace/result.json",
  description: "Run data processing script",
  timeout: 60000,
  run_in_background: true
});

// The command is running in background; check for output file
// Wait a moment then verify output exists
const check = await tools.Shell({
  command: "test -f /workspace/result.json && echo EXISTS || echo MISSING",
  description: "Check if output file was created"
});

const exists = (check?.output || check || "").includes("EXISTS");

if (exists) {
  const result = await tools.Read({ file_path: "/workspace/result.json" });
  text({ status: "completed", output: "/workspace/result.json" });
} else {
  text({ status: "partial", message: "Script started but output not yet available. Check manually." });
}
```

## Anti-Patterns (Do NOT Do This)

```js
// ❌ Don't copy pattern tool names without checking ALL_TOOLS
await tools.WebSearch({ query: "..." });  // WRONG if your env calls it "web_search" or "search"

// ❌ Don't guess parameter names from patterns
await tools.Read({ file_path: "/x" });  // WRONG if your tool uses { path: "/x" }

// ❌ Don't use unavailable APIs
const resp = await fetch("https://...");  // WRONG - fetch doesn't exist in Exec
console.log(data);  // WRONG - console doesn't exist in Exec

// ❌ Don't fan-out writes (race conditions)
await Promise.all(files.map(f => tools.Write({...})));  // WRONG - writes must be sequential

// ❌ Don't create unbounded loops
while (true) { await tools.Shell({...}); }  // WRONG - always bound with max iterations

// ❌ Don't embed secrets
const API_KEY = ***REDACTED***

// ❌ Don't skip tool discovery and jump straight to orchestration
// WRONG: writing a full script without first running ALL_TOOLS
// RIGHT: first Exec → discover tools, second Exec → real orchestration
```
