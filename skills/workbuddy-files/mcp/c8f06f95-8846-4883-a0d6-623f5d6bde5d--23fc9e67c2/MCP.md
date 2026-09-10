{
  "mcpServers": {
    "connector:linear-mcp": {
      "url": "https://mcp.linear.app/mcp",
      "disabled": true
    },
    "connector:canva-ai": {
      "type": "streamableHttp",
      "url": "https://mcp.canva.com/mcp",
      "timeout": 60000,
      "disabled": true
    },
    "connector:tdx-connector": {
      "url": "https://txmcp.tdx.com.cn:3001/txmcp",
      "type": "streamable-http",
      "timeout": 30000,
      "disabled": true
    },
    "connector:westock-mcp": {
      "type": "streamableHttp",
      "url": "https://stockbuddy.qq.com/cgi/cgi-bin/openai/mcp/mcp",
      "timeout": 30000,
      "disabled": true
    },
    "connector:qq-mail": {
      "timeout": 600000,
      "url": "https://api.mail.qq.com/mcp",
      "disabled": true
    },
    "connector:ima-mcp": {
      "url": "https://ima.qq.com/mcp",
      "type": "streamableHttp",
      "timeout": 20000,
      "disabled": true
    },
    "connector:lexiang": {
      "timeout": 600000,
      "url": "https://mcp.lexiang-app.com/mcp",
      "disabled": true
    },
    "connector:tencent-docs": {
      "timeout": 600000,
      "url": "https://docs.qq.com/openapi/mcp",
      "disabled": true
    },
    "connector:tencent-docs-oa": {
      "timeout": 600000,
      "url": "https://saas.docs.qq.com/api/v6/open/agent/mcp",
      "disabled": true
    },
    "connector:tencent-survey": {
      "type": "streamableHttp",
      "url": "https://wj.qq.com/api/v2/mcp",
      "timeout": 30000,
      "disabled": true
    },
    "connector:tapd": {
      "url": "https://websocket.tapd.cn/mcp/mcp",
      "disabled": true
    },
    "connector:tencent-weiyun": {
      "url": "https://www.weiyun.com/api/v3/mcpserver",
      "type": "streamableHttp",
      "timeout": 60000,
      "disabled": true
    },
    "connector:fbs-connector": {
      "type": "streamableHttp",
      "url": "https://api2.u3w.com/fbs-mcp/mcp",
      "staticHeaders": {
        "X-FBS-Connector-Source": "fbs-connector",
        "X-FBS-Connector-Version": "1.2.9",
        "X-FBS-Connector-Package-Version": "26.8.20",
        "X-Request-Source": "workbuddy"
      },
      "disabledTools": [
        "lebao_drop"
      ],
      "timeout": 60000,
      "disabled": true
    },
    "connector:kdocs": {
      "timeout": 600000,
      "url": "https://mcp-center.wps.cn/skill_hub/mcp",
      "staticHeaders": {
        "X-Request-Source": "workbuddy",
        "X-Skill-Version": "1.4.12"
      },
      "disabled": true
    },
    "connector:pkulaw": {
      "type": "streamableHttp",
      "url": "https://apim-gateway.pkulaw.com/mcp-law-agg/1.0.0/mcp",
      "timeout": 60000,
      "disabled": true
    },
    "connector:qcc-company": {
      "type": "streamableHttp",
      "url": "https://agent.qcc.com/mcp/company/stream",
      "disabled": true
    },
    "connector:tyc-mcp": {
      "url": "https://mcp.tianyancha.com/v1",
      "type": "streamableHttp",
      "timeout": 600000,
      "disabled": true
    },
    "connector:baidu-netdisk": {
      "type": "sse",
      "url": "https://mcp-pan.baidu.com/sse",
      "disabled": true
    },
    "connector:tushare": {
      "url": "https://api.tushare.pro/mcp/?token=${TUSHARE_TOKEN}",
      "type": "streamableHttp",
      "timeout": 30000,
      "disabled": true
    },
    "connector:dnb-global-data": {
      "type": "streamableHttp",
      "url": "https://plus.dnb.com/v2/mcp",
      "headers": {
        "Authorization": "***REDACTED***"
      },
      "timeout": 86400000,
      "disabled": true
    },
    "connector:xhcj-mcp-announcements-news-policy": {
      "type": "streamableHttp",
      "url": "https://mcp.cnfic.com.cn/mcp-servers/xhcj-mcp-announcements-news-policy",
      "headers": {
        "Authorization": "***REDACTED***"
      },
      "timeout": 30000,
      "disabled": true
    },
    "connector:github": {
      "timeout": 600000,
      "url": "https://api.githubcopilot.com/mcp/",
      "disabled": true
    },
    "connector:notion": {
      "url": "https://mcp.notion.com/mcp",
      "disabled": true
    },
    "connector:tencent-qidian-cs": {
      "url": "https://sse.qidian.qq.com/qidian-cs/mcp",
      "disabled": true
    },
    "connector:edgeone-pages": {
      "timeout": 600000,
      "command": "npx",
      "args": [
        "edgeone-pages-mcp-fullstack@latest",
        "--region",
        "china"
      ],
      "runtime": {
        "type": "node",
        "version": ">=20"
      },
      "disabled": true
    },
    "connector:cloudbase": {
      "command": "npx",
      "args": [
        "-y",
        "@cloudbase/cloudbase-mcp@latest"
      ],
      "runtime": {
        "type": "node",
        "version": ">=20"
      },
      "staticEnv": {
        "INTEGRATION_IDE": "WorkBuddy"
      },
      "disabled": true
    },
    "connector:bugly-token": "***REDACTED***",
    "connector:neo-crm": {
      "type": "streamableHttp",
      "url": "https://mcp.xiaoshouyi.com/mcp",
      "disabled": true
    },
    "connector:xiaoe-cloud-cli": {
      "type": "streamableHttp",
      "url": "https://agent.xiaoe-tech.com/mcp",
      "timeout": 60000,
      "disabled": true
    },
    "connector:yuandian-mcp": {
      "type": "streamableHttp",
      "url": "https://open.chineselaw.com/mcp",
      "timeout": 600000,
      "disabled": true
    },
    "connector:weisheng-scrm": {
      "type": "stdio",
      "timeout": 120000,
      "command": "npx",
      "args": [
        "--registry=https://registry.npmmirror.com",
        "-y",
        "mcp-server-weisheng-scrm@latest"
      ],
      "runtime": {
        "type": "node",
        "version": ">=18"
      },
      "env": {
        "SCRM_APP_KEY": "",
        "SCRM_BASE_URL": "https://open.wshoto.com",
        "npm_config_registry": "https://registry.npmmirror.com"
      },
      "disabled": true
    },
    "connector:zfs-fssc-ai": {
      "type": "sse",
      "url": "https://mcpdemo.ztccloud.com.cn/sse",
      "headers": {
        "X-Zfs-Login-Key": "${ZFS_LOGIN_KEY}",
        "X-Zfs-Login-Password": "***REDACTED***"
      },
      "timeout": 120000,
      "disabled": true
    },
    "connector:gildata": {
      "type": "streamableHttp",
      "url": "https://api.gildata.com/mcp-servers/aidata-assistant-srv-tool?token=${GILDATA_TOKEN}",
      "timeout": 180000,
      "disabled": true
    },
    "connector:tencent-map": {
      "type": "sse",
      "url": "https://mcp.map.qq.com/sse?key=${TENCENT_MAP_KEY}&format=0",
      "timeout": 30000,
      "disabled": true
    },
    "connector:qixinhuiyan-mcp": {
      "type": "streamableHttp",
      "url": "https://mcp.qixin.com/mcp",
      "disabled": true
    },
    "connector:patsnap-search": {
      "type": "streamableHttp",
      "url": "https://connect.zhihuiya.com/2b0355/logic-mcp?apikey=${PATSNAP_API_KEY}",
      "timeout": 30000,
      "disabled": true
    },
    "connector:mastergo-vibe-mcp": {
      "type": "stdio",
      "command": "npx",
      "args": [
        "-y",
        "@mastergo/vibe-mcp",
        "--url=http://localhost:50678"
      ],
      "env": {
        "NO_PROXY": "localhost,127.0.0.1,::1"
      },
      "runtime": {
        "type": "node",
        "version": ">=18"
      },
      "npmRegistry": "https://registry.npmmirror.com",
      "disabled": true
    },
    "connector:tencent-health-nges": {
      "type": "streamableHttp",
      "url": "https://test.nges.qq.com/mcp/aggregate",
      "disabled": true
    },
    "connector:canva": {
      "type": "streamableHttp",
      "url": "https://mcp.canva.cn/mcp",
      "timeout": 60000,
      "disabled": true
    },
    "connector:qingflow": {
      "type": "streamableHttp",
      "url": "https://mcp.qingflow.com/mcp",
      "timeout": 30000,
      "disabled": true
    },
    "connector:wk-workbuddy": {
      "url": "https://mcp.wkinfo.com.cn/mcp-servers/integrated/",
      "type": "streamableHttp",
      "timeout": 60000,
      "disabled": true
    },
    "connector:fyopen-lawsearch": {
      "type": "streamableHttp",
      "url": "https://api.cjbdi.com:8443/354347/mcp_law_service",
      "disabled": true
    },
    "connector:yzf-invoice-mcp-server": {
      "type": "streamableHttp",
      "url": "https://super-ai-app.yunzhangfang.com/api/mcp/invoice/stream",
      "timeout": 30000,
      "disabled": true
    },
    "connector:tongzhou-fin-research": {
      "type": "streamableHttp",
      "url": "https://mcp-gateway.textmind-gz.com/mcp/tongzhou-research",
      "timeout": 180000,
      "disabled": true
    },
    "connector:tec-do": {
      "type": "streamableHttp",
      "url": "https://tec-chi-external-skill-mcp.tec-do.cn/mcp",
      "timeout": 30000,
      "disabled": true
    },
    "connector:yingmi-mcp": {
      "type": "streamableHttp",
      "url": "https://stargate.yingmi.com/mcp/v2?apiKey=${YINGMI_API_KEY}",
      "env": {
        "YINGMI_API_KEY": "***REDACTED***"
      },
      "timeout": 30000,
      "disabled": true
    },
    "connector:jinshuju": {
      "url": "https://jinshuju.net/mcp",
      "type": "streamableHttp",
      "timeout": 30000,
      "disabled": true
    },
    "connector:moka": {
      "type": "streamableHttp",
      "url": "https://mcp.mokahr.com/mcp",
      "disabled": true
    },
    "connector:linkfox-product-selection": {
      "type": "streamableHttp",
      "url": "https://mcp-tool-gateway.linkfox.com/mcp/any-tool",
      "disabled": true
    },
    "connector:archive-hospital-mcp": {
      "type": "streamableHttp",
      "url": "https://bingli.tengmed.com/mcp",
      "timeout": 30000,
      "disabled": true
    },
    "connector:wind-finance": {
      "type": "streamableHttp",
      "url": "https://mcp.wind.com.cn/vserver_workbuddy/mcp/",
      "headers": {
        "Authorization": "***REDACTED***",
        "Accept": "application/json, text/event-stream"
      },
      "timeout": 30000,
      "disabled": true
    },
    "connector:qcc-legal": {
      "type": "streamableHttp",
      "url": "https://agent.qcc.com/mcp/legal/stream",
      "disabled": true
    },
    "connector:salesnail-instructor": {
      "type": "streamableHttp",
      "url": "https://sn.long-arena.com/mcp",
      "disabled": true
    },
    "connector:mx-ds-mcp": {
      "type": "streamableHttp",
      "url": "https://mxapi.eastmoney.com/mxds/v2/mcp",
      "timeout": 180000,
      "disabled": true
    },
    "connector:cisp-mcp": {
      "type": "streamableHttp",
      "url": "https://cisp.zenitera.com/mcp",
      "headers": {
        "Authorization": "***REDACTED***"
      },
      "timeout": 30000,
      "disabled": true
    },
    "connector:ai-hive": {
      "type": "stdio",
      "command": "npx",
      "args": [
        "-y",
        "@infimind-next/ai-hive-mcp@latest"
      ],
      "runtime": {
        "type": "node",
        "version": ">=20.19.0"
      },
      "disabled": true
    },
    "connector:finenter": {
      "type": "sse",
      "url": "https://mcp-server-global.comein.cn/mcp-servers/mcp-server-brm/sse",
      "disabled": true
    },
    "connector:chuhaijiang": {
      "type": "streamableHttp",
      "url": "https://mcp.gateway.chuhaijiang.com/mcp/oauth",
      "timeout": 30000,
      "disabled": true
    },
    "connector:kuaicha-search": {
      "type": "streamableHttp",
      "url": "https://bizveris.kuaicha365.com/mcp?source=workbuddy",
      "headers": {
        "open-authorization": "***REDACTED***"
      },
      "timeout": 30000,
      "disabled": true
    },
    "connector:youshu-bd-mate": {
      "type": "streamableHttp",
      "url": "https://open.yscredit.com/ys-mcp/report",
      "timeout": 30000,
      "disabled": true
    },
    "connector:shanglv-mcp-gateway": {
      "type": "streamableHttp",
      "url": "https://mcp-gateway.yql.net/mcp/",
      "timeout": 30000,
      "disabled": true
    },
    "connector:xingtu-claw-risk": {
      "url": "https://claw-mcp.tcredit.com/mcp/sse",
      "type": "sse",
      "timeout": 600000,
      "disabled": true
    },
    "connector:mzl-trademark": {
      "type": "streamableHttp",
      "url": "https://www.mozlen.com/mcp",
      "timeout": 65000,
      "disabled": true
    },
    "connector:picset-commerce-images": {
      "type": "streamableHttp",
      "url": "https://picsetai.cn/functions/v1/agent-mcp-v1/mcp",
      "headers": {
        "Authorization": "***REDACTED***"
      },
      "timeout": 30000,
      "disabled": true
    },
    "connector:picset-video-generation": {
      "type": "streamableHttp",
      "url": "https://picsetai.cn/functions/v1/agent-video-mcp-v1/mcp",
      "headers": {
        "Authorization": "***REDACTED***"
      },
      "timeout": 30000,
      "disabled": true
    },
    "connector:opendata": {
      "type": "sse",
      "url": "https://mcp.isjike.com/mcp-servers/opendata/sse",
      "headers": {
        "Authorization": "***REDACTED***"
      },
      "timeout": 30000,
      "disabled": true
    },
    "connector:bazhuayu": {
      "type": "streamableHttp",
      "url": "https://mcp.bazhuayu.com?includeTools=search_templates,execute_task,get_task_status,export_data,search_tasks,start_or_stop_task",
      "timeout": 60000,
      "disabled": true
    },
    "connector:ezjoin-meeting": {
      "type": "streamableHttp",
      "url": "https://www.ezyjoin.cn/api/mcp/message",
      "timeout": 30000,
      "disabled": true
    },
    "connector:gangtise-mcp": {
      "type": "streamableHttp",
      "url": "https://openapi.gangtise.com/application/open-mcp/",
      "headers": {
        "accessKey": "${GTS_ACCESS_KEY}",
        "secretKey": "***REDACTED***"
      },
      "timeout": 60000,
      "disabled": true
    },
    "connector:jiushuyun": {
      "type": "streamableHttp",
      "url": "https://work.jiushuyun.com/mcp",
      "timeout": 30000,
      "disabled": true
    },
    "connector:pandadata": {
      "url": "https://pandadatamcp.pandaaiquant.com/mcp",
      "disabled": true
    },
    "connector:kling-ai-plugin": {
      "type": "http",
      "url": "https://klingai.com/mcp",
      "timeout": 30000,
      "disabled": true
    },
    "connector:gongyi-open-mcp": {
      "type": "streamableHttp",
      "url": "https://ssl.gongyi.qq.com/gygw-web/api/open/tob/mcp",
      "disabled": true
    },
    "connector:sharecrm": {
      "type": "streamableHttp",
      "url": "https://open.fxiaoke.com/mcp/connector?id=workbuddy",
      "disabled": true
    },
    "connector:lingxing-mcp": {
      "type": "streamableHttp",
      "url": "https://openmcp.lingxing.com/mcp-servers/lingxing-mcp",
      "headers": {
        "X-Mcp-Key": "${LINGXING_MCP_KEY}"
      },
      "timeout": 30000,
      "disabled": true
    },
    "connector:salestouch": {
      "type": "streamableHttp",
      "url": "https://touch.long-arena.com/mcp",
      "disabled": true
    },
    "connector:h3yun-connector": {
      "url": "https://${H3YUN_API_BASE_URL}/v1/agent/mcp",
      "type": "streamableHttp",
      "headers": {
        "Authorization": "***REDACTED***"
      },
      "timeout": 30000,
      "disabled": true
    },
    "connector:dknowc-mcp": {
      "type": "streamableHttp",
      "url": "https://mcp.dknowc.cn/s6/mcp",
      "disabled": true
    },
    "connector:morningstar": {
      "type": "streamableHttp",
      "url": "https://mcp.morningstar.cn/mcp",
      "timeout": 30000,
      "disabled": true
    },
    "connector:sq-company-dynamic": {
      "type": "streamableHttp",
      "url": "https://api.chanyedata.com/mcp/c3f5924cc60dbe1729f5cc332e627304/mcp",
      "headers": {
        "Authorization": "***REDACTED***"
      },
      "timeout": 30000,
      "disabled": true
    },
    "connector:fazhi-law": {
      "type": "streamableHttp",
      "url": "https://bizveris.kuaicha365.com/law_agent/mcp?source=workbuddy",
      "headers": {
        "open-authorization": "***REDACTED***"
      },
      "timeout": 30000,
      "disabled": true
    },
    "connector:ifind-mcp": {
      "url": "https://api-mcp.51ifind.com:8643/ds-mcp-servers/hexin-ifind-financial-mcp",
      "disabled": true
    },
    "connector:tencent-tchouse-c": {
      "type": "streamableHttp",
      "url": "https://tcmcpserver.cloud.tencent.com/tchousec/mcp",
      "disabled": true
    },
    "connector:ioa": {
      "command": "npx",
      "args": [
        "-y",
        "@ioacloud/ioacloud-mcp@latest"
      ],
      "disabled": true
    },
    "connector:teacher-assistant": {
      "url": "https://aiteach.qq.com/mcp",
      "type": "streamableHttp",
      "timeout": 30000,
      "disabled": true
    },
    "connector:fanruan-growth-advisor": {
      "type": "streamableHttp",
      "url": "https://www.mossdo.com/api/v1/mcp",
      "headers": {
        "X-Moss-WorkBuddy": "1"
      },
      "timeout": 30000,
      "disabled": true
    },
    "connector:flova": {
      "type": "streamableHttp",
      "url": "https://service.flova.tv/api/mcp/",
      "timeout": 60000,
      "disabled": true
    },
    "connector:dcs-cloud": {
      "type": "stdio",
      "command": "npx",
      "args": [
        "dcs-cloud-mcp-server"
      ],
      "env": {
        "DCS_PAT": "${DCS_PAT}"
      },
      "runtime": {
        "type": "node",
        "version": ">=18.0.0"
      },
      "timeout": 60000,
      "disabled": true
    },
    "connector:duoguan-fengchao": {
      "type": "streamableHttp",
      "url": "https://fc.duoguan.com/mcp",
      "timeout": 30000,
      "disabled": true
    },
    "connector:tplus-api": {
      "type": "streamableHttp",
      "url": "https://mcphub.chanapp.chanjet.com/151/mcp",
      "timeout": 30000,
      "disabled": true
    },
    "connector:gaodun-job": {
      "type": "streamableHttp",
      "url": "https://apigateway.gaodun.com/dyson/mcp",
      "timeout": 60000,
      "disabled": true
    },
    "connector:proboost": {
      "type": "sse",
      "url": "https://mcp.microdata-inc.com/mcp-servers/oauth/proboost-tiktok-amazon-patent-mcp/sse?invite=WORKBUDDY",
      "timeout": 60000,
      "disabled": true
    },
    "connector:tanyuan-assistant": {
      "type": "streamableHttp",
      "url": "https://api.tanyuan.qq.com/wb/mcp",
      "timeout": 30000,
      "disabled": true
    },
    "connector:fenbi-baokao-decision": {
      "type": "streamableHttp",
      "url": "https://market-api.fenbi.com/workbuddy/mcp",
      "disabled": true
    },
    "connector:fadada-richee": {
      "type": "streamableHttp",
      "url": "https://claw.richee.cn/claw-api/mcp/workbuddy",
      "timeout": 30000,
      "disabled": true
    },
    "connector:wisenote": {
      "type": "streamableHttp",
      "url": "https://100wiser.com/workbuddy/wisenote/meeting/mcp",
      "timeout": 30000,
      "disabled": true
    },
    "connector:jiandaoyun": {
      "type": "streamableHttp",
      "url": "https://mcp.jiandaoyun.com/mcp",
      "timeout": 30000,
      "disabled": true
    },
    "connector:camscanner-mcp": {
      "type": "streamableHttp",
      "url": "https://ai-tools.camscanner.com/mcp",
      "timeout": 120000,
      "disabled": true
    },
    "connector:fuma-ai-callout": {
      "type": "streamableHttp",
      "url": "https://services.vcrm.vip:60610/mcp",
      "headers": {
        "access-token": "***REDACTED***",
        "orgCode": "${ORG_CODE}",
        "loginName": "${LOGIN_NAME}"
      },
      "timeout": 30000,
      "disabled": true
    },
    "connector:h3c-cloudnet": {
      "type": "sse",
      "url": "https://oasis.h3c.com/mcp-server/api/sse",
      "headers": {
        "Authorization": "***REDACTED***"
      },
      "timeout": 30000,
      "disabled": true
    },
    "connector:yzf-general-mcp-server": {
      "type": "streamableHttp",
      "url": "https://super-ai-app.yunzhangfang.com/api/mcp/general/stream",
      "timeout": 60000,
      "disabled": true
    },
    "connector:tencent-dlc": {
      "url": "https://tcmcpserver.cloud.tencent.com/dlc/mcp",
      "type": "streamable-http",
      "disabled": true
    },
    "connector:tiktok": {
      "type": "streamableHttp",
      "url": "https://business-api.tiktok.com/open_mcp/tt-ads-mcp-flat",
      "disabled": true
    },
    "connector:lingyi-mcp": {
      "type": "streamableHttp",
      "url": "https://service.lingyishuke.com/api/v1/skill-provider/mcp",
      "timeout": 30000,
      "disabled": true
    },
    "connector:dzh-mcp": {
      "type": "streamableHttp",
      "url": "https://mcpali.dzh.com.cn/mcp",
      "timeout": 30000,
      "disabled": true
    },
    "connector:fenbeitong": {
      "type": "streamableHttp",
      "url": "https://mcp.fenbeitong.com/mcp/source/workbuddy",
      "timeout": 120000,
      "headers": {
        "X-FBT-Channel": "workbuddy"
      },
      "disabled": true
    },
    "connector:coros": {
      "type": "streamableHttp",
      "url": "https://mcpcn.coros.com/mcp",
      "timeout": 60000,
      "disabled": true
    },
    "connector:datayes-data": {
      "type": "streamableHttp",
      "url": "https://dataapi-mcp-server.datayes.com/datayes-data/mcp",
      "headers": {
        "Authorization": "***REDACTED***",
        "Accept": "application/json, text/event-stream"
      },
      "timeout": 30000,
      "disabled": true
    },
    "connector:alphapai-lite-mcp": {
      "type": "streamableHttp",
      "url": "https://alphapai-idv.rabyte.cn/alpha/open-api/v1/personal/mcp",
      "timeout": 30000,
      "disabled": true
    },
    "connector:efunds": {
      "type": "streamableHttp",
      "url": "https://sc.efunds.com.cn/api/csai-mcp-service/mcp/",
      "disabled": true
    },
    "connector:plaud": {
      "type": "streamableHttp",
      "url": "https://mcp.plaud.cn/mcp",
      "timeout": 30000,
      "disabled": true
    },
    "connector:tct-business-expert": {
      "type": "streamableHttp",
      "url": "https://tctmcp.zhaogang.com/mcp",
      "timeout": 60000,
      "disabled": true
    },
    "connector:agent-earth": {
      "type": "streamableHttp",
      "url": "https://agentearth.ai/mcp-server/",
      "headers": {
        "X-Api-Key": "***REDACTED***"
      },
      "timeout": 60000,
      "disabled": true
    },
    "connector:caihui-mcp": {
      "url": "https://mcp.finchina.com/finchina-data-mcp-server/mcp",
      "type": "streamableHttp",
      "headers": {
        "x-api-key": "***REDACTED***"
      },
      "staticHeaders": {
        "client": "WorkBuddy"
      },
      "disabled": true
    },
    "connector:sumscope-data": {
      "url": "https://data-api.qeubee.cn/sumscope/common/mcp/stream",
      "type": "streamableHttp",
      "headers": {
        "X-Access-Key": "${X_ACCESS_KEY}"
      },
      "timeout": 30000,
      "disabled": true
    },
    "connector:baixiao-mcp": {
      "type": "streamableHttp",
      "url": "https://mcp.know-pa.cn/mcp",
      "headers": {
        "Authorization": "***REDACTED***"
      },
      "timeout": 30000,
      "disabled": true
    },
    "connector:jinshouzhi": {
      "type": "streamableHttp",
      "url": "https://ad-goldfinger.app.fitgroup-fat.com/mcp",
      "timeout": 30000,
      "disabled": true
    },
    "connector:gfsecurities": {
      "type": "streamableHttp",
      "url": "https://mcp-api.gf.com.cn/server/mcp/gfzq/mcp",
      "timeout": 30000,
      "headers": {
        "x-gf-channel": "workbuddy-area"
      },
      "disabled": true
    },
    "connector:infimind-ecommerce-content": {
      "type": "streamableHttp",
      "url": "https://imiva.ecpro.com/mcp/workbuddy",
      "disabled": true
    },
    "connector:polymas-workbuddy-pre": {
      "type": "streamableHttp",
      "url": "https://pre-agent-assistant.polymas.com/ai-agent/api/workbuddy/mcp/server",
      "timeout": 30000,
      "disabled": true
    },
    "connector:neo-eakey": {
      "type": "streamableHttp",
      "url": "https://buddy-ai.xiaoshouyi.com/mcp",
      "disabled": true
    },
    "connector:biobuddy": {
      "type": "streamableHttp",
      "url": "https://ai4s.tencent.com/biobuddy/mcp",
      "timeout": 30000,
      "disabled": true
    },
    "connector:wm-weight-manage": {
      "type": "streamableHttp",
      "url": "https://ichoice.myweimai.com/weimai-gpt/mcp",
      "timeout": 30000,
      "disabled": true
    },
    "connector:paper-retrieval": {
      "type": "streamableHttp",
      "url": "https://ai-research.dazd.cn/api/paperRetrieval/mcp",
      "timeout": 30000,
      "disabled": true
    },
    "connector:today-watermark-camera": {
      "type": "streamableHttp",
      "url": "https://workbuddy.xhey.top/workbuddy-adapter/mcp",
      "timeout": 60000,
      "disabled": true
    },
    "connector:xmed-figure-mcp": {
      "type": "streamableHttp",
      "url": "https://x-med-kyy-mcp.dazd.cn/kyy_visualization_mcp",
      "timeout": 30000,
      "disabled": true
    },
    "connector:aimoderator": {
      "type": "streamableHttp",
      "url": "https://aimoderator.cn/api/mcp",
      "disabled": true
    },
    "connector:tencent-map-guide": {
      "url": "https://mcp.map.qq.com/mcpgw/oauth/toolgroup",
      "type": "streamableHttp",
      "headers": {
        "McpGw-Tools-ID": "500038"
      },
      "timeout": 30000,
      "disabled": true
    },
    "connector:deeplink": {
      "type": "streamableHttp",
      "url": "https://mcp.dichanai.com/mcp-server",
      "headers": {
        "Authorization": "***REDACTED***"
      },
      "timeout": 600000,
      "disabled": true
    },
    "connector:dramabuddy": {
      "type": "streamableHttp",
      "url": "https://aicomic.yuewen.com/mcp",
      "timeout": 30000,
      "disabled": true
    },
    "connector:hanyi-fonts": {
      "type": "streamableHttp",
      "url": "https://hanyi-mcp.hellofont.cn/mcp",
      "timeout": 30000,
      "disabled": true
    },
    "connector:myunker-mcp": {
      "type": "streamableHttp",
      "url": "https://mcp.myscrm.cn/myy-mcp-server/mcp",
      "disabled": true
    },
    "connector:iyiou-connector": {
      "type": "streamableHttp",
      "url": "https://mcp.iyiou.com/data",
      "headers": {
        "X-Client-Id": "${CLIENT_ID}",
        "X-Client-Secret": "***REDACTED***"
      },
      "timeout": 60000,
      "disabled": true
    },
    "connector:intco-ai-platform": {
      "type": "streamableHttp",
      "url": "https://ai-platform.intcomedical.com.cn:11443/agt_c8c1aaea4a564b0eb1878929dfbf37d2/mcp",
      "timeout": 30000,
      "disabled": true
    },
    "connector:laiye-adp": {
      "command": "npx",
      "args": [
        "-y",
        "@laiye-adp/mcp"
      ],
      "env": {
        "ADP_API_KEY": "***REDACTED***"
      },
      "disabled": true
    },
    "connector:magic-agent-token": "***REDACTED***",
    "connector:zw3d-mcp": {
      "type": "stdio",
      "command": "npx",
      "args": [
        "-y",
        "zw3d-mcp"
      ],
      "timeout": 60000,
      "runtime": {
        "type": "node",
        "version": ">=16"
      },
      "disabled": true
    },
    "connector:zwcad-mcp": {
      "type": "stdio",
      "command": "uvx",
      "args": [
        "zwcad-mcp"
      ],
      "env": {
        "PYTHONUTF8": "1",
        "UV_DEFAULT_INDEX": "https://pypi.tuna.tsinghua.edu.cn/simple"
      },
      "timeout": 60000,
      "disabled": true
    },
    "connector:wscnmcp-token": "***REDACTED***",
    "connector:aidd-saas": {
      "type": "streamableHttp",
      "url": "https://aidd-saas.txfc.cloud/mcp",
      "disabled": true
    },
    "connector:tencent-yaoxiang-bi": {
      "type": "streamableHttp",
      "url": "https://data.eyao.qq.com/mcp",
      "timeout": 30000,
      "disabled": true
    },
    "connector:primematrix-company": {
      "type": "streamableHttp",
      "url": "https://mcp.yidian.cn/mcp/company",
      "headers": {
        "Authorization": "***REDACTED***"
      },
      "timeout": 30000,
      "disabled": true
    },
    "connector:es": {
      "url": "https://tcmcpserver.cloud.tencent.com/es/mcp",
      "type": "streamable-http",
      "disabled": true
    },
    "connector:aiclass-teaching": {
      "type": "streamableHttp",
      "url": "https://aiclass.qq.com/mcp",
      "timeout": 30000,
      "disabled": true
    },
    "connector:yunzhi-mcp": {
      "type": "streamableHttp",
      "url": "https://mcp.yz168.cc/mcp/",
      "headers": {
        "SiteID": "${SITE_ID}",
        "Authorization": "***REDACTED***"
      },
      "disabled": true
    },
    "connector:cloudmall-operations": {
      "type": "streamableHttp",
      "url": "https://admin.rmall-solution.com/mcp",
      "timeout": 30000,
      "disabled": true
    },
    "connector:variflight-mcp": {
      "type": "streamableHttp",
      "url": "https://c-gw.variflight.com/chat_message/mcp/api",
      "headers": {
        "Authorization": "***REDACTED***"
      },
      "timeout": 120000,
      "disabledTools": [
        "getUserInfo",
        "queryUserTripStatsInner"
      ],
      "disabled": true
    },
    "connector:sugon-springscholar-agent": {
      "type": "streamableHttp",
      "url": "http://223.113.240.17:30504/mcp",
      "timeout": 200000,
      "disabled": true
    },
    "connector:xmind": {
      "type": "streamableHttp",
      "url": "https://app.xmind.cn/api/mcp",
      "timeout": 30000,
      "disabled": true
    },
    "connector:jufa-mcp-server": {
      "type": "stdio",
      "command": "npx",
      "args": [
        "-y",
        "jufa-mcp-server@latest"
      ],
      "env": {
        "JUFA_API_KEY": "***REDACTED***"
      },
      "runtime": {
        "type": "node",
        "version": ">=20"
      },
      "timeout": 120000,
      "disabled": true
    },
    "connector:emes-ai": {
      "type": "streamableHttp",
      "url": "https://amos-dev.digihua.com:14000/mcp-platform/mcp/oauth/emes-ai",
      "timeout": 30000,
      "disabled": true
    }
  }
}