import json
import math
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import argparse

# --- 样式配置 ---
STYLE_CONFIG = {
    'start':       {'outline': (76, 175, 80, 255),  'shape': 'rectangle', 'text_color': (255, 255, 255)},
    'finish':      {'outline': (244, 67, 54, 255),  'shape': 'rectangle', 'text_color': (255, 255, 255)},
    'left_hand':   {'outline': (33, 150, 243, 255), 'shape': 'circle',    'text_color': (255, 255, 255)},
    'right_hand':  {'outline': (255, 193, 7, 255),  'shape': 'circle',    'text_color': (0, 0, 0)},
    'both_hands':  {'outline': (156, 39, 176, 255), 'shape': 'circle',    'text_color': (255, 255, 255)},
    'foot':        {'outline': (205, 220, 57, 180), 'shape': 'circle'},
    
    'radius': 18,
    'outline_width': 6,
    # --- **修改点：减小文字偏移量，使其更贴近岩点** ---
    'text_offset': 25,
    'font_size': 70,
    'center_dot_radius': 4,
    'center_dot_color': (255, 255, 255, 220),

    'arrow_color': (255, 255, 255, 200),
    'arrow_width': 5,
    'arrowhead_length': 25,
    'arrowhead_angle': 25,

    # 全局偏移量已重置为 0
    'center_offset_x': 0,
    'center_offset_y': 0,
}

def draw_arrow(draw, start_xy, end_xy):
    """从起点到终点绘制一个箭头。"""
    x1, y1 = start_xy
    x2, y2 = end_xy

    draw.line([start_xy, end_xy], fill=STYLE_CONFIG['arrow_color'], width=STYLE_CONFIG['arrow_width'])

    angle = math.atan2(y2 - y1, x2 - x1)
    length = STYLE_CONFIG['arrowhead_length']
    head_angle = math.radians(STYLE_CONFIG['arrowhead_angle'])

    p1_angle = angle + math.pi - head_angle
    p2_angle = angle + math.pi + head_angle
    p1 = (x2 + length * math.cos(p1_angle), y2 + length * math.sin(p1_angle))
    p2 = (x2 + length * math.cos(p2_angle), y2 + length * math.sin(p2_angle))

    draw.polygon([end_xy, p1, p2], fill=STYLE_CONFIG['arrow_color'])

def draw_hold(draw, center_xy, style, text=None, font=None):
    """在给定的坐标上绘制岩点标记。"""
    x, y = center_xy
    radius = STYLE_CONFIG['radius']
    
    box = [x - radius, y - radius, x + radius, y + radius]
    if style.get('shape') == 'rectangle':
        draw.rectangle(box, outline=style['outline'], width=STYLE_CONFIG['outline_width'])
    else:
        draw.ellipse(box, outline=style['outline'], width=STYLE_CONFIG['outline_width'])

    dot_radius = STYLE_CONFIG['center_dot_radius']
    dot_box = [x - dot_radius, y - dot_radius, x + dot_radius, y + dot_radius]
    draw.ellipse(dot_box, fill=STYLE_CONFIG['center_dot_color'])

    if text and font:
        text_pos_x = x + STYLE_CONFIG['text_offset']
        text_pos_y = y - STYLE_CONFIG['text_offset']
        draw_text_with_outline(draw, (text_pos_x, text_pos_y), text, font,
                               fill_color=style['text_color'],
                               outline_color=(0, 0, 0, 255),
                               outline_width=2)

def draw_text_with_outline(draw, position, text, font, fill_color, outline_color, outline_width):
    """在图片上绘制带有描边的文字。"""
    x, y = position
    for i in range(-outline_width, outline_width + 1, outline_width):
        for j in range(-outline_width, outline_width + 1, outline_width):
            if i != 0 or j != 0:
                draw.text((x + i, y + j), text, font=font, fill=outline_color)
    draw.text(position, text, font=font, fill=fill_color)


def draw_route(route_path, holds_coords_path, base_image_path, output_image_path, font_path=None):
    """根据路线定义，在基础图片上绘制出整条路线，并用箭头连接顺序。"""
    print(f"加载路线: {route_path}")
    with open(route_path, 'r', encoding='utf-8') as f:
        route_data = json.load(f)

    print(f"加载坐标: {holds_coords_path}")
    with open(holds_coords_path, 'r', encoding='utf-8') as f:
        holds_coords = json.load(f)

    print(f"加载图片: {base_image_path}")
    image = Image.open(base_image_path).convert("RGBA")
    draw = ImageDraw.Draw(image, "RGBA")

    try:
        font = ImageFont.truetype(str(font_path) if font_path else "arial.ttf", STYLE_CONFIG['font_size'])
    except IOError:
        print("警告: 找不到用于岩点标签的字体，将使用默认字体。")
        font = ImageFont.load_default()
    
    offset_x = STYLE_CONFIG.get('center_offset_x', 0)
    offset_y = STYLE_CONFIG.get('center_offset_y', 0)

    # 1. 绘制所有可用脚点
    if 'foot' in route_data.get('holds', {}):
        style = STYLE_CONFIG['foot']
        for hold_id in route_data['holds']['foot']:
            if str(hold_id) in holds_coords:
                coords = holds_coords[str(hold_id)]
                center_xy = (coords['x'] + offset_x, coords['y'] + offset_y)
                draw_hold(draw, center_xy, style)

    # 2. 绘制手点序列 (moves) 和箭头
    prev_coords = None
    if 'moves' in route_data:
        # 首先绘制所有箭头
        for move in route_data['moves']:
            hold_id = str(move['hold_id'])
            if hold_id not in holds_coords:
                print(f"警告: 手点ID '{hold_id}' 未在坐标文件中找到，跳过。")
                continue
            
            current_coords_raw = holds_coords[hold_id]
            current_coords = (current_coords_raw['x'] + offset_x, current_coords_raw['y'] + offset_y)
            
            if prev_coords:
                draw_arrow(draw, prev_coords, current_coords)
            
            prev_coords = current_coords

        # 然后在箭头上层绘制所有手点标记
        for move in route_data['moves']:
            hold_id = str(move['hold_id'])
            if hold_id not in holds_coords:
                continue
            
            coords_raw = holds_coords[hold_id]
            center_xy = (coords_raw['x'] + offset_x, coords_raw['y'] + offset_y)
            text_to_draw = move.get('text', '')

            if move.get('type') == 'start': style = STYLE_CONFIG['start']
            elif move.get('type') == 'finish': style = STYLE_CONFIG['finish']
            elif move.get('hand') == 'left': style = STYLE_CONFIG['left_hand']
            elif move.get('hand') == 'right': style = STYLE_CONFIG['right_hand']
            elif move.get('hand') == 'both': style = STYLE_CONFIG['both_hands']
            else: continue
            
            draw_hold(draw, center_xy, style, text_to_draw, font)

    # 3. 绘制路线标题信息
    route_info_text = f"{route_data.get('routeName', '未命名')} | {route_data.get('difficulty', '未知')} | by {route_data.get('author', '匿名')}"
    
    try:
        title_font = ImageFont.truetype(str(font_path) if font_path else "arial.ttf", 60)
    except IOError:
        print("警告: 找不到用于标题的字体，将使用默认字体。")
        title_font = ImageFont.load_default()

    draw_text_with_outline(draw, (50, 50), route_info_text, title_font, (255, 255, 255), (0, 0, 0), 2)
    
    output_image_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_image_path, 'PNG')
    print(f"成功！路线图已保存至: {output_image_path}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="在攀岩墙图片上绘制路线。请在项目根目录下运行此脚本。")
    parser.add_argument("route_file", help="要绘制的路线JSON文件的路径 (例如 routes/route_1_ladder.json)")
    args = parser.parse_args()

    route_to_draw = Path(args.route_file)
    holds_json = Path('data/holds.json')
    original_image = Path('images/ori_image.png') 
    output_filename = f"{route_to_draw.stem}.png"
    output_image = Path('generated_routes') / output_filename

    if not route_to_draw.exists():
        print(f"错误: 路线文件不存在 '{route_to_draw}'")
    elif not holds_json.exists():
        print(f"错误: 岩点坐标文件 '{holds_json}' 不存在。")
    elif not original_image.exists():
        print(f"错误: 原始图片 '{original_image}' 不存在。")
    else:
        draw_route(route_to_draw, holds_json, original_image, output_image, font_path=None)
