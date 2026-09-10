---
name: qoderwake-developer-project-analysis
description: Deep repository analysis and onboarding skill for Git projects. Use this skill when users want to analyze a codebase, onboard a new repository, understand project structure, or generate comprehensive documentation for a Git repo. Triggers on phrases like "analyze this repo", "onboard this project", "generate project docs", or when given a Git repository URL for analysis. This skill performs multi-step analysis including architecture mapping, dependency detection, CI/CD discovery, and generates 8+ markdown documentation files.
---

# QoderWake Developer Project Analysis

This skill performs comprehensive analysis of a Git repository and generates detailed documentation to help AI agents and developers work effectively with the codebase.

## Overview

The skill executes **9 steps** to analyze a repository, generating documentation files stored in `{repoRootPath}/.repo/{repoName}/`:

1. Deep repository exploration (file system, build manifests, dependencies, tests, service startup)
2. Project profile generation (`profile.md`)
3. Platform detection and integration (`platform.md`, `task-source.md`)
4. Branching strategy (`branching.md`)
5. Iteration workflow (`iteration.md`)
6. CI/CD integration (`ci.md`)
7. Agent behavior profile (`agent-profile.md`)
8. Verification strategy (`verification.md`)
9. Final validation

## Input Parameters

The skill requires two parameters, obtained in this order:

1. **First, check environment variables:**
   - `REPO_URL` - Git repository URL
   - `REPO_ROOT_PATH` - Parent directory where repos are stored

2. **If environment variables are missing, check user input:**
   - Extract `repoUrl` and `repoRootPath` from the user's message

3. **If either parameter is missing:**
   - Exit immediately with error: "Missing required parameters. Please provide REPO_URL and REPO_ROOT_PATH via environment variables or in your message."

**Derived values:**
- `repoName` - Extract from URL (e.g., `https://github.com/owner/repo.git` → `repo`)
- `repoPath` - `{repoRootPath}/{repoName}`
- `repoDocumentPath` - `{repoRootPath}/.repo/{repoName}`

## Directory Structure

```plaintext
repoRootPath/
    ├── {repoName}/          # Git repo source code
    └── .repo/
        └── {repoName}/      # Analysis artifacts
            ├── profile.md
            ├── platform.md
            ├── task-source.md
            ├── branching.md
            ├── iteration.md
            ├── ci.md
            ├── agent-profile.md
            └── verification.md
```

## Execution Flow

### Step 0: Clone Repository (if needed)

1. Check if `{repoPath}` already exists
2. If not, clone the repository: `git clone {repoUrl} {repoPath}`
3. If clone fails, exit with error message explaining the failure reason
4. Create the documentation directory: `mkdir -p {repoDocumentPath}`

### Step 1: Deep Repository Exploration

This step thoroughly explores the repository structure, attempts installations, builds, and service startup to understand the project comprehensively.

#### Phase A: File System Discovery & Architecture Mapping

1. **List directory structure** (3 levels deep) to understand the project layout
2. **Find all build manifest files:**
   - `package.json`, `pnpm-workspace.yaml`, `yarn.lock` (Node.js)
   - `go.mod`, `go.work` (Go)
   - `Cargo.toml` (Rust)
   - `pom.xml`, `build.gradle` (Java)
   - `pyproject.toml`, `requirements.txt` (Python)
   - `Makefile`, `CMakeLists.txt` (C/C++)
   - Each file represents a module boundary
3. **Detect `.git` directories** to identify multi-repo setups
4. **Read existing documentation** in the project (don't assume specific filenames)
5. **For monorepos, identify workspace configuration:**
   - `pnpm-workspace.yaml`, `lerna.json`, `turbo.json`, `go.work`, etc.
6. **For each discovered module, identify:**
   - Language and framework
   - Role (frontend/backend/library/CLI/infrastructure)
   - Entry points
7. **Map inter-module dependencies:**
   - Import paths
   - Workspace references
   - Docker Compose `depends_on`
   - Shared libraries
8. **Inspect key files:**
   - `Dockerfile`, `docker-compose.yml`
   - CI/CD config files
   - API contracts (protobuf, OpenAPI, GraphQL schemas)
   - Config files (`.env.example`, `tsconfig.json`, `vite.config.*`, etc.)

#### Phase B: Dependency Installation

1. For each module, detect package manager from lockfiles:
   - `package-lock.json` → npm
   - `yarn.lock` → yarn
   - `pnpm-lock.yaml` → pnpm
   - `go.sum` → `go mod download`
   - `Cargo.lock` → `cargo build`
   - etc.
2. Run installation commands for each module
3. If installation fails and you cannot fix it → skip and continue
4. If all installations succeed, report results and continue

#### Phase C: Build Validation

1. For each module, run build commands (detect from `package.json` scripts, Makefile targets, CI config, etc.)
2. If build fails and you cannot fix it → skip and continue
3. If all builds succeed, report results and continue

#### Phase D: Quick Test

1. Run tests only for critical modules (not full test suite - just enough to verify environment works)
2. If tests take too long → skip and continue
3. If tests fail → skip and continue
4. If tests pass, report results and continue

#### Phase E: Full Project Startup

1. Actually start all services: backend servers, frontend dev servers, databases, middleware, etc.
2. If `docker-compose.yml` exists, run `docker-compose up -d`
3. After startup, verify services respond correctly (curl health endpoints, check ports)
4. If any service fails to start or is unreachable → skip and continue
5. After verification, stop all started services (cleanup)

#### Final Summary

After all phases, display a comprehensive summary:
- Architecture diagram (ASCII art)
- Technology stack table (by module)
- Status table: installation/build/test/startup results for each module
- Any issues discovered and environment prerequisites

### Step 2: Project Profile (`{repoDocumentPath}/profile.md`)

Generate project profile based on everything learned in Step 1. If insufficient information to make reasonable inferences, skip this step.

Document:
- Business context and product form
- Key modules and their purposes
- Coding conventions or special agreements
- Any other information AI agents should know when working on this project

Write the final `{repoDocumentPath}/profile.md`.

### Step 3: Change Platform Detection & Task Source

This step identifies the change platform and discovers project configuration files locally.

#### Phase A: Platform Discovery

1. Run `git remote -v` to detect remote URL
2. Analyze remote URL to identify platform and extract metadata:
   - `github.com` → GitHub (extract owner/repo from URL)
   - `gitlab.com` or `gitlab.*.com` → GitLab (extract owner/repo from URL)
   - `bitbucket.org` → Bitbucket (extract owner/repo from URL)
   - Other or none → No change platform detected

#### Phase B: Repository Access Verification

Test repository access using Git commands:

```bash
# Verify remote access
git ls-remote origin HEAD > /dev/null 2>&1
```

If this succeeds, repository access is confirmed. If it fails, note "Repository access check failed - may require authentication setup."

#### Phase C: Local File Discovery

Discover platform-specific configuration files already present in the repository:

**For GitHub:**
- `.github/workflows/*.yml` or `.github/workflows/*.yaml` → GitHub Actions workflows
- `.github/pull_request_template.md` or `.github/PULL_REQUEST_TEMPLATE/*.md` → PR templates
- `.github/ISSUE_TEMPLATE/*.md` → Issue templates
- `.github/CODEOWNERS` → Code review rules
- List all discovered files with brief descriptions

**For GitLab:**
- `.gitlab-ci.yml` → GitLab CI configuration
- `.gitlab/merge_request_templates/*.md` → MR templates
- `.gitlab/issue_templates/*.md` → Issue templates
- `CODEOWNERS` or `.gitlab/CODEOWNERS` → Code review rules
- List all discovered files with brief descriptions

**For Bitbucket:**
- `bitbucket-pipelines.yml` → Bitbucket Pipelines
- Check for `CODEOWNERS` file

**For all platforms:**
- Check for pre-commit hooks: `.husky/`, `.pre-commit-config.yaml`, `lefthook.yml`

#### Phase D: Generate Web UI Links

Based on the remote URL and platform type, generate helpful Web UI links:

**URL parsing logic:**
```
# Example: git@gitlab.alibaba-inc.com:qoder-cloud-agents/qoder-cloud-cli.git
# → https://gitlab.alibaba-inc.com/qoder-cloud-agents/qoder-cloud-cli

# Example: https://github.com/owner/repo.git
# → https://github.com/owner/repo
```

**Generate links for:**
- Repository home page
- Branches page (e.g., `{base_url}/-/branches` for GitLab, `{base_url}/branches` for GitHub)
- New PR/MR page (e.g., `{base_url}/-/merge_requests/new` for GitLab)
- Issues page
- CI/CD pipelines page
- Settings page (for branch protection, etc.)

#### Phase E: Write Documentation

Write `{repoDocumentPath}/platform.md` documenting:
- Platform type: github / gitlab / bitbucket / other
- Remote URL
- Extracted owner/repo information
- Repository access status (from `git ls-remote` test)
- **Discovered local files** (workflows, templates, CODEOWNERS, hooks)
- **Generated Web UI links** for common operations:
  - View repository
  - View branches
  - Create PR/MR
  - View issues
  - View CI/CD pipelines
  - View settings
- Note: "This analysis is based on local files and Git commands. Platform-specific features (branch protection, required reviewers) must be verified via Web UI."

Write `{repoDocumentPath}/task-source.md` documenting:
- Platform issue tracker URL (generated from remote URL)
- How to access issues/tasks via Web UI
- Recommended task reference format in branch names and commits (e.g., "PROJ-123", "#123")
- Example workflow: "Check issues at [Web UI link] → Create branch with task ID → Reference task in commits"

### Step 4: Branching Strategy (`{repoDocumentPath}/branching.md`)

Read `{repoDocumentPath}/platform.md` to determine if a change platform is available.

#### Investigation

1. **Analyze branches**:
   ```bash
   git branch -a  # All local and remote branches
   git ls-remote --heads origin  # Remote branches only
   ```

2. **Understand commit history**:
   ```bash
   git log --oneline -50  # Recent commit messages
   ```
   - Check for Conventional Commits patterns (`feat:`, `fix:`, `chore:`, etc.)
   - Identify common commit message structure

3. **Detect default branch**:
   ```bash
   git symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@'
   ```

4. **Check for local configuration files** that indicate branching policies:
   - `.github/branch_protection.yml` or similar
   - CI config files that have branch-specific rules
   - `.git/config` for any branch-specific settings

#### Write Documentation

Write `{repoDocumentPath}/branching.md` documenting:
- **Branch model** with ASCII diagram if helpful (trunk-based, git-flow, etc.)
- **Default/main branch name** (detected from git)
- **Branch naming conventions** inferred from history:
  - Features: `feature/TASK-XXX-description` or `feat/description`
  - Bugfixes: `fix/TASK-XXX-description` or `bugfix/description`
  - Releases: `release/vX.Y.Z`
  - Hotfixes: `hotfix/description`
- **Commit message format** with real examples from history:
  - If Conventional Commits detected: document the types and scopes used
  - If custom format: document the pattern observed
  - Provide 3-5 real commit message examples
- **PR/MR creation workflow**:
  - "Create via Web UI: [link to new PR/MR page from platform.md]"
  - List any PR/MR templates found (from Step 3)
  - Example: "To work on task PROJ-123, create branch feature/PROJ-123-add-login from main, implement, push, then create MR via [Web UI link]"
- **Note on branch protection**: "Branch protection rules (required reviewers, status checks, force push restrictions) must be verified via Web UI: [link to settings page]"

### Step 5: Iteration Workflow (`{repoDocumentPath}/iteration.md`)

Read `{repoDocumentPath}/platform.md` and `{repoDocumentPath}/branching.md` for context.

#### Investigation

1. **Check git tags and release history**:
   ```bash
   git tag --sort=-creatordate | head -10
   git log --tags --simplify-by-decoration --pretty="format:%ci %d" | head -20
   ```

2. **Check for changelog and release notes files**:
   - `CHANGELOG.md`, `HISTORY.md`, `RELEASES.md`
   - `docs/releases/`, `docs/changelog/`

3. **Check version patterns in build manifests**:
   - `package.json` version field
   - `Cargo.toml` version field
   - `pyproject.toml` version field
   - `pom.xml` version tag

4. **Infer release rhythm from git tags**:
   - Analyze tag date intervals to determine release frequency
   - Check if tags follow semantic versioning pattern
   - Look for prerelease tags (alpha, beta, rc)

Write `{repoDocumentPath}/iteration.md` documenting:
- Sprint/iteration cycle and release rhythm (inferred from tag intervals)
- Changelog strategy (based on discovered files)
- Version numbering scheme (detected from tags and manifests)
- Release process and triggers (inferred from CI config and git history)

### Step 6: CI/CD Integration (`{repoDocumentPath}/ci.md`)

Read `{repoDocumentPath}/platform.md`, `{repoDocumentPath}/branching.md`, and `{repoDocumentPath}/iteration.md` for context.

#### Investigation

1. **Find CI/CD config files in repository**:
   - `.github/workflows/*.yml` (GitHub Actions)
   - `.gitlab-ci.yml` (GitLab CI)
   - `.aoneci/` (AoneCI)
   - `Jenkinsfile` (Jenkins)
   - `.circleci/config.yml` (CircleCI)
   - `bitbucket-pipelines.yml` (Bitbucket Pipelines)
   - Other CI configs

2. **Read and analyze discovered CI config files**:
   - What events trigger pipelines (push, PR, merge, tag, schedule)
   - What jobs/stages are defined
   - What tasks run in each job
   - Which checks must pass before merge
   - Environment variable requirements

3. **Check Makefile or package manager scripts** for encapsulated CI commands:
   - `package.json` scripts: "ci", "lint", "check", "format", "test"
   - `Makefile` targets
   - `build.gradle` tasks
   - `Cargo.toml` scripts

4. **Check for pre-commit hooks**:
   - `.husky/` directory
   - `.pre-commit-config.yaml`
   - `lefthook.yml`
   - `.git/hooks/` directory

5. **Extract local verification commands** from CI config:
   - Parse CI YAML to find actual commands run (e.g., `bun run typecheck`, `npm test`)
   - Document the exact sequence needed to replicate CI checks locally

Write `{repoDocumentPath}/ci.md` documenting:
- CI/CD platform and config file locations
- Pipeline overview: what events trigger what (push, PR, merge, tag, schedule)
- Required checks before merge (and exact commands for local verification)
- Pre-push checklist: exact command sequence AI agents must run before pushing code (e.g., lint → format → type-check → build → test)
- Deployment process for each environment (inferred from CI config)
- Required environment variable names (not values - just names and descriptions from CI config)
- Known CI quirks, flaky tests, and workarounds (if evident from config comments or retry logic)
- How to read CI results: include Web UI link to pipelines page (generated from git remote URL + platform type)

### Step 7: Agent Behavior Profile (`{repoDocumentPath}/agent-profile.md`)

Generate an agent profile documenting AI agent behavior preferences when working with this project. This helps future agents understand the preferred working style.

Document:
- Code style preferences (formatting, naming conventions)
- Testing approach (when to write tests, coverage expectations)
- Documentation expectations (when to update docs, what level of detail)
- Communication style (how to report progress, when to ask for confirmation)
- Risk tolerance (when to be conservative vs. experimental)

Write `{repoDocumentPath}/agent-profile.md`.

### Step 8: Verification Strategy (`{repoDocumentPath}/verification.md`)

Based on project architecture and tech stack discovered in Step 1, help define verification strategy for future development tasks.

**Strongly recommend end-to-end (E2E) testing** as primary verification method. Explain to user:
- Unit tests alone are insufficient - they verify isolated logic but miss integration issues, UI regressions, and real user workflow breakage
- E2E tests verify the entire system like a real user would, catching issues across module boundaries
- For AI-driven development, E2E tests serve as objective "acceptance gates" proving functionality actually works

Recommend specific E2E frameworks based on project type detected in Step 1:

| Project Type | Recommended Framework | Notes |
|--------------|----------------------|-------|
| Web apps (React, Vue, Angular, etc.) | **Playwright** | Cross-browser, auto-wait, best DX |
| Electron desktop apps | **Playwright (Electron mode)** | Native Electron support via electron.launch() |
| Mobile apps (React Native, Flutter) | **Maestro** or **Detox** | Maestro cross-platform, Detox for RN |
| macOS native apps | **XCUITest** (via xcrun) | Apple's built-in UI testing framework |
| Windows native apps (WPF, WinForms, etc.) | **WinAppDriver** + **Appium** | Microsoft's Windows app UI automation |
| Cross-platform desktop (Tauri, Qt, etc.) | **Playwright** or **Appium** | Playwright for webview-based; Appium otherwise |
| CLI / backend API only | **Integration tests** + **API tests** | Use project's native test runner + curl/httpie verification |
| VS Code / IDE extensions | **VS Code Extension Test** (@vscode/test-electron) | Official VS Code testing framework |

1. If no E2E framework exists yet, generate minimal bootstrap setup:
   - Install selected framework as dev dependency
   - Create config file (e.g., `playwright.config.ts`)
   - Write 1-2 smoke tests verifying basic app launch and one key workflow
   - Run tests to verify setup works
2. Write `{repoDocumentPath}/verification.md` documenting:
   - Selected verification strategy and framework
   - How to run verification (exact commands)
   - Key workflows that must be tested
   - Environment prerequisites
   - Whether verification is blocking or advisory

### Step 9: Final Validation

- Run build and test commands again to confirm everything still works
- Verify all `{repoDocumentPath}` documents were created: `platform.md`, `task-source.md`, `branching.md`, `iteration.md`, `ci.md`, `profile.md`, `agent-profile.md`, `verification.md`
- Display comprehensive summary of everything created:
  - Generated documents
  - Registered skills (if any)
  - Platform integration status
  - Environment health status
- Mark work as completed after all steps finish

## Error Handling Philosophy

**Critical steps that must succeed (exit if they fail):**
- Obtaining `repoUrl` and `repoRootPath` parameters
- Cloning the repository (if needed)

**Optional steps that can be skipped (continue if they fail):**
- Dependency installation
- Build validation
- Running tests
- Service startup
- Repository access verification (if `git ls-remote` fails, note it and continue)
- Any discovery/analysis that doesn't block documentation generation

When skipping a failed step, note the failure in the documentation so users understand the limitations.

## Important Notes

- This skill operates fully autonomously - do not ask users for confirmation during execution
- If something cannot be resolved automatically, skip it and document the issue
- Focus on generating useful documentation even when some steps fail
- Be thorough in exploration but pragmatic about failures
- All generated documentation should be actionable and specific, not generic advice
