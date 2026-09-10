---
name: sites-hosting
description: Host websites with Sites. Always use after `sites-building`, and use for website publishing, deployment, hosting management, or projects containing `.openai/hosting.json`.
---

# Sites hosting

Publish the exact validated source with the shortest safe sequence. Use native Sites connector calls directly, following their descriptions for arguments and archive requirements. Treat IDs and cursors as opaque and copy them unchanged from the selected Site's manifest or tool responses.

Read `references/environment.md` for this environment's native tool calls, archive delivery, and final handoff.

## Site lifecycle ownership

Only the Site-owning agent responsible for the user's requested Site may run `sites-hosting`, call `create_site` or any other Sites tool, edit the Site checkout or `.openai/hosting.json`, obtain source credentials, commit or push, save a version, deploy, or perform the final browser handoff. A spawned subagent must return its assigned image, asset, or research result without invoking this skill or any Sites tool. An independently started background or invisible task that owns the requested Site remains its Site-owning agent.

## Communicate clearly

Assume the user is a nontechnical knowledge worker. Keep source control, credentials, IDs, commits, branches, archives, versions, packaging, connector calls, and deployment polling out of user-facing messages. Usually send one update when publishing begins, then the final URL or a plain-language blocker.
For example: `Your site is ready. I’m publishing it privately now.`

## Rules

- Publish after successful validation unless the user requested local-only work.
- Publishing does not require additional browser testing or visual QA. Preserve the existing Site tab as its single user-facing view; a failed browser handoff does not block publishing.
- Treat `public/screenshot.jpeg` (`screenshot.jpeg` under `static.directory` for buildless sites) as an optional deployment thumbnail. Preserve an existing file. Create or refresh it only when the user explicitly requests a Sites deployment thumbnail; a generic screenshot request does not count. Missing or failed capture never blocks validation, version saving, or deployment.
- Store only `project_id`, optional `static` configuration, logical `d1` and `r2` bindings, and requested supported `capabilities` in `.openai/hosting.json`. Manage runtime values through Sites.

## Fast publish sequence

For unchanged source with a known archive-backed version, reuse that version instead of rebuilding, committing, packaging, uploading, or saving again; continue at step 5. A source-only version may still need its first archive; saving the matching source and archive completes that same version. If the requested version's deployment is already running, continue at step 8 instead of starting another deployment. Use known response IDs; do not add discovery calls to this path.

`<plugin-root>` is the installed plugin directory containing `skills/` and `scripts/`. Run each script directly in a separate exec call with absolute paths and literal arguments, without shell variables, redirects, or chaining. Set exec's working directory to the Site checkout and poll yielded sessions to completion.

1. Reuse the validated output from `sites-building` when the source has not changed. Plain static assets need no build; otherwise rebuild only when needed, using `node <plugin-root>/scripts/build-site.mjs`.
2. Collect the registration call started during `sites-building` before committing or packaging, then re-read `.openai/hosting.json` and verify its `project_id`. Reuse that Site and its source write credential; renew a missing or expired credential for the same Site. If hosting a new Site directly, start registration only when no `project_id` or unresolved prior attempt exists. Follow [Register once while building](../sites-building/references/environment.md#register-once-while-building) for the call, persistence, and recovery steps.
3. Use a Git repository rooted at the selected Site project, initializing one there if needed; do not commit or push an unrelated parent repository. Commit the exact validated source. Push it with the returned credential as a per-command HTTP authorization header. Keep the credential out of remote URLs, Git configuration, files, and user-facing output. Wait for the push to finish successfully, then run `git rev-parse --verify HEAD` in the Site checkout and copy its complete output verbatim as `commit_sha`. Never expand, pad, or guess a SHA from abbreviated commit or push output. Keep that source revision unchanged through packaging and saving.
4. Package with `node <plugin-root>/scripts/package-site.mjs <project> <archive>`.
5. Choose the deployment audience from the site's current access, not tool availability. A site created in this flow remains owner-only until its access changes. For an existing site, call `get_site` and treat it as owner-only only when `current_user_role` is `owner` and `access_policy` verifies `access_mode: "custom"`, exactly one `allowed_account_user_ids` entry, zero `external_visitor_count`, and no workspace or tenant group IDs. Missing or ambiguous access is not verifiably owner-only.
6. For owner-only hosting, use `deploy_private_site_version` when reusing a stored archive's version. Otherwise, use `save_version_and_deploy_private` when exposed in the current tools, passing the pushed `commit_sha` and archive. It saves and privately deploys that exact version in one call; do not save separately first. If the tool is unavailable or returns `tool_not_enabled`, use `save_site_version` followed by `deploy_private_site_version` with its returned version ID. If private hosting returns `site_not_owner_only`, do not retry it; follow the approval path in step 7.
7. For a shared, public, or not verifiably owner-only site, save one version and ask for approval naming the resolved access level, such as `Publish publicly` or `Publish to existing shared access`, plus `Not now`. Use `request_user_input` only when available and permitted for approvals; otherwise ask in the conversation. Wait for the response, and call `deploy_site_version` only after approval. Reuse an already saved version instead of saving again.
8. If the returned deployment status is not terminal, poll `get_deployment_status` directly until it succeeds or fails. Do not poll after a terminal result. Use discovery calls only when an error requires them.

If hosting fails after saving and returns `saved_version_id`, retain it and resume with the appropriate deployment tool after addressing the failure; do not repeat the save. If a timeout or lost response leaves the outcome unknown, reconcile existing versions for the pushed commit before retrying. Leave build errors and repairs to the agent; the combined tool does not build or repair local source.

On `stale_commit_sha`, rerun `git rev-parse --verify HEAD` and verify that commit is the configured remote branch's HEAD before retrying. If the source changed, validate, commit, push, and package it again. Do not substitute a different remote SHA while keeping an archive built from another revision.

## Existing sites and advanced capabilities

- Reuse an existing `project_id` and valid source credential when available.
- If a credential is absent or expired, obtain one with `create_source_repository_write_credential` and reuse it until expiry.
- If the D1 schema changed, ensure generated migrations are present before packaging.
- For server-backed builds, require `dist/server/index.js`, static assets when emitted, `dist/.openai/hosting.json`, and `dist/.openai/drizzle/**` when migrations exist.
- For static-only builds, require an `index.html` in the public output directory selected by `static.directory` in `.openai/hosting.json`. The helper normalizes that output to `dist/` and rewrites the archived `static.directory` to `dist`. Static builds cannot use runtime bindings, capabilities, or migrations.
- For non-vinext server-backed projects, use the established Cloudflare Workers-compatible build output and adapt staging only as required by the connector contract.

## Handoff

After the deployment response or `get_deployment_status` reports `status: "succeeded"`, follow the Handoff section in `references/environment.md` to show the exact deployed URL. Preserve the existing Site view after subsequent fixes and redeployments.

Then return the deployed Sites URL and a concise description of what the user can do. If the deployment is unsuccessful, do not perform the success handoff; explain the user-visible reason and next step. Keep source credentials and temporary archives private. Do not include file paths, commands, build details, IDs, commits, or version information unless the user asks.
