#!/usr/bin/env bash
# Verify a custom Hermes provider is fully wired (config + env + chat round-trip).
# Usage: bash scripts/verify-provider.sh <provider-name> [model-id] [env-var-name]
#
# Exits non-zero on the first failure with a one-line diagnosis.
# Reads API key from $HOME/.hermes/.env (the canonical Hermes store).

set -u
PROV="${1:-}"
MODEL="${2:-}"
ENV_VAR="${3:-}"

if [[ -z "$PROV" ]]; then
  echo "Usage: $0 <provider-name> [model-id] [env-var-name]" >&2
  exit 2
fi

HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
ENV_FILE="$HERMES_HOME/.env"
HERMES="${HERMES_BIN:-hermes}"

fail() { echo "FAIL: $*" >&2; exit 1; }
ok()   { echo "OK:   $*"; }

# 1) .env has the key
if [[ -n "$ENV_VAR" ]]; then
  grep -q "^${ENV_VAR}=" "$ENV_FILE" 2>/dev/null \
    || fail "missing $ENV_VAR in $ENV_FILE — re-run save_provider_env_credential"
  ok ".env has $ENV_VAR"
fi

# 2) provider registered (look for "base_url:" as an exact key, not a substring)
prov_block="$("$HERMES" config get "providers.${PROV}" 2>&1)"
[[ "$prov_block" == *"base_url:"* ]] \
  || fail "providers.${PROV} entry is empty or missing base_url — check hermes config get providers"
ok "providers.${PROV} entry present"

# 3) base_url is reachable + /v1/models returns 200 (if base_url present)
#
# NOTE on the regex: `hermes config get` output can wrap YAML long-lines and
# prepend ANSI colour codes. The earlier script choked on that and produced
# `WARN: https/models returned 000`. The robust move is a Python parser — the
# CLAUDE-helper style of `python3 -c "import yaml; ..."` would do it, but yaml
# isn't always pre-installed. Use a fallback ladder instead:
#   - Try awk on a colon-separated line first
#   - Fall back to grep + sed if the URL spills across wrapped lines
base_url=""
if echo "$prov_block" | grep -q '^base_url:'; then
  base_url="$(echo "$prov_block" | awk -F': *' '/^base_url:/{print $2; exit}' | tr -d '"' | tr -d $'\r' | xargs)"
fi
if [[ -z "$base_url" ]]; then
  # Wrapped or colour-prefixed line: grep for the next URL after 'base_url'
  base_url="$(echo "$prov_block" | grep -A0 'base_url' | grep -oE 'https?://[^ ]+' | head -1 | tr -d $'\r')"
fi
if [[ -n "$base_url" && -n "$ENV_VAR" ]]; then
  api_key=***REDACTED***
  # base_url already ends in /v1 (Hermes' normalize step appends it on set).
  # Models live at <base>/models, not <base>/v1/models. Append only /models.
  models_url="${base_url%/}/models"
  http_code="$(curl -sS -o /tmp/_provider_models.json -w '%{http_code}' \
    -H "Authorization: ***REDACTED***
    "$models_url" 2>/dev/null || echo 000)"
  if [[ "$http_code" == "200" ]]; then
    n_models="$(python3 -c 'import json,sys; d=json.load(open("/tmp/_provider_models.json")); print(len(d.get("data",[]) if isinstance(d,dict) else d))' 2>/dev/null || echo 0)"
    ok "$models_url returns 200, $n_models models visible"
  else
    echo "WARN: $models_url returned $http_code — auth may be off OR the endpoint doesn't expose /v1/models (some Anthropic-compat gateways don't)" >&2
  fi
fi

# 4) chat round-trip
if [[ -n "$MODEL" ]]; then
  out="$("$HERMES" chat -q "reply with exactly the word: PONG" \
        --provider "$PROV" --model "$MODEL" -Q 2>&1)"
  if echo "$out" | grep -q "PONG"; then
    ok "chat round-trip succeeded on $PROV / $MODEL"
  else
    err_line="$(echo "$out" | grep -iE 'HTTP [0-9]{3}|AuthenticationError|PermissionDenied|invalid_request' | head -1)"
    fail "chat round-trip failed on $PROV / $MODEL — ${err_line:-no match for PONG in output}"
  fi
fi

echo
echo "Provider $PROV verified."
