---
name: media-generation
description: Generate, edit, or transform images and videos. Use this skill the moment a user asks to draw, paint, illustrate, make a picture, generate an image, edit an image, swap a background, change a color, remove an object, combine references, create a video, animate a still, morph between frames, or produce b-roll — including phrasings like "text to image", "image to image", "image to video", "first frame", "last frame", "reference image", "Seedance", or "gpt-image-2".
category: automation
symbolName: photo.on.rectangle.angled
seedVersion: 5
allowed-tools: Bash
shell: bash
---

# Media Generation

All requests run through the `neo media` CLI against Neo Gateway. The CLI handles auth, rewrites payloads for the right upstream, and streams results to `artifacts/media-generation/` by default.

**Never** hand-roll `curl`, read tokens, or call `neo-auth` directly. The helper below resolves the neo binary in every environment (bundled, dev, installed):

***REDACTED***
set -euo pipefail

neo_media_cli() {
  local cli_exec="${NEO_AGENT_CLI_EXEC:-}"
  local cli_entry="${NEO_AGENT_CLI_ENTRY:-}"
  if [ -n "$cli_exec" ] && { [ -x "$cli_exec" ] || command -v "$cli_exec" >/dev/null 2>&1; }; then
    case "$(basename "$cli_exec")" in
      bun|bun.exe)
        if [ -n "$cli_entry" ] && [ -f "$cli_entry" ]; then
          "$cli_exec" "$cli_entry" media "$@"
          return
        fi
        ;;
      *)
        "$cli_exec" media "$@"
        return
        ;;
    esac
  fi
  if command -v neo >/dev/null 2>&1; then
    neo media "$@"
    return
  fi
  echo "neo media CLI is unavailable: NEO_AGENT_CLI_EXEC=${NEO_AGENT_CLI_EXEC:-unset}, NEO_AGENT_CLI_ENTRY=${NEO_AGENT_CLI_ENTRY:-unset}, neo is not on PATH" >&2
  return 1
}

# Compatibility alias for occasional model spelling drift. Prefer
# `neo_media_cli` in commands and examples.
neomediacli() {
  neo_media_cli "$@"
}
```

## How to take a media request

Users rarely hand you a clean flag list. They describe what they want in prose, in whichever language they speak. Your job is to **infer the right command + parameters from intent**, run it, and only stop to ask when a decision actually changes the result. Do not keyword-match; read the request as a whole and figure out the desired result.

### 1. Infer the command from what the user said and what's attached

Start from what's *in* the current turn. An attached image means the user has something they want transformed; no attachment almost always means generation from scratch, even when the wording sounds polished ("final hero image", "production banner", "client deliverable") — those are descriptions of what to produce, not hints that an existing file is being edited.

| Signal in the message or context | Pick |
|---|---|
| No image attached, user describes a scene | `image generate` |
| One image attached + user asks to change / restyle / clean / recolor it | `image edit --image <that path>` |
| One image attached + user points at a specific area ("remove the cup", "only change the sky") | `image edit --image <path> --mask <path>` — if no mask exists, ask **once** whether to regenerate the whole image or to mask a region (see §"When to ask") |
| No image + user asks for a video | `video create` |
| One image attached + "animate / make it move / turn into a video" | `video create --first-frame <that path>` |
| Two images attached + "morph / transition / A becomes B" | `video create --first-frame <A> --last-frame <B>` |
| Any real or photoreal person face/character reference that must stay consistent | `video create --character-asset <that image>` — this wins over the generic multi-image reference rule |
| Multiple images attached + "combine / put them in the same scene / keep both subjects" | `video create --reference-image <each>` |
| User references a previous `taskId` / asks "is it done" | `video get --id <taskId>` |

Attachments arrive as absolute paths in the current turn — use them directly, never ask the user to re-upload.

Before choosing a video reference mode, inspect the attached image content. A file
path alone is not enough to know whether it is a real or photoreal person. Use
the visible attachment preview / image-reading ability available in the current
agent environment before deciding between `--reference-image` and
`--character-asset`.

If you cannot visually inspect the image but the user's task is about a real
person, face, avatar, host, actor, model, spokesperson, or "character
consistency", prefer `--character-asset`. If you cannot inspect the image and
the intent is still ambiguous, ask one short question instead of guessing with
`--reference-image`.

### 2. Infer parameters silently when the prompt tells you

You **don't** need permission to set a parameter when the user's description implies it. Read the prompt for intent and fill things in:

Use the subject and purpose to choose each parameter. The table is a set of reasoning hooks, not a keyword list — judge the whole request.

| Parameter | Infer from this intent |
|---|---|
| **Orientation / size** | Default is 4K landscape (16:9). Set `--size` only to change **shape**: portrait/vertical feed → `9:16`; square icon/avatar/logo → `1:1`; otherwise leave it. The default is already max resolution — only step down (`@2K`/`@1K`) for a draft or an explicit "small/quick" request. |
| **Quality** | Default is `high` (max). Only drop to `low`/`medium` for an explicit draft/sketch or a cost-sensitive request. |
| **Video length** | Default is `--duration 15` (longest). Pass a shorter value when the scene is a single brief moment: a quick gesture / loop / single beat → `--duration 5`; a couple of actions → `--duration 10`. Leave it at the 15s default for anything narrative or open-ended. Supported values: 5, 10, 15 (seconds). |
| **Video audio** | Is the video diegetic (cinematic, narrative, characters speaking / the world making sound)? Leave audio on. Is it a silent UI loop, product b-roll, or animated logo? `--audio false`. |
| **Seed** | Only set `--seed` when the user explicitly asks for reproducibility or "same look again". Otherwise let it randomize. |
| **Output path** | Use the default `artifacts/media-generation/` folder unless the user named a destination. |

If none of these signals appear, go with the defaults — don't stall for input — **but do not invent subject matter to fill in a request the user left open-ended**. If the user asked for "a big image" or "something nice" without specifying what the image should show, your job is not to pick a topic for them; either ask what they want depicted or, when the only blocker is orientation, ask just that. Inventing a detailed fantasy scene from a one-line vague request is a misuse.

### 3. Confirm only the parameters that would genuinely waste work if wrong

One short clarifying question is fine; a barrage of them isn't. Ask only when **all three** are true: the choice is irreversible in one shot, the user's wording is ambiguous, and a wrong guess would require regenerating from scratch. See the "When to ask" section at the bottom for the exact shortlist.

## Image generation (`image generate`)

Image tasks are **async** for normal user-facing work. Start them once with a hook receipt, then let the daemon run the provider request and send a hook completion wake when the file is ready.

```bash
neo_media_cli image generate --prompt "<description>" [options] --hook --json
```

Always pass `--hook --json` so you can parse `hookId` and `plannedOutputPath` from stdout without blocking the model turn. Use non-hook image commands only when explicitly debugging the CLI itself.

### Showing the result to the user

After the hook completion wake succeeds, reply with one short sentence describing the completed media. The runtime surfaces the wake's structured result refs as artifact cards automatically through `producedArtifacts`; do not include a Markdown `file://` link unless the user explicitly asks for a copyable path.

The hook completion wake is authoritative: the daemon has already completed the provider call and verified the output file path before waking you. Do **not** call `Read`, `cat`, `file`, `ls`, or any other verification tool on generated images/videos just to confirm the media exists. Reading binary media wastes a turn and can slow or break the reply. Use the returned result path directly unless the user explicitly asks you to inspect pixels or debug a corrupted artifact.

A good completion reply is one concise status line, for example: `Sunset banner is ready.` Skip extra description when the user's last prompt already said it.

### Sizes

**Default when `--size` is omitted: `3840x2160` (16:9 4K) — maximum resolution.**
Pass `--size` only to change shape or step down. Two accepted forms:

- **Exact pixels** — e.g. `3840x2160`, `2880x2880`, `2160x3840`. Sent verbatim.
- **Aspect token** — `16:***REDACTED***

| Want | Pass |
|---|---|
| Max-res landscape (default) | omit, or `16:9` |
| Max-res portrait | `9:16` |
| Max-res square | `1:1` |
| Smaller / faster / cheaper | add `@2K` or `@1K`, e.g. `1:1@1K` |

Higher resolution costs more (4K ≈ 3.5× the 1K rate) and is slower. Only step down when the user wants a draft/thumbnail or explicitly asks for smaller.

### Quality

**Default when `--quality` is omitted: `high` — maximum fidelity.**

| `--quality` | Cost | When |
|---|---|---|
| `low` | cheapest, fastest | thumbnails, drafts |
| `medium` | balanced | general use when cost matters |
| `high` | **default**, most faithful | final deliverables, print |

`high` is ~3.5× the `low` rate. Drop to `low`/`medium` only for drafts or when the user wants to save cost.

### Multiple variations

`--n <count>` is passed through for completeness, but the current image channel (`gpt-image-2-all`) **silently returns one image regardless of `--n`**. If the user asks for multiple options, loop the command yourself and vary the prompt or seed each time. The CLI already stores multi-image responses correctly (extra files become `foo-2.png`, `foo-3.png`, …) for the day the upstream starts honoring `n`.

When looping multiple image/video hooks for one user intent, create one explicit
work run and pass it to every command in that batch:

```bash
work_run_id="media-$(date +%Y%m%d%H%M%S)-$$"
work_run_title="Storyboard options"
work_total=12

for i in $(seq 1 "$work_total"); do
  neo_media_cli image generate \
    --prompt "Storyboard frame ${i}: <specific variation>" \
    --hook \
    --work-run-id "$work_run_id" \
    --work-run-title "$work_run_title" \
    --work-item-id "frame-${i}" \
    --work-total "$work_total" \
    --json
done
```

Only share a `--work-run-id` for items that belong to the same user intent.
If the user asks for another image later, or the conversation changes topic in
between, start a new work run. Do not group by clock time or by similar prompt
text; the id is the contract.

### Example — landscape banner (defaults already give 4K + high)

```bash
neo_media_cli image generate \
  --prompt "A minimalist mountain range at sunrise, flat vector, warm palette" \
  --hook \
  --json
```
That produces a 16:9 4K image at `high` quality with no flags. For a vertical
poster pass `--size 9:16`; for a quick draft pass `--size 1:1@1K --quality low`.

Then save the returned `hookId`. When the hook completion wake arrives, reply with a short completion sentence; the runtime renders the returned result refs as artifact cards. Do not `Read` the generated image/video as a verification step.

### Don't use

- `--background transparent` — currently unstable on `gpt-image-2`. If the user needs a transparent cutout, generate a plain image and suggest they export with the alpha tool of their choice.

## Image editing / image-to-image (`image edit`)

```bash
neo_media_cli image edit \
  --image /absolute/input.png \
  --prompt "<what to change>" \
  [--mask /absolute/mask.png] \
  --hook \
  --json
```

After the hook completion wake succeeds, reply with a short completion sentence — same rule as `image generate`. The runtime renders the returned result refs as artifact cards.

- `--image` accepts `.png`, `.jpg`, `.jpeg`, `.webp`, `.gif`. Any other extension errors out client-side before the network call.
- `--mask` is a PNG where **transparent pixels mark the region to regenerate** and opaque pixels stay fixed. Omit it and the model edits the whole image globally.
- Phrase the prompt as the desired final image, not as a diff. `"a red apple on a marble counter"` works better than `"change the background to marble"`.

## Video generation (`video create`)

All video tasks are **async**. Start them once with a hook receipt, then let the daemon check progress. Do not keep the model turn alive just to poll.

### Hook flow

| Situation | Move |
|---|---|
| Starting a new video | Run `video create ... --hook --output <path> --json`. Save the returned `hookId`. |
| Video still running | Tell the user it started and the daemon will send a hook completion wake when it finishes. |
| Hook completion wake succeeded | Reply with a one-line description. The runtime renders the wake result refs as artifact cards. |
| Hook completion wake failed / expired | Say the concrete failure and offer the smallest rerun/change. |

Use blocking `--wait` only when explicitly debugging the CLI itself. Normal user-facing video work should return quickly with `taskId`, `hookId`, and a clear expectation.

### Modes

Every mode accepts an optional `--prompt`. Local paths are base64-encoded automatically; URLs pass through.

**Text-to-video**
```bash
neo_media_cli video create \
  --prompt "A corgi surfing a small wave at sunset, cinematic" \
  --ratio 16:9 --duration 5 \
  --output artifacts/media-generation/corgi-surfing.mp4 \
  --hook \
  --json
```

**Image-to-video (first frame)**
```bash
neo_media_cli video create \
  --first-frame /absolute/input.png \
  --prompt "The subject slowly turns toward the camera" \
  --ratio 16:9 --duration 5 \
  --output artifacts/media-generation/animated-input.mp4 \
  --hook \
  --json
```

**First + last frame morph**
```bash
neo_media_cli video create \
  --first-frame /absolute/before.png \
  --last-frame  /absolute/after.png \
  --prompt "Smooth morph between the two states" \
  --duration 5 \
  --output artifacts/media-generation/morph.mp4 \
  --hook \
  --json
```
Exactly one of each. Do not combine with `--reference-image`.

**Multi-subject reference**
```bash
neo_media_cli video create \
  --reference-image /absolute/hero.png \
  --reference-image /absolute/prop.png \
  --reference-image-url https://cdn.example.com/scene.jpg \
  --prompt "Put the hero and prop into the referenced scene" \
  --ratio 16:9 \
  --output artifacts/media-generation/hero-scene.mp4 \
  --hook \
  --json
```
`--reference-image` and `--reference-image-url` are **repeatable** — pass the same flag once per image, in order. Do **not** invent synthetic names like `--reference-image-2`; the CLI only recognises the canonical flag repeated. Do not combine with `--first-frame` or `--last-frame`.

If one of the referenced subjects is a real or photoreal person, pass that image as `--character-asset` instead of `--reference-image`; keep non-person props/scenes as `--reference-image`. The real-person rule takes priority over "multi-subject reference".

**Reference audio (drive the video with a sound/voice track)**
```bash
neo_media_cli video create \
  --reference-image /absolute/face.png \
  --reference-audio /absolute/voice.mp3 \
  --prompt "The person speaks in sync with the audio" \
  --ratio 16:9 \
  --output artifacts/media-generation/talking-face.mp4 \
  --hook \
  --json
```
`--reference-audio` (local path, `.mp3/.wav/.m4a/.aac/.flac/.ogg`) and `--reference-audio-url` (remote URL) are **repeatable**. Audio reference is **reference-media mode**: it **must** be accompanied by at least one image/character reference — Seedance rejects an audio reference that arrives alone (the CLI fails fast locally with a clear error). Use this when the user attaches both a face/subject image and an audio clip and wants the video synced to that audio. Do not combine with `--first-frame`/`--last-frame`.

**Real-person face (character asset)**
```bash
neo_media_cli video create \
  --character-asset /absolute/face.png \
  --prompt "The person turns toward the camera and smiles, cinematic" \
  --ratio 16:9 --duration 5 \
  --output artifacts/media-generation/face-video.mp4 \
  --hook \
  --json
```
Use `--character-asset <path|url>` (repeatable; `--character-asset-url` for remote) **whenever the reference image is a real person**. A raw real face sent as `--reference-image` is rejected by content review ("may contain real person"); `--character-asset` instead registers the face with BytePlus (pre-moderation) into a reusable `asset://` reference, then generates from it. This routes through the byteplus-direct backend automatically and adds a small (~8%) surcharge. Do not combine with `--first-frame`/`--last-frame`. If BytePlus rejects the image, the CLI surfaces a clear "preprocessing failed — use another image" error; suggest a clearer, front-facing photo.

Audio is **off by default for character assets** — BytePlus moderates generated audio over real faces and will fail the whole job ("output audio may contain sensitive information"). Pass `--audio true` only if the user explicitly wants sound and accepts the higher rejection risk.

> Backend note: `--character-asset*` (and animals/objects/scenery still fine via `--reference-image`) selects the `byteplus-direct` backend. Everything else defaults to the legacy path unchanged. You normally don't pass `--provider`; it's inferred.

### Parameters

| Flag | Values | Notes |
|---|---|---|
| `--duration` | `5`, `10`, or `15` (seconds) | integer; **default 15** (longest). Cost scales linearly with duration — drop to 5/10 for a brief single-beat clip. |
| `--ratio` | `16:9`, `9:16`, `1:1`, `adaptive` | **default `16:9`**; `adaptive` lets the model pick based on input images |
| `--resolution` | `480p`, `720p`, `1080p` | **default `1080p`** (maximum). Cost scales with resolution (1080p ≈ 3× the 480p rate) and duration; step down only for a draft or cost-sensitive request. |
| `--seed` | any integer | same seed + same prompt + same inputs → same video |
| `--audio` | `true` / `false` | default `true` |
| `--watermark` | `true` / `false` | default `false` |

### Do not pass

The active video model is `doubao-seedance-2-0`. The gateway will return `400 not supported for this model` if you send:
- `--frames` (use `--duration` instead)
- `--camera-fixed`

Other Seedance variants support them; when we upgrade, this note gets removed.

### Reading an existing task

```bash
neo_media_cli video get \
  --id cgt-xxxxxxxx \
  --download \
  --output artifacts/media-generation/final.mp4 \
  --json
```

Use `video get` only when debugging a provider task id by hand. Normal user work should rely on the hook completion wake instead of manual polling. Without blocking flags, it returns the current status and exits.

## What to tell the user

Every CLI call with `--json` prints a single JSON object to stdout. Read these fields and compose your reply:

| Field | Meaning |
|---|---|
| `outputPath` | Primary file saved locally — always mention this |
| `outputPaths` | All files when multiple images were returned (`--n > 1`) |
| `taskId` | Video job id; save it in case the user asks for debugging details later |
| `hookId` | Runtime hook receipt id; the daemon uses it to send the hook completion wake |
| `plannedOutputPath` | Where the finished image/video will be saved later; not markable until the hook succeeds |
| `status` | `created` / `running` / `succeeded` / `failed` |
| `hookState` | `running` at launch, or a terminal state if the provider finished immediately |
| `videoUrl` | Hosted mp4 URL (present on `succeeded`) |
| `responsePath` | Raw provider response on disk — useful when you need to debug |
| `usage` | Token or call usage the user might be billed for |

Good reply shape:
- **Images still running**: "Started — hook `<hookId>`. I will let you know when it is ready." Do not mark; there is no local file yet.
- **Images finished**: after the hook completion wake, reply with a short caption. The runtime renders the completed file as an artifact card.
- **Videos still running**: "Started — task `<taskId>`, hook `<hookId>`. I will let you know when it is ready." Do not mark; there is no local file yet.
- **Videos finished**: after the hook completion wake, reply with a one-liner describing the clip. The runtime renders the completed file as an artifact card.

Never dump the whole JSON object back to the user — link the final artifact and describe it in prose.

## When to ask (and when not to)

**Don't ask** when:
- Orientation / quality / duration / audio / seed are inferable or the user didn't care enough to mention them. Use the heuristics above and proceed.
- The user already gave enough to run. A slightly wrong prompt is cheaper to re-run than to interrogate.
- The choice only affects one parameter and re-running is fast (all image calls).

**Do ask — one short question, then run** — when the choice is load-bearing and not inferable. The short list:

| Situation | Ask, concisely |
|---|---|
| User says "edit" or "change" with an attached image but doesn't say *what* | "Edit the whole image, or just a specific region (and if so, which)?" |
| User says "make a video" with **two** images but doesn't say whether it's a morph or a multi-subject composition | "Morph from the first into the second, or put both subjects into one scene?" |
| User wants a video but didn't hint at length and the scene clearly needs more than 5s (multi-action narrative) | "5, 10, or 15 seconds?" |
| User wants a large or print-quality image but leaves the subject and venue entirely open-ended, so orientation is genuinely unknown — three different shapes would each be a defensible answer | "Square, landscape, or portrait?" |
| User explicitly asks "what size should I pick" or similar | Give a recommendation (don't punt back), then proceed if they agree |

Phrase the question in **one short sentence with the two or three concrete options**, not a menu. Example: "Landscape (16:9) for a wallpaper, or square (1:1)?" — not: "Please specify the desired `--size` parameter from the following list...".

After the user answers, just run it. Don't ask a follow-up about quality or audio unless they volunteered a hint.

## Failure playbook

- **Gateway `429` or `408`** → our gateway already fell back to the secondary channel and still hit load. Say: "The image service is saturated right now — same prompt usually works in a minute or two. Want me to retry, or queue it?" Don't retry silently more than once per user turn.
- **Gateway `401` / `403`** → auth issue. Ask the user to sign in via Matrix.app (or run `neo-auth login`).
- **`Unsupported image file extension`** → the user sent an unsupported format. Ask for PNG / JPG / WEBP / GIF, or convert it yourself via `sips -s format png …` before retrying.
- **Seedance `400 not supported for this model`** → you probably sent `--frames` or `--camera-fixed`. Drop them and retry with `--duration`.
- **Video content review says the reference image may contain a real person / face** → keep the full high-quality prompt and retry with `--character-asset` / `--character-asset-url` for the person image. Do not shorten, simplify, or lower quality just to make submission pass.
- **Video `status: failed`** → report the `responsePath` for inspection and offer to rerun with a different prompt / seed. Don't invent a new prompt without asking.
- **Everything times out** → Seedance video jobs can take 60–180s. If the hook completion wake reports expired, report that and offer one rerun with a smaller prompt or duration.
