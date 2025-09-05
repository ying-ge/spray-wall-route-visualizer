import json
import math
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import argparse
import re
import sys

# --- 样式配置 ---
# 'font_path' has been removed from here as it will now be passed as an argument.
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
        'font_size': 75,
        'font_variation': 700, 
        'fill_color': (255, 255, 255),
        'outline_color': (0, 0, 0),
        'outline_width': 4,
        'margin': 60
    },
    'main_font_style': {
        'font_size': 50,
        'font_variation': 700 
    }
}

# --- 辅助函数 (保持不变) ---
def draw_arrow(draw, start_xy, end_xy):
    x1, y1 = start_xy; x2, y2 = end_xy
    draw.line([start_xy, end_xy], fill=STYLE_CONFIG['arrow_color'], width=STYLE_CONFIG['arrow_width'])
    angle = math.atan2(y2 - y1, x2 - x1); length = STYLE_CONFIG['arrowhead_length']; head_
