# Alibaba Bailian (百炼) Token Plan — Provider Reference

Verified against `https://platform.qianwenai.com/docs/token-plan/` on 2026-07-31. Re-check the live catalog (and `pricing/token-plan`) before onboarding a new account — model lists and pricing tiers change.

## What "Token Plan" actually is

A subscription product on Alibaba Cloud's Bailian (百炼) Model Studio. **It is a separate endpoint family from regular DashScope API access.** The two are quote-unquote "completely isolated":

- Token Plan key prefix: ***REDACTED***
- DashScope pay-as-you-go key prefix: `sk-ws-…` (regular Pay-As-You-Go)

Mixing the key against the wrong base URL returns `401 invalid_api_key` even when the key is otherwise valid.

## Endpoints

The Token Plan web console exposes both protocols. Pick one — do not dual-register unless the user specifically needs both:

***REDACTED***
|---|---|---|
| OpenAI compatible | `https://token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1` | `openai` |
| Anthropic compatible | `https://token-plan.cn-beijing.maas.aliyuncs.com/apps/anthropic` | `anthropic` |

Region is **`cn-beijing`** for the China-mainland deployment. Other regions (e.g. Singapore) have different hostnames — verify in the user's subscription page first if you see `401 geographic_restriction` errors.

## Subscription tiers and what they unlock

Three tiers (Lite / Standard / Pro) plus an optional top-up (加油包). Two limit windows apply: **5-hour rolling** and **7-day rolling**. Either hitting its cap pauses the subscription until reset / top-up.

Pricing tier affects **quotas, not model list** — at least within the same plan family. The published "supported models" list is the same for Lite/Standard/Pro; access to the **preview-tier** `qwen3.8-max-preview` is a special promotional period and may be removed without notice. If a model the user expects is not in the catalog (`/v1/models`), it's almost always because their account is on a different subscription, not a different tier.

## Live catalog (as of 2026-07-31) — 9 models

Verified live by `curl https://token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1/models` with the user's API key:

| `id` (exact, case-sensitive) | Type | Has vision? |
|---|---|---|
| `qwen3.8-max-preview` | text (preview) | **yes** |
| `qwen3.7-max` | text | no |
| `qwen3.7-plus` | text | **yes** |
| `qwen3.6-flash` | text | **yes** |
| `glm-5.2` | text | no |
| `deepseek-v4-pro` | text | no |
| `wan2.7-image` | image generation | n/a (image gen) |
| `wan2.7-image-pro` | image generation | n/a (image gen) |
| `qwen-audio-3.0-tts-plus` | TTS | n/a |

Models commonly referenced in older docs but **NOT on this plan** (the docs are versioned snapshots from months ago):
- `kimi-k2.5` — belongs to Moonshot; was on earlier Token Plan catalogs but not current
- `qwen3.6-plus` / `qwen3.5-plus` — older product names; replaced by `qwen3.7-plus` etc.
- `glm-5` / `glm-4.7` — replaced by `glm-5.2`
- `MiniMax-M2.5` / `MiniMax-M3` etc — Mistral family on DashScope, not on Token Plan

If a model id from older docs is 404ing, check the live catalog first — it's almost certainly been renamed rather than removed.

## What's special about the preview tier

`qwen3.8-max-preview` carries these notes from the docs:
1. **Preview** — model behaviour will iterate; treat outputs as not-API-stable
2. **10× credit bonus** during the launch promo (consumption is 1/10 normal until promo ends)
3. **Overnight extra discount** — calls between 22:00 and 08:00 China time get an additional 80% off (so 2% of base during the promo window)

None of this affects the wire format. Just be aware that credit usage counters in dashboards may look weirdly low for preview-tier calls.

## What you DON'T do — anti-patterns observed

- **Don't use `hermes auth add alibaba`** for a Token Plan key. It writes the credential into the built-in Alibaba provider's pool with the regular DashScope base URL (`dashscope-intl.aliyuncs.com`), so the lookup chain in `runtime_provider.py:***REDACTED***

- **Don't paste the key with `echo >> ~/.hermes/.env`** — terminal daemons block this as a credential-write safety guard. The block surfaces as a fake timeout, not a permission error, and is easy to misread. Use the programmatic path:

  ***REDACTED***
  <LOCAL_PATH> -c '
  from hermes_cli.credential_lifecycle import save_provider_env_credential
  print(save_provider_env_credential("ALIBABA_TOKEN_PLAN_API_KEY", "<the-key>"))
  '
  ```

- **Don't trust the generic add-vision-skill.md doc verbatim for the model list.** That doc is a Claude Code / OpenCode recipe with a generic model catalogue. The plan-specific live `/v1/models` output is authoritative.

- **Don't try to dual-write secrets to both `~/.hermes/.env` and `~/.hermes/auth.json`** for normal CLI-only use. Two sources of truth leads to drift and surprise logins. Pick one canonical store.

  **Exception — when the desktop `Hermes.app` picker needs the provider visible, the two stores do legitimately coexist.** The .env is still the secret source of truth (use `save_provider_env_credential` to write it); `auth.json.credential_pool.<slug>` is a cache the desktop picker's `model.options` RPC reads from. Keep their values aligned. `~/.hermes/skills/autonomous-ai-agents/llm-provider-onboarding/scripts/check-desktop-picker.sh` checks both entries have matching `base_url` and exits non-zero if they drift.

## Useful curl recipes (for verification, not for normal use)

```bash
KEY='sk-sp-…'
BASE='https://token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1'

# Catalog
curl -sS "$BASE/models" -H "Authorization: ***REDACTED***

# Single-shot chat
curl -sS "$BASE/chat/completions" \
  -H "Authorization: ***REDACTED***
  -H "Content-Type: application/json" \
  -d '{"model":"qwen3.7-plus","messages":[{"role":"user","content":"PONG"}],"max_tokens":10}'
```

For image generation models (`wan2.7-image` family), the `/v1/images/generations` endpoint takes `{ "model": ..., "prompt": ..., "size": "1024x1024", "n": 1 }` — same auth header, same token-plan base URL.

## Desktop `Hermes.app` integration (verified 2026-07 v0.19.1)

The desktop model's picker is wired to `~/.hermes/auth.json.credential_pool.<slug>`, not to `providers.<slug>` in config.yaml. Even though `hermes chat -q` succeeds after only the §1–§3 config set in the parent SKILL.md, the model pill in the chat composer won't show "Alibaba Bailian Token Plan" until a credential is also in `auth.json`. The relevant desktop code path is `apps/desktop/src/components/model-picker.tsx` line ~184:

***REDACTED***
const configured = providers.filter(p => (p.models ?? []).length > 0)
```

That `providers[]` comes from the gateway's `model.options` RPC, which only includes providers that have credentials in `auth.json`. Three minimal extra steps after the standard provider registration:

***REDACTED***
hermes auth add bailian-token-plan \
  --type api_key \
  --api-key "$BAILIAN_TOKEN_PLAN_API_KEY" \
  --label 'Bailian Token Plan (personal)'
bash ~/.hermes/skills/autonomous-ai-agents/llm-provider-onboarding/scripts/check-desktop-picker.sh bailian-token-plan
# Then in Hermes.app: click the model pill → click "Refresh Models" / "刷新模型"
```

Caveats specific to Token Plan:

***REDACTED***
- The Bash check script handles drift between those two; if it warns, `hermes auth remove bailian-token-plan <index>` and re-add.
- The picker caches for ~1h; "Refresh Models" busts it. If still missing after refresh, quit and relaunch `Hermes.app`.
- The 3 `happyhorse-*` video models listed in the personal-overview docs are NOT on `/v1/models` for this plan — they need separate Alibaba image2video / text2video endpoints, not a chat-completions alias. Out of scope here.

## Documentation sources cited in this reference

- `https://platform.qianwenai.com/docs/developer-guides/clients-and-developer-tools/hermes-agent.md` — official "接入 Hermes Agent" guide. Worth reading because it's the one doc that explicitly tells users to point Custom Endpoint at `/compatible-mode/v1` (not `/apps/anthropic`) when adding a non-built-in provider to the **desktop** app.
- `https://platform.qianwenai.com/docs/token-plan/personal/token-plan-personal-overview.md` — authoritative model list. Cross-check against `/v1/models`, not against this prose.
- `https://platform.qianwenai.com/docs/token-plan/personal/token-plan-personal-quickstart.md` — base URLs and key format (`sk-sp-` vs `sk-ws-` isolation warning).
- `https://platform.qianwenai.com/docs/token-plan/best-practices/add-vision-skill.md` — the "vision as Skill" recipe. Treat as illustrative for Claude Code / OpenCode only; on Hermes, vision falls back automatically via `agent.image_input_mode: auto` + `auxiliary.vision`.
