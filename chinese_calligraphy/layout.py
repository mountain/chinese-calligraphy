# chinese_calligraphy/layout.py

# 【繁】畫布與版面規格：手卷高度固定、寬度自動量測；並提供段落/邊距等版面參數
# [EN] Canvas & layout specs: handscroll has fixed height and auto-measured width; includes segment/margin specs

from __future__ import annotations

from dataclasses import dataclass

from PIL import Image

from .types import Color


@dataclass
class ScrollCanvas:
    # 【繁】手卷畫布：高度固定，寬度由作品在渲染前量測
    # [EN] Handscroll canvas: fixed height; width is measured by the work before rendering
    height: int
    bg: Color = (245, 240, 225)

    def new_image(self, width: int) -> Image.Image:
        # 【繁】建立 RGB 畫布
        # [EN] Create an RGB canvas
        return Image.new("RGB", (width, self.height), self.bg)


@dataclass
class SegmentSpec:
    # 【繁】正文分段：每段若干列 + 段間氣口（x 方向留白）
    # [EN] Main text segmentation: N columns per segment + inter-segment breathing gap (x direction)
    columns_per_segment: int = 14
    segment_gap: int = 260


@dataclass
class Margins:
    # 【繁】四邊留白（像素）
    # [EN] Margins (pixels)
    top: int = 200
    bottom: int = 200
    right: int = 250
    left: int = 250
