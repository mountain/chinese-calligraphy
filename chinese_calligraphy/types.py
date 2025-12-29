# chinese_calligraphy/types.py

# 【繁】基礎型別與別名：避免跨模組循環 import，保持 API 清爽
# [EN] Core type aliases: avoid circular imports across modules and keep the API clean

from __future__ import annotations

from typing import Tuple

# =========================
# 【基本幾何型別 / Basic geometry types】
# =========================

# 【繁】RGB 顏色（0~255）
# [EN] RGB color (0~255)
Color = Tuple[int, int, int]

# 【繁】整數像素座標點 (x, y)
# [EN] Integer pixel coordinate point (x, y)
Point = Tuple[int, int]


# =========================
# 【字形變體模板 / Glyph variant templates】
# =========================

# 【繁】變體模板：基準 rot/shear/scale/anis_y + 每個參數的可擾動幅度
# [EN] Variant template: base rot/shear/scale/anis_y + per-parameter noise amplitude
#
# 欄位順序 / Field order:
#   base_rot_deg, base_shear_x, base_scale, base_anis_y,
#   amp_rot_deg,  amp_shear_x,  amp_scale,  amp_anis_y
#
# 註 / Notes:
# - base_rot_deg：旋轉角度（度）
# - base_shear_x：x 方向仿射剪切係數（欹側）
# - base_scale：等比縮放
# - base_anis_y：y 方向非等比伸縮（>1 拉長，<1 壓扁）
# - amp_*：對應參數的隨機擾動幅度
VariantTemplate = Tuple[float, float, float, float, float, float, float, float]
