# Chinese Calligraphy (Python API)

A Pythonic interface for composing and rendering traditional Chinese calligraphy works using Pillow. Model whole works like handscrolls with title, main text, colophon, and seals; tune style and brush behavior for organic variation.

![Preview handscroll](https://raw.githubusercontent.com/mountain/chinese-calligraphy/main/handscroll_small.png)

- Components: Title, MainText, Colophon, Seal
- Layout: handscroll canvas, margins, segmentation (columns per segment + inter-segment gap)
- Style: choose font, size, color, inter-character and inter-column spacing
- Brush dynamics: character jitter, segment drift, column inertial drift, contextual micro-variation, and a 3-state model for the character “之”
- Font discovery helper to locate installed fonts by family/name across macOS/Windows/Linux


## Installation

Requires Python 3.10+.

- Core (uses Pillow):
  
  ```bash
  pip install chinese-calligraphy
  ```

- Optional: enable deeper font-name matching via fontTools in the font lookup helper:
  
  ```bash
  pip install "chinese-calligraphy[fonttools]"
  ```


## Quickstart

Render a simple handscroll image:

```python
from chinese_calligraphy import (
    Style, Brush, ScrollCanvas, Margins, SegmentSpec,
    Title, MainText, Colophon, Seal, Handscroll
)
from chinese_calligraphy.font import find_font_path, require_font_path

# Pick fonts installed on your system (change these names if not available)
FONT_PATH = (
    find_font_path("FZWangDXCJF") or
    find_font_path("PingFang") or
    find_font_path("Songti SC") or
    find_font_path("STSong") or
    find_font_path("SimSun") or
    find_font_path("Noto Serif CJK SC")
)
if not FONT_PATH:
    # As a last resort, require a specific installed family (raises if missing)
    FONT_PATH = require_font_path("FZWangDXCJF")

SEAL_FONT = (
    find_font_path("FZZJ-MZFU") or
    find_font_path("STKaiti") or
    find_font_path("KaiTi") or
    find_font_path("KaiTi_GB2312")
)
if not SEAL_FONT:
    SEAL_FONT = require_font_path("FZZJ-MZFU")

canvas = ScrollCanvas(height=2800, bg=(245, 240, 225))
margins = Margins(top=200, bottom=200, right=250, left=250)

title_style = Style(font_path=FONT_PATH, font_size=132, color=(20, 20, 20), char_spacing=15, col_spacing=240)
main_style  = Style(font_path=FONT_PATH, font_size=110, color=(20, 20, 20), char_spacing=10, col_spacing=160)
sig_style   = Style(font_path=FONT_PATH, font_size=66,  color=(60, 60, 60), char_spacing=5,  col_spacing=160)

title = Title(text="愛蓮說", style=title_style, brush=Brush(seed=1, char_jitter=(1, 1)), extra_gap_after=220)

text = (
    "水陸草木之花可愛者甚蕃晉陶淵明獨愛菊自李唐來世人盛愛牡丹"
    "予獨愛蓮之出淤泥而不染濯清漣而不妖中通外直不蔓不枝香遠益清亭亭淨植可遠觀而不可褻玩焉"
    "予謂菊花之隱逸者也牡丹花之富貴者也蓮花之君子者也噫菊之愛陶後鮮有聞蓮之愛同予者何人牡丹之愛宜乎眾矣"
)
main = MainText(text=text, style=main_style, segment=SegmentSpec(columns_per_segment=14, segment_gap=260))

colophon = Colophon(signature="乙巳仲冬 博德仿王鐸意書 於靈境山房", style=sig_style, brush=Brush(seed=3))

lead_seal = Seal(font_path=SEAL_FONT, border_width=6, text_grid=[("雲",0,0),("境",0,1),("清",1,0),("章",1,1)])
name_seal = Seal(font_path=SEAL_FONT, text_grid=[("博",0,0),("德",0,1),("制",1,0),("印",1,1)])

scroll = Handscroll(
    canvas=canvas,
    margins=margins,
    title=title,
    main=main,
    colophon=colophon,
    lead_seal=lead_seal,
    name_seal=name_seal,
    lead_space=420,
    tail_space=780,
)

scroll.save("handscroll.png")
```

This produces an image like the preview above.


## API overview

- chinese_calligraphy.Style
  - font_path, font_size, color=(R,G,B)
  - char_spacing (vertical step), col_spacing (horizontal column pitch)
  - font() -> PIL.ImageFont.FreeTypeFont; step_y property = font_size + char_spacing

- chinese_calligraphy.Brush
  - seed for reproducible randomness
  - char_jitter=(jx,jy) per-character placement jitter
  - segment_drift=(sx,sy) per-segment offset
  - col_drift_step=(sx,sy), col_drift_max=(mx,my), col_drift_damping for inertial column drift
  - var_rotate_deg, var_shear_x, var_scale for contextual micro-variation
  - 3-state model for “之”: zhi_state_probs, zhi_segment_stickiness, zhi_pos_weight, zhi_mirror_prob

- chinese_calligraphy.layout
  - ScrollCanvas(height, bg=(R,G,B)) with new_image(width)
  - SegmentSpec(columns_per_segment=14, segment_gap=260)
  - Margins(top=200, bottom=200, right=250, left=250)

- chinese_calligraphy.elements
  - Title(text, style, brush=Brush(), extra_gap_after=...)
  - MainText(text, style, segment=SegmentSpec(...), brush=default Brush with inertial + 3-state)
    - width(content_height) -> total width of main text region
    - draw(img, draw, x_right_start, y_top, content_height) -> new x_right
  - Colophon(signature, style, brush=Brush())
    - draw(draw, x_right, y_top) -> (end_x, end_y)
  - Seal(font_path, font_size=50, size=110, color=(160,30,30), ...)
    - draw(draw, origin)

- chinese_calligraphy.works.Handscroll
  - canvas: ScrollCanvas; margins: Margins
  - title: Title | None; main: MainText; colophon: Colophon | None
  - lead_seal/name_seal: Seal | None; lead_space/tail_space
  - measure_width() -> total width; render() -> PIL.Image; save(path); save_preview(path, segment_index, preview_width)

Convenience facade imports are exposed at the package top-level for the classes above.


## Fonts and the font helper

You must have suitable Chinese fonts installed. The helper chinese_calligraphy.font provides:

- find_font_path(name, extra_dirs=()) -> Optional[str]
- require_font_path(name, extra_dirs=()) -> str  # raises if not found

It scans common OS font directories and can optionally use fontTools to match name records for better accuracy. If a font is not found, provide explicit paths or install the font. Example family names to try include:

- macOS: "PingFang", "Songti SC", "Hiragino Sans GB"
- Windows: "SimSun", "KaiTi", "FangSong"
- Linux: depends on installed CJK fonts (e.g., Noto Serif CJK, WenQuanYi)


## Examples

A full example is available in examples/handscroll.py in the repository. When installing from PyPI, examples are not included in the wheel; clone the repo to run them locally.

```bash
python examples/handscroll.py
```

The script writes handscroll.png to the current directory.


## Compatibility

- Python: 3.10, 3.11, 3.12, 3.13
- OS: macOS, Windows, Linux (Pillow handles platform specifics)
- Dependencies: Pillow>=10.0.0 (runtime), optional fonttools>=4 for improved font lookup


## Development

Build and validate the distribution locally:

```bash
# using hatch
pip install hatch
hatch build

# or using the build frontend
pip install build twine
python -m build
python -m twine check dist/*
```

Run the example while developing:

```bash
python examples/handscroll.py
```


## Publishing to PyPI

- Bump version in pyproject.toml (follow SemVer): 0.1.1, 0.2.0, etc.
- Build artifacts and verify metadata:

```bash
python -m build
python -m twine check dist/*
```

- Upload (be sure ~/.pypirc is configured or provide creds interactively):

```bash
python -m twine upload dist/*
```

- Tag the release in git and push tags:

```bash
git tag v0.1.0 && git push origin --tags
```

## License

MIT © 2025 Mingli Yuan
