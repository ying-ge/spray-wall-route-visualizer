import json
from pathlib import Path

def main():
    holds_path = Path("data/holds.json")
    if not holds_path.exists():
        print("data/holds.json 文件不存在")
        return

    with open(holds_path, "r", encoding="utf-8") as f:
        holds = json.load(f)
    found_ids = set(holds.keys())

    # 生成标准id集合
    expected_ids = {str(i) for i in range(1, 141)}
    expected_ids.update({chr(c) for c in range(ord("a"), ord("z")+1)})

    missing_ids = sorted(expected_ids - found_ids, key=lambda x: (x.isdigit(), int(x) if x.isdigit() else x))
    if missing_ids:
        print("未识别的岩点ID：")
        print(", ".join(missing_ids))
    else:
        print("所有岩点都已识别！")

if __name__ == "__main__":
    main()
