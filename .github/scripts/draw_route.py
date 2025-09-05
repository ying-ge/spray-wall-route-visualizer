import json
import math
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import argparse
import re
import sys
import textwrap

# --- 样式配置 ---
# 【修改】为 beta_text_style 添加了 font_variation
STYLE_CONFIG = {
    'start':       {'outline': (76, 175, 80, 255),  'shape': 'rectangle', 'text_color': (255, 255, 255)},
    'finish':      {'outline': (244, 67, 54, 255),  'shape': 'rectangle', 'text_color': (255, 255, 255)},
    'left_hand':   {'outline': (33, 150, 243, 255), 'shape': 'circle',    'text_color': (255, 255, 255)},
    'right_hand':  {'outline': (255, 193, 7, 255),  'shape': 'circle',    'text_color': (255, 255, 255)},
    'both_hands':  {'outline': (156, 39, 176, 255), 'shape': 'circle',    'text_color': (255, 255, 255)},
    'foot':        {'outline': (205, 220, 57, 180), 'shape': 'circle'},
    'radius': 18, 'outline_width': 6, 'text_offset': 25, 'font_size': 50, 'text_outline_width': 3,
    'center_dot_radius': 4, 'center_dot_color': (255, 255, 255, 220), 'arrow_color': (255, 255, 255, 200),
    'arrow_width': 5, 'arrowhead_length': 25, 'arrowhead_angle': 25, 'center_offset_x': 0, 'center_offset_y': 0,
    'title_style': {
        'font_path': "fonts/Oswald-Variable.ttf", 'font_size': 75, 'font_variation': 700, 
        'fill_color': (255, 255, 255), 'outline_color': (0, 0, 0), 'outline_width': 4, 'margin': 60,
        'wrap_width': 45, 'line_spacing': 10
    },
    'main_font_style': {
        'font_path': "fonts/Oswald-Variable.ttf", 'font_size': 50, 'font_variation': 700 
    },
    'beta_text_style': {
        'font_path': "fonts/NotoSansSC[wght].ttf", 'font_size': 40, 'font_variation': 700, # 700 是粗体
        'fill_color': (255, 255, 255), 'background_color': (0, 0, 0),
        'padding_x': 50, 'padding_y': 40, 'line_spacing': 15, 'wrap_width': 80
    }
}

# --- 辅助函数 ---
def draw_arrow(draw, start_xy, end_xy):
    x1, y1 = start_xy; x2, y2 = end_xy; draw.line([start_xy, end_xy], fill=STYLE_CONFIG['arrow_color'], width=STYLE_CONFIG['arrow_width'])
    angle = math.atan2(y2 - y1, x2 - x1); length = STYLE_CONFIG['arrowhead_length']; head_angle = math.radians(STYLE_CONFIG['arrowhead_angle'])
    p1 = (x2 + length * math.cos(angle + math.pi - head_angle), y2 + length * math.sin(angle + math.pi - head_angle)); p2 = (x2 + length * math.cos(angle + math.pi + head_angle), y2 + length * math.sin(angle + math.pi + head_angle))
    draw.polygon([end_xy, p1, p2], fill=STYLE_CONFIG['arrow_color'])

def draw_text_with_outline(draw, position, text, font, fill_color, outline_color, outline_width):
    x, y = position
    for i in range(-outline_width, outline_width + 1, outline_width):
        for j in range(-outline_width, outline_width + 1, outline_width):
            if i != 0 or j != 0: draw.text((x + i, y + j), text, font=font, fill=outline_color)
    draw.text(position, text, font=font, fill=fill_color)

def draw_hold(draw, center_xy, style, text=None, font=None):
    x, y = center_xy; radius = STYLE_CONFIG['radius']; box = [x - radius, y - radius, x + radius, y + radius]
    if style.get('shape') == 'rectangle': draw.rectangle(box, outline=style['outline'], width=STYLE_CONFIG['outline_width'])
    else: draw.ellipse(box, outline=style['outline'], width=STYLE_CONFIG['outline_width'])
    dot_radius = STYLE_CONFIG['center_dot_radius']; dot_box = [x - dot_radius, y - dot_radius, x + dot_radius, y + dot_radius]
    draw.ellipse(dot_box, fill=STYLE_CONFIG['center_dot_color'])
    if text and font:
        text_pos_x = x + STYLE_CONFIG['text_offset']; text_pos_y = y - STYLE_CONFIG['text_offset']
        draw_text_with_outline(draw, (text_pos_x, text_pos_y), text, font, fill_color=style['text_color'], outline_color=(0, 0, 0, 255), outline_width=STYLE_CONFIG['text_outline_width'])

def get_wrapped_text_size(draw, text, font, wrap_width, line_spacing):
    lines = textwrap.wrap(text, width=wrap_width)
    max_line_width, total_text_height = 0, 0
    for line in lines:
        try: line_bbox = draw.textbbox((0, 0), line, font=font)
        except AttributeError: line_bbox = font.getbbox(line)
        line_width = line_bbox[2] - line_bbox[0]; line_height = line_bbox[3] - line_bbox[1]
        if line_width > max_line_width: max_line_width = line_width
        total_text_height += line_height
    total_text_height += line_spacing * (len(lines) - 1)
    return max_line_width, total_text_height

def draw_wrapped_title(draw, text, font, style, image_size):
    img_width, img_height = image_size; margin = style['margin']; line_spacing = style['line_spacing']
    lines = textwrap.wrap(text, width=style['wrap_width'])
    block_width, block_height = get_wrapped_text_size(draw, text, font, style['wrap_width'], line_spacing)
    start_x = img_width - block_width - margin; start_y = img_height - block_height - margin
    current_y = start_y
    for line in lines:
        try: line_bbox = draw.textbbox((0, 0), line, font=font)
        except AttributeError: line_bbox = font.getbbox(line)
        line_height = line_bbox[3] - line_bbox[1]
        line_width = line_bbox[2] - line_bbox[0]; line_x = start_x + (block_width - line_width)
        draw_text_with_outline(draw, (line_x, current_y), line, font, style['fill_color'], style['outline_color'], style['outline_width'])
        current_y += line_height + line_spacing

def draw_single_route_image(route_data, holds_coords, base_image, fonts, output_dir):
    image_part = base_image.copy()
    draw = ImageDraw.Draw(image_part, "RGBA")
    offset_x, offset_y = STYLE_CONFIG.get('center_offset_x', 0), STYLE_CONFIG.get('center_offset_y', 0)
    
    title_style = STYLE_CONFIG['title_style']
    route_name = route_data.get('routeName', route_data.get('name', 'N/A'))
    difficulty = route_data.get('difficulty', route_data.get('grade', 'N/A'))
    author = route_data.get('author', 'N/A')
    route_info_text = f"{route_name} | {difficulty} | by {author}"
    draw_wrapped_title(draw, route_info_text, fonts['title'], title_style, image_part.size)

    if 'holds' in route_data and 'foot' in route_data['holds']:
        for hold_id in route_data['holds']['foot']:
            if str(hold_id).lower() in holds_coords:
                draw_hold(draw, (holds_coords[str(hold_id).lower()]['x'] + offset_x, holds_coords[str(hold_id).lower()]['y'] + offset_y), STYLE_CONFIG['foot'])
    
    prev_coords = None
    if 'moves' in route_data:
        for move in route_data['moves']:
            hold_id_str = str(move['hold_id']).lower()
            if hold_id_str in holds_coords:
                center_xy = (holds_coords[hold_id_str]['x'] + offset_x, holds_coords[hold_id_str]['y'] + offset_y)
                style_key = 'start' if move.get('type') == 'start' else 'finish' if move.get('type') == 'finish' else f"{move.get('hand')}_hand"
                style = STYLE_CONFIG.get(style_key)
                text_to_draw = move.get('text') or (move.get('type') or move.get('hand', ''))[0].upper()
                if style:
                    draw_hold(draw, center_xy, style, text_to_draw, fonts['main'])
                if prev_coords:
                    draw_arrow(draw, prev_coords, center_xy)
                prev_coords = center_xy
    
    final_image = image_part
    beta_text = route_data.get('beta')
    if beta_text:
        beta_style = STYLE_CONFIG['beta_text_style']
        beta_font = fonts['beta']
        
        temp_draw = ImageDraw.Draw(Image.new('RGB', (1,1)))
        _, text_height = get_wrapped_text_size(temp_draw, beta_text, beta_font, beta_style['wrap_width'], beta_style['line_spacing'])
        extra_height = text_height + beta_style['padding_y'] * 2
        
        orig_width, orig_height = image_part.size
        new_width, new_height = orig_width, orig_height + int(extra_height)
        final_image = Image.new('RGB', (new_width, new_height), beta_style['background_color'])
        
        final_image.paste(image_part, (0, 0))
        
        beta_draw = ImageDraw.Draw(final_image)
        current_y = orig_height + beta_style['padding_y']
        for line in textwrap.wrap(beta_text, width=beta_style['wrap_width']):
            try: line_bbox = beta_draw.textbbox((0, 0), line, font=beta_font)
            except AttributeError: line_bbox = beta_font.getbbox(line)
            line_height = line_bbox[3] - line_bbox[1]
            beta_draw.text((beta_style['padding_x'], current_y), line, font=beta_font, fill=beta_style['fill_color'])
            current_y += line_height + beta_style['line_spacing']
            
    safe_filename = re.sub(r'[\\/*?:"<>|]', "", route_name)
    output_filename = f"{difficulty.replace(' ', '_')}_{safe_filename.replace(' ', '_')}.png"
    output_path = output_dir / output_filename
    final_image.save(output_path, 'PNG', optimize=True)
    print(f"  ✓ Saved: {output_path}")

# --- 【修改】让 get_variational_font 同时处理 'wght' 轴 ---
def get_variational_font(path, size, variation):
    font = ImageFont.truetype(path, size)
    try:
        # 尝试使用 'wght' 轴来设置粗细，这对于 NotoSansSC[wght].ttf 生效
        font.set_variation_by_axis_name('wght', variation)
    except (AttributeError, TypeError):
        try:
            # 如果失败，回退到按名称设置（例如 "Bold"），对 Oswald 生效
            font.set_variation_by_name("Bold")
        except (AttributeError, TypeError):
             pass # 如果都不支持，则返回默认粗细
    return font

def process_all_routes(routes_db_path, holds_coords_path, base_image_path, output_dir):
    try:
        print(f"Loading routes database: {routes_db_path}");
        with open(routes_db_path, 'r', encoding='utf-8') as f: raw_data = json.load(f)
        if isinstance(raw_data, dict): all_routes_data = raw_data.get('routes', [])
        elif isinstance(raw_data, list): all_routes_data = raw_data
        else: all_routes_data = []
        print(f"Loading hold coordinates: {holds_coords_path}");
        with open(holds_coords_path, 'r', encoding='utf-8') as f: holds_coords = {k.lower(): v for k, v in json.load(f).items()}
        print(f"Loading base image: {base_image_path}"); base_image = Image.open(base_image_path).convert("RGBA")
    except FileNotFoundError as e: print(f"错误: 必需文件未找到 - {e}", file=sys.stderr); sys.exit(1)
    except json.JSONDecodeError as e: print(f"错误: 解析JSON文件时出错 - {e}", file=sys.stderr); sys.exit(1)
    fonts = {}
    try:
        main_style = STYLE_CONFIG['main_font_style']; fonts['main'] = get_variational_font(main_style['font_path'], main_style['font_size'], main_style['font_variation'])
        title_style = STYLE_CONFIG['title_style']; fonts['title'] = get_variational_font(title_style['font_path'], title_style['font_size'], title_style['font_variation'])
        
        # --- 【修改】使用通用的变体字体加载函数来加载 beta 字体 ---
        beta_style = STYLE_CONFIG['beta_text_style']
        fonts['beta'] = get_variational_font(beta_style['font_path'], beta_style['font_size'], beta_style['font_variation'])

    except IOError as e: print(f"错误: 字体文件未找到。请确保字体文件存在于 'fonts/' 目录下 - {e}", file=sys.stderr); sys.exit(1)
    output_dir.mkdir(parents=True, exist_ok=True)
    if not all_routes_data: print("数据库中没有找到任何线路。"); return
    print(f"\nProcessing {len(all_routes_data)} routes...")
    for i, route_data in enumerate(all_routes_data):
        route_name = route_data.get('routeName', route_data.get('name', 'N/A')); print(f"[{i+1}/{len(all_routes_data)}] Drawing route: '{route_name}'")
        draw_single_route_image(route_data, holds_coords, base_image, fonts, output_dir)
    print("\nAll routes processed successfully!")
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="在攀岩墙底图上绘制线路并保存为图片。"); parser.add_argument("--routes_database_file", required=True, help="包含所有线路定义的 JSON 文件路径。"); parser.add_argument("--holds_coords_path", required=True, help="包含岩点坐标的 JSON 文件路径。"); parser.add_argument("--base_image_path", required=True, help="作为背景的攀岩墙图片路径。"); parser.add_argument("--output_dir", required=True, help="保存生成线路图片的目录。")
    args = parser.parse_args(); routes_db_path = Path(args.routes_database_file); holds_coords_path = Path(args.holds_coords_path); base_image_path = Path(args.base_image_path); output_dir = Path(args.output_dir)
    if not routes_db_path.exists(): print(f"错误: 路线数据库文件不存在 '{routes_db_path}'", file=sys.stderr); sys.exit(1)
    if not holds_coords_path.exists(): print(f"错误: 岩点坐标文件 '{holds_coords_path}' 不存在。", file=sys.stderr); sys.exit(1)
    if not base_image_path.exists(): print(f"错误: 原始图片 '{base_image_path}' 不存在。", file=sys.stderr); sys.exit(1)
    process_all_routes(routes_db_path, holds_coords_path, base_image_path, output_dir)
