# Canvas Image Contract

This is the minimum Solo Design canvas contract required by `solo-image-edit`.

## Project Shape

An image-only project normally has:

```text
<project-name>/
├── <project-name>.design
└── assets/
    ├── source-image.png
    └── source-image-comment-edit.png
```

An existing mixed project may also contain `pages/`, theme files, summaries, or other runtime files. Preserve them. The image-edit workflow owns only its generated asset and its appended or explicitly replaced image node.

## `.design` Root

```json
{
  "data": [],
  "config": {
    "autoLayout": true,
    "deviceType": "freeSize",
    "projectName": "Project name"
  }
}
```

- `.design` must be valid JSON.
- `data` must be a non-empty array after registration.
- Preserve the existing `config` object. For a new image-only project, use `autoLayout: true`, `deviceType: "freeSize"`, and a semantic `projectName`.
- Node ids must be unique.

For a direct edit without an existing Design project, copy the original into the new project's flat `assets/` directory and register it as `image-001`. Append the edited comparison as `image-002`. Do not point the new project at an attachment cache or a file outside the project.

## Image Node

```json
{
  "id": "image-002",
  "title": "Hero comment edit",
  "type": "image",
  "version": 1,
  "createdAt": 1785758400000,
  "devMetadata": {
    "imageSrc": "assets/hero-comment-edit.png"
  },
  "canvasData": {
    "x": 1280,
    "y": 0
  }
}
```

| Field | Rule |
| --- | --- |
| `id` | New nodes use the next monotonic `image-NNN` id with at least three digits. Existing ids are never renumbered. |
| `title` | Non-empty semantic title in the user's language. |
| `type` | Exactly `"image"`. |
| `version` | Positive integer. Use `1` for a new node; increment it for an explicit in-place replacement. |
| `createdAt` | Positive millisecond timestamp. Preserve it for in-place replacement. |
| `devMetadata.imageSrc` | Project-relative flat path `assets/<filename>`; never absolute, external, base64, or nested. |
| `canvasData.x/y` | Finite numbers. Image nodes do not use a `group` field. |

Do not add HTML-only fields such as `htmlSrc`, `designType`, or page interaction metadata to an image node.

## Assets

- Put generated outputs directly under `assets/`.
- Supported extensions: `.jpg`, `.jpeg`, `.png`, `.webp`, `.gif`, `.svg`.
- Use semantic kebab-case filenames.
- A kept generated file must have exactly one canvas image node pointing to it.
- Never point a node at a missing file.
- Preserve source images and unrelated assets.

## Comparison Placement

Comparison is the default:

1. Preserve the source image node.
2. Append the edited result after all existing nodes.
3. Prefer the source row: `newX = source.canvasData.x + source.naturalWidth + gap`, `newY = source.canvasData.y`.
4. Use a gap of roughly 80 canvas pixels, then shift right or down until the new position does not overlap a known node.
5. If usable source geometry is unavailable and `config.autoLayout === true`, use the next finite canvas coordinate following the existing image-node ordering.

The placement only needs to be deterministic and visible; it must not modify positions of existing nodes.

## Multiple Source Images

- Produce one final edited asset and one result node per distinct source image.
- Aggregate all comments belonging to the same source before registration.
- Use unique filenames, node ids, and positions for every result.
- Never attach one source image's comments or screenshots to another source image's generation call.
