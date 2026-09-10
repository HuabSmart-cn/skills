# Sources and versions

- Cola CLI (`cola-outlook-calendar`): built from `marswaveai/cola-integration-cli` (`integration-cli/`), the same crate that produces this skill package's mail-side counterparts in `universal-email`. It talks to Microsoft Graph directly; there is no upstream third-party CLI behind it.
- Microsoft Graph endpoints and OAuth scopes used by the binary are documented in `SKILL.md`.

Binary hashes are recorded in `SHA256SUMS`. The binaries are built by hand and
committed to this repository — see `apps/agent-runtime/cli-sources/README.md`
for the change procedure.
