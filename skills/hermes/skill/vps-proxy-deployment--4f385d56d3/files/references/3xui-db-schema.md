# 3X-UI v3.6.0 Database Schema Reference

DB: `/etc/x-ui/x-ui.db` (SQLite, requires `sudo`)

## Key Tables

### settings
| id | key | value |
|----|-----|-------|
| 1 | webPort | panel port (string) |
| 2 | webBasePath | URL path e.g. `/FpTqdwEDzw6OrxRxd0/` |
| 3 | secret | session signing key — **NEVER clear** |
| 4 | panelGuid | UUID |

### users
| id | username | password (bcrypt $2a$) | is_admin |

### inbounds
```sql
CREATE TABLE inbounds (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER,
  up INTEGER, down INTEGER, total INTEGER,
  remark TEXT,
  enable NUMERIC,
  expiry_time INTEGER,
  listen TEXT,
  port INTEGER,
  protocol TEXT,          -- 'vless', 'vmess', 'trojan', etc.
  settings TEXT,          -- JSON: decryption, fallbacks (clients IGNORED here in v3.6.0)
  stream_settings TEXT,   -- JSON: network, security, realitySettings, tcpSettings
  tag TEXT UNIQUE,
  sniffing TEXT           -- JSON
);
```

### clients (v3.6.0+ — THIS is where xray reads clients from)
```sql
CREATE TABLE clients (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT NOT NULL UNIQUE,
  uuid TEXT,
  flow TEXT,              -- e.g. 'xtls-rprx-vision'
  enable NUMERIC DEFAULT true,
  total_gb INTEGER,
  expiry_time INTEGER,
  limit_ip INTEGER,
  created_at INTEGER,
  updated_at INTEGER
);
```

### client_inbounds (junction table)
```sql
CREATE TABLE client_inbounds (
  client_id INTEGER,
  inbound_id INTEGER,
  flow_override TEXT,     -- set this if flow differs per-inbound
  created_at INTEGER,
  PRIMARY KEY (client_id, inbound_id)
);
```

## Full Insertion Example (VLESS-REALITY)

```bash
NOW=$(date +%s)000
UUID=$(cat /proc/sys/kernel/random/uuid)

# 1. Insert inbound
sudo sqlite3 /etc/x-ui/x-ui.db "INSERT INTO inbounds
  (user_id, up, down, total, remark, enable, expiry_time, listen, port, protocol,
   settings, stream_settings, tag, sniffing)
VALUES (1, 0, 0, 0, 'vless-reality-443', 1, 0, '', 443, 'vless',
  '{\"decryption\":\"none\",\"fallbacks\":[]}',
  '{\"network\":\"tcp\",\"security\":\"reality\",\"realitySettings\":{\"dest\":\"www.samsung.com:443\",\"serverNames\":[\"www.samsung.com\"],\"privateKey\":\"PRIV_KEY\",\"shortIds\":[\"SHORT_ID\"],\"minClient\":\"\",\"maxClient\":\"\",\"maxTimediff\":0,\"xver\":0,\"show\":false},\"tcpSettings\":{\"acceptProxyProtocol\":false,\"header\":{\"type\":\"none\"}}}',
  'inbound-443',
  '{\"enabled\":true,\"destOverride\":[\"http\",\"tls\",\"quic\",\"fakedns\"],\"metadataOnly\":false,\"routeOnly\":false}');"

INBOUND_ID=$(sudo sqlite3 /etc/x-ui/x-ui.db "SELECT id FROM inbounds WHERE tag='inbound-443';")

# 2. Insert client
sudo sqlite3 /etc/x-ui/x-ui.db "INSERT INTO clients
  (email, uuid, flow, enable, total_gb, expiry_time, limit_ip, created_at, updated_at)
VALUES ('user1', '${UUID}', 'xtls-rprx-vision', 1, 0, 0, 0, ${NOW}, ${NOW});"

CLIENT_ID=$(sudo sqlite3 /etc/x-ui/x-ui.db "SELECT id FROM clients WHERE email='user1';")

# 3. Link client to inbound
sudo sqlite3 /etc/x-ui/x-ui.db "INSERT INTO client_inbounds
  (client_id, inbound_id, flow_override, created_at)
VALUES (${CLIENT_ID}, ${INBOUND_ID}, 'xtls-rprx-vision', ${NOW});"

# 4. Restart and verify
sudo x-ui restart && sleep 3
sudo cat /usr/local/x-ui/bin/config.json | python3 -c "
import json,sys; cfg=json.load(sys.stdin)
for ib in cfg['inbounds']:
    if ib.get('port')==443:
        print('clients:', json.dumps(ib['settings']['clients'], indent=2))
        print('dest:', ib['streamSettings']['realitySettings']['dest'])
"
```

## Panel Login via API

Login requires the correct bcrypt hash AND the secret must be intact.
If login returns 403 with empty body:
1. Check `secret` in settings table is not empty
2. Check password hash uses `$2a$` prefix
3. Fail2ban jails: `3x-ipl` and `sshd` (not x-ui specific)

## xray Config Location

Generated at: `/usr/local/x-ui/bin/config.json`
Regenerated on every `x-ui restart` from DB contents.
