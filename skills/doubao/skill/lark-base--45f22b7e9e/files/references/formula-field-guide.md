# Base Formula Writing Guide

## Mandatory Read Acknowledgement

When creating or updating a formula field with `lark-cli base +field-create/+field-update --json ...` and `type` is `formula`, you should read this guide first and only then add `--i-have-read-guide` to the command.

Do **not** proactively add `--i-have-read-guide` before reading this guide. Without it, the CLI will fail fast and direct you back to this guide.

When using `+field-update`, also pass `--yes`: field update is a high-risk `PUT` operation because changing a field definition can affect the whole column.

## Default strategy

**All cross-table references, aggregations, and computed fields should use Formula fields by default.** Do NOT use Lookup fields unless the user explicitly requests it. Formula is a strict superset of Lookup — anything Lookup can do, Formula can do with a single expression.

## Usage

When creating a formula field, the Agent should:

1. Get all table names: `lark-cli base +table-list --base-token <base>` — returns `items[].table_name`
2. Get table structure: `lark-cli base +table-get --base-token <base> --table-id <table>` — returns `fields[]`
3. If the formula references other tables, also get those tables' structures
4. Write the formula expression following this guide
5. Construct the Formula field JSON and submit it to create or update the field

**Key constraints**:

- The JSON must include `"type": "formula"` — this field is required
- Table names and field names in the formula must **exactly match** those returned by `+table-list` / `+table-get`
- The `expression` value is a string containing the formula expression; double quotes inside the expression must be properly escaped in JSON (e.g. `\"text\"`)

---

## Section 1: Core Concepts — Scalar vs List

This is the foundation of formula logic. You must determine this before writing any formula.

| Syntax                | Meaning                                      | Return type            | Example                                      |
| --------------------- | -------------------------------------------- | ---------------------- | -------------------------------------------- |
| `[Field]`             | Value of this field in the current row       | Scalar (single value)  | `[Name]` → `"Alice"`                         |
| `[TableName].[Field]` | All values of this field in the target table | List (multiple values) | `[Employees].[Name]` → `["Alice","Bob",...]` |
| `[TableName]`         | The target table (entire table)              | Table reference        | Used as data range for FILTER/COUNTIF etc.   |

**Rules**:

- Scalars can be used directly in operations: `[Price] * [Quantity]`
- Lists cannot be used as scalars — they must be processed first: use `SUM()` for sum, `ARRAYJOIN(",")` for joining, `FIRST()`/`LAST()`/`NTH()` for single value extraction
- Link field access `[LinkField].[TargetField]` returns a list (values of the target field for all linked records)
- **LISTCOMBINE flattening rule**: When a FILTER's result column is itself a multi-value field (`select` with `multiple=true`, `link`, etc.), it produces a 2D array and **must** be flattened with `.LISTCOMBINE()`; for single-value fields (`number`, `text`, etc.) it can be omitted, but adding it is never wrong:

  ```
  [Table].FILTER(CurrentValue.[Field] = [Value]).[Tags].LISTCOMBINE() ← required for multi-value columns
  [Table].FILTER(CurrentValue.[Field] = [Value]).[NumberCol].LISTCOMBINE() ← optional for single-value columns
  ```

---

## Section 2: Data Types and Type Conversion

### Field storage types

| Type | Description | Supported operations |
|------|-------------|----------------------|
| `number` | Stored as numeric value | Math operations, comparisons, auto-converts to string for concatenation |
| `text` | Stored as string | String operations; can participate in math if content is numeric, otherwise errors |
| `datetime` | Date object | Date functions, add/subtract with numbers; auto-converts to default format string when using `&` — use TEXT to format first for controlled output |
| `select` (`multiple=true`) | Data list | List functions, CONTAIN checks |
| `link` | Links to other table records | Chained access `[LinkField].[Field]`, result is a list |
| `checkbox` | TRUE/FALSE | Logical operations; auto-converts to number when compared with numbers |

### Implicit type conversion

| Scenario                     | Conversion rule                                                                                             |
| ---------------------------- | ----------------------------------------------------------------------------------------------------------- |
| Number + Float               | → Float                                                                                                     |
| Date + Number                | → Date (adds/subtracts days). Use `+`/`-` for whole days, use `DURATION()` for hour/minute/second precision |
| Date - Date                  | → Duration                                                                                                  |
| Boolean compared with Number | Boolean auto-converts to number (TRUE=1, FALSE=0)                                                           |
| `&` concatenation            | Both sides auto-convert to string                                                                           |

### Type consistency in comparisons

When using comparison operators (`>`, `>=`, `<`, `<=`, `=`, `!=`), **both sides should be the same type** to avoid semantic errors or unexpected results.

**Principle**: When types differ, explicitly convert one side rather than relying on implicit conversion:

- `number` vs `text` → use `VALUE()` to convert text to number
- `datetime` vs `text` → use `TEXT()` to convert date to text
- `datetime` vs `datetime` equality → dates include time components, so direct `=` comparison may fail due to different hours/minutes/seconds. For day-level equality, convert to text first: `TEXT([DateA], "YYYY/MM/DD") = TEXT([DateB], "YYYY/MM/DD")`
- `select` and `user` fields can be compared with both same-type values and text
- `text` fields in numeric aggregation (SUM/AVERAGE/MIN/MAX etc.) → convert to number with `VALUE()` first. For FILTER results, use `.MAP(VALUE(CurrentValue)).SUM()`

### Typed blank branches in conditional formulas

When a conditional Formula should return a number for matching rows and remain empty otherwise, keep the empty branch compatible with the numeric result:

```text
# pick the empty-branch literal, then confirm it with the readback below
IF([Condition], [NumericExpression], "")        # attested in the dataset goldens
IF([Condition], [NumericExpression], VALUE("")) # candidate when the field must stay numeric-typed
```

For the empty branch, `""` is the attested literal — the dataset's numeric-with-blank goldens use `""` / `" "` — and it is also correct when both branches are text. If you specifically need the field to stay numeric-typed, `VALUE("")` is a candidate, but do not assume it reads back as blank. The mandatory readback below is what decides which literal actually yields an empty, numeric-compatible cell for this base: if the represented false branch reads back as `0`, an error, or the field resolves to text, switch to the other literal instead of asserting either one works. Do not substitute `0` for an intended blank because zero is real data and cannot be distinguished from “not applicable”. Do not invent `BLANK()`, `NULL`, or `NaN()` as empty literals; they are not part of the supported function list, and a formula definition being accepted does not prove that its values can be calculated.

After create/update, use `+field-get` to confirm the saved expression, then make one bounded `+record-list --field-id <condition-field> --field-id <formula-field> --json` read over existing records. Verify each branch that has a representative record in that bounded result: a represented true branch must contain the expected numeric result, and a represented false branch must be empty/null. If one branch has no representative record, mark only that branch as unverified; do not fabricate records, rewrite the Formula, or declare that branch verified merely because the sample is absent.

Only an incorrect represented branch may trigger a targeted correction. If represented true and false branches both return null, treat the empty branch or branch-type compatibility as the first suspect; do not rewrite an independently verified condition, link traversal, or arithmetic expression. Make at most one targeted correction and one readback. If a represented branch still fails, report the Formula as incomplete instead of falling back to `0`; if a branch remains unrepresented, report that narrower verification gap without treating the Formula itself as wrong.

Dashboard filters that restrict an aggregate to eligible records remain necessary when the user requests that population, but they do not replace the row-level distinction between a true zero and a non-applicable blank.

---

## Section 3: CurrentValue

**CurrentValue is the iteration variable in FILTER/MAP/COUNTIF/SUMIF functions, representing the "current item" being processed in the data range.**

### CurrentValue meaning in different contexts

| Data range type              | CurrentValue represents | Access pattern              | Example                                                   |
| ---------------------------- | ----------------------- | --------------------------- | --------------------------------------------------------- |
| Entire table `[TableName]`   | A row in the table      | `CurrentValue.[FieldName]`  | `[Orders].FILTER(CurrentValue.[Amount] > 100).[Customer]` |
| Column `[TableName].[Field]` | A single field value    | Use `CurrentValue` directly | `[Orders].[Amount].FILTER(CurrentValue > 100)`            |
| `select` (`multiple=true`) field `[Tags]` | One option | Use `CurrentValue` directly | `[Tags].FILTER(CurrentValue = "Important")` |
| LIST-generated list          | One element             | Use `CurrentValue` directly | `LIST(1,2,3).MAP(CurrentValue * 2)`                       |

### Key rules

1. **When data range is a table**, use `CurrentValue.[FieldName]` to access row fields
2. **When data range is a column/list**, use `CurrentValue` directly for the element value — **cannot** use `CurrentValue.[FieldName]`
3. CurrentValue can **only** appear inside the condition/mapping parameters of FILTER/MAP/COUNTIF/SUMIF functions
4. To reference the current table's field value in a condition, write `[FieldName]` directly — it refers to the formula row's value, not a property of CurrentValue

### Anti-patterns

| Wrong                                          | Reason                                                                            | Correct                                                |
| ---------------------------------------------- | --------------------------------------------------------------------------------- | ------------------------------------------------------ |
| `[Table].[Col].FILTER(CurrentValue.[Col] > 0)` | Data range is a column; CurrentValue is a scalar, cannot use `.` to access fields | `[Table].[Col].FILTER(CurrentValue > 0)`               |
| `[Table].FILTER(CurrentValue > 100)`           | Data range is a table; CurrentValue is a row, cannot compare directly             | `[Table].FILTER(CurrentValue.[Amount] > 100).[Amount]` |
| `CurrentValue + 1` (at top level)              | CurrentValue can only be used inside iteration functions                          | Use inside MAP/FILTER etc.                             |

---

## Section 4: Operators

Base formulas **only allow** the following operators. `like`, `in`, `<>`, `**`, `^` etc. are prohibited.

| Category      | Operators                  | Description                                                                |
| ------------- | -------------------------- | -------------------------------------------------------------------------- |
| Arithmetic    | `+` `-` `*` `/` `%`        | Add, subtract, multiply, divide, modulo (`%` is equivalent to `MOD()`)     |
| Comparison    | `>` `>=` `<` `<=` `=` `!=` | Greater than, greater or equal, less than, less or equal, equal, not equal |
| Logical       | `&&` `\|\|`                | AND, OR                                                                    |
| Concatenation | `&`                        | Text concatenation; non-text values auto-convert to string                 |

**Important**:

- Equality uses `=` (single equals), not `==`
- Not-equal uses `!=`, not `<>`
- String concatenation uses `&`, not `+`
- Both `&&`/`||` and AND()/OR() functions are supported

---

## Section 5: Link Fields and Cross-Table References

### Link field description

When a field type is described as `FieldName: Link [target table: X, foreign key: Y]`, it links to target table X using field Y as the join key.

### Chained cross-table access

```
[LinkField].[TargetField]
```

Retrieves the target field values for all linked records as a list. Supports continued chaining: `[LinkA].[LinkB].[Field]`.

### Equivalent expanded form

- Multi-value link: `[TargetTableX].FILTER([LinkField].CONTAIN(CurrentValue.[Y])).[TargetField].LISTCOMBINE()`
- Single-value link: `[TargetTableX].FILTER(CurrentValue.[Y] = [LinkField]).[TargetField].LISTCOMBINE()`

(`.LISTCOMBINE()` is required when `[TargetField]` is a multi-value field; optional for single-value fields)

### Notes

- Link fields typically return **lists** (possibly empty)
- To output a single value, use aggregation (SUM/MAX), joining (ARRAYJOIN), or extraction (FIRST/LAST/NTH)
- Do not nest FILTER inside FILTER for cross-table queries — prefer link field chained access

---

## Section 6: Function Call Conventions

### Two calling styles

| Style      | Format             | Description                         |
| ---------- | ------------------ | ----------------------------------- |
| Functional | `FUNC(arg1, arg2)` | Works for all functions             |
| Chained    | `arg1.FUNC(arg2)`  | Moves the first argument before `.` |

**Rules**:

- Zero-argument functions cannot be chained: `NOW()`, `TODAY()`, `PI()`, `TRUE()`, `FALSE()`
- SORTBY can **only** be chained: `[Table].SORTBY([Table].[SortCol]).[OutputCol]`. The sort column always uses the original table's column name (`[TableName].[Field]` format); the engine aligns rows internally, even when the data range is a FILTER result
- FILTER is recommended to be chained: `[Table].FILTER(condition).[OutputCol]`

### FILTER / SORTBY result column rules

- **When data range is a table** `[TableName]`, FILTER / SORTBY returns a table reference. The chain **must** end with `.[Field]` to specify the result column, otherwise the formula fails:

  ```
  Correct: [Sales].FILTER(CurrentValue.[Amount] > 100).[Customer]
  Correct: [Sales].FILTER(condition).SORTBY([Sales].[SortCol]).[Customer]  ← result column at end of chain
  Wrong: [Sales].FILTER(CurrentValue.[Amount] > 100) ← missing result column
  ```

- **When data range is a column** `[TableName].[Field]` or a list, FILTER returns the filtered list directly — **no** result column needed:

  ```
  Correct: [Sales].[Amount].FILTER(CurrentValue > 100)
  ```

After the result column, it's recommended to flatten with `.LISTCOMBINE()` first (especially when the result column is a multi-value field), then chain aggregation functions:

```
[Sales].FILTER(CurrentValue.[Amount] > 100).[Amount].LISTCOMBINE().SUM()
```

---

## Section 7: Hard Constraints

1. **Nesting prohibition**: FILTER / SUMIF / COUNTIF / MAP **must not be nested** inside each other's condition/mapping expressions. None of these functions can appear inside the condition or mapping parameter of another.
   - Prohibited: `[Table1].FILTER(CurrentValue.[Col] = [Table2].FILTER(...).[Col])` ← FILTER inside FILTER condition
   - Prohibited: `[Table].MAP([Table2].MAP(...))` ← MAP inside MAP mapping
   - **Allowed**: `[Table].FILTER(cond1).[Col].FILTER(cond2)` ← chained call; the first FILTER's output is the second's data range, not nesting

2. **Function whitelist**: Only use functions listed in Section 8. No unlisted functions.

3. **Exact name matching**: Table names and field names in formulas must **exactly match** those returned by `+table-get` — no renaming or adding spaces.

4. **Operator whitelist**: Only use operators listed in Section 4.

5. **Strings use double quotes**: Strings must be wrapped in double quotes `"`, single quotes are not supported.

6. **Do not use LOOKUP**: FILTER is a superset of LOOKUP. All LOOKUP formulas can be rewritten with FILTER. Use FILTER exclusively to reduce complexity.

---

## Section 8: Complete Function Reference

### 8.1 Logic functions

| Function      | Signature                                                          | Return type          | Description                                                                                  |
| ------------- | ------------------------------------------------------------------ | -------------------- | -------------------------------------------------------------------------------------------- |
| IF            | `IF(condition, true_val, [false_val])`                             | Matches branch type  | Returns true_val when TRUE, false_val otherwise; omitting false_val returns false (not null) |
| IFS           | `IFS(cond1, val1, cond2, val2, ...)`                               | Matches branch type  | Multi-condition branching; returns value for the first TRUE condition                        |
| SWITCH        | `SWITCH(expr, match1, result1, [match2, result2, ...], [default])` | Matches branch type  | Matches expression value and returns corresponding result                                    |
| IFERROR       | `IFERROR(expr, fallback)`                                          | Matches branch type  | Returns fallback when expression errors                                                      |
| IFBLANK       | `IFBLANK(expr, fallback)`                                          | Matches branch type  | Returns fallback when expression is blank (blank = NULL/empty string/empty list)             |
| AND           | `AND(cond1, cond2, ...)`                                           | Boolean              | TRUE when all conditions are TRUE                                                            |
| OR            | `OR(cond1, cond2, ...)`                                            | Boolean              | TRUE when any condition is TRUE                                                              |
| NOT           | `NOT(condition)`                                                   | Boolean              | Logical negation                                                                             |
| ISBLANK       | `ISBLANK(value)`                                                   | Boolean              | Tests if blank (NULL/empty string/empty list are blank; 0 and FALSE are not)                 |
| ISNULL        | `ISNULL(value)`                                                    | Boolean              | Tests if NULL (only NULL is true; empty string is not)                                       |
| ISERROR       | `ISERROR(expr)`                                                    | Boolean              | Tests if expression errors                                                                   |
| ISNUMBER      | `ISNUMBER(value)`                                                  | Boolean              | Tests if value is a number                                                                   |
| CONTAIN       | `CONTAIN(search_range, value, ...)`                                | Boolean              | Tests if a list or `select` (`multiple=true`) contains the value; **does NOT do text substring matching** |
| CONTAINSALL   | `CONTAINSALL(search_range, value, ...)`                            | Boolean              | Tests if a list or `select` (`multiple=true`) contains all specified values |
| CONTAINSONLY  | `CONTAINSONLY(search_range, value, ...)`                           | Boolean              | Tests if a list or `select` (`multiple=true`) contains only the specified values |
| TRUE          | `TRUE()`                                                           | Boolean              | Returns TRUE                                                                                 |
| FALSE         | `FALSE()`                                                          | Boolean              | Returns FALSE                                                                                |
| RECORD_ID     | `RECORD_ID()`                                                      | Text                 | Returns the current row's record ID                                                          |
| RANDOMBETWEEN | `RANDOMBETWEEN(min_int, max_int, [keep_updating])`                 | Number               | Random integer in the specified range                                                        |
| RANDOMITEM    | `RANDOMITEM(list, [keep_updating])`                                | Matches element type | Randomly picks one element from a list                                                       |

### 8.2 Numeric functions

| Function                                                          | Signature                                | Return type | Description                                                                                                                                                                                                                                                |
| --- | --- | --- | --- |
| SUM                                                               | `SUM(val1, val2, ...)`                   | Number      | Sum; accepts multiple values or a list                                                                                                                                                                                                                     |
| AVERAGE                                                           | `AVERAGE(val1, val2, ...)`               | Number      | Average                                                                                                                                                                                                                                                    |
| MAX                                                               | `MAX(val1, val2, ...)`                   | Number      | Maximum                                                                                                                                                                                                                                                    |
| MIN                                                               | `MIN(val1, val2, ...)`                   | Number      | Minimum                                                                                                                                                                                                                                                    |
| MEDIAN                                                            | `MEDIAN(val1, val2, ...)`                | Number      | Median                                                                                                                                                                                                                                                     |
| COUNTA                                                            | `COUNTA(val1, val2, ...)`                | Number      | Count of non-blank values                                                                                                                                                                                                                                  |
| COUNTIF                                                           | `COUNTIF(data_range, condition)`         | Number      | Count matching items. Data range can be a **table** (CurrentValue is a row, use `CurrentValue.[Field]`) or a **column** (CurrentValue is a scalar value)                                                                                                   |
| SUMIF                                                             | `SUMIF(data_range, condition)`           | Number      | Sum matching values. Data range **must be a numeric column** (e.g. `[Table].[NumField]`); CurrentValue is each value in that column (scalar), cannot use `CurrentValue.[Field]` to access other fields. For cross-field conditions, use FILTER+SUM instead |
| ROUND                                                             | `ROUND(number, digits)`                  | Number      | Round. digits: 1=one decimal, 0=integer, -1=tens place                   

... [Content truncated, total 59,261 chars] ...