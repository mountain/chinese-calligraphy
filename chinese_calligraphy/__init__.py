# chinese_calligraphy/__init__.py

# 【繁】對外 API 匯出點（門面）
# [EN] Public API exports (facade)

from .brush import Brush
from .elements import Colophon, MainText, Seal, Title
from .layout import Margins, ScrollCanvas, SegmentSpec
from .style import Style
from .types import Color, Point, VariantTemplate
from .works.couplet import Couplet
from .works.fan import Fan
from .works.handscroll import Handscroll

__all__ = [
    "Color",
    "Point",
    "VariantTemplate",
    "Style",
    "Brush",
    "ScrollCanvas",
    "SegmentSpec",
    "Margins",
    "Title",
    "MainText",
    "Colophon",
    "Seal",
    "Handscroll",
    "Couplet",
    "Fan",
]
