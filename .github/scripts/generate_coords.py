import easyocr
import json
import cv2
import numpy as np
from pathlib import Path

def generate_holds_coordinates(marked_image_path, output_json_path, debug_image_path=None):
    """
    使用 OCR 从带标记的图片中识别岩点ID及其坐标。

    参数:
    marked_image_path (str): 带有数字/字母标记的墙体图片路径。
    output_json_path (str): 输出的 holds.json 文件路径。
    debug_image_path (str, optional): 用于调试和验证的输出图片路径。
    """
    print("正在初始化 OCR 读取器 (这可能需要一些时间)...")
    # 初始化 OCR 读取器，我们只关心英文
    reader = easyocr.Reader(['en'])

    print(f"正在读取图片: {marked_image_path}")
    image = cv2.imread(str(marked_image_path))
    if image is None:
        raise FileNotFoundError(f"无法找到或读取图片: {marked_image_path}")

    # 创建调试用的图片副本
    debug_image = image.copy()

    print("正在使用 OCR 识别图片中的文本...")
    # readtext 会返回一个列表，每个元素包含 [边界框, 识别的文本, 置信度]
    results = reader.readtext(image)

    holds_data = {}
    print(f"识别到 {len(results)} 个可能的标记。正在处理...")

    for (bbox, text, prob) in results:
        # bbox 是一个包含四个点的列表: [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
        # 我们可以通过计算边界框的中心来确定岩点的坐标
        
        # 获取边界框的左上角和右下角点
        (tl, tr, br, bl) = bbox
        tl = (int(tl[0]), int(tl[1]))
        br = (int(br[0]), int(br[1]))

        # 计算中心点坐标
        cX = int((tl[0] + br[0]) / 2.0)
        cY = int((tl[1] + br[1]) / 2.0)
        
        # 清理识别出的文本，并将其作为岩点的 ID
        hold_id = text.strip()

        # 存储坐标
        holds_data[hold_id] = {"x": cX, "y": cY}
        
        print(f"  - 找到岩点 '{hold_id}' @ ({cX}, {cY})，置信度: {prob:.2f}")

        # 在调试图片上绘制边界框和中心点，以便验证
        if debug_image_path:
            cv2.rectangle(debug_image, tl, br, (0, 255, 0), 2)
            cv2.circle(debug_image, (cX, cY), 5, (0, 0, 255), -1)
            cv2.putText(debug_image, hold_id, (tl[0], tl[1] - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)

    # 按岩点ID排序 (数字优先，然后是字母)
    sorted_keys = sorted(holds_data.keys(), key=lambda k: (k.isdigit(), int(k) if k.isdigit() else ord(k)))
    sorted_holds_data = {k: holds_data[k] for k in sorted_keys}
    
    # 创建 `data` 目录
    output_path = Path(output_json_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"\n正在将 {len(sorted_holds_data)} 个岩点坐标写入到: {output_json_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(sorted_holds_data, f, indent=4, ensure_ascii=False)

    # 保存调试图片
    if debug_image_path:
        debug_path = Path(debug_image_path)
        debug_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(debug_path), debug_image)
        print(f"调试图片已保存到: {debug_image_path}")

if __name__ == '__main__':
    # 确保图片路径相对于项目根目录
    repo_root = Path(__file__).parent.parent
    marked_image = repo_root / 'images/with_mark.png'
    output_json = repo_root / 'data/holds.json'
    debug_image = repo_root / 'generated_routes/debug_ocr.png'
    
    # 检查图片是否存在
    if not marked_image.exists():
        print(f"错误: 找不到标记图片 '{marked_image}'。")
        print("请确保你已经将 with_mark.png 上传到了 'images' 目录下。")
    else:
        generate_holds_coordinates(marked_image, output_json, debug_image)
