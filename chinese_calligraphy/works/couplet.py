# chinese_calligraphy/works/couplet.py

# 【繁】對聯作品容器：增加垂直自動居中與視覺重心修正
# [EN] Couplet work container: Add vertical auto-centering and visual center correction

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
    # 【繁】內容
    # [EN] Content
    text_right: str
    text_left: str
    text_header: Optional[str] = None

    colophon_right: Optional[str] = None
    colophon_left: Optional[str] = None

    # 【繁】風格
    # [EN] Style
    style: Optional[Style] = None
    brush: Brush = field(default_factory=Brush)

    # 【繁】尺寸
    # [EN] Dimensions
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

    def _get_visual_center_y(self, container_h: int, content_h: int) -> int:
        """
        【繁】計算視覺垂直居中的起始點 Y
        [EN] Calculate the starting Y for visual vertical centering

        Note:
        【繁】幾何中心是 (container_h - content_h) // 2。但在書法裱畫中，視覺中心通常偏上（約 45% 處），否則會覺得字「掉」下去了。我們將中心點向上提 15% 的餘量。
        [EN] The geometric center is (container_h - content_h) // 2. However, in calligraphy mounting, the visual center is usually higher (around 45%), otherwise the text feels like it's "falling". We raise the center point by a 15% margin.
        """
        geometric_center_start = (container_h - content_h) // 2
        visual_correction = int(geometric_center_start * 0.15)  # 【繁】向上提 15% 的空白距離 [EN] Raise by 15% blank distance
        return geometric_center_start - visual_correction

    def _render_vertical(self, text: str, colophon_text: Optional[str], seal: Optional[Seal]) -> Image.Image:
        """
        【繁】渲染單幅直聯（垂直自動居中 + 視覺修正）
        [EN] Render a single vertical scroll (vertical auto-centering + visual correction)
        """
        canvas = ScrollCanvas(height=self.height, bg=self.bg_color)
        img = canvas.new_image(self.width)
        draw = ImageDraw.Draw(img)

        # 1. 【繁】計算正文的實際垂直高度
        #    [EN] Calculate the actual vertical height of the main text
        # 【繁】MainText 中，高度 ≈ (字數 - 1) * step_y。因為這裡是單列，我們直接算：
        # [EN] In MainText, height ≈ (num_chars - 1) * step_y. Since this is a single column, we calculate directly:
        num_chars = len(text)

        # 【繁】內容跨度：從第一個字中心到最後一個字中心的距離
        # [EN] Content span: distance from the center of the first character to the center of the last character
        text_span_y = (num_chars - 1) * self.style.step_y

        # 2. 【繁】計算起始 Y (第一個字的中心位置)
        #    [EN] Calculate start Y (center position of the first character)
        # 【繁】使用視覺修正算法，而不是固定的 margins.top
        # [EN] Use visual correction algorithm instead of fixed margins.top
        # 【繁】這裡 content_h 我們視為 text_span_y (雖然字本身有高度，但 Brush 以中心定位，這樣計算是對稱的)
        # [EN] Here we treat content_h as text_span_y (although chars have height, Brush uses center positioning, so this calculation is symmetric)
        y_start_main = self._get_visual_center_y(self.height, text_span_y)

        # 【繁】保底：不要高於 margins.top (防止字太大衝出邊界)
        # [EN] Safeguard: do not go higher than margins.top (prevent text from overflowing the boundary)
        y_start_main = max(self.margins.top, y_start_main)

        # 3. 【繁】準備正文對象
        #    [EN] Prepare MainText object
        main = MainText(
            text=text,
            style=self.style,
            brush=self.brush,
            segment=SegmentSpec(columns_per_segment=1, segment_gap=0)
        )

        # 4. 【繁】計算水平居中 X
        #    [EN] Calculate horizontal centering X
        # 【繁】MainText.width() 用於計算寬度，這裡近似為 font_size
        # [EN] MainText.width() is used to calculate width, approximated here as font_size
        # 【繁】content_height 傳入 self.height 即可，因為我們已經手動控製了 y_start
        # [EN] Pass self.height for content_height, as we have manually controlled y_start
        cols = main._columns(self.height)
        num_cols = len(cols)
        block_axis_span = (num_cols - 1) * self.style.col_spacing
        paper_center_x = self.width // 2
        x_start_main = paper_center_x + (block_axis_span // 2)

        # 5. 【繁】繪製正文
        #    [EN] Draw main text
        # 【繁】注意：content_height 參數在 draw 裡主要用於切分列。因為我們已經強制單列且手動計算了 Y，這裡傳入剩餘高度即可
        # [EN] Note: content_height in draw is mainly used for column splitting. Since we forced a single column and manually calculated Y, passing remaining height is fine
        final_x_main = main.draw(img, draw, x_start_main, y_start_main, self.height)

        # 6. 【繁】處理落款
        #    [EN] Handle colophon
        visual_left_edge = (x_start_main - block_axis_span) - (self.style.font_size // 2)

        # 【繁】默認印章位置
        # [EN] Default seal position
        seal_x = (x_start_main - block_axis_span) - (seal.size // 2 if seal else 0)

        # 【繁】印章跟隨正文結束位置
        # [EN] Seal follows the end position of the main text
        seal_y = y_start_main + text_span_y + self.style.font_size + 50

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

            gap = int(self.style.font_size * 0.8)
            x_col = visual_left_edge - gap

            # 【繁】【重要】落款起始高度改為「相對於正文起始點」
            # [EN] [Important] Colophon start height changed to be "relative to main text start point"
            # 【繁】讓落款的第一個字，對齊正文的第二個字左右，顯得謙卑
            # [EN] Align the first char of colophon roughly with the second char of main text, appearing humble
            y_col = y_start_main + self.style.font_size * 1.5

            end_x_col, end_y_col = colophon_obj.draw(draw, x_col, y_col)

            if seal:
                seal_x = end_x_col - (seal.size - sig_style.font_size) // 2
                seal_y = end_y_col + 30

        if seal:
            seal.draw(draw, (int(seal_x), int(seal_y)))

        return img

    def _render_header(self) -> Optional[Image.Image]:
        """
        【繁】渲染橫批（視覺垂直居中）
        [EN] Render header (visual vertical centering)
        """
        if not self.text_header:
            return None

        w = self.header_width if self.header_width else int(self.width * 2.5)
        h = self.header_height
        canvas = ScrollCanvas(height=h, bg=self.bg_color)
        img = canvas.new_image(w)
        draw = ImageDraw.Draw(img)

        one_char_h = self.style.step_y + 10

        # 【繁】【視覺修正】幾何中軸是 h // 2。我們稍微向上提一點點（如 10% 的半高），讓字看起來更精神
        # [EN] [Visual Correction] Geometric axis is h // 2. We raise it slightly (e.g., 10% of half height) to make the text look more energetic
        visual_shift = int((h // 2) * 0.1)
        y_center_axis = (h // 2) - visual_shift

        main = MainText(
            text=self.text_header,
            style=self.style,
            brush=self.brush,
            segment=SegmentSpec(columns_per_segment=1, segment_gap=0)
        )

        cols = main._columns(one_char_h)
        num_chars = len(cols)
        block_span = (num_chars - 1) * self.style.col_spacing

        x_center = w // 2
        x_right_start = x_center + (block_span // 2)

        main.draw(img, draw, x_right_start, y_center_axis, one_char_h)

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
        w_total = r.width + l.width + gap * 4
        if h:
            w_total = max(w_total, h.width + gap * 2)
        h_header = h.height if h else 0
        h_total = h_header + gap + max(r.height, l.height) + gap

        preview = Image.new("RGB", (w_total, h_total), (255, 255, 255))
        current_y = gap
        if h:
            x_h = (w_total - h.width) // 2
            preview.paste(h, (x_h, current_y))
            current_y += h.height + gap

        pair_w = l.width + gap + r.width
        x_start = (w_total - pair_w) // 2

        # 【繁】左側放左聯（下聯），右側放右聯（上聯），符合展示習慣
        # [EN] Place left scroll (bottom couplet) on the left, right scroll (top couplet) on the right, matching display convention
        preview.paste(l, (x_start, current_y))
        preview.paste(r, (x_start + l.width + gap, current_y))

        preview.save(path)