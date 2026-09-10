# OpenAI-Compatible Custom Provider Schema (Hermes)

The `providers:` block in `~/.hermes/config.yaml` is the user-defined
counterpart to the plugin-shipped providers at
`~/.hermes/hermes-agent/plugins/model-providers/<name>/`. They share the
same schema but live in two different config locations:

| Source | Path | Process |
|---|---|---|
| Plugins (shipped) | `hermes-agent/plugins/model-providers/<name>/__init__.py` | install/upgrade |
| User custom | `config.yaml` → `providers:` | `hermes config set` |
| Legacy (pre-v12) | `config.yaml` → `custom_providers:` (list) | auto-bridged via `get_compatible_custom_providers()` |

## Recognized keys (snake_case)

Source: `hermes_cli/config.py::_normalize_custom_provider_entry` and
`_register_provider_pool_entry` (~lines 1280–1500).

| Field | Type | Required | Notes |
|---|---|---|---|
| `name` | str | no | display name in picker; defaults to dict key |
| `base_url` | str | **YES** | OpenAI-compatible inference endpoint |
| `url` | str | alt | legacy synonym for `base_url` |
| `api` | str | alt | legacy synonym for `base_url` |
| `key_env` | str | recommended | env var name holding the API key |
| `api_key_env` | str | alias | auto-mapped to `key_env`; prefer `key_env` to avoid the warning |
| `api_key` | str | fallback | inline key — only when `key_env` isn't viable; lands in config.yaml as plaintext |
| `api_mode` | str | optional | `openai` (default in practice), `anthropic_messages`, `codex_responses` |
| `transport` | str | alias | v11→v12 migration wrote `api_mode` under `transport`; both accepted |
| `discover_models` | bool | optional | enable `/models` catalog probe |
| `model` / `default_model` | str | optional | fallback when `--model` isn't given |
| `models` | list | optional | static model list |
| `extra_body` | dict | optional | vendor-specific body pass-through |
| `extra_headers` | dict | optional | vendor-specific header pass-through |
| `context_length` | int | optional | context window hint |
| `rate_limit_delay` | float | optional | client-side throttle |
| `request_timeout_seconds` | float | optional | per-request timeout |
| `stale_timeout_seconds` | float | optional | pool-entry freshness TTL |
| `ssl_ca_cert` | str | optional | path to custom CA bundle |
| `ssl_verify` | bool | optional | disable TLS verification |

## camelCase aliases (warned but accepted)

| Alias | Maps to |
|---|---|
| `apiKey` | `api_key` |
| `baseUrl` | `base_url` |
| `apiMode` | `api_mode` |
| `keyEnv` | `key_env` |
| `apiKeyEnv` | `key_env` (OpenClaw-compatible) |
| `defaultModel` | `default_model` |
| `contextLength` | `context_length` |
| `rateLimitDelay` | `rate_limit_delay` |

Unknown keys emit a one-shot warning per provider on load: `unknown config keys
ignored`. They are dropped, not silently kept.

## Credential resolution order

`hermes_cli/runtime_provider.py::_get_named_custom_provider` (and friends):

1. `entry["key_env"]` → `os.environ[KEY_ENV]`
   - `os.environ` is populated by `load_env()` from `~/.hermes/.env` at CLI boot.
   - If the env var isn't set, this returns empty.
2. `entry["api_key"]` — inline fallback.
3. Credential pool match by **base_url** AND **name**, in that priority order
   — only fires if a pool entry's normalized `name` (`strip().lower().replace(' ','-')`)
   equals the `providers.<slug>` dict key. The pool key shape is
   `custom:<normalized_name>`. See `agent/credential_pool.py::get_custom_provider_pool_key`.

A user-defined `providers.bailian-token-plan` block thus does NOT automatically
pick up a credential added via `hermes auth add alibaba` — those are separate
pools keyed by different slugs.

## Legacy `custom_providers:` shape

Before v12 the field was a list:
```yaml
custom_providers:
  - name: bailian-token-plan
    base_url: https://...
    api_key: ***REDACTED***
```

Modern Hermes bridges it via `get_compatible_custom_providers(config)` in
`hermes_cli/config.py`. Don't mix shapes in one file — pick one.

## The "credential pool" path is its own thing

`hermes auth add <provider> --type api-key` writes to `~/.hermes/auth.json` →
`credential_pool.<provider>` (a *list* of `Credential` entries). Each entry has
its own `access_token` and optional `base_url`. The custom-provider resolver
in `_try_resolve_from_custom_pool` matches a pool entry to a
`providers.<slug>` block only when both the normalized `name` matches AND
(optionally) base_url matches. See the credential-pool source for full rules.

Practical implication: if you build a `providers.bailian-token-plan` block,
authenticate it via `key_env`+`.env`, not via `hermes auth add alibaba`.
