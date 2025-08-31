# 🧗‍♂️ 攀岩路线图自动生成器 (Automated Climbing Route Generator)

这是一个基于 GitHub Actions 的全自动攀岩路线图（Topo）生成系统。你只需要在一张攀岩墙的图片上标记出岩点，并在一个JSON文件中定义路线，系统就会自动为你绘制出所有精美的路线图、提交到仓库，并打包成一个ZIP文件方便下载。

## ✨ 核心功能

- **自动化**：只需修改路线定义文件并推送到 `main` 分支，所有图片的生成、压缩和提交过程将自动完成。
- **集中管理**：所有路线都定义在单一的 `routes/all_routes.json` 文件中，管理和维护极为方便。
- **智能识别**：自动从攀岩墙图片中识别岩点编号，并生成坐标文件。
- **精美绘图**：为每条路线生成带起止点、手点顺序、脚点、路线信息和动作流箭头的图片。
- **高效压缩**：生成的PNG图片经过优化和压缩，体积更小，加载更快。
- **方便下载**：所有生成的路线图会自动打包成一个 `.zip` 文件，作为工作流的产物(Artifact)，可一键下载。

## 🚀 工作流程 (How it Works)

本项目的核心是一个 GitHub Actions 工作流 (`.github/workflows/main.yml`)，当 `routes/all_routes.json` 文件或相关脚本被修改并推送到 `main` 分支时，该工作流会被自动触发。

整个流程如下：

1.  **岩点坐标生成 (`generate_coords.py`)**
    -   工作流首先会运行脚本，读取 `images/with_markplus.png` 这张带有标记的攀岩墙图片。
    -   利用 `easyocr` 库识别图片上每个岩点的编号/字母。
    -   生成一份包含所有岩点ID及其(x, y)坐标的 `data/holds.json` 文件。这是后续所有绘图步骤的基础。

2.  **路线图绘制 (`draw_route.py`)**
    -   脚本读取 `routes/all_routes.json` 文件，获取所有路线的定义列表。
    -   对于列表中的**每一条路线**：
        -   在 `images/ori_image.png` (原始底图) 的副本上开始绘制。
        -   根据路线定义中的 `moves` 数组，查找 `data/holds.json` 中对应的手点坐标。
        -   使用不同颜色和形状的圆圈/方框标记出手点、起始点(S)和结束点(F)。
        -   在手点右上角标注清晰的文字（L/R/S/F/B）。
        -   如果定义了 `holds.foot`，则标记出指定的脚点。
        -   绘制箭头，清晰地指示出动作的顺序和方向。
        -   在图片左上角添加标题，包含路线名、难度和作者。
        -   将最终生成的图片进行**量化压缩**，以减小文件体积。
        -   以 `[难度]_[路线名称].png` 的格式 (例如 `V3_Polygon_Puzzle.png`) 保存到 `generated_routes/` 目录下。

3.  **自动提交 (`git-auto-commit-action`)**
    -   工作流会自动将新生成的 `data/holds.json` 文件和 `generated_routes/` 目录下的所有 `.png` 图片提交到你的GitHub仓库。
    -   提交信息为 `"feat(routes): 自动生成所有路线图"`。

4.  **打包与上传 (`zip` & `upload-artifact`)**
    -   将 `generated_routes/` 目录下的所有图片压缩成一个名为 `climbing_routes.zip` 的文件。
    -   将这个ZIP文件作为工作流的**产物 (Artifact)** 上传。

## 📖 如何使用：添加或修改路线

你唯一需要关心和修改的文件就是 `routes/all_routes.json`。

1.  **打开 `routes/all_routes.json` 文件。**
2.  **添加或修改路线**：在 `routes` 数组中，添加一个新的JSON对象，或者修改一个已有的对象。

### 路线JSON结构示例

```json
{
  "routeName": "Purple Valor",
  "difficulty": "V3",
  "author": "ClimbingKoala@xhs",
  "holds": {
    "foot": ["a", "b", "c"]
  },
  "moves": [
    { "hold_id": "61", "type": "start", "hand": "left" },
    { "hold_id": "k", "type": "start", "hand": "right" },
    { "hold_id": "m", "hand": "left" },
    { "hold_id": "128", "hand": "right" },
    { "hold_id": "111", "hand": "left" },
    { "hold_id": "110", "type": "finish", "hand": "both" }
  ]
}
```

-   `routeName`: **(必需)** 路线名称，会显示在图片标题上。
-   `difficulty`: **(必需)** 路线难度，如 "V0", "V1", "V3"。
-   `author`: **(必需)** 定线员或作者的名字。
-   `holds.foot`: 一个数组，包含所有**仅用于这条路线**的额外脚点ID。如果为空 `[]`，则不绘制任何特定脚点。
-   `moves`: **(必需)** 一个包含所有手点动作的数组，**请按顺序排列**。
    -   `hold_id`: **(必需)** 岩点的ID（必须与 `data/holds.json` 中的ID对应）。
    -   `type`: (可选) 标记点的特殊类型。`"start"` 用于起始点，`"finish"` 用于结束点。
    -   `hand`: **(必需)** 指定用哪只手。`"left"` (左手), `"right"` (右手), `"both"` (双手)。

3.  **提交并推送 (Commit & Push)**：将你对 `routes/all_routes.json` 的修改提交并推送到 `main` 分支。
4.  **完成！** GitHub Actions 会接管剩下的一切。稍等片刻，你就可以在仓库的 `generated_routes/` 目录下看到新的路线图，或者在Actions的运行记录页面下载包含所有图片的ZIP压缩包。

## 📂 项目文件结构

```
.
├── .github/
│   ├── scripts/               # 存放所有Python脚本
│   │   ├── generate_coords.py   # 1. 识别岩点坐标
│   │   ├── mark_all_holds.py    # (调试用) 标记所有岩点
│   │   ├── draw_route.py        # 2. 绘制路线图
│   │   └── check_missing_holds.py # (检查用) 检查缺失的岩点
│   └── workflows/
│       └── main.yml           # 核心工作流配置文件
├── data/
│   └── holds.json             # 自动生成的岩点坐标数据
├── generated_routes/          # 自动生成的路线图存放处
│   ├── V0_Green_Highway.png
│   └── ...
├── images/
│   ├── ori_image.png          # 用于绘图的原始底图
│   └── with_markplus.png      # 用于OCR识别的带标记图片
├── routes/
│   └── all_routes.json        # 唯一需要你手动编辑的路线定义文件
└── README.md                  # 就是你正在看的这个文件
```

## 🎨 外观定制

想要修改路线图的样式（如颜色、大小、字体）？

所有样式都定义在 `.github/scripts/draw_route.py` 文件顶部的 `STYLE_CONFIG` 字典中。你可以直接修改里面的值来改变最终图片的视觉效果。

```python
# .github/scripts/draw_route.py

STYLE_CONFIG = {
    'start':       {'outline': (76, 175, 80, 255), ...},
    'finish':      {'outline': (244, 67, 54, 255), ...},
    # ...
    'radius': 18,
    'outline_width': 6,
    'font_size': 100, # 岩点文字大小
    # ...
}
```
