---
name: petdex-pets
description: >-
  Help users discover and install desktop pets through the third-party Petdex
  CLI when they ask to find, recommend, add, or install a new desktop pet.
  Obtain confirmation before running third-party CLI code or changing files.
  Do not use for ordinary desktop-pet settings changes or switching among pets
  that are already installed.
descriptionZh: >-
  当用户希望寻找、推荐、添加或安装新桌宠，或明确提到 Petdex、petdev 时使用；通过第三方
  Petdex CLI 完成安装。运行第三方 CLI 或写入本地文件前必须取得确认。普通桌宠开关、尺寸
  和已有宠物切换不要调用本 Skill。
---

# Petdex Pets

帮助用户通过第三方 Petdex CLI 发现并安装 Qoder 可读取的桌宠包。`petdev` 按用户对 `Petdex` 的误写处理，但执行命令始终使用 npm 包 `petdex`。

Qoder 仅提供本地宠物包兼容与安装指引，不内置、分发或审核 Petdex CLI 及其宠物素材。Petdex 与宠物素材均来自第三方；不要把 Petdex 的收录或审核状态描述为 Qoder 的推荐、授权或版权保证。

## 核心边界

- 第一次运行 `npx` 前，说明它会下载并执行第三方 npm 包、访问网络并可能写入用户目录；等待用户明确确认。
- 查询或推荐不代表安装授权。安装前再次确认宠物名称和 slug；一次只安装用户选定的宠物。
- 不把 Petdex 宠物、Logo、代码或其他素材复制进 Qoder、当前仓库或 Skill。
- 不自行抓取网页、拼接资源下载地址或直接下载 spritesheet；只使用官方 CLI 提供的命令。
- 不安装 Hook、不修改其他 Agent 配置、不启动 Petdex Desktop，也不上传或提交用户本地宠物，除非用户另行明确要求。
- 不删除或覆盖已有宠物。目标目录已存在时，先报告现状并询问用户如何处理。

## 工作流

1. 明确用户目标。用户已经给出 slug 时直接进入核对；用户只描述偏好时，询问一到两个真正影响推荐的条件，例如动物类型或风格。
2. 在获得运行第三方 CLI 的确认后，使用 `npx --yes petdex@latest list` 获取官方候选。不要虚构不存在的宠物、slug、评分或授权信息。
3. 展示不超过五个匹配候选，包含官方返回的名称、slug 和必要署名。
4. 用户选择后，明确将执行 `npx --yes petdex@latest install <slug>`，并等待安装确认。slug 必须来自当前查询结果或经 CLI 核实，作为单独参数传递，不能拼接额外 shell 语法。
5. 安装完成后验证 `~/.petdex/pets/<slug>/pet.json` 存在，并且同目录存在且仅存在一个 `spritesheet.webp` 或 `spritesheet.png`。验证失败时报告实际缺失项和 CLI 错误，不把失败伪装成成功。
6. 成功后告诉用户：打开 Qoder 的桌宠设置，刷新已安装宠物，然后选择新宠物。不要声称已切换，除非当前环境确实提供并成功调用了具名切换能力。

## 失败与恢复

- `npx`、网络、npm 或 Petdex CLI 失败时，保留关键原始错误和退出状态，说明失败发生在哪一步。
- 不用重试循环掩盖失败。只有明显的瞬时网络错误才可在用户同意后重试一次。
- 如果 `~/.petdex/pets/<slug>` 不存在但 `~/.codex/pets/<slug>` 存在，说明 Petdex CLI 的兼容副本存在，但 Qoder 当前只读取 `~/.petdex/pets`；不要擅自复制目录。
- 用户拒绝运行第三方 CLI 时，给出可自行执行的官方命令并停止，不继续下载或安装。

## 完成信息

安装完成后简要报告安装的宠物、验证过的 Petdex 目录，以及用户在 Qoder 中完成选择的下一步。不要输出缓存、认证信息或无关环境数据。
