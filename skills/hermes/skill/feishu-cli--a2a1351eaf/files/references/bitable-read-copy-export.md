# Bitable (多维表格) read / copy / export patterns

Session-tested recipes for the `lark-cli base` and `lark-cli drive` domains. All commands assume the isolated Hermes executable at:

```bash
LARK="$HOME/.hermes/tools/lark-cli/node_modules/.bin/lark-cli"
```

## Token types and the `--base-token` / wiki-token confusion

A Feishu bitable is referenced by several different token forms, and the CLI rejects them differently:

***REDACTED***
|---|---|---|
| Wiki URL token | `C1y9wTTWvi69xbklTdrc0Uxlnkc` (from `yunyinghui.feishu.cn/wiki/...`) | NO — returns code 800004006 "param baseToken is invalid" |
| Wiki URL | `https://...feishu.cn/wiki/...?table=tblXXX&view=vewXXX` | Use `drive +inspect --url` first to unwrap |
| Base URL | `https://www.feishu.cn/base/TIL0bqa2xa8VQ0sheKFcr7LTnbe` | Use `drive +inspect --url` |
| Unwrapped `obj_token` | `TIL0bqa2xa8VQ0sheKFcr7LTnbe` | YES — this is the real `base_token` |
| Table ID | `tbl1T1v3b0DbVzQN` | Pass as `--table-id`, not as `base_token` |

The flag for the base domain is always `--base-token`. `--app-token` returns "unknown flag" with a hint to use `--base-token`. Do not try the alternate name even when other Feishu SDK docs use it.

## Read-only inspection recipe (safe, no writes)

```bash
URL="https://yunyinghui.feishu.cn/wiki/C1y9wTTWvi69xbklTdrc0Uxlnkc?table=tbl1T1v3b0DbVzQN&view=vew3epn8J8"

# 1) Unwrap the URL → real base_token
"$LARK" drive +inspect --url "$URL"
#   {
#     "title": "WAIC2026参展商信息汇总",
#     "token": ***REDACTED***
#     "type": "bitable",
#     "wiki_node": {"node_token": "C1y...lnkc", "obj_token": "TIL0b...", "obj_type": "bitable"}
#   }

BASE="TIL0bqa2xa8VQ0sheKFcr7LTnbe"

# 2) Base metadata
"$LARK" base +base-get --base-token "$BASE"

# 3) All tables in the base
"$LARK" base +table-list --base-token "$BASE"
#   { "tables": [{"id":"tblXXX","name":"全部汇总"}, ...], "total": 7 }

# 4) Fields of one table
"$LARK" base +field-list --base-token "$BASE" --table-id "tbl1T1v3b0DbVzQN"

# 5) Records of one table (default markdown, paginated)
"$LARK" base +record-list --base-token "$BASE" --table-id "tbl1T1v3b0DbVzQN" --limit 100
```

## When the user asks to "copy" a bitable

They almost always want one of three things. Surface the trade-offs explicitly; do not just run `base +base-copy` and claim success.

### Option 1 — Structure-only copy (fast, drops records)

```bash
"$LARK" base +base-copy \
  --base-token "$BASE" \
  --name "WAIC2026参展商信息汇总 - Hermes Copy" \
  --time-zone "Asia/Shanghai"
```

- Copies tables, fields, views, dashboards.
- Does NOT copy records.
- New file lands in the caller's root Drive folder unless `--folder-token` is set.
- **Can fail with `forbidden (code 800004011)`** when the user identity lacks base-copy permission. The user can read the base fine, but the copy endpoint requires a separate scope that may not be auto-granted by `auth login`. When this happens, fall back to Option 2 or Option 3 — do not retry `+base-copy` hoping it works.

### Option 2 — XLSX export (best for "I just need a backup of the data")

```bash
mkdir -p "$HOME/Downloads/feishu-exports"
"$LARK" drive +export \
  --url "$URL" \
  --file-extension xlsx \
  --output-dir "$HOME/Downloads/feishu-exports"
# Output: <output-dir>/WAIC2026参展商信息汇总.xlsx
```

Then optionally re-upload to a chosen Drive folder:

```bash
# Find or create the destination folder
"$LARK" drive +create-folder --name "WAIC2026 Backups"
# Get its token from the response, then:
***REDACTED***
  --file-path "$HOME/Downloads/feishu-exports/WAIC2026参展商信息汇总.xlsx" \
  --parent-token "<folder_token>"
```

Preserves all rows/columns; loses bitable-only features (formulas, automations, view filters, attachments, comments).

### Option 3 — Full editable copy (slow, lossy on attachments)

Use this when the user explicitly wants an editable copy of a populated bitable in their own Drive. The three real failure modes that turn "just replay the records" into a half-day exercise are: (a) `base +base-copy` returns `forbidden (code 800004011)` because the user identity lacks base-copy permission even though read works fine; (b) source `select` fields are often stuffed with long free-text values that fail server-side validation when re-inserted; (c) the batch-create API rate-limits aggressively. The recipe below addresses all three.

#### Step 0 — Probe, do not assume

Before building anything, run the read-only pipeline on the source and answer three questions for the user: how many tables, how many records per table, and which select-type fields have values that are NOT in the declared option list. This is the single most useful data point: bitables in the wild frequently have select fields containing long free-text strings. If you skip this probe, you will discover the problem mid-write with hundreds of records already half-replayed.

```bash
# For each table, count records via paginated record-list
for tbl in tblX1 tblX2 ...; do
  total=0; offset=0; has_more=true
  while $has_more; do
    out=$("$LARK" base +record-list --base-token "$SRC" --table-id "$tbl" \
        --offset "$offset" --limit 200 --format json)
    total=$((total + $(echo "$out" | jq '.data.record_id_list | length')))
    has_more=$(echo "$out" | jq '.data.has_more')
    offset=$((offset + 200))
  done
  echo "$tbl: $total"
done
```

```bash
# For each select field, count how many cell values match the declared options
python3 - <<'PY'
import json
rows = json.load(open('/tmp/waic_dump/<TABLE>_records.json'))
fields = json.load(open('/tmp/waic_dump/<TABLE>_fields.json'))
for i, f in enumerate(fields):
    if f['type'] != 'select': continue
    options = {o['name'] for o in f.get('options', [])}
    non_empty, valid = 0, 0
    for r in rows:
        v = r['_values'][i]
        if v is None: continue
        vals = v if isinstance(v, list) else [v]
        non_empty += len(vals)
        for x in vals:
            if x in options: valid += 1
    pct = 100 * valid / non_empty if non_empty else 0
    print(f"  {f['name'][:40]}: non_empty={non_empty}, valid={valid} ({pct:.0f}%)")
PY
```

If select fields are mostly invalid (>10% non-option values), the user has to choose between: (A) re-create the field as `text` (preserves data, type changes), (B) keep `select` and lose invalid cells, (C) keep `select` and add a parallel text column. Do NOT pick for them — surface the count and let them decide.

#### Step 1 — Create the empty target base and its tables

`+base-create` only creates a base, not its tables. The first table is auto-created with four default fields (in CN locale: `日期`, `单选`, `附件`, `文本`); subsequent tables come from `+table-create` and have NO defaults. Plan for the asymmetry.

```bash
# Empty base (creates default first table automatically)
"$LARK" base +base-create --name "<target name>" --time-zone "Asia/Shanghai"
# Returns: base_token — save it as $NEW.

# One table per source, with fields created up-front
"$LARK" base +table-create --base-token "$NEW" --name "<table name>" \
  --fields '[{"name":"公司名称","type":"text"},{"name":"行业分类","type":"text"}, ...]'

# If the first table needs a different name (it ships as "数据表"), rename it
"$LARK" base +table-rename --base-token "$NEW" --table-id "$DEFAULT" --new-name "全部汇总"
```

For the default first table, add the source fields with `+field-create` rather than recreating the table — it is faster and preserves any extra default columns.

#### Step 2 — Reconcile field types between source and target

For each select field with significant non-option values, the user has chosen to recreate it as `text`. The mechanics are: `+field-delete` (high-risk-write, requires `--yes`) followed by `+field-create` with type `text`. Field IDs change, but names stay the same, so subsequent record-batch-create can use NAMES instead of IDs as the `fields` array.

```bash
# For each select field to flip:
"$LARK" base +field-delete --base-token "$NEW" --table-id "$TID" --field-id "$FID" --yes
"$LARK" base +field-create --base-token "$NEW" --table-id "$TID" \
  --json '{"name":"<same name>","type":"text"}'
```

`+field-create` takes `--json` (a single object), NOT `--field`. The wrong flag is silently rejected with empty stdout in some CLI versions — always read the response and confirm `"ok": true` before continuing.

#### Step 3 — Build the field-name intersection, then batch-insert

This is the step most likely to fail. The intersection of source-field-names and target-field-names is the only safe `fields` list to pass. If the first target table is the auto-created one, its defaults (`日期`/`单选`/`附件`/`文本`) are NOT in the source — including them in `fields` makes the API return `code 800030201 not_found` ("first 5 available fields are: …"). Filter them out explicitly.

```python
def get_new_fields(tid):
    out = run(["base","+field-list","--base-token",NEW,"--table-id",tid,"--format","json"])
    return json.loads(out)["data"]["fields"]

new_fields = get_new_fields(TID)
new_by_name = {f["name"]: f["id"] for f in new_fields}
src_fields = json.load(open(f"/tmp/waic_dump/{TABLE}_fields.json"))
common = [f["name"] for f in src_fields if f["name"] in new_by_name]
# ONLY pass `common` as the `fields` list. NEVER include the new base's
# default columns.
```

#### Step 4 — Coerce every value to a string before batching

`+record-batch-create` is strict about cell shapes. The hint on `code 800010407` is literally "Provide a string value." Source values come in three shapes and only one is acceptable:

- `str` → pass through
- `dict` like `{"name":"x","hue":"Blue"}` → extract `.get("name")`
- `list` of dicts or strings (multi-select cells, even when recreated as text) → join with `", "`, skipping empty entries
- `None` → pass as `None` (the cell stays empty)

```python
def coerce(v):
    if v is None: return None
    if isinstance(v, list):
        if not v: return None
        parts = [(x.get("name") if isinstance(x, dict) else str(x)) for x in v]
        return ", ".join(p for p in parts if p)
    if isinstance(v, dict): return v.get("name") or str(v)
    return str(v)
```

Skipping this step is what causes the `800010407 cell value does not match the expected input shape` errors on the second and third batch. The first batch often succeeds because its first row has only a single text value; the failures start when arrays appear.

#### Step 5 — Batch size and rate-limit handling

The `+record-batch-create` `--help` claims 200 rows max per call. In practice 200 is the documented ceiling but the API frequently returns `code 800004135 "the method: OpenAPIBatchAddRecords limited"` starting around batch 2 or 3. Smaller batches with explicit backoff are far more reliable:

```python
BATCH = 50
for i in range(0, len(rows), BATCH):
    chunk = rows[i:i+BATCH]
    payload = json.dumps({"fields": common, "rows": chunk}, ensure_ascii=False)
    out, rc, err = run(["base","+record-batch-create","--base-token",NEW,
                        "--table-id",tid,"--json",payload])
    if "limited" in (out + err):
        time.sleep(2)
```

50 per batch is the practical sweet spot for a single-table write of 1k rows. For 2k+ rows or 5+ tables, expect 3–8 minutes total wall time with intermittent `800004135` retries.

#### Step 6 — Verify

Always re-count records on each target table after the write completes. The CLI does NOT guarantee a transactional outcome — partial failures can leave a table with N records when you expected M. The count loop is the only reliable check:

```python
for name, tid in tables:
    total = 0; offset = 0; has_more = True
    while has_more and offset < 5000:
        out = run(["base","+record-list","--base-token",NEW,"--table-id",tid,
                   "--offset",str(offset),"--limit","200","--format","json"])
        d = json.loads(out)["data"]
        total += len(d.get("record_id_list", []))
        has_more = d.get("has_more", False)
        offset += 200
    print(f"{name}: {total} records")
```

If a table's count does not match the source, do NOT silently retry — query the failed batches' indices and replay only those.

#### Worked example: WAIC 2026 参展商 (1996 records across 7 tables)

This was the actual session that produced this recipe. Source: `TIL0bqa2xa8VQ0sheKFcr7LTnbe` (7 tables, 1996 total records, with select fields stuffed full of long free-text). Outcome: target base `R7lEbnOwSakWMusT2xAc1voLnHh` with all 1996 records reconstructed, 6 select fields flipped to text per the user's explicit choice. End-to-end wall time including all failures and retries was ~10 minutes.

## `--dry-run` and confirmation

For any write/copy/move/delete/upload, run with `--dry-run` first to print the exact HTTP request that would be sent:

```bash
"$LARK" base +base-copy --base-token "$BASE" --name "Copy" --dry-run
# Returns the would-be POST body and URL, with "dry_run": true
```

Show this to the user, then re-run without `--dry-run` only after explicit confirmation. This applies to `base +base-create`, `base +base-copy`, `base +record-batch-create`, `base +record-update`, `base +record-delete`, `base +field-create`, `base +field-delete`, `drive +create-folder`, `drive +move`, `drive +delete`, `drive +upload`, anything in `im`/`mail` that sends, and any high-risk-write flagged by the CLI's `--help` output.

## Common API gotchas (Option 3 path, distilled)

| Gotcha | Wrong | Right |
|---|---|---|
| Create a base | `+base-create --name X` expecting tables to be inside it | `+base-create` makes ONE default first table. Use `+table-create` for every other table. |
| Field type for a new field | `--field` flag | `--json` with a single object |
| Delete a field | `+field-delete` without confirmation | needs `--yes` (it is high-risk-write) |
| Create one record | `+record-create` | does NOT exist. Use `+record-batch-create` with a one-row batch. |
| Field list in batch-create | pass all fields the table has | pass ONLY the intersection of source field names and target field names. The auto-created first table's 4 default columns (`日期/单选/附件/文本`) are NOT in the source and will cause `not_found (800030201)` if listed. |
| Source value with select-cell as text | pass the array `["a","b"]` as-is | coerce to a single string first, or the API rejects with `cell value does not match (800010407)` "Provide a string value" |
| Batch size | 200 rows per call (the documented max) | 50 rows is the practical sweet spot. 200 hits rate limit `800004135` after batch 2 or 3. |
| Select field full of long text | try to write each value as an option name | detect this in Step 0 and re-create the field as `text`. Without this, every row with non-option content fails. |
