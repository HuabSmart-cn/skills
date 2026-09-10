# Shader Pipeline & Composable Effects

Post-processing effects applied to the pixel canvas (`numpy uint8 array, shape (H,W,3)`) after character rendering and before encoding. Also covers **pixel-level blend modes**, **feedback buffers**, and the **ShaderChain** compositor.

> **See also:** composition.md (blend modes, tonemap) · effects.md · scenes.md · architecture.md · optimization.md · troubleshooting.md
>
> **Blend modes:** For the 20 pixel blend modes and `blend_canvas()`, see `composition.md`. All blending uses `blend_canvas(base, top, mode, opacity)`.

## Design Philosophy

The shader pipeline turns raw ASCII renders into cinematic output. The system is designed for **composability** — every shader, blend mode, and feedback transform is an independent building block. Combining them creates infinite visual variety from a small set of primitives.

Choose shaders that reinforce the mood:
- **Retro terminal**: CRT + scanlines + grain + green/amber tint
- **Clean modern**: light bloom + subtle vignette only
- **Glitch art**: heavy chromatic aberration + glitch bands + color wobble + pixel sort
- **Cinematic**: bloom + vignette + grain + color grade
- **Dreamy**: heavy bloom + soft focus + color wobble + low contrast
- **Harsh/industrial**: high contrast + grain + scanlines + no bloom
- **Psychedelic**: color wobble + chromatic + kaleidoscope mirror + high saturation + feedback with hue shift
- **Data corruption**: pixel sort + data bend + block glitch + posterize
- **Recursive/infinite**: feedback buffer with zoom + screen blend + hue shift

---

## Pixel-Level Blend Modes

All operate on float32 [0,1] canvases for precision. Use `blend_canvas(base, top, mode, opacity)` which handles uint8 <-> float conversion.

### Available Modes

```python
BLEND_MODES = {
    "normal":       lambda a, b: b,
    "add":          lambda a, b: np.clip(a + b, 0, 1),
    "subtract":     lambda a, b: np.clip(a - b, 0, 1),
    "multiply":     lambda a, b: a * b,
    "screen":       lambda a, b: 1 - (1-a)*(1-b),
    "overlay":      # 2*a*b if a<0.5, else 1-2*(1-a)*(1-b)
    "softlight":    lambda a, b: (1-2*b)*a*a + 2*b*a,
    "hardlight":    # like overlay but keyed on b
    "difference":   lambda a, b: abs(a - b),
    "exclusion":    lambda a, b: a + b - 2*a*b,
    "colordodge":   lambda a, b: a / (1-b),
    "colorburn":    lambda a, b: 1 - (1-a)/b,
    "linearlight":  lambda a, b: a + 2*b - 1,
    "vividlight":   # burn if b<0.5, dodge if b>=0.5
    "pin_light":    # min(a,2b) if b<0.5, max(a,2b-1) if b>=0.5
    "hard_mix":     lambda a, b: 1 if a+b>=1 else 0,
    "lighten":      lambda a, b: max(a, b),
    "darken":       lambda a, b: min(a, b),
    "grain_extract": lambda a, b: a - b + 0.5,
    "grain_merge":  lambda a, b: a + b - 0.5,
}
```

### Usage

```python
def blend_canvas(base, top, mode="normal", opacity=1.0):
    """Blend two uint8 canvases (H,W,3) using a named blend mode + opacity."""
    af = base.astype(np.float32) / 255.0
    bf = top.astype(np.float32) / 255.0
    result = BLEND_MODES[mode](af, bf)
    if opacity < 1.0:
        result = af * (1-opacity) + result * opacity
    return np.clip(result * 255, 0, 255).astype(np.uint8)

# Multi-layer compositing
result = blend_canvas(base, layer_a, "screen", 0.7)
result = blend_canvas(result, layer_b, "difference", 0.5)
result = blend_canvas(result, layer_c, "multiply", 0.3)
```

### Creative Combinations

- **Feedback + difference** = psychedelic color evolution (each frame XORs with the previous)
- **Screen + screen** = additive glow stacking
- **Multiply** on two different effects = only shows where both have brightness (intersection)
- **Exclusion** between two layers = creates complementary patterns where they differ
- **Color dodge/burn** = extreme contrast enhancement at overlap zones
- **Hard mix** = reduces everything to pure black/white/color at intersections

---

## Feedback Buffer

Recursive temporal effect: frame N-1 feeds back into frame N with decay and optional spatial transform. Creates trails, echoes, smearing, zoom tunnels, rotation feedback, rainbow trails.

```python
class FeedbackBuffer:
    def __init__(self):
        self.buf = None  # previous frame (float32, 0-1)
    
    def apply(self, canvas, decay=0.85, blend="screen", opacity=0.5,
              transform=None, transform_amt=0.02, hue_shift=0.0):
        """Mix current frame with decayed/transformed previous frame.
        
        Args:
            canvas: current frame (uint8 H,W,3)
            decay: how fast old frame fades (0=instant, 1=permanent)
            blend: blend mode for mixing feedback
            opacity: strength of feedback mix
            transform: None, "zoom", "shrink", "rotate_cw", "rotate_ccw",
                       "shift_up", "shift_down", "mirror_h"
            transform_amt: strength of spatial transform per frame
            hue_shift: rotate hue of feedback buffer each frame (0-1)
        """
```

### Feedback Presets

```python
# Infinite zoom tunnel
fb_cfg = {"decay": 0.8, "blend": "screen", "opacity": 0.4,
          "transform": "zoom", "transform_amt": 0.015}

# Rainbow trails (psychedelic)
fb_cfg = {"decay": 0.7, "blend": "screen", "opacity": 0.3,
          "transform": "zoom", "transform_amt": 0.01, "hue_shift": 0.02}

# Ghostly echo (horror)
fb_cfg = {"decay": 0.9, "blend": "add", "opacity": 0.15,
          "transform": "shift_up", "transform_amt": 0.01}

# Kaleidoscopic recursion
fb_cfg = {"decay": 0.75, "blend": "screen", "opacity": 0.35,
          "transform": "rotate_cw", "transform_amt": 0.005, "hue_shift": 0.01}

# Color evolution (abstract)
fb_cfg = {"decay": 0.8, "blend": "difference", "opacity": 0.4, "hue_shift": 0.03}

# Multiplied depth
fb_cfg = {"decay": 0.65, "blend": "multiply", "opacity": 0.3, "transform": "mirror_h"}

# Rising heat haze
fb_cfg = {"decay": 0.5, "blend": "add", "opacity": 0.2,
          "transform": "shift_up", "transform_amt": 0.02}
```

---

## ShaderChain

Composable shader pipeline. Build chains of named shaders with parameters. Order matters — shaders are applied sequentially to the canvas.

```python
class ShaderChain:
    """Composable shader pipeline.
    
    Usage:
        chain = ShaderChain()
        chain.add("bloom", thr=120)
        chain.add("chromatic", amt=5)
        chain.add("kaleidoscope", folds=6)
        chain.add("vignette", s=0.2)
        chain.add("grain", amt=12)
        canvas = chain.apply(canvas, f=features, t=time)
    """
    def __init__(self):
        self.steps = []

    def add(self, shader_name, **kwargs):
        self.steps.append((shader_name, kwargs))
        return self  # chainable

    def apply(self, canvas, f=None, t=0):
        if f is None: f = {}
        for name, kwargs in self.steps:
            canvas = _apply_shader_step(canvas, name, kwargs, f, t)
        return canvas
```

### `_apply_shader_step()` — Full Dispatch Function

Routes shader names to implementations. Some shaders have **audio-reactive scaling** — the dispatch function reads `f["bdecay"]` and `f["rms"]` to modulate parameters on the beat.

```python
def _apply_shader_step(canvas, name, kwargs, f, t):
    """Dispatch a single shader by name with kwargs.
    
    Args:
        canvas: uint8 (H,W,3) pixel array
        name: shader key string (e.g. "bloom", "chromatic")
        kwargs: dict of shader parameters
        f: audio features dict (keys: bdecay, rms, sub, etc.)
        t: current time in seconds (float)
    Returns:
        canvas: uint8 (H,W,3) — processed
    """
    bd = f.get("bdecay", 0)    # beat decay (0-1, high on beat)
    rms = f.get("rms", 0.3)   # audio energy (0-1)

    # --- Geometry ---
    if name == "crt":
        return sh_crt(canvas, kwargs.get("strength", 0.05))
    elif name == "pixelate":
        return sh_pixelate(canvas, kwargs.get("block", 4))
    elif name == "wave_distort":
        return sh_wave_distort(canvas, t,
            kwargs.get("freq", 0.02), kwargs.get("amp", 8), kwargs.get("axis", "x"))
    elif name == "kaleidoscope":
        return sh_kaleidoscope(canvas.copy(), kwargs.get("folds", 6))
    elif name == "mirror_h":
        return sh_mirror_h(canvas.copy())
    elif name == "mirror_v":
        return sh_mirror_v(canvas.copy())
    elif name == "mirror_quad":
        return sh_mirror_quad(canvas.copy())
    elif name == "mirror_diag":
        return sh_mirror_diag(canvas.copy())

    # --- Channel ---
    elif name == "chromatic":
        base = kwargs.get("amt", 3)
        return sh_chromatic(canvas, max(1, int(base * (0.4 + bd * 0.8))))
    elif name == "channel_shift":
        return sh_channel_shift(canvas,
            kwargs.get("r", (0,0)), kwargs.get("g", (0,0)), kwargs.get("b", (0,0)))
    elif name == "channel_swap":
        return sh_channel_swap(canvas, kwargs.get("order", (2,1,0)))
    elif name == "rgb_split_radial":
        return sh_rgb_split_radial(canvas, kwargs.get("strength", 5))

    # --- Color ---
    elif name == "invert":
        return sh_invert(canvas)
    elif name == "posterize":
        return sh_posterize(canvas, kwargs.get("levels", 4))
    elif name == "threshold":
        return sh_threshold(canvas, kwargs.get("thr", 128))
    elif name == "solarize":
        return sh_solarize(canvas, kwargs.get("threshold", 128))
    elif name == "hue_rotate":
        return sh_hue_rotate(canvas, kwargs.get("amount", 0.1))
    elif name == "saturation":
        return sh_saturation(canvas, kwargs.get("factor", 1.5))
    elif name == "color_grade":
        return sh_color_grade(canvas, kwargs.get("tint", (1,1,1)))
    elif name == "color_wobble":
        return sh_color_wobble(canvas, t, kwargs.get("amt", 0.3) * (0.5 + rms * 0.8))
    elif name == "color_ramp":
        return sh_color_ramp(canvas, kwargs.get("ramp", [(0,0,0),(255,255,255)]))

    # --- Glow / Blur ---
    elif name == "bloom":
        return sh_bloom(canvas, kwargs.get("thr", 130))
    elif name == "edge_glow":
        return sh_edge_glow(canvas, kwargs.get("hue", 0.5))
    elif name == "soft_focus":
        return sh_soft_focus(canvas, kwargs.get("strength", 0.3))
    elif name == "radial_blur":
        return sh_radial_blur(canvas, kwargs.get("strength", 0.03))

    # --- Noise ---
    elif name == "grain":
        return sh_grain(canvas, int(kwargs.get("amt", 10) * (0.5 + rms * 0.8)))
    elif name == "static":
        return sh_static_noise(canvas, kwargs.get("density", 0.05), kwargs.get("color", True))

    # --- Lines / Patterns ---
    elif name == "scanlines":
        return sh_scanlines(canvas, kwargs.get("intensity", 0.08), kwargs.get("spacing", 3))
    elif name == "halftone":
        return sh_halftone(canvas, kwargs.get("dot_size", 6))

    # --- Tone ---
    elif name == "vignette":
        return sh_vignette(canvas, kwargs.get("s", 0.22))
    elif name == "contrast":
        return sh_contrast(canvas, kwargs.get("factor", 1.3))
    elif name == "gamma":
        return sh_gamma(canvas, kwargs.get("gamma", 1.5))
    elif name == "levels":
        return sh_levels(canvas,
            kwargs.get("black", 0), kwargs.get("white", 255), kwargs.get("midtone", 1.0))
    elif name == "brightness":
        return sh_brightness(canvas, kwargs.get("factor", 1.5))

    # --- Glitch / Data ---
    elif name == "glitch_bands":
        return sh_glitch_bands(canvas, f)
    elif name == "block_glitch":
        return sh_block_glitch(canvas, kwargs.get("n_blocks", 8), kwargs.get("max_size", 40))
    elif name == "pixel_sort":
        return sh_pixel_sort(canvas, kwargs.get("threshold", 100), kwargs.get("direction", "h"))
    elif name == "data_bend":
        return sh_data_bend(canvas, kwargs.get("offset", 1000), kwargs.get("chunk", 500))

    else:
        return canvas  # unknown shader — passthrough
```

### Audio-Reactive Shaders

Three shaders scale their parameters based on audio features:

| Shader | Reactive To | Effect |
|--------|------------|--------|
| `chromatic` | `bdecay` | `amt * (0.4 + bdecay * 0.8)` — aberration kicks on beats |
| `color_wobble` | `rms` | `amt * (0.5 + rms * 0.8)` — wobble intensity follows energy |
| `grain` | `rms` | `amt * (0.5 + rms * 0.8)` — grain rougher in loud sections |
| `glitch_bands` | `bdecay`, `sub` | Number of bands and displacement scale with beat energy |

To make any shader beat-reactive, scale its parameter in the dispatch: `base_val * (low + bd * range)`.

---

## Full Shader Catalog

### Geometry Shaders

| Shader | Key Params | Description |
|--------|-----------|-------------|
| `crt` | `strength=0.05` | CRT barrel distortion (cached remap) |
| `pixelate` | `block=4` | Reduce effective resolution |
| `wave_distort` | `freq, amp, axis` | Sinusoidal row/column displacement |
| `kaleidoscope` | `folds=6` | Radial symmetry via polar remapping |
| `mirror_h` | — | Horizontal mirror |
| `mirror_v` | — | Vertical mirror |
| `mirror_quad` | — | 4-fold mirror |
| `mirror_diag` | — | Diagonal mirror |

### Channel Manipulation

| Shader | Key Params | Description |
|--------|-----------|-------------|
| `chromatic` | `amt=3` | R/B channel horizontal shift (beat-reactive) |
| `channel_shift` | `r=(sx,sy), g, b` | Independent per-channel x,y shifting |
| `channel_swap` | `order=(2,1,0)` | Reorder RGB channels (BGR, GRB, etc.) |
| `rgb_split_radial` | `strength=5` | Chromatic aberration radiating from center |

### Color Manipulation

| Shader | Key Params | Description |
|--------|-----------|-------------|
| `invert` | — | Negate all colors |
| `posterize` | `levels=4` | Reduce color depth to N levels |
| `threshold` | `thr=128` | Binary black/white |
| `solarize` | `threshold=128` | Invert pixels above threshold |
| `hue_rotate` | `amount=0.1` | Rotate all hues by amount (0-1) |
| `saturation` | `factor=1.5` | Scale saturation (>1=more, <1=less) |
| `color_grade` | `tint=(r,g,b)` | Per-channel multiplier |
| `color_wobble` | `amt=0.3` | Time-varying per-channel sine modulation |
| `color_ramp` | `ramp=[(R,G,B),...]` | Map luminance to custom color gradient |

### Glow / Blur

| Shader | Key Params | Description |
|--------|-----------|-------------|
| `bloom` | `thr=130` | Bright area glow (4x downsample + box blur) |
| `edge_glow` | `hue=0.5` | Detect edges, add colored overlay |
| `soft_focus` | `strength=0.3` | Blend with blurred version |
| `radial_blur` | `strength=0.03` | Zoom blur from center outward |

### Noise / Grain

| Shader | Key Params | Description |
|--------|-----------|-------------|
| `grain` | `amt=10` | 2x-downsampled film grain (beat-reactive) |
| `static` | `density=0.05, color=True` | Random pixel noise (TV static) |

### Lines / Patterns

| Shader | Key Params | Description |
|--------|-----------|-------------|
| `scanlines` | `intensity=0.08, spacing=3` | Darken every Nth row |
| `halftone` | `dot_size=6` | Halftone dot pattern overlay |

### Tone

| Shader | Key Params | Description |
|--------|-----------|-------------|
| `vignette` | `s=0.22` | Edge darkening (cached distance field) |
| `contrast` | `factor=1.3` | Adjust contrast around midpoint 128 |
| `gamma` | `gamma=1.5` | Gamma correction (>1=brighter mids) |
| `levels` | `black, white, midtone` | Levels adjustment (Photoshop-style) |
| `brightness` | `factor=1.5` | Global brightness multiplier |

### Glitch / Data

| Shader | Key Params | Description |
|--------|-----------|-------------|
| `glitch_bands` | (uses `f`) | Beat-reactive horizontal row displacement |
| `block_glitch` | `n_blocks=8, max_size=40` | Random rectangular block displacement |
| `pixel_sort` | `threshold=100, direction="h"` | Sort pixels by brightness in rows/columns |
| `data_bend` | `offset, chunk` | Raw byte displacement (datamoshing) |

---

## Shader Implementations

Every shader function takes a canvas (`uint8 H,W,3`) and returns a canvas of the same shape. The naming convention is `sh_<name>`. Geometry shaders that build coordinate remap tables should **cache** them since the table only depends on resolution + parameters, not on frame content.

### Helpers

Shaders that manipulate hue/saturation need vectorized HSV conversion:

```python
def rgb2hsv(r, g, b):
    """Vectorized RGB (0-255 uint8) -> HSV (float32 0-1)."""
    rf = r.astype(np.float32) / 255.0
    gf = g.astype(np.float32) / 255.0
    bf = b.astype(np.float32) / 255.0
    cmax = np.maximum(np.maximum(rf, gf), bf)
    cmin = np.minimum(np.minimum(rf, gf), bf)
    delta = cmax - cmin + 1e-10
    h = np.zeros_like(rf)
    m = cmax == rf; h[m] = ((gf[m] - bf[m]) / delta[m]) % 6
    m = cmax == gf; h[m] = (bf[m] - rf[m]) / delta[m] + 2
    m = cmax == bf; h[m] = (rf[m] - gf[m]) / delta[m] + 4
    h = h / 6.0 % 1.0
    s = np.where(cmax > 0, delta / (cmax + 1e-10), 0)
    return h, s, cmax

def hsv2rgb(h, s, v):
    """Vectorized HSV->RGB. h,s,v are numpy float32 arrays."""
    h = h % 1.0
    c = v * s; x = c * (1 - np.abs((h * 6) % 2 - 1)); m = v - c
    r = np.zeros_like(h); g = np.zeros_like(h); b = np.zeros_like(h)
    mask = h < 1/6;            r[mask]=c[mask]; g[mask]=x[mask]
    mask = (h>=1/6)&(h<2/6);   r[mask]=x[mask]; g[mask]=c[mask]
    mask = (h>=2/6)&(h<3/6);   g[mask]=c[mask]; b[mask]=x[mask]
    mask = (h>=3/6)&(h<4/6);   g[mask]=x[mask]; b[mask]=c[mask]
    mask = (h>=4/6)&(h<5/6);   r[mask]=x[mask]; b[mask]=c[mask]
    mask = h >= 5/6;            r[mask]=c[mask]; b[mask]=x[mask]
    R = np.clip((r+m)*255, 0, 255).astype(np.uint8)
    G = np.clip((g+m)*255, 0, 255).astype(np.uint8)
    B = np.clip((b+m)*255, 0, 255).astype(np.uint8)
    return R, G, B

def mkc(R, G, B, rows, cols):
    """Stack R,G,B uint8 arrays into (rows,cols,3) canvas."""
    o = np.zeros((rows, cols, 3), dtype=np.uint8)
    o[:,:,0] = R; o[:,:,1] = G; o[:,:,2] = B
    return o
```

---

### Geometry Shaders

#### CRT Barrel Distortion
Cache the coordinate remap — it never changes per frame:
```python
_crt_cache = {}
def sh_crt(c, strength=0.05):
    k = (c.shape[0], c.shape[1], round(strength, 3))
    if k not in _crt_cache:
        h, w = c.shape[:2]; cy, cx = h/2, w/2
        Y = np.arange(h, dtype=np.float32)[:, None]
        X = np.arange(w, dtype=np.float32)[None, :]
        ny = (Y - cy) / cy; nx = (X - cx) / cx
        r2 = nx**2 + ny**2
        factor = 1 + strength * r2
        sx = np.clip((nx * factor * cx + cx), 0, w-1).astype(np.int32)
        sy = np.clip((ny * factor * cy + cy), 0, h-1).astype(np.int32)
        _crt_cache[k] = (sy, sx)
    sy, sx = _crt_cache[k]
    return c[sy, sx]
```

#### Pixelate
```python
def sh_pixelate(c, block=4):
    """Reduce effective resolution."""
    sm = c[::block, ::block]
    return np.repeat(np.repeat(sm, block, axis=0), block, axis=1)[:c.shape[0], :c.shape[1]]
```

#### Wave Distort
```python
def sh_wave_distort(c, t, freq=0.02, amp=8, axis="x"):
    """Sinusoidal row/column displacement. Uses time t for animation."""
    h, w = c.shape[:2]
    out = c.copy()
    if axis == "x":
        for y in range(h):
            shift = int(amp * math.sin(y * freq + t * 3))
            out[y] = np.roll(c[y], shift, axis=0)
    else:
        for x in range(w):
            shift = int(amp * math.sin(x * freq + t * 3))
            out[:, x] = np.roll(c[:, x], shift, axis=0)
    return out
```

#### Displacement Map
```python
def sh_displacement_map(c, dx_map, dy_map, strength=10):
    """Displace pixels using float32 displacement maps (same HxW as c).
    dx_map/dy_map: positive = shift right/down."""
    h, w = c.shape[:2]
    Y = np.arange(h)[:, None]; X = np.arange(w)[None, :]
    ny = np.clip((Y + (dy_map * strength).astype(int)), 0, h-1)
    nx = np.clip((X + (dx_map * strength).astype(int)), 0, w-1)
    return c[ny, nx]
```

#### Kaleidoscope
```python
def sh_kaleidoscope(c, folds=6):
    """Radial symmetry by polar coordinate remapping."""
    h, w = c.shape[:2]; cy, cx = h//2, w//2
    Y = np.arange(h, dtype=np.float32)[:, None] - cy
    X = np.arange(w, dtype=np.float32)[None, :] - cx
    angle = np.arctan2(Y, X)
    dist = np.sqrt(X**2 + Y**2)
    wedge = 2 * np.pi / folds
    folded_angle = np.abs((angle % wedge) - wedge/2)
    ny = np.clip((cy + dist * np.sin(folded_angle)).astype(int), 0, h-1)
    nx = np.clip((cx + dist * np.cos(folded_angle)).astype(int), 0, w-1)
    return c[ny, nx]
```

#### Mirror Variants
```python
def sh_mirror_h(c):
    """Horizontal mirror — left half reflected to right."""
    w = c.shape[1]; c[:, w//2:] = c[:, :w//2][:, ::-1]; return c

def sh_mirror_v(c):
    """Vertical mirror — top half reflected to bottom."""
    h = c.shape[0]; c[h//2:, :] = c[:h//2, :][::-1, :]; return c

def sh_mirror_quad(c):
    """4-fold mirror — top-left quadrant reflected to all four."""
    h, w = c.shape[:2]; hh, hw = h//2, w//2
    tl = c[:hh, :hw].copy()
    c[:hh, hw:hw+tl.shape[1]] = tl[:, ::-1]
    c[hh:hh+tl.shape[0], :hw] = tl[::-1, :]
    c[hh:hh+tl.shape[0], hw:hw+tl.shape[1]] = tl[::-1, ::-1]
    return c

def sh_mirror_diag(c):
    """Diagonal mirror — top-left triangle reflected."""
    h, w = c.shape[:2]
    for y in range(h):
        x_cut = int(w * y / h)
        if x_cut > 0 and x_cut < w:
            c[y, x_cut:] = c[y, :x_cut+1][::-1][:w-x_cut]
    return c
```

> **Note:** Mirror shaders mutate in-place. The dispatch function passes `canvas.copy()` to avoid corrupting the original.

---

### Channel Manipulation Shaders

#### Chromatic Aberration
```python
def sh_chromatic(c, amt=3):
    """R/B channel horizontal shift. Beat-reactive in dispatch (amt scaled by bdecay)."""
    if amt < 1: return c
    a = int(amt)
    o = c.copy()
    o[:, a:, 0] = c[:, :-a, 0]   # red shifts right
    o[:, :-a, 2] = c[:, a:, 2]   # blue shifts left
    return o
```

#### Channel Shift
```python
def sh_channel_shift(c, r_shift=(0,0), g_shift=(0,0), b_shift=(0,0)):
    """Independent per-channel x,y shifting."""
    o = c.copy()
    for ch_i, (sx, sy) in enumerate([r_shift, g_shift, b_shift]):
        if sx != 0: o[:,:,ch_i] = np.roll(c[:,:,ch_i], sx, axis=1)
        if sy != 0: o[:,:,ch_i] = np.roll(o[:,:,ch_i], sy, axis=0)
    return o
```

#### Channel Swap
```python
def sh_channel_swap(c, order=(2,1,0)):
    """Reorder RGB channels. (2,1,0)=BGR, (1,0,2)=GRB, etc."""
    return c[:, :, list(order)]
```

#### RGB Split Radial
```python
def sh_rgb_split_radial(c, strength=5):
    """Chromatic aberration radiating from center — stronger at edges."""
    h, w = c.shape[:2]; cy, cx = h//2, w//2
    Y = np.arange(h, dtype=np.float32)[:, None]
    X = np.arange(w, dtype=np.float32)[None, :]
    dist = np.sqrt((Y-cy)**2 + (X-cx)**2)
    max_dist = np.sqrt(cy**2 + cx**2)
    factor = dist / max_dist * strength
    dy = ((Y-cy) / (dist+1) * factor).astype(int)
    dx = ((X-cx) / (dist+1) * factor).astype(int)
    out = c.copy()
    ry = np.clip(Y.astype(int)+dy, 0, h-1); rx = np.clip(X.astype(int)+dx, 0, w-1)
    out[:,:,0] = c[ry, rx, 0]  # red shifts outward
    by = np.clip(Y.astype(int)-dy, 0, h-1); bx = np.clip(X.astype(int)-dx, 0, w-1)
    out[:,:,2] = c[by, bx, 2]  # blue shifts inward
    return out
```

---

### Color Manipulation Shaders

#### Invert
```python
def sh_invert(c):
    return 255 - c
```

#### Posterize
```python
def sh_posterize(c, levels=4):
    """Reduce color depth to N levels per channel."""
    step = 256.0 / levels
    return (np.floor(c.astype(np.float32) / step) * step).astype(np.uint8)
```

#### Threshold
```python
def sh_threshold(c, thr=128):
    """Binary black/white at threshold."""
    gray = c.astype(np.float32).mean(axis=2)
    out = np.zeros_like(c); out[gray > thr] = 255
    return out
```

#### Solarize
```python
def sh_solarize(c, threshold=128):
    """Invert pixels above threshold — classic darkroom effect."""
    o = c.copy(); mask = c > threshold; o[mask] = 255 - c[mask]
    return o
```

#### Hue Rotate
```python
def sh_hue_rotate(c, amount=0.1):
    """Rotate all hues by amount (0-1)."""
    h, s, v = rgb2hsv(c[:,:,0], c[:,:,1], c[:,:,2])
    h = (h + amount) % 1.0
    R, G, B = hsv2rgb(h, s, v)
    return mkc(R, G, B, c.shape[0], c.shape[1])
```

#### Saturation
```python
def sh_saturation(c, factor=1.5):
    """Adjust saturation. >1=more saturated, <1=desaturated."""
    h, s, v = rgb2hsv(c[:,:,0], c[:,:,1], c[:,:,2])
    s = np.clip(s * factor, 0, 1)
    R, G, B = hsv2rgb(h, s, v)
    return mkc(R, G, B, c.shape[0], c.shape[1])
```

#### Color Grade
```python
def sh_color_grade(c, tint):
    """Per-channel multiplier. tint=(r_mul, g_mul, b_mul)."""
    o = c.astype(np.float32)
    o[:,:,0] *= tint[0]; o[:,:,1] *= tint[1]; o[:,:,2] *= tint[2]
    return np.clip(o, 0, 255).astype(np.uint8)
```

#### Color Wobble
```python
def sh_color_wobble(c, t, amt=0.3):
    """Time-varying per-channel sine modulation. Audio-reactive in dispatch (amt scaled by rms)."""
    o = c.astype(np.float32)
    o[:,:,0] *= 1.0 + amt * math.sin(t * 5.0)
    o[:,:,1] *= 1.0 + amt * math.sin(t * 5.0 + 2.09)
    o[:,:,2] *= 1.0 + amt * math.sin(t * 5.0 + 4.19)
    return np.clip(o, 0, 255).astype(np.uint8)
```

#### Color Ramp
```python
def sh_color_r

... [Content truncated, total 50,364 chars] ...