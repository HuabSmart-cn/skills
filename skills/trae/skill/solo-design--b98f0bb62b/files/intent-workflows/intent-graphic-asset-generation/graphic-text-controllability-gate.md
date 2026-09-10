---
lane: graphic_bitmap_first
purpose: text controllability gate
---

# Graphic Text Controllability Gate

Use bitmap-first only when exact editable/readable text is not central to the deliverable.

Route to `intent-project-complex-build` with `graphic_layout_static` when the request contains dense copy, prices, schedules, tables, legal/brand copy, PPT/one-pager/manual content, or post-generation text correction requirements.

When routing to `graphic_layout_static`, the Main Agent must write `project.deliverableCompletenessChecklist` before page dispatch. The checklist must cover required pages/assets, required copy blocks, required information types, expected vs actual page count, source material coverage, and `missingRequiredItems[]`. For text-critical deliverables, each `requiredCopyBlocks[]` row must include `{label, text, htmlSrc, selector, role}` so final validation can verify actual default visibility.

Bitmap-first output is forbidden when `layoutStaticRequired=true`.

Before generation, record the gate decision:

```json
{
  "graphicStrategyGate": "bitmap-first | layout-static",
  "textCriticality": "low | medium | high",
  "copyDensity": "short | medium | dense",
  "layoutStaticRequired": false,
  "bitmapFirstAllowed": true,
  "graphicStrategyRoutingReason": "short emotional poster copy"
}
```

If `textCriticality=high`, `copyDensity=dense`, or the request mentions PPT, one-pager, manual, table, price, schedule, legal copy, or brand copy, set `layoutStaticRequired=true` and route to `graphic_layout_static`. Do not ask the image model to carry exact readable/editable information in these cases.
