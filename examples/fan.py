# examples/fan_demo.py

import os
import sys

# 確保能導入本地模組
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from chinese_calligraphy import Brush, Fan, Style
from chinese_calligraphy.font import require_font_path


def main() -> None:
    font_path = require_font_path("FZWangDXCJF")

    # 王維《鳥鳴澗》
    # 正文：大字
    text_content = "人閑桂花落夜靜春山空月出驚山鳥時鳴春澗中"

    # 落款：通常包含年號、作者、齋號
    # 這裡會被 Fan 類自動縮小字號處理
    colophon_content = "乙巳仲冬錄摩詰詩於靈境山房"

    # 正文樣式
    style = Style(
        font_path=font_path,
        font_size=120,  # 正文大字
        color=(20, 20, 20),
        char_spacing=10,
        col_spacing=240,  # 這裡會轉化為角度
    )

    brush = Brush(seed=2025, char_jitter=(2, 2), var_rotate_deg=1.2, var_scale=0.06)

    # 創建扇面
    fan_work = Fan(
        text=text_content,
        colophon=colophon_content,  # 傳入落款
        style=style,
        brush=brush,
        # 參數已在類中優化，使用默認即可，或微調：
        width=2400,
        height=1400,
        angle_span=130,
    )

    print("Generating corrected fan calligraphy (with proper colophon)...")
    fan_work.save("fan.png")
    print("Saved to fan.png")


if __name__ == "__main__":
    main()
