import json
import cv2
from pathlib import Path

def main():
    holds_file = Path("data/holds.json")
    img_file = Path("images/with_markplus.png")
    output_file = Path("generated_routes/debug_mark.png")
    if not holds_file.exists():
        print("holds.json 不存在")
        return
    if not img_file.exists():
        print("with_markplus.png 不存在")
        return

    with open(holds_file, "r", encoding="utf-8") as f:
        holds = json.load(f)

    img = cv2.imread(str(img_file))
    if img is None:
        print(f"无法读取图片 {img_file}")
        return

    for hold_id, coord in holds.items():
        x, y = coord["x"], coord["y"]
        # 画圈
        cv2.circle(img, (x, y), 10, (0, 255, 255), 2)
        # 标注编号
        cv2.putText(img, hold_id, (x + 12, y - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_file), img)
    print(f"已生成 {output_file}")

if __name__ == "__main__":
    main()
