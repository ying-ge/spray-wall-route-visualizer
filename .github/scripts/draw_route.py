import json
import math
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import argparse
import re
import sys
import textwrap

# --- 样式配置 ---
# 【修改】为 title_style 添加了 wrap_width
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
        'wrap_width': 45, 'line_spacing': 10 # 新增：标题的换行宽度和行间距
    },
    'main_font_style': {
        'font_path': "fonts/Oswald-Variable.ttf", 'font_size': 50, 'font_variation': 700 
    },
    'beta_text_style': {
        'font_path': "fonts/NotoSansSC[wght].ttf", 'font_size': 40, 'fill_color': (255, 255, 255),
        'background_color': (0, 0, 0, 160), 'margin': 50, 'line_spacing': 15, 'box_padding': 25, 'wrap_width': 35
    }
}

# --- 辅助函数 (保持不变) ---
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

# --- 【新增】辅助函数：计算换行文本的尺寸 ---
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

# --- 【已升级】智能定位函数，现在会避开标题区域 ---
def find_best_position_for_text(image_size, route_holds_coords, text_box_size, title_area):
    img_width, img_height = image_size; box_width, box_height = text_box_size; margin = STYLE_CONFIG['beta_text_style']['margin']
    positions = {
        'top_left': (margin, margin, margin + box_width, margin + box_height),
        'top_right': (img_width - box_width - margin, margin, img_width - margin, margin + box_height),
        'bottom_left': (margin, img_height - box_height - margin, margin + box_width, img_height - margin),
    }
    for name, (x0, y0, x1, y1) in positions.items():
        is_empty = True
        # 检查是否与岩点重叠
        for hx, hy in route_holds_coords:
            if x0 < hx < x1 and y0 < hy < y1: is_empty = False; break
        if not is_empty: continue
        # 检查是否与标题区域重叠 (AABB-AABB collision detection)
        if x0 < title_area[2] and x1 > title_area[0] and y0 < title_area[3] and y1 > title_area[1]:
            is_empty = False
        if is_empty:
            print(f"    - Beta box position: {name} (area is clear)"); return (x0, y0)
    print("    - Warning: All available corners overlap, defaulting beta box to top-left."); return (positions['top_left'][0], positions['top_left'][1])

# --- 【已升级】文本框函数，调用升级后的智能定位 ---
def draw_wrapped_text_box(draw, text, font, style, image_size, route_holds_coords, title_area):
    if not text: return
    padding = style['box_padding']; line_spacing = style['line_spacing']
    box_width, box_height = get_wrapped_text_size(draw, text, font, style['wrap_width'], line_spacing)
    box_width += padding * 2; box_height += padding * 2
    box_x0, box_y0 = find_best_position_for_text(image_size, route_holds_coords, (box_width, box_height), title_area)
    draw.rectangle([box_x0, box_y0, box_x0 + box_width, box_y0 + box_height], fill=style['background_color'])
    current_y = box_y0 + padding
    for line in textwrap.wrap(text, width=style['wrap_width']):
        try: line_bbox = draw.textbbox((0, 0), line, font=font)
        except AttributeError: line_bbox = font.getbbox(line)
        line_height = line_bbox[3] - line_bbox[1]
        draw.text((box_x0 + padding, current_y), line, font=font, fill=style['fill_color'])
        current_y += line_height + line_spacing

# --- 【新增】绘制换行标题的函数 ---
def draw_wrapped_title(draw, text, font, style, image_size):
    img_width, img_height = image_size; margin = style['margin']; line_spacing = style['line_spacing']
    lines = textwrap.wrap(text, width=style['wrap_width'])
    block_width, block_height = get_wrapped_text_size(draw, text, font, style['wrap_width'], line_spacing)
    start_x = img_width - block_width - margin
    start_y = img_height - block_height - margin
    
    current_y = start_y
    for line in lines:
        try: line_bbox = draw.textbbox((0, 0), line, font=font)
        except AttributeError: line_bbox = font.getbbox(line)
        line_height = line_bbox[3] - line_bbox[1]
        # 右对齐绘制
        line_width = line_bbox[2] - line_bbox[0]
        line_x = start_x + (block_width - line_width) # 右对齐的关键
        draw_text_with_outline(draw, (line_x, current_y), line, font, style['fill_color'], style['outline_color'], style['outline_width'])
        current_y += line_height + line_spacing
    
    # 返回标题占据的区域 (x0, y0, x1, y1)
    return (start_x, start_y, start_x + block_width, start_y + block_height)

# --- 【已升级】主绘制函数，集成所有新逻辑 ---
def draw_single_route_image(route_data, holds_coords, base_image, fonts, output_dir):
    image = base_image.copy(); draw = ImageDraw.Draw(image, "RGBA")
    offset_x, offset_y = STYLE_CONFIG.get('center_offset_x', 0), STYLE_CONFIG.get('center_offset_y', 0)
    
    # 1. 收集所有岩点坐标
    current_route_holds_coords = []
    if 'holds' in route_data and 'foot' in route_data['holds']:
        for hold_id in route_data['holds']['foot']:
            if str(hold_id).lower() in holds_coords: current_route_holds_coords.append((holds_coords[str(hold_id).lower()]['x'] + offset_x, holds_coords[str(hold_id).lower()]['y'] + offset_y))
    if 'moves' in route_data:
        for move in route_data['moves']:
            if str(move['hold_id']).lower() in holds_coords: current_route_holds_coords.append((holds_coords[str(move['hold_id']).lower()]['x'] + offset_x, holds_coords[str(move['hold_id']).lower()]['y'] + offset_y))

    # 2. 绘制标题并获取其占据的区域
    title_style = STYLE_CONFIG['title_style']
    route_name = route_data.get('routeName', route_data.get('name', 'N/A')); difficulty = route_data.get('difficulty', route_data.get('grade', 'N/A')); author = route_data.get('author', 'N/A')
    route_info_text = f"{route_name} | {difficulty} | by {author}"
    title_area = draw_wrapped_title(draw, route_info_text, fonts['title'], title_style, image.size)

    # 3. 绘制指导建议，并传入标题区域以供避让
    beta_text = route_data.get('beta')
    if beta_text:
        draw_wrapped_text_box(draw, beta_text, fonts['beta'], STYLE_CONFIG['beta_text_style'], image.size, current_route_holds_coords, title_area)

    # 4. 绘制岩点和箭头 (这部分逻辑不变)
    if 'holds' in route_data and 'foot' in route_data['holds']:
        for hold_id in route_data['holds']['foot']:
            if str(hold_id).lower() in holds_coords: draw_hold(draw, (holds_coords[str(hold_id).lower()]['x'] + offset_x, holds_coords[str(hold_id).lower()]['y'] + offset_y), STYLE_CONFIG['foot'])
    prev_coords = None
    if 'moves' in route_data:
        for move in route_data['moves']:
            if str(move['hold_id']).lower() in holds_coords:
                current_coords = (holds_coords[str(move['hold_id']).lower()]['x'] + offset_x, holds_coords[str(move['hold_id']).lower()]['y'] + offset_y)
                if prev_coords: draw_arrow(draw, prev_coords, current_coords); prev_coords = current_coords
        for move in route_data['moves']:
            if str(move['hold_id']).lower() in holds_coords:
                center_xy = (holds_coords[str(move['hold_id']).lower()]['x'] + offset_x, holds_coords[str(move['hold_id']).lower()]['y'] + offset_y)
                style_key = 'start' if move.get('type') == 'start' else 'finish' if move.get('type') == 'finish' else f"{move.get('hand')}_hand"
                style = STYLE_CONFIG.get(style_key); text_to_draw = move.get('text') or (move.get('type') or move.get('hand', ''))[0].upper()
                if style: draw_hold(draw, center_xy, style, text_to_draw, fonts['main'])
    
    # 5. 保存图片
    quantized_image = image.quantize(colors=256, dither=Image.Dither.NONE); safe_filename = re.sub(r'[\\/*?:"<>|]', "", route_name)
    output_filename = f"{difficulty.replace(' ', '_')}_{safe_filename.replace(' ', '_')}.png"; output_path = output_dir / output_filename
    quantized_image.save(output_path, 'PNG', optimize=True); print(f"  ✓ Saved (and compressed): {output_path}")

# --- (文件剩余部分与您提供的版本完全相同，无需修改) ---
def get_variational_font(path, size, variation):
    font = ImageFont.truetype(path, size);
    try: font.set_variation_by_name("Bold")
    except (AttributeError, TypeError):
        try: font.set_variation_by_axis_name('wght', variation)
        except (AttributeError, TypeError): pass 
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
        beta_style = STYLE_CONFIG['beta_text_style']; fonts['beta'] = ImageFont.truetype(beta_style['font_path'], beta_style['font_size'])
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
