---
lane: graphic_bitmap_first
surface: migrated
---

# Migrated Workflow: Graphic Asset Generation

Bitmap-first image generation has moved to the standalone `solo-graphic-generation` skill.

## Compatibility Redirect

1. Invoke the `Skill` tool with `name: "solo-graphic-generation"`.
2. Pass the user's complete image request, current project path when present, and any already-confirmed size or aspect ratio.
3. Stop this workflow immediately after the skill call.

## Hard Rules

- Do not read sibling files in this migrated workflow directory.
- Do not call `GenerateImage` from `solo-design`.
- The standalone skill must confirm the requested output size before its first generation call.
