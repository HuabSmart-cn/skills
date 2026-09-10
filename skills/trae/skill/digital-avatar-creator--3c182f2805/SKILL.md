---
name: "digital-avatar-creator"
description: "MANDATORY tool for creating digital avatar skills that run as autonomous SubAgents. MUST be invoked IMMEDIATELY when user wants to create a digital avatar, persona, virtual role, or specialized AI assistant."
---

# Digital Avatar Creator

This skill creates digital avatar skills. Each avatar is a SubAgent that autonomously handles user requests within its defined expertise.

## When to Use

**CRITICAL: Invoke this skill IMMEDIATELY as your FIRST action when:**

- User wants to create a digital avatar, virtual persona, or specialized assistant
- User mentions creating/adding a digital twin, persona, agent, or autonomous helper

**DO NOT:**

- Just explain how to create an avatar without invoking this skill
- Provide manual instructions without using this skill first
- Defer the avatar creation to later steps

## Language Rule (Highest Priority)

**CRITICAL**: Detect the language from the user's input. ALL generated avatar content — `name`, `description`, detail body, examples — MUST be written entirely in that same language. Do NOT mix languages.

- If the user communicates in Chinese, generate everything in Chinese.
- If the user communicates in English, generate everything in English.
- This rule overrides any English templates or examples below. Translate them into the user's language when generating.

## Created Avatar SKILL.md Structure

Every digital avatar MUST follow this exact format:

### Frontmatter

```yaml
---
name: "<role-name>"
description: "<capabilities-description>. When user intent matches this avatar's skills, drive this avatar via Task tool to fulfill the user's intent"
mode: agent
context: isolated # Optional: history context strategy (isolated | same_type | same_type_with_main | fork)
allowed-tools: # Optional: restrict which tools this avatar can use
  - Read
  - Grep
  - Edit
skills: # Optional: declare sub-skills this avatar depends on
  - "sub-skill-name"
custom-tools: # Optional: declare custom shell-based tools this avatar provides
  - "tool-name"
---
```

**Field Rules:**

- `name`: The avatar's role name in kebab-case (e.g., `code-reviewer`, `data-analyst`)
- `description`: First describe the avatar's skills and capabilities, then ALWAYS append a trigger clause stating that when user intent matches this avatar's skills, it should be driven via Task tool to fulfill the request
- `mode`: MUST be `agent` — every digital avatar runs as a SubAgent
- `context` _(optional)_: Controls the history context strategy for the sub-agent. Determines how much conversation history the avatar can see. Available values:
  - `isolated` (default): The avatar has a completely independent history, no prior context is loaded
  - `same_type`: Loads history from the same agent type + current turn's root agent
  - `same_type_with_main`: Loads history from the same agent type + all root agent history
  - `fork`: Loads the entire conversation history up to this point
    When omitted, defaults to `isolated`. Use `same_type`, `same_type_with_main`, or `fork` when the avatar needs awareness of prior conversation context to work effectively
- `allowed-tools` _(optional)_: A list of tool names this avatar is allowed to use. When specified, the avatar can ONLY call tools in this list (it is a **whitelist**, not an incremental addition). When omitted, the avatar falls back to the **main agent's (Level-0) full tool list** — not necessarily all tools in existence. Each name is automatically expanded to all its internal tool variants. **Available tool names:**

  | Name | Description | Expands to |
  |------|-------------|------------|
  | `Read` | File reading, viewing, and codebase search | Read, ViewFile, ViewFiles, SearchCodebase, LS, etc. |
  | `Grep` | Regex and keyword search | Grep, SearchByRegex, SearchByKeyword |
  | `Glob` | File name pattern matching | Glob, FileSearch |
  | `Write` | File creation and writing | Write, WriteToFile |
  | `Edit` | File editing, deleting, renaming, and patching | Edit, MultiEdit, ApplyPatch, DeleteFile, etc. |
  | `Bash` | Terminal command execution and management | RunCommand, CheckCommandStatus, StopCommand, OpenPreview, etc. |
  | `WebSearch` | Web search | WebSearch |
  | `WebFetch` | Web page content fetching | WebFetch |
  | `TodoWrite` | Task list management | TodoWrite |
  | `LSP` | Language server diagnostics | GetDiagnostics |
  | `AskUserQuestion` | Ask clarifying questions to the user | AskUserQuestion |
  | `Skill` | Skill loading and recommendation | Skill, SkillRecommend |

  **⚠️ CAUTION: If a tool name is misspelled or does not exist in the table above, the avatar will silently lose access to that tool. Do NOT include this field unless the user explicitly requests tool restrictions — by default, the avatar inherits the main agent's tool list, which is the recommended behavior.**
- `skills` _(optional)_: A list of other skill names that this avatar depends on or can invoke. Two behaviors based on skill mode:
  - **Default-mode skills** are loaded via the Skill tool and executed locally on the client side within the avatar's context.
  - **Agent-mode skills** become sub-agents callable via the Task tool. **Important: The Task tool at each layer only lists its _direct_ child agents — grandchild agents are NOT visible across layers.** The maximum nesting depth is **5 levels** (`MAX_SUBAGENT_DEPTH = 5`); declaring deeper nesting will be silently truncated.
    When omitted, no additional skills are attached.
- `custom-tools` _(optional)_: A list of custom tool names this avatar provides. Each listed tool MUST have a corresponding directory at `.trae/skills/<avatar-name>/tools/<tool-name>/` containing a `tool.yaml` definition and a `run.sh` entry script. These tools are exposed to the LLM as native function calls and executed locally on the client side

### Detail (Body)

The body MUST follow the Agent identity + workflow pattern:

```
# <Avatar Name>

You are <identity and expertise description>.

## Workflow

1. <Step based on the avatar's specific role>
2. <Step>
3. ...
N. When uncertain about user requirements, use AskUserQuestion tool to clarify before proceeding.
```

**Structure Rules:**

- **Top section**: Avatar identity — who it is, its name and role
- **Workflow section**: Concrete steps the avatar follows to complete tasks, derived from the user's creation intent and the avatar's capabilities
- **Clarification**: The workflow MUST include a step about using `AskUserQuestion` when the avatar needs to clarify ambiguous requirements

### Avatar Icon

Each avatar MUST have an icon file at `.trae/skills/<avatar-name>/icon.png`. The system automatically detects icon files named `icon.png`, `icon.jpg`, `icon.jpeg`, `icon.svg`, or `icon.webp` in the skill directory and displays them as the avatar's profile picture.

**Icon generation rules:**

1. **User provides an icon URL**: Download the image and save it as `.trae/skills/<avatar-name>/icon.png`
2. **User does NOT provide an icon URL**: Use `AskUserQuestion` to ask the user how they want the avatar icon to look (style, color, elements, etc.). Based on their feedback, call the `GenerateImage` tool with a detailed prompt to create the icon:
   - `prompt`: A detailed description of the avatar icon based on user feedback
   - `file_path`: `.trae/skills/<avatar-name>/icon.png`
   - `image_size`: `512x512`

### Custom Tools (Optional)

When an avatar needs to perform specialized operations beyond the built-in tools (e.g., calling external APIs, running data processing scripts, interacting with specific services), you can define custom tools that the avatar can invoke as native function calls.

**Directory structure:**

```
.trae/skills/<avatar-name>/
├── SKILL.md
├── icon.png
└── tools/
    └── <tool-name>/
        ├── tool.yaml    # Tool definition (name, description, parameters)
        └── run.sh       # Entry script (executable)
```

**`tool.yaml` format:**

```yaml
name: "<tool-name>"
description: "What this tool does — clear enough for the LLM to decide when to call it"
parameters:
  type: object
  properties:
    param1:
      type: string
      description: "Description of param1"
    param2:
      type: integer
      description: "Description of param2"
  required:
    - param1
```

**`run.sh` execution protocol:**

- **Input**: LLM-provided arguments are passed as JSON via `stdin`
- **Output**: Tool result written to `stdout` (returned to LLM as tool_call result)
- **Errors**: Non-zero exit code = failure; `stderr` content becomes the error message
- **Working directory**: The tool's own directory (`tools/<tool-name>/`)
- **Locating tool assets**: Use `TOOL_DIR="$(cd "$(dirname "$0")" && pwd)"` to get the absolute path of the tool's directory

**Example `run.sh`:**

```bash
#!/bin/bash
TOOL_DIR="$(cd "$(dirname "$0")" && pwd)"

# Read arguments from stdin
INPUT=$(cat)
QUERY=$(echo "$INPUT" | jq -r '.query')

# Execute tool logic (can call python, node, etc.)
python3 "$TOOL_DIR/search.py" "$QUERY"
```

**Rules:**

- Tool names MUST be in kebab-case (e.g., `search-docs`, `run-tests`)
- Every tool listed in `custom-tools` frontmatter MUST have a matching `tools/<tool-name>/` directory
- **The tool subdirectory name MUST match the `name` field in its `tool.yaml` exactly** — the loader validates this at load time; a mismatch will cause the tool to fail silently
- `run.sh` MUST be executable (`chmod +x`)
- Environment dependencies (e.g., Python 3, Node.js, jq) MUST be documented in the **SKILL.md Prompt body** (not in `tool.yaml`) under a "Prerequisites" or "Environment" section — this is where users read the setup instructions
- Do NOT rely on injected environment variables — scripts should be self-contained

## Creation Workflow

### Step 1: Gather Requirements

Understand from the user:

1. What role/identity should the avatar have?
2. What skills and capabilities should it possess?
3. What kind of tasks should it handle?
4. Does it need custom tools for specialized operations (e.g., calling APIs, running scripts, data processing)?

**If any of the above is unclear or ambiguous, use `AskUserQuestion` to clarify with the user before proceeding.**

### Step 2: Design the Avatar

Based on user input, design:

- A clear `name` in kebab-case
- A `description` covering capabilities + the trigger clause
- An Agent-style detail with identity at the top and a role-specific workflow below
- _(Optional)_ `context`: If the avatar needs awareness of prior conversation history (e.g., following up on earlier discussion, referencing previously reviewed code), set to `same_type` or `fork`. Otherwise, leave it unset (defaults to `isolated` for a clean slate each time)
- _(Optional)_ `allowed-tools`: Only include this field if the user **explicitly** requests tool restrictions. Misspelled or non-existent tool names will silently fail. When in doubt, omit this field — the avatar will fall back to the main agent's tool list by default
- _(Optional)_ `skills`: If the avatar needs to leverage other existing skills, include this field. Ask the user if there are related skills to attach. Note: agent-mode sub-skills are only callable from their direct parent — not across layers. Maximum nesting depth is 5 levels
- _(Optional)_ `custom-tools`: If the avatar needs specialized operations that built-in tools cannot handle (e.g., calling external APIs, running domain-specific scripts), design custom tools. For each custom tool, define its name, description, parameters (JSON Schema), and implement the `run.sh` script
- **All content in the user's language**

### Step 3: Create the SKILL File

1. Create directory: `.trae/skills/<avatar-name>/`
2. Create `SKILL.md` inside the directory with proper frontmatter and detail
3. Ensure `mode: agent` is present in frontmatter
4. If custom tools are needed:
   - Create `tools/<tool-name>/` directory for each tool
   - Create `tool.yaml` with name, description, and parameters (JSON Schema)
   - Create `run.sh` with the execution logic and make it executable
   - Add tool names to `custom-tools` list in frontmatter

### Step 4: Generate Avatar Icon

1. If the user provided an icon URL, download it and save as `.trae/skills/<avatar-name>/icon.png`
2. If the user did NOT provide an icon URL:
   - Use `AskUserQuestion` to ask the user about their preferred icon style, such as color scheme, visual elements, art style, or any specific imagery they want
   - Based on user feedback, call `GenerateImage` with a detailed prompt and save to `.trae/skills/<avatar-name>/icon.png`

### Step 5: Validate

- Confirm frontmatter has `name`, `description`, and `mode: agent`
- Verify the detail starts with the avatar's identity
- Check the workflow is concrete and actionable for the role
- Ensure the description ends with the trigger clause
- Confirm `icon.png` (or another supported format) exists in the skill directory
- If `custom-tools` is present, verify each tool has a matching `tools/<tool-name>/` directory with `tool.yaml` and `run.sh`
- **Ensure no mixed languages in the generated content**

## Examples

### Example 1: Basic Avatar (no custom tools)

When the user says: "Create a data analyst avatar for me"

**`.trae/skills/data-analyst/SKILL.md`**:

```markdown
---
name: "data-analyst"
description: "Professional data analysis avatar skilled in interpreting datasets, identifying trends, writing analysis scripts, and producing clear summaries. When user intent matches this avatar's skills, drive this avatar via Task tool to fulfill the user's intent"
mode: agent
context: same_type
---

# Data Analyst

You are a senior data analyst with deep expertise in statistical analysis, data visualization, and deriving actionable insights from raw datasets.

## Workflow

1. Receive the dataset or data source reference from the user
2. Explore the data structure and understand key fields and distributions
3. Identify trends, anomalies, and patterns relevant to the user's question
4. Produce a structured analysis summary with key findings and recommendations
5. When uncertain about the analysis goal, metrics of interest, or data format, use AskUserQuestion to clarify before proceeding
```

**`.trae/skills/data-analyst/icon.png`**: Generated via `GenerateImage` tool after asking user for icon preferences.

### Example 2: Avatar with context strategy

When the user says: "Create a code review avatar for me"

**`.trae/skills/code-reviewer/SKILL.md`**:

```markdown
---
name: "code-reviewer"
description: "Professional code review avatar skilled in code quality assessment, best practice recommendations, bug detection, and performance optimization suggestions. When user intent matches this avatar's skills, drive this avatar via Task tool to fulfill the user's intent"
mode: agent
context: same_type
---

# Code Reviewer

You are a senior code reviewer with deep expertise in software engineering best practices, code quality assessment, and bug detection.

## Workflow

1. Receive code or file references to review from the user
2. Read and analyze the target code's structure, logic, and patterns
3. Identify issues across dimensions: correctness, performance, readability, security, and style
4. Provide prioritized, actionable improvement suggestions with concrete code examples
5. When uncertain about review scope, coding standards, or focus areas, use AskUserQuestion to clarify with the user before starting
```

**`.trae/skills/code-reviewer/icon.png`**: Generated via `GenerateImage` tool after asking user for icon preferences.

### Example with Custom Tools

When the user says: "Create an avatar that can query our internal API for user info"

**`.trae/skills/api-assistant/SKILL.md`**:

```markdown
---
name: "api-assistant"
description: "Internal API assistant that can query user information from the company's REST API. When user intent matches this avatar's skills, drive this avatar via Task tool to fulfill the user's intent"
mode: agent
custom-tools:
  - "query-user"
---

# API Assistant

You are an internal API assistant specialized in querying and presenting user information from the company's REST API.

## Prerequisites

- `curl` and `jq` must be available in PATH

## Workflow

1. Receive the user's query about user information (user ID, email, name, etc.)
2. Use the `query-user` tool with appropriate parameters to fetch data from the API
3. Parse and format the returned JSON into a clear, readable summary
4. If the query fails or returns unexpected results, report the error and suggest alternatives
5. When uncertain about which user or what information to retrieve, use AskUserQuestion to clarify
```

**`.trae/skills/api-assistant/tools/query-user/tool.yaml`**:

```yaml
name: "query-user"
description: "Query user information from the internal REST API by user ID or email"
parameters:
  type: object
  properties:
    user_id:
      type: string
      description: "The user ID to query"
    email:
      type: string
      description: "The user email to query (alternative to user_id)"
  required: []
```

**`.trae/skills/api-assistant/tools/query-user/run.sh`**:

```bash
#!/bin/bash
TOOL_DIR="$(cd "$(dirname "$0")" && pwd)"

INPUT=$(cat)
USER_ID=$(echo "$INPUT" | jq -r '.user_id // empty')
EMAIL=$(echo "$INPUT" | jq -r '.email // empty')

if [ -n "$USER_ID" ]; then
  curl -s "https://internal-api.company.com/users/$USER_ID"
elif [ -n "$EMAIL" ]; then
  curl -s "https://internal-api.company.com/users?email=$EMAIL"
else
  echo '{"error": "Either user_id or email must be provided"}' >&2
  exit 1
fi
```
