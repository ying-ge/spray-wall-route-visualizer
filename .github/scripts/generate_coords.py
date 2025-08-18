import easyocr
import json
import cv2
import re  # 引入正则表达式库用于精确匹配
from pathlib import Path

def generate_holds_coordinates(marked_image_path, output_json_path, debug_image_path=None):
    """使用 OCR 从带标记的图片中识别岩点ID及其坐标。"""
    print("正在初始化 OCR 读取器 (这可能需要一些时间)...")
    reader = easyocr.Reader(['en'])

    print(f"正在读取图片: {marked_image_path}")
    image = cv2.imread(str(marked_image_path))
    if image is None:
        raise FileNotFoundError(f"无法找到或读取图片: {marked_image_path}")

    debug_image = image.copy()
    print("正在使用 OCR 识别图片中的文本...")
    results = reader.readtext(image)

    holds_data = {}
    print(f"识别到 {len(results)} 个可能的标记。正在处理和过滤...")

    for (bbox, text, prob) in results:
        if prob < 0.6: # 可以适当提高置信度门槛
            print(f"  - (忽略) 低置信度: '{text}' (置信度: {prob:.2f})")
            continue

        hold_id = text.strip().lower() # 统一转为小写，以防识别出大写字母
        
        if not hold_id:
            continue

        # --- **新增的严格格式验证** ---
        # 规则：ID 必须是纯数字 (例如 '101') 或单个小写字母 (例如 'a')
        is_valid_format = hold_id.isdigit() or (len(hold_id) == 1 and 'a' <= hold_id <= 'z')
        
        if not is_valid_format:
            print(f"  - (过滤) 格式错误: '{text}' -> '{hold_id}' (不符合'纯数字'或'单个字母'的规则)")
            continue
        # --- 验证结束 ---

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
        print("请确保你已经将 with_mark.png 上传到了 'image' 目录下。")
    else:
        generate_holds_coordinates(marked_image, output_json, debug_image)
