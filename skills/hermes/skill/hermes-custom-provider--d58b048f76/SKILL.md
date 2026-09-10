---
name: hermes-custom-provider
description: "Wire a custom OpenAI-compatible LLM endpoint into Hermes."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos, linux, windows]
metadata:
  hermes:
    tags: [hermes, providers, openai-compatible, configuration, setup, vision, llm-gateway, bailian, qwen, custom-endpoint]
    related_skills: [hermes-agent]
---

# Custom OpenAI-Compatible LLM Providers in Hermes Agent

Trigger this skill when the user wants to point Hermes at an LLM endpoint that
isn't one of the bundled plugins at `~/.hermes/hermes-agent/plugins/model-providers/`.
The right shape is a `providers:` entry + optional `model_aliases:` entry in
~/.hermes/config.yaml, plus a credential in ~/.hermes/.env. NOT a new plugin,
NOT a `hermes auth add` alone.

## When to use

- Third-party OpenAI-compatible gateway (Alibaba Bailian Token Plan, Xiaomi Mimo MaaS, Zhipu MaaS tier, OpenCode Zen, etc.)
- Local OpenAI-compatible server (Ollama with auth, vLLM, LiteLLM proxy, llama.cpp server)
- Re-pointing one of the built-in provider slots at a different endpoint

## When NOT to use

- A provider that already ships as a plugin (`hermes auth add <provider>` is enough)
- A pure OAuth flow (`hermes login` or `hermes auth add <provider> --type oauth`)

## Minimal working config

```yaml
# ~/.hermes/config.yaml — extend the top-level `providers:` and `model_aliases:` blocks
providers:
  bailian-token-plan:                            ***REDACTED***
    name: Alibaba Bailian Token Plan             # picker display label
    base_url: https://token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1
    key_env: ALIBABA_TOKEN_PLAN_API_KEY          # env var holding the API key
    api_mode: openai                             # openai / anthropic_messages / codex_responses
    discover_models: true                        # live /models probe

model_aliases:
  qwen-vision:                                   # alias name — DOT-FREE (see Pitfalls §B)
    model: qwen3.7-plus
    provider: bailian-token-plan
```

Wire the key through Hermes's own writer (daemon and write_file both refuse .env
edits — see Pitfalls §A):
```bash
hermes setup                                      # wizard → save_env_value path
# OR one-shot:
python3 -c "from hermes_cli.config import save_env_value; save_env_value('ALIBABA_TOKEN_PLAN_API_KEY', 'sk-...')"
```

## Verification protocol (always run all 3)

1. **Raw HTTP** (no Hermes — isolates provider/server issues)
   ```bash
   curl -sS -o /tmp/r -w 'HTTP=%{http_code}\n' \
     -X POST "$URL/chat/completions" \
     -H "Authorization: ***REDACTED***
     -d '{"model":"<id>","messages":[{"role":"user","content":"reply PONG"}],"max_tokens":10}'
   ```
   Expect `HTTP=200` and `choices[0].message.content`. Anything else → provider problem.

2. **Hermes E2E** with explicit provider + model
   ```bash
   hermes chat -q "ping" --provider <slug> --model <model_id>
   ```
   - `401 Invalid API-key` → key not loaded (Pitfalls §A or §D)
   - `404 Model not found` → model_id is wrong at the gateway
   - `Unknown provider '<slug>'` → config not picked up; check spelling in `hermes config get providers`

3. **Alias switching**
   ```bash
   hermes chat -q "ping"
   /model <alias-name>     # session-scoped
   /model <alias> --global # persistent default
   ```
   Fails with "Unknown alias"? See Pitfalls §B.

## Pitfalls

**§A — Writes to ~/.hermes/.env and ~/.hermes/config.yaml are gated**
- `echo KEY=val >> ~/.hermes/.env` → **terminal daemon blocks** ("no user consent") even after prior verbal consent.
- `write_file` / `patch` on `~/.hermes/.env` → **refused** ("protected system/credential file").
- `write_file` / `patch` on `~/.hermes/config.yaml` → **refused** ("security-sensitive configuration").
- Legal write paths only:
  1. `hermes config set KEY VAL` (config.yaml, any nested depth via dotted path)
  2. `hermes auth add <provider> --type api-key --api-key '…'` (auth.json pool)
  3. `python3 -c "from hermes_cli.config import save_env_value; save_env_value('NAME','VAL')"` (.env)
  4. `hermes setup` (guided wizard that calls the above)

**§B — Dots in `model_aliases.<name>` corrupt the entry**
`hermes config set model_aliases.qwen3.7.model qwen3.7-plus` does NOT create
the alias `qwen3.7`. The `_set_nested` helper in `hermes_cli/config.py` treats
`.` as a path separator and produces a nested dict:
```yaml
model_aliases:
  qwen3:
    "7":
      model: qwen3.7-plus
      provider: bailian-token-plan
```
`/model qwen3.7` then can't resolve. Workarounds:
- Use dot-free alias names: `qwen37`, `kimi-k25`, `glm-47`
- Or directly use `/model qwen3.7-plus` (full model_id is accepted at the slash path)

Clean up partial state before retrying:
```bash
hermes config unset model_aliases.qwen3.7 \
  model_aliases.qwen3.7.model model_aliases.qwen3.7.provider
```

**§C — `hermes auth add` pool and `providers.<slug>` are independent**
- `hermes auth add alibaba --label "bailian-token-plan"` writes to `auth.json` under pool key `alibaba`, with the plugin's default base_url.
- A `providers.bailian-token-plan` block is a SEPARATE entity. Runtime credential resolution tries `key_env` first, then inline `api_key`, then matches a pool entry only when the entry's normalized `name` matches the provider slug.
- Net effect: adding a credential via `hermes auth add <x>` does NOT automatically authenticate a custom `providers.<x>` block with the same slug.

**§D — `key_env` is read at request time, .env loaded once at boot**
- `key_env: ALIBABA_TOKEN_PLAN_API_KEY` reads `os.environ[ALIBABA_TOKEN_PLAN_API_KEY]` per request, but `load_env()` (which reads ~/.hermes/.env into the process env) runs only at CLI / desktop-app boot.
- If you edit .env while a Hermes process is alive, that process won't see it until relaunch.
- The desktop app and `hermes chat` are separate processes; edits to .env from a terminal are invisible to the running desktop app until restart.

**§E — "not a recognized config key" warning on `model_aliases.<name>.<field>` is misleading**
The warning fires for any nested key under `model_aliases.` because the
key-registration table doesn't track the schema. The keys ARE written and
`model_switch.py::_load_direct_aliases()` DOES read them. Suppress with
`--force` or ignore.

**§F — Error output shows `Provider: custom` for user-defined providers**
The diagnostic text in API errors reports `Provider: custom` regardless of
the slug you chose. Use this as a signal: "endpoint and model are correct,
issue is auth/key." Combine with raw HTTP test (§A protocol step 1) to confirm.

**§G — Wrong field names → silent drift**
- `providers.<slug>.api_key_env` (with `api_key_env`) is technically accepted (camelCase alias `apiKeyEnv` / snake_case alias), but maps to `key_env` internally. Don't use it — stick with `key_env`.
- `supports_vision`, `display_name`, `api_mode: chat_completions` (vs `openai`) — first two are not in the recognized schema and produce "unknown config keys ignored" warnings. `chat_completions` is the literal default but in practice `openai` is the value that flips the right code path.

**§H — `hermes config set providers.test.x 'hello'` round-trips cleanly**
For sanity-checking, try setting/reading a throwaway key first. `config unset` is idempotent — "Config key not set" is benign.

**§I — `GET /v1/models` is NOT the truth — always live-probe `POST /chat/completions`**
- The `/v1/models` endpoint returns what the gateway *advertises*, which is **not** what your specific subscription is allowed to call. A model can be in the catalog and still 403 for your account (subscription tier restriction).
- Vendor docs ("Personal Plan supports model A, B, C" / "Team Plan supports D, E, F") describe the *platform's* support, not what your individual subscription tier unlocks.
- **Trust HTTP status codes from a real `POST /chat/completions` call**, not the `/v1/models` JSON, not vendor docs:
  - `200` → real, your key works
  - `403` → model exists on the platform but **your subscription tier doesn't include it** (NOT "model doesn't exist")
  - `404` → model literally does not exist on the gateway
- Use `scripts/verify-models.py` to batch-probe a candidate list and bucket them before building `model_aliases:`. Building aliases from docs without probing is how you end up with 11 broken aliases that all 403.

**§J — Don't mis-place a custom key into a built-in provider's auth pool**
- Tempting shortcut: `hermes auth add alibaba --type api-key --label "bailian-token-plan"` to "wire up the key quickly". This writes to `auth.json` under the **built-in** `alibaba` pool slot (with DashScope's default base_url, NOT your token-plan gateway).
- Symptoms: `hermes model` picker shows a duplicate "Qwen Cloud" (= the built-in `alibaba` provider) entry next to your real custom entry. Picking it gets 401/403 because base_url doesn't match.
- Fix: `hermes auth remove <built-in-provider> <index>` to drop the misplaced credential. The custom provider's own `key_env` path is the correct way to authenticate it (Pitfalls §C).
- Rule of thumb: `hermes auth add` is only safe when the slug already has a plugin — for a true custom provider, always go through `key_env` + `.env`.

**§K — Text-only models can see images via `auxiliary.vision` — don't write a Skill**
- If the user has vision-capable and text-only models on the same provider (Token Plan: ***REDACTED***
  ```bash
  hermes config set auxiliary.vision.provider    '<slug>'
  hermes config set auxiliary.vision.model       '<vision-capable-id>'
  hermes config set auxiliary.vision.base_url    '<same-url>'
  hermes config set auxiliary.vision.api_key_env '<env-var>'
  ```
- `agent.image_input_mode: auto` (default) detects non-vision main models and pre-routes the user-attached image through this auxiliary backend; the text-only model only ever sees a text description. Verify with `hermes chat -q '图里有什么?' --image /tmp/test.png -m <text-only-model> -v | grep 'Image analysis completed'`.
- **Don't leave `auxiliary.vision.provider: auto`** — Hermes falls through to OpenRouter / Nous Portal / DeepInfra in that order, which bills against a different subscription and may fail silently. Pin it explicitly.

**§L — Hide a built-in provider from the picker once you've replaced it**
- After onboarding a custom provider that supersedes a built-in (e.g. Token Plan replacing DashScope), the built-in still appears in `hermes model` as long as it has ANY credential in `auth.json` for that pool (even a mismatched one, see §J).
- To silence the built-in:
  ```bash
  hermes config set providers.<builtin-id>.enabled false
  # e.g. hermes config set providers.alibaba.enabled false
  ```
- Order matters: disable first (picker is clean immediately), then `hermes auth remove <builtin-id> <index>` to clean `auth.json`. If you remove first, `hermes auth list` errors out and you can't undo cleanly.

## Decision shortcut — which path to use?

```
Endpoint already has a plugin?       → `hermes auth add <plugin-name>`
OAuth flow needed?                   → `hermes login` / `hermes auth add <x> --type oauth`
OpenAI-compatible + API key + no plugin? → this skill
Vendor uses Anthropic Messages API?  → this skill, set api_mode: anthropic_messages
Vendor uses Codex Responses API?     → this skill, set api_mode: codex_responses
```

## See also

- `references/openai-compatible-providers.md` — full recognized-keys table, camelCase alias mapping, credential resolution order, legacy `custom_providers:***REDACTED***
- `references/token-plan-case-study.md` — full worked example wiring Alibaba Bailian Token Plan (token-plan.cn-beijing.maas.aliyuncs.com) into Hermes; covers `/v1/models` lies, 403-vs-404 diagnosis, alias cleanup, and why `hermes auth add alibaba` was a mis-step.
- `scripts/verify-models.py` — batch-probe a candidate model list against a custom OpenAI-compatible endpoint and bucket the results (200 / 403 / 404) before you commit them to `model_aliases:`. Saves a 401→debug→cleanup loop.
- `templates/providers-block.yaml` — drop-in annotated template for the minimal and the full config.
- Bundled `hermes-agent` skill → `references/providers-and-models.md` — read-only reference for the 35+ shipped provider plugins.
