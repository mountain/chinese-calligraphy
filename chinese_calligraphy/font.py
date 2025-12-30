# chinese_calligraphy/font.py

# 【繁】字體查找：以“字體名字”在不同作業系統上定位字體檔案（TTF/OTF/TTC）
# [EN] Font lookup: locate font files by “font family/name” across OSes (TTF/OTF/TTC)

from __future__ import annotations

import os
import sys
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from functools import lru_cache

FONT_EXTS = (".ttf", ".otf", ".ttc", ".otc")


@dataclass(frozen=True)
class FontSpec:
    # 【繁】字體規格：以名稱（family/name）為主，可選權重/風格作為提示
    # [EN] Font spec: family/name primarily, optional weight/style hints
    name: str
    weight: str | None = None  # e.g. "Regular", "Bold"
    style: str | None = None  # e.g. "Italic"


def _norm(s: str) -> str:
    # 【繁】標準化：小寫、去空白與連字號，便於模糊比對
    # [EN] Normalize: lowercase and remove spaces/hyphens for fuzzy match
    return "".join(ch for ch in s.lower() if ch not in " -_")


def _platform_font_dirs() -> list[str]:
    # 【繁】常見系統字體目錄
    # [EN] Common system font directories
    dirs: list[str] = []

    if sys.platform == "darwin":
        # macOS
        dirs += [
            "/System/Library/Fonts",
            "/Library/Fonts",
            os.path.expanduser("~/Library/Fonts"),
        ]
    elif sys.platform.startswith("win"):
        # Windows
        windir = os.environ.get("WINDIR", r"C:\Windows")
        dirs += [os.path.join(windir, "Fonts")]
        # 也可加：用户本地字体目录（新版本 Windows）
        local = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "Fonts")
        if local.strip():
            dirs += [local]
    else:
        # Linux / other unix
        dirs += [
            "/usr/share/fonts",
            "/usr/local/share/fonts",
            os.path.expanduser("~/.fonts"),
            os.path.expanduser("~/.local/share/fonts"),
        ]

    # 去重且只保留存在的目录
    out: list[str] = []
    seen = set()
    for d in dirs:
        if d and d not in seen and os.path.isdir(d):
            out.append(d)
            seen.add(d)
    return out


def _iter_font_files(dirs: Sequence[str]) -> Iterable[str]:
    # 【繁】遍歷字體檔案（遞迴）
    # [EN] Recursively iterate font files
    for root in dirs:
        for dirpath, _, filenames in os.walk(root):
            for fn in filenames:
                ext = os.path.splitext(fn)[1].lower()
                if ext in FONT_EXTS:
                    yield os.path.join(dirpath, fn)


def _filename_score(path: str, target: str) -> int:
    # 【繁】用檔名做快速粗匹配評分（越高越好）
    # [EN] Quick filename-based scoring (higher is better)
    base = _norm(os.path.basename(path))
    t = _norm(target)

    if t == base:
        return 100
    if t in base:
        return 80
    # 允许 target 的分词都在文件名里
    tokens = [_norm(x) for x in target.split() if x.strip()]
    if tokens and all(tok in base for tok in tokens):
        return 60
    return 0


def _try_fonttools_match(path: str, target: str) -> int:
    # 【繁】（可選）使用 fontTools 讀取 name table 做精確匹配
    # [EN] (Optional) Use fontTools to read name table for better matching
    try:
        from fontTools.ttLib import TTFont  # type: ignore
    except Exception:
        return 0

    try:
        # 注意：TTC/OTC 也可用 TTCollection，但这里先简单处理；失败就回退
        font = TTFont(path, lazy=True)
        name_table = font["name"].names
        t = _norm(target)

        # nameID 常见：1 family, 4 full name, 16 typographic family
        candidates = []
        for rec in name_table:
            try:
                s = rec.toUnicode()
            except Exception:
                continue
            candidates.append(_norm(s))

        font.close()

        if any(t == c for c in candidates):
            return 120
        if any(t in c for c in candidates):
            return 90
        return 0
    except Exception:
        return 0


@lru_cache(maxsize=256)
def find_font_path(font_name: str, extra_dirs: tuple[str, ...] = ()) -> str | None:
    """
    【繁】按字體名字尋找字體檔案路徑；找不到返回 None。
    [EN] Find a font file path by font name; return None if not found.
    """
    dirs = list(_platform_font_dirs()) + [d for d in extra_dirs if os.path.isdir(d)]
    best: tuple[int, str] = (0, "")

    for path in _iter_font_files(dirs):
        s1 = _filename_score(path, font_name)
        if s1:
            score = s1
            # 若分数中等以上，再用 fontTools 提升准确率（若可用）
            if score >= 60:
                score = max(score, _try_fonttools_match(path, font_name))
            if score > best[0]:
                best = (score, path)
                # 过高就提前结束
                if score >= 120:
                    break
        else:
            # 文件名不匹配时，也可尝试 fontTools（但很慢；这里保守跳过）
            pass

    return best[1] if best[0] > 0 else None


def require_font_path(font_name: str, extra_dirs: Sequence[str] = ()) -> str:
    # 【繁】找不到就抛异常，给调用者明确错误
    # [EN] Raise if not found, for a clear error path
    p = find_font_path(font_name, tuple(extra_dirs))
    if not p:
        dirs = _platform_font_dirs()
        raise FileNotFoundError(
            f"Font not found: '{font_name}'. Searched in: {dirs} (plus extra_dirs={list(extra_dirs)})"
        )
    return p
