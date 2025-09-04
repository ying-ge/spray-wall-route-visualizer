import json
import math
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import argparse
import re
import sys

# --- 样式配置 (来自您的版本) ---
STYLE_CONFIG = {
    'start':       {'outline': (76, 175, 80, 255),  'shape': 'rectangle', 'text_color': (255, 255, 255)},
    'finish':      {'outline': (244, 67, 54, 255),  'shape': 'rectangle', 'text_color': (255, 255, 255)},
    'left_hand':   {'outline': (33, 150, 243, 255), 'shape': 'circle',    'text_color': (255, 255, 255)},
    'right_hand':  {'outline': (255, 193, 7, 255),  'shape': 'circle',    'text_color': (255, 255, 255)},
    'both_hands':  {'outline': (156, 39, 176, 255), 'shape': 'circle',    'text_color': (255, 255, 255)},
    'foot':        {'outline': (205, 220, 57, 180), 'shape': 'circle'},
    
    'radius': 18,
    'outline_width': 6,
    'text_offset': 25,
    'text_outline_width': 3,
    'center_dot_radius': 4,
    'center_dot_color': (255, 255, 255, 220),

    'arrow_color': (255, 255, 255, 200),
    'arrow_width': 5,
    'arrowhead_length': 25,
    'arrowhead_angle': 25,

    'center_offset_x': 0,
    'center_offset_y': 0,
    
    'title_style': {
        'font_path': "fonts/Oswald-Variable.ttf", 
        'font_size': 70,
        'font_variation': 700, 
        'fill_color': (255, 255, 255),
        'outline_color': (0, 0, 0),
        'outline_width': 4,
        'margin': 60
    },
    'main_font_style': {
        'font_path': "fonts/Oswald-Variable.ttf", 
        'font_size': 50,
        'font_variation': 700 
    }
}

# --- 辅助函数 (来自您的版本) ---
def draw_arrow(draw, start_xy, end_xy):
    x1, y1 = start_xy; x2, y2 = end_xy
    draw.line([start_xy, end_xy], fill=STYLE_CONFIG['arrow_color'], width=STYLE_CONFIG['arrow_width'])
    angle = math.atan2(y2 - y1, x2 - x1); length = STYLE_CONFIG['arrowhead_length']; head_angle = math.radians(STYLE_CONFIG['arrowhead_angle'])
    p1 = (x2 + length * math.cos(angle + math.pi - head_angle), y2 + length * math.sin(angle + math.pi - head_angle))
    p2 = (x2 + length * math.cos(angle + math.pi + head_angle), y2 + length * math.sin(angle + math.pi + head_angle))
    draw.polygon([end_xy, p1, p2], fill=STYLE_CONFIG['arrow_color'])

def draw_text_with_outline(draw, position, text, font, fill_color, outline_color, outline_width):
    x, y = position
    for i in range(-outline_width, outline_width + 1, outline_width):
        for j in range(-outline_width, outline_width + 1, outline_width):
            if i != 0 or j != 0: draw.text((x + i, y + j), text, font=font, fill=outline_color)
    draw.text(position, text, font=font, fill=fill_color)

def draw_hold(draw, center_xy, style, text=None, font=None):
    x, y = center_xy; radius = STYLE_CONFIG['radius']
    box = [x - radius, y - radius, x + radius, y + radius]
    if style.get('shape') == 'rectangle': draw.rectangle(box, outline=style['outline'], width=STYLE_CONFIG['outline_width'])
    else: draw.ellipse(box, outline=style['outline'], width=STYLE_CONFIG['outline_width'])
    dot_radius = STYLE_CONFIG['center_dot_radius']; dot_box = [x - dot_radius, y - dot_radius, x + dot_radius, y + dot_radius]
    draw.ellipse(dot_box, fill=STYLE_CONFIG['center_dot_color'])
    if text and font:
        text_pos_x = x + STYLE_CONFIG['text_offset']; text_pos_y = y - STYLE_CONFIG['text_offset']
        draw_text_with_outline(draw, (text_pos_x, text_pos_y), text, font, fill_color=style['text_color'], outline_color=(0, 0, 0, 255), outline_width=STYLE_CONFIG['text_outline_width'])

def get_variational_font(path, size, variation):
    try:
        font = ImageFont.truetype(path, size)
        try:
            font.set_variation_by_name("Bold")
        except (AttributeError, TypeError):
            try:
                font.set_variation_by_axis_name('wght', variation)
            except (AttributeError, TypeError):
                 pass 
        return font
    except IOError:
        print(f"错误: 字体 '{path}' 未在项目中找到! 将使用默认字体。", file=sys.stderr)
        return ImageFont.load_default()

# --- 核心绘图逻辑 (来自您的版本) ---
def draw_single_route_image(route_data, holds_coords, base_image, fonts, output_dir):
    image = base_image.copy()
    draw = ImageDraw.Draw(image, "RGBA")
    
    offset_x = STYLE_CONFIG.get('center_offset_x', 0)
    offset_y = STYLE_CONFIG.get('center_offset_y', 0)

    if 'holds' in route_data and 'foot' in route_data['holds']:
        style = STYLE_CONFIG['foot']
        for hold_id in route_data['holds']['foot']:
            str_hold_id = str(hold_id).lower()
            if str_hold_id in holds_coords:
                center_xy = (holds_coords[str_hold_id]['x'] + offset_x, holds_coords[str_hold_id]['y'] + offset_y)
                draw_hold(draw, center_xy, style)

    prev_coords = None
    if 'moves' in route_data:
        for move in route_data['moves']:
            hold_id = str(move['hold_id']).lower()
            if hold_id not in holds_coords: continue
            current_coords = (holds_coords[hold_id]['x'] + offset_x, holds_coords[hold_id]['y'] + offset_y)
            if prev_coords: draw_arrow(draw, prev_coords, current_coords)
            prev_coords = current_coords
        
        for move in route_data['moves']:
            hold_id = str(move['hold_id']).lower()
            if hold_id not in holds_coords: continue
            center_xy = (holds_coords[hold_id]['x'] + offset_x, holds_coords[hold_id]['y'] + offset_y)
            style_key = 'start' if move.get('type') == 'start' else 'finish' if move.get('type') == 'finish' else f"{move.get('hand')}_hand"
            style = STYLE_CONFIG.get(style_key)
            text_to_draw = move.get('text')
            if not text_to_draw:
                if move.get('type') == 'start': text_to_draw = 'S'
                elif move.get('type') == 'finish': text_to_draw = 'F'
                elif move.get('hand') == 'left': text_to_draw = 'L'
                elif move.get('hand') == 'right': text_to_draw = 'R'
                elif move.get('hand') == 'both': text_to_draw = 'B'
            if style: draw_hold(draw, center_xy, style, text_to_draw, fonts['main'])

    title_style = STYLE_CONFIG['title_style']
    route_info_text = f"{route_data.get('routeName', 'N/A')} | {route_data.get('difficulty', 'N/A')} | by {route_data.get('author', 'N/A')}"
    
    try: text_bbox = draw.textbbox((0, 0), route_info_text, font=fonts['title'])
    except AttributeError: text_bbox = fonts['title'].getbbox(route_info_text)
        
    text_width, text_height = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]
    
    img_width, img_height = image.size
    margin = title_style['margin']
    text_x, text_y = img_width - text_width - margin, img_height - text_height - margin
    
    draw_text_with_outline(draw, (text_x, text_y), route_info_text, fonts['title'], 
                           fill_color=title_style['fill_color'], 
                           outline_color=title_style['outline_color'], 
                           outline_width=title_style['outline_width'])
    
    quantized_image = image.quantize(colors=256, dither=Image.Dither.NONE)
    
    safe_filename = re.sub(r'[\\/*?:"<>|]', "", route_data.get('routeName', 'untitled'))
    output_filename = f"{route_data.get('difficulty', 'V_')}_{safe_filename.replace(' ', '_')}.png"
    output_path = output_dir / output_filename
    
    quantized_image.save(output_path, 'PNG', optimize=True)
    print(f"  ✓ Saved (and compressed): {output_path}")

# --- 主函数 (重构以适配多墙结构) ---
def main(routes_db_path_str, holds_coords_path_str, base_image_path_str, output_dir_str):
    routes_db_path = Path(routes_db_path_str)
    holds_coords_path = Path(holds_coords_path_str)
    base_image_path = Path(base_image_path_str)
    output_dir = Path(output_dir_str)

    # 检查输入文件是否存在
    for p in [routes_db_path, holds_coords_path, base_image_path]:
        if not p.exists():
            print(f"错误: 输入文件不存在 '{p}'", file=sys.stderr)
            sys.exit(1)

    print(f"Loading routes database: {routes_db_path}")
    with open(routes_db_path, 'r', encoding='utf-8') as f: all_routes_data = json.load(f).get('routes', [])
    print(f"Loading hold coordinates: {holds_coords_path}")
    with open(holds_coords_path, 'r', encoding='utf-8') as f: holds_coords = {k.lower(): v for k, v in json.load(f).items()}
    print(f"Loading base image: {base_image_path}")
    base_image = Image.open(base_image_path).convert("RGBA")
    
    # 加载字体
    fonts = {}
    main_style = STYLE_CONFIG['main_font_style']
    title_style = STYLE_CONFIG['title_style']
    fonts['main'] = get_variational_font(main_style['font_path'], main_style['font_size'], main_style['font_variation'])
    fonts['title'] = get_variational_font(title_style['font_path'], title_style['font_size'], title_style['font_variation'])

    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\nProcessing {len(all_routes_data)} routes...")
    for i, route_data in enumerate(all_routes_data):
        print(f"[{i+1}/{len(all_routes_data)}] Drawing route: '{route_data.get('routeName', 'N/A')}'")
        draw_single_route_image(route_data, holds_coords, base_image, fonts, output_dir)
    
    print("\nAll routes processed successfully!")

# --- 命令行接口 (重构以适配多墙结构) ---
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="为指定墙体生成所有路线图。")
    parser.add_argument("--routes_database_file", required=True, help="路线定义JSON文件的路径。")
    parser.add_argument("--holds_coords_path", required=True, help="岩点坐标JSON文件的路径。")
    parser.add_argument("--base_image_path", required=True, help="用于绘制的底图路径。")
    parser.add_argument("--output_dir", required=True, help="生成的路线图的输出目录。")
    args = parser.parse_args()

    main(args.routes_database_file, args.holds_coords_path, args.base_image_path, args.output_dir)
