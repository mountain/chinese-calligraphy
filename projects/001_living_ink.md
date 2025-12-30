# 项目 001: 墨韵 (The Living Ink) - 详细设计文档

**Status:** Implemented
**Last Updated:** 2025-12-30

## 0. 最佳实践 (Best Practices)

> [!TIP]
> **Recommended Parameters**:
> *   **Dryness**: `0.00` to `0.10`. (Solid Core with natural edge texture)
> *   **Blur**: `0.0` to `0.5`. (Subtle diffusion/halo for semi-sized paper effect)
>
> 經測試，在此範圍內，筆畫核心飽滿，邊緣呈現自然的紙張纖維紋理与微量晕染。超过此范围可能导致过度枯笔或模糊。

## 1. 背景与目标 (Background & Goals)

### 1.1 问题现状：死墨 (The Dead Ink Problem)
目前的实现使用 Pillow 的 `ImageDraw.text` 进行矢量文字渲染。虽然通过仿射变换实现了字形的动态几何变异（Shear/Rotate/Scale），但**像素层面上是均匀填充的**。
生成的文字边缘锐利、颜色均一，视觉上像是在纸上「贴」了黑色的胶带，缺乏毛笔书写特有的：
*   **飞白 (Flying White / Dry Brush Effect)**: 笔锋快速移动或墨少时产生的丝状留白。
*   **毛边 (Rough Edges)**: 墨水渗透宣纸纤维造成的边缘不规则扩散。
*   **墨色变化 (Ink Variance)**: 浓淡干湿的微观纹理。

### 1.2 这个项目的目标 (Goals)
本项目旨在将渲染管线从简单的「几何填充」升级为基于纹理的「物理模拟」，使生成的书法作品具有**“呼吸感”**和**“物质感”**。

---

## 2. 核心设计理念 (Core Design Philosophy)

1.  **从矢量到纹理 (Vector to Texture)**: 不再追求完美平滑的边缘，而是主动引入噪声和不完美。
2.  **分层模拟 (Layered Simulation)**: 将最终的像素看作是 **纸张纹理 (Paper)**、**笔触掩模 (Brush Mask)** 和 **墨水形态 (Ink State)** 交互的结果。
3.  **参数化控制 (Parametric Control)**: 通过 `dryness` (干枯度) 等参数控制物理效果，而非硬编码。

---

## 3. 技术架构 (Technical Architecture)

### 3.1 核心依赖 (Dependencies)
为了实现高效的图像处理与噪声生成，我们需要引入科学计算库：
*   **NumPy**: 用于高效的矩阵操作和像素级处理。
*   **SciPy (`scipy.ndimage`)**: 用于形态学操作（腐蚀/膨胀），这是模拟墨水物理扩散与收缩的关键算法。

### 3.2 模块变更 (Module Architecture)

#### A. 新增 `chinese_calligraphy/noise.py` (Conditional)
负责生成连续的自然噪声，作为纹理的基础。
*   **约束 (Constraint)**: 如果实现代码行数 < 200 行，则合并入 `chinese_calligraphy/utils.py`。如果超过 200 行，则保持独立文件 `noise.py`。
*   **Class `NoiseGenerator`**:
    *   `generate_simplex(width, height, scale, seed)`: 生成 Simplex/Perlin 噪声图（灰度）。
    *   `generate_fiber_texture(width, height)`: 生成模拟宣纸纤维的高频噪声。

#### B. 重构 `chinese_calligraphy/brush.py`
将 `Brush` 类的 `draw_char` 方法彻底重构。
*   **Current**: `Draw Text` -> `Affine Transform` -> `Paste`.
*   **New Pipeline**: `Rasterize` -> `Erode (Physical Simulation)` -> `Texture Mapping` -> `Colorize` -> `Composite`.

#### C. 变更 `chinese_calligraphy/style.py`
在 `Style` 数据类中增加墨韵相关的物理参数。
*   `ink_dryness`: `float` (0.0 - 1.0). 控制飞白的强度。0.0 为饱满浓墨，1.0 为极度枯笔。
*   `ink_uniformity`: `float` (0.0 - 1.0). 控制墨色内部的均匀度。

---

## 4. 详细实现步骤 (Implementation Details)

### 步骤 1: 建立噪声库 (`noise.py`)
我们需要一个确定性的噪声生成器（基于 seed），以确保存档的可复现性。
*   可以利用 `opensimplex` 库（如果允许引入）或基于 `numpy` 实现一个简易的向量化值噪声 (Value Noise) 或分形布朗运动 (fBm)。
*   **关键输出**: 生成一张与字 PATCH 大小相同的灰度图，值域 [0, 1]，代表“墨水附着概率”。

### 步骤 2: 重构渲染管线 (`brush.py` -> `draw_char`)

#### Phase 1: 高分辨率光栅化 (Rasterization)
*   为了保证边缘处理的细腻度，先在 **2倍或4倍** 的分辨率下创建 `Image` 对象。
*   绘制纯白色的文字 Mask。

#### Phase 2: 形态学枯笔模拟 (Morphological Dry Brush)
*   **原理**: 枯笔本质上是墨水未能完全覆盖纸张纤维。
*   **操作**:
    1.  将 Mask 转换为 boolean numpy 数组。
    2.  根据 `style.ink_dryness`，生成随机的噪声 Mask。
    3.  使用 `scipy.ndimage.binary_erosion` 对文字主体进行**条件腐蚀**。即：在噪声值高的区域（代表纸面凸起或拒水），文字像素更容易被“吃掉”。
    4.  对于笔画末端（通常是从左向右书写的右侧，或下侧），可以根据梯度施加更强的腐蚀，模拟运笔末尾的枯竭。

#### Phase 3: 边缘扩散 (Edge Diffusion - Optional)
*   如果模拟“晕染”（湿墨），则使用高斯模糊 (Gaussian Blur) 或 膨胀 (Dilation) 处理 Mask 边缘。
*   本项目一期优先作为“枯笔”实现（即腐蚀为主）。

#### Phase 4: 纹理合成与着色 (Compositing)
*   将处理后的 Mask (Alpha channel) 缩放回原始尺寸 (`Image.Resampling.LANCZOS` 以获得平滑抗锯齿)。
*   生成颜色层：不仅仅是纯色，可以是在 `Style.color` 基础上叠加了微量 RGB 噪声的图层。
*   将 Alpha Mask 应用于颜色层。
*   合成到底图上。

### 步骤 3: 风格参数接入 (`style.py`)
```python
@dataclass(frozen=True)
class Style:
    # ... existing fields ...
    # 新增
    ink_dryness: float = 0.1  # 默认润墨
    blur_sigma: float = 0.0   # 默认无晕染
```

---

## 5. 验证与测试计划 (Verification)

### 5.1 单元测试
*   测试 `noise.py` 的确定性：相同的 seed 必须生成完全相同的噪声矩阵。

### 5.2 视觉验证脚本 (`examples/verify_living_ink.py`)
*   生成一个 5x5 的矩阵。
*   **X轴**: 逐渐增加 `ink_dryness` (从 0.0 到 1.0)。
*   **Y轴**: 逐渐增加 `font_size` (测试不同分辨率下的噪声纹理是否自然)。
*   **预期结果**: 左侧列墨迹饱满圆润，右侧列出现明显的丝状飞白，且边缘破碎自然。

## 6. 未来扩展 (Future Work)
*   **流体动力学模拟**: 真正模拟墨汁在纤维管中的毛细现象（计算量大，作为高级选项目标）。
*   **各种纸张模型**: 定义 `SemianXuan`, `RawXuan` 等不同纸张类，影响墨水的扩散系数。
