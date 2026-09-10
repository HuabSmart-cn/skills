# QoderWake 自演进模式

基于 CLI 的自动化演进模式，使数字员工能够自主提升能力、积累经验、响应外部事件。

## 模式一：定时回报模式

通过 automation 创建定时任务，waker 可以周期性地拉取外部任务源并自动处理。

### 场景

- 定时代码审查
- 自动修复外部平台上拉取到的问题单
- 周期性项目巡检

### 实现步骤

```bash
# 1. 查看 schedule 创建命令参数
qoderwake automation create schedule --help

# 2. 创建定时任务。必须带 schedule 子命令；不要把参数传给父命令 qoderwake automation create。
# automation create schedule 不支持 --format / --json，使用默认输出解析结果。
qoderwake automation create schedule \
  --waker-id <wakerId> \
  --project-id <projectId> \
  --name "daily-routine" \
  --schedule-type cron \
  --cron "0 9 * * *" \
  --cron-preset daily \
  --timezone Asia/Shanghai \
  --prompt "请处理该任务，完成后输出总结"

# 3. 验证拉取配置
qoderwake automation test-pull --waker-id <wakerId> --automation-id <automationId>

# 4. 监控执行情况
qoderwake automation detail --waker-id <wakerId> --automation-id <automationId>

# 5. 诊断异常 run
qoderwake automation inspect run --worker-id <wakerId> --run-id <runId> --format timeline

# 6. 查看执行产出
qoderwake session artifacts --session-id <sessionId> --include-file-changes
```

### 调优

```bash
# 更新 prompt 以优化执行质量
qoderwake automation update --waker-id <wakerId> --automation-id <automationId> \
  --prompt-file ./improved-prompt.md

# 调整定时频率（原地更新，不要重新创建任务）
qoderwake automation update --waker-id <wakerId> --automation-id <automationId> \
  --schedule-type cron --cron "0 * * * *" --cron-preset hourly

# 暂停任务
qoderwake automation update --waker-id <wakerId> --automation-id <automationId> \
  --enabled false
```

---

## 模式二：能力自扩展模式

通过 skill 管理，waker 可以动态添加、更新、回滚自身技能。

### 场景

- 根据任务需求动态加载技能
- 技能迭代后自动升级
- 出现回归时快速回滚

### 实现步骤

```bash
# 1. 注册新技能
qoderwake skill add --waker-id <wakerId> \
  --skill-id my-new-skill \
  --name "My New Skill" \
  --description "一个新的自定义技能"

# 2. 上传技能包（新版本）
qoderwake skill upload ./my-new-skill-v1.0.0.zip --waker-id <wakerId>

# 3. 查看版本历史
qoderwake skill versions --waker-id <wakerId> --skill-id my-new-skill

# 4. 对比版本差异（检查变更是否符合预期）
qoderwake skill diff --waker-id <wakerId> --skill-id my-new-skill --version v_002

# 5. 如果新版本有问题，回滚
qoderwake skill rollback --waker-id <wakerId> --skill-id my-new-skill \
  --to v_001 --reason "v2 引入回归"

# 6. 安装到本地以立即生效
qoderwake skill install --waker-id <wakerId> --skill-id my-new-skill

# 7. 临时禁用有问题的技能
qoderwake skill toggle --waker-id <wakerId> --skill-id my-new-skill --enabled false
```

### MCP 工具扩展

```bash
# 添加新的 MCP 工具服务器
qoderwake mcp add --waker-id <wakerId> \
  --name code-search \
  --http-url https://search.example.com/mcp \
  --transport http \
  --header "Authorization: ***REDACTED***

# 刷新工具列表
qoderwake mcp refresh-tools --waker-id <wakerId> --mcp-id <mcpId>

# 禁用不需要的 MCP
qoderwake mcp toggle --waker-id <wakerId> --mcp-id <mcpId> --enabled false
```

---

## 模式三：记忆自整理模式

通过 memory 管理，waker 可以积累和整理经验记忆，持续提升决策质量。

### 场景

- 会话后自动沉淀经验
- 定期整理零散记忆为结构化知识
- 记忆版本管理和回滚

### 实现步骤

```bash
# 1. 查看当前记忆状态
qoderwake memory show --waker-id <wakerId> --view all

# 2. 触发 dream（预览候选记忆合并）
qoderwake memory dream --waker-id <wakerId> --mode preview

# 3. 确认候选无误后应用
qoderwake memory dream --waker-id <wakerId> --mode apply \
  --preview-run-id <previewRunId>

# 4. 检查 dream 效果
qoderwake memory show --waker-id <wakerId> --view long_term

# 5. 查看生命周期统计
qoderwake memory lifecycle inspect --waker-id <wakerId>
```

### 记忆保护和恢复

```bash
# 创建快照（操作前备份）
qoderwake memory snapshot --waker-id <wakerId>

# 查看版本历史
qoderwake memory versions --waker-id <wakerId>

# 对比两个快照的差异
qoderwake memory diff --waker-id <wakerId> --from <snap1> --to <snap2>

# 回滚指定文件到历史版本（先 dry-run 预览）
qoderwake memory rollback --waker-id <wakerId> \
  --snapshot-id <snapId> --path topics/coding-patterns.md

# 确认无误后实际回滚
qoderwake memory rollback --waker-id <wakerId> \
  --snapshot-id <snapId> --path topics/coding-patterns.md --apply
```

### 精确更新记忆

```bash
# 更新指定文本片段
qoderwake memory update --waker-id <wakerId> \
  --path topics/best-practices.md \
  --old-text "旧的最佳实践描述" \
  --content "新的最佳实践描述" \
  --reason "根据最新经验更新"

# 删除过时记忆
qoderwake memory remove --waker-id <wakerId> \
  --path topics/deprecated.md \
  --old-text "已过时的内容" \
  --reason "该模式已废弃"
```

### 记忆导入导出

```bash
# 导出记忆（用于迁移或备份）
qoderwake memory export --waker-id <wakerId> \
  --out-path ./memory-backup.tar.gz \
  --include-sessions --include-versions

# 导入记忆（先预览）
qoderwake memory import --waker-id <wakerId> \
  --package-path ./memory-backup.tar.gz

# 确认后实际导入
qoderwake memory import --waker-id <wakerId> \
  --package-path ./memory-backup.tar.gz --apply
```

---

## 模式四：项目感知模式

通过 project 管理，waker 可以动态管理工作上下文，感知多项目的代码和配置。

### 场景

- 管理多个代码仓库
- 项目初始化和索引
- 动态切换工作上下文

### 实现步骤

```bash
# 1. 创建项目（本地路径）
qoderwake project create --waker-id <wakerId> \
  --name "backend-api" \
  --path ./projects/backend \
  --initializer-command "npm install" \
  --initializer-timeout 120

# 2. 创建项目（Git 仓库）
qoderwake project create --waker-id <wakerId> \
  --name "frontend-app" \
  --git-url https://github.com/org/frontend.git \
  --local-path ./projects/frontend

# 3. 触发 onboarding（让 waker 理解项目）
qoderwake project onboard --waker-id <wakerId> --project-id <projectId>

# 4. 查看 waker 下所有项目
qoderwake project list --waker-id <wakerId>

# 5. 创建项目绑定的会话
qoderwake session create --waker-id <wakerId> \
  --title "Review PR" \
  --message "请审查最近的 PR" \
  --project-id <projectId>

# 6. 项目级记忆管理
qoderwake memory show --waker-id <wakerId> \
  --scope project --project-id <projectId> --view all

qoderwake memory dream --waker-id <wakerId> \
  --scope project --project-id <projectId> --mode preview
```

### 项目配置更新

```bash
# 更新项目 Git URL
qoderwake project update --waker-id <wakerId> --project-id <projectId> \
  --git-url https://github.com/org/new-repo.git

# 更新初始化命令
qoderwake project update --waker-id <wakerId> --project-id <projectId> \
  --initializer-command "bun install && bun run build"

# 删除不再需要的项目
qoderwake project delete --waker-id <wakerId> --project-id <projectId>
```

---

## 模式五：Waker 导出与复制模式

通过 waker export/create，可以将配置好的数字员工打包分发。

在用户 session 中执行 `waker create` 前必须二次确认：该命令没有 `--waker-id` / `--worker-id`，会创建一个独立的新数字员工，而不是修改当前员工配置。

### 场景

- 创建标准化的数字员工模板
- 在团队间共享 waker 配置
- 备份和恢复 waker

### 实现步骤

```bash
# 1. 导出已配置好的 waker
qoderwake waker export --waker-id <wakerId> --out ./waker-template.zip

# 2. 在其他环境中用 zip 包创建
# 用户 session 内执行前先确认新员工名称/模板来源/影响范围
qoderwake waker create --template-zip ./waker-template.zip

# 3. 或者用 JSON 模板创建
qoderwake waker create --template-json ./template.json --name "clone-waker"
```

---

## 组合模式示例：完整的自动化开发流程

```bash
# 1. 创建 waker
# 用户 session 内执行前先确认新员工名称/模板来源/影响范围
qoderwake waker create --template-id default --name "dev-bot" --json
# 记录 wakerId

# 2. 配置项目
qoderwake project create --waker-id <wakerId> --name "main-repo" \
  --path /path/to/repo --json
# 记录 projectId

# 3. onboard 项目
qoderwake project onboard --waker-id <wakerId> --project-id <projectId>

# 4. 添加所需技能
qoderwake skill upload ./code-review-skill.zip --waker-id <wakerId>
qoderwake skill upload ./test-writing-skill.zip --waker-id <wakerId>

# 5. 添加 MCP 工具
qoderwake mcp add --waker-id <wakerId> --name github \
  --command npx --args "-y,@modelcontextprotocol/server-github" \
  --env '{"GITHUB_TOKEN":***REDACTED***

# 6. 设置自动化任务
qoderwake automation create schedule --help
qoderwake automation create schedule \
  --waker-id <wakerId> --project-id <projectId> \
  --name "auto-routine" \
  --schedule-type cron \
  --cron "0 9 * * *" \
  --cron-preset daily \
  --timezone Asia/Shanghai \
  --prompt "请按例行公事处理该任务"

# 7. 定期触发 dream 整理记忆
qoderwake memory dream --waker-id <wakerId> --mode preview
qoderwake memory dream --waker-id <wakerId> --mode apply \
  --preview-run-id <runId>
```
