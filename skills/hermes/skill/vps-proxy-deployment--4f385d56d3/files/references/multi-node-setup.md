# Multi-node Setup Reference (UK + US verified example)

This reference captures the verified end-to-end setup for running TWO VLESS-REALITY nodes
on different VPS regions (London + Oregon) and serving them through ONE ClashMi
subscription. All configurations here were verified working as of 2026-08-01.

## Server Inventory (verified)

| Region | IP | 3X-UI panel | xray | Subscription host? |
|---|---|---|---|---|
| UK (eu-west-2, London) | 35.176.43.20 | 19909 (HTTP) / 19910 (HTTPS) | v24.11.21 + tunnel wrapper | **Yes** |
| US (us-west-2, Oregon) | 54.200.16.195 | 19909 / 19910 | v24.11.21 + tunnel wrapper | No |

## UK node credentials (London)

```yaml
server: 35.176.43.20
port: 443
uuid: 1a7f9b3f-26bb-4cf2-bfa2-ccf3016a7249
flow: xtls-rprx-vision
publicKey: MmCv8L6fSdzl-5O-Etgg7bl1OkIlk9-_gaqIX1gHG3o
shortId: e1ae0b7fba11ea14
SNI: www.samsung.com
fingerprint: chrome
```

## US node credentials (Oregon)

```yaml
server: 54.200.16.195
port: 443
uuid: db6854e6-a7d5-4c1d-ad68-d7f993afc7d4
flow: xtls-rprx-vision
publicKey: zoJy4evQX1JZCiSTm5R1JAdNAshFbMyKqxiL2MAV4SE
shortId: 844527026cbf0153
SNI: www.samsung.com
fingerprint: chrome
```

## Subscription YAML (verified working)

```yaml
port: 7890
socks-port: 7891
allow-lan: false
mode: rule
log-level: info
dns:
  enable: true
  enhanced-mode: fake-ip
  fake-ip-range: 198.18.0.1/16
  nameserver:
    - https://dns.alidns.com/dns-query
    - https://doh.pub/dns-query
  fallback:
    - https://1.1.1.1/dns-query
    - https://dns.google/dns-query
  fallback-filter:
    geoip: true
    geoip-code: CN

proxies:
  - name: "UK-London"
    type: vless
    server: 35.176.43.20
    port: 443
    uuid: 1a7f9b3f-26bb-4cf2-bfa2-ccf3016a7249
    network: tcp
    udp: true
    tls: true
    flow: xtls-rprx-vision
    client-fingerprint: chrome
    servername: www.samsung.com
    reality-opts:
      public-key: MmCv8L6fSdzl-5O-Etgg7bl1OkIlk9-_gaqIX1gHG3o
      short-id: e1ae0b7fba11ea14

  - name: "US-Oregon"
    type: vless
    server: 54.200.16.195
    port: 443
    uuid: db6854e6-a7d5-4c1d-ad68-d7f993afc7d4
    network: tcp
    udp: true
    tls: true
    flow: xtls-rprx-vision
    client-fingerprint: chrome
    servername: www.samsung.com
    reality-opts:
      public-key: zoJy4evQX1JZCiSTm5R1JAdNAshFbMyKqxiL2MAV4SE
      short-id: 844527026cbf0153

proxy-groups:
  - name: "PROXY"
    type: select
    proxies:
      - UK-London
      - US-Oregon

  - name: "AUTO"
    type: url-test
    proxies:
      - UK-London
      - US-Oregon
    url: http://www.gstatic.com/generate_204
    interval: 300

  - name: "DIRECT"
    type: select
    proxies:
      - DIRECT

rules:
  - GEOIP,CN,DIRECT
  - MATCH,PROXY
```

## Subscription delivery (UK VPS hosts it)

URL format (Basic Auth with URL-safe password — alphanumeric only, NEVER base64):
***REDACTED***
http://USER:PASS@35.176.43.20/SUB_PATH/clash.yaml
```

nginx config:
```nginx
server {
    listen 80;
    server_name _;
    location /SUB_PATH/clash.yaml {
        auth_basic "Restricted";
        auth_basic_user_file /etc/nginx/.htpasswd;
        alias /var/www/sub/clash.yaml;
        default_type "text/yaml; charset=utf-8";
    }
    location / { return 404; }
}
```

## Local verification (Mac, before pushing to user)

```bash
# 1. Download subscription to local file
curl -s -u USER:PASS http://35.176.43.20/SUB_PATH/clash.yaml -o /tmp/sub.yaml

# 2. Validate with mihomo (same kernel ClashMi uses)
curl -sL "https://github.com/MetaCubeX/mihomo/releases/download/v1.19.10/mihomo-darwin-arm64-go120-v1.19.10.gz" \
  -o /tmp/mihomo.gz && gunzip -f /tmp/mihomo.gz && chmod +x /tmp/mihomo

# 3. Change ports if 7890/7891 are taken (running ClashMi)
sed -i.bak 's/^port: 7890/port: 7892/; s/^socks-port: 7891/socks-port: 7893/' /tmp/sub.yaml

# 4. Run mihomo in background + test
/tmp/mihomo -d /tmp/mih_test -f /tmp/sub.yaml &
sleep 3
curl -x http://127.0.0.1:7892 https://www.google.com -o /dev/null -w 'http=%{http_code}\n'
curl -x http://127.0.0.1:7892 https://ip.sb -w '\nhttp=%{http_code}\n'
# → 200 + 2600:1f13:... (Oregon IPv6) when PROXY first entry is US-Oregon
# → 200 + 2a05:d01c:... (London IPv6) when PROXY first entry is UK-London
# To test the other node: edit /tmp/sub.yaml to reorder PROXY group, restart mihomo
```

## OpenWrt side-router node setup (verified)

```bash
# Append new node section (use quoted named section)
cat >> /etc/config/passwall << 'EOF'

config nodes 'us_reality'
    option remarks 'VLESS-REALITY-Oregon'
    option type 'Xray'
    option protocol 'vless'
    option address '54.200.16.195'
    option port '443'
    option uuid 'db6854e6-a7d5-4c1d-ad68-d7f993afc7d4'
    option flow 'xtls-rprx-vision'
    option encryption 'none'
    option transport 'tcp'
    option tls '1'
    option reality '1'
    option reality_fingerprint 'chrome'
    option reality_publicKey 'zoJy4evQX1JZCiSTm5R1JAdNAshFbMyKqxiL2MAV4SE'
    option reality_shortId '844527026cbf0153'
    option reality_spiderX '/'
    option tls_serverName 'www.samsung.com'
EOF

# Switch primary node (always check actual index first)
uci show passwall | grep '@nodes\['    # confirm @nodes[N] index
uci set passwall.@global[0].tcp_node='@nodes[3]'   # use real index, not assumed
uci set passwall.@global[0].udp_node='@nodes[3]'
uci commit passwall
/etc/init.d/passwall restart
# SSH drops for ~5s during restart — wait and reconnect.
```

Verify active node from the router:
```bash
curl -s --connect-timeout 8 https://ip.sb -w 'http=%{http_code}\n'
# IP should match the active node's region
```

## iOS ClashMi VPN tunnel timeout (real session issue)

If the user reports `startVPNtunnel status timeout` on iOS:

1. **This is iOS VPN configuration issue, NOT proxy config issue** — mihomo/sing-box tests prove the config works.
2. Fix: in ClashMi iOS, delete the existing subscription → iOS Settings → General → VPN & Device Management → delete any stale VPN configs → quit ClashMi entirely → re-add subscription.
3. Alternative: switch to **Hiddify** (same subscription URL works) which has fewer iOS VPN integration quirks.