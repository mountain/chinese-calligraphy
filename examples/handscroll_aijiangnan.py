# examples/handscroll_aijiangnan.py

from chinese_calligraphy import (
    Style, Brush, ScrollCanvas, Margins, SegmentSpec,
    Title, MainText, Colophon, Seal, Handscroll
)
from chinese_calligraphy.font import require_font_path


def main():
    FONT_PATH = require_font_path("FZWangDXCJF")     # 正文字体名
    SEAL_FONT_PATH = require_font_path("FZZJ-MZFU")  # 印章字体名

    TITLE_TEXT = "哀江南賦序"
    TEXT_CONTENT = r"""
粵以戊辰之年建亥之月大盜移國金陵瓦解
余乃竄身荒谷公私塗炭華陽奔命有去無歸
中興道消窮於甲戌三日哭於都亭三年囚於別館
天道周星物極不反傅燮之但悲身世無所求生
袁安之每念王室自然流涕昔桓君山之志事
杜元凱之生平竝有著書咸能自序
潘岳之文采始述家風陸機之詞賦先陳世德
信年始二毛即逢喪亂藐是流離至於暮齒
燕歌遠別悲不自勝楚老相逢泣將何及
畏南山之雨忽踐秦庭讓東海之濱遂餐周粟
下亭漂泊高橋羈旅楚歌非取樂之方
魯酒無忘憂之用追為此賦聊以記言
不無危苦之辭惟以悲哀為主
日暮途遠人間何世將軍一去大樹飄零
壯士不還寒風蕭瑟荊璧睨柱受連城而見欺
載書橫階捧珠盤而不定鍾儀君子
入就南冠之囚季孫行人留守西河之館
申包胥之頓地碎之以首蔡威公之淚
盡加之以血釣臺移柳非玉關之可望
華亭鶴唳豈河橋之可聞
孫策以天下為三分眾裁一旅項籍用江東之子弟
人惟八千遂乃分裂山河宰割天下豈有百萬義師
一朝卷甲芟夷斬伐如草木焉江淮無涯岸之阻
亭壁無藩籬之固頭會箕斂者合從締交
鉏耰棘矜者因利乘便
將非江錶王氣終於三百年乎
是知併吞六合不免軹道之災混一車書
無救平陽之禍嗚呼山嶽崩頹既履危亡之運
春秋迭代必有去故之悲
天意人事可以悽愴傷心者矣
況復舟檝路窮星漢非乘槎可上風飈道阻蓬萊
無可到之期窮者欲達其言勞者須歌其事
陸士衡聞而撫掌是所甘心
張平子見而陋之固其宜矣
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
        text_grid=[("大", 0, 0), ("宗", 0, 1), ("伯", 1, 0), ("印", 1, 1)],
    )
    lead_seal = Seal(
        font_path=SEAL_FONT_PATH,
        border_width=6,
        text_grid=[("雲", 0, 0), ("境", 0, 1), ("閒", 1, 0), ("章", 1, 1)],
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

    scroll.save("handscroll_aijiangnan.png")

if __name__ == "__main__":
    main()
