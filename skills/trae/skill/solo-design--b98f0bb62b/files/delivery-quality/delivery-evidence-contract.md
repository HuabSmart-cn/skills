# Output Delivery And Artifact Readiness Rules

This file keeps the historical delivery-evidence name for compatibility. The
finish gate is about Design engineering readiness and link-free delivery text,
not a fixed natural-language summary format.

## Preview Method

**Default (ONLY) method**: Let the host application render the `.design` artifact automatically. Do not output a manual Markdown link, bare file path, `computer://` URL, or "查看设计项目 / 查看 xxx 页面" link in the assistant summary.

**Do NOT** start a local HTTP server (`python -m http.server`, `npx serve`, etc.) or call `OpenPreview` unless the user **explicitly** requests browser preview (e.g., "在浏览器中打开", "show me in browser", "I want to see the HTML preview", "open preview page").

When the user does explicitly request browser preview:
1. Start a local HTTP server pointing to the project directory
2. Call `OpenPreview` with the server URL

## Artifact Declaration (Finish Summary must not include links)

When the task is complete (calling the Finish tool), **the summary must not include any Markdown link, bare path, `computer://` URL, or manual artifact link text**. The host-rendered artifact entry is the only visible entry point for the `.design` artifact.

## Finish Gate

Before final response, verify the completion evidence already produced by the workflow. This gate must not start preview, browser automation, or an extra full validation run by itself.

- HTML/page workflows require `validation-report.json success=true`. **Exception:** restore_1to1 workflows do NOT require `validation-report.json` — skip `validate-design-workspace.mjs` and proceed directly to `validate-finish-readiness.mjs`.
- If any project file was modified after the validation report was produced, return to the workflow's final validation step before responding.
- HTML/page workflows must pass `validate-finish-readiness.mjs <design-project-path> --check=all` after validation succeeds. Restore workflows must pass `validate-finish-readiness.mjs <design-project-path> --check=all --final-response-file=<draft.md>` so the delivery text is checked for link-free/path-free policy and recorded by hash. `--check=artifact`, `--check=repair-ledger`, and `--check=response` are partial diagnostics, not final delivery gates.
- Natural-language completion is allowed when the selected workflow's validation and evidence gates have already passed.
No fixed final-summary table, ending style, or follow-up question is required by this contract.

Forbidden examples:

```
[查看设计项目](computer://...)
查看 design-4 页面
/absolute/path/to/project.design
computer:///absolute/path/to/project.design
```

Rules:
- Finish summary should be short natural language only, in the user's language.
- Mention what changed and that the result is available in the generated artifact entry, but do not create a clickable link yourself.
- For restore workflows, write the final summary draft to a small local draft file and pass it to `validate-finish-readiness.mjs <design-project-path> --check=all --final-response-file=<draft.md>` before final delivery. The final answer must be text-equivalent to the checked draft.
- The `.design.name` / backend `display_name` is still responsible for the host-rendered artifact title. Do not duplicate it as a manual link in text.
- In redesign-ui flow, the host-rendered artifact entry should point to the duplicate project's `.design` artifact; the textual summary still contains no link.

Suggested final summary template:

```text
Completed {brief result summary}. The result is available in the generated artifact entry.
```
