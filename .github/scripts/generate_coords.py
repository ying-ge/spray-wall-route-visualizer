import easyocr
import json
import cv2
import numpy as np # 需要 numpy
from pathlib import Path

def generate_holds_coordinates(marked_image_path, output_json_path, debug_image_path=None):
    """使用 OCR 从带标记的图片中识别岩点ID及其坐标。"""
    print("正在初始化 OCR 读取器 (这可能需要一些时间)...")
    # --- 改进1: 添加字符白名单 ---
    # 只识别数字和26个小写字母
    allowed_chars = '0123456789abcdefghijklmnopqrstuvwxyz'
    reader = easyocr.Reader(['en'])

    print(f"正在读取图片: {marked_image_path}")
    image = cv2.imread(str(marked_image_path))
    if image is None:
        raise FileNotFoundError(f"无法找到或读取图片: {marked_image_path}")

    # --- 改进2: 图像预处理 ---
    print("正在对图片进行预处理以提升OCR准确率...")
    # 1. 转为灰度图
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # 2. 应用自适应阈值，使其在不同光照下效果更好
    # blockSize 必须是奇数, C 是从均值或加权均值中减去的常数
    binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                   cv2.THRESH_BINARY_INV, 25, 10)

    # 3. 形态学操作来去噪和连接字符
    kernel = np.ones((2,2), np.uint8)
    processed_image = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    
    # (可选) 如果需要调试预处理效果，可以保存中间图片
    # cv2.imwrite('generated_routes/debug_preprocessed.png', processed_image)

    debug_image = image.copy()
    print("正在使用 OCR 识别处理后的图片中的文本...")
    # 在 readtext 中传入白名单
    results = reader.readtext(processed_image, allowlist=allowed_chars)

    holds_data = {}
    print(f"识别到 {len(results)} 个可能的标记。正在处理和过滤...")

    for (bbox, text, prob) in results:
        # --- 改进3: 调整置信度阈值 ---
        if prob < 0.4: # 预处理后可以适当放宽标准
            print(f"  - (忽略) 低置信度: '{text}' (置信度: {prob:.2f})")
            continue

        hold_id = text.strip().lower()
        
        if not hold_id:
            continue

        # 格式验证 (这个依然保留，非常重要)
        is_valid_format = hold_id.isdigit() or (len(hold_id) == 1 and 'a' <= hold_id <= 'z')
        
        if not is_valid_format:
            print(f"  - (过滤) 格式错误: '{text}' -> '{hold_id}' (不符合'纯数字'或'单个字母'的规则)")
            continue

        (tl, tr, br, bl) = bbox
        tl = (int(tl[0]), int(tl[1]))
        br = (int(br[0]), int(br[1]))
        cX = int((tl[0] + br[0]) / 2.0)
        cY = int((tl[1] + br[1]) / 2.0)
        
        holds_data[hold_id] = {"x": cX, "y": cY}
        print(f"  - (有效) 找到岩点 '{hold_id}' @ ({cX}, {cY})，置信度: {prob:.2f}")

        if debug_image_path:
            cv2.rectangle(debug_image, tl, br, (0, 255, 0), 2)
            cv2.circle(debug_image, (cX, cY), 5, (0, 0, 255), -1)
            cv2.putText(debug_image, hold_id, (tl[0], tl[1] - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)

    def sort_key(k):
        is_digit = k.isdigit()
        return (not is_digit, int(k) if is_digit else k)

    sorted_keys = sorted(holds_data.keys(), key=sort_key)
    sorted_holds_data = {k: holds_data[k] for k in sorted_keys}
    
    output_path = Path(output_json_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"\n处理完成！正在将 {len(sorted_holds_data)} 个有效岩点坐标写入到: {output_json_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(sorted_holds_data, f, indent=4, ensure_ascii=False)

    if debug_image_path:
        debug_path = Path(debug_image_path)
        debug_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(debug_path), debug_image)
        print(f"调试图片已保存到: {debug_image_path}")

if __name__ == '__main__':
    marked_image = Path('images/with_mark.png')
    output_json = Path('data/holds.json')
    debug_image = Path('generated_routes/debug_ocr.png')
    
    if not marked_image.exists():
        print(f"错误: 找不到标记图片 '{marked_image}'。")
        print("请确保你已经将 with_mark.png 上传到了 'images' 目录下。")
    else:
        generate_holds_coordinates(marked_image, output_json, debug_image)
