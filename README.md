# Chinese Calligraphy (Python API)

A Pythonic interface for composing and rendering traditional Chinese calligraphy works using Pillow. Model whole works like handscrolls, vertical couplets (with optional horizontal header), and folding fans, with title, main text, colophon, and seals; tune style and brush behavior for organic variation.

![Preview handscroll](https://raw.githubusercontent.com/mountain/chinese-calligraphy/main/handscroll_small.png)

- Components: Title, MainText, Colophon, Seal
- Layout: handscroll canvas, couplet sheet, fan radial layout; margins, segmentation (columns per segment + inter-segment gap)
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

Or render a couplet preview:

```python
from chinese_calligraphy import Style, Brush, Couplet, Seal
from chinese_calligraphy.font import find_font_path, require_font_path

# Choose fonts on your system
font_path = require_font_path("FZWangDXCJF")
seal_font = find_font_path("FZZJ-MZFU") or font_path

style = Style(font_path=font_path, font_size=220, color=(20, 20, 20), char_spacing=10, col_spacing=200)
brush = Brush(seed=2025, char_jitter=(3, 3), var_scale=0.08, var_rotate_deg=1.5)

couplet = Couplet(
    text_right="一肩風雪吟詩苦",
    text_left="滿紙冰霜入骨清",
    text_header="自甘其寒",
    colophon_right="乙巳新春試筆",
    colophon_left="博德書於靈境山房",
    style=style,
    brush=brush,
    width=600,
    height=2400,
    header_height=400,
    seal_left=Seal(font_path=seal_font, text_grid=[("博",0,0),("德",0,1)], size=100, color=(140,30,30))
)

couplet.save_preview("couplet.png")
```

This writes a white-background preview image that lays out the left/right scrolls and optional header together as couplet.png.

Or render a folding fan:

```python
from chinese_calligraphy import Style, Brush, Fan
from chinese_calligraphy.font import require_font_path

# Choose a Chinese font available on your system
font_path = require_font_path("FZWangDXCJF")

# Main text and colophon (the colophon style is auto-derived if not provided)
text = "人閑桂花落夜靜春山空月出驚山鳥時鳴春澗中"
colophon = "乙巳仲冬錄摩詰詩於靈境山房"

style = Style(
    font_path=font_path,
    font_size=120,
    color=(20, 20, 20),
    char_spacing=10,
    # In Fan, col_spacing controls angular step between columns
    col_spacing=220
)
brush = Brush(seed=2025, char_jitter=(2, 2), var_rotate_deg=1.2, var_scale=0.06)

fan = Fan(
    text=text,
    colophon=colophon,
    style=style,
    brush=brush,
    width=2400,
    height=1400,
    angle_span=130,
)

fan.save("fan.png")
```

This writes a curved fan-face composition as fan.png. The colophon is rendered with a slightly smaller, auto-generated style unless you provide colophon_style explicitly.


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

- chinese_calligraphy.works.Couplet
  - text_right, text_left, text_header=None; colophon_right=None, colophon_left=None
  - style: Style (required); brush: Brush (optional)
  - width, height; header_height; header_width=None; margins; bg_color
  - seal_right/left/header: Seal | None
  - render() -> (Image right, Image left, Optional[Image header]); save(prefix) -> writes prefix_right.png/prefix_left.png/[prefix_header.png]; save_preview(path, gap=50)

- chinese_calligraphy.works.Fan
  - text, colophon=None
  - style: Style (required); colophon_style: Style | None (auto-derived ~55% size if omitted)
  - brush: Brush (optional)
  - width, height; center_x, center_y
  - radius_outer, radius_inner; angle_span
  - bg_color
  - render() -> PIL.Image; save(path)

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

Full examples are available in the repository under examples/. When installing from PyPI, examples are not included in the wheel; clone the repo to run them locally.

Handscroll:

```bash
python examples/handscroll.py
```

Generates handscroll.png.

Couplet:

```bash
python examples/couplet.py
```

Generates couplet.png (a preview sheet with header and the two vertical scrolls). To export individual scroll images instead, call couplet.save("couplet") which writes couplet_right.png, couplet_left.png, and optionally couplet_header.png.

Fan:

```bash
python examples/fan.py
```

Generates fan.png.


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
