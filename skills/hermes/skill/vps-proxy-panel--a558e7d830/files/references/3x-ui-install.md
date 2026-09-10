# 3X-UI install + config — verified recipe (v3.6.0, Ubuntu 24.04/noble, AWS Lightsail)

SSH key perms first: `chmod 600 KEY.pem`. Connect as `ubuntu`, use `sudo`.

## 1. System prep
```bash
sudo apt update -y && sudo apt upgrade -y
sudo timedatectl set-timezone Europe/London   # match region
# BBR (often already on in AWS kernels; persist it):
sudo tee /etc/sysctl.d/99-bbr.conf >/dev/null <<'EOF'
net.core.default_qdisc=fq
net.ipv4.tcp_congestion_control=bbr
EOF
sudo sysctl --system
sysctl net.ipv4.tcp_congestion_control   # expect: bbr
```

## 2. Install (NONINTERACTIVE, NO --port)
```bash
curl -Ls -o /tmp/3xui-install.sh https://raw.githubusercontent.com/mhsanaei/3x-ui/master/install.sh
export NONINTERACTIVE=1
sudo -E bash /tmp/3xui-install.sh
```
- `--port 8443` FAILS: installer reads first positional as version → tries to
  download "--port" → curl 404. Set the port AFTER install (step 3).
- Installs Fail2ban + IP-limit jails automatically.
- Prints the `x-ui` subcommand menu when done.

## 3. Read current settings (random port/path/user by default)
```bash
sudo x-ui settings
# or directly:
sudo apt install -y sqlite3
sudo sqlite3 /etc/x-ui/x-ui.db 'SELECT * FROM settings;'
# rows: webPort | webBasePath | secret | panelGuid
sudo sqlite3 /etc/x-ui/x-ui.db 'SELECT id,username FROM users;'
```

## 4. Change port (DB, not the menu)
The `x-ui` interactive menu rejects piped stdin. Edit DB:
```bash
sudo sqlite3 /etc/x-ui/x-ui.db "UPDATE settings SET value='8443' WHERE key='webPort';"
sudo x-ui restart
```

## 5. Set admin username + password (bcrypt — MUST use $2a$)
```bash
# CRITICAL: prefix=b'2a' — the panel's Go backend rejects $2b$ with silent 403
HASH=$(python3 -c "import bcrypt; print(bcrypt.hashpw(b'YOUR_PASSWORD', bcrypt.gensalt(prefix=b'2a')).decode())")
sudo sqlite3 /etc/x-ui/x-ui.db "UPDATE users SET username='admin', password='${HASH}' WHERE id=1;"
sudo x-ui restart
```
(If `import bcrypt` fails: `sudo apt install -y python3-bcrypt`.)

⚠️ **NEVER clear the `secret` row in settings** — it's the session signing key.
Emptying it bricks ALL panel requests (login, API, web UI) with 403.

## 6. Verify
```bash
sudo x-ui settings   # port now 8443
```
Panel URL: `http://SERVER_IP:8443/<webBasePath>/` — log in with admin / YOUR_PASSWORD.

## Firewall (AWS Lightsail — separate from OS)
Open in Lightsail → Networking → Firewall (TCP): 22 (SSH), panel port (e.g. 8443),
node port (e.g. 443 for VLESS-REALITY). OS install does NOT open these.

## Notes
- Panel is HTTP by default (no SSL). SSL via menu option 20 later.
- A "22.04" Lightsail image may actually run a noble/24.04 kernel — trust `uname -a`.
- Panel API login via curl often returns 403 even with correct creds (CSP/session
  issues). Don't debug the API — use direct SQLite for everything.

## 7. Create VLESS-REALITY node (direct DB INSERT)

### Generate keys
```bash
# x25519 keypair (private goes in server config, public goes to clients)
/usr/local/x-ui/bin/xray-linux-amd64 x25519
# Output: PrivateKey: <PRIV>  /  Password (PublicKey): <PUB>

# Client UUID
UUID=$(cat /proc/sys/kernel/random/uuid)

# Short ID (16 hex chars)
SHORT_ID=$(openssl rand -hex 8)
```

### INSERT into inbounds table
```bash
sudo sqlite3 /etc/x-ui/x-ui.db "INSERT INTO inbounds (
  user_id, up, down, total, remark, enable, expiry_time,
  listen, port, protocol, settings, stream_settings, tag, sniffing
) VALUES (
  1, 0, 0, 0, 'vless-reality-443', 1, 0,
  '', 443, 'vless',
  '{\"clients\":[{\"id\":\"${UUID}\",\"flow\":\"xtls-rprx-vision\"}],\"decryption\":\"none\",\"fallbacks\":[]}',
  '{\"network\":\"tcp\",\"security\":\"reality\",\"externalProxy\":[],\"realitySettings\":{\"show\":false,\"xver\":0,\"dest\":\"www.microsoft.com:443\",\"serverNames\":[\"www.microsoft.com\"],\"privateKey\":\"${PRIV_KEY}\",\"minClient\":\"\",\"maxClient\":\"\",\"maxTimediff\":0,\"shortIds\":[\"${SHORT_ID}\"],\"settings\":{\"publicKey\":\"${PUB_KEY}\",\"fingerprint\":\"chrome\",\"serverName\":\"\",\"spiderX\":\"/\"}},\"tcpSettings\":{\"acceptProxyProtocol\":false,\"header\":{\"type\":\"none\"}}}',
  'inbound-443',
  '{\"enabled\":true,\"destOverride\":[\"http\",\"tls\",\"quic\",\"fakedns\"],\"metadataOnly\":false,\"routeOnly\":false}'
);"
sudo x-ui restart
```

### Verify
```bash
sudo ss -tlnp | grep 443   # expect: xray-linux-amd6 listening on *:443
sudo sqlite3 /etc/x-ui/x-ui.db "SELECT id, remark, port, protocol, enable FROM inbounds;"
```

### Build share link
```
vless://UUID@SERVER_IP:443?encryption=none&flow=xtls-rprx-vision&security=reality&sni=www.microsoft.com&fp=chrome&pbk=PUB_KEY&sid=SHORT_ID&spiderx=%2F&type=tcp#vless-reality-443
```

### SNI/dest choices
Good REALITY dest targets (stable, TLS 1.3, H2, no client-cert):
`www.microsoft.com`, `www.samsung.com`, `www.sony.com`, `discord.com`.
Avoid: sites behind Cloudflare (they rotate certs), Google (CAPTCHA on spiderX).
