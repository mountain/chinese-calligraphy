# chinese_calligraphy/works/handscroll.py

# 【繁】手卷作品容器：負責量測寬度、按慣例調度各元素繪製、輸出/預覽
# [EN] Handscroll work container: measures width, orchestrates element drawing, saves output/previews

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from PIL import Image, ImageDraw

from ..layout import Margins, ScrollCanvas
from ..elements import Title, MainText, Colophon, Seal


@dataclass
class Handscroll:
    # 【繁】手卷：右起左行；寬度自動量測；元素依慣例序列繪製
    # [EN] Handscroll: starts from the right and flows left; auto-measures width; draws elements in convention order
    canvas: ScrollCanvas
    margins: Margins = field(default_factory=Margins)

    title: Optional[Title] = None
    main: Optional[MainText] = None
    colophon: Optional[Colophon] = None

    lead_seal: Optional[Seal] = None   # 引首章 / lead seal (optional)
    name_seal: Optional[Seal] = None   # 名章 / name seal (optional)

    # 【繁】引首/拖尾留白：決定“卷”的呼吸
    # [EN] Lead/tail blank spaces: breathing of the scroll
    lead_space: int = 520
    tail_space: int = 780

    def _content_height(self) -> int:
        # 【繁】正文可用高度
        # [EN] Available content height
        return self.canvas.height - self.margins.top - self.margins.bottom

    def measure_width(self) -> int:
        # 【繁】量測整卷寬度：左右邊距 + 引首/拖尾 + 題 + 正文 + 款 + 鈐印餘量
        # [EN] Measure total width: margins + lead/tail + title + main + colophon + extra for seals
        assert self.main is not None, "Handscroll.main must be set"

        content_h = self._content_height()
        w = self.margins.left + self.margins.right + self.lead_space + self.tail_space

        if self.title is not None:
            w += self.title.width()
            w += self.title.extra_gap_after

        w += self.main.width(content_h)

        if self.colophon is not None:
            w += self.colophon.width()
            w += 260  # 【繁】款後留一口氣，便於名章落款；[EN] breathing room after colophon

        return w

    def render(self) -> Image.Image:
        # 【繁】生成整卷圖像
        # [EN] Render full scroll image
        assert self.main is not None, "Handscroll.main must be set"

        content_h = self._content_height()
        width = self.measure_width()

        img = self.canvas.new_image(width)
        draw = ImageDraw.Draw(img)

        # 【繁】右起：從最右端向左逐段展開
        # [EN] Start from the right edge and flow leftwards
        x_right = width - self.margins.right - self.lead_space
        y_top = self.margins.top

        # 1) 引首題字 / Lead title
        if self.title is not None:
            self.title.draw(draw, x_right, y_top + 50)

            # 引首章（可選）：放在題後稍偏下
            # Lead seal (optional): place slightly below after title
            if self.lead_seal is not None:
                seal_x = x_right + 20
                seal_y = y_top + 50 + len(self.title.text) * self.title.style.step_y + 90
                self.lead_seal.draw(draw, (seal_x, seal_y))

            x_right -= self.title.width() + self.title.extra_gap_after

        # 2) 正文（分段）/ Main text (segmented)
        x_right = self.main.draw(img, draw, x_right, y_top, content_h)

        # 3) 款識 / Colophon
        if self.colophon is not None:
            # 【繁】款識略低：避免與正文末列同高頂住
            # [EN] Put colophon a bit lower to avoid cramped ending
            sig_x = x_right - 50
            sig_y = y_top + 600
            _, end_y = self.colophon.draw(draw, sig_x, sig_y)

            # 4) 名章（可選）/ Name seal (optional)
            if self.name_seal is not None:
                seal_x = sig_x - 20
                seal_y = end_y + 30
                self.name_seal.draw(draw, (seal_x, seal_y))

        return img

    def save(self, path: str) -> None:
        # 【繁】輸出 PNG
        # [EN] Save PNG
        self.render().save(path)

    def save_preview(self, path: str, segment_index: int, preview_width: int = 3200) -> None:
        # 【繁】輸出某一段附近的裁切預覽，便於調參
        # [EN] Save a cropped preview around a segment for tuning
        assert self.main is not None

        img = self.render()

        # 計算正文起點（扣除引首）
        x_right_full = img.size[0] - self.margins.right - self.lead_space
        if self.title is not None:
            x_right_full -= self.title.width() + self.title.extra_gap_after

        cols_per_seg = self.main.segment.columns_per_segment
        seg_gap = self.main.segment.segment_gap
        seg_w = cols_per_seg * self.main.style.col_spacing + seg_gap

        target_x_right = x_right_full - segment_index * seg_w
        x1 = max(0, target_x_right - preview_width)
        x2 = min(img.size[0], target_x_right)

        crop = img.crop((x1, 0, x2, img.size[1]))
        crop.save(path)
