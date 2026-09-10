# Metadata authority and status model

## One authority per fact

| Data | Authority | May decide |
| --- | --- | --- |
| `skills/**` | captured original source | original text and bundled source files only |
| `manifest.json` | generated public catalog | discovery, display and repository entry location only |
| `registry/capabilities/*.json` | HuabSmart Registry | declared dependency, Runtime requirement, permission, lifecycle and verification status |
| `registry/dependency-candidates.json` | generated textual analysis | candidate names only; never required/optional dependency |
| `HBS_BUNDLE.json` | derived at download time | a snapshot of the above facts for one package; never an independent authority |
| website runtime data | presentation cache | display only; it must not invent Registry or Runtime facts |

If values conflict, the higher row in this order wins for the relevant fact: original source for source text; Registry for HuabSmart control-plane facts; catalog for discovery only. A bundle or website never overrides Registry.

## Status model

- `cataloged`: an asset record and entry file exist in this repository.
- `dependency_resolved`: every declared required dependency has a Registry target; it does not mean installed.
- `ready_for_runtime_install`: Resolver produced an unblocked plan. It does not mean safe, copied, discovered, loaded or called.
- `installed`, `runtime_discovered`, `loaded`, `invoked`, `verified`: Runtime-only states. Each requires a version-bound receipt and must not be inferred from a plan.
- `blocked`: Resolver found missing or ambiguous dependencies.

`safeToInstall` is deliberately prohibited. It conflates an unblocked metadata plan with real Runtime security and execution evidence.
