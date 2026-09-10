---
name: buddy-image-processing
description: Process existing images with text and watermark removal, general enhancement, portrait beautification, image restoration, and general matting. Use the ImageGen tool for image generation.
---

# Image Processing

Use `buddy-image-processing.py` only when the user provides an existing image and requests one of the supported processing operations.

## Routing Rules

- If the user requests text or watermark removal, use `erase`.
- If the user requests image enhancement, sharpening, denoising, deblurring, or low-light enhancement, use `enhance`.
- If the user requests portrait beautification or retouching, use `beauty`.
- If the user requests old-photo or damaged-image restoration, use `restore`.
- If the user requests foreground extraction or a transparent background, use `matting`.
- `matting` only returns the foreground on a transparent background. A white, colored, or replacement background requires a separate compositing step; never claim that matting alone completed it.
- If the user requests text-to-image generation, generative image-to-image creation, or style transfer, stop using this skill and use `ImageGen`.
- If the user requests a 3D model or template-based image-to-video effect, stop using this skill and use `buddy-multimodal-generation`.
- If the user requests general text-to-video or image-to-video generation, stop using this skill and use `VideoGen`.

## Supported Capabilities

| Capability | Operation | Typical Use Cases | Trigger Phrases |
|---|---|---|---|
| AI text and watermark removal | `erase` | Remove watermarks, logos, channel marks, subtitles, stamps, labels, and outdated text | remove watermark / erase watermark / remove text / erase text / remove logo / remove channel mark / remove subtitles / remove stamp |
| General image enhancement | `enhance` | Improve low-resolution, blurry, noisy, or low-light images | upscale image / enhance resolution / optimize image quality / denoise image / remove blur / enhance image / sharpen / enhance low-light image |
| Portrait beautification | `beauty` | Improve selfies, ID photos, business portraits, model photos, and studio portraits | portrait beautification / skin smoothing / blemish removal / skin whitening / even skin tone / slim face / facial adjustment / portrait retouching / batch beautification |
| Image restoration | `restore` | Restore old photos, scratches, creases, mold stains, fading, damage, and missing regions | restore old photo / restore image / remove scratches / repair damage / fill missing regions / renovate photo |
| General matting | `matting` | Extract people or products onto a transparent background | image matting / one-click matting / remove background / transparent background / transparent PNG / foreground extraction / precise matting |

Each operation maps to a fixed service model. Never override the model mapping.

## Input Rules

- Select exactly one `--operation` from `erase`, `enhance`, `beauty`, `restore`, and `matting`.
- Select exactly one input from `--image-file`, `--image-url`, and `--image-base64`.
- Prefer `--image-file` for local images. Never convert a local image to Base64 in the conversation or shell arguments, and never create a wrapper script to bypass command-length limits.
- Use `--image-url` only for an accessible HTTP(S) URL.
- Use `--image-base64` only when the input is already a small Base64 value. Never print a large Base64 payload in the conversation or logs.
- A local file or decoded Base64 image must be non-empty and smaller than 4 MB.
- Preserve the user's intent and pass additional processing instructions unchanged through `--prompt`. Do not expand them without permission.

## Examples

```bash
python3 <SKILL_DIR>/scripts/buddy-image-processing.py image-edit --operation erase --image-file "/absolute/path/to/photo.png" --prompt "Remove the watermark in the lower-right corner" --token "<clientTempToken>"
python3 <SKILL_DIR>/scripts/buddy-image-processing.py image-edit --operation enhance --image-url "https://example.com/photo.jpg" --token "<clientTempToken>"
```

To submit without polling and query the original task:

```bash
python3 <SKILL_DIR>/scripts/buddy-image-processing.py image-edit --operation restore --image-file "/absolute/path/to/photo.jpg" --no-poll --token "<clientTempToken>"
python3 <SKILL_DIR>/scripts/buddy-image-processing.py status <task_id> --token "<clientTempToken>"
```

## Execution Flow

1. Call `connect_cloud_service` once before each image-processing task.
2. Read only the `clientTempToken` returned for the current task and pass it through `--token`. Stop immediately if the field is missing.
3. Run `image-edit` once. The script polls every 5 seconds by default for up to 600 seconds.
4. If the command times out after returning a `task_id`, query only that task with `status`.
5. Read `result_files[].path`; the script has already saved each result locally.
6. Use `present_files` to display every local result and return its full path to the user.

Never display, explain, cache, or reuse authentication credentials. Never fall back to JWT, `tempToken`, a long-lived Client API Key, or any other credential.

## Retry Rules

- Never automatically retry an `image-edit` submission.
- Never use an external `sleep` loop to run `image-edit` again.
- If submission times out before returning a `task_id`, report `SUBMISSION_STATUS_UNKNOWN`.
- After receiving a `task_id`, only query the original task. If authentication expires, authenticate again without resubmitting.
- Return the actual sanitized error when a call fails. Never fabricate a result or file path.

## Script Execution

Always use the script under the current skill directory:

```text
<SKILL_DIR>/scripts/buddy-image-processing.py
```

Do not guess the WorkBuddy installation directory or manually construct an `app.asar` path. If `python3` is unavailable, try `python`. If neither is available, stop and do not install a runtime automatically.

## Dependencies

- Python 3.7+
- `requests`, installed automatically by the script when missing
