# Codex environment

## Hosted runtime

Hosted server code runs in Cloudflare Workers, with **128 MB of memory per isolate**, shared across concurrent requests and including JavaScript and WebAssembly allocations.

## Project setup

### 1. Choose or reuse the project

- **New Site:** Use the task's workspace directory if it is suitable for initializing a new Site; otherwise choose an empty project directory without moving, deleting, or overwriting existing files.
- **Existing Site:** Preserve its package manager, lockfile, scripts, architecture, and binding names. Run `node <plugin-root>/scripts/install-dependencies.mjs` only when a `package.json` is present and dependencies are missing; do not initialize it again.
- **Retained template:** Run `node <plugin-root>/scripts/project-setup.mjs --template-source <absolute-sanitized-source-directory>` in the empty project directory, then `node <plugin-root>/scripts/install-dependencies.mjs` if the template has a `package.json`. Do not copy the bundled starter over it.

### 2. Set up the selected project

For plain static assets, author `dist/index.html` and supporting assets directly, and set `static.directory` to `dist` in `.openai/hosting.json`. Keep authored assets tracked in Git. Skip starter setup, dependency installation, and build scripts; validate entrypoints, requested routes, local asset references, and JavaScript syntax before hosting. Framework static exports still use their installation and build scripts.

For a new Site using the bundled starter, run `node <plugin-root>/scripts/project-setup.mjs` with the selected project directory as the working directory and retain the session until completion. It copies `templates/vinext-starter` with dotfiles, leaves Git metadata untouched, and runs the locked `npm run install:ci` without an npm scaffolder. Initialize Git during publishing, if needed.

- **Network:** Uncached dependencies require npm registry access. Request network escalation for the initializer only when the sandbox's registry access requires it.
- **Environment:** Preserve the caller's HOME, npm cache, registry, proxy, and temporary-directory settings. The installer uses the project's own lockfile even inside an npm workspace and includes required dev/optional dependencies despite production/omit settings.
- **Authoring:** Begin source work once copied files exist; edit the Site checkout, not the bundled starter. Do not overlap installers. Reuse the starter's bundled components, helpers, and dependencies; avoid redundant installs.

## Register once while building

For the split scaffold and `create_site` workflow, keep registration in the Site-owning task. The running call's **cell ID** is used to collect its result; the created **Site ID** is saved as `project_id`.

1. Reuse an existing `project_id` or an already-running registration. An empty `.openai/hosting.json` is not a reason to start another `create_site` call.
2. Start `create_site` once in its own `functions.exec` call. Put `// @exec: {"yield_time_ms": 1000}` on the first line, and await the request inside that script. This lets the agent continue after about one second while registration keeps running. Keep the returned cell ID if the call is still running; yielding does not cancel it.
3. While registration runs, inspect source and write the application through subsequent tool calls. Do not edit `.openai/hosting.json` from another cell or immediately wait while useful independent work remains. Keep dependency checks and unrelated reads out of the registration cell; awaiting several tools in a cell that has not yielded still blocks the next model response.
4. Inside that same registration script, check that `create_site` succeeded. Keep the exact returned Site `id` and source write credential in session memory before attempting to save the ID as `project_id` in `.openai/hosting.json`. Save it immediately, preserve the file's other fields, reject a conflicting ID, and write the file atomically. Return only the Site ID, whether it was saved, and whether a credential is available; never print the credential or full response.
5. Before other hosting-manifest edits, committing, pushing, packaging, or saving a version, collect that same registration call and re-read `.openai/hosting.json` to verify its ID. Use `functions.wait` only if the call returned a running-cell ID; keep that same ID if it is still running. Otherwise inspect the completed result directly. Verify both request success and that the ID was saved. Wait before a build only when compiled code needs registration values; saving only the ID does not require rebuilding when the packager copies the current manifest.

### Errors and resuming

- If using `store`, use a Site-specific key. Later cells can read its values only after the registration cell completes. Keep credentials out of files, Git configuration, remote URLs, and user-facing output.
- If the local write fails after creation succeeds, keep the known Site ID and credential. Return the Site ID with `manifest_persisted: ***REDACTED***
- A timeout, cancellation, missing cell, malformed response, or transport failure can leave creation's outcome uncertain. Preserve any known Site ID and resolve the original attempt or use Sites discovery before proceeding; do not issue another `create_site` call. A short wait, installation failure, or build failure is not a reason to create again. Treat quota, permission, and access errors as terminal.
- Retry creation only after the previous attempt has definitively failed with an explicit temporary failure or slug conflict and no Site was created. Resolve an ambiguous outcome before retrying; never start a second request while the first is running.
- If only the source write credential is missing, expired, or lost after resumption, renew it for the same Site during hosting.
- If the environment cannot keep a cell running after yielding, await the single registration request normally. Never drop an unawaited promise or cancel the request to regain model control.

## Starter capabilities

- **Build:** Preserve `sites()` from `./build/sites-vite-plugin` in `vite.config.ts`; `node <plugin-root>/scripts/build-site.mjs` runs the project's build script to emit the Worker, hosting metadata, and migrations.
- **Auth:** Use the bundled `app/chatgpt-auth.ts` helpers for sign-in-gated routes; do not install another auth scaffold. Preserve equivalent integrations in existing/retained projects and follow the shared authentication guidance.
- **Storage:** Declare logical D1/R2 bindings in `.openai/hosting.json` (`DB`/`BUCKET` when enabled); preserve existing binding names. Access R2 only server-side through `env` from `cloudflare:workers`. For bundled-starter D1 previews, follow [Local D1 migrations](../templates/vinext-starter/README.md#local-d1-migrations).

## Development and first preview

In a visible foreground thread, start the project's development script or a local HTTP server for the static directory in a retained session as soon as setup finishes. Request network escalation for the initial server launch. Reuse the same session through preview and publishing, and stop it during final teardown.

A Site-owning agent running in an independently started background, delegated, or invisible task initializes normally but does not start a browser-only preview unless its task otherwise needs the server. Skip `open_in_codex` in that case.

## Preview handoff

Make one lightweight non-browser request to the exact Local URL printed by the development server, using the same networking context as the server (with network escalation when needed), to force the current route to render. Require a non-error response and successful compilation when needed, but do not inspect the response body as visual QA. Then use `open_in_codex` to show that Local URL. Establish a stable browser-tab ID from the first preview and reuse it through edits, publishing, and any later fixes.

## Browser testing

Use the environment's browser tools only when the user explicitly requests browser testing. Reuse the existing Site tab and development server; opening the user-facing preview does not itself require screenshots, DOM inspection, or interaction testing.
