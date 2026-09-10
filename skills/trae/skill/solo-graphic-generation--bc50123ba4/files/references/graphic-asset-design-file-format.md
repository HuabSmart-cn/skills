# Image-Only Design File Structure

## Directory Structure

```text
<project-name>/
├── <project-name>.design
├── assets/
└── generation-summary.json        # optional internal summary
```

Do not create `pages/`, `partials/`, `theme/`, or `colors_and_type.css` for normal image-only output. When appending any generated image into an existing design project, preserve the existing project structure and only add the new asset file plus its image node.

## `.design` Shape

```json
{
  "data": [
    {
      "id": "image-001",
      "title": "主视觉",
      "type": "image",
      "version": 1,
      "createdAt": 1782990000000,
      "devMetadata": {
        "imageSrc": "assets/main-key-visual.jpg"
      },
      "canvasData": {
        "x": 0,
        "y": 0
      }
    }
  ],
  "config": {
    "autoLayout": true,
    "deviceType": "freeSize",
    "projectName": "活动主视觉"
  }
}
```

## Node Rules

| Field | Rule |
| --- | --- |
| `id` | `image-NNN`, 3+ digit zero-padded monotonic counter |
| `title` | Semantic title in the user's language; do not mechanically Title Case filenames |
| `type` | Must be `"image"` |
| `version` | Positive integer, normally `1` |
| `createdAt` | Positive integer timestamp in milliseconds |
| `devMetadata.imageSrc` | Relative path under `assets/` |
| `canvasData` | Contains only numeric `x` and `y`; no `group` field |

## Asset Rules

- Put generated images directly under `assets/`; keep the structure flat.
- Supported extensions: `.jpg`, `.jpeg`, `.png`, `.webp`, `.gif`, `.svg`.
- Every top-level supported image file under `assets/` must be registered in `.design`.
- Do not create image nodes for non-image files.
- Do not register files from nested subdirectories.
- Do not leave a node pointing to a missing file.

## Naming Rules

| Asset | Filename Examples |
| --- | --- |
| Poster | `campaign-poster.jpg` |
| Banner | `summer-sale-banner.jpg` |
| KV | `launch-key-visual.jpg` |
| Cover | `video-cover.jpg`, `wechat-cover.jpg` |
| Invitation | `event-invitation.jpg` |
| Generated image asset | `organic-farmer-couple.png`, `product-cutout.png`, `hero-visual.jpg`, `concept-variant-a.jpg` |
| Variant | `campaign-poster-warm.jpg`, `campaign-poster-minimal.jpg` |

Use semantic kebab-case. Preserve any user-specified supported extension; otherwise use `.jpg` for ordinary raster output. Avoid numeric-only names and mechanical suffixes unless the user asks for numbered alternatives.

## Validation

Run:

```bash
node {SKILL_DIR}/scripts/validate-graphic-asset-design.mjs <design-project-path>
```

The validator checks:

- Exactly one `.design` file in the project root.
- `.design.data` is non-empty.
- Every node is `type: "image"`.
- Image node fields are complete.
- Referenced image files exist under `assets/`.
- Every top-level image asset is registered exactly once.
- No `pages/*.html` page flow is mixed into this image-only project.
