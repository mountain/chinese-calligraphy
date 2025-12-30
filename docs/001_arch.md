# 架構哲學：數字書法的五層結構

# Architecture Philosophy: The Five-Layer Structure of Digital Calligraphy

本項目不僅僅是一個圖像生成工具，它是中國古代書法理論的數字化重構。我們採用了「五層結構」（制、文、書、行、境）作為核心架構理念 。這種分層設計確保了系統的**模塊化（Modularity）**與**解耦（Decoupling）**，使得開發者可以在任意層級獨立進行優化或擴展。

This project is more than an image generation tool; it is a digital reconstruction of traditional Chinese calligraphy theory. We adopt the "Five-Layer Structure" (Zhi, Wen, Shu, Xing, Jing) as our core architectural philosophy. This layered design ensures **modularity** and **decoupling**, allowing developers to independently optimize or extend any specific layer.

---

## 1. 制 (Zhi) —— System & Constraints

**物理規約與格式系統 / The Physical Constraints & Layout System**

### 理論 (Theory)

「制」規定了書寫的物質邊界與社會形式。在書法史上，它體現為詔版、碑刻、手卷或扇面等具體形制，同時也包含了紙張、筆墨等工具材料的物理限制 。正如秦詔版受限於金屬冶鑄工藝而呈現方折之姿，「制」是書法存在的物質前提與底層邏輯 。

*Zhi* defines the material boundaries and social forms of writing. In the history of calligraphy, it manifests as specific formats like imperial edicts, steles, handscrolls, or fans, while also encompassing the physical constraints of tools such as paper and ink. Just as the Qin dynasty edict plates took on a square and angular form due to metal casting limitations, *Zhi* serves as the material prerequisite and underlying logic of calligraphy's existence.

### 實現 (Implementation)

在代碼庫中，這一層對應於 `works/` 目錄下的容器類（如 `Handscroll`, `Fan`, `Couplet`）以及 `layout.py` 中的基礎定義 。它們負責定義畫布的物理尺寸（如 `ScrollCanvas`）、處理頁面留白（`Margins`），以及執行從右向左、從上到下的傳統排版邏輯 。例如，`Fan` 類通過幾何計算模擬了扇面的輻射狀排版約束 。

In the codebase, this layer corresponds to container classes in the `works/` directory (e.g., `Handscroll`, `Fan`, `Couplet`) and the foundational definitions in `layout.py`. They are responsible for defining the physical dimensions of the canvas (e.g., `ScrollCanvas`), handling page margins (`Margins`), and executing the traditional layout logic flowing from right to left and top to bottom. For instance, the `Fan` class simulates the radial layout constraints of a folding fan through geometric calculations.

### 🔧 擴展性指南 (Extensibility Guide)

* **獨立改進**：您可以增加新的形制類。例如，實現**「冊頁 (Album Leaf)」**或**「團扇 (Round Fan)」**，只需關注幾何計算與佈局規則，無需觸碰筆觸或文字渲染邏輯。
* **協同改進**：與渲染層配合，引入「材質模擬」（如宣紙的紋理映射與吸水性模擬），使「制」的約束更具物理真實感 。


* **Independent Improvement**: You can add new format classes. For example, implementing **"Album Leaf"** or **"Round Fan"** requires focusing only on geometric calculations and layout rules, without touching the brushwork or text rendering logic.
* **Collaborative Improvement**: Collaborate with the rendering layer to introduce "Material Simulation" (e.g., texture mapping and water absorbency of Xuan paper), making the constraints of *Zhi* more physically realistic.

---

## 2. 文 (Wen) —— Content & Semantics

**語義驅動與文本結構 / Semantics-Driven Content Structure**

### 理論 (Theory)

「文」是書法的內容核心與靈魂。蘇軾曾提出「書文並茂」，強調書法是文學內容的視覺延伸 。不同的文本屬性（如莊重的詔令、悲憤的祭文、閒適的詩札）決定了書寫的基調與節奏 。

*Wen* is the content core and soul of calligraphy. Su Shi once proposed the "Integration of Calligraphy and Text," emphasizing that calligraphy is the visual extension of literary content. Different text attributes (such as solemn edicts, indignant requiems, or leisurely poems) determine the tone and rhythm of the writing.

### 實現 (Implementation)

代碼通過 `elements.py` 中的組件類來區分文本的語義角色：`Title`（引首）、`MainText`（正文）和 `Colophon`（落款）。系統根據這些角色自動調整排版策略。例如，`Colophon` 通常會自動縮小字號以示謙卑，並安排在正文之後 。這種設計將「文」的尊卑秩序轉化為視覺上的自動化規則。

The code distinguishes semantic roles of text via component classes in `elements.py`: `Title` (Lead Title), `MainText` (Main Body), and `Colophon` (Inscription/Signature). The system automatically adjusts layout strategies based on these roles. For example, `Colophon` is usually automatically resized to a smaller font to show humility and placed after the main text. This design translates the hierarchical order of *Wen* into visual automation rules.

### 🔧 擴展性指南 (Extensibility Guide)

* **獨立改進**：您可以接入 **LLM (大語言模型)**，自動生成符合平仄對仗的「對聯」文本，或為生成的畫作撰寫相應的「題跋」。
* **協同改進**：引入**情感分析 (Sentiment Analysis)**。分析輸入文本的情感傾向（如悲、喜、怒），並將結果傳遞給下一層（書/行），自動調整筆觸的抖動參數與墨色濃淡，模擬顏真卿《祭侄文稿》中因悲憤而產生的筆觸變化 。


* **Independent Improvement**: You can integrate an **LLM (Large Language Model)** to automatically generate "Couplet" text that conforms to tonal patterns and parallelism, or to compose appropriate "Colophons" for the generated artwork.
* **Collaborative Improvement**: Introduce **Sentiment Analysis**. Analyze the emotional inclination of the input text (e.g., sadness, joy, anger) and pass the results to the next layers (Shu/Xing) to automatically adjust brush jitter parameters and ink density, simulating the brushwork changes caused by grief and indignation seen in Yan Zhenqing's *Requiem to My Nephew*.

---

## 3. 書 (Shu) —— Script & Morphology

**字形形態與參數化排版 / Script Morphology & Parametric Typography**

### 理論 (Theory)

「書」層聚焦於字體演變與形態學。它涵蓋了字體風格（如正書的法度與行草的放逸）以及特定字形的微觀變異 。在書法生態中，同一個字在不同語境下會呈現不同面貌，體現了字形的動態生命力 。

The *Shu* layer focuses on script evolution and morphology. It covers font styles (such as the strict rules of standard script versus the freedom of running-cursive script) and the microscopic variations of specific glyphs. In the ecology of calligraphy, the same character can take on different appearances in different contexts, embodying the dynamic vitality of glyphs.

### 實現 (Implementation)

核心實現位於 `font.py` 的字體加載機制與 `Brush` 類中的模板系統 。特別是 `brush.py` 中的 `zhi_templates` 與 `pick_zhi_variant` 函數，實現了基於上下文（Context-aware）的「之」字三態模型（穩態、流動、縱勢）。這展示了代碼如何打破傳統字庫的靜態限制，模擬書法中「同字不同形」的藝術特徵。

The core implementation lies in the font loading mechanism of `font.py` and the template system in the `Brush` class. Specifically, the `zhi_templates` and `pick_zhi_variant` functions in `brush.py` implement a context-aware three-state model for the character "Zhi" (stable, flowing, vertical). This demonstrates how code can break the static limitations of traditional font libraries to simulate the artistic feature of "same character, different forms" in calligraphy.

### 🔧 擴展性指南 (Extensibility Guide)

* **獨立改進**：字體設計師可以貢獻更豐富的**字體庫**；開發者可以擴展**「變異模板庫」**，讓更多漢字（如「而」、「也」等高頻虛詞）擁有動態變體，而不僅僅局限於「之」字。
* **協同改進**：與「行」層結合，開發**矢量筆畫生成 (Vector Stroke Generation)** 引擎，替代目前的基於字體文件的渲染方式，實現真正的「數字造字」，模擬筆鋒在紙面上的物理擴散。
* **Independent Improvement**: Font designers can contribute richer **font libraries**; developers can extend the **"Variation Template Library"** to endow more Chinese characters (such as high-frequency function words like "Er" and "Ye") with dynamic variants, not limited to the character "Zhi".
* **Collaborative Improvement**: Collaborate with the *Xing* layer to develop a **Vector Stroke Generation** engine, replacing the current font-file-based rendering method to achieve true "digital character creation" that simulates the physical diffusion of the brush tip on paper.

---

## 4. 行 (Xing) —— Action & Process

**時空過程與擬人化算法 / Spatiotemporal Process & Humanization Algorithms**

### 理論 (Theory)

「行」不僅指書寫動作，更指作品在被觀看時引發的時空體驗。書法是時間的軌跡，包含了書寫者的慣性、呼吸節奏以及身體的隨機性 。從手卷的「散點透視」到筆觸的連帶，體現了時間的流動 。

*Xing* refers not only to the action of writing but also to the spatiotemporal experience triggered when the work is viewed. Calligraphy is a trace of time, encompassing the writer's inertia, breathing rhythm, and physical randomness. From the "scattered perspective" of handscrolls to the connection between brushstrokes, it embodies the flow of time.

### 實現 (Implementation)

這是 `Brush` 類的核心算法邏輯 。我們使用**隨機遊走 (Random Walk)** 和 **阻尼系統 (Damping System)**（由 `col_drift_damping` 參數控制）來模擬書寫時列級的慣性漂移；使用 `char_jitter` 模擬手部的高頻微顫 。代碼並非簡單的像素排列，而是模擬了一個動態的「生長」過程，每一列的坐標都受到上一列慣性的影響。

This is the core algorithmic logic of the `Brush` class. We use **Random Walk** and a **Damping System** (controlled by the `col_drift_damping` parameter) to simulate the column-level inertial drift during writing, and `char_jitter` to simulate high-frequency micro-tremors of the hand. The code is not a simple arrangement of pixels but simulates a dynamic "growth" process, where the coordinates of each column are influenced by the inertia of the previous one.

### 🔧 擴展性指南 (Extensibility Guide)

* **獨立改進**：這是一個純算法層。您可以引入 **Perlin Noise** 或更複雜的**物理引擎**來優化筆觸軌跡的自然度，甚至模擬書寫速度對線條粗細的影響。
* **協同改進**：可以記錄生成的坐標序列數據，導出為動畫格式，展示「書寫的過程」，讓觀者能像觀看電影長鏡頭一樣體驗作品的生成 。


* **Independent Improvement**: This is a purely algorithmic layer. You can introduce **Perlin Noise** or more complex **Physics Engines** to optimize the naturalness of brush trajectories, or even simulate the effect of writing speed on line thickness.
* **Collaborative Improvement**: You can record the generated coordinate sequence data and export it as an animation, displaying the "process of writing" so that viewers can experience the creation of the work like watching a long-take film shot.

---

## 5. 境 (Jing) —— Realm & Aesthetic Goal

**整體氛圍與風格遷移 / Aesthetic Realm & Style Transfer**

### 理論 (Theory)

「境」是前四層綜合作用後生成的終極審美場域，是作品傳遞的「氣韻」與「意境」 。無論是廟堂之高的莊嚴，還是山林之遠的逍遙，都是技術與內容共振的結果 。

*Jing* is the ultimate aesthetic field generated by the comprehensive interaction of the previous four layers, representing the "Spirit Resonance" and "Atmosphere" conveyed by the work. Whether it is the solemnity of the imperial court or the carefree nature of the distant mountains and forests, it is the result of the resonance between technique and content.

### 實現 (Implementation)

在軟件中，這體現為**參數配置 (Configuration)** 與**最終渲染 (Final Rendering)**。通過 `Style` 類（控制字距、列距、字號）和 `Brush` 類（控制抖動幅度、變異率、墨色）的組合配置，生成不同風格的作品 。用戶可以通過調整種子數 (`seed`) 和風格參數，探索不同的審美邊界。

In software, this manifests as **Configuration** and **Final Rendering**. Through the combined configuration of the `Style` class (controlling character spacing, column spacing, font size) and the `Brush` class (controlling jitter amplitude, variation rate, ink color), works of different styles are generated. Users can explore different aesthetic boundaries by adjusting the `seed` and style parameters.

### 🔧 擴展性指南 (Extensibility Guide)

* **獨立改進**：建立**「風格預設庫 (Style Presets)」**。例如定義一套 `WangXizhi_Style`（王羲之風）或 `YanZhenqing_Style`（顏真卿風）的參數包，方便用戶一鍵調用，體驗不同的書法意境。
* **協同改進**：引入 **AI 審美評估 (AI Aesthetic Evaluation)**，作為一個「批評家代理 (Critic Agent)」，自動調整前四層的參數，直到生成的作品達到某種「意境」標準（如「雄強」或「飄逸」）。
* **Independent Improvement**: Establish a **"Style Presets Library"**. For example, define a set of parameter packages for `WangXizhi_Style` or `YanZhenqing_Style`, allowing users to apply them with one click and experience different calligraphic realms.
* **Collaborative Improvement**: Introduce **AI Aesthetic Evaluation** as a "Critic Agent" to automatically adjust the parameters of the previous four layers until the generated work meets certain "aesthetic realm" standards (such as "Vigorous" or "Elegant").