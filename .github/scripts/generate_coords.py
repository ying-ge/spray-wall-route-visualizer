import argparse
import json
from pathlib import Path
import easyocr
import cv2
import numpy as np
import sys

def generate_coords(image_path_str: str, output_path_str: str):
    """
    从给定的图片中识别所有字母和数字标记，并将其中心坐标保存为 JSON 文件。
    这个版本是通用的，不包含任何特定于墙体的规则。
    """
    image_path = Path(image_path_str)
    output_path = Path(output_path_str)

    # 1. 检查输入图片是否存在
    if not image_path.exists():
        print(f"错误: 图片文件未找到 at {image_path}", file=sys.stderr)
        sys.exit(1)

    # 2. 初始化 EasyOCR 读取器
    print("正在初始化 EasyOCR...")
    reader = easyocr.Reader(['en'], gpu=False) # 在 GitHub Actions 环境中使用 CPU

    # 3. 读取图片
    print(f"正在读取图片: {image_path}")
    image = cv2.imread(str(image_path))
    if image is None:
        print(f"错误: 无法加载图片 at {image_path}", file=sys.stderr)
        sys.exit(1)

    # 4. 使用 EasyOCR 进行文字识别
    print("正在识别图片中的文字...")
    results = reader.readtext(image)

    # 5. 处理识别结果并提取坐标
    holds_coords = {}
    print(f"识别到 {len(results)} 个文本框，正在处理...")

    for (bbox, text, prob) in results:
        # 清理文本：去除所有非字母和非数字的字符，并转为小写。
        # 例如 "#a" -> "a", "123." -> "123", "X-Y" -> "xy"
        # 这样做使脚本非常通用，不依赖于任何特定的标记格式。
        cleaned_text = ''.join(filter(str.isalnum, text)).lower()
        
        if cleaned_text:
            # 计算边界框的中心点 (保留您版本中更精确的 np.mean 方法)
            center_x = int(np.mean([point[0] for point in bbox]))
            center_y = int(np.mean([point[1] for point in bbox]))

            holds_coords[cleaned_text] = {'x': center_x, 'y': center_y}
            # print(f"找到岩点: {cleaned_text} -> 坐标: ({center_x}, {center_y})")

    # 6. 确保输出目录存在
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 7. 将结果写入 JSON 文件 (保留您版本中的格式)
    print(f"处理完成，正在将 {len(holds_coords)} 个岩点坐标写入: {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(holds_coords, f, indent=2, sort_keys=True)

    print("岩点坐标生成完毕！")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="从图片中生成岩点坐标。")
    parser.add_argument('--image_path', type=str, required=True, help='输入图片的路径。')
    parser.add_argument('--output_path', type=str, required=True, help='输出 JSON 文件的路径。')
    
    args = parser.parse_args()
    
    generate_coords(args.image_path, args.output_path)
