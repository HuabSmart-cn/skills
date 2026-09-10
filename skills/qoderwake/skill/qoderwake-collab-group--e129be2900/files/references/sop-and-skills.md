# SOP and Skill ownership reference

Read this before persisting any rule, knowledge, or capability for the Group.
The decision table in `SKILL.md` chooses the surface; this file gives the exact
procedures and the boundaries that must not be crossed.

## The four surfaces

| Need | Surface | Boundary |
| --- | --- | --- |
| Define how several members coordinate, hand off, approve, keep secrets, order steps, check progress, or finish | **Group collaboration rule = ***REDACTED***
| Share reusable business knowledge, tools, or working methods with current and future members | **Group Skill** | Group-specific and useful to more than one member; never defines collaboration protocol |
| Give one Group Waker a capability only for the current assignment | **Per-Waker temporary Skill overlay** | Target Waker, task, and expiry explicit; Run/assignment-scoped; never persisted into the Group binding or the Waker SkillStore |
| Strengthen one Waker's durable identity or capability across Groups and direct work | **The Waker's own Skill** | Persist only when the capability remains useful outside this Group |

In product language **a collaboration rule is an SOP** and **a Group Skill is a
shared business Skill**; do not use the names interchangeably.

### Classification rules

1. Classify by the requested behavior, not by the label. If any part of the
   content defines collaboration or SOP semantics (member roles, coordination,
   handoffs, approvals, confidentiality, execution order, progress checkpoints,
   completion conditions), the whole request is an SOP, even when the user calls
   it a “Group Skill” or “群技能”. Only when none of those properties apply does
   shared knowledge, a tool, or a reusable method become a Group Skill.
2. The user's wording can select the SOP path outright: SOP, 解决方案,
   协作 / 协同 / 协作方式, 团队 / 团队协作, 分工 / 角色分工,
   协作流程 / 工作流程 / 流程, 协作机制 / 机制, or a request to land, create, or
   confirm a team design, role split, or way of working the conversation just
   iterated on (“确认创建”, “就这样落地”, “把这版团队定下来”). The classification
   is then decided: publish and bind an SOP, and do not ask a clarifying
   question.
3. The wording rule needs an intent to establish, persist, change, or confirm.
   A question or passing reference about the current way of working (“团队现在的
   工作流程是什么”) is not a persistence request: answer it and persist nothing.
4. If neither behavior nor wording points at collaboration and the request is
   still genuinely ambiguous, ask one concise clarifying question first. Make no
   file, catalog, binding, or SkillStore change until the user answers.
5. Do not choose a Group Skill merely because the request arrived in a Group,
   and do not permanently modify a Waker merely because only one member is
   executing. If the runtime offers no explicit temporary scope, state that
   boundary and ask whether the user wants a Group Skill or a durable Waker
   Skill; never emulate temporary scope with a permanent install.

## Publishing and binding an SOP

An SOP is real only after it is published to the catalog and bound to the
Group. Editing a shared Markdown note, a `*SOP*.md`, a workspace document, or
any file in the Group directory does not register an SOP and is never an
acceptable substitute. Never create an SOP with `skill manage`, never write it
into the Conversation SkillStore, and never persist it as an ordinary file.

**Discussion Runs cannot manage SOPs.** When
`QODERWAKE_CONVERSATION_KIND=group_thread`, the current Conversation id names a
Discussion and cannot identify the owning Group. Do not publish or mutate
anything from that Run; ask the user to repeat the request in the Group's
first-level Conversation or use its visible Group management entry.

For a `group_conversation`, follow this exact ordered CLI flow and advance only
after each step succeeds. `<conversation-id>` is the literal id from your Run
prompt.

1. **Scaffold.** `qoderwake sop init <file> --skill-id <kebab-id> --version <semver>`.
   Never hand-write the JSON from scratch. The scaffold uses the exact top-level
   camelCase keys the CLI requires (`skillId`, `version`, `template`); renaming
   them to snake_case is rejected (`SOP template skillId must be kebab-case`).
   Edit only `template.body` (rendered as the SOP `SKILL.md`) and any optional
   `${{param}}` parameters. `template.body` is a JSON string: every `"`, `\`,
   and newline in your markdown must be JSON-escaped, so prefer plain quotes or,
   for a large body, build the JSON programmatically (a heredoc piped through
   `jq` or `python -c`) instead of hand-editing quotes.
2. **Validate (hard gate).** `qoderwake sop validate <file>` must print
   `... is valid` before you continue. Fix and re-validate on invalid JSON or a
   rejected field; do not publish, bind, or fall back to another surface until
   it passes. Optionally preview with `qoderwake sop build <file> --output <dir>`.
3. **Publish.** `qoderwake sop publish --file <file>` creates the immutable
   release. Skip re-publishing when `qoderwake sop list --json` already lists a
   matching `skill_id@version`.
4. **Read current bindings.** `qoderwake group sop list <conversation-id> --json`.
5. **Bind.** `qoderwake group sop set <conversation-id> --sop <skill_id[@version]> ... [--param <selector.key=value> ...]`.

Steps 4 and 5 accept the exact Conversation id from your Run prompt even when it
names the current task Conversation rather than the Group's first-level one; the
CLI resolves it to the owning Group. Do not invent a different handle, and never
read a handle error as a signal to switch to another surface.

`group sop set` replaces the complete ordered binding list. When adding or
updating one SOP, preserve every unchanged binding, its version, order, and
parameters, and submit the full merged list in a single call. Confirm both
publish and binding success before saying the SOP is active. A failure at any
step means fix the template and retry this same flow; hard SOP authoring is never
a reason to reach for `skill manage`. If publishing or binding is unavailable or
unauthorized, report that boundary; never fall back to a Group Skill and never
silently downgrade to writing a file.

## Creating a Group Skill

Draft the `SKILL.md` body into a local file first, then:

```bash
qoderwake skill manage --conversation-id <conversation-id> --action create \
  --skill-name "<name>" --content-file <absolute-path-to-draft> --summary "<why>"
```

- Use exactly one of `--conversation-id` and `--waker-id`; the Group Skill is
  owned by the Conversation. Never substitute `--waker-id` merely because one
  Waker is executing the request.
- A successful creation returns `status="applied"`; only then say it was
  created. It becomes available to all Group members on their next Run and must
  appear in the current Conversation's Skill list.
- `--action patch|edit|write_file|remove_file` maintain an existing Group Skill
  the same way; `--dry-run` previews without writing.
