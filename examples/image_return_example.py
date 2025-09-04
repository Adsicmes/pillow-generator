"""
返回Image对象功能示例

此示例展示了新的代码生成器功能：生成的函数返回PIL Image对象而不是直接保存文件。
这使得生成的函数更加灵活，可以进行后续处理。
"""

from PIL import Image, ImageDraw, ImageFont
import os

def generate_business_card():
    """
    生成名片 - 返回Image对象示例
    
    返回:
        PIL.Image.Image: 生成的图像对象
    """
    # 创建底图
    result = Image.new("RGBA", (400, 250), (255, 255, 255, 255))
    
    # 添加文字层
    draw = ImageDraw.Draw(result)
    
    # 名字
    try:
        name_font = ImageFont.truetype("arial.ttf", 24)
    except:
        name_font = ImageFont.load_default()
    
    # 职位
    try:
        title_font = ImageFont.truetype("arial.ttf", 16)
    except:
        title_font = ImageFont.load_default()
    
    # 绘制文字
    draw.text((50, 80), "张三", font=name_font, fill=(0, 0, 0, 255))
    draw.text((50, 120), "软件工程师", font=title_font, fill=(100, 100, 100, 255))
    draw.text((50, 150), "电话: 138-0000-0000", font=title_font, fill=(100, 100, 100, 255))
    draw.text((50, 180), "邮箱: zhangsan@company.com", font=title_font, fill=(100, 100, 100, 255))
    
    # 返回生成的图像
    return result


def generate_social_post(title: str, content: str):
    """
    生成社交媒体帖子 - 参数化示例
    
    参数:
        title: 帖子标题
        content: 帖子内容
        
    返回:
        PIL.Image.Image: 生成的图像对象
    """
    # 创建底图
    result = Image.new("RGBA", (600, 400), (240, 240, 240, 255))
    
    # 添加文字层
    draw = ImageDraw.Draw(result)
    
    # 标题字体
    try:
        title_font = ImageFont.truetype("arial.ttf", 32)
    except:
        title_font = ImageFont.load_default()
    
    # 内容字体
    try:
        content_font = ImageFont.truetype("arial.ttf", 18)
    except:
        content_font = ImageFont.load_default()
    
    # 绘制标题
    title_bbox = draw.textbbox((0, 0), title, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    title_x = (600 - title_width) // 2
    draw.text((title_x, 80), title, font=title_font, fill=(50, 50, 50, 255))
    
    # 绘制内容
    content_bbox = draw.textbbox((0, 0), content, font=content_font)
    content_width = content_bbox[2] - content_bbox[0]
    content_x = (600 - content_width) // 2
    draw.text((content_x, 200), content, font=content_font, fill=(80, 80, 80, 255))
    
    # 返回生成的图像
    return result


def demonstrate_flexibility():
    """演示返回Image对象的灵活性"""
    print("=== 返回Image对象功能演示 ===")
    
    # 1. 生成名片
    print("1. 生成名片...")
    business_card = generate_business_card()
    
    # 可以进行后续处理
    # 例如：调整尺寸
    resized_card = business_card.resize((200, 125))
    
    # 例如：添加边框
    bordered_card = Image.new("RGBA", (220, 145), (0, 0, 0, 255))
    bordered_card.paste(resized_card, (10, 10))
    
    # 保存最终结果
    bordered_card.save("examples/output/processed_business_card.png")
    print("   已保存处理后的名片到 examples/output/processed_business_card.png")
    
    # 2. 生成多个社交媒体帖子
    print("2. 生成社交媒体帖子...")
    posts_data = [
        ("新产品发布", "我们很高兴宣布新产品正式发布！"),
        ("感谢客户", "感谢所有客户的支持与信任！"),
        ("团队招聘", "我们正在寻找优秀的人才加入团队！")
    ]
    
    # 批量生成并合并
    combined_width = 600 * len(posts_data)
    combined_image = Image.new("RGBA", (combined_width, 400), (255, 255, 255, 255))
    
    for i, (title, content) in enumerate(posts_data):
        post_image = generate_social_post(title, content)
        combined_image.paste(post_image, (i * 600, 0))
    
    combined_image.save("examples/output/combined_social_posts.png")
    print(f"   已保存 {len(posts_data)} 个帖子的组合图到 examples/output/combined_social_posts.png")
    
    # 3. 演示图像处理管道
    print("3. 图像处理管道演示...")
    base_image = generate_business_card()
    
    # 处理步骤
    steps = [
        ("original", base_image),
        ("grayscale", base_image.convert("L").convert("RGBA")),
        ("rotated", base_image.rotate(45, expand=True)),
        ("thumbnail", base_image.copy())
    ]
    
    # 缩略图
    steps[3][1].thumbnail((100, 62))
    
    # 保存每个步骤
    for step_name, img in steps:
        img.save(f"examples/output/pipeline_{step_name}.png")
    
    print("   已保存图像处理管道的各个步骤")
    
    print("\n=== 功能优势 ===")
    print("✓ 返回Image对象提供了更大的灵活性")
    print("✓ 可以进行后续图像处理和组合")
    print("✓ 支持批量处理和自动化工作流")
    print("✓ 调用者可以决定何时以及如何保存图像")


if __name__ == "__main__":
    # 确保输出目录存在
    os.makedirs("examples/output", exist_ok=True)
    
    # 运行演示
    demonstrate_flexibility()
