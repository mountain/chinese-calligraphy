# chinese_calligraphy/__init__.py

# 【繁】對外 API 匯出點（門面）
# [EN] Public API exports (facade)

from .types import Color, Point, VariantTemplate
from .style import Style
from .brush import Brush
from .layout import ScrollCanvas, SegmentSpec, Margins
from .elements import Title, MainText, Colophon, Seal
from .works.handscroll import Handscroll
from .works.couplet import Couplet
from .works.fan import Fan

__all__ = [
    "Color", "Point", "VariantTemplate",
    "Style", "Brush",
    "ScrollCanvas", "SegmentSpec", "Margins",
    "Title", "MainText", "Colophon", "Seal",
    "Handscroll",
    "Couplet",
    "Fan",
]
