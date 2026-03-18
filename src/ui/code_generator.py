"""
代码生成器实现
"""

import os
from typing import Any

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTextEdit,
    QPushButton,
    QHBoxLayout,
    QLabel,
    QGroupBox,
    QLineEdit,
    QFormLayout,
    QFileDialog,
    QMessageBox,
    QSplitter,
    QListWidget,
    QListWidgetItem,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from ..core.models import (
    ProjectModel,
    ImageLayer,
    TextLayer,
    LayerType,
    TextAlignment,
    TextOverflowMode,
)


class CodeGenerator(QWidget):
    """代码生成器"""

    def __init__(self, project_model: ProjectModel, parent=None):
        super().__init__(parent)

        self.project_model = project_model

        self.init_ui()
        self.connect_signals()

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
        self.function_name_edit = QLineEdit()
        function_layout.addRow("函数名:", self.function_name_edit)

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

    def connect_signals(self):
        """连接信号槽"""
        # 连接函数名输入框的变化到项目模型
        self.function_name_edit.textChanged.connect(self.on_function_name_changed)

        # 初始化函数名输入框的值
        self.function_name_edit.setText(self.project_model.function_name)

    def on_function_name_changed(self, text: str):
        """函数名变化处理"""
        self.project_model.function_name = text

    def update_from_project(self):
        """从项目模型更新UI"""
        # 更新函数名输入框
        self.function_name_edit.blockSignals(True)
        self.function_name_edit.setText(self.project_model.function_name)
        self.function_name_edit.blockSignals(False)

        # 刷新参数列表
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
                item = QListWidgetItem(
                    f"{param['name']} ({param['type']}) - {param['description']}"
                )
                self.param_list.addItem(item)

    def collect_parameters(self) -> list[dict[str, Any]]:
        """收集所有参数"""
        parameters: list[dict[str, Any]] = []

        # 收集底图参数
        base_image = self.project_model.base_image
        if base_image and base_image.is_path_parameter:
            parameters.append(
                {
                    "name": base_image.parameter_name,
                    "type": "str",
                    "description": f"底图路径 - {base_image.name}",
                }
            )

        # 收集图片层参数
        for layer in self.project_model.get_layers_by_type(LayerType.IMAGE):
            if isinstance(layer, ImageLayer) and layer.is_path_parameter:
                parameters.append(
                    {
                        "name": layer.parameter_name,
                        "type": "str",
                        "description": f"图片路径 - {layer.name}",
                    }
                )

        # 收集文字层参数
        for layer in self.project_model.get_layers_by_type(LayerType.TEXT):
            if isinstance(layer, TextLayer):
                if layer.is_text_parameter:
                    parameters.append(
                        {
                            "name": layer.text_parameter_name,
                            "type": "str",
                            "description": f"文字内容 - {layer.name}",
                        }
                    )
                if layer.is_font_parameter:
                    parameters.append(
                        {
                            "name": layer.font_parameter_name,
                            "type": "str",
                            "description": f"字体路径 - {layer.name}",
                        }
                    )

        return parameters

    def generate_code(self):
        """生成Pillow代码"""
        code = self.build_code()
        self.code_text.setPlainText(code)

        parent = self.parent()
        while parent:
            status_bar = getattr(parent, "status_bar", None)
            if status_bar and hasattr(status_bar, "showMessage"):
                if self.project_model.base_image:
                    status_bar.showMessage("代码生成完成", 3000)
                else:
                    status_bar.showMessage(
                        "代码生成完成：当前未设置底图，已生成空白画布版本",
                        4000,
                    )
                break
            parent = parent.parent()

    def _get_project_file_path(self) -> str | None:
        parent = self.parent()
        while parent:
            project_manager = getattr(parent, "project_manager", None)
            if project_manager and hasattr(project_manager, "current_file"):
                return project_manager.current_file
            parent = parent.parent()
        return None

    def _get_asset_base_dir(self, output_file_path: str | None) -> str | None:
        if output_file_path:
            return os.path.dirname(os.path.abspath(output_file_path))

        project_file_path = self._get_project_file_path()
        if project_file_path:
            return os.path.dirname(os.path.abspath(project_file_path))

        return None

    def _build_asset_reference(
        self, asset_path: str, output_file_path: str | None
    ) -> str:
        asset_abs_path = os.path.abspath(asset_path)
        base_dir = self._get_asset_base_dir(output_file_path)
        if base_dir:
            try:
                relative_path = os.path.relpath(asset_abs_path, base_dir)
                return relative_path.replace("\\", "/")
            except ValueError:
                pass
        return asset_abs_path.replace("\\", "/")

    def build_code(self, output_file_path: str | None = None) -> str:
        """构建代码字符串"""
        lines: list[str] = []

        # 添加导入语句
        lines.append("from PIL import Image, ImageDraw, ImageFont")
        lines.append("from pathlib import Path")
        lines.append("")
        lines.append("SCRIPT_DIR = Path(__file__).resolve().parent")
        lines.append("")
        lines.append("def resolve_asset_path(asset_path: str) -> str:")
        lines.append("    path = Path(asset_path)")
        lines.append("    if path.is_absolute():")
        lines.append("        return str(path)")
        lines.append("    return str((SCRIPT_DIR / path).resolve())")
        lines.append("")

        # 函数定义
        function_name = self.project_model.function_name or "generate_image"
        parameters = self.collect_parameters()

        param_strs = []
        for param in parameters:
            param_strs.append(f"{param['name']}: {param['type']}")

        function_signature = f"def {function_name}({', '.join(param_strs)}):"
        lines.append(function_signature)

        # 函数文档字符串
        lines.append('    """')
        lines.append(f"    生成图像 - {self.project_model.project_name}")
        lines.append("    ")
        if parameters:
            lines.append("    参数:")
            for param in parameters:
                lines.append(f"        {param['name']}: {param['description']}")
            lines.append("    ")
        lines.append("    返回:")
        lines.append("        PIL.Image.Image: 生成的图像对象")
        lines.append('    """')

        # 加载底图
        base_image = self.project_model.base_image
        if base_image and base_image.image_path:
            lines.append("    # 加载底图")
            if base_image.is_path_parameter:
                # 作为参数传入
                lines.append(
                    f"    base_image = Image.open({base_image.parameter_name})"
                )
            else:
                asset_reference = self._build_asset_reference(
                    base_image.image_path,
                    output_file_path,
                )
                lines.append(
                    f'    base_image = Image.open(resolve_asset_path(r"{asset_reference}"))'
                )
            lines.append("    result = base_image.copy()")
            lines.append("")
        else:
            lines.append("    # 创建空白图像")
            lines.append(
                '    result = Image.new("RGBA", (800, 600), (255, 255, 255, 255))'
            )
            lines.append("")

        # 处理图片层
        image_layers = self.project_model.get_layers_by_type(LayerType.IMAGE)
        if image_layers:
            lines.append("    # 添加图片层")

            for i, layer in enumerate(image_layers):
                if not isinstance(layer, ImageLayer):
                    continue
                image_layer = layer
                if not image_layer.visible:
                    lines.append(f'    # 图片层 "{layer.name}" 已隐藏')
                    continue

                layer_var = f"image_{i}"

                # 加载图片
                if image_layer.is_path_parameter:
                    lines.append(
                        f"    {layer_var} = Image.open({image_layer.parameter_name})"
                    )
                else:
                    if image_layer.image_path:
                        asset_reference = self._build_asset_reference(
                            image_layer.image_path,
                            output_file_path,
                        )
                        lines.append(
                            f'    {layer_var} = Image.open(resolve_asset_path(r"{asset_reference}"))'
                        )
                    else:
                        lines.append(
                            f'    # 警告: 图片层 "{layer.name}" 没有设置图片路径'
                        )
                        continue

                # 调整大小
                if image_layer.size.width != 100 or image_layer.size.height != 100:
                    lines.append(
                        f"    {layer_var} = {layer_var}.resize(({image_layer.size.width}, {image_layer.size.height}))"
                    )

                # 处理透明度
                if image_layer.opacity < 1.0:
                    opacity_value = int(image_layer.opacity * 255)
                    lines.append(f"    # 设置透明度")
                    lines.append(f'    if {layer_var}.mode != "RGBA":')
                    lines.append(f'        {layer_var} = {layer_var}.convert("RGBA")')
                    lines.append(f"    alpha = {layer_var}.split()[-1]")
                    lines.append(
                        f"    alpha = alpha.point(lambda p: int(p * {image_layer.opacity}))"
                    )
                    lines.append(f"    {layer_var}.putalpha(alpha)")

                # 处理旋转
                if image_layer.rotation != 0:
                    lines.append(
                        f"    {layer_var} = {layer_var}.rotate({image_layer.rotation}, expand=True)"
                    )

                # 粘贴到结果图像
                lines.append(
                    f"    result.paste({layer_var}, ({image_layer.position.x}, {image_layer.position.y}), {layer_var})"
                )
                lines.append("")

        # 处理文字层
        text_layers = self.project_model.get_layers_by_type(LayerType.TEXT)
        if text_layers:
            lines.append("    # 添加文字层")
            lines.append("    draw = ImageDraw.Draw(result)")
            lines.append("")
            lines.append("    # 文字处理工具函数")
            lines.append("    def get_text_size(text, font):")
            lines.append("        bbox = font.getbbox(text)")
            lines.append("        return bbox[2] - bbox[0], bbox[3] - bbox[1]")
            lines.append("")

            lines.append('    def truncate_text(text, font, max_width, suffix="..."):')
            lines.append("        if not text or not max_width:")
            lines.append("            return text")
            lines.append("        text_width, _ = get_text_size(text, font)")
            lines.append("        if text_width <= max_width:")
            lines.append("            return text")
            lines.append("        suffix_width, _ = get_text_size(suffix, font)")
            lines.append("        available_width = max_width - suffix_width")
            lines.append("        if available_width <= 0:")
            lines.append('            return suffix[:1] if suffix else ""')
            lines.append("        left, right = 0, len(text)")
            lines.append('        result = ""')
            lines.append("        while left <= right:")
            lines.append("            mid = (left + right) // 2")
            lines.append("            test_text = text[:mid]")
            lines.append("            test_width, _ = get_text_size(test_text, font)")
            lines.append("            if test_width <= available_width:")
            lines.append("                result = test_text")
            lines.append("                left = mid + 1")
            lines.append("            else:")
            lines.append("                right = mid - 1")
            lines.append("        return result + suffix")
            lines.append("")

            for i, layer in enumerate(text_layers):
                if not isinstance(layer, TextLayer):
                    continue
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
                        lines.append(f"    try:")
                        lines.append(
                            f"        {font_var} = ImageFont.truetype({text_layer.font_parameter_name}, {text_layer.font_size})"
                        )
                        lines.append(f"    except:")
                        lines.append(f"        {font_var} = ImageFont.load_default()")
                    else:
                        asset_reference = self._build_asset_reference(
                            text_layer.font_path,
                            output_file_path,
                        )
                        lines.append(f"    try:")
                        lines.append(
                            f'        {font_var} = ImageFont.truetype(resolve_asset_path(r"{asset_reference}"), {text_layer.font_size})'
                        )
                        lines.append(f"    except:")
                        lines.append(f"        {font_var} = ImageFont.load_default()")
                else:
                    lines.append(f"    {font_var} = ImageFont.load_default()")

                # 处理文字内容（宽度限制）
                color_tuple = f"({text_layer.color[0]}, {text_layer.color[1]}, {text_layer.color[2]}, {text_layer.color[3]})"

                # 处理文字宽度限制
                if (
                    text_layer.max_width is not None
                    and text_layer.overflow_mode == TextOverflowMode.TRUNCATE
                ):
                    lines.append(f"    # 处理文字宽度限制")
                    lines.append(
                        f'    processed_text = truncate_text({text_var}, {font_var}, {text_layer.max_width}, "{text_layer.truncate_suffix}")'
                    )
                    lines.append(f"    text_lines = [processed_text]")
                else:
                    lines.append(f"    text_lines = [{text_var}]")

                lines.append("")

                # 计算文字位置（考虑对齐方式）
                # 注意：text_layer.position 存储的是对齐锚点位置
                anchor_x = text_layer.position.x
                anchor_y = text_layer.position.y

                # 绘制多行文字
                lines.append(f"    # 绘制多行文字")
                lines.append(f"    if text_lines:")

                # 计算总文字尺寸
                lines.append(f"        # 计算文字总尺寸")
                lines.append(f"        max_line_width = 0")
                lines.append(
                    f'        line_height = get_text_size("Ag", {font_var})[1]'
                )
                lines.append(f"        for line in text_lines:")
                lines.append(
                    f"            line_width = get_text_size(line, {font_var})[0]"
                )
                lines.append(
                    f"            max_line_width = max(max_line_width, line_width)"
                )

                lines.append(f"        total_height = line_height")

                # 计算起始位置（考虑对齐）
                lines.append(f"        # 计算起始位置（考虑对齐）")

                # 水平对齐
                if text_layer.horizontal_align == TextAlignment.CENTER:
                    lines.append(f"        start_x = {anchor_x} - max_line_width // 2")
                elif text_layer.horizontal_align == TextAlignment.RIGHT:
                    lines.append(f"        start_x = {anchor_x} - max_line_width")
                else:
                    lines.append(f"        start_x = {anchor_x}")

                # 垂直对齐
                if text_layer.vertical_align == TextAlignment.MIDDLE:
                    lines.append(f"        start_y = {anchor_y} - total_height // 2")
                elif text_layer.vertical_align == TextAlignment.BOTTOM:
                    lines.append(f"        start_y = {anchor_y} - total_height")
                else:
                    lines.append(f"        start_y = {anchor_y}")

                # 绘制每一行
                lines.append(f"        # 绘制每一行文字")
                lines.append(f"        current_y = start_y")
                lines.append(f"        for line in text_lines:")

                # 每行的水平对齐
                if text_layer.horizontal_align == TextAlignment.CENTER:
                    lines.append(
                        f"            line_width = get_text_size(line, {font_var})[0]"
                    )
                    lines.append(f"            line_x = {anchor_x} - line_width // 2")
                elif text_layer.horizontal_align == TextAlignment.RIGHT:
                    lines.append(
                        f"            line_width = get_text_size(line, {font_var})[0]"
                    )
                    lines.append(f"            line_x = {anchor_x} - line_width")
                else:
                    lines.append(f"            line_x = start_x")

                lines.append(
                    f"            draw.text((line_x, current_y), line, font={font_var}, fill={color_tuple})"
                )
                lines.append(f"            current_y += line_height")

                lines.append("")

        # 返回结果
        lines.append("    # 返回生成的图像")
        lines.append("    return result")
        lines.append("")

        # 添加示例调用
        lines.append("")
        lines.append("# 示例调用:")
        lines.append('if __name__ == "__main__":')

        example_params = []
        for param in parameters:
            if param["type"] == "str" and "path" in param["name"].lower():
                example_params.append(f'"{param["name"]}": "path/to/file"')
            else:
                example_params.append(f'"{param["name"]}": "example_value"')

        # 生成示例调用
        if example_params:
            lines.append("    # 生成图像")
            lines.append("    params = {")
            for param_str in example_params:
                key, value = param_str.split(": ")
                lines.append(f"        {key}: {value},")
            lines.append("    }")
            lines.append(f"    image = {function_name}(**params)")
        else:
            lines.append("    # 生成图像")
            lines.append(f"    image = {function_name}()")

        lines.append("    ")
        lines.append("    # 保存图像（可选）")
        lines.append('    image.save("output.png")')
        lines.append('    print("图像已生成并保存到 output.png")')

        return "\n".join(lines)

    def copy_code(self):
        """复制代码到剪贴板"""
        from PySide6.QtWidgets import QApplication

        clipboard = QApplication.clipboard()
        clipboard.setText(self.code_text.toPlainText())

        # 显示提示
        parent = self.parent()
        while parent:
            if hasattr(parent, "status_bar"):
                status_bar = getattr(parent, "status_bar", None)
                if status_bar and hasattr(status_bar, "showMessage"):
                    status_bar.showMessage("代码已复制到剪贴板", 3000)
                break
            parent = parent.parent()

    def save_code(self):
        """保存代码到文件"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存代码",
            f"{self.function_name_edit.text()}.py",
            "Python文件 (*.py);;所有文件 (*)",
        )

        if file_path:
            try:
                code = self.build_code(output_file_path=file_path)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(code)

                self.code_text.setPlainText(code)

                QMessageBox.information(self, "成功", f"代码已保存到:\n{file_path}")

                # 更新状态栏
                parent = self.parent()
                while parent:
                    if hasattr(parent, "status_bar"):
                        status_bar = getattr(parent, "status_bar", None)
                        if status_bar and hasattr(status_bar, "showMessage"):
                            status_bar.showMessage(
                                f"代码已保存到: {os.path.basename(file_path)}", 3000
                            )
                        break
                    parent = parent.parent()

            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败:\n{str(e)}")
