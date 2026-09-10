# OpenWrt / Kwrt PassWall — adding a second VLESS-REALITY node

When the user already has one PassWall VLESS-REALITY node configured on the
OpenWrt/Kwrt side router and wants to add a second region (e.g. UK → US),
follow this procedure. Tested on Kwrt 24.10-SNAPSHOT with luci-app-passwall
25.6.1 + xray 25.5.16.

## UCI: how PassWall stores nodes

Config file: `/etc/config/passwall`. Nodes live in a typed UCI section:

```
config nodes
    option uuid '<UUID>'
    option address '<server_ip>'
    option port '443'
    option protocol 'vless'
    option flow 'xtls-rprx-vision'
    option transport 'tcp'
    option tls '1'
    option reality '1'                    # NOT 'tls=reality' — that's wrong
    option tls_serverName '<SNI>'        # NOT 'sni=' — that's wrong
    option reality_fingerprint 'chrome'
    option reality_publicKey '<PUBKEY>'
    option reality_shortId '<SHORTID>'
    option reality_spiderX '/'
    option remarks '<human label>'
```

The global section (`@global[0]`) selects the active node:

```
config global 'global'
    option tcp_node '@nodes[N]'   # N = index in nodes array (0-based, depends on order)
    option udp_node '@nodes[N]'
```

`tcp_node_socks_port` is the local SOCKS5 port (e.g. `1070`).

## Add a second node via UCI

```bash
# Generate the next section name (passwall auto-names them cfg<hex>)
NEW=$(uci add passwall nodes)
uci set "passwall.$NEW.uuid='<UUID>'"
uci set "passwall.$NEW.address='<server_ip>'"
uci set "passwall.$NEW.port='443'"
uci set "passwall.$NEW.protocol='vless'"
uci set "passwall.$NEW.flow='xtls-rprx-vision'"
uci set "passwall.$NEW.transport='tcp'"
uci set "passwall.$NEW.tls='1'"
uci set "passwall.$NEW.reality='1'"
uci set "passwall.$NEW.tls_serverName='www.samsung.com'"
uci set "passwall.$NEW.reality_fingerprint='chrome'"
uci set "passwall.$NEW.reality_publicKey='<PUBKEY>'"
uci set "passwall.$NEW.reality_shortId='<SHORTID>'"
uci set "passwall.$NEW.reality_spiderX='/'"
uci set "passwall.$NEW.remarks='US-VLESS'"
uci commit passwall

# Find the index of the new node
uci show passwall | grep '@nodes\['
# e.g. "@nodes[2]" → use that index in tcp_node
uci set passwall.@global[0].tcp_node='@nodes[2]'
uci set passwall.@global[0].udp_node='@nodes[2]'
uci commit passwall

/etc/init.d/passwall restart
```

## Common field-name mistakes (silently breaks REALITY)

| Wrong | Right | Effect |
|---|---|---|
| `option tls='reality'` | `option tls='1'` + `option reality='1'` | xray JSON gets no `realitySettings` → handshake fails |
| `option sni='...'` | `option tls_serverName='...'` | xray JSON missing `serverName` → REALITY verification fails |
| `option short_id='...'` | `option reality_shortId='...'` | short ID not applied |
| `option public_key='...'` | `option reality_publicKey='...'` | public key not applied |

## Verify the generated xray config

```bash
cat /tmp/etc/passwall/acl/default/TCP_UDP_SOCKS.json | python3 -c "
import json, sys
cfg = json.load(sys.stdin)
ob = cfg['outbounds'][0]
print('server:', ob['settings']['vnext'][0]['address'])
print('flow:', ob['settings']['vnext'][0]['users'][0]['flow'])
print('serverName:', ob['streamSettings']['realitySettings'].get('serverName'))
print('publicKey:', ob['streamSettings']['realitySettings'].get('publicKey'))
print('shortId:', ob['streamSettings']['realitySettings'].get('shortId'))
"
```

Must show the new node's IP, SNI, publicKey, shortId. If `serverName` is
missing → `tls_serverName` was set wrong (most common cause of "VPN connects
but no traffic").

## Switching nodes without restart

In LuCI: 访问控制 → TCP 节点 → 主节点 → pick from dropdown → 保存并应用.
This rewrites `@global[0].tcp_node` and restarts PassWall (~3s downtime).

Or via SSH: same `uci set` commands above.

## DNS mode considerations for multi-node

When using `dns_mode='xray'` (recommended for Chinadns-ng trust-dns),
the xray DNS outbound goes through the SAME proxy chain as the data plane.
If you switch the main node but DNS is still pointed at the OLD node's
upstream, DNS leaks via old node. Fix:

```bash
uci set passwall.@global[0].remote_dns='1.1.1.1:53'   # or 8.8.8.8:53
uci set passwall.@global[0].use_default_dns='223.5.5.5'
uci set passwall.@global[0].v2ray_dns_mode='tcp'      # or 'udp' for direct
uci commit passwall && /etc/init.d/passwall restart
```

If `dns_mode='doh'` with chinadns-ng, the chinadns-ng trust-dns points at
`127.0.0.1#15353` which is the xray DNS proxy. Make sure xray is up (verify
`netstat -tlnup | grep 15353`).

## Final verification

From the OpenWrt router itself (not from a client) — `ps w | grep xray` to
confirm xray is running, then via the local SOCKS:

```bash
curl --socks5 127.0.0.1:1070 -s -o /dev/null -w '%{http_code}\n' https://www.google.com
```

200 = both proxy tunnel and DNS resolution work end-to-end on the new node.