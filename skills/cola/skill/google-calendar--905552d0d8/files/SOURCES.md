# Sources and versions

- Google Workspace CLI (`gws`): self-maintained build. Source lives in `marswaveai/cola-integration-cli` under `google-workspace-cli/` (upstream `googleworkspace/cli` tag `v0.22.5`, commit `705fb0e`, with Cola patches applied in place — that directory's README records the patch list, rebuild commands, and upstream-upgrade flow); the version string stays `0.22.5`. Before patching, the unpatched build was verified against the previously bundled official binary (`--version` and `auth login --help` byte-identical). macOS targets are built with the Apple toolchains, `win32-x64` with `x86_64-pc-windows-gnu` (the official release uses MSVC).
- Skill reference: `googleworkspace/cli` tag `v0.22.5`, `skills/gws-calendar`, `skills/gws-calendar-agenda`, `skills/gws-calendar-insert`, and `skills/gws-shared`.

`SKILL.md` is a calendar-only rewrite of the upstream skills:

- Only the calendar command surface is kept; every other Google service and all upstream non-calendar skills, examples, and repository-interaction guidance are removed.
- Login uses `gws auth login` with calendar-only scopes (`https://www.googleapis.com/auth/calendar.events`, `https://www.googleapis.com/auth/calendar.calendarlist.readonly` plus OpenID identity). Config directory follows `GOOGLE_WORKSPACE_CLI_CONFIG_DIR` when set.
- Resources outside the granted scopes (`acl`, calendar create/delete, `settings`, `watch`/`channels`) are documented as unavailable instead of listed as commands.

Binary hashes are recorded in `SHA256SUMS`; the final ZIP hash is recorded in the sibling `.zip.sha256` file.
