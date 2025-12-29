# examples/handscroll.py

from chinese_calligraphy import (
    Style, Brush, ScrollCanvas, Margins, SegmentSpec,
    Title, MainText, Colophon, Seal, Handscroll
)
from chinese_calligraphy.font import require_font_path


def main():
    FONT_PATH = require_font_path("FZWangDXCJF")     # 正文字体名
    SEAL_FONT_PATH = require_font_path("FZZJ-MZFU")  # 印章字体名

    TITLE_TEXT = "愛蓮說"
    TEXT_CONTENT = r"""
水陸草木之花可愛者甚蕃晉陶淵明獨愛菊自李唐來世人盛愛牡丹
予獨愛蓮之出淤泥而不染濯清漣而不妖中通外直不蔓不枝香遠益清亭亭淨植可遠觀而不可褻玩焉
予謂菊花之隱逸者也牡丹花之富貴者也蓮花之君子者也噫菊之愛陶後鮮有聞蓮之愛同予者何人牡丹之愛宜乎眾矣
"""
    SIGNATURE = "乙巳仲冬 博德仿王鐸意書 於靈境山房"

    canvas = ScrollCanvas(height=2800, bg=(245, 240, 225))
    margins = Margins(top=200, bottom=200, right=250, left=250)

    title_style = Style(font_path=FONT_PATH, font_size=132, color=(20, 20, 20), char_spacing=15, col_spacing=240)
    main_style  = Style(font_path=FONT_PATH, font_size=110, color=(20, 20, 20), char_spacing=10, col_spacing=160)
    sig_style   = Style(font_path=FONT_PATH, font_size=66,  color=(60, 60, 60), char_spacing=5,  col_spacing=160)

    title = Title(
        text=TITLE_TEXT,
        style=title_style,
        brush=Brush(seed=1, char_jitter=(1, 1)),
        extra_gap_after=220,
    )

    main = MainText(
        text=TEXT_CONTENT,
        style=main_style,
        segment=SegmentSpec(columns_per_segment=14, segment_gap=260),
        # 不传 brush 则用默认 factory（包含“之”三态与惯性）
    )

    colophon = Colophon(
        signature=SIGNATURE,
        style=sig_style,
        brush=Brush(seed=3, char_jitter=(0, 0)),
    )

    name_seal = Seal(
        font_path=SEAL_FONT_PATH,
        text_grid=[("博", 0, 0), ("德", 0, 1), ("制", 1, 0), ("印", 1, 1)],
    )
    lead_seal = Seal(
        font_path=SEAL_FONT_PATH,
        border_width=6,
        text_grid=[("雲", 0, 0), ("境", 0, 1), ("清", 1, 0), ("章", 1, 1)],
    )

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

if __name__ == "__main__":
    main()
