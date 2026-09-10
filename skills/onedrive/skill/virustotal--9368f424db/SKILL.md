---
name: virustotal
description: >
  VirusTotal 安全检测框架。查询文件哈希、URL、域名、IP 的威胁情报。
  聚合 70+ 杀毒引擎结果，辅助判断文件/链接安全性。
  触发词："查一下这个文件"、"检查这个链接"、"域名安全吗"、
  "这个 IP 有问题吗"、"virustotal"、"VT"
metadata:
  openclaw:
    emoji: "🔍"
---

# VirusTotal Security Skill

VirusTotal 是一个知名的在线恶意软件/URL/域名检测平台，聚合了 70+ 杀毒引擎的扫描结果。本 skill 让 AI Agent 能够调用 VirusTotal API v3 进行安全检测。

**注意**：本 skill 仅供安全研究目的使用。

## API Key 配置

VirusTotal API v3 需要 API Key 才能使用。

### 获取 API Key

1. 访问 [VirusTotal 注册页面](https://www.virustotal.com/gui/join-us)
2. 注册免费账号（有一定查询配额限制）
3. 登录后访问 [API Key 页面](https://www.virustotal.com/gui/user/HuKee/apikey) 获取你的 API Key

### 配置方式

在你的 agent 环境中设置环境变量：

```bash
export VIRUSTOTAL_API_KEY=***REDACTED***
```

或者在 agent 的配置文件中设置变量 `VIRUSTOTAL_API_KEY`。

### 速率限制（免费 tier）

- **4 次/分钟**，每分钟最多 4 次 API 调用
- 文件上传：20 次/分钟
- 建议在连续查询间添加短暂延迟

---

## 查询类型

### 1. 文件哈希查询

查询已扫描过的文件（通过 MD5/SHA1/SHA256 哈希）。

```bash
curl -s "https://www.virustotal.com/api/v3/files/{hash}" \
  -H "x-apikey: ***REDACTED***
```

**返回关键字段**：
- `data.attributes.last_analysis_stats` — 各引擎检测结果
- `data.attributes.last_analysis_results` — 每个引擎的详细结果
- `data.attributes.meaningful_name` — 文件真实名称
- `data.attributes.creation_date` — 文件首次提交时间
- `data.attributes.type_description` — 文件类型

**输出示例**：
```
## 文件分析结果

**文件：** suspicious.exe
**哈希：** abc123def456...
**类型：** Win32 Executable
**首次提交：** 2024-01-15

### 检测统计
- 阳性：12/72
- 引擎标记：Kaspersky、TDR、McAfee...

### 安全评级
🟡 可疑文件（12 个引擎标记）
```

### 2. URL 扫描查询

查询 URL 是否被标记为恶意/钓鱼。

```bash
# 先对 URL 进行 base64 编码
curl -s "https://www.virustotal.com/api/v3/urls/{url_id}" \
  -H "x-apikey: ***REDACTED***

# 或者直接提交 URL 进行扫描
curl -s -X POST "https://www.virustotal.com/api/v3/urls" \
  -d "url=https://example.com/malware" \
  -H "x-apikey: ***REDACTED***
```

**返回关键字段**：
- `data.attributes.last_analysis_stats` — 检测统计
- `data.attributes.last_analysis_results` — 各引擎结果
- `data.attributes.creation_date` — 首次扫描时间
- `data.attributes.threat_names` — 威胁分类（钓鱼、恶意软件等）

**URL ID 计算方法**：将 URL 进行 base64 编码，移除 `=` 填充，替换 `/` 为 `_`，`+` 为 `-`

Python 示例：
```python
import base64
url = "https://example.com/malware"
url_id = base64.urlsafe_b64encode(url.encode()).decode().rstrip("=")
```

### 3. 域名/主机名查询

获取域名的 WHOIS、DNS 记录、关联样本等情报。

```bash
curl -s "https://www.virustotal.com/api/v3/domains/{domain}" \
  -H "x-apikey: ***REDACTED***
```

**返回关键字段**：
- `data.attributes.creation_date` — 域名注册时间
- `data.attributes.registrar` — 注册商
- `data.attributes.whois` — WHOIS 完整信息
- `data.attributes.last_analysis_stats` — 检测统计
- `data.attributes.popularity_ranking` — 流量排名
- `data.attributes.jarm` — JARM 指纹（识别 C2 服务器）
- `data.attributes.last_dns_records` — DNS 记录

**分析要点**：
- 注册时间短的域名风险较高
- 匿名注册（Privacy Guard）需警惕
- 关联多个恶意样本是强风险信号

### 4. IP 地址查询

查询 IP 的威胁情报和关联域名。

```bash
curl -s "https://www.virustotal.com/api/v3/ip_addresses/{ip}" \
  -H "x-apikey: ***REDACTED***
```

**返回关键字段**：
- `data.attributes.network` — 所属网络
- `data.attributes.country` — 国家
- `data.attributes.last_analysis_stats` — 检测统计
- `data.attributes.jarm` — JARM 指纹
- `data.attributes.resolutions` — 关联域名

**分析要点**：
- 恶意软件常见 C2 IP
- 关联多个钓鱼/恶意域名
- 非住宅 IP（托管服务器）风险视场景而定

### 5. 文件上传扫描

上传文件（最大 32MB）进行完整扫描。

```bash
curl -s -X POST "https://www.virustotal.com/api/v3/files" \
  -F "file=@/path/to/file.exe" \
  -H "x-apikey: ***REDACTED***
```

上传后会返回 `id`（分析 ID），轮询获取结果：

```bash
curl -s "https://www.virustotal.com/api/v3/analyses/{id}" \
  -H "x-apikey: ***REDACTED***
```

**注意**：
- 文件大小限制 32MB
- 免费 tier 有上传频率限制
- 建议先计算文件哈希查询是否已有结果，避免重复上传

---

## 输出格式模板

### 文件分析报告
```
## 🔍 文件分析报告 — {日期}

**文件名：** {name}
**哈希类型：** SHA256
**Hash：** `{hash}`
**文件大小：** {size}
**文件类型：** {type}

### 检测结果
- 🟢 安全：{safe}/72
- 🟡 可疑：{suspicious}/72
- 🔴 恶意：{malicious}/72

### 引擎标记详情
{列表显示标记恶意的引擎和类型}

### 威胁分类
{whois/whois穷举}

### 安全建议
{根据检测结果给出建议}
```

### URL 分析报告
```
## 🔍 URL 安全分析 — {日期}

**URL：** {url}
**首次扫描：** {date}

### 检测结果
- 🟢 安全：{safe}/72
- 🔴 恶意：{malicious}/72

### 威胁类型
{钓鱼、恶意软件分发、广告软件等}

### 详情
{相关引擎的详细判断}

### 安全建议
{访问风险评估}
```

### 域名/IP 分析报告
```
## 🔍 威胁情报报告 — {日期}

**目标：** {domain/ip}
**类型：** 域名/IP
**注册/所属：** {registrar/network}

### 基础信息
- 注册时间：{date}
- 注册商：{registrar}
- 国家：{country}

### 检测结果
- 🟢 安全：{safe}/72
- 🔴 恶意：{malicious}/72

### 关联样本数
{数量}

### DNS/关联域名
{列表}

### WHOIS 摘要
{关键信息}

### 安全建议
{风险评估}
```

---

## 触发短语

当用户输入以下内容时，激活本 skill：

- "查一下这个文件安全吗"
- "检查这个链接"
- "这个 URL 有问题吗"
- "域名安全吗"
- "这个 IP 是什么情况"
- "virustotal"
- "VT 查询"
- "扫描一下"
- "帮我看看这个文件"
- 粘贴文件哈希（MD5/SHA1/SHA256，32/40/64 字符）
- 粘贴 URL 或域名/IP 地址（6 字符）

---

## 分析流程

### 文件分析流程
1. 识别用户提供的是哈希还是文件路径
2. 如果是路径，计算文件哈希（MD5/SHA256）
3. 调用 `/files/{hash}` 查询
4. 解析 `last_analysis_stats` 和 `last_analysis_results`
5. 按模板输出报告
6. 给出安全建议

### URL 分析流程
1. 接收 URL，验证格式
2. 计算 URL ID（base64 编码）
3. 调用 `/urls/{url_id}` 查询
4. 如无结果，调用 POST `/urls` 提交扫描
5. 解析结果并输出报告

### 域名/IP 分析流程
1. 识别是域名还是 IP 地址
2. 调用对应端点查询
3. 解析 WHOIS、DNS、检测结果
4. 输出威胁情报报告

---

## 免责声明

本 skill 仅供安全研究和教育目的使用。

- VirusTotal 聚合多家厂商结果，存在误报/漏报可能
- 阴性结果不代表文件 100% 安全
- 请遵守当地法律法规使用本 skill
- 作者不对误报/漏报导致的任何损失负责

---

<sub>VirusTotal Skill for HuabSmart / MOSS</sub>
