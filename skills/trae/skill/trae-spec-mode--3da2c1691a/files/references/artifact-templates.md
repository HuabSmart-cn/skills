# Artifact Templates

Use these templates when the Spec Mode workflow creates or updates its durable
artifacts.
Include only fields that apply; preserve existing evidence and history.

## Contents

- `spec.md`
- `tasks.md`
- `review.md`
- Independent review report
- Review issue

## `spec.md`

```markdown
# [Project Title] - Product Requirements Document

## Overview
- **Summary**: [What is being built]
- **Purpose**: [Why]
- **Target Users**: [Who]

## Goals
- [Goal]

## Non-Goals
- [Excluded scope]

## Background & Context
- [Evidence and prior decisions]

## Functional Requirements
- **FR-1**: [Required behavior]

## Non-Functional Requirements
- **NFR-1**: [Quality requirement]

## Constraints
- **Technical**: [...]
- **Business**: [...]
- **Dependencies**: [...]

## Assumptions
- [...]

## Acceptance Criteria

### AC-1: [Rule title]
- **Type**: `rule`
- **Given**: [...]
- **When**: [...]
- **Then**: [...]
- **Pass Condition**: [...]
- **Evidence**: [...]

### AC-2: [Rubric title]
- **Type**: `rubric`
- **Dimension**: [...]
- **Scale**: 1-5
- **Anchors**: 1 = [...]; 3 = [...]; 5 = [...]
- **Pass Threshold**: >= 4
- **Evidence**: [...]

## Open Questions
- [ ] [...]
```

## `tasks.md`

```markdown
# [Project Title] - Implementation Plan

## Task 1: [Descriptive title]
- **Status**: `pending`
- **Priority**: high | medium | low
- **Depends On**: [Item IDs or "None"]
- **Description**:
  - [Implementation outcome]
- **Acceptance Criteria Addressed**: [AC IDs]
- **Test Requirements**:
  - `rule` TR-1.1: [Binary condition and evidence]
  - `rubric` TR-1.2: [Dimension]; scale 1-5; anchors 1/3/5; threshold >= 4; evidence [...]
- **Notes**: [Optional]
```

The example shows both TR types; include only applicable types and at least one TR
per item. Add status-specific fields only when that status occurs.

### Status-Specific Fields

Completed:

```markdown
- **Status**: `completed`
- **Completion Evidence**:
  - [Rule result, command output, or artifact]
  - [Rubric score, rationale, and evidence]
```

Blocked:

```markdown
- **Status**: `blocked`
- **Blocked By**: [Observable blocker]
- **Unblock Condition**: [Condition that permits resumption]
```

Cancelled:

```markdown
- **Status**: `cancelled`
- **Cancellation Reason**: [Why the work is no longer required]
- **Cancellation Approved By**: [User approval evidence]
```

## `review.md`

Create this file only after the implementation queue drains.

```markdown
# [Project Title] - Independent Review

- [ ] CP-R1: [Binary product outcome]
  - **Type**: `rule`
  - **Covers**: [AC/TR IDs]
  - **Evidence**: Pending

- [ ] CP-U1: [Evaluative product outcome]
  - **Type**: `rubric`
  - **Covers**: [AC/TR IDs]
  - **Scale**: 1-5
  - **Anchors**: 1 = [...]; 3 = [...]; 5 = [...]
  - **Pass Threshold**: >= 4
  - **Evidence**: Pending

## Review History

### Review R1
- **Result**: `pass` | `fail` | `blocked`
- **Evidence**: [...]
- **Blocked By**: [Only when blocked]
- **Resume When**: [Only when blocked]
```

Every AC/TR must be covered. Combine related ACs/TRs only when one coherent,
observable checkpoint verifies them.

## Independent Review Report

```markdown
# Review R[N]
- **Result**: `pass` | `fail` | `blocked`
- **Checks Performed**:
  - [Check and command/action]
- **Evidence**:
  - [Observed result]
- **Checkpoint Results**:
  - CP-R1 (`rule`): `pass` | `fail` | `blocked`
  - CP-U1 (`rubric`): `pass` | `fail` | `blocked`; score [1-5]; rationale [...]
- **Findings**:
  - [ID]: `actionable` | `advisory`; severity; reproduction; expected outcome
- **Recommended Issues**:
  - [Title, priority, AC/checkpoint links, regression requirement]
```

Apply these invariants:

- `pass` requires every checkpoint to pass, every AC to have independent
  evidence, and no actionable finding or blocked check.
- `fail` requires at least one actionable finding.
- Every failed checkpoint maps to an actionable finding.
- Every actionable finding maps to a pending review issue.
- `blocked` records an unavailable environment, permission, or dependency rather
  than an implementation defect.

## Review Issue

After a failed Review has recorded its findings in `review.md`, transition to
Implement and materialize every actionable finding with this template before
selecting work.

```markdown
## Issue I-[N]: [Finding title]
- **Status**: `pending`
- **Priority**: high | medium | low
- **Depends On**: [Item IDs or "None"]
- **Discovered By**: Review R[N]
- **Description**:
  - [Observable gap and reproduction]
- **Acceptance Criteria Addressed**: [AC IDs]
- **Test Requirements**:
  - `rule` TR-I-[N].1: [Regression condition and evidence]
  - `rubric` TR-I-[N].2: [Dimension; scale; anchors; threshold; evidence]
- **Notes**: [Optional]
```

Include only applicable TR types and at least one TR. Prefer a new issue over
reopening completed work; reopen only when its local completion evidence was
invalid.
