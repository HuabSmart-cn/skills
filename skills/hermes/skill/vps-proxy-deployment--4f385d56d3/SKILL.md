---
name: vps-proxy-deployment
description: "Use when deploying 3X-UI/VLESS-REALITY proxy nodes on VPS."
version: 1
tags: [vps, proxy, 3x-ui, vless, reality, clashmi, mihomo, xray]
triggers:
  - deploy proxy node on VPS
  - install 3x-ui panel
  - create VLESS-REALITY inbound
  - generate ClashMi / mihomo YAML config
  - configure xray reality
  - install WireGuard VPN for VoWiFi
  - add WireGuard alongside proxy
---

# VPS Proxy Node Deployment

Deploy and manage proxy infrastructure (3X-UI panel + VLESS-REALITY nodes) on Linux VPS, and generate client configs.

## Workflow

1. SSH into server (find credentials in user's local files if provided)
   - **SSH key path pitfall**: If the user's local key file lives under a non-ASCII path (e.g. `<LOCAL_PATH>`), copy it to an ASCII path FIRST (`cp -p "ORIG" /tmp/vps_key.pem && chmod 600 /tmp/vps_key.pem`). macOS's SSH client can mangle UTF-8 in key paths and load a zero-byte key, causing silent "Text file busy"-style failures. Symptom: `debug1: no pubkey loaded from <path> type -1`.
2. System prep: update, timezone, BBR
3. Firewall port planning (remind user to open ports in cloud console)
4. Install 3X-UI panel
5. Create VLESS-REALITY inbound
6. Generate client config (ClashMi/mihomo YAML by default for this user)
7. Connectivity test

## 3X-UI Installation

```bash
# Download then execute (avoids curl|bash security blocks)
curl -Ls -o /tmp/3xui-install.sh https://raw.githubusercontent.com/mhsanaei/3x-ui/master/install.sh
export NONINTERACTIVE=1
sudo -E bash /tmp/3xui-install.sh
```

### Pitfalls

- **`--port` flag does NOT work**: the install script interprets it as a version string, causing a 404 download failure. Install with no args, change port after.
- **Interactive menu rejects piped stdin**: `echo '10' | sudo x-ui` fails with "Please enter the correct number". Use `expect` or direct DB edits instead.
- **`x-ui setting -port` is not a valid subcommand** — it just prints the help menu.

## 3X-UI v3.6.0 Database Schema (Critical)

DB path: `/etc/x-ui/x-ui.db` (SQLite). Requires `sudo apt install -y sqlite3`.

### Settings table
```sql
SELECT * FROM settings;
-- key='webPort' → panel port
-- key='webBasePath' → URL path suffix
-- key='secret' → session signing key (NEVER clear this — causes global 403)
```

### Change panel port

**DO NOT edit `/usr/local/x-ui/bin/config.json`** — that's xray's runtime config (regenerated on every x-ui restart from the DB). Panel settings live ONLY in the SQLite `settings` table:

```sql
UPDATE settings SET value='YOUR_PORT' WHERE key='webPort';
-- then: sudo x-ui restart
```

### ⚠️ Client storage (v3.6.0+)

**Clients are NOT read from `inbounds.settings` JSON.** They live in separate tables:

```
clients          → one row per client (uuid, flow, email, enable, ...)
client_inbounds  → junction table linking client_id ↔ inbound_id (+ flow_override)
inbounds         → inbound definition (port, protocol, stream_settings)
```

Inserting clients into `inbounds.settings.clients` JSON is silently ignored when x-ui generates `/usr/local/x-ui/bin/config.json`. You MUST insert into both `clients` and `client_inbounds`.

See `references/3xui-db-schema.md` for full schema and insertion SQL.

### Password hash

Must use `$2a$` prefix (not `$2b$`). Go's bcrypt library may reject `$2b$`:
```python
import bcrypt
h = bcrypt.hashpw(b'YOUR_PASSWORD', bcrypt.gensalt(prefix=b'2a'))
```

## VLESS-REALITY Node Creation

### Generate keys
```bash
/usr/local/x-ui/bin/xray-linux-amd64 x25519
# Returns PrivateKey, PublicKey (labeled "Password"), Hash32
```

### SNI / dest selection

- ❌ `www.microsoft.com` — xray warns: "will increase the likelihood of your server's IP being blocked by the GFW"
- ✅ Good choices: `www.samsung.com`, `www.yahoo.com`, `www.sony.com` — high-traffic CDN-backed sites with valid TLS on port 443
- Rule: pick a site that resolves to a CDN IP near your server's region, supports TLS 1.3, and is not GFW-sensitive

### ⚠️⚠️ xray v26.x REALITY is INCOMPATIBLE with all non-xray clients

**This is the #1 cause of "reality verification failed" / client timeout.**

xray ≥26.3.27 changed the REALITY wire protocol. Non-xray clients (sing-box, mihomo/ClashMi, Hiddify, v2rayNG) ALL fail the handshake. Symptoms:
- Server-side: xray logs show NO errors (connection accepted, then silently dropped)
- Client-side: `reality verification failed` (sing-box) or just timeout (ClashMi/Hiddify)
- VPS self-test (xray-to-xray) succeeds — **misleadingly** confirms "server is fine"
- Setting `minClient` to `1.0.0` does **NOT** fix it — the protocol change is deeper than a version gate

**The ONLY fix: downgrade xray to v24.x** (last version compatible with all clients).

#### Downgrade procedure (x-ui v3.6.0 + xray v24)

x-ui v3.6.0 generates a `tunnel` protocol inbound that xray v24 doesn't understand (`unknown config id: tunnel`). You need a wrapper script:

```bash
# 1. Stop x-ui
sudo systemctl stop x-ui

# 2. Download xray v24.11.21 (last v24 release)
curl -Ls -o /tmp/xray.zip "https://github.com/XTLS/Xray-core/releases/download/v24.11.21/Xray-linux-64.zip"
# unzip may not be installed; use python:
cd /tmp && python3 -c "import zipfile; zipfile.ZipFile('xray.zip').extract('xray','/tmp')"

# 3. Install as the "real" binary
sudo cp /tmp/xray /usr/local/x-ui/bin/xray-linux-amd64-real
sudo chmod +x /usr/local/x-ui/bin/xray-linux-amd64-real
```bash
# 4. Create wrapper that strips tunnel inbounds before launch
# (Or use the verified template at templates/xray-v24-wrapper.sh)
sudo cp templates/xray-v24-wrapper.sh /usr/local/x-ui/bin/xray-linux-amd64
sudo chmod +x /usr/local/x-ui/bin/xray-linux-amd64
```
# 5. Start and verify
sudo systemctl start x-ui && sleep 4
sudo ss -tlnp | grep -E '443|PANEL_PORT'
```

**Why the wrapper?** x-ui regenerates `config.json` from its DB on every restart. Manually editing config.json is futile — x-ui overwrites it. The wrapper intercepts at launch time.

**Cannot replace binary while running**: `cp` fails with "Text file busy". Always `sudo systemctl stop x-ui` first.

**Unzip missing on minimal Ubuntu images**: Run `sudo apt install -y unzip` before extracting xray.zip; otherwise the `unzip` command silently fails. Alternatively use `python3 -c "import zipfile; zipfile.ZipFile('xray.zip').extract('xray','/tmp')"` which works without unzip.

### ⚠️ REALITY config field shape (server + client)

The xray v24 REALITY validator enforces these fields regardless of side:

```json
"realitySettings": {
  "serverNames": ["www.samsung.com"],   // ARRAY (singular "serverName" is wrong)
  "shortIds": ["844527026cbf0153"],     // ARRAY (singular "shortId" is wrong)
  "privateKey": "...",                  // REQUIRED even on CLIENT side (won't be used)
  "dest": "www.samsung.com:443",
  "fingerprint": "chrome",
  "publicKey": "...",
  "xver": 0
}
```

Missing-field startup errors (silent if not in debug mode):
- `empty "serverNames"` → use array form
- `empty "shortIds"` → use array form
- `empty "privateKey"` → add the field even on client (use server's PrivateKey value as placeholder)

**⚠️ Cleanup pitfall**: After the wrapper is in place, there are TWO files:
- `xray-linux-amd64` — the wrapper bash script (small, ~500 bytes)
- `xray-linux-amd64-real` — the actual xray v24 binary (~28MB)

When cleaning up temp/backup files, **NEVER delete `xray-linux-amd64-real`** — it looks like a leftover but is the production binary. Only `.bak.v26` (the old xray v26 backup) is safe to remove. If accidentally deleted, re-download v24.11.21 and restore.

#### Version landscape (as of 2026-07)
- xray v24.11.21 = last v24, compatible with ALL clients
- xray v26.3.27+ = REALITY protocol change, xray-only
- No v25.x exists (jumped from v24 → v26)
- x-ui v3.6.0 bundles xray v26.7.28 by default

### ⚠️ flow_override is required (and silently missing = silent failure)

Inserting `flow='xtls-rprx-vision'` into the `clients` table alone is NOT enough. The flow field only appears in xray's generated config if `client_inbounds.flow_override` is also set:

```sql
UPDATE client_inbounds SET flow_override='xtls-rprx-vision' WHERE client_id=1 AND inbound_id=1;
```

If you forget this:
- TCP/TLS handshake completes normally
- `sing-box` log says `connection download finished` (looks like success)
- But `curl` returns 000 with `SSL_ERROR_SYSCALL` right after `Client hello!`
- REALITY appears to work, x-ui logs show nothing wrong

**Verify after every node creation**: confirm the field is in the generated config:
```bash
sudo cat /usr/local/x-ui/bin/config.json | python3 -c "
import json,sys; cfg=json.load(sys.stdin)
for ib in cfg['inbounds']:
    if ib.get('port')==443:
        for c in ib['settings']['clients']:
            print(c.get('id','?')[:8], 'flow=', c.get('flow','MISSING'))
"
```
If `flow=MISSING`, fix it and `sudo x-ui restart`.

### Panel API login returns 403

Even with correct creds, curl-based login often gets 403 (CSP headers, session-cookie issues). Don't waste time debugging the API — use direct SQLite for ALL config changes.

### Verify after creation
```bash
sudo x-ui restart && sleep 3
# Check xray actually loaded the client:
sudo cat /usr/local/x-ui/bin/config.json | python3 -c "
import json,sys; cfg=json.load(sys.stdin)
ib=[i for i in cfg['inbounds'] if i.get('port')==443][0]
print('clients:', json.dumps(ib['settings']['clients'], indent=2))
print('dest:', ib['streamSettings']['realitySettings']['dest'])
"
# Check port listening:
sudo ss -tlnp | grep 443
```

## Client Config

User's client: **ClashMi** (mihomo/ClashMeta kernel). See `templates/clashmi-vless-reality.yaml`.

Key mihomo fields for VLESS-REALITY:
```yaml
type: vless
flow: xtls-rprx-vision
tls: true
servername: <SNI>          # must match server's serverNames
client-fingerprint: chrome
reality-opts:
  public-key: <PUB_KEY>
  short-id: <SHORT_ID>
```

## User Preferences

- Execute commands directly on the server via SSH — do NOT give copy-paste instructions
- Step-by-step with confirmation between major phases
- ClashMi is the proxy client (not v2rayN/Shadowrocket)
- User may want subscription URL + QR code for mobile import

## Support files

- `references/3xui-db-schema.md` — full SQLite schema for 3X-UI v3.6.0+ and insertion SQL
- `references/multi-node-setup.md` — verified end-to-end UK+US two-VPS setup: subscription YAML, nginx delivery, Mac verification recipe with mihomo binary, OpenWrt PassWall multi-node commands, iOS ClashMi VPN tunnel timeout fix

## Subscription Link (nginx)

Serve the ClashMi YAML over HTTP on port 80 with a random path:
```bash
SUB_PATH=$(openssl rand -hex 12)
sudo mkdir -p /var/www/sub
# Write clash.yaml to /var/www/sub/clash.yaml
# nginx site: location /${SUB_PATH}/clash.yaml { alias /var/www/sub/clash.yaml; }
```
QR code: `python3 -c "import segno; segno.make('URL').save('sub-qrcode.png', scale=5)"` (use `segno`, NOT `qrcode[pil]` — PIL's `_imaging` C extension is frequently broken in venvs on macOS; `segno` is pure-Python and always works).

**Generate TWO QR codes for the user**: (1) the subscription URL (preferred — client auto-fetches updates), AND (2) the static YAML file content as fallback for clients that can't parse userinfo in URLs. The file QR is larger (~1.5KB encoded) but always works. Both should be saved to the user's VPS folder.

### Subscription Basic Auth (recommended)

Protect the subscription from discovery/scanning:
```bash
SUB_USER=$(openssl rand -hex 4)
SUB_PASS=$(openssl rand -hex 8)
sudo apt-get install -y apache2-utils
sudo htpasswd -cb /etc/nginx/.htpasswd "$SUB_USER" "$SUB_PASS"
```

Add to the nginx location block:
```nginx
location /SUB_PATH/clash.yaml {
    auth_basic "Restricted";
    auth_basic_user_file /etc/nginx/.htpasswd;
    alias /var/www/sub/clash.yaml;
    default_type "text/yaml; charset=utf-8";
}
```

Client import URL with auth: `http://USER:PASS@SERVER_IP/SUB_PATH/clash.yaml`
(ClashMi, Hiddify support userinfo in URL.)

**Pitfall**: After first adding auth_basic, must `sudo systemctl restart nginx` (not just reload) — reload sometimes doesn't pick up new htpasswd files. Verify: no-auth → 401, with-auth → 200.

### ⚠️ Subscription password MUST be URL-safe (alphanumeric only)

**This is the #1 cause of "client says update failed" after the first re-deploy.**

When generating `SUB_PASS`, NEVER use the default `openssl rand -base64`. Base64 output contains `+`, `/`, `=` characters. When embedded in a URL like `http://USER:PASS@HOST/path/clash.yaml`, these characters get URL-encoded by some clients (ClashMi in particular) but NOT by others, and ClashMi/Hiddify's URL parser silently truncates at the first non-safe char → 401 Unauthorized → "update failed".

**Symptom**: User updates subscription in ClashMi → error. Manual `curl -u USER:PASS URL` works fine on the VPS, so the server config looks correct. The issue is the CLIENT-side URL parsing, not the server.

**Fix**: Generate passwords with URL-safe character set only:
```bash
SUB_PASS=$(openssl rand -base64 16 | tr -dc 'a-zA-Z0-9' | head -c 16)
# Verify NO special chars: must be all alphanumeric
echo "$SUB_PASS" | grep -qE '^[a-zA-Z0-9]+$' || echo "BAD: regenerate"
```

**Important**: If the password was already deployed and clients fail to update, REGENERATE the password with safe chars and update the URL. You DO NOT know the original password if it was base64-generated — must reset:
```bash
NEW_PASS=$(openssl rand -base64 16 | tr -dc 'a-zA-Z0-9' | head -c 16)
sudo htpasswd -b /etc/nginx/.htpasswd "$SUB_USER" "$NEW_PASS"
# Then update the URL in any QR codes / saved configs
```

**⚠️ NEVER regenerate a working htpasswd to "fix something"** (updated from earlier "Never reset" note — this exact mistake happened in a real session and broke the user's setup): When debugging subscription update failures, DO NOT reset htpasswd password as a first troubleshooting step. The actual cause is almost always:
- URL special-character escaping in the client (see § Subscription password URL-safe below)
- The client cache holding a stale URL

If you DO end up regenerating because the original password is lost, immediately:
***REDACTED***
2. Provide the updated full subscription URL with the new password embedded
3. Verify the new URL works from Mac (`curl -u NEW_USER:NEW_PASS URL`) BEFORE telling user to update client

If you lose the original htpasswd password and don't know it (e.g., it was generated in a previous session you don't have context for):
***REDACTED***
# Don't blow it away. Read the existing one first:
sudo cat /etc/nginx/.htpasswd     # captures current value
# User has the working URL in their client. If you reset, the client's saved URL breaks silently.
```

The pattern that caused real breakage: `sudo htpasswd -b /etc/nginx/.htpasswd USER NEW_PASS` overwrote a working password, the user's saved subscription URL no longer worked, they got "update failed", and the cause was invisible to them. Always **add the URL-safe pitfall check** before resetting.

**Bonus**: When writing ClashMi subscription YAML with multiple nodes, avoid emoji in node/group names. Some clients (Hiddify on Android) display them as garbled characters or reject the YAML. Use plain ASCII names like `UK-London`, `US-Oregon`, `PROXY`, `AUTO`, `DIRECT`.

## Multi-node (multi-region) subscription merge

When adding a second (or third) VPS, the user typically wants **all nodes in ONE subscription** so ClashMi/Hiddify picks them up with a single "update subscription" action.

**Workflow**:
1. Generate credentials for new VPS (independent UUID/privateKey from existing)
2. SSH to ONE existing VPS that hosts the subscription (or pick the most stable one)
3. Edit `/var/www/sub/clash.yaml` to append the new proxy block
4. Add new proxy name to the `proxies:` array of any `select` / `url-test` proxy-groups
5. nginx serves the updated file immediately — no restart needed (nginx doesn't cache static files)
6. Tell the user to "update subscription" in their client — done

**Don't**: Create a second subscription URL just to host the new node. Single subscription is operationally simpler; client config stays the same forever (just refresh).

**Reference template**: `templates/clashmi-vless-reality.yaml` shows the canonical structure. Append additional `- name: ... type: vless ...` entries to the `proxies:` section.

When user has multiple VPS in different regions (e.g. London + US-West) and wants to switch between them:

- **One 3X-UI panel per VPS** (don't try to manage both from one panel — adds complexity for no benefit)
- Each VPS runs the full standalone procedure above (install 3x-ui, downgrade xray v24, VLESS-REALITY 443, panel HTTPS, subscription)
- **Generate credentials independently per VPS** — DO NOT reuse UUID/privateKey across nodes (security isolation)
- **Subscription workflow**: easiest path is a SECOND mihomo proxy entry in the user's ClashMi YAML with the same flow/fingerprint/SNI. The user picks the active node in mihomo's UI or via proxy-groups rules (`GEOIP,CN,DIRECT + MATCH,PROXY` with a select group of both nodes).
- **PassWall on OpenWrt**: add a second `nodes` UCI section, then `tcp_node='@nodes[N]'`. UI: 访问控制 → TCP 节点 → 主节点下拉切换。

For a reusable OpenWrt-specific multi-node setup, see `references/openwrt-multi-node.md` once added.

## Post-Deployment Hardening

### Panel HTTPS (nginx self-signed reverse proxy)

3X-UI panel runs HTTP internally. Add an HTTPS reverse proxy on a separate port:
```bash
# Self-signed cert (10 years)
sudo openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
  -keyout /etc/nginx/panel.key -out /etc/nginx/panel.crt \
  -subj '/CN=SERVER_IP'
```

nginx site (`/etc/nginx/sites-available/panel`):
```nginx
server {
    listen 19910 ssl;
    server_name _;
    ssl_certificate /etc/nginx/panel.crt;
    ssl_certificate_key /etc/nginx/panel.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    location / {
        proxy_pass http://127.0.0.1:PANEL_PORT;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```
Enable: `sudo ln -sf /etc/nginx/sites-available/panel /etc/nginx/sites-enabled/panel && sudo nginx -t && sudo systemctl reload nginx`

Access: `https://SERVER_IP:19910/WEB_BASE_PATH/` (browser warns about self-signed — expected).
Old HTTP panel port can be removed from cloud firewall once HTTPS confirmed.

### Hardening checklist (suggest to user after deployment)
- [ ] Subscription Basic Auth (above)
- [ ] Panel HTTPS (above)
- [ ] UFW: `sudo ufw allow 22,80,443,19910/tcp && sudo ufw enable`
- [ ] SSH: disable password auth (`PasswordAuthentication no`)
- [ ] `unattended-upgrades` for auto security patches
- [ ] Log rotation for xray access logs
- [ ] Backup node on alternate port/SNI for redundancy

## Client "Broadcast IP" / Fake-IP Confusion

When user reports seeing "broadcast IP" or weird IP in speed tests:
- mihomo's `enhanced-mode: fake-ip` with `fake-ip-range: 198.18.0.1/16` returns virtual IPs for DNS queries
- `198.18.0.0/15` is IANA-reserved for benchmarking — some tools mislabel it as "broadcast"
- This is NORMAL and does NOT mean the proxy is broken
- Verify real exit IP: browser → https://ip.sb (should show VPS IP)
- If user is bothered: switch `enhanced-mode` from `fake-ip` to `redir-host` in DNS config

## WireGuard VPN (alongside VLESS-REALITY)

Use case: VoWiFi (WiFi Calling) requires a system-level VPN tunnel (IPsec/IKEv2). VLESS-REALITY is application-layer and CANNOT carry VoWiFi. WireGuard is network-layer and CAN. Deploy both; user switches between them.

### Coexistence

| Service | Protocol | Port | Use |
|---|---|---|---|
| VLESS-REALITY | TCP | 443 | Daily proxy/browsing |
| WireGuard | UDP | non-default (e.g. 48217) | VoWiFi / system-level VPN |

They don't conflict (different protocols/ports). **Client must NOT run both simultaneously** — WireGuard captures all traffic at network layer, making the proxy client redundant and causing double-encapsulation slowdown.

**⚠️ User requires non-default ports.** Never use 51820 (WireGuard default) — user explicitly rejects default ports for security. Pick a random high port (e.g. 48217) and update server config, client config, AND QR code together.

### Install & configure

```bash
sudo apt-get install -y wireguard

# Generate keys
SERVER_PRIV=$(wg genkey)
SERVER_PUB=$(echo "$SERVER_PRIV" | wg pubkey)
CLIENT_PRIV=$(wg genkey)
CLIENT_PUB=$(echo "$CLIENT_PRIV" | wg pubkey)
CLIENT_PSK=$(wg genpsk)

# Server config
sudo tee /etc/wireguard/wg0.conf > /dev/null << EOF
[Interface]
Address = 10.8.0.1/24
ListenPort = 51820
PrivateKey = $SERVER_PRIV
PostUp = iptables -A FORWARD -i wg0 -j ACCEPT; iptables -t nat -A POSTROUTING -o ens5 -j MASQUERADE
PostDown = iptables -D FORWARD -i wg0 -j ACCEPT; iptables -t nat -D POSTROUTING -o ens5 -j MASQUERADE

[Peer]
PublicKey = $CLIENT_PUB
PresharedKey = $CLIENT_PSK
AllowedIPs = 10.8.0.2/32
EOF
sudo chmod 600 /etc/wireguard/wg0.conf

# Enable IP forwarding + start
echo 'net.ipv4.ip_forward=1' | sudo tee /etc/sysctl.d/99-wireguard.conf
sudo sysctl -p /etc/sysctl.d/99-wireguard.conf
sudo systemctl enable --now wg-quick@wg0
sudo wg show  # verify
```

**Note**: The NAT interface name (`ens5`) varies — check with `ip route | grep default` on the VPS.

### Client config (mobile)

```ini
[Interface]
PrivateKey = CLIENT_PRIV
Address = 10.8.0.2/32
DNS = 8.8.8.8, 1.1.1.1

[Peer]
PublicKey = SERVER_PUB
PresharedKey = CLIENT_PSK
Endpoint = SERVER_IP:51820
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
```

Generate QR for mobile import: `python3 -c "import segno; segno.make(open('wg-client.conf').read()).save('wg-qrcode.png', scale=5)"`

### Firewall

Cloud firewall must allow **UDP 51820** (not TCP). Remind user explicitly — most people default to TCP.

### VoWiFi caveats

- Some carriers (China Mobile/Unicom/Telecom) check IP geolocation for VoWiFi registration — a foreign VPS IP may be rejected. Only testing confirms.
- If VoWiFi fails over WireGuard, it's a carrier policy issue, not a config issue.

## Connectivity Debugging

### Diagnostic order (follow this sequence)
1. Server self-test (xray-to-xray on VPS) → confirms server config is valid
2. **Local sing-box test from user's Mac** → isolates protocol vs network issues
3. Network-level checks (TCP, TLS, ICMP)
4. Client app checks (ClashMi/Hiddify config)

**Critical insight**: Step 1 succeeding does NOT mean clients will work. xray v26 self-test passes but ALL non-xray clients fail (see § xray v26 incompatibility above). Always do step 2 before concluding "server is fine".

### Server-side self-test
When client reports timeout, test from the VPS itself using the xray binary already installed:
```bash
# Write a client config pointing to 127.0.0.1:443 with the same credentials
# Run: timeout 10 /usr/local/x-ui/bin/xray-linux-amd64 -c /tmp/xray-client.json
# Then: curl -x socks5://127.0.0.1:1080 http://www.google.com
```
If this succeeds (HTTP 200), the server config is internally consistent — but may still be incompatible with non-xray clients.

**⚠️ Pitfall with self-test**: Writing the test client config via `ssh ... 'cat > /tmp/x.json << EOF'` often mangles JSON (heredoc + SSH quoting + bash parsing). Common failures:
- "empty 'serverNames'" → typo'd `realitySetings` (missing t) or used singular `serverName`
- "empty 'shortIds'" → used singular `shortId`
- "empty 'privateKey'" → required on client side too (use server's PrivateKey as placeholder)
- "invalid character 'i'" → heredoc got truncated, missing leading `{`

**Reliable pattern**: Write the JSON locally with Python's `json.dump`, then `scp` it to the VPS. Always use array forms (`serverNames`, `shortIds`) and include `privateKey` even on the client side.

**Even more reliable**: Skip the server-side self-test entirely. If panel + 443 + nginx are all responding correctly and the wrapper is in place, just tell the user to test with their actual ClashMi/Hiddify. Self-test adds time and has its own failure modes that don't reflect the real deployment.

**Also broken**: SSH port-forward + curl + SOCKS5 combinations give confusing `SSL_ERROR_SYSCALL` errors that don't reliably diagnose anything. The TLS layer in this chain (curl → SSH tunnel → xray SOCKS → VLESS REALITY → xray server → upstream TLS) has too many hops. If you need to verify from outside the VPS, use a real client.

### Local sing-box test (definitive for protocol compatibility)
Download sing-box to the user's Mac (GitHub direct often times out from China; use mirror or download on VPS then SCP):
```bash
# Download via GitHub mirror (from China):
curl -Ls -o /tmp/sing-box.tar.gz "https://ghfast.top/https://github.com/SagerNet/sing-box/releases/download/v1.13.15/sing-box-1.13.15-darwin-arm64.tar.gz"
# Or download on VPS (fast) then SCP back
```

### Local mihomo test (when user's actual client is ClashMi/mihomo)

**For this user, the actual production client is ClashMi (mihomo kernel).** Testing with the SAME kernel that they'll use in production eliminates an entire class of "works in sing-box but fails in ClashMi" issues. Mihomo binary download is faster and smaller than sing-box.

```bash
# Download mihomo binary (arm64 for Apple Silicon, amd64 for Intel Macs)
curl -sL -o /tmp/mihomo.gz "https://github.com/MetaCubeX/mihomo/releases/download/v1.19.10/mihomo-darwin-arm64-go120-v1.19.10.gz"
gunzip -f /tmp/mihomo.gz && chmod +x /tmp/mihomo && /tmp/mihomo -v
# → "Mihomo Meta v1.19.10 darwin arm64 with go1.20.14 ..."
```

Write the EXACT ClashMi subscription YAML to a test config (modify `port`/`socks-port` if 7890/7891 are taken by a running ClashMi instance — common on dev machines):
```bash
/tmp/mihomo -d /tmp/mihomo_test -f /tmp/test_clash.yaml -t   # validate config only
```
Run in background, then test:
```bash
curl -x http://127.0.0.1:7892 https://www.google.com -o /dev/null -w '%{http_code}\n'  # → 200
curl -x http://127.0.0.1:7892 https://ip.sb                      # → real VPS exit IP
```

**Debug log mode reveals REALITY failures**: add `log-level: debug` to config. Look for:
- `XTLS Vision found TLS 1.3 ...` + `REALITY Authentication: true` = working
- `REALITY Authentication: false` = wrong public_key, short_id, or serverNames
- No "REALITY Authentication" line = TCP didn't reach xray (firewall / port)

**Stopping mihomo**: `pkill -f 'mihomo.*test_clash'` (background process; won't die on terminal close).

Minimal sing-box VLESS-REALITY client config (`test-vless.json`):
```json
{
  "log": {"level": "debug"},
  "inbounds": [{"type": "mixed", "listen": "127.0.0.1", "listen_port": 2080}],
  "outbounds": [{
    "type": "vless",
    "server": "SERVER_IP", "server_port": 443,
    "uuid": "UUID", "flow": "xtls-rprx-vision",
    "tls": {
      "enabled": true, "server_name": "SNI",
      "utls": {"enabled": true, "fingerprint": "chrome"},
      "reality": {"enabled": true, "public_key": "PUBKEY", "short_id": "SHORTID"}
    }
  }]
}
```
Run: `sing-box run -c test-vless.json` (background), then `curl -x http://127.0.0.1:2080 http://www.google.com`.

- `reality verification failed` in sing-box logs = **xray v26 protocol incompatibility** → downgrade server xray
- Connection timeout = network/firewall issue
- HTTP 200 = server fully working, problem is in the client app config

### Client-side checks
- ClashMi displays `vless/xudp` even with `network: tcp` — this is mihomo labeling, not necessarily wrong
- mihomo kernel must be ≥1.18.0 for full REALITY + xtls-rprx-vision support
- Verify the user imported the LATEST config (SNI changes require re-import)

### Network-level checks
- AWS Lightsail blocks ICMP by default — ping failure ≠ IP blocked
- TCP connectivity: `nc -zv -w 5 SERVER_IP 443`
- REALITY handshake: `echo | openssl s_client -connect SERVER_IP:443 -servername SNI` — should return the dest site's cert
- TLS handshake from China taking 3-4s is normal for AWS London (high latency)
- If TCP connects but VLESS fails from China: possible DPI interference on 443; try a non-standard port
