---
name: TRAE-code-mode-orchestrator
description: "Code Mode (Exec) usage patterns and applicable scenarios. Covers parallel fan-out, pipeline with JS transforms, conditional branching, loop-until-condition, and multi-source aggregation. Trigger when the task benefits from orchestrating multiple tool calls in a single JavaScript script rather than sequential direct calls."
---

# TRAE Code Mode Orchestrator

> Resolve `references/exec-patterns.md` and `references/usecase-patterns.md` relative to this file.

## What Exec Actually Is

`Exec` runs JavaScript in an isolated V8 sandbox. It has **no** filesystem, **no** network, **no** `fetch`, **no** `require`, **no** `process`, **no** `setTimeout`. The only way to interact with the outside world is through `await tools.<name>(args)`.

Available globals:
- `tools` — proxy to call any tool exposed in the current session
- `ALL_TOOLS` — read-only array of `{ name, description, parameters }` for runtime schema inspection
- `text(value)` — emit output (JSON.stringify for non-strings)
- `exit()` — stop execution early, preserving prior `text()` output

## When to Use Code Mode (Decision Criteria)

Use Code Mode when **at least two** of these conditions hold:

| # | Condition | Example |
|---|-----------|---------|
| 1 | **Fan-out**: same tool called on N items in parallel | Search 8 news URLs concurrently, read 12 files |
| 2 | **Data dependency between steps**: output of step A feeds into step B's parameters after JS transformation | Parse JSON from Shell output → extract IDs → call API per ID |
| 3 | **Conditional branching**: next action depends on prior result | File exists? read it : create it. Command exit 0? continue : retry |
| 4 | **Loop/iteration**: process a list of items with the same logic | For each keyword: search → filter → collect |
| 5 | **Aggregation/dedup/scoring**: combine results from multiple tool calls using JS logic | Merge search results, remove duplicates by URL, sort by date |
| 6 | **Validation gate**: check an artifact before reporting success | Read generated file → verify non-empty and contains expected sections |

### When NOT to Use Code Mode

Do NOT use Code Mode when:

1. **The core work is LLM generation** — writing essays, novels, analysis reports, code, or creative content. Exec is a tool orchestrator, not a text generator. If the task's bottleneck is "think and write 2000+ words," Code Mode adds no value.

2. **Linear A→B→C with no branching** — if each step is a single tool call and the next step is always the same regardless of output, just make direct tool calls. Three sequential calls don't need a JS wrapper.

3. **Single tool call** — looking up a stock price, running one search query, reading one file. No orchestration needed.

4. **The task requires capabilities not available in current runtime** — direct HTTP requests (`fetch`), real-time streaming, timers/cron, or persistent state across sessions. Always check `ALL_TOOLS` to confirm what's actually available.

5. **Unclear scope or needs clarification** — if the user hasn't specified what to do, ask first. Don't wrap uncertainty in a script.

## Decision Flowchart

```
User request arrives
    │
    ├─ Is the core work LLM text generation?
    │   YES → Direct execution (no Code Mode)
    │
    ├─ Can it be done with ≤ 2 sequential tool calls?
    │   YES → Direct tool calls
    │
    ├─ Does it involve fan-out OR loop OR conditional branching?
    │   YES → Code Mode
    │
    ├─ Does it need to merge/dedup/transform outputs between tools?
    │   YES → Code Mode
    │
    └─ Is there a validation step after producing artifacts?
        YES → Code Mode
        NO  → Direct tool calls
```

## Execution Protocol

### Prerequisite: Load Tool Definitions from System Instruction

Before writing any Exec code, first refer to the **Code Mode / Exec tool description in the system instruction** of your current session. Use it as the ground truth for what Exec can and cannot do.

### Step 0: Discover Available Tools (MANDATORY)

Before writing any Exec orchestration code, **always** inspect the runtime first:

```js
const schema = ALL_TOOLS.map(t => ({
  name: t.name,
  desc: t.description?.slice(0, 100),
  params: t.parameters?.properties
    ? Object.entries(t.parameters.properties).map(([k, v]) => `${k}:${v.type}`)
    : []
}));
text(schema);
```

This returns the **exact** tool names and parameter schemas available in your current session. You must use these names and parameter structures — not the ones from pattern examples.

**Critical rules:**
1. **Never assume tool names.** Patterns use `tools.WebSearch`, `tools.Shell` etc. as _illustrations_. Your environment may expose completely different names.
2. **Never assume parameter shapes.** A pattern shows `tools.Read({ file_path: "..." })` — your actual tool might need `{ path: "..." }` or `{ filename: "...", encoding: "utf8" }`. Check `ALL_TOOLS` for the real schema.
3. **Two-step execution is the norm.** First Exec call: discover tools → read the output. Second Exec call: write orchestration code using real names/params.
4. **If a needed capability isn't listed in ALL_TOOLS, stop.** Don't guess alternatives — report that the capability isn't available.

### Step 1: Map Task to Tool Capabilities

After tool discovery, map task requirements to available tools:

```
Task: "Search 6 keywords, deduplicate results, write report"
Available: WebSearch(query, num), Write(file_path, content), Read(file_path)

Plan:
  - Fan-out: 6× WebSearch
  - JS transform: dedup by URL, sort
  - Sequential: 1× Write
  - Validate: 1× Read
```

If the available tools don't cover a requirement (e.g., no search tool exists), fall back to direct tool calls outside Exec or ask the user.

### Step 2: Write Bounded Code Using Actual Tool Signatures

Rules:
- Copy tool names and parameter keys **exactly** from ALL_TOOLS output
- Every loop has a max iteration count
- Every `Promise.all` is for independent, **read-only** calls only
- Side effects (write, shell commands that modify state) are sequential
- `try/catch` around tool calls that might fail — tool responses vary; handle both string and object returns
- One final `text({...})` with structured result

**Handling tool return values:** Tool responses are not standardized. They may return:
- A raw string (e.g., file content, command output)
- An object with `output`, `content`, `stdout`, or other fields
- Use defensive access: `const out = typeof r === "string" ? r : (r.output || r.content || r.stdout || JSON.stringify(r));`

### Step 3: Validate Before Claiming Success

After producing artifacts, verify them:
- Read the file back, check it's non-empty
- Check command exit codes
- Verify expected fields exist in parsed output

## Pattern Library

See `references/exec-patterns.md` for reusable JavaScript templates.
See `references/usecase-patterns.md` for task-type patterns with decision trees.

## Safety Rules

1. **No secrets in code** — never hardcode tokens, cookies, passwords, or API keys in Exec scripts
2. **Side effects require confirmation** — file deletion, git push, external posts, deployments must be confirmed before execution
3. **Bound all execution** — max 20 items in a fan-out, max 5 retries, max 3 polling rounds. If limits are exceeded, report partial results.
4. **Don't bypass permission prompts** — if a tool requires approval, nested calls still surface that approval
5. **Report honestly** — if validation fails or results are partial, say so in the output

## Output Contract

Every Code Mode execution should end with:

```js
text({
  status: "completed" | "partial" | "blocked",
  items_processed: N,
  outputs: ["path/to/artifact1", "path/to/artifact2"],
  validation: { checks_passed: N, checks_failed: N, details: [...] },
  errors: [...],  // empty if all good
});
```

The agent reports this to the user as a concise summary. Never claim success beyond what validation confirmed.
