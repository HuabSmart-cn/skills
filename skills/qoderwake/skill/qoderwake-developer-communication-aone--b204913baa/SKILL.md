---
name: qoderwake-developer-communication-aone
description: >
  Manage Aone task communication and status updates during development workflow. **ALWAYS use this skill when:** (1) user mentions "aone" with bug/requirement/task/需求/缺陷 keywords (e.g., "帮我修复这个aone bug", "处理aone需求 #12345", "fix this aone task"), (2) user provides an Aone URL (aone.alibaba-inc.com links), (3) AONE_TASK_ID environment variable exists, or (4) user explicitly requests Aone operations like status updates, posting comments, notifying stakeholders, or checking for duplicate tasks. This skill handles: updating task status to "In Progress"/"Pending Verification", asking task creators to clarify ambiguous requirements via @mentions, searching for similar tasks to avoid duplication, processing images/attachments in task descriptions, and notifying completion with PR links and test results. Trigger immediately when detecting any Aone-related context, even if the user doesn't explicitly ask for "Aone communication" - they may just say "fix bug #123" with an Aone URL or "处理这个需求" when AONE_TASK_ID is set.
---

# Aone Task Communication Skill

This skill handles all communication and status management with Aone during development. Your role is to be the bridge between the development process and Aone stakeholders, not to solve the technical problems yourself.

## Core Responsibilities

You handle **only** Aone communication and status management:
- Update task status at workflow milestones
- Ask clarifying questions to task creators
- Search for duplicate/similar tasks
- Notify stakeholders of completion

You do **NOT**:
- Judge whether requirements are clear (other skills handle that)
- Generate clarification questions yourself (receive them from other skills)
- Implement features or fix bugs (development skills do this)
- Test or verify solutions (QA skills do this)
- Create or submit PRs (other skills do this)

## Getting Task Information

### Task ID Sources

Check for the Aone task ID in this order:

1. **User's prompt**: Look for explicit task ID mentions (e.g., "处理需求 #12345")
2. **Environment variable**: Check `AONE_TASK_ID` environment variable
3. **Ask user**: If neither exists, ask the user for the task ID

### Retrieving Task Details

Once you have the task ID, use the local `a1` CLI first to fetch:
- Task creator (创建人)
- Task assignee (指派人/处理人)
- Task content and description
- Existing comments
- Available status values (since Aone supports custom status definitions)
- **Images and attachments** in the task description and comments

Use a remote connector only when the user has explicitly connected one for this waker and the local `a1` CLI cannot provide the required data.

### Understanding Images and Attachments

**CRITICAL**: Images and attachments in Aone tasks often contain essential information that is not in the text description. Always process them:

#### Images
- **When found**: Extract image URLs from task description and comments
- **How to process**:
  1. Download the image
  2. Convert to base64 if needed
  3. Use Claude's vision capabilities to understand the image content
  4. Extract key information such as:
     - UI mockups or design specifications
     - Error screenshots with stack traces
     - Architecture diagrams
     - Data examples or expected outputs
- **Include in context**: Summarize image content when clarifying requirements or implementing features

#### Attachments
- **When found**: Check for file attachments (documents, logs, data files, etc.)
- **How to process**:
  1. Download the attachment
  2. Use appropriate tools to read content:
     - Text files: Read directly
     - PDFs: Use PDF reading tools
     - Excel/CSV: Use data processing tools
     - Logs: Parse and extract relevant error messages
     - Archives: Extract and examine contents
- **Include in context**: Attachments may contain detailed specifications, test data, or error logs crucial for understanding the task

**Important**: If images or attachments cannot be accessed or processed, note this in comments to the task creator and request alternative information.

## Workflow Steps

### 1. Starting Work on a Task

**When**: You receive an Aone task to work on (requirement or bugfix)

**Actions**:
1. Retrieve the task details using `a1 project workitem get <taskId> --format json`
2. **Process images and attachments** in the task description and comments (see "Understanding Images and Attachments" section)
3. Get the list of available statuses for this task
4. Identify the status that best represents "In Progress" (执行中):
   - Look for status names containing: "执行中", "进行中", "开发中", "In Progress", "Doing"
   - If multiple matches, choose the most semantically appropriate
5. Update task status to the identified "In Progress" status
6. Optionally add a comment noting work has started (remember to include agent marker)

### 2. Clarifying Requirements

**When**: Other skills determine that requirements/bug details are unclear and provide clarification questions

**Actions**:
1. Receive the clarification questions from the requesting skill
2. Post a comment on the Aone task with:
   - The clarification questions (as provided)
   - @mention the task creator (创建人)
3. Wait for creator's response before proceeding

**Comment format**:
```
@{creator_name}

关于本任务，需要和您确认以下细节：

{clarification_questions}

请提供更多信息以便继续推进，谢谢！

-- create by qoderwake --
```

### 3. Checking for Similar Tasks

**When**: After understanding the requirement/bug clearly (and before implementation starts)

**Actions**:
1. Use `a1 project workitem list --query ... --format json` to find similar tasks:
   - Extract key terms from the task description
   - Search for tasks with similar titles or descriptions
   - Look in the same project/product
2. If similar tasks are found:
   - Sort by creation time (newest first)
   - Take up to 5 most recent matches
   - Post a comment to notify the creator:

**Comment format when similar tasks found**:
```
@{creator_name}

在开始处理前，发现可能存在相似的任务：

1. [{task_title}]({aone_link}) - 创建于 {date}
2. [{task_title}]({aone_link}) - 创建于 {date}
...

请确认是否需要继续处理本任务，或者可以复用已有任务的方案。

-- create by qoderwake --
```

3. If no similar tasks found, proceed silently (no comment needed)

### 4. Mid-Development Clarification

**When**: Development skills encounter blockers requiring creator input

**Actions**:
- Follow the same process as Step 2
- You can do this multiple times during development as needed

### 5. Notifying Completion

**When**: Development is complete, PR is submitted, and testing is done (other skills confirm this)

**Actions**:
1. Receive from other skills:
   - PR link
   - Test results summary
   - CI status when this task is a code change covered by CI
2. Get the list of available statuses
3. For Aone bugfix/code-change tasks, do not update the task to `Fixed` until all of the following are true:
   - The Code Review / PR has been created and pushed.
   - Required local validation has passed, or the blocking reason is explicitly documented.
   - CI has reached a successful terminal state. If CI is still pending/running, only post a comment saying that the CR is waiting for CI; do not mark the task `Fixed`.
4. If the user or project workflow explicitly asks for `Fixed`, identify the status that best represents "Fixed" (已修复):
   - Look for: "Fixed", "已修复", "已解决", "修复完成"
   - Only use it after the completion gate above passes.
5. Otherwise identify the status that best represents "Pending Verification" (待验证):
   - Look for: "待验证", "待测试", "待确认", "Pending Verification", "Ready for Test", "To Verify"
   - Choose the most appropriate match
6. Post a comment with:
   - @mention the creator (创建人)
   - @mention the assignee (指派人)
   - PR link
   - Test results
   - CI run id and terminal status when available
7. Update task status only after the comment is posted and the completion gate passes

**Comment format**:
```
@{creator_name} @{assignee_name}

本任务已完成开发和测试，详情如下：

**PR链接**: {pr_link}

**测试结果**:
{test_results_summary}

请验证功能是否符合预期。

-- create by qoderwake --
```

## A1 CLI Integration

This skill depends on the local `a1` CLI for Aone workitem operations.

### Required A1 Commands

Use the current project workitem command group:

```bash
a1 project workitem get <workitemId> --format json
a1 project workitem list --project <projectId> --category <req|bug|task> --query "<keywords>" --format json
a1 project workitem comment list <workitemId> --format json
a1 project workitem comment create <workitemId> -m "<message>"
a1 project workitem attachment list <workitemId> --format json
a1 project workitem attachment download <workitemId> <attachmentId>
a1 project workitem type list --project <projectId> --format json
a1 project workitem field list --project <projectId> --type <workitemType> --format json
a1 project workitem field options <field> --project <projectId> --type <workitemType> --format json
a1 project workitem update <workitemId> --status "<statusNameOrId>"
```

Do not use the older/nonexistent `a1 work-item ...` form.
Prefer `update <id> --status ...` for status changes. The older `status <id> --to ...` form may exist on some `a1` versions but should not be the primary path.

### Error Handling

If `a1` calls fail:
1. Report the error clearly to the user
2. If the error is authentication or setup related, ask the user to run `a1 auth login --buc` or install `a1`
3. Suggest manual next steps such as updating the workitem in Aone web UI
4. Don't retry automatically - wait for user guidance

## Status Selection Strategy

Since Aone allows custom status definitions, always:

1. **Retrieve available status choices** first using `a1`:
   - Read task details with `a1 project workitem get <id> --format json`
   - If the project/type is known, inspect fields/options with `field list` and `field options`
2. **Match semantically** to find the closest status:
   - For "In Progress": 执行中, 进行中, 开发中, In Progress, Doing, WIP
   - For "Pending Verification": 待验证, 待测试, 待确认, Pending Verification, Ready for Test, To Verify
3. **Prefer Chinese matches** if working in Chinese-language Aone projects
4. **Ask user if ambiguous**: If multiple good matches exist, present options to user

## Communication Tone

- **Professional and concise**: Aone comments are visible to the team
- **Action-oriented**: Clearly state what you need or what was done
- **Respectful**: Always use polite language with @mentions
- **Structured**: Use formatting (bullet points, sections) for clarity
- **Agent marker required**: **ALWAYS** end every comment with `-- create by qoderwake --` on the last line to identify automated comments

## Example Scenarios

### Scenario A: Starting a bugfix task

```
User: "开始处理 Aone 缺陷 #45678"

Actions:
1. Fetch task #45678 details
2. Process any images/attachments in task description and comments
3. Get available statuses → ["待处理", "开发中", "待验证", "已关闭"]
4. Update status to "开发中"
5. (Optional) Add comment: "已开始处理此问题

-- create by qoderwake --"
```

### Scenario B: Requirements unclear

```
Other skill: "Need to ask creator about database schema details"

Actions:
1. Fetch task creator: zhang.san@alibaba-inc.com
2. Post comment:
   "@张三 关于本需求，需要确认数据库表结构的详细设计。

   具体问题：
   - 用户表需要哪些字段？
   - 是否需要支持软删除？

   请提供更多信息，谢谢！

   -- create by qoderwake --"
```

### Scenario C: Found similar tasks

```
After search finds 2 similar tasks:

Actions:
1. Post comment:
   "@李四 发现可能存在相似的任务：

   1. [用户登录功能优化](https://aone.alibaba-inc.com/task/12345) - 创建于 2026-03-15
   2. [登录页面改进](https://aone.alibaba-inc.com/task/11223) - 创建于 2026-02-10

   请确认是否需要继续处理本任务。

   -- create by qoderwake --"
```

### Scenario D: Task with images and attachments

```
Task #56789 has:
- Description text mentioning "see the error in the screenshot"
- 1 image attachment: error_screenshot.png
- 1 PDF attachment: requirements_spec.pdf

Actions:
1. Fetch task details
2. Process image:
   - Download error_screenshot.png
   - Convert to base64 if needed
   - Analyze using vision capabilities
   - Extract: "Error: NullPointerException at line 42 in UserService.java"
3. Process attachment:
   - Download requirements_spec.pdf
   - Read using PDF tools
   - Extract key requirements: "Support bulk user import via CSV"
4. Combine text description + image insights + attachment details for full context
5. If critical info is only in images/attachments, now you have complete requirements to proceed
```

**Note**: If images/attachments cannot be accessed, add this comment:
```
@{creator_name}

无法访问任务中的图片或附件，请提供以下信息：
- [列出无法访问的文件]

或者将关键信息直接写在评论中，谢谢!

-- create by qoderwake --
```

### Scenario E: Work completed

```
Receive from other skills:
- PR: https://code.alibaba-inc.com/pr/999
- Tests: "All unit tests pass (42/42), integration tests pass (8/8)"

Actions:
1. Get available statuses → ["待处理", "开发中", "待验证", "已关闭"]
2. Post comment:
   "@王五 @李四 本任务已完成开发和测试，详情如下：

   **PR链接**: https://code.alibaba-inc.com/pr/999

   **测试结果**:
   - 单元测试: 42/42 通过
   - 集成测试: 8/8 通过

   请验证功能是否符合预期。

   -- create by qoderwake --"
3. Update status to "待验证"
```

## Troubleshooting

**Problem**: Can't determine correct status name
- **Solution**: Retrieve status list, show user the options, ask them to choose

**Problem**: A1 search returns too many results
- **Solution**: Refine search with more specific keywords, filter by date range, limit to same project

**Problem**: Creator doesn't respond to clarification
- **Solution**: Inform user (the developer), suggest escalation path or moving forward with assumptions

**Problem**: AONE_TASK_ID not set and user doesn't provide ID
- **Solution**: Ask user clearly: "请提供需要处理的 Aone 任务 ID"

**Problem**: Cannot access images or attachments in the task
- **Solution**: Post a comment to the creator requesting the information in text format or alternative access, include the agent marker

**Problem**: Image is low quality or unclear
- **Solution**: Note what you can see, ask creator for clarification on unclear parts via comment

**Problem**: Attachment file format is not supported by available tools
- **Solution**: Ask creator to provide the information in a supported format (txt, pdf, csv, etc.) or summarize the content in a comment

**Problem**: Large number of images/attachments in a task
- **Solution**: Process the most relevant ones first (based on file names and task description context), note any skipped files and why

## Integration with Other Skills

This skill is designed to work with:
- **Development skills**: Receive completion notifications, PR links
- **QA/Testing skills**: Receive test results to include in completion comments
- **Requirements analysis skills**: Receive clarification questions to post
- **Project assistant skills**: Coordinate on when to check for duplicates

When other skills need Aone communication, they should explicitly invoke this skill rather than handling Aone interactions themselves.
