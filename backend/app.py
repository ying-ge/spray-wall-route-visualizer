from flask import Flask, request, jsonify
import cv2
import numpy as np
import os

app = Flask(__name__)

def dummy_detect_points(img):
    # 假设岩点识别，返回随机点
    h, w, _ = img.shape
    points = [(int(np.random.uniform(0, w)), int(np.random.uniform(0, h))) for _ in range(6)]
    return points

def dummy_plan_route(points):
    # 简单地按顺序连线
    return points

def draw_route(img, points, route):
    # 在图片上画点和连线
    for pt in points:
        cv2.circle(img, pt, 10, (0, 255, 0), -1)
    for i in range(len(route)-1):
        cv2.line(img, route[i], route[i+1], (0, 0, 255), 3)
    return img

@app.route('/api/detect', methods=['POST'])
def detect():
    file = request.files['file']
    img_array = np.frombuffer(file.read(), np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    points = dummy_detect_points(img)
    route = dummy_plan_route(points)
    img_result = draw_route(img, points, route)
    result_path = os.path.join('static', 'result.jpg')
    cv2.imwrite(result_path, img_result)
    return jsonify({'result_image': 'http://localhost:5000/static/result.jpg'})

if __name__ == '__main__':
    os.makedirs('static', exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=True)
