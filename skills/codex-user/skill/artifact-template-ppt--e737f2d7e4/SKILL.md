---
name: artifact-template-ppt
description: "Create a presentation using the 大模型教案PPT模板 template and its retained reference file. Use when the user selects this template, names 大模型教案PPT模板, or explicitly invokes $artifact-template-ppt. 用高级感浅灰蓝四页信息板制作教案PPT，适合按国内、国外、开源、其它等分类介绍主题，并保留模板排版、导航栏、来源说明和简短模型卡片风格。"
---

# 大模型教案PPT模板

Create a new presentation from this template. Keep the reference file unchanged.

## Workflow

1. Read `artifact-template.json` and resolve its paths relative to this skill directory.
2. Load [@presentations](plugin://presentations@openai-primary-runtime) and invoke its reference/template workflow with the retained file.
3. Treat the user's prompt and available sources as the content input. Do not invent facts merely to fill a template slot.
4. Clone or import the reference instead of replacing its visual system with generic defaults.
5. Render and verify the finished presentation, then return the final artifact.

## Fidelity

Preserve source slides, layouts, masters, typography, geometry, images, charts, tables, and recurring slide chrome.

User instructions control requested content and explicit deviations. The retained reference controls layout and formatting where the user has not requested a change.
