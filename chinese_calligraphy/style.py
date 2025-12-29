# chinese_calligraphy/style.py

# 【繁】書寫風格：字體、字號、墨色、字距、列距
# [EN] Writing style: font, size, ink color, char/column spacing

from __future__ import annotations

from dataclasses import dataclass
from PIL import ImageFont

from .types import Color


@dataclass(frozen=True)
class Style:
    # 【繁】書寫風格：字體、字號、墨色、字距、列距
    # [EN] Writing style: font, size, ink color, char/column spacing
    font_path: str
    font_size: int
    color: Color = (20, 20, 20)

    # 【繁】竪排：字與字之間（y）
    # [EN] Vertical layout: inter-character spacing (y)
    char_spacing: int = 15

    # 【繁】竪排：列與列之間（x）
    # [EN] Vertical layout: inter-column spacing (x)
    col_spacing: int = 160

    def font(self) -> ImageFont.FreeTypeFont:
        # 【繁】載入字體（TrueType/OpenType）
        # [EN] Load font (TrueType/OpenType)
        return ImageFont.truetype(self.font_path, self.font_size)

    @property
    def step_y(self) -> int:
        # 【繁】竪排每個字的垂直步長
        # [EN] Vertical step per character for vertical layout
        return self.font_size + self.char_spacing
