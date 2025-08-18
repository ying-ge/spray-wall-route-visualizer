import json
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import argparse

# --- 绘图样式配置 ---
# 我们可以根据国际惯例定义不同点的样式
# 你可以随时调整这些颜色和大小
STYLE_CONFIG = {
    'start': {'fill': (76, 175, 80, 100), 'outline': (255, 255, 255, 255), 'shape': 'rectangle'}, # 绿色方框
    'hand':  {'fill': (33, 150, 243, 100), 'outline': (255, 255, 255, 255), 'shape': 'circle'},    # 蓝色圆圈
    'foot':  {'fill': (255, 235, 59, 100), 'outline': (255, 255, 255, 255), 'shape': 'circle'},    # 黄色圆圈 (如果特别指定脚点)
    'finish':{'fill': (244, 67, 54, 100),  'outline': (255, 255, 255, 255), 'shape': 'rectangle'}, # 红色方框
    'radius': 40, # 标记的半径大小
    'outline_width': 3,
}

def draw_hold(draw, center_xy, style):
    """在给定的坐标上绘制一个岩点标记"""
    x, y = center_xy
    radius = STYLE_CONFIG['radius']
    fill_color = style['fill']
    outline_color = style['outline']
    width = STYLE_CONFIG['outline_width']
    
    # 定义形状的边界框
    box = [x - radius, y - radius, x + radius, y + radius]

    if style['shape'] == 'rectangle':
        draw.rectangle(box, fill=fill_color, outline=outline_color, width=width)
    else: # 默认为 circle
        draw.ellipse(box, fill=fill_color, outline=outline_color, width=width)

def draw_route(route_path, holds_coords_path, base_image_path, output_image_path, font_path=None):
    """
    根据路线定义，在基础图片上绘制出整条路线。

    参数:
    route_path (Path): 路线定义文件 (JSON) 的路径。
    holds_coords_path (Path): 岩点坐标数据 (JSON) 的路径。
    base_image_path (Path): 原始攀岩墙图片 (ori_image.png) 的路径。
    output_image_path (Path): 生成的路线图的保存路径。
    font_path (Path, optional): 用于在图片上写字的字体文件路径。
    """
    print(f"正在加载路线定义: {route_path}")
    with open(route_path, 'r', encoding='utf-8') as f:
        route_data = json.load(f)

    print(f"正在加载岩点坐标: {holds_coords_path}")
    with open(holds_coords_path, 'r', encoding='utf-8') as f:
        holds_coords = json.load(f)

    print(f"正在加载基础图片: {base_image_path}")
    image = Image.open(base_image_path).convert("RGBA")
    draw = ImageDraw.Draw(image, "RGBA") # 使用 RGBA 模式以支持半透明绘图

    # 绘制所有在路线中使用的点
    hold_types = ['start', 'hand', 'foot', 'finish']
    for hold_type in hold_types:
        if hold_type in route_data['holds']:
            style = STYLE_CONFIG[hold_type]
            for hold_id in route_data['holds'][hold_type]:
                str_hold_id = str(hold_id) # 确保ID是字符串以便在JSON中查找
                if str_hold_id in holds_coords:
                    coords = holds_coords[str_hold_id]
                    draw_hold(draw, (coords['x'], coords['y']), style)
                else:
                    print(f"警告: 在坐标文件中找不到岩点 ID '{str_hold_id}'")

    # 在图片顶部添加路线信息
    try:
        font = ImageFont.truetype(str(font_path) if font_path else "arial.ttf", 60)
    except IOError:
        print("警告: 找不到指定的字体文件，将使用默认字体。")
        font = ImageFont.load_default()
        
    route_info_text = f"{route_data.get('routeName', '未命名路线')} | {route_data.get('difficulty', '难度未知')} | by {route_data.get('author', '匿名')}"
    text_position = (50, 50) # 左上角位置
    # 添加一个半透明背景条
    draw.rectangle([(text_position[0]-10, text_position[1]-10), (image.width - 40, text_position[1] + 80)], fill=(0,0,0,128))
    draw.text(text_position, route_info_text, font=font, fill=(255, 255, 255, 255))
    
    # 保存最终图片
    output_image_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_image_path, 'PNG')
    print(f"成功！路线图已保存至: {output_image_path}")


if __name__ == '__main__':
    # --- 用于直接运行脚本的示例 ---
    parser = argparse.ArgumentParser(description="在攀岩墙图片上绘制路线")
    parser.add_argument("route_file", help="要绘制的路线JSON文件的路径 (例如 routes/sample_route.json)")
    
    args = parser.parse_args()

    repo_root = Path(__file__).parent.parent
    
    # 定义文件路径
    route_to_draw = Path(args.route_file)
    holds_json = repo_root / 'data/holds.json'
    original_image = repo_root / 'images/ori_image.png'
    
    # 定义输出文件名
    output_filename = f"{route_to_draw.stem}.png"
    output_image = repo_root / 'generated_routes' / output_filename

    # 检查所需文件是否存在
    if not route_to_draw.exists():
        print(f"错误: 路线文件不存在 '{route_to_draw}'")
    elif not holds_json.exists():
        print(f"错误: 岩点坐标文件不存在 '{holds_json}'。请先运行 'generate_coords.py'。")
    elif not original_image.exists():
        print(f"错误: 原始图片不存在 '{original_image}'。请确保 ori_image.png 在 'images' 目录下。")
    else:
        # (可选) 如果你想用特定的中文字体，可以把字体文件（如 .ttf 或 .otf）放到项目里
        # font_file = repo_root / 'fonts' / 'YourFont.ttf'
        draw_route(route_to_draw, holds_json, original_image, output_image)
