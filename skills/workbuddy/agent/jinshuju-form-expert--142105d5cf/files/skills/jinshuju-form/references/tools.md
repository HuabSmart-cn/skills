# 金数据 MCP 工具完整参考

本文档列出当前对外开放的 **30 个 MCP 工具**，每个工具包含一句话用途、输入参数、输出字段、所需 OAuth scope 和常见错误。

> 工具的实际暴露名可能带客户端前缀（如 `mcp__jinshuju__list_forms`），按客户端实际名字调用即可，本文统一用裸名。

## 索引

| 类别 | 工具 |
| ---- | ---- |
| **Forms** | [`list_forms`](#list_forms) · [`list_my_submitted_forms`](#list_my_submitted_forms) · [`list_folders`](#list_folders) · [`create_folder`](#create_folder) · [`get_form`](#get_form) · [`get_field_rules`](#get_field_rules) · [`check_field_data`](#check_field_data) · [`create_form`](#create_form) · [`copy_form`](#copy_form) · [`move_form`](#move_form) · [`edit_form`](#edit_form) · [`edit_field_rules`](#edit_field_rules) · [`edit_theme`](#edit_theme) |
| **考试 / 测评** | [`create_exam_form`](#create_exam_form) · [`edit_exam_form`](#edit_exam_form) · [`create_evaluation_form`](#create_evaluation_form) · [`edit_evaluation_form`](#edit_evaluation_form) |
| **上传** | [`prepare_form_image_upload`](#prepare_form_image_upload) · [`prepare_entry_attachment_upload`](#prepare_entry_attachment_upload) |
| **Entries** | [`list_entries`](#list_entries) · [`list_my_submitted_entries`](#list_my_submitted_entries) · [`get_entry`](#get_entry) · [`create_entry`](#create_entry) · [`create_entries`](#create_entries) · [`update_entry`](#update_entry) · [`patch_entries`](#patch_entries) · [`delete_entry`](#delete_entry) |
| **Account** | [`get_current_user`](#get_current_user) · [`get_current_billing_account`](#get_current_billing_account) · [`list_account_users`](#list_account_users) |

## OAuth Scope 速查

| Scope | 涵盖工具 |
| ----- | -------- |
| `forms` | list_forms / list_my_submitted_forms / list_folders / create_folder / get_form / get_field_rules / check_field_data / create_form / copy_form / move_form / edit_form / edit_field_rules / create_exam_form / edit_exam_form / create_evaluation_form / edit_evaluation_form / prepare_form_image_upload（type=field_choice） |
| `form_setting` | edit_theme / prepare_form_image_upload（type=header） |
| `read_entries` | list_entries / list_my_submitted_entries / get_entry |
| `write_entries` | create_entry / create_entries / update_entry / patch_entries / delete_entry / prepare_entry_attachment_upload |
| `user` | get_current_user |
| `billing_account` | get_current_billing_account / list_account_users |

> Basic Auth / JWT 模式下不受 scope 限制；OAuth 模式下被授权的 scope 决定可调用工具集合，未授权 scope 调用会报 `Insufficient scope: <name> required`。

---

# Forms

## list_forms

**用途**：列出当前凭证名下能访问的表单（自己创建的 + 被分享协作的）。

**Scope**：`forms`

**输入**

| 参数 | 类型 | 必填 | 说明 |
| ---- | ---- | ---- | ---- |
| `name` | string | 否 | 表单名关键字（**正则匹配，大小写不敏感**），如 `"survey"` 能匹配 `Survey A` |
| `next` | string | 否 | 翻页游标（上一次响应里的 `next` 字段） |
| `limit` | integer | 否 | 默认 50；越界自动截断 |

**输出**

```json
{
  "total": 3,
  "count": 3,
  "data": [
    {
      "name": "2026 春季发布会报名表",
      "description": "活动报名收集",
      "token": "abCdEf",
      "scene": "registration",
      "form_url": "https://jinshuju.net/f/abCdEf",
      "created_at": "2026-04-20T10:00:00+08:00",
      "entries_count": 128
    }
  ],
  "next": null
}
```

**常见错误**

- `Insufficient scope: forms required` — OAuth 未授权 `forms` scope

---

## list_my_submitted_forms

**用途**：列出当前用户作为**填写者**提交过数据的表单（不一定是所有者），按最近提交时间倒序。用户模糊说"我填过的那张表单"时用这个。

**Scope**：`forms`

**输入**

| 参数 | 类型 | 必填 | 说明 |
| ---- | ---- | ---- | ---- |
| `next` | integer | 否 | 翻页偏移量（上次响应里的 `next`） |
| `limit` | integer | 否 | 默认 50，最大 50 |

**输出**

```json
{
  "total": 3,
  "count": 3,
  "data": [
    {
      "name": "2026 客户满意度调查",
      "description": "季度回访",
      "token": "abCdEf",
      "form_url": "https://jinshuju.net/f/abCdEf",
      "scene": "survey",
      "submitted_entries_count": 2,
      "last_submitted_at": "2026-06-20T10:00:00+08:00"
    }
  ],
  "next": null
}
```

> 排除快捷支付（quickpay）表单。别人拥有、你只是填写者的表单也会出现在这里。

**常见错误**

- `Insufficient scope: forms required`

---

## list_folders

**用途**：列出当前用户能管理的文件夹，**只为给 create_form / copy_form / move_form 拿 folder_token 用**。

**Scope**：`forms`

**输入**

| 参数 | 类型 | 必填 | 说明 |
| ---- | ---- | ---- | ---- |
| `limit` | integer | 否 | 默认 50，最大 100，越界自动截断 |

**输出**

```json
{
  "total": 4,
  "returned": 4,
  "data": [
    { "token": "FLD_a1b2", "name": "市场活动" },
    { "token": "FLD_c3d4", "name": "客户登记" }
  ]
}
```

> 别人的文件夹不会出现在结果里。返回字段没有 `id`，**只用 token**。

**常见错误**

- `Insufficient scope: forms required`

---

## create_folder

**用途**：新建一个文件夹，返回的 `token` 可作为 `folder_token` 传给 `create_form` / `copy_form` / `move_form`，把表单放进该文件夹。

**Scope**：`forms`

**输入**

| 参数 | 类型 | 必填 | 说明 |
| ---- | ---- | ---- | ---- |
| `name` | string | ✅ | 文件夹名称 |

**输出**

```json
{ "token": "FLD_e5f6", "name": "2026 市场活动" }
```

**常见错误**

- `Insufficient scope: forms required`

---

## get_form

**用途**：拿表单完整结构（字段 / 主题 / setting）。**调任何 entry 类工具前必先 get_form** 拿 `api_code`。

**Scope**：`forms`

**输入**

| 参数 | 类型 | 必填 | 说明 |
| ---- | ---- | ---- | ---- |
| `token` | string | ✅ | 表单 token **或** form id（数字 ID 也接受） |
| `include_theme` | bool | 否 | 是否返回 `theme`（页头 / 配色 / 字体等样式）。默认 `false` |
| `include_setting` | bool | 否 | 是否返回 `setting`（提交行为 / 关闭规则 / 通知规则 / 考试测评设置 / 字段显示规则）。默认 `false` |
| `include_field_rules` | bool | 否 | 是否返回字段显示规则 `field_rules`（每条带 0-based `index`，供 [`edit_field_rules`](#edit_field_rules) 精确改 / 删）。默认 `false`。也可用只读的 [`get_field_rules`](#get_field_rules) 单独取 |

**输出**

```json
{
  "name": "2026 春季发布会报名表",
  "token": "abCdEf",
  "description": "活动报名",
  "form_url": "https://jinshuju.net/f/abCdEf",
  "layout": "classic",
  "fields": [
    {
      "api_code": "field_1",
      "label": "姓名",
      "type": "NameField",
      "required": true,
      "private": false
    },
    {
      "api_code": "field_2",
      "label": "参会城市",
      "type": "DropDown",
      "required": true,
      "private": false,
      "choices": [
        { "value": "北京", "api_code": "city_bj" },
        { "value": "上海", "api_code": "city_sh" }
      ]
    },
    {
      "api_code": "field_3",
      "label": "评分",
      "type": "RatingField",
      "rating_max": 5
    },
    {
      "api_code": "field_4",
      "label": "费用明细",
      "type": "TableField",
      "init_row_length": 3,
      "dimensions": [
        { "api_code": "col_1", "label": "项目", "type": "TextField" },
        { "api_code": "col_2", "label": "金额", "type": "NumberField" }
      ]
    }
  ],
  "theme": {
    "primary_color": "#3B82F6",
    "header": { "type": "image", "has_header_image": true }
  },
  "setting": {
    "entry_submit_mode": "show_message",
    "success_message": "感谢报名！",
    "success_message_style": "text",
    "open_entry_action": "view",
    "show_serial_number_on_success": true,
    "manually_close_rule": null,
    "by_time_range_close_rule": { "start_time": "2026-05-01T09:00+08:00", "end_time": "2026-05-31T18:00+08:00" },
    "by_entries_close_rule": { "limit": 500 },
    "fill_frequency": { "fill_type": "repeatable", "condition": "by_ip", "cycle_period": "every_day", "limited_time": 3 },
    "password_required": false,
    "allowed_audience": "public",
    "notification_rules": [
      { "id": "...", "approach": "WXWORK", "url": "https://qyapi.weixin.qq.com/...", "content": "新报名：$(field_1)", "trigger_scope": "all_new", "enabled": true, "from_next": true }
    ]
  }
}
```

> ⚠️ **默认只返回核心信息**（`name` / `token` / `form_url` / `description` / `layout` / `fields`）。`theme` / `setting` / `field_rules` 三块体积大，默认**不返回**，需分别传 `include_theme` / `include_setting` / `include_field_rules=true` 才带上。只为拿字段结构（`api_code`）时保持默认即可。顶层 `layout` 恒返回：`classic`（经典式）/ `card`（分页式，一页一题）。
>
> 字段特有属性（如 `goods_items` / `reservation_items` / `associated_form_token` / `predefined_value` / `placeholder` / `range_min/max` / `precision` / `media_type` / `max_size` 等）按字段类型出现在对应 field 节点上。选项字段的 `choices[]` 中，「其他」选项（扩展输入）会带 `"is_other": true`，普通选项不带该键；预约字段 `daily_time_range_quotas` 的时刻以零填充字符串返回（`"09"` 而非 `9`）。
>
> 另外：传 `include_field_rules=true` 时返回顶层 `field_rules`（字段显示规则，每条带 0-based `index`；结构与增删改见 [`edit_field_rules`](#edit_field_rules)）；`include_setting=true` 时考试 / 测评表单还会返回 `setting.exam_setting` / `setting.evaluation_setting`（结构与 [`create_exam_form`](#create_exam_form) / [`create_evaluation_form`](#create_evaluation_form) 的同名入参对齐，题目字段带 `customized_type` 和按选项 value 序列化的 `answers`）——重写 answers / indicators 这类整体替换列表前，先用 get_form 读出现状。

**常见错误**

- `Form cannot be found` — token 错 / 表单不属于当前账号 / 没被分享
- `Insufficient scope: forms required`

---

## get_field_rules

**用途**：只读列出表单的字段显示规则，每条带 0-based `index`——改 / 删规则前用它（或 `get_form` 带 `include_field_rules=true`）拿到 `index`。返回内容与 `get_form(include_field_rules=true)` 的 `field_rules` 一致。

**Scope**：`forms`

**输入**

| 参数 | 类型 | 必填 | 说明 |
| ---- | ---- | ---- | ---- |
| `form_token` | string | ✅ | 表单 token 或 form id |

**输出**

```json
{
  "token": "abCdEf",
  "field_rules": [
    {
      "index": 0,
      "targets": ["field_5"],
      "targets_display_mode": "show",
      "operator": "or",
      "conditions": [
        { "trigger": "field_1", "comparator": "equal", "value": ["choice_A"] }
      ]
    }
  ]
}
```

**规则项字段**

| 字段 | 说明 |
| ---- | ---- |
| `index` | 该规则的 0-based 序号，`edit_field_rules` 的 update / remove 按它定位 |
| `targets` | 目标字段 api_code 列表；`targets_display_mode=show` 时必填，`abort` 时忽略。目标字段在表单顺序上必须位于触发字段**之后**，否则规则被静默丢弃；目标必须是**普通字段（`private=false`）**，`private=true` 的隐藏字段任何规则都显示不出来 |
| `targets_display_mode` | `show`（命中显示目标字段）/ `abort`（命中终止填写） |
| `operator` | 多条件组合 `and` / `or`，默认 `or` |
| `conditions[].trigger` | 触发字段 api_code |
| `conditions[].comparator` | **必须匹配触发字段类型**，否则该 `edit_field_rules` 调用被拒。选择类（单选 / 多选 / 下拉 / 级联 / 排序 / 预约 / 表单关联）用 `equal`（包含任一）/ `none_in`（都不包含）；评分 / NPS 用 `between`；文本类（文本 / 多行 / 邮箱 / 手机 / 座机 / 链接 / 身份证）用 `like` / `not_like`。省略时按类型取主 comparator：选择→`equal`、评分 / NPS→`between`、文本→`like` |
| `conditions[].value` | 按 comparator 取标量 / 数组 |

**常见错误**

- `Form cannot be found`
- `Insufficient scope: forms required`

---

## create_form

**用途**：从零创建一张表单。一次性指定 name + 字段列表 + 可选 setting + 可选 folder。

> ⚠️ 考试 / 测评场景不要用本工具：`scene` 枚举已移除 `exam` / `evaluation`，请改用 [`create_exam_form`](#create_exam_form) / [`create_evaluation_form`](#create_evaluation_form)（题目答案、计分只在专用工具里可用）。

**Scope**：`forms`

**输入**

| 参数 | 类型 | 必填 | 说明 |
| ---- | ---- | ---- | ---- |
| `name` | string | ✅ | 表单名 |
| `fields` | array  | ✅ | 字段列表，每项见下表 |
| `description` | string | 否 | 表单说明 |
| `scene` | enum | 否 | 表单场景：`form`（默认）/ `survey` / `registry` / `reservation` / `online_payment`。⚠️ `vote` / `customer_acquisition` 已移除且会被拒（新编辑器打不开），改用 `form` 场景 |
| `layout` | enum | 否 | 排版：`classic`（经典式，默认，所有题在一页滚动）/ `card`（分页式，一页一题、自动翻页 Typeform 风格）。用户要 分页式 / 卡片式 / 一页一题 / 自动翻页 时传 `card`——**不要用 PageBreak 拼**。`card` 仅 `form` / `survey` 场景生效，其他场景自动降级为 classic；且不支持这些字段类型（含则报错）：`PageBreak` `MatrixField` `MatrixScaleField` `TableField` `GoodsField` `ESignatureField` `FormAssociation` `MultipleBlanksField` `WidgetMap` `WidgetContact` `WidgetVideo` `WidgetButton` `WidgetMarquee` |
| `setting` | object | 否 | 初次创建的关键 setting（仅 `success_message` / `open_entry_action` / `open_entry_message` / `notification_rules`）。完整 setting 用 `edit_form` 配 |
| `folder_token` | string | 否 | 表单要放进的文件夹 token |

**fields[] 通用属性**

| 字段 | 类型 | 说明 |
| ---- | ---- | ---- |
| `type` | string | 字段类型，必须是 [39 种白名单](#字段类型白名单) 之一 |
| `label` | string | 字段标签 |
| `cid` | string | 客户端引用 id：每个新字段生成一个表单内唯一的短随机 token（6-8 位字母数字，**不能含 `.`**）。`api_code` 由后端生成、**不可自行指定**；同请求内 FormulaField 公式、测评维度等需要引用新字段时用 cid |
| `required` | bool | 是否必填，与 `private` 互斥 |
| `private` | bool | 是否隐藏，设 true 时 `required` 自动置 false |
| `unique` | bool | 不允许重复值。仅 `TextField` / `NameField` / `EmailField` / `MobileField` / `TelephoneField` / `IdCardField` / `LinkField` / `FormAssociation` 支持 |
| `notes` | string | 字段提示文案（SectionBreak 时是描述正文） |
| `choices` | array | 选项字段用：`[{ value, quota?, selected?, operand_value?, image_url?, image_upload_token?, sub_choices? }]`。`quota`（名额）**省略 = 不限量**（默认，绝大多数情况用这个）；正整数 = 该选项最多可被选中的份数，满额后选项展示但置灰不可选；`0` = 一开始就满、立即不可选（仅当你**故意**要一个"展示但禁用"的选项时才传 0）。**绝不要用 `0` 表示"不限量"**——那会让选项渲染出来却选不了；不限量就省略该字段。`selected: true` 设**默认选中**——RadioButton / DropDown / ImageRadioButton 仅一项生效，CheckBox / ImageCheckBox 可多项，CascadeDropDown 沿选中路径每级节点都设 `selected: true`。`operand_value`（选项赋值）配合字段 `calculable=true` 给每个选项赋数值，供 FormulaField 计算——开启 calculable 后**每个选项都必须给** `operand_value`；`image_upload_token` 见 [prepare_form_image_upload](#prepare_form_image_upload)。**图片选项（ImageRadioButton / ImageCheckBox）的 `value` 是选项文字标签、必填，且每项必须带 `image_upload_token` / `image_url` / `image_base64` 之一，否则被拒** |
| `choices_layout` | enum | 选项排列方式，仅 `RadioButton` / `CheckBox` / `ImageRadioButton` / `ImageCheckBox` 支持：`column`（列表 / 纵向，默认）/ `side_by_side`（平铺 / 横向）。其余字段忽略 |
| `statements` | array | 矩阵类用：`[{ label }]` |
| `dimensions` | array | TableField / MatrixField 用 |
| `rating_max` | int | RatingField / MatrixScaleField 用，3/5/10 |
| `predefined_value` | string / object | 默认值，类型见对应字段说明。**选择类字段（单选 / 多选 / 下拉 / 级联）不接受**，默认选中改用 `choices[].selected` |
| `other_choice_required` | bool | 选了「其他」选项后必须填写其扩展文本框（"其他选项必填"校验）。默认 false。仅 `RadioButton` / `CheckBox` / `DropDown` 且含「其他」选项时生效，其余类型忽略 |
| `placeholder` | string | 占位文本 |
| `range_min` / `range_max` | number | NumberField 取值范围 |
| `precision` | int / string | NumberField (0-14) 或 DateTimeField (`year`/`month`/`day`/`hour`/`minute`/`second`) |

> 不同字段类型还有专属属性（`max_size` / `media_type` / `goods_items` / `reservation_items` / `formula_display` / `associated_form_token` 等），全部见 [字段类型清单](#字段类型白名单)。

**setting 子参数**（创建阶段只接受这几个，更多设置走 edit_form）

| 字段 | 类型 | 说明 |
| ---- | ---- | ---- |
| `success_message` | string | 提交成功提示文案 |
| `open_entry_action` | enum | `hide` / `view` / `edit`，默认 `view` |
| `open_entry_message` | string | 已填过表单的提示文案（默认 `你已填写过该表单`） |
| `notification_rules` | array | 通知规则数组，见 [edit_form](#edit_form) 同名参数 |

**输出**

```json
{
  "name": "2026 春季发布会报名表",
  "token": "abCdEf",
  "description": "活动报名",
  "form_url": "https://jinshuju.net/f/abCdEf",
  "fields_count": 7,
  "created_at": "2026-05-17T10:00:00+08:00"
}
```

**调用示例（活动报名表）**

```json
{
  "name": "2026 春季发布会报名表",
  "description": "公司春季发布活动登记",
  "fields": [
    { "type": "NameField", "label": "姓名", "required": true },
    { "type": "MobileField", "label": "手机号", "required": true, "sms_verification": true },
    { "type": "TextField", "label": "公司" },
    { "type": "TextField", "label": "职位" },
    {
      "type": "DropDown", "label": "参会城市", "required": true,
      "choices": [{ "value": "北京" }, { "value": "上海" }, { "value": "深圳" }, { "value": "线上" }]
    },
    {
      "type": "CheckBox", "label": "感兴趣议题",
      "choices": [{ "value": "产品发布" }, { "value": "技术架构" }, { "value": "客户案例" }]
    },
    { "type": "TextArea", "label": "备注" }
  ],
  "setting": {
    "success_message": "感谢报名！我们将于活动前一周发送参会指引"
  },
  "folder_token": "FLD_a1b2"
}
```

**常见错误**

- `Name cannot be empty`
- `Fields cannot be empty`
- `Invalid field type: <Type>` — 字段类型不在白名单
- `Folder not accessible` — folder_token 不属于当前用户
- `Insufficient scope: forms required`

### 字段类型白名单

**基础（19）**：`TextField` `TextArea` `NumberField` `EmailField` `MobileField` `TelephoneField` `IdCardField` `NameField` `AddressField` `LinkField` `GeoField` `AttachmentField` `DateTimeField` `TimeField` `RatingField` `NpsField` `RadioButton` `CheckBox` `DropDown`

**进阶（14）**：`TableField` `CascadeDropDown` `SortField` `LikertField` `MatrixField` `MatrixScaleField` `ImageRadioButton` `ImageCheckBox` `GoodsField` `FormulaField` `ReservationField` `FormAssociation` `ESignatureField` `AudioField`

**装饰 / 控件（6）**：`SectionBreak`（描述字段）`PageBreak` `WidgetButton` `WidgetContact` `WidgetMap` `WidgetMarquee`

> `PageBreak` 只是在**经典式**表单内手动分页（拆子页），**不等于分页式表单**；要整表一页一题 / 自动翻页，用 `create_form` 的 `layout: "card"`（见输入表），别拿 PageBreak 拼。

**复杂字段示例片段**

```json
{
  "type": "GoodsField", "label": "选购", "unit": "件",
  "goods_items": [
    { "layout": "without_images", "name": "黑色 T 恤", "price": 99, "inventory": 50 },
    { "layout": "images", "name": "彩色 T 恤", "price": 99, "image_urls": ["https://cdn.example.com/tshirt.jpg"] },
    {
      "layout": "price_only", "name": "爱心捐款",
      "dimensions": [{ "label": "金额", "options": [{ "label": "100" }, { "label": "500" }, { "label": "自定义", "value": "customized" }] }],
      "skus": [
        { "specification": { "金额": "100" }, "price": 100 },
        { "specification": { "金额": "500" }, "price": 500 },
        { "specification": { "金额": "customized" }, "price": 0.01 }
      ]
    }
  ]
}
```

```json
{
  "type": "ReservationField", "label": "预约场次",
  "reservation_items": [{
    "name": "诊室 A",
    "quota_setting": {
      "type": "by_time_range_repeat_daily",
      "available_days_of_week": ["monday", "tuesday", "wednesday", "thursday", "friday"],
      "time_range_mode": "same_by_wday",
      "show_left_quota": true,
      "start_time_offset": { "offset_number": 1, "unit": "day" },
      "end_time_offset": { "offset_number": 14, "unit": "day" },
      "daily_time_range_quotas": [
        { "quota": 5, "start_time": { "hour": 9, "minute": 0 }, "end_time": { "hour": 12, "minute": 0 } },
        { "quota": 5, "start_time": { "hour": 14, "minute": 0 }, "end_time": { "hour": 17, "minute": 0 } }
      ]
    }
  }]
}
```

> `start_time_offset` = 提前预约要求（须提前 N 天 / 小时预约）；`end_time_offset` = 未来可约窗口（未来可约 N 天 / 小时内）；`unit` 取 `day` / `hour`，省略则无对应限制。`start_time` / `end_time` 传 `{ hour, minute }` 整数即可，`get_form` 读回时时刻是零填充字符串（`"09"`）。
>
> ⚠️ **`edit_form` 更新 `reservation_items` 是整体替换**：要保留某个已有项（如只改 quota），必须从 `get_form` 读出并在该项回传其 `api_code`——预约提交数据按 item 的 `api_code` 索引，丢了会让历史预约数据失联。省略 `api_code` 时后端按 `name` 匹配现有项保留；**改名务必回传 `api_code`**，否则视为新项、旧数据失联。

```json
{
  "type": "ImageRadioButton", "label": "选择头像", "choices_layout": "side_by_side",
  "choices": [
    { "value": "头像 A", "image_upload_token": "form_img_tok_..." },
    { "value": "头像 B", "image_url": "https://cdn.example.com/b.png" }
  ]
}
```

> 图片选项（`ImageRadioButton` / `ImageCheckBox`）的 `value` 是**文字标签、必填**；图片走 `image_upload_token`（本地图先 [prepare_form_image_upload](#prepare_form_image_upload)）/ `image_url` / `image_base64`，三者必须有其一。

```json
{
  "type": "FormulaField", "label": "总价",
  "formula_display": "<gd-field data-api-code=\"field_2\"></gd-field> * <gd-field data-cid=\"qty7x\"></gd-field>",
  "result_display_type": "numeric",
  "precision": 2,
  "icon_type": "cny1",
  "thousands_separator": true
}
```

> 公式引用规则：**已存在的字段**用 `data-api-code`；**同一请求里新增的字段**还没有 api_code，用 `data-cid`（值是该字段的 `cid`），保存时后端解析为新分配的 api_code。表格 / 矩阵的新维度用 `data-cid="表格cid" data-dimension-cid="列cid"`。不要预测 `field_N` 序号或自行指定 api_code。

```json
{
  "type": "FormAssociation", "label": "关联客户", "required": true,
  "associated_form_token": "MASTER_TOKEN",
  "associated_field_api_codes": ["field_1"],
  "display_field_api_codes": ["field_2", "field_3"]
}
```

```json
{
  "type": "SectionBreak", "label": "活动说明",
  "notes": "请仔细阅读以下规则……",
  "show_split_line": true,
  "show_part_description": true
}
```

---

## copy_form

**用途**：基于已有表单创建新表单（继承字段、主题、setting）。

**Scope**：`forms`

**输入**

| 参数 | 类型 | 必填 | 说明 |
| ---- | ---- | ---- | ---- |
| `form_token` | string | ✅ | 源表单 token |
| `name` | string | 否 | 新表单名，默认 `"Copy of <原名>"` |
| `folder_token` | string | 否 | 新表单要放进的文件夹 token |

**输出**

```json
{
  "name": "2026 年会报名表",
  "token": "newToken",
  "description": "...",
  "form_url": "https://jinshuju.net/f/newToken",
  "fields_count": 8,
  "created_at": "2026-05-17T10:00:00+08:00"
}
```

**常见错误**

- `Form cannot be found` — 源表单 token 错
- `Folder not accessible` — folder_token 不属于当前用户
- `Failed to copy form: ...`

---

## move_form

**用途**：把表单移到指定文件夹，或移回根目录。

**Scope**：`forms`

**输入**

| 参数 | 类型 | 必填 | 说明 |
| ---- | ---- | ---- | ---- |
| `form_token` | string | ✅ | 要移动的表单 token |
| `folder_token` | string | 否 | 目标文件夹 token；**省略或传 `""` = 移出文件夹回到根目录** |

**输出**

```json
{ "form_token": "abCdEf", "folder_token": "FLD_a1b2" }
```

移出文件夹时 `folder_token` 为 `null`：

```json
{ "form_token": "abCdEf", "folder_token": null }
```

**常见错误**

- `Form cannot be found`
- `Folder not accessible` — 文件夹不存在或不属于当前用户

---

## edit_form

**用途**：原子化地更新表单——可一次性改 name / description / setting / fields（字段增删改、选项增删改名）。

> ⚠️ **删字段 / 选项前先用 [`check_field_data`](#check_field_data) 查是否有提交数据**——删除有数据的字段 / 选项会永久清除这些数据且不可恢复。`has_data=true` 时先把影响告诉用户、取得确认再删（human-in-the-loop）。edit_form 本身不做拦截、不需要任何 force 参数，直接删。

**Scope**：`forms`

**输入**

| 参数 | 类型 | 必填 | 说明 |
| ---- | ---- | ---- | ---- |
| `form_token` | string | ✅ | |
| `name` | string | 否 | 新表单名 |
| `description` | string | 否 | 新表单说明 |
| `setting` | object | 否 | 见下"setting 全字段表"；**只传要改的 key，其他保持原值** |
| `fields` | object | 否 | `{ add[], remove[], update[], update_choices[] }` 四种操作，原子化执行 |

**必须至少传一个 edit 操作，否则报 `No edit operations specified`。**

> ⚠️ 字段显示规则**不再通过 edit_form 编辑**：`field_rules` 参数已移除，误传会被拒（`field_rules is no longer edited through edit_form. Use the edit_field_rules tool`）。改用专用工具 [`edit_field_rules`](#edit_field_rules)（外科式增删改，按 index 定位）。

### setting 全字段表

| 字段 | 类型 | 说明 |
| ---- | ---- | ---- |
| `entry_submit_mode` | enum | 提交后行为 `show_message` / `redirect` / `reports` / `exam_score`；填了 `success_redirect_url` 时强制改为 `redirect` |
| `success_message` | string | 文本成功页文案 |
| `success_message_rich_text` | string | HTML 富文本成功页（需套餐支持） |
| `success_message_style` | enum | `text` / `rich_text`；只传一个 message 字段时自动设置 |
| `success_redirect_url` | string | 跳转 URL |
| `success_redirect_fields` | string[] | 跳转 URL 上拼接哪些字段的 api_code |
| `open_entry_action` | enum | `hide` / `view` / `edit`（edit 需 submitter_edit_open_entry 套餐能力） |
| `open_entry_message` | string | 已填过表单的提示语 |
| `open_entry_cancel_reservation` | bool | 预约场景：edit 时是否显示"取消预约"按钮 |
| `show_serial_number_on_success` | bool | 成功页是否显示流水号 |
| `show_submit_again` | bool | 成功页是否显示"再次提交" |
| `manually_close_rule` | object | `{ closed: bool }`，写后清除其他 close rules |
| `by_time_range_close_rule` | object | `{ start_time, end_time }` ISO 8601 |
| `by_entries_close_rule` | object | `{ limit: int }` |
| `show_close_count_down` | bool | 显示截止倒计时；只在有时间 close rule 时生效，否则静默被重置成 false |
| `show_form_before_open` | bool | 开放前是否预览表单；同上 |
| `fill_frequency` | object | `{ fill_type, condition, cycle_period, cycles_per_period, limited_time, limited_field_api_codes }` |
| `password_required` | bool | 启用访问密码闸；开启时必须同时给 `access_password` |
| `access_password` | string | 访问密码 |
| `allowed_audience` | enum | `public` / `internal` / `private` / `gd_user_only` / `weixin_followers_only` / `weixin_qiye_followers_only` |
| `notification_rules` | array | 通知规则数组，见下 |

**notification_rules** —— **替换语义**：传该 key 会重建所有 MCP 管理的规则（即 `from_next=true` 的）；传 `[]` 清空 MCP 规则；4.0 桌面的规则（`from_next=false`）不会被动。

```json
[
  {
    "approach": "WXWORK",
    "url": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=...",
    "content": "新报名：$(field_1) - $(field_2)",
    "trigger_scope": "all_new",
    "mentioned_mobile_list": ["13812345678", "@all"],
    "enabled": true
  },
  {
    "approach": "DING_TALK",
    "url": "https://oapi.dingtalk.com/robot/send?access_token=...",
    "content": "新订单：$(field_3) 元",
    "trigger_scope": "all_new"
  },
  {
    "approach": "WEBHOOK",
    "url": "https://my.server/jinshuju-hook",
    "content": "{\"name\":\"$(field_1)\",\"mobile\":\"$(field_2)\"}",
    "trigger_scope": "all_new"
  }
]
```

`approach` 必须是 `WXWORK` / `DING_TALK` / `WEBHOOK` 之一；`trigger_scope` 取值：`all_new` / `all_update` / `matched_new` / `matched_update` / `all` / `schedule_time`。

### fields 四种操作

#### `fields.add: []`

形态与 `create_form.fields[]` 完全一致（含 `cid`，同请求内公式引用新字段时必需），可额外指定 `position`（0-based 插入位置，省略则追加到末尾）。

```json
{
  "fields": {
    "add": [
      { "type": "NumberField", "label": "年龄", "range_min": 18, "range_max": 100, "position": 2 },
      { "type": "AttachmentField", "label": "简历", "max_size": 8, "max_file_quantity": 2 }
    ]
  }
}
```

#### `fields.remove: ["api_code", ...]`

只传 api_code 列表；**不接受 label**。删除前先对每个 api_code 调 [`check_field_data`](#check_field_data)，有数据则向用户确认。

```json
{ "fields": { "remove": ["field_5", "field_7"] } }
```

#### `fields.update: []`

每项必须有 `api_code`，可修改 label / required / private / notes / unique / other_choice_required / choices_layout / 类型专属属性。**改 TableField / MatrixField 的 dimensions / statements、以及 ReservationField 的 reservation_items 时必须带各自的 api_code**（预约项 api_code 见 [字段类型清单](#字段类型白名单) 的 ReservationField 片段），否则旧数据引用会失效。传 `position`（0-based 整数）可把已存在字段移到新位置，保留 api_code 和数据；在 `fields.add` 插入之后应用，多个 `position` 按升序执行，越界钳到末尾。

```json
{
  "fields": {
    "update": [
      { "api_code": "field_1", "label": "全名", "required": true, "position": 0 },
      { "api_code": "field_3", "notes": "请填整数" },
      { "api_code": "field_8", "media_type": { "type": "custom", "value": ["pdf", "docx"] }, "max_size": 10 }
    ]
  }
}
```

#### `fields.update_choices: []`

选项字段的增删改名。**改文案永远用 `update`（保留 api_code）**，不要用 `remove` + `add`，否则历史数据引用失效。切换选项的**默认选中**也用 `update`（带 `api_code` + `selected`）；`add` 的新选项也可带 `selected`。`remove` 选项前先用 [`check_field_data`](#check_field_data)（带 `choice_value`）查该选项是否有数据，有则向用户确认。**图片选项字段（ImageRadioButton / ImageCheckBox）**：`add` 的每项必须带 `image_upload_token` / `image_url` / `image_base64` 之一（缺图报 `ima

... [Content truncated, total 55,599 chars] ...