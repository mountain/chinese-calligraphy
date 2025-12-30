# examples/couplet.py

from chinese_calligraphy import Brush, Couplet, Seal, Style
from chinese_calligraphy.font import find_font_path, require_font_path


def main() -> None:
    font_name = "FZWangDXCJF"
    if not find_font_path(font_name):
        font_name = "KaiTi"

    font_path = require_font_path(font_name)
    seal_font = find_font_path("FZZJ-MZFU") or font_path

    right_text = "一肩風雪吟詩苦"
    left_text = "滿紙冰霜入骨清"
    header_text = "自甘其寒"

    # 落款
    # 上联（右）：通常写时间、地点、或赠予对象
    # 下联（左）：写作者名、斋号
    colophon_r = "乙巳新春試筆"
    colophon_l = "博德書於靈境山房"

    # 3. 样式
    style = Style(
        font_path=font_path,
        font_size=220,  # 字号加大
        color=(20, 20, 20),
        char_spacing=10,  # 字距紧凑更有气势
        col_spacing=200,
    )

    brush = Brush(
        seed=2025,
        char_jitter=(3, 3),  # 稍微增加一点抖动
        var_scale=0.08,  # 增加大小变化，让字不那么死板
        var_rotate_deg=1.5,
    )

    # 印章
    seal = Seal(font_path=seal_font, text_grid=[("博", 0, 0), ("德", 0, 1)], size=100, color=(140, 30, 30))

    # 4. 生成
    # 注意：width 设为 450，font_size 220，这样字占纸面约 50%，加上落款正好
    couplet = Couplet(
        text_right=right_text,
        text_left=left_text,
        text_header=header_text,
        colophon_right=colophon_r,  # 加上落款
        colophon_left=colophon_l,  # 加上落款
        style=style,
        brush=brush,
        width=600,  # 纸张变窄，聚焦视觉
        height=2400,
        header_height=400,
        seal_left=seal,  # 印章通常盖在下联落款后
    )

    print("Generating corrected couplet...")
    couplet.save_preview("couplet.png")
    print("Saved couplet.png")


if __name__ == "__main__":
    main()
