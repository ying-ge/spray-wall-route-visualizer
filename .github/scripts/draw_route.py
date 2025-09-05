import json
import math
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import argparse
import re
import sys
import textwrap # <--- 新增: 导入文本换行模块

# --- 样式配置 ---
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
    'font_size': 50,
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
        'font_size': 75,
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
    },
    # <--- 新增: 指导建议文本框的样式 ---
    'beta_text_style': {
        'font_path': "fonts/NotoSansSC-Regular.ttf", # 使用思源黑体
        'font_size': 40,
        'fill_color': (255, 255, 255),
        'background_color': (0, 0, 0, 160), # 半透明黑色背景
        'margin': 50, # 文本框距离图片边缘的距离
        'line_spacing': 15, # 行间距
        'box_padding': 25, # 文字距离背景框边缘的距离
        'wrap_width': 35 # 每行大约的字符数
    }
}

# --- 辅助函数 (保持不变) ---
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

# <--- 新增: 绘制带背景和自动换行的文本框 ---
def draw_wrapped_text_box(draw, text, font, style, image_size):
    if not text: return
    
    img_width, img_height = image_size
    margin = style['margin']
    padding = style['box_padding']
    line_spacing = style['line_spacing']
    
    # 使用textwrap模块进行文本换行
    wrapper = textwrap.TextWrapper(width=style['wrap_width'])
    wrapped_lines = wrapper.wrap(text)
    
    # 计算文本块的总高度和最大宽度
    max_line_width = 0
    total_text_height = 0
    line_heights = []
    for line in wrapped_lines:
        try: line_bbox = draw.textbbox((0, 0), line, font=font)
        except AttributeError: line_bbox = font.getbbox(line)
        line_width = line_bbox[2] - line_bbox[0]
        line_height = line_bbox[3] - line_bbox[1]
        
        if line_width > max_line_width: max_line_width = line_width
        total_text_height += line_height
        line_heights.append(line_height)
        
    total_text_height += line_spacing * (len(wrapped_lines) - 1)
    
    # 计算背景框的位置和大小
    box_width = max_line_width + padding * 2
    box_height = total_text_height + padding * 2
    box_x0 = margin
    box_y0 = margin
    
    # 绘制半透明背景
    draw.rectangle([box_x0, box_y0, box_x0 + box_width, box_y0 + box_height], fill=style['background_color'])
    
    # 逐行绘制文本
    current_y = box_y0 + padding
    for i, line in enumerate(wrapped_lines):
        draw.text((box_x0 + padding, current_y), line, font=font, fill=style['fill_color'])
        current_y += line_heights[i] + line_spacing

def draw_single_route_image(route_data, holds_coords, base_image, fonts, output_dir):
    image = base_image.copy()
    draw = ImageDraw.Draw(image, "RGBA")
    
    offset_x = STYLE_CONFIG.get('center_offset_x', 0)
    offset_y = STYLE_CONFIG.get('center_offset_y', 0)

    # 绘制指定脚点
    if 'holds' in route_data and 'foot' in route_data['holds']:
        style = STYLE_CONFIG['foot']
        for hold_id in route_data['holds']['foot']:
            str_hold_id = str(hold_id).lower()
            if str_hold_id in holds_coords:
                center_xy = (holds_coords[str_hold_id]['x'] + offset_x, holds_coords[str_hold_id]['y'] + offset_y)
                draw_hold(draw, center_xy, style)

    # 绘制箭头
    prev_coords = None
    if 'moves' in route_data:
        for move in route_data['moves']:
            hold_id = str(move['hold_id']).lower()
            if hold_id not in holds_coords: continue
            current_coords = (holds_coords[hold_id]['x'] + offset_x, holds_coords[hold_id]['y'] + offset_y)
            if prev_coords: draw_arrow(draw, prev_coords, current_coords)
            prev_coords = current_coords
        
        # 绘制手点
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

    # 绘制标题
    title_style = STYLE_CONFIG['title_style']
    route_name = route_data.get('routeName', route_data.get('name', 'N/A'))
    difficulty = route_data.get('difficulty', route_data.get('grade', 'N/A'))
    author = route_data.get('author', 'N/A')
    route_info_text = f"{route_name} | {difficulty} | by {author}"
    
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
    
    # <--- 新增: 绘制指导建议文本框 ---
    beta_text = route_data.get('beta')
    if beta_text:
        draw_wrapped_text_box(draw, beta_text, fonts['beta'], STYLE_CONFIG['beta_text_style'], image.size)

    # 保存图片
    quantized_image = image.quantize(colors=256, dither=Image.Dither.NONE)
    safe_filename = re.sub(r'[\\/*?:"<>|]', "", route_name)
    output_filename = f"{difficulty.replace(' ', '_')}_{safe_filename.replace(' ', '_')}.png"
    output_path = output_dir / output_filename
    quantized_image.save(output_path, 'PNG', optimize=True)
    print(f"  ✓ Saved (and compressed): {output_path}")

def get_variational_font(path, size, variation):
    font = ImageFont.truetype(path, size)
    try:
        font.set_variation_by_name("Bold")
    except (AttributeError, TypeError):
        try:
            font.set_variation_by_axis_name('wght', variation)
        except (AttributeError, TypeError):
             pass 
    return font

def process_all_routes(routes_db_path, holds_coords_path, base_image_path, output_dir):
    try:
        print(f"Loading routes database: {routes_db_path}")
        with open(routes_db_path, 'r', encoding='utf-8') as f: 
            raw_data = json.load(f)
        
        if isinstance(raw_data, dict): all_routes_data = raw_data.get('routes', [])
        elif isinstance(raw_data, list): all_routes_data = raw_data
        else: all_routes_data = []

        print(f"Loading hold coordinates: {holds_coords_path}")
        with open(holds_coords_path, 'r', encoding='utf-8') as f: 
            holds_coords = {k.lower(): v for k, v in json.load(f).items()}
        
        print(f"Loading base image: {base_image_path}")
        base_image = Image.open(base_image_path).convert("RGBA")
    except FileNotFoundError as e:
        print(f"错误: 必需文件未找到 - {e}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"错误: 解析JSON文件时出错 - {e}", file=sys.stderr)
        sys.exit(1)

    fonts = {}
    try:
        # 加载英文字体
        main_style = STYLE_CONFIG['main_font_style']
        fonts['main'] = get_variational_font(main_style['font_path'], main_style['font_size'], main_style['font_variation'])
        title_style = STYLE_CONFIG['title_style']
        fonts['title'] = get_variational_font(title_style['font_path'], title_style['font_size'], title_style['font_variation'])
        
        # <--- 新增: 加载中文字体 ---
        beta_style = STYLE_CONFIG['beta_text_style']
        fonts['beta'] = ImageFont.truetype(beta_style['font_path'], beta_style['font_size'])
    
    except IOError as e:
        print(f"错误: 字体文件未找到。请确保字体文件存在于 'fonts/' 目录下 - {e}", file=sys.stderr)
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not all_routes_data:
        print("数据库中没有找到任何线路。")
        return

    print(f"\nProcessing {len(all_routes_data)} routes...")
    for i, route_data in enumerate(all_routes_data):
        route_name = route_data.get('routeName', route_data.get('name', 'N/A'))
        print(f"[{i+1}/{len(all_routes_data)}] Drawing route: '{route_name}'")
        draw_single_route_image(route_data, holds_coords, base_image, fonts, output_dir)
    
    print("\nAll routes processed successfully!")

# --- 主程序入口 (保持不变) ---
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="在攀岩墙底图上绘制线路并保存为图片。")
    parser.add_argument("--routes_database_file", required=True, help="包含所有线路定义的 JSON 文件路径。")
    parser.add_argument("--holds_coords_path", required=True, help="包含岩点坐标的 JSON 文件路径。")
    parser.add_argument("--base_image_path", required=True, help="作为背景的攀岩墙图片路径。")
    parser.add_argument("--output_dir", required=True, help="保存生成线路图片的目录。")
    
    args = parser.parse_args()

    routes_db_path = Path(args.routes_database_file)
    holds_coords_path = Path(args.holds_coords_path)
    base_image_path = Path(args.base_image_path)
    output_dir = Path(args.output_dir)

    if not routes_db_path.exists():
        print(f"错误: 路线数据库文件不存在 '{routes_db_path}'", file=sys.stderr)
        sys.exit(1)
    if not holds_coords_path.exists():
        print(f"错误: 岩点坐标文件 '{holds_coords_path}' 不存在。", file=sys.stderr)
        sys.exit(1)
    if not base_image_path.exists():
        print(f"错误: 原始图片 '{base_image_path}' 不存在。", file=sys.stderr)
        sys.exit(1)
    
    process_all_routes(routes_db_path, holds_coords_path, base_image_path, output_dir)
