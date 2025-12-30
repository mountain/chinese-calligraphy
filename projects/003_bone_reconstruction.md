# 计划三：拆骨重塑 (The "Bone Reconstruction" Plan)

**难度：** ⭐⭐⭐⭐⭐ (极难)
**针对痛点：** "僵骨" (The Rigid Bone Problem)
**核心目标：** 深入字体文件内部，直接修改贝塞尔曲线控制点，实现非均匀形变，从而模拟真正的“运笔”而非“图片旋转”。

**实施步骤：**

1. **升级依赖**
* 将 `fontTools` 从可选依赖提升为核心依赖。

2. **开发 `VectorBrush` 类**
* 不再使用 Pillow 的 `ImageFont.truetype` 直接渲染。
* **提取路径：** 使用 `fontTools.pens.recordingPen` 读取字符的矢量路径。
* **施加非均匀扰动：**
* 遍历路径上的所有点（on-curve 和 off-curve）。
* 定义变形场（Deformation Field）：例如，定义一个函数 `f(x, y)`，使得字的上半部分向左倾斜程度大，下半部分小（模拟行书的势）。
* **局部扭曲：** 随机选取路径上的某一段（代表某一笔画），对其施加微小的位移，模拟手抖导致笔画位置的偏差（而不是整个字歪了）。

3. **矢量光栅化 (Rasterization)**
* 使用 `fontTools.pens.freetypePen` 或 `pathops` 将修改后的路径重新光栅化为 Pillow 的 Image 对象。
* 这一步将替代原有的 `Brush.draw_char` 核心渲染逻辑。

**预期效果：**

这是质的飞跃。你将能够生成标准字库中不存在的字形变体（例如：由于运笔过快导致的笔画连带、或者独特的结体倾斜），彻底摆脱“印刷体”的影子。
