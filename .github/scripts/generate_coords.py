import os
if os.path.exists("data/holds.json"):
    print("data/holds.json 已存在，跳过自动生成。")
    exit(0)
    
import cv2
import easyocr
import json
import numpy as np
import argparse
import os
import re

def extract_hold_coordinates(image_path, output_path):
    """
    从给定的图片中识别岩点标记，并将其中心坐标保存为 JSON 文件。

    Args:
        image_path (str): 输入图片的路径。
        output_path (str): 输出 JSON 文件的路径。
    """
    # 1. 初始化 EasyOCR 读取器
    # 我们只关心英文和数字，所以指定 'en'
    print("正在初始化 EasyOCR...")
    reader = easyocr.Reader(['en'], gpu=False) # 在 GitHub Actions 环境中使用 CPU

    # 2. 读取图片
    print(f"正在读取图片: {image_path}")
    if not os.path.exists(image_path):
        print(f"错误: 图片文件未找到 at {image_path}")
        return
    
    image = cv2.imread(image_path)
    if image is None:
        print(f"错误: 无法加载图片 at {image_path}")
        return

    # 3. 使用 EasyOCR 进行文字识别
    print("正在识别图片中的文字...")
    results = reader.readtext(image)

    # 4. 处理识别结果并提取坐标
    holds_coords = {}
    print(f"识别到 {len(results)} 个文本框，正在处理...")

    # 正则表达式匹配 #a, #b, ..., #z 和 #1, #2, ..., #140
    pattern = re.compile(r'^#([a-z]|[1-9][0-9]?|1[0-3][0-9]|140)$')

    for (bbox, text, prob) in results:
        # 清理识别出的文本
        clean_text = text.strip().lower()
        
        match = pattern.match(clean_text)
        if match:
            hold_id = match.group(1) # 获取括号内的内容 (例如 'a' or '25')
            
            # bbox 是一个包含四个点的列表 [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
            # 计算边界框的中心点
            center_x = int(np.mean([point[0] for point in bbox]))
            center_y = int(np.mean([point[1] for point in bbox]))

            holds_coords[hold_id] = {'x': center_x, 'y': center_y}
            print(f"找到岩点: {hold_id} -> 坐标: ({center_x}, {center_y})")

    # 5. 确保输出目录存在
    output_dir = os.path.dirname(output_path)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 6. 将结果写入 JSON 文件
    print(f"处理完成，正在将 {len(holds_coords)} 个岩点坐标写入: {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(holds_coords, f, indent=2, sort_keys=True)

    print("岩点坐标生成完毕！")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="从图片中生成岩点坐标。")
    parser.add_argument('--image_path', type=str, required=True, help='输入图片的路径。')
    parser.add_argument('--output_path', type=str, required=True, help='输出 JSON 文件的路径。')
    
    args = parser.parse_args()
    
    extract_hold_coordinates(args.image_path, args.output_path)
