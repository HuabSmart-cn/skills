---
name: solo-image-edit
description: Edit existing bitmap images with image-to-image generation and place every kept result on a `.design` canvas. Use for structured Design image comments or explicit pixel-level edits with an original image.
---

# Solo Image Edit

Use this Skill only for editing an existing bitmap. It consumes the Design image-comment command contract, calls `GenerateImage` in image-to-image mode, and writes every kept result back into the owning `.design` canvas.

This Skill is self-contained. Read `references/canvas-image-contract.md` before changing any asset or `.design` file.

## Non-Negotiable Rules

- Use image-to-image generation. Every `GenerateImage` call must include a non-empty `image_paths`.
- `image_paths[0]` is always the original image and source-of-truth visual base. On later batches, `image_paths[1]` may be the current edited-original working image; annotation screenshots follow in stable annotation order. Only the original or its current edited result may supply output pixels.
- Treat input envelopes as transport details. Extract the source image, edit instruction, location evidence, and any annotation screenshots from the current-turn context without requiring one exact wrapper, field name, or resource-id scheme.
- When multiple comments target one image, or a comment contains boxes, arrows, pen strokes, pins, or other visual markup, pass every resolvable annotation screenshot that fits the call and explicitly map each `<image N>` to its matching comment. The screenshots are location evidence only, never replacement visuals or style references.
- Explicitly tell `GenerateImage` to modify only the original image. Boxes, arrows, outlines, pins, dotted guides, cursor marks, dimming, crop handles, and surrounding editor UI from annotation screenshots must never appear in the generated result.
- Every `GenerateImage` prompt must explicitly instruct the model to remove any watermark or watermark-like overlay from the bottom-right corner and reconstruct the underlying pixels naturally. Do not hide it by cropping, and do not add a replacement mark.
- Preserve all pixels and subjects outside the requested edit regions unless the user explicitly requests a global change.
- A missing annotation screenshot, `imageId`, or preferred wrapper is not by itself blocking when the original image, comment text, and enough structured location evidence are available. Continue with the evidence that exists and never invent a path or identifier.
- Never fall back to text-to-image when the original image cannot be resolved.
- Every kept output must be stored under the owning project's `assets/` directory and represented by a `.design` `type: "image"` node.
- Default to a comparison result: preserve the source node and append one edited image node per source image. Only replace the source node or source file when the user explicitly requests overwrite or in-place replacement.
- Do not edit HTML, CSS, page nodes, Design Library files, or unrelated image nodes.

## Input Evidence

Do not require a fixed JSON envelope. Normalize whatever current-turn context is available into these semantic fields:

- source identity: local image path or project-relative `imagePath`, source node id, title, and natural dimensions when available;
- edit instruction: the visible user comment, an adjacent top-level comment, or the nested annotation comment;
- location evidence: region, image intersection, anchor, rectangles, arrows, pen strokes, or other markups;
- annotation screenshot: an explicitly linked screenshot path/resource or an unambiguous current-turn uploaded screenshot;
- owning project: project root, root `.design` file, and source image node when this is a Design Canvas edit.

Known inputs may include, but are not limited to:

- a `web-element` / `design-canvas-page` record;
- a `selected_browser_item` whose tag is `image-region`, with JSON stored in `outerHTML` or `outer_html`;
- a system-injected `design-image-annotation` payload plus current-turn uploaded files;
- a direct user request with an original image path or attachment.

## Step 1 — Detect and Normalize

1. Find current-turn items whose tag or semantic payload indicates `image-region` / `design-image-annotation`.
2. Parse annotation JSON even when it is nested inside `outerHTML`, `outer_html`, a selected-item wrapper, or another structured command field.
3. Extract the source identity, authoritative comment, location evidence, and any screenshot reference. Prefer the visible or adjacent top-level comment; fall back to `annotation.comment`.
4. Group annotations by source `imagePath`; when absent, use source node id or the resolved original path.
5. Sort each source group by numeric `annotation.index`, then stable input order.
6. Associate screenshots through an explicit resource/path link when available. Otherwise use clearly associated current-turn uploads or stable annotation/upload order only when the pairing is unambiguous.
7. Keep region, image intersection, anchor, and markup geometry even when no screenshot can be resolved.

For a direct non-comment image edit, synthesize one group from the user-provided original image and visible request. Do not fabricate a `design-image-annotation`.

## Step 2 — Resolve Required Files

Resolve the original image using the first existing local path in this order:

1. an explicit current-turn source `filePath` or local path;
2. owning project root plus a relative source path such as `relatePath`;
3. owning project root plus a matching canvas-page `imagePath`;
4. owning project root plus the parsed annotation source `imagePath`;
5. a current-turn local image attachment explicitly identified by the user

Resolve annotation screenshots opportunistically from explicit paths/resource ids or associated current-turn uploads. Include every screenshot that is confidently matched, especially for multi-comment edits and visual markups. If a screenshot is unavailable, retain the comment plus structured coordinates/markup description and continue when those are sufficient to express the edit.

Before generation, verify:

- the original image exists and is a supported image file;
- every comment has non-empty text;
- a structured Design image-comment request's owning project has exactly one root `.design` file;
- the structured `source.nodeId` exists as an image node when this is a Design image-comment request.

Stop before `GenerateImage` only when the original image or edit instruction cannot be resolved, the owning canvas cannot be safely identified, or the runtime lacks image-to-image support. Do not substitute an annotation screenshot for the original image.

For a direct image edit that is not attached to an existing Design project, create a new image-only project before generation: create `assets/`, copy the original image into it with a semantic filename, create exactly one root `.design`, and register the copied source as the first image node using `references/canvas-image-contract.md`. The edited result will then be appended as the comparison node.

## Step 3 — Build the Image-to-Image Call

Prefer one `GenerateImage` call per source image when the reference-image limit allows it. For example, two screenshot-backed comments can be sent as:

```json
{
  "prompt": "Design Canvas image edit: modify only <image 1>, the original image and sole visual base. <image 2> is location evidence for annotation 1; its rectangle marks the target area and must not appear in the result. Apply annotation 1 exactly: \"Remove the chart title\". <image 3> is location evidence for annotation 2; its arrow points to the target and the arrow must not appear in the result. Apply annotation 2 exactly: \"Add a warm sun\". Use the annotation coordinates and markups only to locate edits on <image 1>. Do not copy any rectangle, arrow, outline, pin, guide, dimming, cursor, crop handle, or editor UI from <image 2> or <image 3>. Remove any watermark or watermark-like overlay from the bottom-right corner and reconstruct the underlying pixels naturally; do not crop to hide it and do not add a replacement mark. Preserve every other unrequested part of <image 1>. Return the complete edited original image, not a crop.",
  "image_paths": [
    "/project/assets/hero.png",
    "/resolved/attachments/comment-1.png",
    "/resolved/attachments/comment-2.png"
  ],
  "path": "/project/assets/hero-edited",
  "image_size": "landscape_4_3"
}
```

Prompt requirements:

- Begin with the purpose: `Design Canvas image edit:`.
- State that `<image 1>` is the original image, the sole visual base, and the only image to modify.
- Map each later image to its exact annotation index when a screenshot is included.
- Include each authoritative comment verbatim, preserving its language.
- Include the matching region or intersection coordinates when available.
- Describe markups when present: rectangles define target areas; arrow tips/endpoints identify targets; pen strokes highlight regions. Treat them only as edit-location evidence.
- State explicitly that rectangles, arrows, comment pins, dotted guides, selection boxes, markup strokes, cursor/crosshair UI, crop handles, dimming, and surrounding editor chrome must not appear in the output unless the comment explicitly asks to create such content.
- Include this instruction in every call, including retries and later batches: `Remove any watermark or watermark-like overlay from the bottom-right corner and reconstruct the underlying pixels naturally; do not crop to hide it and do not add a replacement mark.`
- State what must remain unchanged.
- Ask for the complete edited image, not a crop.

When no screenshot is included, omit references to later `<image N>` values and express the same edit using the original image, comment text, and available coordinates/markup geometry.

Use the original aspect ratio. When custom sizes are supported and the original dimensions satisfy the tool constraints, use `naturalWidthxnaturalHeight`; otherwise choose the closest supported preset. Do not distort the aspect ratio merely to match a preset.

`GenerateImage.image_paths` accepts at most nine images. When screenshots exceed the remaining reference slots, process ordered batches. Every batch must keep the original image first, may include the current edited-original result second, and must map every included screenshot and matching comment. Tell later batches to edit the current edited-original while using the original only as fidelity authority; annotation screenshots remain non-output evidence. Repeat the mandatory bottom-right watermark-removal instruction in every batch prompt.

If the runtime `GenerateImage` schema does not expose `image_paths`, stop as blocked because image-to-image capability is unavailable. Do not issue a text-only call.

## Step 4 — Save and Register the Result

Follow `references/canvas-image-contract.md`.

For the default comparison result:

1. Save the generated file directly under `<design-project>/assets/` with a semantic kebab-case name such as `hero-comment-edit.png` or `hero-comment-edit-2.png`.
   Use the actual extension returned by `GenerateImage`; its `path` input omits the extension.
2. Read the existing `.design` JSON.
3. Append a new image node using the next monotonic `image-NNN` id.
4. Set `devMetadata.imageSrc` to the project-relative `assets/<filename>`.
5. Position the result beside the source node using numeric `canvasData.x/y`; use the source image's natural width plus a reasonable gap and avoid overlap with existing nodes.
6. Preserve every existing node and the entire existing `config` object byte-for-byte in meaning.

For an explicitly requested in-place replacement:

1. Keep the existing node id, title, `createdAt`, and `canvasData`.
2. Update only `devMetadata.imageSrc` to the new asset path and increment the positive integer `version`.
3. Do not delete the original asset unless the user explicitly requested deletion and no other node references it.

Write JSON atomically when the environment provides an atomic file-write primitive. Do not leave a partially written `.design`.

## Step 5 — Validate

Run:

```bash
node {SKILL_DIR}/scripts/validate-image-edit-canvas.mjs <design-project-path> --node-id=<result-node-id> --image-src=assets/<result-filename>
```

Validation failure blocks completion. Repair only the new asset registration or the newly changed node; do not rewrite unrelated canvas content.

## Completion

Report:

- number of source images edited;
- number of comments applied;
- result image node ids;
- whether each result was appended or replaced in place;
- validation status;
- a precise blocked reason when image-to-image capability or an input resource was unavailable.

Do not claim success from the `GenerateImage` response alone. Success requires the output file, `.design` registration, and a passing validator.
