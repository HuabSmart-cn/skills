"""
_common.py — Shared logic for ComfyUI skill scripts.

Single source of truth for:
- HTTP transport (with retry/backoff, streaming, timeout handling)
- Cloud detection and endpoint mapping (local ComfyUI vs Comfy Cloud)
- Workflow node-type catalogs (param patterns, model loaders, output nodes)
- API-format validation
- Path-traversal-safe file writes
- API-key loading from env / CLI

Stdlib-only by design (with optional `requests` upgrade if installed). Python 3.10+.
"""

from __future__ import annotations

import json
import os
import random
import re
import sys
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator
from urllib.parse import urlparse

# Optional: prefer `requests` if installed (better redirects, streaming, header handling)
try:
    import requests  # type: ignore[import-not-found]
    HAS_REQUESTS = True
except ImportError:  # pragma: no cover - exercised via stdlib fallback
    HAS_REQUESTS = False
    import urllib.error
    import urllib.request


# =============================================================================
# Constants & catalogs
# =============================================================================

DEFAULT_LOCAL_HOST = "http://127.0.0.1:8188"
DEFAULT_CLOUD_HOST = "https://cloud.comfy.org"
ENV_API_KEY = ***REDACTED***

# Connection / retry defaults
DEFAULT_HTTP_TIMEOUT = 60          # seconds — single-attempt request timeout
DEFAULT_RETRIES = 3                # total attempts including the first
RETRY_BASE_DELAY = 1.0             # seconds — exponential backoff base
RETRY_MAX_DELAY = 30.0             # seconds — cap on backoff
RETRY_STATUS_CODES = {408, 429, 500, 502, 503, 504, 522, 524}

# Streaming download chunk size (bytes)
DOWNLOAD_CHUNK_SIZE = 1 << 16  # 64 KiB

# Heuristic: workflows with these node types tend to be slow → larger default timeout
SLOW_OUTPUT_NODES = {
    "VHS_VideoCombine", "SaveAnimatedWEBP", "SaveAnimatedPNG",
    "SaveVideo", "SaveAudio", "SaveAnimateDiffVideo",
    "SVD_img2vid_Conditioning",
    "WanVideoSampler", "HunyuanVideoSampler",
    "CogVideoSampler", "LTXVideoSampler",
}

# ---------------------------------------------------------------------------
# Output node catalog (extensible — community packs add their own)
# ---------------------------------------------------------------------------
OUTPUT_NODES: set[str] = {
    # Built-in
    "SaveImage", "PreviewImage",
    "SaveAudio", "SaveVideo", "PreviewAudio", "PreviewVideo",
    "SaveAnimatedWEBP", "SaveAnimatedPNG",
    # Common community packs
    "VHS_VideoCombine",       # Video Helper Suite
    "ImageSave",              # Was Node Suite
    "Image Save",             # Was Node Suite (alt name)
    "easy imageSave",         # easy-use
    "Image Save With Metadata",
    "PreviewImage|pysssss",   # pysssss preview
    "ShowText|pysssss",
    "SaveLatent",
    "SaveGLB",                # 3D
    "Save3D",
}

# ---------------------------------------------------------------------------
# Folder aliases — handle ComfyUI's gradual folder renames
# ---------------------------------------------------------------------------
# When `check_deps.py` queries `/models/<folder>` and gets 404 / empty,
# it tries each alias in turn. Critical for Comfy Cloud which has fully
# migrated to the new naming (unet → diffusion_models, clip → text_encoders).
FOLDER_ALIASES: dict[str, list[str]] = {
    "unet": ["unet", "diffusion_models"],
    "diffusion_models": ["diffusion_models", "unet"],
    "clip": ["clip", "text_encoders"],
    "text_encoders": ["text_encoders", "clip"],
    "controlnet": ["controlnet", "control_net"],
}


def folder_aliases_for(folder: str) -> list[str]:
    """Return the search order of folder names (primary first)."""
    return FOLDER_ALIASES.get(folder, [folder])


# ---------------------------------------------------------------------------
# Model-loader catalog: class_type -> (input field, model folder)
# ---------------------------------------------------------------------------
# A loader can have multiple fields (e.g., DualCLIPLoader has clip_name1 and
# clip_name2). We list them with explicit entries. The folder name is the
# *canonical* one; FOLDER_ALIASES is consulted when querying.
MODEL_LOADERS: dict[str, list[tuple[str, str]]] = {
    # Checkpoints
    "CheckpointLoaderSimple":   [("ckpt_name", "checkpoints")],
    "CheckpointLoader":         [("ckpt_name", "checkpoints")],
    "CheckpointLoader (Simple)": [("ckpt_name", "checkpoints")],
    "ImageOnlyCheckpointLoader": [("ckpt_name", "checkpoints")],
    "unCLIPCheckpointLoader":   [("ckpt_name", "checkpoints")],
    # LoRA
    "LoraLoader":               [("lora_name", "loras")],
    "LoraLoaderModelOnly":      [("lora_name", "loras")],
    "LoraLoaderTagsQuery":      [("lora_name", "loras")],
    # VAE
    "VAELoader":                [("vae_name", "vae")],
    # ControlNet
    "ControlNetLoader":         [("control_net_name", "controlnet")],
    "DiffControlNetLoader":     [("control_net_name", "controlnet")],
    "ControlNetLoaderAdvanced": [("control_net_name", "controlnet")],
    # CLIP / text encoders (primary "clip" folder; check_deps tries text_encoders too)
    "CLIPLoader":               [("clip_name", "clip")],
    "DualCLIPLoader":           [("clip_name1", "clip"), ("clip_name2", "clip")],
    "TripleCLIPLoader":         [("clip_name1", "clip"), ("clip_name2", "clip"), ("clip_name3", "clip")],
    "CLIPVisionLoader":         [("clip_name", "clip_vision")],
    # UNET / Diffusion model (primary "unet"; check_deps tries diffusion_models too)
    "UNETLoader":               [("unet_name", "unet")],
    "DiffusionModelLoader":     [("model_name", "diffusion_models")],
    "UNETLoaderGGUF":           [("unet_name", "unet")],
    # Upscaler
    "UpscaleModelLoader":       [("model_name", "upscale_models")],
    # Style / GLIGEN / Hypernetwork
    "StyleModelLoader":         [("style_model_name", "style_models")],
    "GLIGENLoader":             [("gligen_name", "gligen")],
    "HypernetworkLoader":       [("hypernetwork_name", "hypernetworks")],
    # IPAdapter family (community).
    # Note: IPAdapterUnifiedLoader's `preset` and IPAdapterInsightFaceLoader's
    # `provider` are enums (not file paths), so they're intentionally omitted —
    # check_deps would otherwise treat enum values as missing model files.
    "IPAdapterModelLoader":     [("ipadapter_file", "ipadapter")],
    "InstantIDModelLoader":     [("instantid_file", "instantid")],
    # AnimateDiff / video
    "ADE_LoadAnimateDiffModel": [("model_name", "animatediff_models")],
    "ADE_AnimateDiffLoaderWithContext": [("model_name", "animatediff_models")],
    "ADE_AnimateDiffLoaderGen1": [("model_name", "animatediff_models")],
    # Photomaker
    "PhotoMakerLoader":         [("photomaker_model_name", "photomaker")],
    # Sampler / scheduler models
    "ModelSamplingFlux":        [],  # parametric only
}

# ---------------------------------------------------------------------------
# Param patterns: (class_type, field_name) -> friendly_name
# Order matters — first match wins for naming. Use _meta.title for disambiguation.
# ---------------------------------------------------------------------------
PARAM_PATTERNS: list[tuple[str, str, str]] = [
    # ---- Prompts ----
    ("CLIPTextEncode", "text", "prompt"),
    ("CLIPTextEncodeSDXL", "text_g", "prompt"),
    ("CLIPTextEncodeSDXL", "text_l", "prompt_l"),
    ("CLIPTextEncodeSDXLRefiner", "text", "refiner_prompt"),
    ("CLIPTextEncodeFlux", "clip_l", "prompt_l"),
    ("CLIPTextEncodeFlux", "t5xxl", "prompt"),
    ("CLIPTextEncodeFlux", "guidance", "guidance"),
    ("smZ CLIPTextEncode", "text", "prompt"),
    ("BNK_CLIPTextEncodeAdvanced", "text", "prompt"),

    # ---- Standard sampling ----
    ("KSampler", "seed", "seed"),
    ("KSampler", "steps", "steps"),
    ("KSampler", "cfg", "cfg"),
    ("KSampler", "sampler_name", "sampler_name"),
    ("KSampler", "scheduler", "scheduler"),
    ("KSampler", "denoise", "denoise"),
    ("KSamplerAdvanced", "noise_seed", "seed"),
    ("KSamplerAdvanced", "steps", "steps"),
    ("KSamplerAdvanced", "cfg", "cfg"),
    ("KSamplerAdvanced", "sampler_name", "sampler_name"),
    ("KSamplerAdvanced", "scheduler", "scheduler"),
    ("KSamplerAdvanced", "start_at_step", "start_at_step"),
    ("KSamplerAdvanced", "end_at_step", "end_at_step"),

    # ---- Modern sampler chain (Flux / SD3 / SDXL refiner via SamplerCustom) ----
    ("RandomNoise", "noise_seed", "seed"),
    ("BasicScheduler", "steps", "steps"),
    ("BasicScheduler", "scheduler", "scheduler"),
    ("BasicScheduler", "denoise", "denoise"),
    ("KSamplerSelect", "sampler_name", "sampler_name"),
    # NB: BasicGuider has no cfg input (it just bundles model+conditioning).
    ("CFGGuider", "cfg", "cfg"),
    ("DualCFGGuider", "cfg_conds", "cfg"),
    ("DualCFGGuider", "cfg_cond2_negative", "cfg_negative"),
    ("ModelSamplingFlux", "max_shift", "max_shift"),
    ("ModelSamplingFlux", "base_shift", "base_shift"),
    ("ModelSamplingFlux", "width", "model_width"),
    ("ModelSamplingFlux", "height", "model_height"),
    ("ModelSamplingSD3", "shift", "shift"),
    ("ModelSamplingDiscrete", "sampling", "sampling"),
    ("SDTurboScheduler", "steps", "steps"),
    ("SDTurboScheduler", "denoise", "denoise"),
    ("SamplerCustom", "noise_seed", "seed"),
    ("SamplerCustom", "cfg", "cfg"),
    # NB: SamplerCustomAdvanced takes a NOISE input (from RandomNoise) — no seed field directly.

    # ---- Dimensions / latent ----
    ("EmptyLatentImage", "width", "width"),
    ("EmptyLatentImage", "height", "height"),
    ("EmptyLatentImage", "batch_size", "batch_size"),
    ("EmptySD3LatentImage", "width", "width"),
    ("EmptySD3LatentImage", "height", "height"),
    ("EmptySD3LatentImage", "batch_size", "batch_size"),
    ("EmptyHunyuanLatentVideo", "width", "width"),
    ("EmptyHunyuanLatentVideo", "height", "height"),
    ("EmptyHunyuanLatentVideo", "length", "length"),
    ("EmptyHunyuanLatentVideo", "batch_size", "batch_size"),
    ("EmptyMochiLatentVideo", "width", "width"),
    ("EmptyMochiLatentVideo", "height", "height"),
    ("EmptyMochiLatentVideo", "length", "length"),
    ("EmptyLTXVLatentVideo", "width", "width"),
    ("EmptyLTXVLatentVideo", "height", "height"),
    ("EmptyLTXVLatentVideo", "length", "length"),
    ("LatentUpscale", "width", "upscale_width"),
    ("LatentUpscale", "height", "upscale_height"),
    ("LatentUpscaleBy", "scale_by", "scale_by"),
    ("ImageScale", "width", "width"),
    ("ImageScale", "height", "height"),

    # ---- Image input ----
    ("LoadImage", "image", "image"),
    ("LoadImageMask", "image", "mask_image"),
    ("LoadImageOutput", "image", "image"),
    ("VHS_LoadVideo", "video", "video"),
    ("VHS_LoadAudio", "audio", "audio"),

    # ---- Model selection (sometimes useful to swap per run) ----
    ("CheckpointLoaderSimple", "ckpt_name", "ckpt_name"),
    ("CheckpointLoader", "ckpt_name", "ckpt_name"),
    ("ImageOnlyCheckpointLoader", "ckpt_name", "ckpt_name"),
    ("VAELoader", "vae_name", "vae_name"),
    ("UNETLoader", "unet_name", "unet_name"),
    ("DiffusionModelLoader", "model_name", "diffusion_model_name"),
    ("UpscaleModelLoader", "model_name", "upscale_model_name"),
    ("CLIPLoader", "clip_name", "clip_name"),
    ("DualCLIPLoader", "clip_name1", "clip_name1"),
    ("DualCLIPLoader", "clip_name2", "clip_name2"),
    ("ControlNetLoader", "control_net_name", "controlnet_name"),

    # ---- LoRA ----
    ("LoraLoader", "lora_name", "lora_name"),
    ("LoraLoader", "strength_model", "lora_strength"),
    ("LoraLoader", "strength_clip", "lora_strength_clip"),
    ("LoraLoaderModelOnly", "lora_name", "lora_name"),
    ("LoraLoaderModelOnly", "strength_model", "lora_strength"),

    # ---- ControlNet ----
    ("ControlNetApply", "strength", "controlnet_strength"),
    ("ControlNetApplyAdvanced", "strength", "controlnet_strength"),
    ("ControlNetApplyAdvanced", "start_percent", "controlnet_start"),
    ("ControlNetApplyAdvanced", "end_percent", "controlnet_end"),

    # ---- IPAdapter ----
    ("IPAdapterAdvanced", "weight", "ipadapter_weight"),
    ("IPAdapterAdvanced", "start_at", "ipadapter_start"),
    ("IPAdapterAdvanced", "end_at", "ipadapter_end"),
    ("IPAdapter", "weight", "ipadapter_weight"),

    # ---- Upscale ----
    ("ImageUpscaleWithModel", "upscale_method", "upscale_method"),

    # ---- AnimateDiff ----
    ("ADE_AnimateDiffLoaderWithContext", "motion_scale", "motion_scale"),
    ("ADE_AnimateDiffLoaderGen1", "motion_scale", "motion_scale"),

    # ---- Video / Save ----
    ("VHS_VideoCombine", "frame_rate", "frame_rate"),
    ("VHS_VideoCombine", "format", "video_format"),
    ("VHS_VideoCombine", "filename_prefix", "filename_prefix"),
    ("SaveImage", "filename_prefix", "filename_prefix"),

    # ---- Hunyuan / Wan / LTX video ----
    ("HunyuanVideoSampler", "seed", "seed"),
    ("HunyuanVideoSampler", "steps", "steps"),
    ("HunyuanVideoSampler", "cfg", "cfg"),
    ("WanVideoSampler", "seed", "seed"),
    ("WanVideoSampler", "steps", "steps"),
    ("WanVideoSampler", "cfg", "cfg"),
    ("LTXVScheduler", "max_shift", "max_shift"),
    ("LTXVScheduler", "base_shift", "base_shift"),

    # ---- rgthree primitives (often used as user-facing inputs) ----
    ("Seed (rgthree)", "seed", "seed"),
    ("Image Comparer (rgthree)", "image_a", "image"),
    ("Power Lora Loader (rgthree)", "PowerLoraLoaderHeaderWidget", "_lora_header"),

    # ---- Easy-use / utility primitives ----
    ("PrimitiveNode", "value", "primitive_value"),
    ("easy seed", "seed", "seed"),
    ("easy positive", "positive", "prompt"),
    ("easy negative", "negative", "negative_prompt"),
    ("easy fullLoader", "ckpt_name", "ckpt_name"),
    ("easy fullLoader", "vae_name", "vae_name"),
    ("easy fullLoader", "lora_name", "lora_name"),
    ("easy fullLoader", "positive", "prompt"),
    ("easy fullLoader", "negative", "negative_prompt"),
]

# Prompt-like fields whose value should be scanned for embedding references
PROMPT_FIELDS = {"text", "text_g", "text_l", "t5xxl", "clip_l", "positive", "negative"}

# Pattern matches: embedding:name, embedding:name.pt, embedding:name:1.2, (embedding:name:1.2)
# Word-boundary at start avoids matching things like "no_embedding:foo".
EMBEDDING_REGEX = re.compile(
    r"(?:^|[\s,(\[])embedding\s*:\s*([A-Za-z0-9_\-\./\\]+?)(?:\.(?:pt|safetensors|bin))?(?=[\s:,)\(\]]|$)",
    re.IGNORECASE,
)


# =============================================================================
# Cloud detection & endpoint routing
# =============================================================================

CLOUD_DOMAIN_SUFFIXES = (".comfy.org",)
CLOUD_DOMAIN_EXACT = {"cloud.comfy.org"}


def is_cloud_host(host: str) -> bool:
    """True if the host points at Comfy Cloud (or staging/preview subdomain)."""
    parsed = urlparse(host if "://" in host else f"http://{host}")
    hostname = (parsed.hostname or "").lower()
    if hostname in CLOUD_DOMAIN_EXACT:
        return True
    return any(hostname.endswith(s) for s in CLOUD_DOMAIN_SUFFIXES)


def build_cloud_aware_url(base: str, path: str, *, force_cloud: bool | None = None) -> str:
    """Build a URL that adds /api prefix when targeting Comfy Cloud.

    Local ComfyUI accepts both `/foo` and `/api/foo` for many endpoints.
    Cloud requires `/api/foo`.

    `path` should be a path component (e.g. "/prompt") or full path with query
    (e.g. "/view?filename=x").
    """
    base = base.rstrip("/")
    cloud = is_cloud_host(base) if force_cloud is None else force_cloud
    if not path.startswith("/"):
        path = "/" + path
    if cloud and not path.startswith("/api/"):
        path = "/api" + path
    return base + path


def cloud_endpoint(path: str) -> str:
    """Map a cloud endpoint path to its current canonical form.

    Handles known renames documented in the Comfy Cloud API:
      /history       -> /history_v2
      /models/<f>    -> /experiment/models/<f>
      /models        -> /experiment/models
    """
    if path.startswith("/history") and not path.startswith("/history_v2"):
        return "/history_v2" + path[len("/history"):]
    if path.startswith("/models/"):
        return "/experiment/models/" + path[len("/models/"):]
    if path == "/models":
        return "/experiment/models"
    return path


def resolve_url(base: str, path: str, *, is_cloud: bool | None = None) -> str:
    """Top-level URL resolver. Applies cloud rename + /api prefix as needed."""
    cloud = is_cloud_host(base) if is_cloud is None else is_cloud
    if cloud:
        path = cloud_endpoint(path)
    return build_cloud_aware_url(base, path, force_cloud=cloud)


# =============================================================================
# API key resolution
# =============================================================================

def resolve_api_key(explicit: ***REDACTED***
    """Look up API key from CLI flag → env var. Strips whitespace and quotes."""
    val = explicit if explicit else os.environ.get(ENV_API_KEY)
    if val is None:
        return None
    val = val.strip().strip("'\"")
    return val or None


# =============================================================================
# HTTP transport
# =============================================================================

@dataclass
class HTTPResponse:
    status: int
    headers: dict[str, str]
    body: bytes
    url: str  # final URL after redirects

    def text(self, encoding: str = "utf-8") -> str:
        return self.body.decode(encoding, errors="replace")

    def json(self) -> Any:
        return json.loads(self.body.decode("utf-8", errors="replace"))


def _sleep_backoff(attempt: int, base: float = RETRY_BASE_DELAY, cap: float = RETRY_MAX_DELAY) -> None:
    """Sleep with full-jitter exponential backoff."""
    delay = min(cap, base * (2 ** attempt))
    delay = random.uniform(0, delay)
    time.sleep(delay)


def http_request(
    method: str,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    json_body: Any = None,
    data: bytes | None = None,
    files: dict | None = None,
    form: dict | None = None,
    timeout: float = DEFAULT_HTTP_TIMEOUT,
    follow_redirects: bool = True,
    retries: int = DEFAULT_RETRIES,
    stream: bool = False,
    sink: Path | None = None,
) -> HTTPResponse:
    """Single entry point for all HTTP traffic.

    Behavior:
      - Retries on connection errors and on HTTP statuses in RETRY_STATUS_CODES,
        with exponential backoff + jitter.
      - For cross-host redirects, drops Authorization-style headers (so signed
        URLs don't leak the API key to S3/CloudFront).
      - When `stream=True` and `sink` is a Path, streams the response body to
        disk in 64 KiB chunks instead of buffering.

    Either `json_body`, `data`, or `files`+`form` may be supplied (mutually exclusive).
    """
    if headers is None:
        headers = {}
    headers = dict(headers)  # copy
    headers.setdefault("User-Agent", "hermes-comfyui-skill/5.0")

    if files or form is not None:
        # Multipart upload — needs `requests`. The stdlib fallback lacks
        # multipart encoding helpers; raise a clear error.
        if not HAS_REQUESTS:
            raise RuntimeError(
                "Multipart upload requires the `requests` package. "
                "Install with: pip install requests"
            )

    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            resp = _http_once(
                method=method, url=url, headers=headers,
                json_body=json_body, data=data, files=files, form=form,
                timeout=timeout, follow_redirects=follow_redirects,
                stream=stream, sink=sink,
            )
            if resp.status in RETRY_STATUS_CODES and attempt + 1 < retries:
                _sleep_backoff(attempt)
                continue
            return resp
        except (TimeoutError, ConnectionError, OSError) as e:
            last_exc = e
            if attempt + 1 < retries:
                _sleep_backoff(attempt)
                continue
            raise

    # Should not reach here unless retries was 0
    if last_exc:
        raise last_exc
    raise RuntimeError("http_request: retries exhausted with no response")


_SENSITIVE_HEADERS = ("x-api-key", "authorization", "cookie")


if HAS_REQUESTS:
    class _StripSensitiveOnRedirectSession(requests.Session):
        """Session that drops sensitive headers on cross-host redirects.

        `requests` already strips `Authorization` cross-host (rebuild_auth),
        but it does NOT strip custom headers like `X-API-Key`. We override
        `rebuild_auth` to additionally strip every header in
        `_SENSITIVE_HEADERS` when the destination is a different host —
        critical when ComfyUI Cloud's `/api/view` redirects to a signed S3 URL.
        """

        def rebuild_auth(self, prepared_request, response):  # type: ignore[override]
            super().rebuild_auth(prepared_request, response)
            try:
                old_url = response.request.url
                new_url = prepared_request.url
                old_host = (urlparse(old_url).hostname or "").lower()
                new_host = (urlparse(new_url).hostname or "").lower()
                if old_host and new_host and old_host != new_host:
                    headers = prepared_request.headers
                    for key in list(headers.keys()):
                        if key.lower() in _SENSITIVE_HEADERS:
                            del headers[key]
            except Exception:
                # Defensive: never let header stripping break a redirect.
                pass


def _http_once(
    *, method: str, url: str, headers: dict[str, str],
    json_body: Any, data: bytes | None, files: dict | None, form: dict | None,
    timeout: float, follow_redirects: bool,
    stream: bool, sink: Path | None,
) -> HTTPResponse:
    """One HTTP attempt. No retry."""
    if HAS_REQUESTS:
        kwargs: dict[str, Any] = {
            "method": method, "url": url, "headers": headers,
            "timeout": timeout, "allow_redirects": follow_redirects,
        }
        if json_body is not None:
            kwargs["json"] = json_body
        elif data is not None:
            kwargs["data"] = data
        elif files is not None or form is not None:
            kwargs["files"] = files
            kwargs["data"] = form
        if stream:
            kwargs["stream"] = True

        # Use the subclass that strips sensitive headers cross-host
        with _StripSensitiveOnRedirectSession() as s:
            try:
                r = s.request(**kwargs)
                if stream and sink is not None:
                    sink.parent.mkdir(parents=True, exist_ok=True)
                    with sink.open("wb") as f:
                        for chunk in r.iter_content(DOWNLOAD_CHUNK_SIZE):
                            if chunk:
                                f.write(chunk)
                    body = b""  # already drained
                else:
                    body = r.content
                return HTTPResponse(
                    status=r.status_code,
                    headers={k: v for k, v in r.headers.items()},
                    body=body,
                    url=r.url,
                )
            except requests.exceptions.RequestException as e:
                # Convert to TimeoutError / ConnectionError so the retry loop
                # picks them up uniformly with the stdlib path.
                if isinstance(e, requests.exceptions.Timeout):
                    raise TimeoutError(str(e)) from e
                raise ConnectionError(str(e)) from e

    # ---------- stdlib fallback ----------
    if json_body is not None:
        body_bytes = json.dumps(json_body).encode("utf-8")
        headers.setdefault("Content-Type", "application/json")
    else:
        body_bytes = data
    req = urllib.request.Request(url, data=body_bytes, headers=headers, method=method)

    # urllib follows redirects by default. We need to:
    # 1) intercept cross-host redirects and drop X-API-Key
    # 2) optionally NOT follow redirects when follow_redirects=False
    class _RedirectHandler(urllib.request.HTTPRedirectHandler):
        def __init__(self, original_host: str, follow: bool):
            self.original_host = original_host
            self.follow = follow

        def redirect_request(self, req2, fp, code, msg, hdrs, newurl):
            if not self.follow:
                return None
            new_host = (urlparse(newurl).hostname or "").lower()
            if new_host != self.original_host:
                # Build a new request with cleaned headers
                clean_headers = {
                    k: v for k, v in req2.header_items()
                    if k.lower() not in {"x-api-key", "authorization", "cookie"}
            

... [Content truncated, total 33,760 chars] ...