# chinese_calligraphy/elements.py

# 【繁】作品元素（組件）：題、正文、款識、印章
# [EN] Work elements (components): title, main text, colophon, seals

from __future__ import annotations

from dataclasses import dataclass, field

from PIL import Image, ImageDraw, ImageFont

from .brush import Brush
from .layout import SegmentSpec
from .style import Style
from .types import Color, Point
from .utils import chunk, floor_int, strip_newlines

# =========================
# 【引首題 / Title】
# =========================


@dataclass
class Title:
    # 【繁】引首題字（通常一列）
    # [EN] Lead title (usually a single vertical column)
    text: str
    style: Style
    brush: Brush = field(default_factory=Brush)

    # 【繁】題後留白（題與正文之間的氣口）
    # [EN] Extra gap after title (breathing room before main text)
    extra_gap_after: int = 180

    def width(self) -> int:
        # 【繁】題字寬度估計：預留兩列更穩
        # [EN] Estimated width: reserve about two column widths
        return floor_int(self.style.col_spacing * 2.0)

    def draw(self, draw: ImageDraw.ImageDraw, x_right: int, y_top: int) -> None:
        # 【繁】在 (x_right, y_top) 畫一列竪排題字
        # [EN] Draw title as a vertical column at (x_right, y_top)
        font = self.style.font()
        r = self.brush.rng()

        x = x_right
        y = y_top
        for ch in self.text:
            p = (x, y)
            p = self.brush.jitter_point_basic(p, r)
            draw.text(p, ch, font=font, fill=self.style.color)
            y += self.style.step_y


# =========================
# 【正文 / Main text】
# =========================


@dataclass
class MainText:
    # 【繁】正文：按列高切列，再按段落打包（手卷右起左行）
    # [EN] Main text: slice into columns by height, then pack into segments (handscroll: right-to-left)
    text: str
    style: Style
    segment: SegmentSpec = field(default_factory=SegmentSpec)

    # 【繁】筆觸模型（含「之」三態、慣性漂移等）
    # [EN] Brush model (incl. 3-state '之' + inertial drift, etc.)
    brush: Brush = field(
        default_factory=lambda: Brush(
            seed=2,
            char_jitter=(1, 1),
            segment_drift=(10, 10),
            col_drift_step=(0, 10),
            col_drift_max=(0, 36),
            col_drift_damping=0.85,
            var_rotate_deg=1.2,
            var_shear_x=0.06,
            var_scale=0.03,
        )
    )

    # 【繁】可選：手動指定每列字數（覆蓋自動計算）
    # [EN] Optional: override characters per column
    chars_per_col: int | None = None

    def _chars_per_col(self, content_height: int) -> int:
        # 【繁】每列可容納字數（或使用手動指定）
        # [EN] Characters per column (or use manual override)
        if self.chars_per_col is not None:
            return max(1, int(self.chars_per_col))
        return max(1, floor_int(content_height / self.style.step_y))

    def _columns(self, content_height: int) -> list[str]:
        # 【繁】將全文轉字流，再按列字數切成多列
        # [EN] Convert to stream, then chunk into columns
        stream = strip_newlines(self.text)
        cpc = self._chars_per_col(content_height)
        return chunk(stream, cpc)

    def width(self, content_height: int) -> int:
        # 【繁】計算正文總寬度（列距 * 列數 + 段間氣口）
        # [EN] Measure total main text width (columns + inter-segment gaps)
        cols = self._columns(content_height)
        cols_per_seg = self.segment.columns_per_segment
        seg_gap = self.segment.segment_gap
        segs = (len(cols) + cols_per_seg - 1) // cols_per_seg
        return len(cols) * self.style.col_spacing + max(0, segs - 1) * seg_gap

    def draw(
        self,
        img: Image.Image,
        draw: ImageDraw.ImageDraw,
        x_right_start: int,
        y_top: int,
        content_height: int,
    ) -> int:
        # 【繁】從右向左繪製正文；回傳繪製結束後的 x_right（更靠左）
        # [EN] Draw main text right-to-left; return final x_right after drawing
        font = self.style.font()
        r = self.brush.rng()

        cols = self._columns(content_height)
        cols_per_seg = self.segment.columns_per_segment
        seg_gap = self.segment.segment_gap

        x_right = x_right_start

        for seg_i in range(0, len(cols), cols_per_seg):
            seg_cols = cols[seg_i : seg_i + cols_per_seg]
            seg_idx = seg_i // cols_per_seg

            # 【繁】段級偏移（一次）
            # [EN] Segment-level drift (once per segment)
            sx, sy = self.brush.begin_segment(r)

            # 【繁】列級慣性狀態（每段重置一次）
            # [EN] Column inertial state (reset per segment)
            col_state = self.brush.init_col_state()

            seg_x_right = x_right + sx
            seg_y_top = y_top + sy

            for local_col_idx, col_text in enumerate(seg_cols):
                col_pos_ratio = 0.0 if len(seg_cols) <= 1 else (local_col_idx / (len(seg_cols) - 1))

                # 更新列級慣性漂移
                col_state = self.brush.step_col_state(r, col_state)
                dx, dy = col_state

                cx = seg_x_right + int(dx)
                cy = seg_y_top + int(dy)

                y = cy
                for row_idx, ch in enumerate(col_text):
                    prev_ch = col_text[row_idx - 1] if row_idx > 0 else None
                    next_ch = col_text[row_idx + 1] if row_idx + 1 < len(col_text) else None

                    if ch == "之":
                        # 三態 → 模板 → 連續抽樣 → 去偏
                        _, tpl = self.brush.pick_zhi_variant(r=r, seg_idx=seg_idx, col_pos_ratio=col_pos_ratio)
                        rot, shear_x, scale, anis_y = self.brush.sample_from_template(r, tpl)
                        rot, shear_x = self.brush.balance_zhi_params(r, seg_idx, rot, shear_x)

                        # 【繁】小幅噪聲，避免模板味
                        # [EN] Tiny noise to avoid template feel
                        rot += r.uniform(-0.35, 0.35)
                        shear_x += r.uniform(-0.010, 0.010)
                        scale *= 1.0 + r.uniform(-0.006, 0.006)
                        anis_y *= 1.0 + r.uniform(-0.010, 0.010)
                    else:
                        rot, shear_x, scale = self.brush.glyph_transform_params(
                            r=r,
                            ch=ch,
                            prev_ch=prev_ch,
                            next_ch=next_ch,
                            seg_idx=seg_idx,
                            col_idx=local_col_idx,
                            row_idx=row_idx,
                        )
                        anis_y = 1.0

                    self.brush.draw_char(
                        base_img=img,
                        draw=draw,
                        p=(cx, y),
                        ch=ch,
                        font=font,
                        fill=self.style.color,
                        r=r,
                        rot=rot,
                        shear_x=shear_x,
                        scale=scale,
                        anis_y=anis_y,
                    )

                    y += self.style.step_y

                seg_x_right -= self.style.col_spacing

            x_right = seg_x_right - seg_gap

        return x_right


# =========================
# 【款識 / Colophon】
# =========================


@dataclass
class Colophon:
    # 【繁】款識（默認一列小字）
    # [EN] Colophon (default one small column)
    signature: str
    style: Style
    brush: Brush = field(default_factory=Brush)

    def width(self) -> int:
        # 【繁】估算款識占寬：預留兩列更穩
        # [EN] Estimated width: reserve about two column widths
        return floor_int(self.style.col_spacing * 2.0)

    def draw(self, draw: ImageDraw.ImageDraw, x_right: int, y_top: int) -> tuple[int, int]:
        # 【繁】繪製款識並回傳末尾位置（便於放名章）
        # [EN] Draw colophon and return end position for placing the name seal
        font = self.style.font()
        r = self.brush.rng()

        x = x_right
        y = y_top
        for ch in self.signature:
            p = (x, y)
            p = self.brush.jitter_point_basic(p, r)
            draw.text(p, ch, font=font, fill=self.style.color)
            y += self.style.step_y
        return (x, y)


# =========================
# 【印章 / Seal】
# =========================


@dataclass
class Seal:
    # 【繁】印章（v0：方印 + 2x2 排列印文）
    # [EN] Seal (v0: square seal + 2x2 grid)
    font_path: str
    font_size: int = 50
    size: int = 110
    color: Color = (160, 30, 30)
    border_width: int = 8
    padding: int = 10
    cell: int = 45
    text_grid: list[tuple[str, int, int]] = field(default_factory=list)  # (char, row, col)

    def draw(self, draw: ImageDraw.ImageDraw, origin: Point) -> None:
        # 【繁】在 origin 畫印：先框，再印文
        # [EN] Draw seal at origin: border then characters
        x, y = origin
        draw.rectangle([x, y, x + self.size, y + self.size], outline=self.color, width=self.border_width)
        font = ImageFont.truetype(self.font_path, self.font_size)
        for ch, row, col in self.text_grid:
            cx = x + self.padding + col * self.cell
            cy = y + self.padding + row * self.cell
            draw.text((cx, cy), ch, font=font, fill=self.color)
