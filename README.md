# HuabSmart Skills

> 一个面向 AI 能力资产的开放仓库：发现、整理并复用 Skill、Prompt、Agent、MCP、Workflow 与知识文件。

- 在线目录：[skills.huabsmart.cn](https://skills.huabsmart.cn)
- 项目仓库：[github.com/HuabSmart-cn/skills](https://github.com/HuabSmart-cn/skills)
- 更新记录：[Commits](https://github.com/HuabSmart-cn/skills/commits/main)
- 问题与建议：[Issues](https://github.com/HuabSmart-cn/skills/issues)

## 项目简介

AI 能力散落在不同平台、社区和代码仓库中，寻找、比较和复用它们往往比使用本身更费时间。HuabSmart Skills 将这些可公开分享的能力资产整理为统一目录，提供可搜索的元数据、分类、标签、详情预览与原始文件入口。

这不是一个运行时框架，也不会替你安装或执行第三方代码。仓库只保存公开的能力元数据与文件，方便个人开发者、团队和其他工具按需取用。网站前端和部署实现不属于本仓库。

## 主要功能

- 按类型、平台、领域和标签组织能力资产
- 为每项能力提供可检索的公开元数据
- 保留能力说明、目录结构和附属文件
- 为每项能力提供稳定的仓库内路径
- 便于其他目录、工具和应用按需读取与打包

## 仓库结构

```text
.
├── manifest.json    # 可检索的公开元数据
└── skills/          # 按来源与类型组织的能力文件
```

`manifest.json` 描述公开能力资产，`skills/` 保存对应文件。网站只是读取这些公开数据的一个使用界面，源码不在本仓库中。

## Capability Registry（迁移中）

仓库正在增加 `registry/` 作为机器可读的控制面，用来声明依赖、运行条件、权限、失败语义、来源、生命周期和验证状态。它不会改变本仓库“目录而非 Runtime”的边界：**被收录不等于已安装、可运行、已真实调用或已验证**。历史资产在未有真实验证凭据前会保持 `unverified`。

规范、状态定义和迁移原则见 [docs/capability-registry.md](docs/capability-registry.md)。

跨包调用的候选关系由 `registry/dependency-candidates.json` 记录；下载服务可用 sidecar 将它随单个资产包提供，不改写第三方原文。

## 许可与第三方资产

根目录 [LICENSE](LICENSE) 中的 Apache-2.0 仅适用于 HuabSmart 原创的 Registry、Schema、工具、CI 配置和文档；具体范围见 [NOTICE](NOTICE)。仓库内第三方 Skill、Prompt、Agent、MCP 配置、脚本和附属文件不因收录而被重新许可，仍以原作者的版权、署名和 License 为准。License 或来源未确认时，本仓库不授予该资产的再利用许可。

### 官方能力搜索目录

下载后的 Skill 如需寻找协同能力，应只使用本仓库维护的在线目录，而不将整份目录复制进 ZIP：

- 供 Agent / 工具读取的 JSON：[search-index.json](https://raw.githubusercontent.com/HuabSmart-cn/skills/main/registry/search-index.json)
- 供用户浏览的 GitHub 页面：[search-index.json](https://github.com/HuabSmart-cn/skills/blob/main/registry/search-index.json)

目录为每个资产提供唯一 `assetId`、名称、简介、标签、平台、类型和源路径。名称匹配唯一时只能作为可推荐候选；名称重复或不确定时必须展示差异并等待用户选择。只有用户明确要求“一起安装”后，Agent 才可按其当前 Runtime 的官方方式继续安装；找不到时必须报告缺失，不能模拟结果。

## 参与贡献

欢迎提交新的公开能力、元数据修正、界面改进和文档改进。提交前请确认：

1. 内容可以公开分发，并符合原作者的许可与署名要求。
2. 不包含密码、令牌、私钥、个人信息、本机绝对路径或内部配置。
3. 不上传缓存、构建产物、私有数据和与能力本身无关的过程文件。
4. 能力中的脚本、提示词和外部链接已经过基本审阅，并在必要处注明风险。

请通过 [Issues](https://github.com/HuabSmart-cn/skills/issues) 报告问题，或提交 Pull Request。

## 安全与内容说明

仓库只收录公开可分享的能力资产。第三方 Skill、Prompt、Agent 和脚本仍应在使用前自行审阅；目录收录不代表对其准确性、安全性或适用性作出保证。发现疑似敏感信息或版权问题，请通过 Issues 联系维护者。

## 愿景

我们正在收集这个时代最值得留下的 AI 能力。你不必从零开始，全球优秀的 AI 范式，都可以成为你的下一种能力。
