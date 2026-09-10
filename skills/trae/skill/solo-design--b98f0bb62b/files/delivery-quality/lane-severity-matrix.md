---
owner: delivery-quality
purpose: define error/warning/n-a severity by lane
---

# Lane Severity Matrix

This matrix is the shared quality interpretation layer for deterministic validators and delivery review.

| Check | free_exploration | restore_1to1 | library_bound | graphic_bitmap_first | graphic_layout_static | existing_edit / redesign / variants / theme |
| --- | --- | --- | --- | --- | --- | --- |
| `.design` structural integrity | error | error | error | error | error | error |
| Missing HTML page file | error | error | error | n/a | error | error when page exists |
| Missing image node for kept asset | error | error | error | error | error | error |
| Restore evidence missing | n/a | error | n/a | n/a | n/a | warning unless inherited restore source |
| Library identity / token reference missing | n/a | n/a | error | n/a | n/a | error when `sourceProjectLaneHeritage=***REDACTED***
| Graphic bitmap delivered as page-only | n/a | n/a | n/a | error | n/a | n/a |
| Graphic layout-static degraded to image-only | n/a | n/a | n/a | n/a | error | error when inherited |
| Route contamination / dispatch contract mismatch | warning first | error | error | error when page dispatch mixed in | error | error when artifact ownership breaks |
| Visual polish issue without render break | warning | warning unless source mismatch | warning | warning | warning | warning |

Validators may hard-code render correctness and structural integrity, but lane-specific interpretation must reference this matrix instead of duplicating policy text.
