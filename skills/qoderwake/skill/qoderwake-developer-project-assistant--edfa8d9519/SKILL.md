---
name: qoderwake-developer-project-assistant
description: Browse QoderWake-analyzed projects and their documentation. **USE THIS SKILL PROACTIVELY** when users mention ANY of: "项目" (project), "repo/仓库" (repository), "workspace", "代码" (code), "开发规范" (dev conventions), "主分支" (main branch), "分支命名" (branch naming), "commit message", "ci", "测试" (tests), or describe a task/bug without specifying which codebase to work in. This skill helps users discover what projects exist, understand what each does, learn conventions (branching, commits, CI/CD, testing), and decide which repo(s) to modify. Also auto-updates documentation when code changes make it stale.
---

# QoderWake Developer Project Assistant

This skill helps developers work with projects analyzed by `qoderwake-developer-project-analysis` by:
1. **Discovering and browsing** multiple analyzed projects in the workspace
2. **Locating the right repo(s)** for a given task or bugfix using semantic matching and code search
3. **Reading and presenting** project conventions (branching, commits, CI/CD, testing)
4. **Maintaining documentation** artifacts to keep them synchronized with code changes

## When to Use This Skill

**PROACTIVELY** trigger this skill when users:
- Describe a task or bugfix without specifying which repo to work in
- Ask questions like "哪个项目" (which project), "在哪改" (where to change), "改哪几个repo" (which repos to modify)
- Mention "项目" (project), "仓库" (repo), "代码" (code), "工作目录" (workspace)
- Ask about development conventions: "开发规范", "主分支", "分支命名", "commit格式", "CI配置", "测试要求"
- Work on projects with analysis artifacts (even if they don't explicitly ask for them)

## Workspace Structure

The skill operates within this directory structure:

```plaintext
workspace/
  ├── project/
  │     └── {projectId}/          # repoRootPath
  │           ├── {repoName}/     # Git repo source code
  │           └── .repo/
  │                 └── {repoName}/  # Documentation artifacts
  │                       ├── profile.md
  │                       ├── platform.md
  │                       ├── task-source.md
  │                       ├── branching.md
  │                       ├── iteration.md
  │                       ├── ci.md
  │                       ├── agent-profile.md
  │                       └── verification.md
  └── .qoder/  # Agent configuration
```

## Core Capabilities

### 0. Multi-Project Discovery and Location (NEW - Priority Feature)

When users need to figure out which repo(s) to work in, help them discover and locate projects using a two-phase approach:

#### Phase 1: Discover All Analyzed Projects

1. **Find all analyzed projects** in the workspace:
   - Search for `.repo/*/profile.md` pattern from current directory upward
   - Each `.repo/{repoName}/` directory represents an analyzed project
   - Look in typical workspace structures:
     - `workspace/project/{projectId}/{repoName}/` (QoderWake default)
     - `~/projects/`, `~/code/`, `~/workspace/`
     - Current directory and parent directories

2. **Read project metadata** for each discovered project:
   - Read `profile.md` for: project name, purpose, tech stack, architecture
   - Read `branching.md` for: main branch, branch naming conventions
   - Read `platform.md` for: Git hosting platform, remote URL
   - Extract repository root path from directory structure

3. **Present projects overview** using this table format:

```markdown
## Available Projects

| Project | Purpose | Tech Stack | Main Branch | Location |
|---------|---------|------------|-------------|----------|
| frontend-web | User-facing web app | React, TypeScript, Vite | main | ~/workspace/project/123/frontend-web |
| backend-api | REST API service | Node.js, Express, PostgreSQL | master | ~/workspace/project/456/backend-api |
| shared-utils | Common utilities library | TypeScript, Bun | main | ~/workspace/project/789/shared-utils |
```

**If no analyzed projects found:** Inform user that no QoderWake-analyzed projects were detected. Ask if they want to run `/qoderwake-developer-project-analysis` on their repos.

#### Phase 2: Locate Target Repo(s) for User's Task

When user describes a task/bugfix (e.g., "fix login timeout", "add export feature"), use **both** strategies in parallel:

**Strategy A: Semantic Matching**
1. Extract key concepts from user's task description (e.g., "login" → authentication, user session)
2. Read each project's `profile.md` to find:
   - Purpose/description containing related keywords
   - Module names mentioning relevant functionality
   - Architecture diagrams showing related components
3. Score projects by relevance (0-10) based on keyword matches and semantic similarity
4. Filter projects with score >= 6 as candidates

**Strategy B: Code Search**
1. Extract search keywords from task description:
   - "login timeout" → ["login", "auth", "session", "timeout"]
   - "export CSV" → ["export", "csv", "download", "file"]
2. For each project, run `grep -r` searches:
   - Search in main source directories (src/, lib/, app/, pkg/)
   - Look for files, functions, classes, or comments matching keywords
   - Count matches per project
3. Rank projects by match density (matches per 1000 lines of code)
4. Select top 3 projects with most relevant matches

**Combine Results:**
- Merge candidates from both strategies
- For each candidate project, explain WHY it was selected:
  - "backend-api: profile mentions 'user authentication module' + found 23 files containing 'login'"
  - "frontend-web: profile describes 'data export features' + found components/ExportButton.tsx"
- If task spans multiple domains (e.g., "frontend + backend"), identify all relevant repos
- Show recommended project(s) with confidence level:
  - **High confidence** (1 clear match): "This should be done in [project-name]"
  - **Medium confidence** (2-3 matches): "This likely involves [project-a] and [project-b]"
  - **Low confidence** (no strong matches): "I couldn't confidently locate the right repo. Here are all available projects: [list]"

**Present location guidance:**
```markdown
## Recommended Repo(s) for Your Task

### Primary: backend-api (High Confidence)
**Why:** Project profile describes "handles user authentication and session management" + found 23 files with 'login' keyword including `src/auth/session-timeout.ts`

**Location:** `~/workspace/project/456/backend-api`

**Development Conventions:**
- Main branch: `master`
- Feature branch: `feature/fix-login-timeout`
- Commit format: `fix(auth): <description>`
- Pre-push: `bun test && bun run typecheck`
```

**Follow-up Actions:**
- If user confirms the project, read more documentation (branching.md, ci.md, verification.md) to provide detailed development guidance
- If user says it's wrong, ask clarifying questions and re-search
- Once project is confirmed, change directory to project root: `cd [project-path]`

### 1. Intelligent Documentation Reading

When users ask about project conventions or need context:

1. **Determine user intent** from their message:
   - Working on CI/CD → prioritize `ci.md`, `verification.md`
   - Creating branches/commits → prioritize `branching.md`
   - Adding features → prioritize `profile.md`, `agent-profile.md`, `verification.md`
   - Fixing bugs → prioritize `verification.md`, `ci.md`, `agent-profile.md`
   - Release/versioning questions → prioritize `iteration.md`, `branching.md`

2. **Locate the project** by checking current working directory:
   - Look for `.repo/{repoName}/` pattern in current directory or parent directories
   - If found, read the relevant documentation files
   - If not found, ask user for project path or repoName

3. **Present information contextually**:
   - **For specific questions:** Extract and show only the relevant section
   - **For broad questions:** Show full document with clear headings
   - **For task-oriented requests:** Synthesize actionable steps from multiple docs

**Example outputs:**

User: "How do I create a feature branch?"
→ Read `branching.md`, extract branch naming section and creation workflow, show step-by-step instructions

User: "What tests should I run before pushing?"
→ Read `ci.md` and `verification.md`, synthesize pre-push checklist with exact commands

User: "Tell me about this project"
→ Read `profile.md` and show full overview with architecture, tech stack, key modules

### 2. Auto-Detection of Stale Documentation

After users make code changes, proactively check if documentation needs updating:

#### Change Detection Patterns

Monitor these file patterns for changes (via git diff, file modification times, or explicit user mention):

| Change Type | File Patterns | Affected Docs |
|------------|---------------|---------------|
| **CI/CD** | `.aoneci/**`, `.github/workflows/**`, `.gitlab-ci.yml`, `Jenkinsfile`, `.circleci/**` | `ci.md` |
| **Dependencies** | `package.json`, `pnpm-workspace.yaml`, `go.mod`, `Cargo.toml`, `pom.xml`, `requirements.txt` | `profile.md` |
| **Build Config** | `tsconfig.json`, `vite.config.*`, `webpack.config.*`, `Makefile`, `CMakeLists.txt` | `profile.md` |
| **Testing** | New test files, test config changes (`playwright.config.*`, `jest.config.*`) | `verification.md` |
| **Git Hooks** | `.husky/**`, `.pre-commit-config.yaml`, `lefthook.yml` | `ci.md` |
| **Branch Protection** | Changes via platform API (GitHub/GitLab branch rules) | `branching.md` |

#### Detection Workflow

1. **After user completes a commit or significant change:**
   - Check git diff for modified files matching patterns above
   - If matches found, proceed to step 2

2. **Analyze the impact:**
   - Read the changed files to understand what was modified
   - Read the corresponding documentation to check if it's outdated
   - Identify specific sections that need updating

3. **Assess confidence level:**
   - **High confidence** = clear, objective change (e.g., new CI job added, dependency version changed, new test file added)
   - **Low confidence** = ambiguous change, unclear mapping to docs, or potential conflict with manual edits

4. **High confidence - Auto-update:**
   - Execute the update immediately (see "Documentation Update Process" below)
   - Show diff of changes made for review
   - Brief notification: "Updated [doc.md] to reflect changes in [file(s)]"
   - Remind user to commit the updated docs

5. **Low confidence - Skip update:**
   - Do not update and do not ask the user
   - User can manually update if needed or explicitly request an update later

### 3. Documentation Update Process

When updating documentation files:

#### Update Strategy by Document Type

**`profile.md` - Project Profile**
- **Triggers:** Dependency changes, new modules added, tech stack changes
- **What to update:**
  - Technology stack table (new dependencies, version bumps)
  - Module descriptions (if new workspaces added)
  - Architecture diagrams (if structure changed)
- **How:** Re-analyze the specific changed section, preserve rest of document

**`ci.md` - CI/CD Integration**
- **Triggers:** CI config file changes, new pipeline jobs, hook changes
- **What to update:**
  - Pipeline job descriptions
  - Pre-push checklist commands
  - Required environment variables
  - Known issues section (if new quirks discovered)
- **How:** Parse new CI config, extract job definitions, update corresponding sections

**`branching.md` - Branching Strategy**
- **Triggers:** Commit message format changes, new branch naming patterns, platform protection rule changes
- **What to update:**
  - Branch naming templates
  - Commit message examples (if conventional commit format changed)
  - PR workflow (if template changed)
- **How:** Analyze recent commits for new patterns, update examples

**`verification.md` - Verification Strategy**
- **Triggers:** New test files, test framework changes, E2E test additions
- **What to update:**
  - Test infrastructure section (new frameworks installed)
  - Key workflows to test (new E2E scenarios added)
  - Pre-push checklist (new test commands)
- **How:** Detect new test files, read their purpose, document new verification steps

**`iteration.md` - Iteration Workflow**
- **Triggers:** Version bumps, changelog additions, release process changes
- **What to update:**
  - Current version number
  - Recent releases in changelog
  - Release process steps (if CI release pipeline changed)
- **How:** Extract version from package.json, parse CHANGELOG.md if exists

**`platform.md` & `task-source.md`**
- **Triggers:** Rarely updated (only if remote URL changes or CLI tool versions change)
- **What to update:** Connection status, CLI version, discovered platform features
- **How:** Re-run platform detection commands

**`agent-profile.md`**
- **Triggers:** Rarely updated (only if explicit code style guidelines change)
- **What to update:** Code style preferences, testing coverage targets
- **How:** Manual update based on user feedback

#### Update Execution

1. **Read the current document** to understand its structure
2. **Identify the specific section(s)** to update
3. **Generate new content** by:
   - Re-analyzing the changed files
   - Extracting new information (dependencies, pipeline jobs, etc.)
   - Formatting it to match the existing document style
4. **Apply the update** using the Edit tool (preserve document structure)
5. **Show the diff** to the user for review
6. **Remind user to commit** the updated documentation

### 4. Missing Documentation Detection

If a project exists but lacks `.repo/{repoName}/` directory or some documentation files:

1. **Inform the user:** "This project doesn't have analysis documentation. Would you like me to run `/qoderwake-developer-project-analysis` to generate it?"
2. **If user agrees:** Trigger the analysis skill with detected repoUrl and repoRootPath
3. **If user declines:** Proceed with best-effort assistance based on direct file inspection

## Workflow Examples

### Example 0: Multi-Project Discovery (NEW)

**User:** "我的工作目录下有好几个项目,能帮我看看都有哪些项目吗?"

**Skill Actions:**
1. Search for `.repo/*/profile.md` pattern in current directory and parents
2. Find 3 projects: `frontend-web`, `backend-api`, `shared-utils`
3. Read each project's `profile.md` and `branching.md`
4. Present overview table:

```markdown
## Available Projects

| Project | Purpose | Tech Stack | Main Branch | Location |
|---------|---------|------------|-------------|----------|
| frontend-web | User-facing React web app | React, TypeScript, Vite | main | ~/workspace/frontend-web |
| backend-api | REST API service | Node.js, Express, PostgreSQL | master | ~/workspace/backend-api |
| shared-utils | Common utilities library | TypeScript, Bun | main | ~/workspace/shared-utils |

You can ask me about any project's conventions, or describe a task to find which repo(s) to modify.
```

### Example 0b: Locating Repo for Bugfix (NEW)

**User:** "我需要修复一个用户登录超时的 bug,应该在哪个 repo 改?"

**Skill Actions:**
1. Extract keywords: "用户登录", "超时" → ["login", "auth", "timeout", "session"]
2. **Semantic matching:** Read all projects' `profile.md`:
   - frontend-web: mentions "user authentication UI"
   - backend-api: describes "user authentication and session management module"
   - shared-utils: no authentication-related description
   - **Scores:** backend-api: 9/10, frontend-web: 5/10
3. **Code search:** Run `grep -r "login\|auth\|session\|timeout"` in each project:
   - backend-api: 43 matches (src/auth/session.ts, src/middleware/auth.ts, etc.)
   - frontend-web: 12 matches (components/LoginForm.tsx, hooks/useAuth.ts)
   - shared-utils: 0 matches
4. **Combine results:** backend-api is the clear winner (high semantic score + most code matches)
5. Read backend-api's `branching.md` for conventions
6. Present recommendation:

```markdown
## Recommended Repo: backend-api (High Confidence)

**Why:** Project profile describes "handles user authentication and session management" + found 43 files with login/session logic including `src/auth/session-timeout.ts`

**Location:** `~/workspace/backend-api`

**Development Conventions:**
- Main branch: `master`
- Feature branch format: `fix/login-session-timeout`
- Commit format: `fix(auth): resolve session timeout issue`
- Pre-push checklist:
  1. `bun test src/auth/**/*.test.ts`
  2. `bun run typecheck`
  3. `bun run build`

Ready to cd into this project?
```

### Example 0c: Multi-Repo Feature (NEW)

**User:** "我要开发一个新功能:在前端添加数据导出按钮,后端提供导出 CSV 的 API。这需要改哪几个 repo?"

**Skill Actions:**
1. Identify cross-cutting concern: frontend UI + backend API
2. **Frontend search:** Look for projects with "frontend", "web", "UI" in profile
   - Found: frontend-web (React app)
3. **Backend search:** Look for projects with "backend", "API", "server" in profile
   - Found: backend-api (REST API service)
4. For each project, read branching conventions
5. Present multi-repo plan:

```markdown
## Multi-Repo Feature Plan

This feature spans **2 repositories**:

### 1. backend-api
**What to do:** Add `/api/export/csv` endpoint
**Location:** `~/workspace/backend-api`
**Branch:** `feature/add-csv-export-api`
**Commit format:** `feat(api): add CSV export endpoint`

### 2. frontend-web
**What to do:** Add export button component and API integration
**Location:** `~/workspace/frontend-web`
**Branch:** `feature/add-export-button`
**Commit format:** `feat(ui): add data export button`

**Recommended workflow:**
1. Start with backend-api (implement and test API first)
2. Then implement frontend-web (consume the new API)
3. Test end-to-end integration

Ready to start with backend-api?
```

### Example 1: User Working on Bug Fix

**User:** "I need to fix a bug in the authentication module"

**Skill Actions:**
1. Detect project by finding `.repo/qoder-cloud-cli/` in parent directories
2. Read `verification.md` and `ci.md` for testing requirements
3. Read `agent-profile.md` for code style preferences
4. Present synthesized guidance:
   ```
   Before fixing the bug in qoder-cloud-cli:

   Testing Requirements (from verification.md):
   - Write unit tests for the fix
   - Run: bun test package/src/core/__tests__/*.test.ts
   - Run E2E: bun run scripts/e2e-real-cli.ts

   Code Style (from agent-profile.md):
   - Use TypeScript strict mode, explicit return types
   - Add descriptive error types (e.g., AuthenticationError)
   - Document error handling with JSDoc comments

   Pre-push Checklist (from ci.md):
   1. bun run typecheck
   2. bun test (focused tests)
   3. bun run build
   ```

### Example 2: Auto-Detect CI Config Change

**User makes commit changing `.aoneci/test.yaml`**

**Skill Actions:**
1. Detect modification to CI config file
2. Read `.aoneci/test.yaml` to understand new changes
3. Read `.repo/qoder-cloud-cli/ci.md` to check if it reflects the changes
4. Find discrepancy: new CI job added but not documented (high confidence scenario)
5. Automatically update `ci.md` with new job description
6. Show diff and notify:
   ```
   Updated ci.md to reflect the new "lint-check" job from .aoneci/test.yaml.

   Changes:
   - Added job description section for "lint-check"
   - Updated required checks count
   - Added pre-push command for lint

   Please review the changes and commit them.
   ```

### Example 3: User Asks About Branching

**User:** "What's the commit message format for this project?"

**Skill Actions:**
1. Locate project documentation
2. Read `branching.md`
3. Extract commit message section
4. Present formatted answer:
   ```
   qoder-cloud-cli uses Conventional Commits:

   Format: <type>(<scope>): <subject>

   Types: feat, fix, docs, style, refactor, test, chore

   Examples:
   - feat(daemon): add OAuth authentication support
   - fix(cli): resolve port conflict on daemon startup
   - chore(deps): update dependencies to latest versions

   See branching.md for full guidelines.
   ```

## Error Handling

**Project not found:**
- Check if user is in a Git repository
- Search parent directories for `.repo/` pattern
- If still not found, ask user: "Which project are you working on? Please provide the project path or repo name."

**Documentation files missing:**
- Suggest running `/qoderwake-developer-project-analysis` to generate them
- If user declines, fall back to direct file inspection

**Stale detection uncertainty:**
- If unsure whether documentation needs updating, skip the update
- User can manually update or explicitly request documentation updates later

**Update conflicts:**
- If user modified documentation manually and auto-update would conflict, skip the automatic update to preserve user changes
- User can manually reconcile or explicitly request a forced update

## Important Notes

- **Confidence-based updates:** Only auto-update documentation when you have high confidence (clear, objective changes). If uncertain, skip the update without asking.
- **Preserve document structure:** When updating, match existing formatting, tone, and organization
- **Show diffs:** Always show what changed so users can review
- **Context-aware reading:** Don't dump entire documents; extract relevant information based on user's task
- **Complement, don't replace analysis:** This skill maintains docs; `/qoderwake-developer-project-analysis` generates them initially
- **No confirmation prompts:** Never ask "Would you like me to update...?" — either update confidently or skip silently
