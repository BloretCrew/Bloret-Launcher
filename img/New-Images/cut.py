import cv2
import os
import numpy as np

def crop_window(image_path, output_path):
    # 使用 numpy 读取，以支持中文路径
    try:
        img = cv2.imdecode(np.fromfile(image_path, dtype=np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            print(f"警告: 无法读取文件，跳过: {image_path}")
            return
    except Exception as e:
        print(f"读取出错: {image_path}, 错误: {e}")
        return

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 边缘检测
    edges = cv2.Canny(gray, 50, 150)

    # 查找轮廓
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # 检查是否找到了轮廓，防止 max() 函数崩溃
    if not contours:
        print(f"未在图中找到明确轮廓，跳过: {image_path}")
        return

    # 找到最大轮廓
    max_contour = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(max_contour)

    # 裁剪
    cropped = img[y:y+h, x:x+w]

    # 使用 imencode 保存，以支持中文输出路径
    ext = os.path.splitext(output_path)[1]
    result, nparray = cv2.imencode(ext, cropped)
    if result:
        nparray.tofile(output_path)
    else:
        print(f"保存失败: {output_path}")

def batch_crop(input_folder, output_folder):
    if not os.path.exists(input_folder):
        print(f"错误: 输入文件夹 '{input_folder}' 不存在")
        return

    os.makedirs(output_folder, exist_ok=True)
    
    # 过滤掉隐藏文件（如 .DS_Store）
    files = [f for f in os.listdir(input_folder) if not f.startswith('.')]
    
    for filename in files:
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            input_path = os.path.join(input_folder, filename)
            output_path = os.path.join(output_folder, filename)
            crop_window(input_path, output_path)
            print(f"成功处理: {filename}")

# 示例用法
if __name__ == "__main__":
    batch_crop("screenshots", "cropped")