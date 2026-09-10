# Effect Catalog

Effect building blocks that produce visual patterns. In v2, these are used **inside scene functions** that return a pixel canvas directly. The building blocks below operate on grid coordinate arrays and produce `(chars, colors)` or value/hue fields that the scene function renders to canvas via `_render_vf()`.

> **See also:** architecture.md · composition.md · scenes.md · shaders.md · troubleshooting.md

## Design Philosophy

Effects are the creative core. Don't copy these verbatim for every project -- use them as **building blocks** and **combine, modify, and invent** new ones. Every project should feel distinct.

Key principles:
- **Layer multiple effects** rather than using a single monolithic function
- **Parameterize everything** -- hue, speed, density, amplitude should all be arguments
- **React to features** -- audio/video features should modulate at least 2-3 parameters per effect
- **Vary per section** -- never use the same effect config for the entire video
- **Invent project-specific effects** -- the catalog below is a starting vocabulary, not a fixed set

---

## Background Fills

Every effect should start with a background. Never leave flat black.

### Animated Sine Field (General Purpose)
```python
def bg_sinefield(g, f, t, hue=0.6, bri=0.5, pal=PAL_DEFAULT,
                 freq=(0.13, 0.17, 0.07, 0.09), speed=(0.5, -0.4, -0.3, 0.2)):
    """Layered sine field. Adjust freq/speed tuples for different textures."""
    v1 = np.sin(g.cc*freq[0] + t*speed[0]) * np.sin(g.rr*freq[1] - t*speed[1]) * 0.5 + 0.5
    v2 = np.sin(g.cc*freq[2] - t*speed[2] + g.rr*freq[3]) * 0.4 + 0.5
    v3 = np.sin(g.dist_n*5 + t*0.2) * 0.3 + 0.4
    v4 = np.cos(g.angle*3 - t*0.6) * 0.15 + 0.5
    val = np.clip((v1*0.3 + v2*0.25 + v3*0.25 + v4*0.2) * bri * (0.6 + f["rms"]*0.6), 0.06, 1)
    mask = val > 0.03
    ch = val2char(val, mask, pal)
    h = np.full_like(val, hue) + f.get("cent", 0.5)*0.1 + val*0.08
    R, G, B = hsv2rgb(h, np.clip(0.35+f.get("flat",0.4)*0.4, 0, 1) * np.ones_like(val), val)
    return ch, mkc(R, G, B, g.rows, g.cols)
```

### Video-Source Background
```python
def bg_video(g, frame_rgb, pal=PAL_DEFAULT, brightness=0.5):
    small = np.array(Image.fromarray(frame_rgb).resize((g.cols, g.rows)))
    lum = np.mean(small, axis=2) / 255.0 * brightness
    mask = lum > 0.02
    ch = val2char(lum, mask, pal)
    co = np.clip(small * np.clip(lum[:,:,None]*1.5+0.3, 0.3, 1), 0, 255).astype(np.uint8)
    return ch, co
```

### Noise / Static Field
```python
def bg_noise(g, f, t, pal=PAL_BLOCKS, density=0.3, hue_drift=0.02):
    val = np.random.random((g.rows, g.cols)).astype(np.float32) * density * (0.5 + f["rms"]*0.5)
    val = np.clip(val, 0, 1); mask = val > 0.02
    ch = val2char(val, mask, pal)
    R, G, B = hsv2rgb(np.full_like(val, t*hue_drift % 1), np.full_like(val, 0.3), val)
    return ch, mkc(R, G, B, g.rows, g.cols)
```

### Perlin-Like Smooth Noise
```python
def bg_smooth_noise(g, f, t, hue=0.5, bri=0.5, pal=PAL_DOTS, octaves=3):
    """Layered sine approximation of Perlin noise. Cheap, smooth, organic."""
    val = np.zeros((g.rows, g.cols), dtype=np.float32)
    for i in range(octaves):
        freq = 0.05 * (2 ** i)
        amp = 0.5 / (i + 1)
        phase = t * (0.3 + i * 0.2)
        val += np.sin(g.cc * freq + phase) * np.cos(g.rr * freq * 0.7 - phase * 0.5) * amp
    val = np.clip(val * 0.5 + 0.5, 0, 1) * bri
    mask = val > 0.03
    ch = val2char(val, mask, pal)
    h = np.full_like(val, hue) + val * 0.1
    R, G, B = hsv2rgb(h, np.full_like(val, 0.5), val)
    return ch, mkc(R, G, B, g.rows, g.cols)
```

### Cellular / Voronoi Approximation
```python
def bg_cellular(g, f, t, n_centers=12, hue=0.5, bri=0.6, pal=PAL_BLOCKS):
    """Voronoi-like cells using distance to nearest of N moving centers."""
    rng = np.random.RandomState(42)  # deterministic centers
    cx = (rng.rand(n_centers) * g.cols).astype(np.float32)
    cy = (rng.rand(n_centers) * g.rows).astype(np.float32)
    # Animate centers
    cx_t = cx + np.sin(t * 0.5 + np.arange(n_centers) * 0.7) * 5
    cy_t = cy + np.cos(t * 0.4 + np.arange(n_centers) * 0.9) * 3
    # Min distance to any center
    min_d = np.full((g.rows, g.cols), 999.0, dtype=np.float32)
    for i in range(n_centers):
        d = np.sqrt((g.cc - cx_t[i])**2 + (g.rr - cy_t[i])**2)
        min_d = np.minimum(min_d, d)
    val = np.clip(1.0 - min_d / (g.cols * 0.3), 0, 1) * bri
    # Cell edges (where distance is near-equal between two centers)
    # ... second-nearest trick for edge highlighting
    mask = val > 0.03
    ch = val2char(val, mask, pal)
    R, G, B = hsv2rgb(np.full_like(val, hue) + min_d * 0.005, np.full_like(val, 0.5), val)
    return ch, mkc(R, G, B, g.rows, g.cols)
```

---

> **Note:** The v1 `eff_rings`, `eff_rays`, `eff_spiral`, `eff_glow`, `eff_tunnel`, `eff_vortex`, `eff_freq_waves`, `eff_interference`, `eff_aurora`, and `eff_ripple` functions are superseded by the `vf_*` value field generators below (used via `_render_vf()`). The `vf_*` versions integrate with the multi-grid composition pipeline and are preferred for all new scenes.

---

## Particle Systems

### General Pattern
All particle systems use persistent state via the `S` dict parameter:
```python
# S is the persistent state dict (same as r.S, passed explicitly)
if "px" not in S:
    S["px"]=[]; S["py"]=[]; S["vx"]=[]; S["vy"]=[]; S["life"]=[]; S["char"]=[]

# Emit new particles (on beat, continuously, or on trigger)
# Update: position += velocity, apply forces, decay life
# Draw: map to grid, set char/color based on life
# Cull: remove dead, cap total count
```

### Particle Character Sets

Don't hardcode particle chars. Choose per project/mood:

```python
# Energy / explosive
PART_ENERGY  = list("*+#@\u26a1\u2726\u2605\u2588\u2593")
PART_SPARK   = list("\u00b7\u2022\u25cf\u2605\u2736*+")
# Organic / natural
PART_LEAF    = list("\u2740\u2741\u2742\u2743\u273f\u2618\u2022")
PART_SNOW    = list("\u2744\u2745\u2746\u00b7\u2022*\u25cb")
PART_RAIN    = list("|\u2502\u2503\u2551/\\")
PART_BUBBLE  = list("\u25cb\u25ce\u25c9\u25cf\u2218\u2219\u00b0")
# Data / tech
PART_DATA    = list("01{}[]<>|/\\")
PART_HEX     = list("0123456789ABCDEF")
PART_BINARY  = list("01")
# Mystical
PART_RUNE    = list("\u16a0\u16a2\u16a6\u16b1\u16b7\u16c1\u16c7\u16d2\u16d6\u16da\u16de\u16df\u2726\u2605")
PART_ZODIAC  = list("\u2648\u2649\u264a\u264b\u264c\u264d\u264e\u264f\u2650\u2651\u2652\u2653")
# Minimal
PART_DOT     = list("\u00b7\u2022\u25cf")
PART_DASH    = list("-=~\u2500\u2550")
```

### Explosion (Beat-Triggered)
```python
def emit_explosion(S, f, center_r, center_c, char_set=PART_ENERGY, count_base=80):
    if f.get("beat", 0) > 0:
        for _ in range(int(count_base + f["rms"]*150)):
            ang = random.uniform(0, 2*math.pi)
            sp = random.uniform(1, 9) * (0.5 + f.get("sub_r", 0.3)*2)
            S["px"].append(float(center_c))
            S["py"].append(float(center_r))
            S["vx"].append(math.cos(ang)*sp*2.5)
            S["vy"].append(math.sin(ang)*sp)
            S["life"].append(1.0)
            S["char"].append(random.choice(char_set))
# Update: gravity on vy += 0.03, life -= 0.015
# Color: life * 255 for brightness, hue fade controlled by caller
```

### Rising Embers
```python
# Emit: sy = rows-1, vy = -random.uniform(1,5), vx = random.uniform(-1.5,1.5)
# Update: vx += random jitter * 0.3, life -= 0.01
# Cap at ~1500 particles
```

### Dissolving Cloud
```python
# Init: N=600 particles spread across screen
# Update: slow upward drift, fade life progressively
# life -= 0.002 * (1 + elapsed * 0.05)  # accelerating fade
```

### Starfield (3D Projection)
```python
# N stars with (sx, sy, sz) in normalized coords
# Move: sz -= speed (stars approach camera)
# Project: px = cx + sx/sz * cx, py = cy + sy/sz * cy
# Reset stars that pass camera (sz <= 0.01)
# Brightness = (1 - sz), draw streaks behind bright stars
```

### Orbit (Circular/Elliptical Motion)
```python
def emit_orbit(S, n=20, radius=15, speed=1.0, char_set=PART_DOT):
    """Particles orbiting a center point."""
    for i in range(n):
        angle = i * 2 * math.pi / n
        S["px"].append(0.0); S["py"].append(0.0)  # will be computed from angle
        S["vx"].append(angle)  # store angle as "vx" for orbit
        S["vy"].append(radius + random.uniform(-2, 2))  # store radius
        S["life"].append(1.0)
        S["char"].append(random.choice(char_set))
# Update: angle += speed * dt, px = cx + radius * cos(angle), py = cy + radius * sin(angle)
```

### Gravity Well
```python
# Particles attracted toward one or more gravity points
# Update: compute force vector toward each well, apply as acceleration
# Particles that reach well center respawn at edges
```

### Flocking / Boids

Emergent swarm behavior from three simple rules: separation, alignment, cohesion.

```python
def update_boids(S, g, f, n_boids=200, perception=8.0, max_speed=2.0,
                 sep_weight=1.5, ali_weight=1.0, coh_weight=1.0,
                 char_set=None):
    """Boids flocking simulation. Particles self-organize into organic groups.

    perception: how far each boid can see (grid cells)
    sep_weight: separation (avoid crowding) strength
    ali_weight: alignment (match neighbor velocity) strength
    coh_weight: cohesion (steer toward group center) strength
    """
    if char_set is None:
        char_set = list("·•●◦∘⬤")
    if "boid_x" not in S:
        rng = np.random.RandomState(42)
        S["boid_x"] = rng.uniform(0, g.cols, n_boids).astype(np.float32)
        S["boid_y"] = rng.uniform(0, g.rows, n_boids).astype(np.float32)
        S["boid_vx"] = (rng.random(n_boids).astype(np.float32) - 0.5) * max_speed
        S["boid_vy"] = (rng.random(n_boids).astype(np.float32) - 0.5) * max_speed
        S["boid_ch"] = [random.choice(char_set) for _ in range(n_boids)]

    bx = S["boid_x"]; by = S["boid_y"]
    bvx = S["boid_vx"]; bvy = S["boid_vy"]
    n = len(bx)

    # For each boid, compute steering forces
    ax = np.zeros(n, dtype=np.float32)
    ay = np.zeros(n, dtype=np.float32)

    # Spatial hash for efficient neighbor lookup
    cell_size = perception
    cells = {}
    for i in range(n):
        cx_i = int(bx[i] / cell_size)
        cy_i = int(by[i] / cell_size)
        key = (cx_i, cy_i)
        if key not in cells:
            cells[key] = []
        cells[key].append(i)

    for i in range(n):
        cx_i = int(bx[i] / cell_size)
        cy_i = int(by[i] / cell_size)
        sep_x, sep_y = 0.0, 0.0
        ali_x, ali_y = 0.0, 0.0
        coh_x, coh_y = 0.0, 0.0
        count = 0

        # Check neighboring cells
        for dcx in range(-1, 2):
            for dcy in range(-1, 2):
                for j in cells.get((cx_i + dcx, cy_i + dcy), []):
                    if j == i:
                        continue
                    dx = bx[j] - bx[i]
                    dy = by[j] - by[i]
                    dist = np.sqrt(dx * dx + dy * dy)
                    if dist < perception and dist > 0.01:
                        count += 1
                        # Separation: steer away from close neighbors
                        if dist < perception * 0.4:
                            sep_x -= dx / (dist * dist)
                            sep_y -= dy / (dist * dist)
                        # Alignment: match velocity
                        ali_x += bvx[j]
                        ali_y += bvy[j]
                        # Cohesion: steer toward center of group
                        coh_x += bx[j]
                        coh_y += by[j]

        if count > 0:
            # Normalize and weight
            ax[i] += sep_x * sep_weight
            ay[i] += sep_y * sep_weight
            ax[i] += (ali_x / count - bvx[i]) * ali_weight * 0.1
            ay[i] += (ali_y / count - bvy[i]) * ali_weight * 0.1
            ax[i] += (coh_x / count - bx[i]) * coh_weight * 0.01
            ay[i] += (coh_y / count - by[i]) * coh_weight * 0.01

    # Audio reactivity: bass pushes boids outward from center
    if f.get("bass", 0) > 0.5:
        cx_g, cy_g = g.cols / 2, g.rows / 2
        dx = bx - cx_g; dy = by - cy_g
        dist = np.sqrt(dx**2 + dy**2) + 1
        ax += (dx / dist) * f["bass"] * 2
        ay += (dy / dist) * f["bass"] * 2

    # Update velocity and position
    bvx += ax; bvy += ay
    # Clamp speed
    speed = np.sqrt(bvx**2 + bvy**2) + 1e-10
    over = speed > max_speed
    bvx[over] *= max_speed / speed[over]
    bvy[over] *= max_speed / speed[over]
    bx += bvx; by += bvy

    # Wrap at edges
    bx %= g.cols; by %= g.rows

    S["boid_x"] = bx; S["boid_y"] = by
    S["boid_vx"] = bvx; S["boid_vy"] = bvy

    # Draw
    ch = np.full((g.rows, g.cols), " ", dtype="U1")
    co = np.zeros((g.rows, g.cols, 3), dtype=np.uint8)
    for i in range(n):
        r, c = int(by[i]) % g.rows, int(bx[i]) % g.cols
        ch[r, c] = S["boid_ch"][i]
        spd = min(1.0, speed[i] / max_speed)
        R, G, B = hsv2rgb_scalar(spd * 0.3, 0.8, 0.5 + spd * 0.5)
        co[r, c] = (R, G, B)
    return ch, co
```

### Flow Field Particles

Particles that follow the gradient of a value field. Any `vf_*` function becomes a "river" that carries particles:

```python
def update_flow_particles(S, g, f, flow_field, n=500, speed=1.0,
                          life_drain=0.005, emit_rate=10,
                          char_set=None):
    """Particles steered by a value field gradient.

    flow_field: float32 (rows, cols) — the field particles follow.
                Particles flow from low to high values (uphill) or along
                the gradient direction.
    """
    if char_set is None:
        char_set = list("·•∘◦°⋅")
    if "fp_x" not in S:
        S["fp_x"] = []; S["fp_y"] = []; S["fp_vx"] = []; S["fp_vy"] = []
        S["fp_life"] = []; S["fp_ch"] = []

    # Emit new particles at random positions
    for _ in range(emit_rate):
        if len(S["fp_x"]) < n:
            S["fp_x"].append(random.uniform(0, g.cols - 1))
            S["fp_y"].append(random.uniform(0, g.rows - 1))
            S["fp_vx"].append(0.0); S["fp_vy"].append(0.0)
            S["fp_life"].append(1.0)
            S["fp_ch"].append(random.choice(char_set))

    # Compute gradient of flow field (central differences)
    pad = np.pad(flow_field, 1, mode="wrap")
    grad_x = (pad[1:-1, 2:] - pad[1:-1, :-2]) * 0.5
    grad_y = (pad[2:, 1:-1] - pad[:-2, 1:-1]) * 0.5

    # Update particles
    i = 0
    while i < len(S["fp_x"]):
        px, py = S["fp_x"][i], S["fp_y"][i]
        # Sample gradient at particle position
        gc = int(px) % g.cols; gr = int(py) % g.rows
        gx = grad_x[gr, gc]; gy = grad_y[gr, gc]
        # Steer velocity toward gradient direction
        S["fp_vx"][i] = S["fp_vx"][i] * 0.9 + gx * speed * 10
        S["fp_vy"][i] = S["fp_vy"][i] * 0.9 + gy * speed * 10
        S["fp_x"][i] += S["fp_vx"][i]
        S["fp_y"][i] += S["fp_vy"][i]
        S["fp_life"][i] -= life_drain

        if S["fp_life"][i] <= 0:
            for k in ("fp_x", "fp_y", "fp_vx", "fp_vy", "fp_life", "fp_ch"):
                S[k].pop(i)
        else:
            i += 1

    # Draw
    ch = np.full((g.rows, g.cols), " ", dtype="U1")
    co = np.zeros((g.rows, g.cols, 3), dtype=np.uint8)
    for i in range(len(S["fp_x"])):
        r = int(S["fp_y"][i]) % g.rows
        c = int(S["fp_x"][i]) % g.cols
        ch[r, c] = S["fp_ch"][i]
        v = S["fp_life"][i]
        co[r, c] = (int(v * 200), int(v * 180), int(v * 255))
    return ch, co
```

### Particle Trails

Draw fading lines between current and previous positions:

```python
def draw_particle_trails(S, g, trail_key="trails", max_trail=8, fade=0.7):
    """Add trails to any particle system. Call after updating positions.
    Stores previous positions in S[trail_key] and draws fading lines.

    Expects S to have 'px', 'py' lists (standard particle keys).
    max_trail: number of previous positions to remember
    fade: brightness multiplier per trail step (0.7 = 70% each step back)
    """
    if trail_key not in S:
        S[trail_key] = []

    # Store current positions
    current = list(zip(
        [int(y) for y in S.get("py", [])],
        [int(x) for x in S.get("px", [])]
    ))
    S[trail_key].append(current)
    if len(S[trail_key]) > max_trail:
        S[trail_key] = S[trail_key][-max_trail:]

    # Draw trails onto char/color arrays
    ch = np.full((g.rows, g.cols), " ", dtype="U1")
    co = np.zeros((g.rows, g.cols, 3), dtype=np.uint8)
    trail_chars = list("·∘◦°⋅.,'`")

    for age, positions in enumerate(reversed(S[trail_key])):
        bri = fade ** age
        if bri < 0.05:
            break
        ci = min(age, len(trail_chars) - 1)
        for r, c in positions:
            if 0 <= r < g.rows and 0 <= c < g.cols and ch[r, c] == " ":
                ch[r, c] = trail_chars[ci]
                v = int(bri * 180)
                co[r, c] = (v, v, int(v * 0.8))
    return ch, co
```

---

## Rain / Matrix Effects

### Column Rain (Vectorized)
```python
def eff_matrix_rain(g, f, t, S, hue=0.33, bri=0.6, pal=PAL_KATA,
                    speed_base=0.5, speed_beat=3.0):
    """Vectorized matrix rain. S dict persists column positions."""
    if "ry" not in S or len(S["ry"]) != g.cols:
        S["ry"] = np.random.uniform(-g.rows, g.rows, g.cols).astype(np.float32)
        S["rsp"] = np.random.uniform(0.3, 2.0, g.cols).astype(np.float32)
        S["rln"] = np.random.randint(8, 40, g.cols)
        S["rch"] = np.random.randint(0, len(pal), (g.rows, g.cols))  # pre-assign chars

    speed_mult = speed_base + f.get("bass", 0.3)*speed_beat + f.get("sub_r", 0.3)*3
    if f.get("beat", 0) > 0: speed_mult *= 2.5
    S["ry"] += S["rsp"] * speed_mult

    # Reset columns that fall past bottom
    rst = (S["ry"] - S["rln"]) > g.rows
    S["ry"][rst] = np.random.uniform(-25, -2, rst.sum())

    # Vectorized draw using fancy indexing
    ch = np.full((g.rows, g.cols), " ", dtype="U1")
    co = np.zeros((g.rows, g.cols, 3), dtype=np.uint8)
    heads = S["ry"].astype(int)
    for c in range(g.cols):
        head = heads[c]
        trail_len = S["rln"][c]
        for i in range(trail_len):
            row = head - i
            if 0 <= row < g.rows:
                fade = 1.0 - i / trail_len
                ci = S["rch"][row, c] % len(pal)
                ch[row, c] = pal[ci]
                v = fade * bri * 255
                if i == 0:  # head is bright white-ish
                    co[row, c] = (int(v*0.9), int(min(255, v*1.1)), int(v*0.9))
                else:
                    R, G, B = hsv2rgb_single(hue, 0.7, fade * bri)
                    co[row, c] = (R, G, B)
    return ch, co, S
```

---

## Glitch / Data Effects

### Horizontal Band Displacement
```python
def eff_glitch_displace(ch, co, f, intensity=1.0):
    n_bands = int(8 + f.get("flux", 0.3)*25 + f.get("bdecay", 0)*15) * intensity
    for _ in range(int(n_bands)):
        y = random.randint(0, ch.shape[0]-1)
        h = random.randint(1, int(3 + f.get("sub", 0.3)*8))
        shift = int((random.random()-0.5) * f.get("rms", 0.3)*40 + f.get("bdecay", 0)*20*(random.random()-0.5))
        if shift != 0:
            for row in range(h):
                rr = y + row
                if 0 <= rr < ch.shape[0]:
                    ch[rr] = np.roll(ch[rr], shift)
                    co[rr] = np.roll(co[rr], shift, axis=0)
    return ch, co
```

### Block Corruption
```python
def eff_block_corrupt(ch, co, f, char_pool=None, count_base=20):
    if char_pool is None:
        char_pool = list(PAL_BLOCKS[4:] + PAL_KATA[2:8])
    for _ in range(int(count_base + f.get("flux", 0.3)*60 + f.get("bdecay", 0)*40)):
        bx = random.randint(0, max(1, ch.shape[1]-6))
        by = random.randint(0, max(1, ch.shape[0]-4))
        bw, bh = random.randint(2,6), random.randint(1,4)
        block_char = random.choice(char_pool)
        # Fill rectangle with single char and random color
        for r in range(bh):
            for c in range(bw):
                rr, cc = by+r, bx+c
                if 0 <= rr < ch.shape[0] and 0 <= cc < ch.shape[1]:
                    ch[rr, cc] = block_char
                    co[rr, cc] = (random.randint(100,255), random.randint(0,100), random.randint(0,80))
    return ch, co
```

### Scan Bars (Vertical)
```python
def eff_scanbars(ch, co, f, t, n_base=4, chars="|\u2551|!1l"):
    for bi in range(int(n_base + f.get("himid_r", 0.3)*12)):
        sx = int((t*50*(1+bi*0.3) + bi*37) % ch.shape[1])
        for rr in range(ch.shape[0]):
            if random.random() < 0.7:
                ch[rr, sx] = random.choice(chars)
    return ch, co
```

### Error Messages
```python
# Parameterize the error vocabulary per project:
ERRORS_TECH = ["SEGFAULT","0xDEADBEEF","BUFFER_OVERRUN","PANIC!","NULL_PTR",
               "CORRUPT","SIGSEGV","ERR_OVERFLOW","STACK_SMASH","BAD_ALLOC"]
ERRORS_COSMIC = ["VOID_BREACH","ENTROPY_MAX","SINGULARITY","DIMENSION_FAULT",
                 "REALITY_ERR","TIME_PARADOX","DARK_MATTER_LEAK","QUANTUM_DECOHERE"]
ERRORS_ORGANIC = ["CELL_DIVISION_ERR","DNA_MISMATCH","MUTATION_OVERFLOW",
                  "NEURAL_DEADLOCK","SYNAPSE_TIMEOUT","MEMBRANE_BREACH"]
```

### Hex Data Stream
```python
hex_str = "".join(random.choice("0123456789ABCDEF") for _ in range(random.randint(8,20)))
stamp(ch, co, hex_str, rand_row, rand_col, (0, 160, 80))
```

---

## Spectrum / Visualization

### Mirrored Spectrum Bars
```python
def eff_spectrum(g, f, t, n_bars=64, pal=PAL_BLOCKS, mirror=True):
    bar_w = max(1, g.cols // n_bars); mid = g.rows // 2
    band_vals = np.array([f.get("sub",0.3), f.get("bass",0.3), f.get("lomid",0.3),
                          f.get("mid",0.3), f.get("himid",0.3), f.get("hi",0.3)])
    ch = np.full((g.rows, g.cols), " ", dtype="U1")
    co = np.zeros((g.rows, g.cols, 3), dtype=np.uint8)
    for b in range(n_bars):
        frac = b / n_bars
        fi = frac * 5; lo_i = int(fi); hi_i = min(lo_i+1, 5)
        bval = min(1, (band_vals[lo_i]*(1-fi%1) + band_vals[hi_i]*(fi%1)) * 1.8)
        height = int(bval * (g.rows//2 - 2))
        for dy in range(height):
            hue = (f.get("cent",0.5)*0.3 + frac*0.3 + dy/max(height,1)*0.15) % 1.0
            ci = pal[min(int(dy/max(height,1)*len(pal)*0.7+len(pal)*0.2), len(pal)-1)]
            for dc in range(bar_w - (1 if bar_w > 2 else 0)):
                cc = b*bar_w + dc
                if 0 <= cc < g.cols:
                    rows_to_draw = [mid - dy, mid + dy] if mirror else [g.rows - 1 - dy]
                    for row in rows_to_draw:
                        if 0 <= row < g.rows:
                            ch[row, cc] = ci
                            co[row, cc] = hsv_to_rgb_single(hue, 0.85, 0.5+dy/max(height,1)*0.5)
    return ch, co
```

### Waveform
```python
def eff_waveform(g, f, t, row_offset=-5, hue=0.1):
    ch = np.full((g.rows, g.cols), " ", dtype="U1")
    co = np.zeros((g.rows, g.cols, 3), dtype=np.uint8)
    for c in range(g.cols):
        wv = (math.sin(c*0.15+t*5)*f.get("bass",0.3)*0.5
            + math.sin(c*0.3+t*8)*f.get("mid",0.3)*0.3
            + math.sin(c*0.6+t*12)*f.get("hi",0.3)*0.15)
        wr = g.rows + row_offset + int(wv * 4)
        if 0 <= wr < g.rows:
            ch[wr, c] = "~"
            v = int(120 + f.get("rms",0.3)*135)
            co[wr, c] = [v, int(v*0.7), int(v*0.4)]
    return ch, co
```

---

## Fire / Lava

### Fire Columns
```python
def eff_fire(g, f, t, n_base=20, hue_base=0.02, hue_range=0.12, pal=PAL_BLOCKS):
    n_cols = int(n_base + f.get("bass",0.3)*30 + f.get("sub_r",0.3)*20)
    ch = np.full((g.rows, g.cols), " ", dtype="U1")
    co = np.zeros((g.rows, g.cols, 3), dtype=np.uint8)
    for fi in range(n_cols):
        fx_c = int((fi*g.cols/n_cols + np.sin(t*2+fi*0.7)*3) % g.cols)
        height = int((f.get("bass",0.3)*0.4 + f.get("sub_r",0.3)*0.3 + f.get("rms",0.3)*0.3) * g.rows * 0.7)
        for dy in range(min(height, g.rows)):
            fr = g.rows - 1 - dy
            frac = dy / max(height, 1)
            bri = max(0.1, (1 - frac*0.6) * (0.5 + f.get("rms",0.3)*0.5))
            hue = hue_base + frac * hue_range
            ci = "\u2588" if frac<0.2 else ("\u2593" if frac<0.4 else ("\u2592" if frac<0.6 else "\u2591"))
            ch[fr, fx_c] = ci
            R, G, B = hsv2rgb_single(hue, 0.9, bri)
            co[fr, fx_c] = (R, G, B)
    return ch, co
```

### Ice / Cold Fire (same structure, different hue range)
```python
# hue_base=0.55, hue_range=0.15 -- blue to cyan
# Lower intensity, slower movement
```

---

## Text Overlays

### Scrolling Ticker
```python
def eff_ticker(ch, co, t, text, row, speed=15, color=(80, 100, 140)):
    off = int(t * speed) % max(len(text), 1)
    doubled = text + "   " + text
    stamp(ch, co, doubled[off:off+ch.shape[1]], row, 0, color)
```

### Beat-Triggered Words
```python
def eff_beat_words(ch, co, f, words, row_center=None, color=(255,240,220)):
    if f.get("beat", 0) > 0:
        w = random.choice(words)
        r = (row_center or ch.shape[0]//2) + rando

... [Content truncated, total 72,821 chars] ...