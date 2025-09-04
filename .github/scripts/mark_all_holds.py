import json
import cv2
from pathlib import Path
import argparse
import sys

def main(wall_dir_str: str):
    """
    为一个指定的墙体生成调试图片，标记出所有已识别的岩点坐标。
    这是一个本地调试工具。
    """
    wall_dir = Path(wall_dir_str)
    
    # 1. 使用动态路径
    holds_file = wall_dir / "output/data/holds.json"
    img_file = wall_dir / "image_marked.png"  # 使用带标记的图片作为底图更直观
    output_file = wall_dir / "output/debug_all_holds_marked.png"

    # 2. 检查文件是否存在
    if not holds_file.exists():
        print(f"错误: 岩点坐标文件不存在 '{holds_file}'", file=sys.stderr)
        sys.exit(1)
    if not img_file.exists():
        print(f"错误: 标记图片不存在 '{img_file}'", file=sys.stderr)
        sys.exit(1)

    # 3. 加载数据和图片
    print(f"正在加载坐标: {holds_file}")
    with open(holds_file, "r", encoding="utf-8") as f:
        holds = json.load(f)

    print(f"正在加载图片: {img_file}")
    img = cv2.imread(str(img_file))
    if img is None:
        print(f"错误: 无法读取图片 {img_file}", file=sys.stderr)
        sys.exit(1)

    # 4. 绘制所有岩点 (核心逻辑保持不变)
    print(f"正在图片上标记 {len(holds)} 个岩点...")
    for hold_id, coord in holds.items():
        x, y = coord["x"], coord["y"]
        # 画一个明亮的圈来高亮显示识别出的中心点
        cv2.circle(img, (x, y), 20, (0, 255, 255), 3)
        # 标注识别出的编号
        cv2.putText(img, hold_id, (x + 25, y - 25), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)

    # 5. 保存输出文件
    output_file.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_file), img)
    print(f"✅ 调试图片已成功生成: {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="生成一张调试图片，标记出指定墙体的所有已识别岩点。")
    parser.add_argument("--wall_dir", required=True, help="需要处理的墙体目录路径 (例如: 'walls/spray_wall')")
    args = parser.parse_args()
    
    main(args.wall_dir)
