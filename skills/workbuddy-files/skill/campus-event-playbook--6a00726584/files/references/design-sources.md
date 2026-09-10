# 设计来源与使用限制

核验日期：2026-08-22

以下资料仅用于借鉴工作流、字段和交互设计，不作为学校政策、安全标准或事实依据。

| 来源 | 类型 | 借鉴内容 | 使用限制 | 风险等级 |
|---|---|---|---|---|
| Event Planner Pro, https://openskillindex.com/skills/openclaw-skills-event-planner-pro | 社区 Skill 索引，MIT 标注 | 活动 Brief、倒排计划、Run of Show、就绪检查、复盘结构 | 偏商业活动，预算、ROI、赞助和海外平台规则不适合直接照搬 | 中 |
| Event Planner OS, https://clawhub.ai/chris-openclaw/event-planner-os | 社区 Skill 页面 | 活动状态、任务、人员、预算和收尾的持续管理思路 | 页面声明能力与数据模型存在不完全匹配，文件持久化和提醒能力取决于运行环境 | 中 |
| Event Management, https://www.skillmd.ai/zh/how-to-build/event-management-1 | 社区 Skill 展示页 | 策略、物流、宣传、准备、执行、活动后跟进的阶段结构 | 偏开发者和商业活动，金额、周期和指标仅能作设计参考 | 中 |
| Project Management, https://www.skillmd.ai/how-to-build/project-management-6 | 社区 Skill 展示页 | WBS、RACI、RAID、关键路径、状态同步 | 软件项目术语需简化为学生组织可理解的结构 | 中 |
| Risk Register, https://skillmd.ai/zh/how-to-build/risk-register-1 | 社区 Skill 展示页 | 概率、影响、策略、负责人和期限的风险登记方法 | PMBOK 风格较重，不替代校方安全评估 | 中 |
| Social Media Engine, https://openclawai.io/skills/skill/social-media-engine | 社区 Skill 页面 | 内容日历、渠道适配、先审后发、数据复盘 | 面向海外社交平台，自动发布依赖外部服务；本 Skill 只保留草稿和确认机制 | 中 |
| Volunteer Coordinator, https://skillmd.ai/pt/how-to-build/volunteer-coordinator | 社区 Skill 展示页 | 岗位卡、技能匹配、活动前确认、候补、培训和反馈 | 长期志愿者留存指标和海外工具不适合一次性校园活动 | 中 |

## 内置事实性资料来源

以下资料已内化为包内文件，作为事实性依据使用。引用时以官方原文为准，并按下表风险等级控制使用方式。

| 包内文件 | 来源 | 适用范围 | 风险等级 |
|---|---|---|---|
| references/regulations-quick-reference.md | 《大型群众性活动安全管理条例》（国务院令第505号，2007-10-01 施行，中国政府网/应急管理部官网）；《高校学生社团建设管理办法》（教党〔2020〕13号，教育部党组、共青团中央印发） | 全国性法规条款速查：许可门槛、时限、材料、罚则；社团活动合规基线 | 高：条款引用错误后果严重，正式引用必须对照官方原文；注意条例后续修订 |
| references/campus-approval-common-pattern.md | 多校官网公开管理规定：郑州轻工业大学、湖南涉外经济学院、扬州大学广陵学院、邵阳学院、南京工业职业技术大学、山西中医药大学、枣庄职业（技师）学院 | 审批共性模式预判：规模分档、时间窗、材料组合、审批链、宣传与经费纪律 | 中：只用于预判和提问，任何具体数字必须标注待官方核验，不得写成本校规定 |
| references/campus-safety-and-privacy.md（参加者构成、合同财务声誉两节） | University of Oregon / United Educators《Risk Management for Campus Student Events》；UNC Charlotte 学生组织风险管理手册（均经本土化改写，非翻译照搬） | 风险识别盲区清单：参加者构成、合同责任、财务内控、声誉风险 | 中：海外制度背景，仅作检查项提示，不作中国校园制度依据 |
| assets/emergency-plan-skeleton.md | 山东省高校安全保卫协会预案要素分析；义乌工商职业技术学院、上海体育大学、成都大学、西南医科大学公开应急预案的共性结构 | 应急预案骨架：组织指挥、工作组分工、处置流程、信息报告 | 高：仅为起草底稿，不是经批准的正式预案，必须经校方责任主体确认 |

外部开源项目（MLH Hackathon Organizer Guide 等）仅用于研究工作流设计，未复制内容进包。

## 内部设计规则

以下内容属于专家经验规则：

- 首发聚焦招新、破冰、迎新和小型活动。
- 一次只询问影响当前判断的关键问题。
- 每项关键任务只有一个最终负责人。
- 已发生问题与潜在风险分开记录。
- 风险判断记录事实依据、证据状态、来源和待核验事项。
- 现场流程以 Run of Show 作为统一执行依据。
- 未提供就绪数据时标记为未评估，不推断为缺失或阻断。
- 关键审批、安全和责任主体缺失时给出补齐、降级、延期或转介方案。
- 对外发送、发布、提交和联系人员前取得明确确认。

这些规则用于稳定工作方式，不代表任何学校的正式制度。
