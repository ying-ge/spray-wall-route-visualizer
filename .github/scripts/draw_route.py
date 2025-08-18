import json
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import argparse

STYLE_CONFIG = {
    'start': {'fill': (76, 175, 80, 100), 'outline': (255, 255, 255, 255), 'shape': 'rectangle'},
    'hand':  {'fill': (33, 150, 243, 100), 'outline': (255, 255, 255, 255), 'shape': 'circle'},
    'foot':  {'fill': (255, 235, 59, 100), 'outline': (255, 255, 255, 255), 'shape': 'circle'},
    'finish':{'fill': (244, 67, 54, 100),  'outline': (255, 255, 255, 255), 'shape': 'rectangle'},
    'radius': 40,
    'outline_width': 3,
}

def draw_hold(draw, center_xy, style):
    """在给定的坐标上绘制一个岩点标记"""
    x, y = center_xy
    radius = STYLE_CONFIG['radius']
    box = [x - radius, y - radius, x + radius, y + radius]
    if style['shape'] == 'rectangle':
        draw.rectangle(box, fill=style['fill'], outline=style['outline'], width=STYLE_CONFIG['outline_width'])
    else:
        draw.ellipse(box, fill=style['fill'], outline=style['outline'], width=STYLE_CONFIG['outline_width'])

def draw_route(route_path, holds_coords_path, base_image_path, output_image_path, font_path=None):
    """根据路线定义，在基础图片上绘制出整条路线。"""
    print(f"正在加载路线定义: {route_path}")
    with open(route_path, 'r', encoding='utf-8') as f:
        route_data = json.load(f)

    print(f"正在加载岩点坐标: {holds_coords_path}")
    with open(holds_coords_path, 'r', encoding='utf-8') as f:
        holds_coords = json.load(f)

    print(f"正在加载基础图片: {base_image_path}")
    image = Image.open(base_image_path).convert("RGBA")
    draw = ImageDraw.Draw(image, "RGBA")

    hold_types = ['start', 'hand', 'foot', 'finish']
    for hold_type in hold_types:
        if hold_type in route_data['holds']:
            style = STYLE_CONFIG[hold_type]
            for hold_id in route_data['holds'][hold_type]:
                str_hold_id = str(hold_id)
                if str_hold_id in holds_coords:
                    coords = holds_coords[str_hold_id]
                    draw_hold(draw, (coords['x'], coords['y']), style)
                else:
                    print(f"警告: 在坐标文件中找不到岩点 ID '{str_hold_id}'")

    try:
        font = ImageFont.truetype(str(font_path) if font_path else "arial.ttf", 60)
    except IOError:
        print("警告: 找不到字体文件，将使用默认字体。")
        font = ImageFont.load_default()
    
    route_info_text = f"{route_data.get('routeName', '未命名路线')} | {route_data.get('difficulty', '难度未知')} | by {route_data.get('author', '匿名')}"
    text_position = (50, 50)
    draw.rectangle([(text_position[0]-10, text_position[1]-10), (image.width - 40, text_position[1] + 80)], fill=(0,0,0,128))
    draw.text(text_position, route_info_text, font=font, fill=(255, 255, 255, 255))
    
    output_image_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_image_path, 'PNG')
    print(f"成功！路线图已保存至: {output_image_path}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="在攀岩墙图片上绘制路线")
    parser.add_argument("route_file", help="要绘制的路线JSON文件的路径 (例如 routes/sample_route.json)")
    args = parser.parse_args()

    # 在 GitHub Action 中，脚本是从仓库根目录运行的。
    # 所有路径都应相对于根目录。
    route_to_draw = Path(args.route_file)
    holds_json = Path('data/holds.json')
    original_image = Path('images/ori_image.png')
    output_filename = f"{route_to_draw.stem}.png"
    output_image = Path('generated_routes') / output_filename

    if not route_to_draw.exists():
        print(f"错误: 路线文件不存在 '{route_to_draw}'")
    elif not holds_json.exists():
        print(f"错误: 岩点坐标文件不存在 '{holds_json}'。")
    elif not original_image.exists():
        print(f"错误: 原始图片不存在 '{original_image}'。")
    else:
        draw_route(route_to_draw, holds_json, original_image, output_image)
