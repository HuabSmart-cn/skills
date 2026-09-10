#!/usr/bin/env bash
# check-desktop-picker.sh — verify a custom provider is wired up for the
# desktop Hermes.app picker (not just the CLI runtime).
#
# The CLI runtime (`hermes chat`) is satisfied by:
#   - providers.<slug> in config.yaml
#   - BAILIAN_TOKEN_PLAN_API_KEY=***REDACTED***
# The desktop picker additionally requires:
#   - A credential in ~/.hermes/auth.json.credential_pool.<slug>
#   - That entry's base_url matching providers.<slug>.base_url (otherwise
#     the picker would silently route through a wrong endpoint)
#
# Run after `hermes auth add <slug>` to catch the silent-base-URL-drift
# footgun before the user relaunches Hermes.app to find out.
#
# Usage:
#   bash check-desktop-picker.sh <provider-slug>
#
# Exits 0 if both checks pass, 1 otherwise. Prints the diff otherwise.

set -u
SLUG="${1:-}"

if [[ -z "$SLUG" ]]; then
  echo "Usage: $0 <provider-slug>" >&2
  exit 2
fi

HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
ENV_FILE="$HERMES_HOME/.env"
AUTH_FILE="$HERMES_HOME/auth.json"
HERMES="${HERMES_BIN:-hermes}"

fail() { echo "FAIL: $*" >&2; exit 1; }
ok()   { echo "OK:   $*"; }

# ----- Check 1: pool entry exists for <slug> -----

if command -v jq >/dev/null 2>&1; then
  HAS_POOL=$(jq -r --arg s "$SLUG" '.credential_pool[$s] // [] | length' "$AUTH_FILE" 2>/dev/null)
else
  HAS_POOL=$(/usr/bin/python3 -c "
import json, sys
try:
    with open('$AUTH_FILE') as f: d = json.load(f)
    print(len(d.get('credential_pool', {}).get('$SLUG', [])))
except Exception: print(0)
")
fi

if [[ -z "$HAS_POOL" || "$HAS_POOL" -eq 0 ]]; then
  echo "WARN: no credential_pool[$SLUG] entry in $AUTH_FILE"
  echo "      Run: hermes auth add $SLUG --type api_key --api-key <key> --label '<label>'"
  echo "      Then re-run this script + click the 'Refresh Models' button in Hermes.app"
  exit 1
fi
ok "credential_pool.$SLUG has $HAS_POOL entry(ies)"

# ----- Check 2: pool entry's base_url matches providers.<slug>.base_url -----

EXPECTED_BASE=$("$HERMES" config get "providers.${SLUG}.base_url" 2>/dev/null \
                 | sed -E 's/^base_url:[[:space:]]*//' \
                 | tr -d '"' \
                 | xargs)

if [[ -z "$EXPECTED_BASE" ]]; then
  echo "WARN: providers.${SLUG}.base_url is empty in config.yaml"
  echo "      Set it with: hermes config set providers.${SLUG}.base_url '<your-base-url>'"
  exit 1
fi

if command -v jq >/dev/null 2>&1; then
  ACTIVE_BASE=$(jq -r --arg s "$SLUG" '.credential_pool[$s][0].base_url // ""' "$AUTH_FILE" 2>/dev/null)
else
  ACTIVE_BASE=$(/usr/bin/python3 -c "
import json
with open('$AUTH_FILE') as f: d = json.load(f)
pool = d.get('credential_pool', {}).get('$SLUG', [])
print(pool[0].get('base_url', '') if pool else '')
")
fi

if [[ -z "$ACTIVE_BASE" ]]; then
  echo "WARN: credential_pool.$SLUG[0].base_url is empty (older auth entries have no base_url)"
  echo "      Should match: $EXPECTED_BASE"
  echo "      Run: hermes auth remove $SLUG 0 && re-add with --inference-url <url> if needed"
  exit 1
fi

# Strip trailing slashes for comparison
A="${EXPECTED_BASE%/}"
B="${ACTIVE_BASE%/}"
if [[ "$A" != "$B" ]]; then
  echo "FAIL: base_url drift detected."
  echo "  providers.${SLUG}.base_url       = $EXPECTED_BASE"
  echo "  credential_pool.$SLUG[0].base_url = ***REDACTED***
  echo "  Fix: hermes auth remove $SLUG 0 && re-add, or edit $AUTH_FILE while unlocked"
  exit 1
fi
ok "base_url aligned: $A"

# ----- Check 3: a real catalog probe (best-effort, only if env has the key) -----

ENV_VAR=$("$HERMES" config get "providers.${SLUG}.key_env" 2>/dev/null \
         | sed -E 's/^key_env:[[:space:]]*//' \
         | tr -d '"' \
         | xargs)

if [[ -n "$ENV_VAR" ]] && grep -q "^${ENV_VAR}=" "$ENV_FILE" 2>/dev/null; then
  API_KEY=***REDACTED***
  CODE=$(curl -sS -o /tmp/_picker_models.json -w '%{http_code}' \
    -H "Authorization: ***REDACTED***
    "${A}/models" 2>/dev/null || echo 000)
  if [[ "$CODE" == "200" ]]; then
    N=$(python3 -c "import json; print(len(json.load(open('/tmp/_picker_models.json')).get('data',[])))" 2>/dev/null || echo 0)
    ok "live catalog probe OK ($N models at $A/models)"
  else
    echo "WARN: live probe returned HTTP $CODE — auth may be off, OR endpoint shape differs"
  fi
else
  echo "skip live probe: $ENV_VAR not present in $ENV_FILE"
fi

echo
echo "Provider $SLUG should now appear in Hermes.app's model picker."
echo "If it doesn't: open Hermes.app → click the model pill → click 'Refresh Models'."
echo "If still missing after refresh, fully quit and relaunch Hermes.app."
