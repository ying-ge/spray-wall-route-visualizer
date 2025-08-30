import os

if os.path.exists("data/holds.json"):
    print("data/holds.json 已存在，跳过自动生成。")
    exit(0)
    
import easyocr
import json
import cv2
from pathlib import Path

def generate_holds_coordinates(marked_image_path, output_json_path, debug_image_path=None):
    print("正在初始化 OCR 读取器...")
    reader = easyocr.Reader(['en'])

    print(f"正在读取图片: {marked_image_path}")
    image = cv2.imread(str(marked_image_path))
    if image is None:
        raise FileNotFoundError(f"无法找到或读取图片: {marked_image_path}")

    debug_image = image.copy()
    results = reader.readtext(image)

    holds_data = {}
    print(f"识别到 {len(results)} 个文本块。")

    for (bbox, text, prob) in results:
        clean_text = text.strip().lower()
        (tl, tr, br, bl) = bbox
        tl_int = (int(tl[0]), int(tl[1]))
        br_int = (int(br[0]), int(br[1]))
        cX = int((tl[0] + br[0]) / 2.0)
        cY = int((tl[1] + br[1]) / 2.0)

        # 所有识别结果都画出来
        label = f"{clean_text} ({prob:.2f})"
        # 合格的用绿色，不合格的用红色
        is_valid = (clean_text.isdigit() or (len(clean_text) == 1 and 'a' <= clean_text <= 'z')) and prob >= 0.5
        color = (0, 255, 0) if is_valid else (0, 0, 255)
        cv2.rectangle(debug_image, tl_int, br_int, color, 2)
        cv2.putText(debug_image, label, (tl_int[0], tl_int[1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
        cv2.circle(debug_image, (cX, cY), 5, color, -1)

        # 只保存合格的点
        if is_valid:
            holds_data[clean_text] = {"x": cX, "y": cY}

    output_path = Path(output_json_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(holds_data, f, indent=4, ensure_ascii=False)

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
    else:
        generate_holds_coordinates(marked_image, output_json, debug_image)
