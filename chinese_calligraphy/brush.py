# chinese_calligraphy/brush.py

# 【繁】筆觸與字形變異：列級慣性漂移 + 字級微抖 + 上下文微變異 + 「之」三態模型
# [EN] Brush & glyph variation: column inertial drift + micro jitter + contextual variation + 3-state model for '之'

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import random
from PIL import Image, ImageDraw, ImageFont

from .types import Color, Point, VariantTemplate
from .utils import clamp_int


@dataclass
class Brush:
    # =========================
    # 【隨機性 / Randomness】
    # =========================
    seed: Optional[int] = None

    # =========================
    # 【高頻字級抖動 / High-frequency char jitter】
    # =========================
    char_jitter: Tuple[int, int] = (0, 0)  # (jx, jy)

    # =========================
    # 【段級漂移 / Segment drift】
    # =========================
    segment_drift: Tuple[int, int] = (0, 0)  # (sx, sy)

    # =========================
    # 【列級慣性漂移 / Column inertial drift (random walk)】
    # =========================
    col_drift_step: Tuple[int, int] = (0, 0)     # per-column step range (sx, sy)
    col_drift_max: Tuple[int, int] = (0, 0)      # clamp max drift (mx, my)
    col_drift_damping: float = 0.85              # damping < 1.0

    # =========================
    # 【一般字微變異 / General glyph micro-variation】
    # =========================
    var_rotate_deg: float = 0.0   # ± degrees
    var_shear_x: float = 0.0      # ± shear coefficient (x)
    var_scale: float = 0.0        # ± relative scale, e.g. 0.03 => [0.97, 1.03]

    # =========================
    # 【「之」三態概率模型 / 3-state model for '之'】
    # =========================
    zhi_state_probs: Tuple[float, float, float] = (0.34, 0.40, 0.26)  # (stable, flow, vertical)
    zhi_segment_stickiness: float = 0.10  # 0~1 (higher => more sticky)
    zhi_pos_weight: float = 0.24          # 0~0.5 recommended
    zhi_mirror_prob: float = 0.68         # flip sign of rot/shear with this prob

    # 「之」模板庫 / Template banks for '之'
    zhi_templates: Dict[str, List[VariantTemplate]] = field(default_factory=lambda: {
        "stable": [
            # base_rot, base_shear, base_scale, base_anis_y, amp_rot, amp_shear, amp_scale, amp_anis_y
            (0.0,  0.00, 1.00, 1.00,  0.9, 0.025, 0.020, 0.030),
            (0.3, -0.02, 0.99, 0.97,  1.0, 0.030, 0.020, 0.035),
            (-0.4, 0.03, 1.01, 0.95,  1.1, 0.030, 0.020, 0.040),
            (0.1,  0.01, 0.98, 1.03,  1.0, 0.025, 0.025, 0.040),
        ],
        "flow": [
            (-0.6,  0.06, 1.02, 1.02,  1.6, 0.060, 0.030, 0.050),
            (0.7,  -0.06, 0.99, 0.98,  1.7, 0.060, 0.030, 0.055),
            (-0.4,  0.05, 1.04, 0.96,  1.4, 0.055, 0.035, 0.050),
            (0.5,  -0.05, 0.97, 1.05,  1.5, 0.055, 0.035, 0.055),
            (0.3,   0.04, 1.01, 1.00,  1.4, 0.055, 0.030, 0.050),
        ],
        "vertical": [
            (-0.6,  0.05, 1.00, 1.10,  1.3, 0.040, 0.025, 0.060),
            (0.7,  -0.06, 0.98, 1.14,  1.4, 0.045, 0.025, 0.070),
            (0.1,   0.02, 1.01, 1.18,  1.1, 0.035, 0.020, 0.080),
            (-0.3,  0.03, 0.99, 1.22,  1.2, 0.040, 0.020, 0.085),
            (0.4,  -0.02, 1.02, 1.12,  1.2, 0.035, 0.025, 0.070),
        ],
    })

    # 段內緩存：段內家族相 / Per-segment cache: family resemblance within segment
    _zhi_cache: Dict[int, Tuple[str, int]] = field(default_factory=dict)  # seg_idx -> (state, template_idx)

    # 段內統計：shear 去偏 / Per-segment stats for shear de-bias
    _zhi_seg_shear_sum: Dict[int, float] = field(default_factory=dict)
    _zhi_seg_shear_cnt: Dict[int, int] = field(default_factory=dict)

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
    def _jitter_point(p: Point, r: random.Random, j: Tuple[int, int]) -> Point:
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
    def begin_segment(self, r: random.Random) -> Tuple[int, int]:
        # 【繁】段起：抽取段級偏移
        # [EN] Segment start: sample segment-level drift
        sx = r.randint(-self.segment_drift[0], self.segment_drift[0]) if self.segment_drift[0] else 0
        sy = r.randint(-self.segment_drift[1], self.segment_drift[1]) if self.segment_drift[1] else 0
        return (sx, sy)

    # =========================
    # 【列級慣性 / Column inertial drift】
    # =========================
    def init_col_state(self) -> Tuple[float, float]:
        # 【繁】列漂移狀態初始化
        # [EN] Initialize column drift state
        return (0.0, 0.0)

    def step_col_state(self, r: random.Random, state: Tuple[float, float]) -> Tuple[float, float]:
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
        prev_ch: Optional[str],
        next_ch: Optional[str],
        seg_idx: int,
        col_idx: int,
        row_idx: int,
    ) -> Tuple[float, float, float]:
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
    def _weighted_choice3(self, r: random.Random, probs: Tuple[float, float, float]) -> int:
        # 【繁】按概率選 0/1/2
        # [EN] Weighted choice among 0/1/2
        x = r.random()
        a, b, c = probs
        if x < a:
            return 0
        if x < a + b:
            return 1
        return 2

    def _state_probs_with_position(self, col_pos_ratio: float) -> Tuple[float, float, float]:
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

    def pick_zhi_variant(self, r: random.Random, seg_idx: int, col_pos_ratio: float) -> Tuple[str, VariantTemplate]:
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

    def sample_from_template(self, r: random.Random, tpl: VariantTemplate) -> Tuple[float, float, float, float]:
        # 【繁】模板基準 + 連續擾動（幅度由模板指定）
        # [EN] Template base + continuous noise (amplitudes from template)
        base_rot, base_shear, base_scale, base_anis, amp_rot, amp_sh, amp_sc, amp_an = tpl

        rot = base_rot + r.uniform(-amp_rot, amp_rot)
        shear_x = base_shear + r.uniform(-amp_sh, amp_sh)

        # scale / anis_y 使用乘法擾動更自然
        scale = base_scale * (1.0 + r.uniform(-amp_sc, amp_sc))
        anis_y = base_anis * (1.0 + r.uniform(-amp_an, amp_an))

        return rot, shear_x, scale, anis_y

    def balance_zhi_params(self, r: random.Random, seg_idx: int, rot: float, shear_x: float) -> Tuple[float, float]:
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
    ) -> None:
        # 【繁】以「貼字」方式做幾何微變異（shear/scale/rotate），最後再做字級抖動並貼回底圖
        # [EN] Render glyph to a patch, apply shear/scale/rotate, then jitter and paste onto base image

        # 1) patch size estimation
        fs = getattr(font, "size", 100)
        pad = max(10, fs // 3)
        w = fs * 2 + pad * 2
        h = fs * 2 + pad * 2

        patch = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        pd = ImageDraw.Draw(patch)

        # 2) draw glyph roughly centered
        cx, cy = w // 2, h // 2
        pd.text((cx - fs // 2, cy - fs // 2), ch, font=font, fill=(*fill, 255))

        # 3) shear
        if shear_x != 0.0:
            a, b, c = 1.0, shear_x, 0.0
            d, e, f = 0.0, 1.0, 0.0
            patch = patch.transform(
                patch.size,
                Image.AFFINE,
                (a, b, c, d, e, f),
                resample=Image.BICUBIC,
            )

        # 4) scale + anis_y
        if scale != 1.0 or anis_y != 1.0:
            sx = scale
            sy = scale * anis_y
            nw = max(1, int(round(w * sx)))
            nh = max(1, int(round(h * sy)))
            scaled = patch.resize((nw, nh), resample=Image.BICUBIC)
            patch2 = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            patch2.paste(scaled, ((w - nw) // 2, (h - nh) // 2), scaled)
            patch = patch2

        # 5) rotate
        if rot != 0.0:
            patch = patch.rotate(rot, resample=Image.BICUBIC, expand=False)

        # 6) final jitter at placement
        p2 = self._jitter_point(p, r, self.char_jitter)

        # 7) paste patch centered at p2
        x = p2[0] - w // 2
        y = p2[1] - h // 2
        base_img.paste(patch, (x, y), patch)
