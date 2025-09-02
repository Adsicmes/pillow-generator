#!/usr/bin/env python3
"""
示例：如何使用Pillow代码生成器生成的代码
"""

# 这是一个由Pillow代码生成器生成的示例函数
from PIL import Image, ImageDraw, ImageFont
import os

def generate_business_card(output_path: str, name: str = "张三", title: str = "软件工程师", logo_path: str = "logo.png"):
    """
    生成商务名片
    
    参数:
        output_path: 输出图片路径
        name: 姓名
        title: 职位
        logo_path: 公司logo路径
    """
    # 创建底图（如果没有底图文件的话）
    result = Image.new("RGBA", (400, 250), (255, 255, 255, 255))
    
    # 添加边框
    draw = ImageDraw.Draw(result)
    draw.rectangle([5, 5, 395, 245], outline=(0, 0, 0, 255), width=2)
    
    # 添加logo（如果存在）
    if os.path.exists(logo_path):
        try:
            logo = Image.open(logo_path)
            logo = logo.resize((60, 60))
            if logo.mode == "RGBA":
                result.paste(logo, (20, 20), logo)
            else:
                result.paste(logo, (20, 20))
        except Exception as e:
            print(f"无法加载logo: {e}")
    
    # 添加姓名文字
    try:
        # 尝试使用系统字体，如果失败则使用默认字体
        name_font = ImageFont.truetype("arial.ttf", 24)
    except:
        try:
            name_font = ImageFont.truetype("simhei.ttf", 24)  # Windows中文字体
        except:
            name_font = ImageFont.load_default()
    
    draw.text((100, 30), name, font=name_font, fill=(0, 0, 0, 255))
    
    # 添加职位文字
    try:
        title_font = ImageFont.truetype("arial.ttf", 16)
    except:
        try:
            title_font = ImageFont.truetype("simhei.ttf", 16)
        except:
            title_font = ImageFont.load_default()
    
    draw.text((100, 65), title, font=title_font, fill=(100, 100, 100, 255))
    
    # 添加联系信息
    contact_font = title_font
    draw.text((20, 150), "电话: +86 138-0000-0000", font=contact_font, fill=(50, 50, 50, 255))
    draw.text((20, 175), "邮箱: example@company.com", font=contact_font, fill=(50, 50, 50, 255))
    draw.text((20, 200), "地址: 北京市朝阳区xx街道", font=contact_font, fill=(50, 50, 50, 255))
    
    # 保存结果
    result.save(output_path)
    print(f"商务名片已生成: {output_path}")


def generate_social_media_post(output_path: str, title: str = "精彩内容", subtitle: str = "不要错过！", bg_color: tuple = (70, 130, 180)):
    """
    生成社交媒体帖子图片
    
    参数:
        output_path: 输出路径
        title: 主标题
        subtitle: 副标题
        bg_color: 背景颜色RGB
    """
    # 创建底图
    width, height = 800, 800
    result = Image.new("RGBA", (width, height), (*bg_color, 255))
    
    draw = ImageDraw.Draw(result)
    
    # 添加渐变背景效果（简单实现）
    for y in range(height):
        alpha = int(255 * (1 - y / height * 0.3))
        color = (*bg_color, alpha)
        draw.line([(0, y), (width, y)], fill=color)
    
    # 添加主标题
    try:
        title_font = ImageFont.truetype("arial.ttf", 48)
    except:
        title_font = ImageFont.load_default()
    
    # 计算文字居中位置
    title_bbox = draw.textbbox((0, 0), title, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    title_x = (width - title_width) // 2
    
    draw.text((title_x, 300), title, font=title_font, fill=(255, 255, 255, 255))
    
    # 添加副标题
    try:
        subtitle_font = ImageFont.truetype("arial.ttf", 24)
    except:
        subtitle_font = ImageFont.load_default()
    
    subtitle_bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
    subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
    subtitle_x = (width - subtitle_width) // 2
    
    draw.text((subtitle_x, 380), subtitle, font=subtitle_font, fill=(255, 255, 255, 200))
    
    # 保存结果
    result.save(output_path)
    print(f"社交媒体帖子已生成: {output_path}")


def main():
    """主函数 - 演示如何使用生成的函数"""
    print("Pillow代码生成器 - 示例输出")
    print("=" * 40)
    
    # 确保输出目录存在
    os.makedirs("output", exist_ok=True)
    
    # 生成商务名片
    print("\n1. 生成商务名片...")
    generate_business_card(
        "output/business_card.png",
        name="李明",
        title="Python开发工程师"
    )
    
    # 生成社交媒体帖子
    print("\n2. 生成社交媒体帖子...")
    generate_social_media_post(
        "output/social_post.png",
        title="Pillow代码生成器",
        subtitle="可视化创建PIL代码",
        bg_color=(34, 139, 34)  # 森林绿
    )
    
    print("\n✅ 所有示例图片已生成完成！")
    print("请查看 output/ 目录中的文件")


if __name__ == "__main__":
    main()
