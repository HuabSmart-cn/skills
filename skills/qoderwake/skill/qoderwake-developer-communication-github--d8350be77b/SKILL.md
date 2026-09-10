---
name: github-developer-communication
description: >
  Manage GitHub issue communication and status updates during development workflow. **ALWAYS use this skill when:** (1) user mentions "github issue" with bug/fix/task keywords (e.g., "fix github issue #123", "处理 github issue", "work on issue #456"), (2) user provides a GitHub issue URL (github.com/*/issues/*), (3) GITHUB_ISSUE environment variable exists, or (4) user explicitly requests GitHub issue operations like status updates, posting comments, notifying stakeholders, or checking for duplicate issues. This skill handles: updating issue labels to "in-progress"/"needs-review", auto-assigning yourself, asking issue creators to clarify ambiguous requirements via @mentions, searching for similar issues (open + recently closed) to avoid duplication, processing images/attachments in issue descriptions, and notifying completion with PR links and test results. Trigger immediately when detecting any GitHub issue context, even if the user doesn't explicitly ask for "GitHub communication" - they may just say "fix issue #123" with a GitHub URL or "处理这个问题" when GITHUB_ISSUE is set.
---

# GitHub Issue Communication Skill

This skill handles all communication and status management with GitHub issues during development. Your role is to be the bridge between the development process and GitHub stakeholders, not to solve the technical problems yourself.

## Core Responsibilities

You handle **only** GitHub issue communication and status management:
- Update issue labels and assignees at workflow milestones
- Ask clarifying questions to issue creators
- Search for duplicate/similar issues
- Notify stakeholders of completion

You do **NOT**:
- Judge whether requirements are clear (other skills handle that)
- Generate clarification questions yourself (receive them from other skills)
- Implement features or fix bugs (development skills do this)
- Test or verify solutions (QA skills do this)
- Create or submit PRs (other skills do this)

## Getting Issue Information

### Issue ID Sources

Check for the GitHub issue number in this order:

1. **User's prompt**: Look for explicit issue mentions (e.g., "fix issue #123", "处理 issue #456")
2. **Issue URL**: Extract number from GitHub URLs (e.g., `https://github.com/owner/repo/issues/123`)
3. **Environment variable**: Check `GITHUB_ISSUE` environment variable
4. **Ask user**: If none exist, ask the user for the issue number

### Retrieving Issue Details

Once you have the issue number, use `gh` CLI to fetch:
- Issue creator (author)
- Issue assignees
- Issue title and body content
- Existing comments
- Current labels
- **Images and attachments** in the issue body and comments

Example command:
```bash
gh issue view 123 --json number,title,body,author,assignees,labels,comments,url
```

### Understanding Images and Attachments

**CRITICAL**: Images and attachments in GitHub issues often contain essential information that is not in the text description. Always process them:

#### Images

GitHub issues can contain images in several ways:
- **Markdown images**: `![alt](https://user-images.githubusercontent.com/...)`
- **HTML img tags**: `<img src="..." />`
- **Drag-and-drop uploads**: Converted to markdown with GitHub CDN URLs
- **Pasted screenshots**: Same as drag-and-drop

**How to process**:
1. Extract all image URLs from the issue body and comments using regex patterns:
   - `!\[.*?\]\((https?://[^\)]+)\)`
   - `<img[^>]+src=["'](https?://[^"']+)["']`
   - Look for `github.com/user-attachments/assets/` URLs
   - Look for `user-images.githubusercontent.com` URLs
2. Download each image (use `curl` or `wget`)
3. Use Claude's vision capabilities to understand image content
4. Extract key information such as:
   - UI mockups or design specifications
   - Error screenshots with stack traces
   - Architecture diagrams
   - Data examples or expected outputs
   - Workflow diagrams
5. Include extracted information in context when clarifying requirements or implementing features

#### File Attachments

GitHub allows attaching files (PDFs, logs, archives, etc.):
- They appear as download links in the markdown
- URLs typically: `https://github.com/*/files/*` or `github.com/user-attachments/files/*`

**How to process**:
1. Extract attachment URLs from issue body and comments
2. Download the files using `gh api` or `curl` with authentication
3. Use appropriate tools to read content:
   - Text files (`.txt`, `.log`): Read directly
   - PDFs: Use PDF reading tools
   - CSV/Excel: Parse as data
   - Archives (`.zip`, `.tar.gz`): Extract and examine contents
   - JSON/YAML: Parse and analyze structure
4. Include key information from attachments in context

**Important**: If images or attachments cannot be accessed or processed, note this in a comment to the issue creator and request alternative information.

## Workflow Steps

### 1. Starting Work on an Issue

**When**: You receive a GitHub issue to work on (feature request or bug)

**Actions**:
1. Retrieve the issue details using `gh issue view`
2. **Detect issue language**:
   - Count Chinese characters (Unicode range: \u4e00-\u9fff) in title + body
   - If Chinese characters > 30% of total text, use Chinese for comments
   - Otherwise, use English
3. **Process images and attachments** in the issue body and comments
4. **Smart label matching**:
   - Get all repository labels: `gh label list --json name,description`
   - Match for "in-progress" status:
     * Exact match (case-insensitive): `in-progress`, `in progress`, `wip`, `doing`, `开发中`, `进行中`, `执行中`
     * Partial match: labels containing these terms
   - If no match found, create the label: `gh label create "in-progress" --color "0e8a16" --description "Work in progress"`
5. **Add label and assign yourself**:
   ```bash
   gh issue edit 123 --add-label "in-progress" --add-assignee "@me"
   ```
6. **Optionally post a comment** noting work has started:
   ```bash
   gh issue comment 123 --body "Started working on this issue.

   -- create by qoderwake --"
   ```

**Label color scheme** (if creating new labels):
- `in-progress`: `#0e8a16` (green)
- `needs-review`: `#fbca04` (yellow)
- `clarification-needed`: `#d93f0b` (orange)

### 2. Clarifying Requirements

**When**: Other skills determine that requirements/bug details are unclear and provide clarification questions

**Actions**:
1. Receive the clarification questions from the requesting skill
2. Detect issue language (same method as step 1)
3. **Add clarification label**:
   - Smart match for: `clarification-needed`, `needs-clarification`, `question`, `待确认`, `需澄清`
   - Create if not exists: `gh label create "clarification-needed" --color "d93f0b"`
4. Post a comment mentioning the issue creator:

**English comment format**:
```bash
gh issue comment 123 --body "@creator_username

We need clarification on the following details:

{clarification_questions}

Please provide more information to proceed. Thank you!

-- create by qoderwake --"
```

**Chinese comment format**:
```bash
gh issue comment 123 --body "@creator_username

关于本 issue，需要和您确认以下细节：

{clarification_questions}

请提供更多信息以便继续推进，谢谢！

-- create by qoderwake --"
```

### 3. Checking for Similar Issues

**When**: After understanding the requirement/bug clearly (and before implementation starts)

**Actions**:
1. Extract key terms from the issue title and body (5-10 most relevant words)
2. Get current repository (from git remote or `gh repo view --json nameWithOwner`)
3. Search for similar issues (open + recently closed within 30 days):
   ```bash
   # For single-repo searches, use gh issue list (more reliable for small/private repos)
   gh issue list -R owner/repo --search "key terms" \
     --json number,title,state,url,createdAt \
     --limit 10 --state all

   # Alternative: Use gh search issues for cross-repo searches (may not work for private/small repos)
   DATE_30_DAYS_AGO=$(date -u -v-30d +%Y-%m-%d 2>/dev/null || date -u -d '30 days ago' +%Y-%m-%d)
   gh search issues "key terms repo:owner/repo" --limit 10

   # Note: gh search issues uses GitHub's search index which may be incomplete for small repos
   # Prefer gh issue list --search for single-repo scenarios
   ```
4. Filter and rank results by relevance (title similarity, description overlap)
5. If similar issues found (top 5):
   - Sort by creation time (newest first)
   - Post a comment to notify the creator

**English comment format**:
```
@creator_username

Before starting work, I found potentially similar issues:

1. [Issue Title](issue_url) - Created on {date} (#{number}, {state})
2. [Another Title](issue_url) - Created on {date} (#{number}, {state})
...

Please confirm if we should proceed with this issue or reuse solutions from existing ones.

-- create by qoderwake --
```

**Chinese comment format**:
```
@creator_username

在开始处理前，发现可能存在相似的 issue：

1. [Issue 标题](issue_url) - 创建于 {date} (#{number}, {state})
2. [另一个标题](issue_url) - 创建于 {date} (#{number}, {state})
...

请确认是否需要继续处理本 issue，或者可以复用已有 issue 的方案。

-- create by qoderwake --
```

6. If no similar issues found, proceed silently (no comment needed)

### 4. Mid-Development Clarification

**When**: Development skills encounter blockers requiring creator input

**Actions**:
- Follow the same process as Step 2
- You can do this multiple times during development as needed
- Make sure `clarification-needed` label is added if not already present

### 5. Notifying Completion

**When**: Development is complete, PR is submitted, and testing is done (other skills confirm this)

**Actions**:
1. Receive from other skills:
   - PR link (URL or PR number)
   - Test results summary
2. Detect issue language
3. **Smart label matching** for completion:
   - Remove: `in-progress` label
   - Match for "needs review": `needs-review`, `review-needed`, `ready-for-review`, `待验证`, `待测试`, `待审核`
   - Create if not exists: `gh label create "needs-review" --color "fbca04"`
   - Add: matched review label
4. Get PR details if only number provided:
   ```bash
   gh pr view 456 --json url,title
   ```
5. Post completion comment mentioning creator and assignees:

**English comment format**:
```bash
gh issue comment 123 --body "@creator_username @assignee1 @assignee2

This issue has been resolved. Details:

**Pull Request**: {pr_url}

**Test Results**:
{test_results_summary}

Please verify that the functionality meets expectations.

-- create by qoderwake --"
```

**Chinese comment format**:
```bash
gh issue comment 123 --body "@creator_username @assignee1 @assignee2

本 issue 已完成开发和测试，详情如下：

**PR 链接**: {pr_url}

**测试结果**:
{test_results_summary}

请验证功能是否符合预期。

-- create by qoderwake --"
```

6. Update labels:
   ```bash
   gh issue edit 123 --remove-label "in-progress" --add-label "needs-review"
   ```

## Language Detection

Implement language detection using this logic:

```bash
# Extract Chinese character count
CHINESE_COUNT=$(echo "$ISSUE_CONTENT" | grep -o '[\u4e00-\u9fff]' | wc -l)
TOTAL_CHARS=$(echo "$ISSUE_CONTENT" | wc -m)

# Calculate percentage
if (( CHINESE_COUNT * 100 / TOTAL_CHARS > 30 )); then
  LANGUAGE="zh"
else
  LANGUAGE="en"
fi
```

Or use a simpler heuristic:
- If title OR body contains significant Chinese text (>30% characters), use Chinese
- Otherwise, use English
- Can check with regex: `/[\u4e00-\u9fff]/` for Chinese characters

## Smart Label Matching

When matching labels for status updates:

1. **Retrieve all repository labels**:
   ```bash
   gh label list --json name,description,color
   ```

2. **Match semantically**:
   - **For "in-progress"**:
     * Priority 1 (exact): `in-progress`, `in progress`, `wip`, `doing`
     * Priority 2 (Chinese): `开发中`, `进行中`, `执行中`
     * Priority 3 (partial): labels containing these terms

   - **For "needs-review"**:
     * Priority 1 (exact): `needs-review`, `review-needed`, `ready-for-review`, `ready for review`
     * Priority 2 (Chinese): `待验证`, `待测试`, `待审核`, `待确认`
     * Priority 3 (partial): labels containing these terms

   - **For "clarification-needed"**:
     * Priority 1 (exact): `clarification-needed`, `needs-clarification`, `question`, `help wanted`
     * Priority 2 (Chinese): `待确认`, `需澄清`, `需要说明`
     * Priority 3 (partial): labels containing these terms

3. **Matching algorithm**:
   - Try exact match first (case-insensitive)
   - If multiple exact matches, prefer the first one
   - If no exact match, try partial match
   - If still no match, create the default English label

4. **Create label if needed**:
   ```bash
   gh label create "label-name" --color "hexcolor" --description "Description"
   ```

## gh CLI Commands Reference

### Essential Commands

**View issue details**:
```bash
gh issue view <number> --json number,title,body,author,assignees,labels,comments,url,state
```

**List repository labels**:
```bash
gh label list --json name,description,color
```

**Create label**:
```bash
gh label create "label-name" --color "0e8a16" --description "Label description"
```

**Edit issue (add label, assignee)**:
```bash
gh issue edit <number> --add-label "label-name" --add-assignee "@me"
gh issue edit <number> --remove-label "old-label" --add-label "new-label"
```

**Post comment**:
```bash
gh issue comment <number> --body "Comment text with @mentions"
```

**Search issues** (open + recently closed):
```bash
# Get date 30 days ago
DATE_30_DAYS_AGO=$(date -u -v-30d +%Y-%m-%d 2>/dev/null || date -u -d '30 days ago' +%Y-%m-%d)

# Search
gh search issues "keywords repo:owner/repo (is:open OR (is:closed closed:>$DATE_30_DAYS_AGO))" \
  --json number,title,state,url,createdAt,closedAt \
  --limit 10
```

**Get current repository**:
```bash
gh repo view --json nameWithOwner,owner,name
```

**Get PR details**:
```bash
gh pr view <number> --json number,url,title,state
```

### Fallback to `gh api`

For operations not in high-level commands, use `gh api`:

**Download image/file with authentication**:
```bash
gh api -H "Accept: application/octet-stream" <url> > output_file
```

**GraphQL for complex queries**:
```bash
gh api graphql -f query='
query($owner: String!, $repo: String!, $number: Int!) {
  repository(owner: $owner, name: $repo) {
    issue(number: $number) {
      title
      body
      author { login }
      labels(first: 10) { nodes { name } }
    }
  }
}' -f owner="owner" -f repo="repo" -F number=123
```

## Error Handling

### Common Issues and Solutions

**Problem**: Label doesn't exist in repository
- **Solution**: Create the label with predefined color and description

**Problem**: Cannot determine issue language
- **Solution**: Default to English, but inform user they can override

**Problem**: No permission to edit issue (labels/assignees)
- **Solution**:
  1. Report the error clearly to the user
  2. Suggest they check `gh auth status` for permissions
  3. Fallback: post comments only (comments usually work with read permissions)

**Problem**: Search returns too many results
- **Solution**: Refine search with more specific keywords, use exact phrases with quotes

**Problem**: GITHUB_ISSUE not set and user doesn't provide number
- **Solution**: Ask user clearly: "Please provide the GitHub issue number or URL"

**Problem**: Cannot access images or attachments
- **Solution**:
  1. Try `gh api` with authentication
  2. If still fails, post a comment:
     ```
     @creator_username

     Unable to access images/attachments in this issue. Please provide the following:
     - [List of inaccessible files]

     Or include key information directly in comments. Thank you!

     -- create by qoderwake --
     ```

**Problem**: Image is low quality or unclear
- **Solution**: Note what you can see, ask creator for clarification via comment

**Problem**: Not in a Git repository
- **Solution**: Ask user to provide repository in format `owner/repo`, then use `-R` flag:
  ```bash
  gh issue view 123 -R owner/repo
  ```

**Problem**: Multiple repositories in current directory
- **Solution**: Use `gh repo view` to confirm which repo is being used, or ask user to specify with `-R`

## Communication Tone

- **Professional and concise**: GitHub comments are public and visible to the community
- **Action-oriented**: Clearly state what you need or what was done
- **Respectful**: Always use polite language with @mentions
- **Structured**: Use markdown formatting (headings, bullet points, code blocks) for clarity
- **Agent marker required**: **ALWAYS** end every comment with `-- create by qoderwake --` to identify automated comments

## Example Scenarios

### Scenario A: Starting a bug fix (English issue)

```
User: "Start working on github issue #123"

Actions:
1. gh issue view 123 --json title,body,author,labels
2. Detect language: title="Fix login redirect bug" → English (no Chinese chars)
3. Process any images in issue body
4. gh label list --json name → finds "WIP" label
5. gh issue edit 123 --add-label "WIP" --add-assignee "@me"
6. gh issue comment 123 --body "Started working on this issue.\n\n-- create by qoderwake --"
```

### Scenario B: Starting a feature (Chinese issue)

```
User: "处理 issue #456"

Actions:
1. gh issue view 456 --json title,body,author,labels
2. Detect language: title="添加用户导出功能" → Chinese (>30% Chinese chars)
3. Process any images/attachments
4. gh label list --json name → no match found
5. gh label create "in-progress" --color "0e8a16" --description "开发中"
6. gh issue edit 456 --add-label "in-progress" --add-assignee "@me"
7. gh issue comment 456 --body "已开始处理此 issue。\n\n-- create by qoderwake --"
```

### Scenario C: Requirements unclear (with image)

```
Other skill: "Need to ask creator about the expected error message format. The issue has a screenshot showing an error but text is unclear."

Actions:
1. gh issue view 789 --json body,author
2. Extract image URLs from body: https://user-images.githubusercontent.com/12345/screenshot.png
3. Download and analyze image with vision capabilities
4. Detect language: Chinese issue
5. gh label list --json name → finds "需要说明" label
6. gh issue edit 789 --add-label "需要说明"
7. gh issue comment 789 --body "@creator 关于本 issue，需要确认：

- 错误提示的具体文案应该是什么？
- 是否需要支持多语言？

从截图中看到错误对话框，但无法确认最终的文案需求。请提供更多信息，谢谢！

-- create by qoderwake --"
```

### Scenario D: Found similar issues

```
After searching, found 2 similar issues:

Actions:
1. DATE=$(date -u -v-30d +%Y-%m-%d)
2. gh search issues "user export repo:owner/repo (is:open OR (is:closed closed:>$DATE))" --json number,title,url,state,createdAt --limit 10
3. Found matches: #234 (open), #189 (closed 15 days ago)
4. Detect language: Chinese issue
5. gh issue comment 456 --body "@creator 在开始处理前，发现可能存在相似的 issue：

1. [用户数据导出优化](https://github.com/owner/repo/issues/234) - 创建于 2024-03-15 (#234, open)
2. [批量导出用户信息](https://github.com/owner/repo/issues/189) - 创建于 2024-02-10 (#189, closed)

请确认是否需要继续处理本 issue，或者可以复用已有 issue 的方案。

-- create by qoderwake --"
```

### Scenario E: Work completed

```
Receive from other skills:
- PR: https://github.com/owner/repo/pull/567
- Tests: "All unit tests pass (42/42), integration tests pass (8/8)"

Actions:
1. gh issue view 456 --json author,assignees
2. Detect language: Chinese
3. gh label list --json name → finds "待验证" label
4. gh issue comment 456 --body "@creator @assignee1 本 issue 已完成开发和测试，详情如下：

**PR 链接**: https://github.com/owner/repo/pull/567

**测试结果**:
- 单元测试: 42/42 通过
- 集成测试: 8/8 通过

请验证功能是否符合预期。

-- create by qoderwake --"
5. gh issue edit 456 --remove-label "in-progress" --add-label "待验证"
```

### Scenario F: Issue with multiple images and file attachment

```
Issue #890 has:
- Description mentioning "see the architecture in the diagram"
- 2 images: architecture.png, error_screenshot.png
- 1 PDF attachment: requirements_spec.pdf

Actions:
1. gh issue view 890 --json body,comments
2. Extract image URLs using regex:
   - https://user-images.githubusercontent.com/12345/architecture.png
   - https://github.com/owner/repo/assets/67890/error_screenshot.png
3. Download images:
   curl -L "https://user-images.githubusercontent.com/12345/architecture.png" -o arch.png
   curl -L "https://github.com/owner/repo/assets/67890/error_screenshot.png" -o error.png
4. Analyze with vision:
   - architecture.png: "Shows microservice architecture with API Gateway, Auth Service, User Service"
   - error_screenshot.png: "NullPointerException at UserController.java:142"
5. Extract PDF URL and download:
   gh api <pdf_url> > requirements.pdf
6. Read PDF and extract: "Must support exporting 100k+ users, CSV format required"
7. Now have complete context: architecture design + error location + performance requirement
```

## Integration with Other Skills

This skill is designed to work with:
- **Development skills**: Receive completion notifications, PR links
- **QA/Testing skills**: Receive test results to include in completion comments
- **Requirements analysis skills**: Receive clarification questions to post
- **Project assistant skills**: Coordinate on when to check for duplicates

When other skills need GitHub issue communication, they should explicitly invoke this skill rather than handling GitHub interactions themselves.

## Authentication Requirements

This skill requires `gh` CLI to be authenticated with appropriate permissions:

```bash
# Check authentication status
gh auth status

# Required scopes:
# - repo (read/write access to repositories)
# - read:org (if working with organization repos)
```

If authentication fails, guide user to:
```bash
gh auth login
```

## Repository Context

The skill works in two modes:

1. **Inside a Git repository**: `gh` automatically detects the repository from git remotes
2. **Outside a repository**: User must provide repository with `-R owner/repo` flag, or you must ask for it

Always verify repository context:
```bash
# Check if in a git repo
git rev-parse --git-dir 2>/dev/null

# Get current repo
gh repo view --json nameWithOwner
```
