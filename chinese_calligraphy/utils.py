# chinese_calligraphy/utils.py

# 【繁】純工具函式：不依賴作品/元素/筆觸物件，便於測試與重用
# [EN] Pure utility functions: no dependency on work/element/brush objects; easy to test and reuse

from __future__ import annotations

import math

# =========================
# 【文字預處理 / Text preprocessing】
# =========================


def strip_newlines(text: str) -> str:
    # 【繁】去除空白行與換行，保留純文字流（利於按列高切列）
    # [EN] Remove empty lines/newlines to get a continuous stream (useful for column slicing)
    lines = [ln.strip() for ln in text.strip().splitlines()]
    return "".join([ln for ln in lines if ln])


def split_lines(text: str) -> list[str]:
    # 【繁】按行切分，去除空白行（適合“每行=一列”的排法）
    # [EN] Split by lines and drop empty ones (useful when “one line = one column”)
    lines = [ln.strip() for ln in text.strip().splitlines()]
    return [ln for ln in lines if ln]


def chunk(s: str, n: int) -> list[str]:
    # 【繁】將字流按每列字數切分成多列（最後一列可不足 n）
    # [EN] Split the stream into chunks of length n (last chunk may be shorter)
    if n <= 0:
        raise ValueError("chunk size n must be positive")
    return [s[i : i + n] for i in range(0, len(s), n)]


# =========================
# 【數值 / Numeric helpers】
# =========================


def floor_int(x: float) -> int:
    # 【繁】安全取整（向下取整）
    # [EN] Safe floor int
    return int(math.floor(x))


def clamp_int(v: int, lo: int, hi: int) -> int:
    # 【繁】整數截斷到區間 [lo, hi]
    # [EN] Clamp integer to [lo, hi]
    if lo > hi:
        lo, hi = hi, lo
    return max(lo, min(hi, v))
