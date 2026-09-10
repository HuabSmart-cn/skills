---
name: create-cola-plugin
description: Build, test, and install Cola plugins, or prepare them for sharing through the marswaveai/cola-plugins repository. Use when the user asks to create a Cola plugin or channel plugin, integrate Cola with an external messaging service, bot, device, or tool, install a local Cola plugin, install a plugin from a Git repository URL, or open a pull request that adds or updates a plugin in cola-plugins.
metadata:
  category: development
---

# Create Cola Plugin

## Overview

Create or update Cola plugins with the smallest reliable workflow: inspect the repo, implement the plugin, verify it, then ask whether to install it locally or prepare a pull request for the official plugin repo.

Use the official docs for SDK details instead of copying long API explanations into the skill:

- Cola docs index: `https://docs.colaos.ai/en/docs/`
- Plugin SDK: `https://docs.colaos.ai/en/docs/plugin-sdk/`
- Channels and Plugins: `https://docs.colaos.ai/en/docs/channels-and-plugins/`
- CLI: `https://docs.colaos.ai/en/docs/cli/`

## Workflow

1. Inspect the current repo before editing.
   - Check `git status --short` and avoid touching unrelated dirty files.
   - Read `README.md`, `CONTRIBUTING.md`, `package.json`, and the closest existing plugin under `plugins/*`.
   - Treat `pnpm-workspace.yaml` and the existing package scripts as the source of truth for local commands.

2. Identify the plugin target.
   - Derive a stable lowercase plugin id, usually the product or protocol name.
   - Ask only for missing facts that block implementation: target service/device, incoming and outgoing capabilities, auth/config fields, and any required external API behavior.
   - Do not ask up front whether the result should be local-only or shared unless it affects naming, licensing, or scope. Ask after the plugin is written and verified.

3. Create or update the plugin package.
   - Put official-repo plugins under `plugins/<id>/`.
   - Follow the current package shape used by nearby plugins: `package.json`, `src/index.ts`, `tsconfig.json`, `tsup.config.ts`, and a user-facing `README.md`.
   - Use package name `cola-plugin-<id>` unless the repo already uses a different convention.
   - Depend on the published `@marswave/cola-plugin-sdk`.
   - Keep `cola.plugin.id` equal to the SDK entry id, and keep `cola.plugin.entry` pointed at built JavaScript, normally `./dist/index.js`.
   - Fill `cola.channel` metadata for the settings UI and plugin store. For PR-ready plugins, set `docsPath` to the GitHub README URL in `marswaveai/cola-plugins`.

4. Implement the channel behavior.
   - Prefer `defineChannel(...)` for channel-only plugins.
   - Keep the entrypoint thin: define `id`, `meta`, `capabilities`, `config`, `gateway`, `outbound`, optional `commands`, and delegate protocol-specific logic to small modules.
   - Store secrets in config fields with `type: ***REDACTED***
   - Never commit real tokens, account snapshots, QR-login results, local runtime state, or private message content.
   - For SDK APIs, lifecycle shape, tools, session events, auth, or install semantics, read the official docs above instead of guessing.

5. Verify the plugin.
   - Run focused checks first:
     ```bash
     pnpm --filter "./plugins/<id>" run typecheck
     pnpm --filter "./plugins/<id>" run build
     ```
   - Add focused deterministic tests for config parsing, protocol parsing, outbound formatting, auth/session handling, deduplication, retry behavior, and device/gateway edge cases where relevant.
   - Before a PR, run the repo-level gates:
     ```bash
     pnpm fmt:check
     pnpm lint
     pnpm test
     pnpm build
     pnpm typecheck
     ```
   - Use `pnpm build:registry` only to inspect generated store metadata. Do not commit `registry.json`.

## Finish By Asking

After the plugin is implemented and the relevant checks have run, ask the user to choose one path:

- **Local install only**: install the plugin on this machine and do not prepare a PR.
- **Share by PR**: make the plugin suitable for `marswaveai/cola-plugins`, then branch, commit, push, and open a pull request if the user wants you to proceed.

## Local Install Path

Use this when the user chooses local install only, or when they only want to try the plugin before deciding whether to share it.

`cola plugin install <dir>` symlinks `~/.cola/plugins/<id>` to the source directory instead of copying it, so the installed plugin keeps loading from that directory permanently. The source must live in a persistent location — never `/tmp`, `mktemp` output, or any other OS temp directory: the OS clears those, the symlink goes dangling, and the plugin silently disappears from Cola. When installing from a Git repository URL, clone into `~/.cola/plugin-src/<id>` first, then follow the steps below with that directory.

1. Build the plugin.

   ```bash
   pnpm --filter "./plugins/<id>" run build
   ```

2. Install the plugin directory root, not `dist/`.

   ```bash
   cola plugin install /absolute/path/to/plugins/<id>
   ```

3. If testing against a local Cola checkout instead of an installed `cola` binary, use that checkout's dev CLI.

   ```bash
   pnpm cli:dev plugin install /absolute/path/to/plugins/<id>
   ```

4. Confirm installation when possible.

   ```bash
   cola plugin list
   cola plugin enable <id>
   ```

5. If the plugin does not appear, rebuild and reinstall, then refresh or restart the running Cola Server. The plugin root must contain `package.json`, and `cola.plugin.entry` must point to an existing built file.

## PR Sharing Path

Use this when the user chooses to share the plugin through this repo.

1. Ensure the plugin is under `plugins/<id>/` and has a user-facing README with setup, config, permissions, security notes, and troubleshooting.
2. Ensure `cola.channel.docsPath` points to `https://github.com/marswaveai/cola-plugins/blob/main/plugins/<id>/README.md`.
3. Bump the plugin package version for public updates. Do not overwrite a version that may already have been published.
4. Run the repo-level gates listed in the verification section.
5. Inspect `pnpm build:registry` output if store metadata changed, but leave `registry.json` uncommitted.
6. Prepare a focused branch and commit that excludes unrelated dirty worktree changes.
7. Open a PR with the plugin purpose, user-facing setup summary, verification commands, and any external account/device assumptions.

Current repo automation validates PRs with formatting, lint, and build/typecheck for changed plugins. Public release happens from `main` when plugin package manifests change, or through a manual release workflow.
