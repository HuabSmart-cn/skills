---
name: debug-and-report
description: Use inside the Matrix app when the user sends an in-app bug report with the composer debug report button, reports a crash, broken chat, blank view, auth failure, or model/API failure. Collect Matrix diagnostic proof for user-consented full upload and create a new Matrix debug report.
user-invocable: false
---

# Debug and Report Matrix App

You are the Matrix in-app agent handling a user bug report. The user's current chat may be degraded, so keep the workflow short, collect Matrix diagnostic proof for full user-consented upload, and create a debug report.

This built-in skill is for **new user reports from inside Matrix**. Existing submitted issue handoff for engineers lives at the repository-root skill:

```text
.agents/skills/matrix-issue-engineer/SKILL.md
```

## Inputs

Enter this workflow when:

- the user message starts with `## Bug Report`
- the user used the composer debug report button
- the user describes Matrix as crashed, stuck, blank, offline, unauthenticated, or repeatedly failing API calls
- the prompt contains a fenced `bug-report-metadata` JSON block

Parse `bug-report-metadata` when present and use it as authoritative context for `app_version`, `os_version`, `workspace_id`, `agent_id`, `session_id`, `model_name`, `consent_version`, and `upload_policy`. Expected consent metadata is `consent_version: matrix-debug-upload-v1` and `upload_policy: full-session-no-redaction`.

## Safety

- Matrix UI captures user consent before this workflow with `consent_version` `matrix-debug-upload-v1` and `upload_policy` `full-session-no-redaction`.
- After that consent, collected Matrix diagnostic artifacts are uploaded as-is and may include personal, private, sensitive, or credential-like data from the current Matrix session, logs, process list, prompt context, and transcripts.
- Do not perform local redaction, secret scanning, blocker checks, or sensitive-filename filtering on collected Matrix diagnostic artifacts.
- You may read local auth only to build an in-memory `Authorization` header. Never print the token as a standalone value.
- Do not browse unrelated private files outside Matrix/Neo diagnostic locations unless they are necessary for this report or the user explicitly provides the path.
- Ask at most three short questions. If the user supplied an error, screenshot, or description, start collecting proof.

## Paths

```bash
NEO_HOME="${NEO_HOME:-$HOME/.neo}"
GATEWAY="${NEO_GATEWAY_URL:-https://matrix.agent.space}"
```

## Collect Proof

Create one temp directory:

```bash
TMPDIR="$(mktemp -d "/tmp/matrix-runtime-debug.XXXXXX")"
NEO_HOME="${NEO_HOME:-$HOME/.neo}"

{
  echo "timestamp_utc=$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
  echo "neo_home=$NEO_HOME"
  echo "os_version=$(sw_vers -productVersion 2>/dev/null || true)"
  echo "os_build=$(sw_vers -buildVersion 2>/dev/null || true)"
  echo "arch=$(uname -m 2>/dev/null || true)"
  echo "model=$(sysctl -n hw.model 2>/dev/null || true)"
  echo "memory_gb=$(($(sysctl -n hw.memsize 2>/dev/null || echo 0) / 1024 / 1024 / 1024))"
  echo "consent_version=matrix-debug-upload-v1"
  echo "upload_policy=full-session-no-redaction"
} > "$TMPDIR/context.env"

cat > "$TMPDIR/debug-consent.json" <<'JSON'
{
  "consent_version": "matrix-debug-upload-v1",
  "upload_policy": "full-session-no-redaction",
  "consent_text": "Please describe here in detail what went wrong in Matrix and attach screenshots if available. Press Send to automatically debug the issue and submit a report to the flowith dev team. Debug mode uploads all current session information, which may include personal or sensitive data, to flowith for debugging. By using it, you consent to these data processing terms."
}
JSON

cp "$NEO_HOME/daemon/daemon.log" "$TMPDIR/daemon.log" 2>/dev/null \
  || tail -c 5242880 "$NEO_HOME/daemon/daemon.log" > "$TMPDIR/daemon.log" 2>/dev/null \
  || true
cp "$NEO_HOME/daemon/status.json" "$TMPDIR/status.json" 2>/dev/null || true
log show --last 2h --style compact --info --debug \
  --predicate 'process == "Matrix" OR process CONTAINS[c] "neo" OR subsystem == "flowith.matrix" OR subsystem == "com.flowith.matrix"' \
  > "$TMPDIR/macos-matrix.log" 2>/dev/null || true
ps auxww > "$TMPDIR/processes.txt" 2>/dev/null || true
```

Write the full user bug report text and parsed metadata to `$TMPDIR/prompt-context.md`. Include `consent_version`, `upload_policy`, workspace ID, session ID, agent ID, visible error, model name, app version, OS version, source, and debug trigger when present.

After `$TMPDIR/prompt-context.md` exists, collect discoverable session registry and transcript artifacts for the current session/workspace:

```bash
node --input-type=module - "$TMPDIR" "$NEO_HOME" <<'NODE'
import { copyFileSync, existsSync, readFileSync, readdirSync, statSync, writeFileSync } from "node:fs";
import path from "node:path";

const [tmpdir, neoHome] = process.argv.slice(2);
const copied = [];
const skipped = [];

function readText(filePath) {
  try {
    return readFileSync(filePath, "utf8");
  } catch {
    return "";
  }
}

const haystack = ["prompt-context.md", "user-prompt.md", "report.json"]
  .map((name) => readText(path.join(tmpdir, name)))
  .join("\n");

function extract(keys) {
  const values = new Set();
  for (const key of keys) {
    const quoted = new RegExp(`["']${key}["']\\s*[:=]\\s*["']([^"']+)["']`, "gi");
    for (const match of haystack.matchAll(quoted)) values.add(match[1]);
    const loose = new RegExp(`\\b${key}\\b\\s*[:=]\\s*([^\\s,;)\\]}]+)`, "gi");
    for (const match of haystack.matchAll(loose)) values.add(match[1].replace(/^["']|["']$/g, ""));
  }
  return [...values].filter(Boolean);
}

const sessionIds = new Set(extract(["session_id", "sessionId", "root_session_id", "rootSessionId", "parent_session_id", "parentSessionId"]));
const workspaceIds = new Set(extract(["workspace_id", "workspaceId", "workspace"]));
const departmentIds = new Set(extract(["department_id", "departmentId", "agent_id", "agentId"]));

function safeName(value) {
  return String(value).replace(/[^a-zA-Z0-9._-]+/g, "-").slice(0, 160) || "unknown";
}

function copyArtifact(source, filename) {
  try {
    if (!source || !existsSync(source)) return;
    const stats = statSync(source);
    if (!stats.isFile()) return;
    const dest = path.join(tmpdir, filename);
    if (existsSync(dest)) return;
    copyFileSync(source, dest);
    copied.push({ source, filename, bytes: stats.size });
  } catch (error) {
    skipped.push({ source, reason: String(error?.message ?? error) });
  }
}

function sanitizeProjectPath(targetPath) {
  return targetPath.replace(/[^a-zA-Z0-9]/g, "-");
}

function predictedTranscriptPath(sessionId, cwd) {
  if (!cwd) return undefined;
  return path.join(neoHome, "projects", sanitizeProjectPath(cwd), `${sessionId}.jsonl`);
}

function resolvedTranscriptPath(entry, deptRoot) {
  if (typeof entry.transcriptPath !== "string" || entry.transcriptPath.length === 0) return undefined;
  return path.isAbsolute(entry.transcriptPath)
    ? entry.transcriptPath
    : path.join(entry.cwd ?? deptRoot, entry.transcriptPath);
}

function matchesSession(entry, workspace, department) {
  if (!entry || typeof entry !== "object") return false;
  const ids = [entry.sessionId, entry.rootSessionId, entry.parentSessionId].filter((value) => typeof value === "string");
  if (ids.some((id) => sessionIds.has(id))) return true;
  if (sessionIds.size > 0) return false;
  if (workspaceIds.size > 0 && workspaceIds.has(workspace) && (entry.status === "open" || entry.canonicalForDepartment === true)) return true;
  if (departmentIds.size > 0 && departmentIds.has(department) && (entry.status === "open" || entry.canonicalForDepartment === true)) return true;
  return false;
}

const workspacesRoot = path.join(neoHome, "workspaces");
const workspaceNames = [];
try {
  const all = readdirSync(workspacesRoot).filter((name) => {
    try {
      return statSync(path.join(workspacesRoot, name)).isDirectory();
    } catch {
      return false;
    }
  });
  workspaceNames.push(...(workspaceIds.size > 0 ? all.filter((name) => workspaceIds.has(name)) : all));
} catch {}

let matchedSessions = 0;
for (const workspace of workspaceNames) {
  const departmentsRoot = path.join(workspacesRoot, workspace, "departments");
  let departments = [];
  try {
    departments = readdirSync(departmentsRoot);
  } catch {
    continue;
  }
  for (const department of departments) {
    const deptRoot = path.join(departmentsRoot, department);
    const sessionsDir = path.join(deptRoot, ".runtime", "sessions");
    let files = [];
    try {
      files = readdirSync(sessionsDir).filter((name) => name.endsWith(".json"));
    } catch {
      continue;
    }
    for (const file of files) {
      const sessionPath = path.join(sessionsDir, file);
      let entry;
      try {
        entry = JSON.parse(readText(sessionPath));
      } catch {
        continue;
      }
      if (!matchesSession(entry, workspace, department)) continue;
      matchedSessions += 1;
      const sessionId = typeof entry.sessionId === "string" ? entry.sessionId : path.basename(file, ".json");
      const prefix = `${safeName(workspace)}-${safeName(department)}-${safeName(sessionId)}`;
      copyArtifact(sessionPath, `session-${prefix}.json`);
      copyArtifact(resolvedTranscriptPath(entry, deptRoot), `transcript-${prefix}.jsonl`);
      copyArtifact(predictedTranscriptPath(sessionId, entry.cwd), `transcript-canonical-${prefix}.jsonl`);
      copyArtifact(path.join(deptRoot, "trace.jsonl"), `trace-${safeName(workspace)}-${safeName(department)}.jsonl`);
      copyArtifact(path.join(deptRoot, ".runtime", "team.json"), `runtime-team-${safeName(workspace)}-${safeName(department)}.json`);
    }
  }
}

if (sessionIds.size > 0 && matchedSessions === 0) {
  try {
    for (const project of readdirSync(path.join(neoHome, "projects"))) {
      for (const sessionId of sessionIds) {
        copyArtifact(path.join(neoHome, "projects", project, `${sessionId}.jsonl`), `transcript-${safeName(project)}-${safeName(sessionId)}.jsonl`);
      }
    }
  } catch {}
}

writeFileSync(path.join(tmpdir, "session-artifacts-manifest.json"), JSON.stringify({
  requested_session_ids: [...sessionIds],
  requested_workspace_ids: [...workspaceIds],
  requested_department_ids: [...departmentIds],
  matched_sessions: matchedSessions,
  copied,
  skipped
}, null, 2) + "\n");
NODE
```
If a screenshot was attached to the Matrix message, include a note in `$TMPDIR/screenshot-note.txt`; do not capture the screen yourself unless the user asks.

## Diagnose

Use focused searches:

```bash
rg -n "401|invalid token|authentication_error|auth|token|refresh" "$TMPDIR" > "$TMPDIR/auth-hints.txt" 2>/dev/null || true
rg -n "400|tool use|tool_use|concurrency|invalid_request" "$TMPDIR" > "$TMPDIR/tool-use-hints.txt" 2>/dev/null || true
rg -n "blank|empty|white|stuck|interrupted|stream|websocket|disconnect|offline" "$TMPDIR" > "$TMPDIR/chat-hints.txt" 2>/dev/null || true
```

Write `$TMPDIR/findings.md`:

```text
User-visible symptom:

Likely cause:

Proof:

Suggested fix or workaround:
```

The report description must be a clean factual paragraph. Do not add fixed labels such as `AI Summary:` or `Original description:`.

## Upload

Prepare a token helper:

***REDACTED***
matrix_gateway_token() {
  node --input-type=module <<'NODE'
import { readFileSync } from "node:fs";
import os from "node:os";
import path from "node:path";

const authPath = path.join(os.homedir(), ".neo", "neo-auth.json");
const auth = JSON.parse(readFileSync(authPath, "utf8"));
const candidates = [
  auth.session?.accessToken,
  auth.session?.access_token,
  auth.accessToken,
  auth.access_token,
  auth.currentSession?.accessToken,
  auth.currentSession?.access_token,
  auth.supabase?.session?.accessToken,
  auth.supabase?.session?.access_token
];
const token = ***REDACTED***
if (!token) process.exit(2);
process.stdout.write(token);
NODE
}
```

Create `$TMPDIR/report.json` with facts and parsed metadata:

```json
{
  "title": "Matrix issue",
  "description": "Concise factual summary.",
  "severity": "normal",
  "source": "in_app",
  "app_version": "",
  "os_version": "",
  "user_email": "",
  "model_name": "",
  "workspace_id": "",
  "agent_id": "",
  "session_id": "",
  "consent_version": "matrix-debug-upload-v1",
  "upload_policy": "full-session-no-redaction"
}
```

Allowed `severity`: `critical`, `high`, `normal`, `low`.
Allowed `source`: `in_app`, `menubar`, `external_ai`.

Upload policy is full-session/no-redaction after Matrix UI consent. Collected Matrix diagnostic artifacts are uploaded as-is and may include personal or sensitive data. Do not generate a redaction review, run secret scanners, redact files, block sensitive-looking filenames, or remove diagnostic artifacts before upload. Only skip the submit artifacts that would recursively include the upload request/response itself.

Build and send the payload:

```bash
TOKEN=***REDACTED***
PAYLOAD_JSON="$TMPDIR/payload.json"

node --input-type=module - "$TMPDIR" "$TMPDIR/report.json" > "$PAYLOAD_JSON" <<'NODE'
import { readFileSync, readdirSync, statSync } from "node:fs";
import { writeFileSync } from "node:fs";
import path from "node:path";

const [tmpdir, reportPath] = process.argv.slice(2);
const report = JSON.parse(readFileSync(reportPath, "utf8"));
const selfGenerated = new Set([
  "payload.json",
  "report.json",
  "attachment-manifest.json",
  "submit-response.json",
]);
const manifest = [];
const files = readdirSync(tmpdir)
  .filter((name) => !selfGenerated.has(name))
  .map((name) => {
    const filePath = path.join(tmpdir, name);
    const stats = statSync(filePath);
    if (!stats.isFile()) return null;
    manifest.push({ filename: name, bytes: stats.size });
    return {
      filename: name,
      content_type: name.endsWith(".json") ? "application/json" : "text/plain",
      content: readFileSync(filePath).toString("base64")
    };
  })
  .filter(Boolean);

writeFileSync(path.join(tmpdir, "attachment-manifest.json"), JSON.stringify({ files: manifest }, null, 2) + "\n");
console.log(JSON.stringify({ ...report, files }));
NODE

cat "$TMPDIR/attachment-manifest.json"

curl -sS -X POST "$GATEWAY/v1/debug-reports" \
  -H "Authorization: ***REDACTED***
  -H "Content-Type: application/json" \
  --data-binary "@$PAYLOAD_JSON" \
  | tee "$TMPDIR/submit-response.json"
```

Expected response:

```json
{"data":{"ticket":"DBG-YYYYMMDD-XXXX","id":"<uuid>"}}
```

## Reply

Keep the reply short:

- ticket and report ID
- one-line likely cause
- proof temp directory
- HTTP/API error if upload failed
