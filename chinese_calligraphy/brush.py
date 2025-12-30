# chinese_calligraphy/brush.py

# 【繁】筆觸與字形變異：列級慣性漂移 + 字級微抖 + 上下文微變異 + 「之」三態模型
# [EN] Brush & glyph variation: column inertial drift + micro jitter + contextual variation + 3-state model for '之'

from __future__ import annotations

import random
from dataclasses import dataclass, field

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

from .types import Color, Point, VariantTemplate
from .utils import NoiseGenerator, clamp_int


@dataclass
class Brush:
    # =========================
    # 【隨機性 / Randomness】
    # =========================
    seed: int | None = None

    # =========================
    # 【高頻字級抖動 / High-frequency char jitter】
    # =========================
    char_jitter: tuple[int, int] = (0, 0)  # (jx, jy)

    # =========================
    # 【段級漂移 / Segment drift】
    # =========================
    segment_drift: tuple[int, int] = (0, 0)  # (sx, sy)

    # =========================
    # 【列級慣性漂移 / Column inertial drift (random walk)】
    # =========================
    col_drift_step: tuple[int, int] = (0, 0)  # per-column step range (sx, sy)
    col_drift_max: tuple[int, int] = (0, 0)  # clamp max drift (mx, my)
    col_drift_damping: float = 0.85  # damping < 1.0

    # =========================
    # 【一般字微變異 / General glyph micro-variation】
    # =========================
    var_rotate_deg: float = 0.0  # ± degrees
    var_shear_x: float = 0.0  # ± shear coefficient (x)
    var_scale: float = 0.0  # ± relative scale, e.g. 0.03 => [0.97, 1.03]

    # =========================
    # 【「之」三態概率模型 / 3-state model for '之'】
    # =========================
    zhi_state_probs: tuple[float, float, float] = (0.34, 0.40, 0.26)  # (stable, flow, vertical)
    zhi_segment_stickiness: float = 0.10  # 0~1 (higher => more sticky)
    zhi_pos_weight: float = 0.24  # 0~0.5 recommended
    zhi_mirror_prob: float = 0.68  # flip sign of rot/shear with this prob

    # 「之」模板庫 / Template banks for '之'
    zhi_templates: dict[str, list[VariantTemplate]] = field(
        default_factory=lambda: {
            "stable": [
                # base_rot, base_shear, base_scale, base_anis_y, amp_rot, amp_shear, amp_scale, amp_anis_y
                (0.0, 0.00, 1.00, 1.00, 0.9, 0.025, 0.020, 0.030),
                (0.3, -0.02, 0.99, 0.97, 1.0, 0.030, 0.020, 0.035),
                (-0.4, 0.03, 1.01, 0.95, 1.1, 0.030, 0.020, 0.040),
                (0.1, 0.01, 0.98, 1.03, 1.0, 0.025, 0.025, 0.040),
            ],
            "flow": [
                (-0.6, 0.06, 1.02, 1.02, 1.6, 0.060, 0.030, 0.050),
                (0.7, -0.06, 0.99, 0.98, 1.7, 0.060, 0.030, 0.055),
                (-0.4, 0.05, 1.04, 0.96, 1.4, 0.055, 0.035, 0.050),
                (0.5, -0.05, 0.97, 1.05, 1.5, 0.055, 0.035, 0.055),
                (0.3, 0.04, 1.01, 1.00, 1.4, 0.055, 0.030, 0.050),
            ],
            "vertical": [
                (-0.6, 0.05, 1.00, 1.10, 1.3, 0.040, 0.025, 0.060),
                (0.7, -0.06, 0.98, 1.14, 1.4, 0.045, 0.025, 0.070),
                (0.1, 0.02, 1.01, 1.18, 1.1, 0.035, 0.020, 0.080),
                (-0.3, 0.03, 0.99, 1.22, 1.2, 0.040, 0.020, 0.085),
                (0.4, -0.02, 1.02, 1.12, 1.2, 0.035, 0.025, 0.070),
            ],
        }
    )

    # 段內緩存：段內家族相 / Per-segment cache: family resemblance within segment
    _zhi_cache: dict[int, tuple[str, int]] = field(default_factory=dict)  # seg_idx -> (state, template_idx)

    # 段內統計：shear 去偏 / Per-segment stats for shear de-bias
    _zhi_seg_shear_sum: dict[int, float] = field(default_factory=dict)
    _zhi_seg_shear_cnt: dict[int, int] = field(default_factory=dict)

    # 噪聲生成器 / Noise Generator
    _noise_gen: NoiseGenerator = field(init=False)

    def __post_init__(self) -> None:
        # Initialize noise generator with a derived seed
        # Use a fixed default if seed is None (though usually provided)
        s = self.seed if self.seed is not None else 42
        self._noise_gen = NoiseGenerator(seed=s)

    # =========================
    # 【隨機源 / RNG】
    # =========================
    def rng(self) -> random.Random:
        # 【繁】可復現隨機源
        # [EN] Reproducible RNG
        return random.Random(self.seed)

    # =========================
    # 【基本抖動 / Basic jitter】
    # =========================
    @staticmethod
    def _jitter_point(p: Point, r: random.Random, j: tuple[int, int]) -> Point:
        jx, jy = j
        if jx == 0 and jy == 0:
            return p
        return (p[0] + r.randint(-jx, jx), p[1] + r.randint(-jy, jy))

    def jitter_point_basic(self, p: Point, r: random.Random) -> Point:
        # 【繁】基礎字級抖動：僅做高頻微抖，不涉及慣性或變形
        # [EN] Basic char-level jitter only (no inertia or deformation)
        return self._jitter_point(p, r, self.char_jitter)

    # =========================
    # 【段級 / Segment drift】
    # =========================
    def begin_segment(self, r: random.Random) -> tuple[int, int]:
        # 【繁】段起：抽取段級偏移
        # [EN] Segment start: sample segment-level drift
        sx = r.randint(-self.segment_drift[0], self.segment_drift[0]) if self.segment_drift[0] else 0
        sy = r.randint(-self.segment_drift[1], self.segment_drift[1]) if self.segment_drift[1] else 0
        return (sx, sy)

    # =========================
    # 【列級慣性 / Column inertial drift】
    # =========================
    def init_col_state(self) -> tuple[float, float]:
        # 【繁】列漂移狀態初始化
        # [EN] Initialize column drift state
        return (0.0, 0.0)

    def step_col_state(self, r: random.Random, state: tuple[float, float]) -> tuple[float, float]:
        # 【繁】列級 random walk + 阻尼 + 截斷
        # [EN] Column random-walk with damping and clamping
        dx, dy = state
        sx, sy = self.col_drift_step

        if sx:
            dx = self.col_drift_damping * dx + r.randint(-sx, sx)
        if sy:
            dy = self.col_drift_damping * dy + r.randint(-sy, sy)

        mx, my = self.col_drift_max
        if mx:
            dx = float(clamp_int(int(round(dx)), -mx, mx))
        else:
            dx = float(int(round(dx)))
        if my:
            dy = float(clamp_int(int(round(dy)), -my, my))
        else:
            dy = float(int(round(dy)))

        return (dx, dy)

    # =========================
    # 【一般字微變異 / General glyph micro-variation params】
    # =========================
    def glyph_transform_params(
        self,
        r: random.Random,
        ch: str,
        prev_ch: str | None,
        next_ch: str | None,
        seg_idx: int,
        col_idx: int,
        row_idx: int,
    ) -> tuple[float, float, float]:
        # 【繁】依上下文生成微變異參數：rot / shear_x / scale
        # [EN] Contextual micro-variation params: rot / shear_x / scale

        # 段內/列內：幅度更小；跨列：稍大
        # Within-column smaller, across columns slightly larger
        col_factor = 0.6
        row_factor = 0.4

        # 列首（前兩字）更收斂，避免顫
        # Reduce at the top of a column to avoid jittery feel
        boundary_factor = 0.7 if (row_idx < 2) else 1.0

        # 連字（如 之之）收斂，避免太花
        # Repeated neighbor reduces amplitude
        repeat_factor = 0.65 if (prev_ch == ch or next_ch == ch) else 1.0

        amp = boundary_factor * repeat_factor

        rot = 0.0
        if self.var_rotate_deg:
            rot = r.uniform(-self.var_rotate_deg, self.var_rotate_deg) * amp * (col_factor + row_factor)

        shear = 0.0
        if self.var_shear_x:
            shear = r.uniform(-self.var_shear_x, self.var_shear_x) * amp * (col_factor + row_factor)

        scale = 1.0
        if self.var_scale:
            scale = 1.0 + r.uniform(-self.var_scale, self.var_scale) * amp * (0.5 + 0.5 * col_factor)

        return rot, shear, scale

    # =========================
    # 【「之」三態 / 3-state model for '之'】
    # =========================
    def _weighted_choice3(self, r: random.Random, probs: tuple[float, float, float]) -> int:
        # 【繁】按概率選 0/1/2
        # [EN] Weighted choice among 0/1/2
        x = r.random()
        a, b, c = probs
        if x < a:
            return 0
        if x < a + b:
            return 1
        return 2

    def _state_probs_with_position(self, col_pos_ratio: float) -> tuple[float, float, float]:
        """
        col_pos_ratio: 0 at segment start, 1 at segment end
        """
        s, f, v = self.zhi_state_probs

        # 【繁】列首更穩、列中更放、列尾略縱
        # [EN] Start stable, middle freer (flow), end slightly more vertical
        w = self.zhi_pos_weight
        stable_bias = (1.0 - col_pos_ratio) * w
        flow_bias = (1.0 - abs(col_pos_ratio - 0.5) * 2.0) * w
        vert_bias = col_pos_ratio * w * 0.8

        s2 = max(0.01, s + stable_bias - 0.3 * vert_bias)
        f2 = max(0.01, f + flow_bias)
        v2 = max(0.01, v + vert_bias - 0.3 * stable_bias)

        z = s2 + f2 + v2
        return (s2 / z, f2 / z, v2 / z)

    def pick_zhi_variant(self, r: random.Random, seg_idx: int, col_pos_ratio: float) -> tuple[str, VariantTemplate]:
        # 【繁】先選態，再選模板；段內可黏性（stickiness）
        # [EN] Pick state then template, optionally sticky within segment
        if (seg_idx in self._zhi_cache) and (r.random() < self.zhi_segment_stickiness):
            state, tidx = self._zhi_cache[seg_idx]
        else:
            probs = self._state_probs_with_position(col_pos_ratio)
            state_idx = self._weighted_choice3(r, probs)
            state = ("stable", "flow", "vertical")[state_idx]
            tidx = r.randrange(len(self.zhi_templates[state]))
            self._zhi_cache[seg_idx] = (state, tidx)

        tpl = self.zhi_templates[state][tidx]
        return state, tpl

    def sample_from_template(self, r: random.Random, tpl: VariantTemplate) -> tuple[float, float, float, float]:
        # 【繁】模板基準 + 連續擾動（幅度由模板指定）
        # [EN] Template base + continuous noise (amplitudes from template)
        base_rot, base_shear, base_scale, base_anis, amp_rot, amp_sh, amp_sc, amp_an = tpl

        rot = base_rot + r.uniform(-amp_rot, amp_rot)
        shear_x = base_shear + r.uniform(-amp_sh, amp_sh)

        # scale / anis_y 使用乘法擾動更自然
        scale = base_scale * (1.0 + r.uniform(-amp_sc, amp_sc))
        anis_y = base_anis * (1.0 + r.uniform(-amp_an, amp_an))

        return rot, shear_x, scale, anis_y

    def balance_zhi_params(self, r: random.Random, seg_idx: int, rot: float, shear_x: float) -> tuple[float, float]:
        # 【繁】鏡像 + 段內 shear 去偏（讓均值趨近 0）
        # [EN] Mirroring + per-segment shear de-bias (keep mean near 0)

        # 1) mirror
        if r.random() < self.zhi_mirror_prob:
            rot = -rot
            shear_x = -shear_x

        # 2) de-bias shear mean in segment
        s = self._zhi_seg_shear_sum.get(seg_idx, 0.0)
        c = self._zhi_seg_shear_cnt.get(seg_idx, 0)
        mean = (s / c) if c > 0 else 0.0

        k = 0.82  # stronger correction to remove one-sided bias
        shear_x = shear_x - k * mean

        self._zhi_seg_shear_sum[seg_idx] = s + shear_x
        self._zhi_seg_shear_cnt[seg_idx] = c + 1

        return rot, shear_x

    # =========================
    # 【貼字渲染 / Patch-based glyph rendering】
    # =========================
    # =========================
    # 【貼字渲染 / Patch-based glyph rendering】
    # =========================
    def draw_char(
        self,
        base_img: Image.Image,
        draw: ImageDraw.ImageDraw,
        p: Point,
        ch: str,
        font: ImageFont.FreeTypeFont,
        fill: Color,
        r: random.Random,
        rot: float,
        shear_x: float,
        scale: float,
        anis_y: float = 1.0,
        ink_dryness: float = 0.0,
        blur_sigma: float = 0.0,
    ) -> None:
        # 【繁】物理模擬渲染管線：Raster -> Transform -> Erode -> Noise -> Composite
        # [EN] Physical simulation pipeline: Raster -> Transform -> Erode -> Noise -> Composite

        # 1) Patch size estimation
        fs = getattr(font, "size", 100)
        # Increase padding for transformations
        pad = max(20, fs // 2)
        w = fs * 2 + pad * 2
        h = fs * 2 + pad * 2

        # 2) High-res rasterization (2x super-sampling for better morphology)
        super_scale = 2
        sw, sh = w * super_scale, h * super_scale
        
        # Draw white text on black background for mask processing
        mask_img = Image.new("L", (sw, sh), 0)
        md = ImageDraw.Draw(mask_img)
        
        # Centered drawing
        cx, cy = sw // 2, sh // 2
        # Use larger font for super-sampling
        # Note: loading font repeatedly is slow, so we scale the font object if possible
        # Or just scale the coordinate system if font is vector. 
        # PIL font size change requires reloading.
        # Efficient hack: draw at normal size then scale up? No, jagged edges.
        # Better: just use font.font_variant(size=fs*super_scale) if possible?
        # Standard FreeTypeFont allows reloading size.
        # For performance/simplicity in this step, let's try to just load the larger font
        # if readily available, OR just draw at normal size and scale up (blurrier but acceptable for ink).
        # Let's try drawing at normal size * super_scale?
        # Actually, let's stick to 1x rasterization if font reloading is expensive, 
        # but 2x is much better for erosion quality.
        # To avoid IO, we might just scale the vectors. but PIL doesn't expose that easily.
        # We will fallback to 1x raster for now to be safe on perf, 
        # but use a larger canvas.
        
        # WAIT: font object is passed in. Cloning it with new size implies IO.
        # Let's trust the user passed a sizeable font or accept 1x resolution.
        # For "Living Ink", texture detail > sharp vector edges.
        # So we draw at 1x, then upsample if needed for noise interaction?
        # Or just work at 1x.
        # Let's stick to working at provided resolution `fs` but on a padded canvas.
        
        mask_img_1x = Image.new("L", (w, h), 0)
        md_1x = ImageDraw.Draw(mask_img_1x)
        md_1x.text((w // 2 - fs // 2, h // 2 - fs // 2), ch, font=font, fill=255)
        
        # 3) Apply geometric transforms (Shear / Scale / Rotate) on the MASK
        #    This is generic PIL stuff.
        patch = mask_img_1x
        
        # Shear
        if shear_x != 0.0:
            a, b, c = 1.0, shear_x, 0.0
            d, e, f = 0.0, 1.0, 0.0
            patch = patch.transform(
                patch.size,
                Image.Transform.AFFINE,
                (a, b, c, d, e, f),
                resample=Image.Resampling.BICUBIC,
            )

        # Scale + Anis
        if scale != 1.0 or anis_y != 1.0:
            sx = scale
            sy = scale * anis_y
            nw = max(1, int(round(w * sx)))
            nh = max(1, int(round(h * sy)))
            scaled = patch.resize((nw, nh), resample=Image.Resampling.BICUBIC)
            patch2 = Image.new("L", (w, h), 0)
            patch2.paste(scaled, ((w - nw) // 2, (h - nh) // 2))
            patch = patch2

        # Rotate
        if rot != 0.0:
            patch = patch.rotate(rot, resample=Image.Resampling.BICUBIC, expand=False)
            
        # 4) Physical Simulation (Erosion / Dryness)
        # Only apply if we have dryness > 0.0, else standard compositing
        if ink_dryness > 0.001:
            arr = np.array(patch)
            
            # Generate generic noise for this patch
            # We use a deterministic seed per char based on position or just random?
            # self.rng() is generic. We can use a fresh random int for noise seed.
            param_seed = r.randint(0, 100000)
            
            # High-frequency fiber noise
            fiber = self._noise_gen.generate_fiber_texture(w, h)
            # Roll it randomly to avoid repetitive patterns if generator is deterministic
            roll_x = param_seed % w
            roll_y = (param_seed // w) % h
            fiber = np.roll(fiber, (roll_y, roll_x), axis=(0, 1))
            
            # Threshold for erosion: Higher dryness => easier to erode
            # We want to erode pixels where (fiber_val < threshold)
            # Or formatted: output = input AND (fiber > dryness)
            # "Erosion" usually shrinks the shape. 
            # Digital "Dry brush" is effectively a mask based on texture.
            
            # Map [0, 255] to [0.0, 1.0]
            alpha_f = arr.astype(float) / 255.0
            
            # Modulate alpha by fiber noise
            # dryness 0.1 => retain 90%. dryness 0.9 => retain 10%
            # We use a sigmoid-ish contrast curve for the fiber mask
            limit = 1.0 - (ink_dryness * 0.8) # keep at least some
            
            # Mask out areas where fiber texture is "low" (valleys in paper)
            # If ink is dry, it only touches peaks (high values).
            # So we keep pixels where fiber > (dryness_threshold)
            
            # Dynamic thresholding based on original alpha (so text core is preserved more than edges?)
            # Actually flying white cuts through the stroke.
            
            # Simple interaction model: 
            # Result = Original * SmoothStep(fiber, dryness, dryness + 0.2)
            
            # Normalized dryness threshold
            thresh = ink_dryness * 0.7  # Scale to avoid empty characters
            
            # Soft mask from noise
            mask_d = np.clip((fiber - thresh) * 5.0, 0.0, 1.0)
            
            # 【繁】核心保護邏輯：計算距離變換，保護筆畫內部不被低干枯度的噪聲侵蝕
            # [EN] Core protection: use distance transform to prevent noise erosion in stroke core at low dryness
            
            # 1. Calculate distance from background
            # We treat standard alpha > 0.1 as "inside"
            dist = ndimage.distance_transform_edt(alpha_f > 0.1)
            
            # 2. Define protection factor
            # "Wet" ink (low dryness) flows to fill the core -> high protection
            # "Dry" ink (high dryness) allows streaks -> low protection
            # Transition: protect pixels > 1.5px from edge, fade out by 3.5px
            core_factor = np.clip((dist - 1.5) / 2.0, 0.0, 1.0)
            
            # 3. Modulate protection by dryness
            # If dryness is low (e.g. 0.01), we want near 100% protection in core.
            # If dryness is high (e.g. 0.9), we want less protection (allow flying white).
            # Let's say protection decays as dryness increases.
            # solidity = core_factor * (1.0 - dryness)^k
            solidity = core_factor * (1.0 - ink_dryness * 0.8)
            
            # 4. Blend noise mask with solid core
            # effective_mask = mask_d * (1 - solidity) + 1.0 * solidity
            #                = mask_d - mask_d * solidity + solidity
            effective_mask = mask_d + (1.0 - mask_d) * solidity
            
            # Apply to alpha
            final_alpha = alpha_f * effective_mask
            
            # Erosion on edges to make them rough?
            # We can threshold the final alpha
            final_alpha = np.clip(final_alpha * 255.0, 0, 255).astype(np.uint8)
            patch = Image.fromarray(final_alpha, mode="L")
        
        # 4.5) Diffusion / Blur (Halo)
        # Apply gaussian blur if sigma > 0
        if blur_sigma > 0.01:
            # Need to convert to numpy if not already (dryness might have skipped step 4)
            if not isinstance(patch, np.ndarray):
                # Recast only if we skipped the dryness block
                # but wait, patch is PIL Image here (either from step 3 or step 4)
                pass 
            
            # Simple way: use PIL gaussian blur or scipy
            # Scipy is better for exact float sigma control
            arr = np.array(patch)
            
            # Distance transform to keep core darker? 
            # Or just simple gaussian blur for halo.
            # Real ink diffusion keeps the center dark (carbon particles) and water spreads out (lighter).
            # Simple gaussian blurs everything.
            # Let's do a weighted blend: Original (Dark) + Blurred (Light Halo)
            
            blurred = ndimage.gaussian_filter(arr.astype(float), sigma=blur_sigma)
            
            # Composite: Keep original structure dominant, add blur as halo
            # halo = blurred * 0.5 ?
            # If we just replace with blurred, it looks out of focus.
            # Ink diffusion: Core is crisp-ish, edge is soft.
            # Let's try: Result = max(Original, Blurred * 0.7)
            
            # But wait, we are manipulating alpha channel here (L mode).
            # So: alpha = max(alpha_orig, alpha_blur * wetness)
            
            final_arr = np.maximum(arr.astype(float), blurred * 0.8)
            final_arr = np.clip(final_arr, 0, 255).astype(np.uint8)
            patch = Image.fromarray(final_arr, mode="L")

        # 5) Composite
        # Colored patch
        final_w, final_h = patch.size
        color_patch = Image.new("RGBA", (final_w, final_h), fill + (0,))
        
        # Apply mask
        color_patch.paste(fill + (255,), (0, 0), mask=patch)
        
        # 6) Jitter position
        p2 = self._jitter_point(p, r, self.char_jitter)
        
        # 7) Paste to base
        x = p2[0] - final_w // 2
        y = p2[1] - final_h // 2
        
        base_img.paste(color_patch, (x, y), color_patch)
