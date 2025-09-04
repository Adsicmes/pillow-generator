"""
底图参数化功能示例

此示例展示了如何使用底图参数化功能生成的代码。
当底图设置为参数时，生成的函数可以接受不同的底图文件，
使同一个模板可以应用于多个不同的底图。
"""

from PIL import Image, ImageDraw, ImageFont
import os

def generate_image_with_parameter(base_image_path: str):
    """
    生成图像 - 参数化底图示例
    
    参数:
        base_image_path: 底图路径
        
    返回:
        PIL.Image.Image: 生成的图像对象
    """
    # 加载底图
    base_image = Image.open(base_image_path)
    result = base_image.copy()
    
    # 添加文字层
    draw = ImageDraw.Draw(result)
    
    # 示例文字：标题
    try:
        title_font = ImageFont.truetype("arial.ttf", 36)
    except:
        title_font = ImageFont.load_default()
    
    # 计算文字位置和尺寸
    title_text = "参数化底图示例"
    text_bbox = draw.textbbox((0, 0), title_text, font=title_font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    
    # 水平居中，垂直偏上
    image_width, image_height = result.size
    text_x = (image_width - text_width) // 2
    text_y = image_height // 4
    
    # 绘制文字
    draw.text((text_x, text_y), title_text, font=title_font, fill=(255, 255, 255, 255))
    
    # 返回生成的图像
    return result


def generate_image_without_parameter():
    """
    生成图像 - 固定底图示例
    
    返回:
        PIL.Image.Image: 生成的图像对象
    """
    # 加载固定底图
    base_image = Image.open(r"examples/sample_background.png")
    result = base_image.copy()
    
    # 添加文字层
    draw = ImageDraw.Draw(result)
    
    # 示例文字：标题
    try:
        title_font = ImageFont.truetype("arial.ttf", 36)
    except:
        title_font = ImageFont.load_default()
    
    # 绘制文字
    draw.text((100, 100), "固定底图示例", font=title_font, fill=(0, 0, 0, 255))
    
    # 返回生成的图像
    return result


if __name__ == "__main__":
    # 演示参数化底图的使用
    print("=== 底图参数化功能演示 ===")
    
    # 使用不同的底图文件
    backgrounds = [
        "examples/background1.png",
        "examples/background2.png", 
        "examples/background3.png"
    ]
    
    # 确保输出目录存在
    os.makedirs("examples/output", exist_ok=True)
    
    for i, bg_path in enumerate(backgrounds):
        if os.path.exists(bg_path):
            # 生成图像
            image = generate_image_with_parameter(bg_path)
            # 保存图像
            output_file = f"examples/output/parametric_result_{i+1}.png"
            image.save(output_file)
            print(f"图像已生成并保存到: {output_file}")
        else:
            print(f"底图文件不存在: {bg_path}")
    
    print("\n=== 功能对比 ===")
    print("1. 参数化底图：可以使用任意底图文件")
    print("2. 固定底图：只能使用预设的底图文件")
    print("3. 参数化使模板更灵活，可重用性更强")
