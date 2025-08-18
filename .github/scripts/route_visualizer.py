import cv2
import numpy as np
import json
import os
import argparse
from pathlib import Path

def load_config(config_path):
    """加载包含攀爬路线信息的配置文件"""
    with open(config_path, 'r') as f:
        return json.load(f)

def visualize_route(image_path, config, output_path=None):
    """可视化攀爬路线，标记岩点并添加序号和箭头"""
    # 读取图片
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"无法读取图片: {image_path}")
    
    # 获取图片尺寸
    height, width = img.shape[:2]
    
    # 创建图像副本
    result = img.copy()
    
    # 获取路线点坐标
    holds = config.get('holds', [])
    
    # 设置字体和线条属性
    font = cv2.FONT_HERSHEY_SIMPLEX
    circle_color = config.get('circle_color', (0, 255, 0))  # 绿色圆圈
    text_color = config.get('text_color', (255, 255, 255))  # 白色文本
    shadow_color = config.get('shadow_color', (0, 0, 0))    # 黑色阴影
    arrow_color = config.get('arrow_color', (0, 0, 255))    # 红色箭头
    circle_thickness = config.get('circle_thickness', 3)
    text_thickness = config.get('text_thickness', 2)
    shadow_thickness = text_thickness + 2  # 阴影比文本粗一些
    arrow_thickness = config.get('arrow_thickness', 2)
    
    # 计算合适的圆圈大小和字体大小（基于图像尺寸）
    circle_radius = int(min(width, height) * 0.02)
    font_scale = min(width, height) * 0.001
    
    # 绘制每个岩点和序号
    for i, hold in enumerate(holds):
        x, y = hold['x'], hold['y']
        
        # 确保坐标在图像范围内
        if 0 <= x < width and 0 <= y < height:
            # 绘制圆圈
            cv2.circle(result, (x, y), circle_radius, circle_color, circle_thickness)
            
            # 添加序号（先绘制阴影，再绘制文本）
            text = str(i + 1)
            text_size = cv2.getTextSize(text, font, font_scale, text_thickness)[0]
            text_x = x - text_size[0] // 2
            text_y = y + text_size[1] // 2
            
            # 绘制黑色阴影/轮廓（在文本下方多个位置绘制以形成轮廓效果）
            for dx, dy in [(1,1), (1,-1), (-1,1), (-1,-1), (0,1), (1,0), (0,-1), (-1,0)]:
                cv2.putText(result, text, (text_x+dx, text_y+dy), font, font_scale, shadow_color, shadow_thickness)
            
            # 绘制白色文本
            cv2.putText(result, text, (text_x, text_y), font, font_scale, text_color, text_thickness)
    
    # 绘制攀爬路径（箭头）
    for i in range(len(holds) - 1):
        start_x, start_y = holds[i]['x'], holds[i]['y']
        end_x, end_y = holds[i+1]['x'], holds[i+1]['y']
        
        # 计算箭头起点和终点
        # 箭头不从圆心出发，而是从圆的边缘开始
        angle = np.arctan2(end_y - start_y, end_x - start_x)
        start_x_adjusted = int(start_x + circle_radius * np.cos(angle))
        start_y_adjusted = int(start_y + circle_radius * np.sin(angle))
        
        # 箭头不到圆心，而是到圆的边缘
        end_x_adjusted = int(end_x - circle_radius * np.cos(angle))
        end_y_adjusted = int(end_y - circle_radius * np.sin(angle))
        
        # 绘制带箭头的线
        cv2.arrowedLine(result, (start_x_adjusted, start_y_adjusted), 
                        (end_x_adjusted, end_y_adjusted), 
                        arrow_color, arrow_thickness, tipLength=0.3)
    
    # 保存结果图像
    if output_path is None:
        # 创建输出文件路径
        base_path = os.path.splitext(image_path)[0]
        output_path = f"{base_path}_route.jpg"
    
    # 确保输出目录存在
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    # 保存图像
    cv2.imwrite(output_path, result)
    print(f"路线可视化图已保存到: {output_path}")
    
    return output_path

def main():
    parser = argparse.ArgumentParser(description='攀岩路线可视化工具')
    parser.add_argument('--image', type=str, required=True, help='攀岩墙照片路径')
    parser.add_argument('--config', type=str, required=True, help='路线配置文件路径')
    parser.add_argument('--output', type=str, help='输出图片路径')
    
    args = parser.parse_args()
    
    config = load_config(args.config)
    visualize_route(args.image, config, args.output)

if __name__ == "__main__":
    main()
