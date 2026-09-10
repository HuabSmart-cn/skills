---
name: solo-graphic-generation
description: Generate bitmap-first static visual assets such as posters, banners, KV/key visuals, covers, invitations, social cards, illustrations, product images, and image batches without HTML. Confirm the output size before generation; if an exact size is unsupported, expose the constraint and wait for the user to choose a replacement instead of substituting one.
---

# Solo Graphic Generation

Use this Skill when the requested deliverable is the generated bitmap image itself rather than an editable HTML page. It owns text-to-image generation for posters, banners, KV/key visuals, covers, cards, invitations, illustrations, portraits, product images, transparent-background assets, and image batches.

This Skill is self-contained. Read `references/graphic-asset-design-file-format.md` before writing a `.design` file.

## Scope Gate

Stay in this Skill when visual impact is primary and exact editable text, DOM structure, interactions, or page flow are not required.

Immediately hand off and stop this Skill when:

- an existing bitmap must be edited, retouched, extended, or changed at pixel level: invoke `Skill` with `name: "solo-image-edit"`;
- exact readable/editable copy is central, including prices, dates, venues, schedules, tables, legal copy, dense body copy, PPT, one-pager, or manual/document layout: invoke `Skill` with `name: "solo-design"` and state that the request requires `graphic_layout_static`;
- the user requests UI screens, websites, page layouts, components, or interactions: invoke `Skill` with `name: "solo-design"`;
- the user requests a reusable Design Library, token architecture, or component system: ***REDACTED***

Do not create HTML, `pages/`, theme files, or page nodes in bitmap-first mode.

## Non-Negotiable Rules

- Confirm the generation size before the first `GenerateImage` call.
- A precise size or aspect ratio explicitly supplied by the user counts as the user's requested size. It does not authorize a different size.
- Never silently choose a default size when the user has not provided one.
- Never replace exact dimensions with a preset, nearest size, same-ratio size, larger render, smaller render, or post-generation resize without the user's explicit confirmation.
- When a size-related schema or tool error occurs, expose the actual constraint to the user and open the next round by asking them to choose a replacement size.
- Never invent a tool limitation, infer an undocumented mapping, or record a substituted size as user-confirmed.
- Every successful image that is kept must be saved under the owning project's `assets/` directory and registered as a `.design` `type: "image"` node.
- For a new deliverable, create exactly one root `.design` file after at least one image succeeds.
- For an existing project, append image nodes to its existing root `.design`; do not create a second project or overwrite existing nodes.
- Use `GenerateImage` directly for visual generation. Do not create an HTML composition and rasterize it as a substitute.
- Do not use bitmap generation for text-critical deliverables that require exact readable or editable copy.

## Step 1 — Classify Bitmap-First Output

Record a compact decision in working notes:

```json
{
  "graphicStrategyGate": "bitmap-first",
  "textCriticality": "low | medium",
  "copyDensity": "none | short | medium",
  "bitmapFirstAllowed": true,
  "layoutStaticRequired": false,
  "routingReason": "image itself is the requested deliverable"
}
```

If exact copy is central or `layoutStaticRequired` would be `true`, hand off to `solo-design` before asking for image size.

## Step 2 — Confirm Generation Size

Before any `GenerateImage` call, preserve the user's size request verbatim and identify the exact `image_size` value that will be sent. If those values differ, generation remains blocked until the user explicitly accepts the proposed value.

If the current request does not already contain a precise size, aspect ratio, or supported preset:

1. Use `AskUserQuestion` in the user's language.
2. Ask one direct question such as: `这批图片要生成什么尺寸或比例？`
3. Offer purpose-aware options, for example:
   - `16:9 横版` for banners, landscape KV, and presentation covers;
   - `1:1 方图` for social posts and square cards;
   - `9:16 竖版` for vertical posters and stories;
   - `4:3 / 3:4` for conventional landscape or portrait artwork.
4. Let the tool's custom/other answer collect exact dimensions such as `1200x628`.
5. Stop generation and wait for the answer. Do not call `GenerateImage` in the same turn while size remains unconfirmed.

If `AskUserQuestion` is unavailable, ask the same question in normal chat and wait.

For a batch, ask once whether one size applies to all images unless the user already specified per-image sizes. After the answer, inspect the runtime `GenerateImage.image_size` schema and map the confirmed choice to a supported preset or custom size. If the exact requested size is unsupported, explain the nearest supported choices and ask the user to confirm one before generation.

### Unsupported or Rejected Size Gate

Apply this gate whenever the requested exact dimensions are absent from the runtime schema, violate a documented constraint, or a `GenerateImage` call returns a size validation error:

1. Preserve and repeat the user's exact requested dimensions.
2. State the schema constraint or tool error accurately and concisely. Do not turn one failed value into a broader claim such as "custom sizes are unsupported" unless the tool explicitly says so.
3. Present only alternatives supported by the current runtime description or error. Clearly label any uncertainty or contradiction between the schema and backend behavior.
4. Ask the user to choose or provide a replacement size. A same-ratio preset or an upscaled/downscaled size is still a replacement and requires confirmation.
5. End the failed attempt by asking the user which replacement size to use next. Do not silently retry with a preset, and do not create a `.design` file for an ungenerated result.

Example after a rejection:

> 你指定的 `500×500` 被生图服务拒绝，错误提示为“总像素数至少需要 3,686,400”。工具说明仍列出了若干预设尺寸，因此当前说明与后端校验可能不一致。我不会自行改成其他尺寸。你希望改用工具列出的方图预设，还是提供满足限制的新尺寸？

The example error threshold is illustrative evidence from one response, not a permanent rule. Always use the current schema and actual error.

## Step 3 — Plan Assets

After size confirmation, determine:

- project display name in the user's language;
- asset count, defaulting to one only when the user did not request a count;
- semantic title and kebab-case filename for each image;
- confirmed output size for each image;
- required short visible copy, when any;
- subject, composition, focal point, palette, material, lighting, and visual direction;
- whether this is a new image-only project or append mode for an existing canvas.

For variants, make each direction meaningfully different in composition, palette, or visual metaphor.

## Step 4 — Generate Images

For a new project, create the project directory and flat `assets/` directory first, but do not write an empty `.design`.

Generate independent images in parallel when possible. Each call must use the user-confirmed size:

```json
{
  "prompt": "Poster / banner / KV / cover purpose: subject and business context, short required copy when provided, composition, visual style, palette, lighting, publish context, high quality, production-ready graphic design, clean unbranded final artwork, no platform UI, no source website frame, no gallery page, no creator tag, no corner label",
  "path": "<design-project>/assets/<semantic-filename-without-extension>",
  "image_size": "<confirmed runtime-supported size>"
}
```

Rules:

- Preserve the user's requested subject, format, background, crop, completeness, material, and composition.
- Retry a failed image at most once only for a transient, non-size error, using the same user-confirmed `image_size`.
- Treat a different `image_size` after a size/schema/validation failure as the user's next-round choice, not as an automatic retry.
- Omit failed images from `.design`.
- If every image fails, stop without creating an empty `.design`.
- Accept a successful generation result; do not post-process it because of development-preview overlays.

## Step 5 — Register on the Design Canvas

Follow `references/graphic-asset-design-file-format.md`.

For a new project:

1. Write one `.design` file containing one image node per successful asset.
2. Use monotonic ids `image-001`, `image-002`, and so on.
3. Set `config.autoLayout: true`, `deviceType: "freeSize"`, and a semantic `projectName`.

For append mode:

1. Re-read the latest existing `.design` after generation.
2. Preserve all existing nodes, interactions, positions, and the full `config`.
3. Append one image node per new asset using the next monotonic image ids.
4. Write the file once.

## Step 6 — Record Generation Summary

Read `skill-release-manifest.json`, then write `generation-summary.json` containing:

- skill provenance;
- requested size verbatim, actual tool `image_size`, and explicit user confirmation for any difference;
- asset count;
- filename, title, intended size, and generation status for each asset;
- canvas image node ids.

Do not hard-code a version from this document. Use the manifest value actually read at runtime.

Never describe an automatic substitution as confirmed by the user. If the requested size was rejected and the user has not selected an alternative, do not write a successful generation summary.

## Step 7 — Validate

Run:

```bash
node {SKILL_DIR}/scripts/validate-graphic-asset-design.mjs <design-project-path>
```

Validation failure blocks completion. Fix missing image registrations, invalid nodes, or broken asset references before finishing.

## Completion

Reply in the user's language and report:

- confirmed generation size;
- number of successfully generated assets;
- registered `.design` image node ids;
- validation status;
- any failed or omitted direction.

Do not expose absolute paths or claim completion from `GenerateImage` alone.
