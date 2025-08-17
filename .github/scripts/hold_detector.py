import cv2
import numpy as np
import json
import os
import argparse
from pathlib import Path

def detect_holds(image_path, output_json=None, debug_image=None):
    """
    检测攀岩墙照片中的岩点并返回它们的坐标
    
    参数:
    image_path - 攀岩墙照片的路径
    output_json - 输出JSON文件的路径(可选)
    debug_image - 调试图像的输出路径(可选)
    
    返回:
    包含所有检测到的岩点坐标的列表
    """
    # 读取图片
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"无法读取图片: {image_path}")
    
    # 创建输出图像副本(用于调试)
    debug_img = img.copy()
    
    # 转换到HSV颜色空间，有助于分离不同颜色的岩点
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # 预处理步骤
    # 1. 高斯模糊以减少噪声
    blurred = cv2.GaussianBlur(img, (5, 5), 0)
    
    # 2. 创建多个颜色通道的掩码来检测不同颜色的岩点
    # 这些阈值需要根据实际的岩点颜色进行调整
    color_ranges = [
        # 红色(红色在HSV中分布在0和180附近)
        [(0, 50, 50), (10, 255, 255)],
        [(170, 50, 50), (180, 255, 255)],
        # 蓝色
        [(100, 50, 50), (130, 255, 255)],
        # 绿色
        [(40, 50, 50), (80, 255, 255)],
        # 黄色
        [(20, 50, 50), (40, 255, 255)],
        # 粉色/紫色
        [(130, 50, 50), (170, 255, 255)]
    ]
    
    # 综合掩码
    combined_mask = np.zeros((img.shape[0], img.shape[1]), dtype=np.uint8)
    
    # 为每个颜色创建掩码
    for lower, upper in color_ranges:
        lower = np.array(lower)
        upper = np.array(upper)
        mask = cv2.inRange(hsv, lower, upper)
        combined_mask = cv2.bitwise_or(combined_mask, mask)
    
    # 3. 形态学操作以清理掩码
    kernel = np.ones((5, 5), np.uint8)
    mask_cleaned = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, kernel)
    mask_cleaned = cv2.morphologyEx(mask_cleaned, cv2.MORPH_CLOSE, kernel)
    
    # 4. 边缘检测
    edges = cv2.Canny(mask_cleaned, 50, 150)
    
    # 5. 寻找轮廓
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # 过滤太小的轮廓(可能是噪声)
    min_contour_area = 100  # 可根据图像尺寸调整
    filtered_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > min_contour_area]
    
    # 对于每个轮廓，计算中心点
    holds = []
    for i, cnt in enumerate(filtered_contours):
        # 计算轮廓的矩
        M = cv2.moments(cnt)
        if M["m00"] != 0:
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])
            
            # 保存岩点信息
            holds.append({
                "x": cX,
                "y": cY,
                "area": cv2.contourArea(cnt),
                "description": f"自动检测的岩点 #{i+1}"
            })
            
            # 在调试图像上绘制轮廓和中心点
            cv2.drawContours(debug_img, [cnt], -1, (0, 255, 0), 2)
            cv2.circle(debug_img, (cX, cY), 5, (255, 0, 0), -1)
            cv2.putText(debug_img, f"#{i+1}", (cX - 10, cY - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
    
    # 按照从下到上的顺序对岩点进行排序(因为攀岩通常从下往上爬)
    holds = sorted(holds, key=lambda h: h["y"], reverse=True)
    
    # 重新编号岩点
    for i, hold in enumerate(holds):
        hold["description"] = f"自动检测的岩点 #{i+1}"
    
    # 如果需要，保存调试图像
    if debug_image:
        cv2.imwrite(debug_image, debug_img)
        print(f"调试图像已保存到: {debug_image}")
    
    # 准备输出JSON
    output_data = {
        "route_name": "自动检测的路线",
        "difficulty": "未知",
        "description": "通过计算机视觉自动检测的岩点",
        "author": "AI检测系统",
        "date_created": "自动生成",
        "circle_color": [0, 255, 0],
        "text_color": [255, 255, 255],
        "arrow_color": [0, 0, 255],
        "holds": holds
    }
    
    # 如果指定了输出路径，保存JSON文件
    if output_json:
        os.makedirs(os.path.dirname(os.path.abspath(output_json)), exist_ok=True)
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        print(f"岩点坐标已保存到: {output_json}")
    
    return holds

def main():
    parser = argparse.ArgumentParser(description='攀岩墙岩点检测工具')
    parser.add_argument('--image', type=str, required=True, help='攀岩墙照片路径')
    parser.add_argument('--output', type=str, help='输出JSON文件路径')
    parser.add_argument('--debug', type=str, help='调试图像输出路径')
    
    args = parser.parse_args()
    
    detect_holds(args.image, args.output, args.debug)

if __name__ == "__main__":
    main()
