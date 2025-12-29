# chinese_calligraphy/works/fan.py

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional

from PIL import Image, ImageDraw

from ..types import Color
from ..style import Style
from ..brush import Brush
from ..utils import strip_newlines, chunk


@dataclass
class Fan:
    """
    【繁】折扇扇面：輻射狀排版，支持正文與落款不同字號
    [EN] Folding fan layout: Radial text arrangement, supporting distinct main text and colophon styles
    """
    text: str  # 正文
    colophon: Optional[str] = None  # 落款

    style: Optional[Style] = None  # 正文样式
    colophon_style: Optional[Style] = None  # 落款样式 (若無則自動生成)

    brush: Brush = field(default_factory=Brush)

    # 【繁】幾何參數 (Geometry)
    # 調整了預設值以確保扇面完整顯示
    width: int = 2400
    height: int = 1400

    # 圓心位置：X居中，Y在畫布下方
    center_x: int = 1200
    center_y: int = 2600

    # 半徑：確保 (center_y - radius_inner) > 0 且在畫布內
    radius_outer: int = 2200  # 頂邊 Y = 2600 - 2200 = 400
    radius_inner: int = 1350  # 底邊 Y = 2600 - 1350 = 1250 (在畫布範圍內)

    # 扇面開合角度
    angle_span: int = 140

    bg_color: Color = (235, 215, 170)  # 泥金/灑金紙色

    def __post_init__(self):
        if self.style is None:
            raise ValueError("Fan.style must be provided")

        # 自動生成落款樣式：字號約為正文的 50%~60%，字距列距相應縮小
        if self.colophon and self.colophon_style is None:
            small_size = int(self.style.font_size * 0.55)
            self.colophon_style = Style(
                font_path=self.style.font_path,
                font_size=small_size,
                color=(60, 60, 60),  # 落款墨色可稍淡，或同色
                char_spacing=int(self.style.char_spacing * 0.6),
                col_spacing=int(self.style.col_spacing * 0.6)
            )

    def _get_columns(self, text: str, style: Style, content_height_ratio: float = 1.0) -> List[str]:
        # content_height_ratio: 落款通常不寫滿到底，只寫約 80% 高度
        available_height = self.radius_outer - self.radius_inner
        margin = style.font_size

        # 實際可用高度
        content_h = (available_height - margin * 2) * content_height_ratio
        cpc = max(1, int(content_h / style.step_y))

        clean_text = strip_newlines(text)
        return chunk(clean_text, cpc)

    def render(self) -> Image.Image:
        img = Image.new("RGB", (self.width, self.height), (255, 255, 255))
        draw = ImageDraw.Draw(img)

        # --- 1. 繪製扇形背景 (Draw Background) ---
        half_span = self.angle_span / 2
        pil_start = 270 - half_span
        pil_end = 270 + half_span

        # 外弧 (Gold)
        bbox_outer = [
            self.center_x - self.radius_outer, self.center_y - self.radius_outer,
            self.center_x + self.radius_outer, self.center_y + self.radius_outer
        ]
        draw.pieslice(bbox_outer, start=pil_start, end=pil_end, fill=self.bg_color)

        # 內弧 (White mask) - 模擬扇骨鏤空區
        bbox_inner = [
            self.center_x - self.radius_inner, self.center_y - self.radius_inner,
            self.center_x + self.radius_inner, self.center_y + self.radius_inner
        ]
        draw.pieslice(bbox_inner, start=pil_start - 1, end=pil_end + 1, fill=(255, 255, 255))

        # --- 2. 準備排版數據 ---
        # 正文
        main_cols = self._get_columns(self.text, self.style, content_height_ratio=1.0)

        # 落款 (高度略短，顯得透氣)
        col_cols = []
        if self.colophon and self.colophon_style:
            col_cols = self._get_columns(self.colophon, self.colophon_style, content_height_ratio=0.85)

        # 計算總角度寬度
        # 角度計算：theta = ArcLength / Radius
        r_mid = (self.radius_outer + self.radius_inner) / 2

        def get_angle_step(s: Style):
            return math.degrees(s.col_spacing / r_mid)

        step_main = get_angle_step(self.style)
        step_col = get_angle_step(self.colophon_style) if self.colophon_style else 0

        # 正文總角度 + 正文與落款間距 + 落款總角度
        # 間距：通常空一個正文列寬
        gap_angle = step_main * 1.5 if col_cols else 0

        total_angle = (
                (len(main_cols) * step_main) +
                gap_angle +
                (len(col_cols) * step_col)
        )

        # --- 3. 繪製循環 ---
        # 起始角度：居中
        # 扇面右側為負角度，左側為正角度 (0度為正上方)
        current_angle = - (total_angle / 2)

        # 為了視覺平衡，先加上半個列寬，讓整體塊居中
        current_angle += step_main / 2

        font_main = self.style.font()
        font_col = self.colophon_style.font() if self.colophon_style else None
        rng = self.brush.rng()

        # 3.1 繪製正文
        for col_idx, col_text in enumerate(main_cols):
            self._draw_column(img, draw, col_text, current_angle, self.style, font_main, rng, is_colophon=False)
            current_angle += step_main

        # 3.2 繪製落款
        if col_cols:
            current_angle += (gap_angle - step_main / 2 - step_col / 2)  # 調整間距補償

            for col_idx, col_text in enumerate(col_cols):
                # 落款通常稍微低一點開始 (天頭留白更多)
                self._draw_column(img, draw, col_text, current_angle, self.colophon_style, font_col, rng,
                                  is_colophon=True)
                current_angle += step_col

        return img

    def _draw_column(self, img, draw, text, angle_deg, style, font, rng, is_colophon):
        # 計算列的起始半徑
        # 正文：緊貼上邊緣；落款：稍微下沈
        top_margin = style.font_size * 0.8
        if is_colophon:
            top_margin += style.font_size * 1.0  # 落款低一字

        current_r = self.radius_outer - top_margin

        # 列級漂移初始化
        dx, dy = self.brush.init_col_state()

        for row_idx, ch in enumerate(text):
            rad = math.radians(angle_deg)

            cx = self.center_x + current_r * math.sin(rad)
            cy = self.center_y - current_r * math.cos(rad)

            # 字形旋轉：指向圓心
            base_rot = -angle_deg

            # 筆觸變形
            rot_jit, shear, scale = self.brush.glyph_transform_params(
                rng, ch, None, None, 0, 0, row_idx
            )

            self.brush.draw_char(
                base_img=img,
                draw=draw,
                p=(int(cx + dx), int(cy + dy)),
                ch=ch,
                font=font,
                fill=style.color,
                r=rng,
                rot=base_rot + rot_jit,
                shear_x=shear,
                scale=scale
            )

            current_r -= style.step_y

    def save(self, path: str) -> None:
        """
        【繁】保存到文件
        [EN] Save to file
        """
        self.render().save(path)