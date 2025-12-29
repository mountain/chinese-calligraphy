# chinese_calligraphy/works/couplet.py

# 【繁】對聯作品容器：包含上聯、下聯與橫批，修正居中算法
# [EN] Couplet work container: Fix centering logic based on column axis

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Tuple

from PIL import Image, ImageDraw

from ..layout import Margins, ScrollCanvas, SegmentSpec
from ..elements import MainText, Seal, Colophon
from ..brush import Brush
from ..style import Style


@dataclass
class Couplet:
    # 内容
    text_right: str
    text_left: str
    text_header: Optional[str] = None

    colophon_right: Optional[str] = None
    colophon_left: Optional[str] = None

    # 风格
    style: Optional[Style] = None
    brush: Brush = field(default_factory=Brush)

    # 尺寸
    width: int = 500
    height: int = 2000

    header_height: int = 450
    header_width: Optional[int] = None

    margins: Margins = field(default_factory=lambda: Margins(top=200, bottom=200, right=50, left=50))
    bg_color: Tuple[int, int, int] = (160, 40, 40)

    seal_right: Optional[Seal] = None
    seal_left: Optional[Seal] = None
    seal_header: Optional[Seal] = None

    def __post_init__(self):
        if self.style is None:
            raise ValueError("Style must be provided")

    def _render_vertical(self, text: str, colophon_text: Optional[str], seal: Optional[Seal]) -> Image.Image:
        """
        【繁】渲染單幅直聯（修正版：幾何絕對居中）
        [EN] Render single vertical scroll (Fixed: Absolute geometric centering)
        """
        canvas = ScrollCanvas(height=self.height, bg=self.bg_color)
        img = canvas.new_image(self.width)
        draw = ImageDraw.Draw(img)

        content_h = self.height - self.margins.top - self.margins.bottom

        # 1. 準備正文
        main = MainText(
            text=text,
            style=self.style,
            brush=self.brush,
            segment=SegmentSpec(columns_per_segment=1, segment_gap=0)
        )

        # 【核心修正】：計算到底有幾列（通常對聯為1列，但也可能因為字多變2列）
        cols = main._columns(content_h)
        num_cols = len(cols)

        # 計算「列群」的總跨度（第一列軸線到最後一列軸線的距離）
        # span = (n-1) * spacing
        block_axis_span = (num_cols - 1) * self.style.col_spacing

        # 2. 計算起始 X (最右側一列的軸線位置)
        # 邏輯：紙張中心 + (總跨度的一半)
        # 如果只有1列，span=0，x_start 直接等於 center。這就完美居中了。
        paper_center_x = self.width // 2
        x_start_main = paper_center_x + (block_axis_span // 2)

        # 繪製正文
        final_x_main = main.draw(img, draw, x_start_main, self.margins.top, content_h)

        # 3. 處理落款 (Colophon)
        # 落款依附於正文的「左邊緣」。
        # 我們需要估算正文最左側一列的視覺邊緣。
        # 正文最左側軸線 = x_start_main - block_axis_span
        # 視覺左邊緣 ≈ 最左軸線 - (font_size / 2)

        visual_left_edge = (x_start_main - block_axis_span) - (self.style.font_size // 2)

        # 默認印章位置（無落款時，居中於正文最左列下方）
        seal_x = (x_start_main - block_axis_span) - (seal.size // 2 if seal else 0)
        seal_y = self.height - self.margins.bottom - (seal.size if seal else 100)

        if colophon_text:
            sig_style = Style(
                font_path=self.style.font_path,
                font_size=int(self.style.font_size * 0.5),
                color=self.style.color,
                char_spacing=int(self.style.char_spacing * 0.5),
                col_spacing=self.style.col_spacing
            )
            colophon_obj = Colophon(
                signature=colophon_text,
                style=sig_style,
                brush=self.brush
            )

            # 落款位置：在正文視覺左邊緣，再往左空一點間隙
            gap = int(self.style.font_size * 0.8)
            x_col = visual_left_edge - gap

            # 落款高度：比正文起始略低，更有層次
            y_col = self.margins.top + self.style.font_size * 2

            end_x_col, end_y_col = colophon_obj.draw(draw, x_col, y_col)

            # 有落款時，印章蓋在落款下面
            if seal:
                seal_x = end_x_col - (seal.size - sig_style.font_size) // 2
                seal_y = end_y_col + 30

        # 4. 繪製印章
        if seal:
            seal.draw(draw, (int(seal_x), int(seal_y)))

        return img

    def _render_header(self) -> Optional[Image.Image]:
        """
        【繁】渲染橫批（修正版：水平幾何居中）
        """
        if not self.text_header:
            return None

        w = self.header_width if self.header_width else int(self.width * 2.5)
        h = self.header_height
        canvas = ScrollCanvas(height=h, bg=self.bg_color)
        img = canvas.new_image(w)
        draw = ImageDraw.Draw(img)

        one_char_h = self.style.step_y + 10
        top_margin = (h - self.style.font_size) // 2

        main = MainText(
            text=self.text_header,
            style=self.style,
            brush=self.brush,
            segment=SegmentSpec(columns_per_segment=1, segment_gap=0)
        )

        # 計算字數與跨度
        # 橫批其實是被切成了 N 列，每列 1 字
        cols = main._columns(one_char_h)  # 這裡會把每個字切成一列
        num_chars = len(cols)

        block_span = (num_chars - 1) * self.style.col_spacing

        x_center = w // 2
        # 右起橫排：第一字（最右）的軸線 = 中心 + 總跨度一半
        x_right_start = x_center + (block_span // 2)

        main.draw(img, draw, x_right_start, top_margin, one_char_h)

        if self.seal_header:
            sx = self.margins.left
            sy = (h - self.seal_header.size) // 2
            self.seal_header.draw(draw, (sx, sy))

        return img

    def render(self) -> Tuple[Image.Image, Image.Image, Optional[Image.Image]]:
        img_right = self._render_vertical(self.text_right, self.colophon_right, self.seal_right)
        img_left = self._render_vertical(self.text_left, self.colophon_left, self.seal_left)
        img_header = self._render_header()
        return img_right, img_left, img_header

    def save(self, prefix: str) -> None:
        r, l, h = self.render()
        r.save(f"{prefix}_right.png")
        l.save(f"{prefix}_left.png")
        if h:
            h.save(f"{prefix}_header.png")

    def save_preview(self, path: str, gap: int = 50) -> None:
        r, l, h = self.render()

        # 计算总画布尺寸
        w_total = r.width + l.width + gap * 4
        if h:
            w_total = max(w_total, h.width + gap * 2)
        h_header = h.height if h else 0
        h_total = h_header + gap + max(r.height, l.height) + gap

        preview = Image.new("RGB", (w_total, h_total), (255, 255, 255))

        # 1. 贴横批（居中）
        current_y = gap
        if h:
            x_h = (w_total - h.width) // 2
            preview.paste(h, (x_h, current_y))
            current_y += h.height + gap

        # 2. 贴对联（传统布局：右为上，左为下）
        # 观众视角： [下联 (Left Text)]  <-- gap -->  [上联 (Right Text)]

        pair_w = l.width + gap + r.width
        x_start = (w_total - pair_w) // 2

        # 先贴左边的位置（放置下联 l）
        preview.paste(l, (x_start, current_y))

        # 再贴右边的位置（放置上联 r）
        preview.paste(r, (x_start + l.width + gap, current_y))

        preview.save(path)