#!/bin/bash
# xray v24 wrapper for 3X-UI v3.6.0
# Strips the v26-only "tunnel" inbound that x-ui v3.6.0 generates but xray v24 can't parse.
#
# Use when:
#   - x-ui v3.6.0+ is installed (bundles xray v26.7.28 by default)
#   - xray has been downgraded to v24.x (run alongside xray-linux-amd64-real)
#   - you see "unknown config id: tunnel" in xray logs
#
# Usage:
#   sudo cp xray-linux-amd64-real /usr/local/x-ui/bin/
#   sudo chmod +x /usr/local/x-ui/bin/xray-linux-amd64-real
#   sudo cp xray-v24-wrapper.sh /usr/local/x-ui/bin/xray-linux-amd64
#   sudo chmod +x /usr/local/x-ui/bin/xray-linux-amd64
#   sudo systemctl restart x-ui

REAL="/usr/local/x-ui/bin/xray-linux-amd64-real"
ARGS=("$@")

for i in "${!ARGS[@]}"; do
  if [[ "${ARGS[$i]}" == "-config" || "${ARGS[$i]}" == "-c" ]]; then
    CFG="${ARGS[$((i+1))]}"
    if [[ -n "$CFG" && -f "$CFG" ]]; then
      TMP=$(mktemp /tmp/xray-cfg-XXXX.json)
      python3 -c "
import json
with open('$CFG') as f:
    cfg = json.load(f)
if 'inbounds' in cfg:
    cfg['inbounds'] = [ib for ib in cfg['inbounds'] if ib.get('protocol') != 'tunnel']
with open('$TMP', 'w') as f:
    json.dump(cfg, f)
" 2>/dev/null && ARGS[$((i+1))]="$TMP"
    fi
    break
  fi
done

exec "$REAL" "${ARGS[@]}"