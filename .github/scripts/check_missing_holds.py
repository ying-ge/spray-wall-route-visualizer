import json
import argparse
from pathlib import Path
import sys

def check_holds(wall_dir_str: str):
    """
    为一个指定的墙体检查是否有岩点缺失。
    """
    wall_dir = Path(wall_dir_str)
    
    config_path = wall_dir / "config.json"
    holds_path = wall_dir / "output/data/holds.json"

    if not config_path.exists():
        print(f"⚠️  警告: 墙体 '{wall_dir.name}' 的配置文件不存在。跳过检查。", file=sys.stderr)
        return

    if not holds_path.exists():
        print(f"⚠️  警告: 墙体 '{wall_dir.name}' 的岩点坐标文件不存在。跳过检查。", file=sys.stderr)
        return

    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    with open(holds_path, 'r', encoding='utf-8') as f:
        # 将所有检测到的岩点ID转为小写，以便进行不区分大小写的比较
        detected_holds = {str(h).lower() for h in json.load(f).keys()}

    wall_name = config.get("wall_name", wall_dir.name)
    
    # --- 核心修复点 ---
    # 1. 正确获取名为 "valid_hold_ranges" 的配置块
    expected_config = config.get("valid_hold_ranges")
    
    if not expected_config:
        print(f"ℹ️  信息: 墙体 '{wall_name}' 的 config.json 中未定义 'valid_hold_ranges'。跳过检查。")
        return

    print(f"\n--- 正在为墙体检查缺失的岩点: {wall_name} ---")

    expected_holds = set()
    
    # 2. 分别处理 "numeric_ranges"
    numeric_ranges = expected_config.get("numeric_ranges", [])
    for start, end in numeric_ranges:
        for i in range(start, end + 1):
            expected_holds.add(str(i))
            
    # 3. 分别处理 "alphabetic_ranges"
    alphabetic_ranges = expected_config.get("alphabetic_ranges", [])
    for start_char, end_char in alphabetic_ranges:
        for i in range(ord(start_char.lower()), ord(end_char.lower()) + 1):
            expected_holds.add(chr(i))
    # --- 修复结束 ---

    if not expected_holds:
        print(f"ℹ️  信息: 'valid_hold_ranges' 中未定义任何范围。无需检查。")
        return

    # 计算缺失的岩点
    missing_holds = sorted(list(expected_holds - detected_holds), key=lambda x: (x.isdigit(), int(x) if x.isdigit() else ord(x)))

    if not missing_holds:
        print("✅  成功！所有预期的岩点都已被识别。")
    else:
        # 使用 GitHub Actions 的错误格式输出，使其在摘要中更醒目
        print(f"::error::🚨  错误: 发现了 {len(missing_holds)} 个缺失的岩点！")
        print("::error::缺失的岩点编号/字母:", ", ".join(missing_holds))
        # 也可以选择让工作流失败
        # sys.exit(1)

    print("-" * (42 + len(wall_name)))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="检查一个或多个攀岩墙是否有缺失的岩点。")
    parser.add_argument(
        "wall_dirs",
        nargs='*',
        default=[],
        help="要检查的特定墙体目录 (例如, 'walls/spray_wall')。如果为空，则检查 'walls/' 下的所有目录。"
    )
    args = parser.parse_args()
    project_root = Path(__file__).resolve().parents[2]
    walls_root = project_root / "walls"

    if args.wall_dirs:
        target_dirs = [project_root / d for d in args.wall_dirs]
    else:
        target_dirs = [d for d in walls_root.iterdir() if d.is_dir()]

    if not target_dirs:
        print("没有找到需要检查的墙体目录。", file=sys.stderr)
        sys.exit(0)
        
    print(f"找到 {len(target_dirs)} 个墙体进行处理。")
    for wall_dir in target_dirs:
        check_holds(wall_dir)
