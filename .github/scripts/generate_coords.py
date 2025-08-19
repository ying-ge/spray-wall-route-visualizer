import easyocr
import json
import cv2
from pathlib import Path

def generate_holds_coordinates(marked_image_path, output_json_path, debug_image_path=None):
    """
    使用新的标记方案 (# + ID) 进行高精度OCR识别。
    """
    print("正在初始化 OCR 读取器...")
    # 我们让OCR识别更多字符，然后用代码逻辑来精确过滤
    reader = easyocr.Reader(['en'])

    print(f"正在读取图片: {marked_image_path}")
    image = cv2.imread(str(marked_image_path))
    if image is None:
        raise FileNotFoundError(f"无法找到或读取图片: {marked_image_path}")

    # 对于高对比度的标记，直接在原图上识别效果最好
    print("正在使用高精度模式识别 '# + ID' 标记...")
    results = reader.readtext(image)

    holds_data = {}
    print(f"初步识别到 {len(results)} 个文本块。正在过滤和提取有效ID...")

    for (bbox, text, prob) in results:
        # 清理文本，统一转为小写
        clean_text = text.strip().lower()

        # --- 核心逻辑：只处理以 '#' 开头的文本 ---
        if not clean_text.startswith('#'):
            print(f"  - (跳过) '{text}' -> 未检测到 '#' 锚点符号。")
            continue
        
        # 提取 '#' 后面的真实ID
        hold_id = clean_text[1:]

        # 对提取出的ID进行最终格式验证
        is_valid_format = hold_id.isdigit() or (len(hold_id) == 1 and 'a' <= hold_id <= 'z')
        
        if not is_valid_format:
            print(f"  - (过滤) '{text}' -> 提取的ID '{hold_id}' 格式无效。")
            continue
        
        # 如果置信度太低，也跳过
        if prob < 0.5:
            print(f"  - (忽略) '{text}' -> 置信度过低 ({prob:.2f})")
            continue

        (tl, tr, br, bl) = bbox
        cX = int((tl[0] + br[0]) / 2.0)
        cY = int((tl[1] + br[1]) / 2.0)
        
        holds_data[hold_id] = {"x": cX, "y": cY}
        print(f"  ✅ (成功) 找到有效岩点 '{hold_id}' @ ({cX}, {cY})，置信度: {prob:.2f}")

        if debug_image_path:
            (tl, tr, br, bl) = bbox
            tl_int = (int(tl[0]), int(tl[1]))
            br_int = (int(br[0]), int(br[1]))
            cv2.rectangle(debug_image, tl_int, br_int, (0, 255, 0), 2)
            cv2.putText(debug_image, f"#{hold_id}", (tl_int[0], tl_int[1] - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)

    # --- 后续处理和保存 ---
    def sort_key(k):
        is_digit = k.isdigit()
        return (not is_digit, int(k) if is_digit else k)

    sorted_keys = sorted(holds_data.keys(), key=sort_key)
    sorted_holds_data = {k: holds_data[k] for k in sorted_keys}
    
    output_path = Path(output_json_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"\n处理完成！共识别出 {len(sorted_holds_data)} 个有效岩点。正在写入到: {output_json_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(sorted_holds_data, f, indent=4, ensure_ascii=False)

    if debug_image_path:
        debug_image = image.copy()
        for hold_id, data in holds_data.items():
            # (此部分仅为示例，实际绘制已在上面循环中完成)
            pass
        debug_path = Path(debug_image_path)
        debug_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(debug_path), debug_image)
        print(f"调试图片已保存到: {debug_image_path}")

if __name__ == '__main__':
    marked_image = Path('images/with_markplus.png')
    output_json = Path('data/holds.json')
    debug_image = Path('generated_routes/debug_ocr.png')
    
    if not marked_image.exists():
        print(f"错误: 找不到标记图片 '{marked_image}'。")
    else:
        generate_holds_coordinates(marked_image, output_json, debug_image)
