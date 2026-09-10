# Codex environment

## Tools and archives

Pass the absolute local archive path to the native version-saving tool; the connector uploads that file. Keep the archive unchanged in the same execution environment until saving succeeds.

## OpenAI API keys

When a site needs `OPENAI_API_KEY`, use the ["OpenAI Developers"](plugin:***REDACTED***

## Handoff

Use `open_in_codex` to show the exact deployed URL in the existing Site tab using the stable browser-tab ID established for its first preview. If no Site tab exists, open one with a stable browser-tab ID. Reuse that same tab after subsequent fixes and redeployments so the user finishes with one working view of the deployed Site.

In a delegated, background, or invisible thread, skip `open_in_codex` and say why. A failed browser handoff does not block returning the successfully deployed URL.
