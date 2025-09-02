"""
代码生成器实现
"""
import os
from typing import List, Dict, Any

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout,
    QLabel, QGroupBox, QCheckBox, QLineEdit, QFormLayout, QFileDialog,
    QMessageBox, QSplitter, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from ..core.models import (
    ProjectModel, BaseLayer, ImageLayer, TextLayer, 
    LayerType, TextAlignment
)


class CodeGenerator(QWidget):
    """代码生成器"""
    
    def __init__(self, project_model: ProjectModel, parent=None):
        super().__init__(parent)
        
        self.project_model = project_model
        
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel("代码生成器")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title_label)
        
        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Vertical)
        layout.addWidget(splitter)
        
        # 上部分：参数配置
        config_widget = QWidget()
        splitter.addWidget(config_widget)
        
        config_layout = QVBoxLayout(config_widget)
        
        # 函数配置组
        function_group = QGroupBox("函数配置")
        config_layout.addWidget(function_group)
        
        function_layout = QFormLayout(function_group)
        
        # 函数名
        self.function_name_edit = QLineEdit("generate_image")
        function_layout.addRow("函数名:", self.function_name_edit)
        
        # 输出路径参数名
        self.output_param_edit = QLineEdit("output_path")
        function_layout.addRow("输出路径参数:", self.output_param_edit)
        
        # 参数列表
        param_group = QGroupBox("参数列表")
        config_layout.addWidget(param_group)
        
        param_layout = QVBoxLayout(param_group)
        
        # 参数列表显示
        self.param_list = QListWidget()
        param_layout.addWidget(self.param_list)
        
        # 按钮行
        button_layout = QHBoxLayout()
        
        self.refresh_params_btn = QPushButton("刷新参数")
        self.refresh_params_btn.clicked.connect(self.refresh_parameters)
        button_layout.addWidget(self.refresh_params_btn)
        
        self.generate_btn = QPushButton("生成代码")
        self.generate_btn.clicked.connect(self.generate_code)
        button_layout.addWidget(self.generate_btn)
        
        self.copy_btn = QPushButton("复制代码")
        self.copy_btn.clicked.connect(self.copy_code)
        button_layout.addWidget(self.copy_btn)
        
        self.save_btn = QPushButton("保存代码")
        self.save_btn.clicked.connect(self.save_code)
        button_layout.addWidget(self.save_btn)
        
        config_layout.addLayout(button_layout)
        
        # 下部分：生成的代码
        code_widget = QWidget()
        splitter.addWidget(code_widget)
        
        code_layout = QVBoxLayout(code_widget)
        
        code_label = QLabel("生成的Pillow代码:")
        code_label.setStyleSheet("font-weight: bold;")
        code_layout.addWidget(code_label)
        
        # 代码显示区域
        self.code_text = QTextEdit()
        self.code_text.setFont(QFont("Consolas", 10))
        self.code_text.setReadOnly(True)
        code_layout.addWidget(self.code_text)
        
        # 设置分割器比例
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        # 初始刷新参数
        self.refresh_parameters()
        
    def refresh_parameters(self):
        """刷新参数列表"""
        self.param_list.clear()
        
        parameters = self.collect_parameters()
        
        if not parameters:
            item = QListWidgetItem("无参数")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.param_list.addItem(item)
        else:
            for param in parameters:
                item = QListWidgetItem(f"{param['name']} ({param['type']}) - {param['description']}")
                self.param_list.addItem(item)
                
    def collect_parameters(self) -> List[Dict[str, Any]]:
        """收集所有参数"""
        parameters = []
        
        # 添加输出路径参数
        output_param = self.output_param_edit.text() or "output_path"
        parameters.append({
            'name': output_param,
            'type': 'str',
            'description': '输出图片路径'
        })
        
        # 收集图片层参数
        for layer in self.project_model.get_layers_by_type(LayerType.IMAGE):
            image_layer = layer
            if image_layer.is_path_parameter:
                parameters.append({
                    'name': image_layer.parameter_name,
                    'type': 'str',
                    'description': f'图片路径 - {layer.name}'
                })
                
        # 收集文字层参数
        for layer in self.project_model.get_layers_by_type(LayerType.TEXT):
            text_layer = layer
            if text_layer.is_text_parameter:
                parameters.append({
                    'name': text_layer.text_parameter_name,
                    'type': 'str',
                    'description': f'文字内容 - {layer.name}'
                })
            if text_layer.is_font_parameter:
                parameters.append({
                    'name': text_layer.font_parameter_name,
                    'type': 'str',
                    'description': f'字体路径 - {layer.name}'
                })
                
        return parameters
        
    def generate_code(self):
        """生成Pillow代码"""
        if not self.project_model.base_image:
            QMessageBox.warning(self, "警告", "请先设置底图!")
            return
            
        code = self.build_code()
        self.code_text.setPlainText(code)
        
    def build_code(self) -> str:
        """构建代码字符串"""
        lines = []
        
        # 添加导入语句
        lines.append("from PIL import Image, ImageDraw, ImageFont")
        lines.append("import os")
        lines.append("")
        
        # 函数定义
        function_name = self.function_name_edit.text() or "generate_image"
        parameters = self.collect_parameters()
        
        param_strs = []
        for param in parameters:
            param_strs.append(f"{param['name']}: {param['type']}")
            
        function_signature = f"def {function_name}({', '.join(param_strs)}):"
        lines.append(function_signature)
        
        # 函数文档字符串
        lines.append('    """')
        lines.append(f'    生成图像 - {self.project_model.project_name}')
        lines.append('    ')
        lines.append('    参数:')
        for param in parameters:
            lines.append(f'        {param["name"]}: {param["description"]}')
        lines.append('    """')
        
        # 加载底图
        base_image = self.project_model.base_image
        if base_image and base_image.image_path:
            # 使用相对路径
            rel_path = os.path.relpath(base_image.image_path)
            lines.append(f'    # 加载底图')
            lines.append(f'    base_image = Image.open(r"{rel_path}")')
            lines.append('    result = base_image.copy()')
            lines.append('')
        else:
            lines.append('    # 创建空白图像')
            lines.append('    result = Image.new("RGBA", (800, 600), (255, 255, 255, 255))')
            lines.append('')
            
        # 处理图片层
        image_layers = self.project_model.get_layers_by_type(LayerType.IMAGE)
        if image_layers:
            lines.append('    # 添加图片层')
            
            for i, layer in enumerate(image_layers):
                image_layer = layer
                if not image_layer.visible:
                    lines.append(f'    # 图片层 "{layer.name}" 已隐藏')
                    continue
                    
                layer_var = f"image_{i}"
                
                # 加载图片
                if image_layer.is_path_parameter:
                    lines.append(f'    {layer_var} = Image.open({image_layer.parameter_name})')
                else:
                    if image_layer.image_path:
                        rel_path = os.path.relpath(image_layer.image_path)
                        lines.append(f'    {layer_var} = Image.open(r"{rel_path}")')
                    else:
                        lines.append(f'    # 警告: 图片层 "{layer.name}" 没有设置图片路径')
                        continue
                        
                # 调整大小
                if image_layer.size.width != 100 or image_layer.size.height != 100:
                    lines.append(f'    {layer_var} = {layer_var}.resize(({image_layer.size.width}, {image_layer.size.height}))')
                    
                # 处理透明度
                if image_layer.opacity < 1.0:
                    opacity_value = int(image_layer.opacity * 255)
                    lines.append(f'    # 设置透明度')
                    lines.append(f'    if {layer_var}.mode != "RGBA":')
                    lines.append(f'        {layer_var} = {layer_var}.convert("RGBA")')
                    lines.append(f'    alpha = {layer_var}.split()[-1]')
                    lines.append(f'    alpha = alpha.point(lambda p: int(p * {image_layer.opacity}))')
                    lines.append(f'    {layer_var}.putalpha(alpha)')
                    
                # 处理旋转
                if image_layer.rotation != 0:
                    lines.append(f'    {layer_var} = {layer_var}.rotate({image_layer.rotation}, expand=True)')
                    
                # 粘贴到结果图像
                lines.append(f'    result.paste({layer_var}, ({image_layer.position.x}, {image_layer.position.y}), {layer_var})')
                lines.append('')
                
        # 处理文字层
        text_layers = self.project_model.get_layers_by_type(LayerType.TEXT)
        if text_layers:
            lines.append('    # 添加文字层')
            lines.append('    draw = ImageDraw.Draw(result)')
            lines.append('')
            
            for i, layer in enumerate(text_layers):
                text_layer = layer
                if not text_layer.visible:
                    lines.append(f'    # 文字层 "{layer.name}" 已隐藏')
                    continue
                    
                # 获取文字内容
                if text_layer.is_text_parameter:
                    text_var = text_layer.text_parameter_name
                else:
                    text_var = f'"{text_layer.text}"'
                    
                # 设置字体
                font_var = f"font_{i}"
                if text_layer.font_path:
                    if text_layer.is_font_parameter:
                        lines.append(f'    try:')
                        lines.append(f'        {font_var} = ImageFont.truetype({text_layer.font_parameter_name}, {text_layer.font_size})')
                        lines.append(f'    except:')
                        lines.append(f'        {font_var} = ImageFont.load_default()')
                    else:
                        rel_path = os.path.relpath(text_layer.font_path)
                        lines.append(f'    try:')
                        lines.append(f'        {font_var} = ImageFont.truetype(r"{rel_path}", {text_layer.font_size})')
                        lines.append(f'    except:')
                        lines.append(f'        {font_var} = ImageFont.load_default()')
                else:
                    lines.append(f'    {font_var} = ImageFont.load_default()')
                    
                # 绘制文字
                color_tuple = f"({text_layer.color[0]}, {text_layer.color[1]}, {text_layer.color[2]}, {text_layer.color[3]})"
                
                # 计算文字位置（考虑对齐方式）
                pos_x = text_layer.position.x
                pos_y = text_layer.position.y
                
                if (text_layer.horizontal_align != TextAlignment.LEFT or 
                    text_layer.vertical_align != TextAlignment.TOP):
                    
                    lines.append(f'    # 计算文字对齐位置')
                    lines.append(f'    text_bbox = draw.textbbox((0, 0), {text_var}, font={font_var})')
                    lines.append(f'    text_width = text_bbox[2] - text_bbox[0]')
                    lines.append(f'    text_height = text_bbox[3] - text_bbox[1]')
                    
                    # 水平对齐
                    if text_layer.horizontal_align == TextAlignment.CENTER:
                        lines.append(f'    text_x = {pos_x} - text_width // 2')
                    elif text_layer.horizontal_align == TextAlignment.RIGHT:
                        lines.append(f'    text_x = {pos_x} - text_width')
                    else:
                        lines.append(f'    text_x = {pos_x}')
                        
                    # 垂直对齐
                    if text_layer.vertical_align == TextAlignment.MIDDLE:
                        lines.append(f'    text_y = {pos_y} - text_height // 2')
                    elif text_layer.vertical_align == TextAlignment.BOTTOM:
                        lines.append(f'    text_y = {pos_y} - text_height')
                    else:
                        lines.append(f'    text_y = {pos_y}')
                        
                    lines.append(f'    draw.text((text_x, text_y), {text_var}, font={font_var}, fill={color_tuple})')
                else:
                    lines.append(f'    draw.text(({pos_x}, {pos_y}), {text_var}, font={font_var}, fill={color_tuple})')
                    
                lines.append('')
                
        # 保存结果
        output_param = self.output_param_edit.text() or "output_path"
        lines.append('    # 保存结果')
        lines.append(f'    result.save({output_param})')
        lines.append(f'    print(f"图像已保存到: {{{output_param}}}")')
        lines.append('')
        
        # 添加示例调用
        lines.append('')
        lines.append('# 示例调用:')
        lines.append('if __name__ == "__main__":')
        
        example_params = []
        for param in parameters:
            if param['name'] == output_param:
                example_params.append(f'"{param["name"]}": "output.png"')
            elif param['type'] == 'str' and 'path' in param['name'].lower():
                example_params.append(f'"{param["name"]}": "path/to/file"')
            else:
                example_params.append(f'"{param["name"]}": "example_value"')
                
        # 生成示例参数字典
        if len(example_params) > 1:  # 有除了输出路径之外的参数
            lines.append('    params = {')
            for param_str in example_params:
                key, value = param_str.split(': ')
                lines.append(f'        {key}: {value},')
            lines.append('    }')
            lines.append(f'    {function_name}(**params)')
        else:
            # 只有输出路径参数
            lines.append(f'    {function_name}("output.png")')
            
        return '\n'.join(lines)
        
    def copy_code(self):
        """复制代码到剪贴板"""
        from PySide6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(self.code_text.toPlainText())
        
        # 显示提示
        parent = self.parent()
        while parent:
            if hasattr(parent, 'status_bar'):
                parent.status_bar.showMessage("代码已复制到剪贴板", 3000)
                break
            parent = parent.parent()
            
    def save_code(self):
        """保存代码到文件"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存代码",
            f"{self.function_name_edit.text()}.py",
            "Python文件 (*.py);;所有文件 (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.code_text.toPlainText())
                    
                QMessageBox.information(self, "成功", f"代码已保存到:\n{file_path}")
                
                # 更新状态栏
                parent = self.parent()
                while parent:
                    if hasattr(parent, 'status_bar'):
                        parent.status_bar.showMessage(f"代码已保存到: {os.path.basename(file_path)}", 3000)
                        break
                    parent = parent.parent()
                    
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败:\n{str(e)}")
