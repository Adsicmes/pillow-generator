# Pillow 代码生成器

一个可视化的Pillow模板编排工具，帮助您快速创建和生成PIL/Pillow代码。

！本README完全使用ai生成，项目代码大幅度使用了ai，请注意甄别！

## 功能特性

### 🎨 可视化编辑
- **直观的画布界面**：使用QGraphicsView实现的可视化编辑界面
- **拖拽操作**：支持图层的拖拽移动和实时预览
- **缩放和平移**：鼠标滚轮缩放，中键拖拽平移视图
- **网格背景**：帮助精确定位的背景网格

### 🖼️ 图层管理
- **底图支持**：设置模板的基础底图
- **图片层**：添加多个图片层，支持缩放、旋转、透明度调整
- **文字层**：添加文字层，支持自定义字体、大小、颜色、对齐方式
- **图层面板**：直观的图层管理，支持显示/隐藏、重排序
- **实时预览**：所有修改实时显示在画布上

### 🛠️ 属性编辑
- **位置控制**：精确的X/Y坐标设置
- **尺寸调整**：图片层的宽高调整
- **样式设置**：透明度、旋转角度调整
- **文字属性**：字体大小、颜色、对齐方式设置
- **参数化选项**：支持将路径和文字设为函数参数

### 📝 代码生成
- **自动生成**：根据设计自动生成完整的Pillow代码
- **参数化支持**：生成可参数化的函数，便于重用
- **相对路径**：智能处理文件路径，使用相对路径保证可移植性
- **代码预览**：实时预览生成的代码
- **一键复制/保存**：支持复制到剪贴板或保存为.py文件

### 💾 项目管理
- **项目保存**：以.pgp格式保存完整的项目文件
- **项目加载**：快速载入之前的设计
- **相对路径管理**：自动处理资源文件的相对路径

## 系统要求

- Python 3.12+
- PySide6 6.9.2+
- Pillow 11.3.0+

## 安装和运行

1. 克隆项目到本地：
```bash
git clone <repository-url>
cd pillow-generator
```

2. 安装依赖（推荐使用uv）：
```bash
uv install
```

3. 运行应用：
```bash
python main.py
```

## 使用指南

### 1. 创建新项目
- 启动应用后会自动创建新项目
- 或通过 `文件 -> 新建项目` 创建

### 2. 设置底图
- 点击 `文件 -> 设置底图` 或工具栏的"设置底图"按钮
- 选择您的模板底图文件

### 3. 添加图层
- **添加图片层**：点击"添加图片"按钮，选择图片文件
- **添加文字层**：点击"添加文字"按钮，自动创建文字层

### 4. 编辑属性
- 在画布中选择图层，或在图层面板中点击选择
- 在属性面板中调整位置、大小、样式等属性
- 勾选"作为参数"可将该属性设为函数参数

### 5. 生成代码
- 在代码生成器面板中点击"生成代码"
- 查看生成的Pillow代码
- 可复制到剪贴板或保存为Python文件

### 6. 保存项目
- `文件 -> 保存项目` 保存到当前文件
- `文件 -> 另存为` 保存到新位置

## 项目结构

```
pillow-generator/
├── main.py                 # 应用程序入口
├── src/
│   ├── core/              # 核心功能模块
│   │   ├── models.py      # 数据模型定义
│   │   └── project_manager.py  # 项目文件管理
│   └── ui/                # 用户界面模块
│       ├── main_window.py # 主窗口
│       ├── canvas_view.py # 画布视图
│       ├── layer_panel.py # 图层面板
│       ├── property_panel.py # 属性面板
│       └── code_generator.py # 代码生成器
├── pyproject.toml         # 项目配置
└── README.md             # 说明文档
```

## 生成的代码示例

```python
from PIL import Image, ImageDraw, ImageFont
import os

def generate_image(output_path: str, user_name: str, avatar_path: str):
    """
    生成图像 - 用户卡片模板
    
    参数:
        output_path: 输出图片路径
        user_name: 用户名文字
        avatar_path: 头像图片路径
    """
    # 加载底图
    base_image = Image.open(r"templates/card_bg.png")
    result = base_image.copy()
    
    # 添加图片层
    image_0 = Image.open(avatar_path)
    image_0 = image_0.resize((100, 100))
    result.paste(image_0, (50, 50), image_0)
    
    # 添加文字层
    draw = ImageDraw.Draw(result)
    try:
        font_0 = ImageFont.truetype(r"fonts/Arial.ttf", 24)
    except:
        font_0 = ImageFont.load_default()
    draw.text((200, 75), user_name, font=font_0, fill=(0, 0, 0, 255))
    
    # 保存结果
    result.save(output_path)
    print(f"图像已保存到: {output_path}")

# 示例调用:
if __name__ == "__main__":
    generate_image("output.png", "张三", "avatar.jpg")
```

## 技术特性

### 架构设计
- **MVC模式**：清晰的模型-视图-控制器分离
- **信号槽机制**：基于Qt的事件驱动架构
- **模块化设计**：高内聚低耦合的模块结构

### UI框架
- **PySide6**：现代化的Python GUI框架
- **QGraphicsView**：高性能的2D图形显示
- **停靠窗口**：灵活的界面布局

### 数据管理
- **JSON格式**：人类可读的项目文件格式
- **相对路径**：保证项目的可移植性
- **类型安全**：使用dataclass和类型提示

## 贡献

欢迎提交Issue和Pull Request！

## 许可证

MIT License