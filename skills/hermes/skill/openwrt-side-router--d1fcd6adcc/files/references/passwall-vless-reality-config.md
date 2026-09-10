# Verified PassWall VLESS-REALITY Configuration (Kwrt 24.10-SNAPSHOT)

Tested on: Kwrt 24.10-SNAPSHOT, PassWall 25.6.1, xray 25.5.16, sing-box 1.11.11
Date: 2026-08-01

## Full working uci config (node section)

```
config nodes 'cfg131c7e'
	option remarks 'vless-reality-443'
	option type 'Xray'
	option protocol 'vless'
	option address '35.176.43.20'
	option port '443'
	option uuid '[REDACTED]'
	option vless_flow 'xtls-rprx-vision'
	option transport 'tcp'
	option tls '1'
	option reality '1'
	option tls_serverName 'www.samsung.com'
	option fingerprint 'chrome'
	option reality_publicKey '[REDACTED]'
	option reality_shortId '[REDACTED]'
	option reality_spiderX '/'
```

## Full working uci config (global DNS section)

```
config global
	option enabled '1'
	option tcp_node '@nodes[2]'
	option udp_node '@nodes[2]'
	option dns_shunt 'chinadns-ng'
	option dns_mode 'xray'
	option v2ray_dns_mode 'tcp'
	option remote_dns '1.1.1.1:53'
	option use_default_dns '223.5.5.5'
```

## Generated xray JSON (key excerpt, verified working)

```json
{
  "outbounds": [{
    "protocol": "vless",
    "settings": {
      "vnext": [{
        "address": "35.176.43.20",
        "port": 443,
        "users": [{
          "id": "[REDACTED]",
          "flow": "xtls-rprx-vision",
          "encryption": "none"
        }]
      }]
    },
    "streamSettings": {
      "network": "tcp",
      "security": "reality",
      "realitySettings": {
        "serverName": "www.samsung.com",
        "publicKey": "[REDACTED]",
        "shortId": "[REDACTED]",
        "fingerprint": "chrome",
        "spiderX": "/"
      }
    }
  }]
}
```

## Network config (wireless bridge via relayd)

```
config interface 'lan'
	option proto 'static'
	option ipaddr '192.168.50.2'
	option netmask '255.255.255.0'
	option gateway '192.168.50.1'
	list dns '223.5.5.5'

config interface 'wwan'
	option proto 'relay'
	list network 'lan'
	list network 'wan'
```

## Firewall fix (allow SSH from main router subnet)

The wireless STA interface lands in `wan` zone by default. wan zone has `input='REJECT'`.
Fix: either change wan zone input to ACCEPT, or move the STA interface to lan zone.

In LuCI: Network → Firewall → wan row → Edit → 入站数据 → 接受

## Verification commands

```bash
# Proxy working?
curl -s --connect-timeout 10 -x socks5://127.0.0.1:1070 https://www.google.com -o /dev/null -w '%{http_code}'
# Expected: 200

# DNS working?
nslookup www.google.com 127.0.0.1
# Expected: resolves to 142.x.x.x

# Transparent proxy (no socks flag)?
curl -s --connect-timeout 10 https://www.google.com -o /dev/null -w '%{http_code}'
# Expected: 200

# xray DNS proxy listening?
netstat -tlnup | grep 15353
# Expected: xray process on 127.0.0.1:15353
```

## Debugging sequence when proxy doesn't work

1. Check xray process: `ps w | grep xray`
2. Check generated config: `cat /tmp/etc/passwall/acl/default/TCP_UDP_SOCKS.json`
3. Verify realitySettings present with serverName
4. Check SOCKS port: `curl -x socks5://127.0.0.1:1070 http://142.250.80.46` (IP, no DNS needed)
5. If SOCKS works but transparent doesn't: DNS issue → check 15353 listening
6. If 15353 not listening: dns_mode wrong (must be 'xray' or 'sing-box', not 'doh')
7. Check nft rules: `nft list ruleset | grep 'dport 53'` (port-53 hijack active?)
8. Check chinadns-ng config: `cat /tmp/etc/passwall/acl/default/chinadns_ng.conf`
   - trust-dns should point to 127.0.0.1#15353
   - china-dns should be public DNS (223.5.5.5), NOT main router IP
