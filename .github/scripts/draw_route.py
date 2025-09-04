import json
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import re

# --- 全局常量 ---
# 字体设置 (已恢复)
try:
    FONT = ImageFont.truetype("fonts/Oswald-Variable.ttf", 40)
    FONT_GRADE = ImageFont.truetype("fonts/Oswald-Variable.ttf", 30)
except IOError:
    print("警告: Oswald 字体未找到。将使用默认字体。")
    FONT = ImageFont.load_default()
    FONT_GRADE = ImageFont.load_default()

# 颜色定义 (R, G, B, A)
COLORS = {
    "start": (0, 255, 0, 255),       # 绿色
    "finish": (255, 0, 0, 255),      # 红色
    "hand": (0, 0, 255, 255),        # 蓝色
    "foot": (255, 255, 0, 255),      # 黄色
    "hand_foot": (0, 191, 255, 255)  # 天蓝色
}

# 标记点半径
RADIUS = 25

def sanitize_filename(name: str) -> str:
    """
    清理字符串，使其成为有效的文件名。
    """
    # 移除无效字符
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    # 将空格替换为下划线
    name = name.replace(" ", "_")
    return name

def draw_hold(draw: ImageDraw.ImageDraw, center_x: int, center_y: int, hold_type: str):
    """
    根据岩点类型在指定位置绘制标记。
    """
    color = COLORS.get(hold_type, COLORS["hand"])
    
    # 绘制一个带边框的透明圆形
    outline_color = (color[0], color[1], color[2], 255) # 边框不透明
    fill_color = (color[0], color[1], color[2], 80) # 填充半透明
    
    draw.ellipse(
        (center_x - RADIUS, center_y - RADIUS, center_x + RADIUS, center_y + RADIUS),
        fill=fill_color,
        outline=outline_color,
        width=4
    )

def draw_route(route_info: dict, holds_coords: dict, base_image: Image.Image) -> Image.Image:
    """
    在底图上绘制单条线路。
    """
    # 创建一个可以在其上绘制的图像副本
    route_image = base_image.copy()
    draw = ImageDraw.Draw(route_image, "RGBA")

    # 绘制所有岩点
    for hold_type, hold_ids in route_info.get("holds", {}).items():
        if hold_type not in COLORS:
            continue
        for hold_id in hold_ids:
            # 统一将岩点ID转为小写字符串进行匹配
            str_hold_id = str(hold_id).lower()
            if str_hold_id in holds_coords:
                coords = holds_coords[str_hold_id]
                draw_hold(draw, coords["x"], coords["y"], hold_type)

    # --- 核心修复点: 恢复绘制标题和等级的代码 ---
    route_name = route_info.get("name", "未命名线路")
    grade = route_info.get("grade", "")
    
    # 绘制带有白色描边的黑色文字，以确保在任何背景下都清晰可见
    def draw_text_with_outline(draw_obj, position, text, font, fill_color, outline_color):
        x, y = position
        # 绘制描边
        draw_obj.text((x-1, y-1), text, font=font, fill=outline_color)
        draw_obj.text((x+1, y-1), text, font=font, fill=outline_color)
        draw_obj.text((x-1, y+1), text, font=font, fill=outline_color)
        draw_obj.text((x+1, y+1), text, font=font, fill=outline_color)
        # 绘制主文字
        draw_obj.text(position, text, font=font, fill=fill_color)

    # 绘制线路名称
    draw_text_with_outline(draw, (10, 10), route_name, FONT, (255, 255, 255), (0, 0, 0))
    
    # 如果有等级信息，绘制在名称下方
    if grade:
        draw_text_with_outline(draw, (10, 55), f"等级: {grade}", FONT_GRADE, (220, 220, 220), (0, 0, 0))

    return route_image

def main(routes_db_path: str, holds_coords_path: str, base_image_path: str, output_dir: str):
    """
    主函数，加载数据并为每条线路生成图片。
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"正在加载线路数据库: {routes_db_path}")
    try:
        with open(routes_db_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
        
        if isinstance(raw_data, dict):
            all_routes_data = raw_data.get('routes', [])
        elif isinstance(raw_data, list):
            all_routes_data = raw_data
        else:
            print(f"警告: '{routes_db_path}' 的格式无法识别。")
            all_routes_data = []
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"错误: 无法加载或解析线路数据库 '{routes_db_path}': {e}")
        return

    print(f"正在加载岩点坐标: {holds_coords_path}")
    try:
        with open(holds_coords_path, 'r', encoding='utf-8') as f:
            holds_coords = {k.lower(): v for k, v in json.load(f).items()}
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"错误: 无法加载或解析岩点坐标文件 '{holds_coords_path}': {e}")
        return

    print(f"正在加载底图: {base_image_path}")
    try:
        base_image = Image.open(base_image_path).convert("RGBA")
    except FileNotFoundError:
        print(f"错误: 底图文件 '{base_image_path}' 未找到。")
        return

    if not all_routes_data:
        print("数据库中没有找到任何线路。")
        return

    print(f"正在处理 {len(all_routes_data)} 条线路...")
    for i, route_info in enumerate(all_routes_data):
        route_name = route_info.get("name", f"线路_{i+1}")
        print(f"  [{i+1}/{len(all_routes_data)}] 正在绘制线路: '{route_name}'")
        
        route_image = draw_route(route_info, holds_coords, base_image)
        
        grade = route_info.get("grade", "NoGrade")
        sanitized_grade = sanitize_filename(grade)
        sanitized_name = sanitize_filename(route_name)
        
        output_filename = f"{sanitized_grade}_{sanitized_name}.png"
        final_path = output_path / output_filename
        
        route_image.save(final_path, "PNG", optimize=True)
        print(f"  ✓ 已保存: {final_path}")

    print("\n所有线路处理完毕！")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="在攀岩墙底图上绘制线路并保存为图片。")
    parser.add_argument("--routes_database_file", required=True, help="包含所有线路定义的 JSON 文件路径。")
    parser.add_argument("--holds_coords_path", required=True, help="包含岩点坐标的 JSON 文件路径。")
    parser.add_argument("--base_image_path", required=True, help="作为背景的攀岩墙图片路径。")
    parser.add_argument("--output_dir", required=True, help="保存生成线路图片的目录。")
    
    args = parser.parse_args()
    main(args.routes_database_file, args.holds_coords_path, args.base_image_path, args.output_dir)
