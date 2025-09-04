"""
属性面板实现
"""
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLabel, QLineEdit,
    QSpinBox, QDoubleSpinBox, QCheckBox, QComboBox, QPushButton,
    QColorDialog, QFileDialog, QGroupBox, QSlider, QHBoxLayout
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from ..core.models import (
    ProjectModel, BaseLayer, ImageLayer, TextLayer, BaseImageLayer,
    LayerType, TextAlignment
)


class PropertyPanel(QWidget):
    """属性面板"""
    
    def __init__(self, project_model: ProjectModel, parent=None):
        super().__init__(parent)
        
        self.project_model = project_model
        self.current_layer: Optional[BaseLayer] = None
        
        self.init_ui()
        self.connect_signals()
        
    def connect_signals(self):
        """连接信号槽"""
        # 监听图层更新信号，用于实时更新属性显示
        self.project_model.layer_updated.connect(self.on_layer_updated)
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel("属性")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title_label)
        
        # 基本属性组
        self.basic_group = QGroupBox("基本属性")
        layout.addWidget(self.basic_group)
        
        basic_layout = QFormLayout(self.basic_group)
        
        # 图层名称
        self.name_edit = QLineEdit()
        self.name_edit.textChanged.connect(self.on_name_changed)
        basic_layout.addRow("名称:", self.name_edit)
        
        # 可见性
        self.visible_checkbox = QCheckBox()
        self.visible_checkbox.toggled.connect(self.on_visibility_changed)
        basic_layout.addRow("可见:", self.visible_checkbox)
        
        # 位置属性组
        self.position_group = QGroupBox("位置")
        layout.addWidget(self.position_group)
        
        position_layout = QFormLayout(self.position_group)
        
        # X坐标
        self.x_spinbox = QSpinBox()
        self.x_spinbox.setRange(-9999, 9999)
        self.x_spinbox.valueChanged.connect(self.on_position_changed)
        position_layout.addRow("X:", self.x_spinbox)
        
        # Y坐标
        self.y_spinbox = QSpinBox()
        self.y_spinbox.setRange(-9999, 9999)
        self.y_spinbox.valueChanged.connect(self.on_position_changed)
        position_layout.addRow("Y:", self.y_spinbox)
        
        # 图片属性组（仅图片层显示）
        self.image_group = QGroupBox("图片属性")
        layout.addWidget(self.image_group)
        
        image_layout = QFormLayout(self.image_group)
        
        # 图片路径
        image_path_layout = QHBoxLayout()
        self.image_path_edit = QLineEdit()
        self.image_path_edit.textChanged.connect(self.on_image_path_changed)
        image_path_layout.addWidget(self.image_path_edit)
        
        self.browse_image_btn = QPushButton("浏览")
        self.browse_image_btn.clicked.connect(self.browse_image)
        image_path_layout.addWidget(self.browse_image_btn)
        
        image_layout.addRow("图片路径:", image_path_layout)
        
        # 作为参数
        self.image_parameter_checkbox = QCheckBox()
        self.image_parameter_checkbox.toggled.connect(self.on_image_parameter_changed)
        image_layout.addRow("作为参数:", self.image_parameter_checkbox)
        
        # 参数名称
        self.image_param_name_edit = QLineEdit()
        self.image_param_name_edit.textChanged.connect(self.on_image_param_name_changed)
        image_layout.addRow("参数名:", self.image_param_name_edit)
        
        # 图片尺寸
        size_layout = QHBoxLayout()
        
        self.width_spinbox = QSpinBox()
        self.width_spinbox.setRange(1, 9999)
        self.width_spinbox.setValue(100)
        self.width_spinbox.valueChanged.connect(self.on_size_changed)
        size_layout.addWidget(QLabel("宽:"))
        size_layout.addWidget(self.width_spinbox)
        
        self.height_spinbox = QSpinBox()
        self.height_spinbox.setRange(1, 9999)
        self.height_spinbox.setValue(100)
        self.height_spinbox.valueChanged.connect(self.on_size_changed)
        size_layout.addWidget(QLabel("高:"))
        size_layout.addWidget(self.height_spinbox)
        
        image_layout.addRow("尺寸:", size_layout)
        
        # 透明度
        opacity_layout = QHBoxLayout()
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(100)
        self.opacity_slider.valueChanged.connect(self.on_opacity_changed)
        opacity_layout.addWidget(self.opacity_slider)
        
        self.opacity_label = QLabel("100%")
        opacity_layout.addWidget(self.opacity_label)
        
        image_layout.addRow("透明度:", opacity_layout)
        
        # 旋转
        self.rotation_spinbox = QDoubleSpinBox()
        self.rotation_spinbox.setRange(-360, 360)
        self.rotation_spinbox.setSuffix("°")
        self.rotation_spinbox.valueChanged.connect(self.on_rotation_changed)
        image_layout.addRow("旋转:", self.rotation_spinbox)
        
        # 底图属性组（仅底图显示）
        self.base_image_group = QGroupBox("底图属性")
        layout.addWidget(self.base_image_group)
        
        base_image_layout = QFormLayout(self.base_image_group)
        
        # 底图路径
        base_path_layout = QHBoxLayout()
        self.base_image_path_edit = QLineEdit()
        self.base_image_path_edit.setReadOnly(True)
        base_path_layout.addWidget(self.base_image_path_edit)
        
        self.browse_base_image_btn = QPushButton("浏览")
        self.browse_base_image_btn.clicked.connect(self.browse_base_image)
        base_path_layout.addWidget(self.browse_base_image_btn)
        
        base_image_layout.addRow("底图路径:", base_path_layout)
        
        # 作为参数
        self.base_image_parameter_checkbox = QCheckBox()
        self.base_image_parameter_checkbox.toggled.connect(self.on_base_image_parameter_changed)
        base_image_layout.addRow("作为参数:", self.base_image_parameter_checkbox)
        
        # 参数名称
        self.base_image_param_name_edit = QLineEdit()
        self.base_image_param_name_edit.textChanged.connect(self.on_base_image_param_name_changed)
        base_image_layout.addRow("参数名:", self.base_image_param_name_edit)
        
        # 文字属性组（仅文字层显示）
        self.text_group = QGroupBox("文字属性")
        layout.addWidget(self.text_group)
        
        text_layout = QFormLayout(self.text_group)
        
        # 文字内容
        self.text_edit = QLineEdit()
        self.text_edit.textChanged.connect(self.on_text_changed)
        text_layout.addRow("文字:", self.text_edit)
        
        # 文字作为参数
        self.text_parameter_checkbox = QCheckBox()
        self.text_parameter_checkbox.toggled.connect(self.on_text_parameter_changed)
        text_layout.addRow("文字作为参数:", self.text_parameter_checkbox)
        
        # 文字参数名
        self.text_param_name_edit = QLineEdit()
        self.text_param_name_edit.textChanged.connect(self.on_text_param_name_changed)
        text_layout.addRow("文字参数名:", self.text_param_name_edit)
        
        # 字体路径
        font_path_layout = QHBoxLayout()
        self.font_path_edit = QLineEdit()
        self.font_path_edit.textChanged.connect(self.on_font_path_changed)
        font_path_layout.addWidget(self.font_path_edit)
        
        self.browse_font_btn = QPushButton("浏览")
        self.browse_font_btn.clicked.connect(self.browse_font)
        font_path_layout.addWidget(self.browse_font_btn)
        
        text_layout.addRow("字体文件:", font_path_layout)
        
        # 字体作为参数
        self.font_parameter_checkbox = QCheckBox()
        self.font_parameter_checkbox.toggled.connect(self.on_font_parameter_changed)
        text_layout.addRow("字体作为参数:", self.font_parameter_checkbox)
        
        # 字体参数名
        self.font_param_name_edit = QLineEdit()
        self.font_param_name_edit.textChanged.connect(self.on_font_param_name_changed)
        text_layout.addRow("字体参数名:", self.font_param_name_edit)
        
        # 字体大小
        self.font_size_spinbox = QSpinBox()
        self.font_size_spinbox.setRange(8, 200)
        self.font_size_spinbox.setValue(24)
        self.font_size_spinbox.valueChanged.connect(self.on_font_size_changed)
        text_layout.addRow("字体大小:", self.font_size_spinbox)
        
        # 文字颜色
        color_layout = QHBoxLayout()
        self.color_btn = QPushButton()
        self.color_btn.setFixedSize(50, 25)
        self.color_btn.clicked.connect(self.choose_color)
        color_layout.addWidget(self.color_btn)
        
        self.color_label = QLabel("黑色")
        color_layout.addWidget(self.color_label)
        
        # 在控件创建后设置初始颜色
        self.update_color_button(QColor(0, 0, 0))
        
        text_layout.addRow("颜色:", color_layout)
        
        # 水平对齐
        self.h_align_combo = QComboBox()
        self.h_align_combo.addItems(["左对齐", "居中", "右对齐"])
        self.h_align_combo.currentTextChanged.connect(self.on_h_align_changed)
        text_layout.addRow("水平对齐:", self.h_align_combo)
        
        # 垂直对齐
        self.v_align_combo = QComboBox()
        self.v_align_combo.addItems(["顶部", "居中", "底部"])
        self.v_align_combo.currentTextChanged.connect(self.on_v_align_changed)
        text_layout.addRow("垂直对齐:", self.v_align_combo)
        
        layout.addStretch()
        
        # 初始状态：隐藏所有属性组
        self.hide_all_groups()
        
    def hide_all_groups(self):
        """隐藏所有属性组"""
        self.basic_group.hide()
        self.position_group.hide()
        self.image_group.hide()
        self.base_image_group.hide()
        self.text_group.hide()
        
    def set_current_layer(self, layer_id: str):
        """设置当前图层"""
        layer = self.project_model.get_layer(layer_id)
        if not layer:
            # 检查是否是底图
            if self.project_model.base_image and self.project_model.base_image.id == layer_id:
                layer = self.project_model.base_image
                
        if layer:
            self.current_layer = layer
            self.update_ui()
        else:
            self.current_layer = None
            self.hide_all_groups()
            
    def update_ui(self):
        """更新UI显示"""
        if not self.current_layer:
            return
            
        # 显示基本属性
        self.basic_group.show()
        self.name_edit.setText(self.current_layer.name)
        self.visible_checkbox.setChecked(self.current_layer.visible)
        
        # 显示位置属性（底图除外）
        if self.current_layer.layer_type != LayerType.BASE:
            self.position_group.show()
            self.x_spinbox.setValue(self.current_layer.position.x)
            self.y_spinbox.setValue(self.current_layer.position.y)
        else:
            self.position_group.hide()
            
        # 根据图层类型显示相应属性
        if isinstance(self.current_layer, ImageLayer):
            self.show_image_properties()
            self.text_group.hide()
            self.base_image_group.hide()
        elif isinstance(self.current_layer, TextLayer):
            self.show_text_properties()
            self.image_group.hide()
            self.base_image_group.hide()
        elif isinstance(self.current_layer, BaseImageLayer):
            self.show_base_image_properties()
            self.image_group.hide()
            self.text_group.hide()
        else:
            self.image_group.hide()
            self.text_group.hide()
            self.base_image_group.hide()
            
    def show_image_properties(self):
        """显示图片属性"""
        self.image_group.show()
        if not isinstance(self.current_layer, ImageLayer):
            return
            
        layer = self.current_layer
        
        self.image_path_edit.setText(layer.image_path)
        self.image_parameter_checkbox.setChecked(layer.is_path_parameter)
        self.image_param_name_edit.setText(layer.parameter_name)
        self.width_spinbox.setValue(layer.size.width)
        self.height_spinbox.setValue(layer.size.height)
        self.opacity_slider.setValue(int(layer.opacity * 100))
        self.opacity_label.setText(f"{int(layer.opacity * 100)}%")
        self.rotation_spinbox.setValue(layer.rotation)
        
    def show_text_properties(self):
        """显示文字属性"""
        self.text_group.show()
        if not isinstance(self.current_layer, TextLayer):
            return
            
        layer = self.current_layer
        
        self.text_edit.setText(layer.text)
        self.text_parameter_checkbox.setChecked(layer.is_text_parameter)
        self.text_param_name_edit.setText(layer.text_parameter_name)
        self.font_path_edit.setText(layer.font_path)
        self.font_parameter_checkbox.setChecked(layer.is_font_parameter)
        self.font_param_name_edit.setText(layer.font_parameter_name)
        self.font_size_spinbox.setValue(layer.font_size)
        
        # 设置颜色
        color = QColor(*layer.color)
        self.update_color_button(color)
        
        # 设置对齐
        h_align_map = {
            TextAlignment.LEFT: 0,
            TextAlignment.CENTER: 1,
            TextAlignment.RIGHT: 2
        }
        self.h_align_combo.setCurrentIndex(h_align_map.get(layer.horizontal_align, 0))
        
        v_align_map = {
            TextAlignment.TOP: 0,
            TextAlignment.MIDDLE: 1,
            TextAlignment.BOTTOM: 2
        }
        self.v_align_combo.setCurrentIndex(v_align_map.get(layer.vertical_align, 0))
        
    def show_base_image_properties(self):
        """显示底图属性"""
        self.base_image_group.show()
        if not isinstance(self.current_layer, BaseImageLayer):
            return
            
        layer = self.current_layer
        
        self.base_image_path_edit.setText(layer.image_path)
        self.base_image_parameter_checkbox.setChecked(layer.is_path_parameter)
        self.base_image_param_name_edit.setText(layer.parameter_name)
        
    # 信号处理函数
    def on_name_changed(self, text: str):
        """名称变化"""
        if self.current_layer:
            self.current_layer.name = text
            self.update_layer()
            
    def on_visibility_changed(self, visible: bool):
        """可见性变化"""
        if self.current_layer:
            self.current_layer.visible = visible
            self.update_layer()
            
    def on_position_changed(self):
        """位置变化"""
        if self.current_layer:
            self.current_layer.position.x = self.x_spinbox.value()
            self.current_layer.position.y = self.y_spinbox.value()
            self.update_layer()
            
    def on_image_path_changed(self, path: str):
        """图片路径变化"""
        if isinstance(self.current_layer, ImageLayer):
            self.current_layer.image_path = path
            self.update_layer()
            
    def on_image_parameter_changed(self, is_parameter: bool):
        """图片参数变化"""
        if isinstance(self.current_layer, ImageLayer):
            self.current_layer.is_path_parameter = is_parameter
            self.update_layer()
            
    def on_image_param_name_changed(self, name: str):
        """图片参数名变化"""
        if isinstance(self.current_layer, ImageLayer):
            self.current_layer.parameter_name = name
            self.update_layer()
            
    def on_size_changed(self):
        """尺寸变化"""
        if isinstance(self.current_layer, ImageLayer):
            self.current_layer.size.width = self.width_spinbox.value()
            self.current_layer.size.height = self.height_spinbox.value()
            self.update_layer()
            
    def on_opacity_changed(self, value: int):
        """透明度变化"""
        if isinstance(self.current_layer, ImageLayer):
            self.current_layer.opacity = value / 100.0
            self.opacity_label.setText(f"{value}%")
            self.update_layer()
            
    def on_rotation_changed(self, value: float):
        """旋转变化"""
        if isinstance(self.current_layer, ImageLayer):
            self.current_layer.rotation = value
            self.update_layer()
            
    def on_text_changed(self, text: str):
        """文字变化"""
        if isinstance(self.current_layer, TextLayer):
            self.current_layer.text = text
            self.update_layer()
            
    def on_text_parameter_changed(self, is_parameter: bool):
        """文字参数变化"""
        if isinstance(self.current_layer, TextLayer):
            self.current_layer.is_text_parameter = is_parameter
            self.update_layer()
            
    def on_text_param_name_changed(self, name: str):
        """文字参数名变化"""
        if isinstance(self.current_layer, TextLayer):
            self.current_layer.text_parameter_name = name
            self.update_layer()
            
    def on_font_path_changed(self, path: str):
        """字体路径变化"""
        if isinstance(self.current_layer, TextLayer):
            self.current_layer.font_path = path
            self.update_layer()
            
    def on_font_parameter_changed(self, is_parameter: bool):
        """字体参数变化"""
        if isinstance(self.current_layer, TextLayer):
            self.current_layer.is_font_parameter = is_parameter
            self.update_layer()
            
    def on_font_param_name_changed(self, name: str):
        """字体参数名变化"""
        if isinstance(self.current_layer, TextLayer):
            self.current_layer.font_parameter_name = name
            self.update_layer()
            
    def on_font_size_changed(self, size: int):
        """字体大小变化"""
        if isinstance(self.current_layer, TextLayer):
            self.current_layer.font_size = size
            self.update_layer()
            
    def on_h_align_changed(self, text: str):
        """水平对齐变化"""
        if isinstance(self.current_layer, TextLayer):
            align_map = {
                "左对齐": TextAlignment.LEFT,
                "居中": TextAlignment.CENTER,
                "右对齐": TextAlignment.RIGHT
            }
            self.current_layer.horizontal_align = align_map.get(text, TextAlignment.LEFT)
            self.update_layer()
            
    def on_v_align_changed(self, text: str):
        """垂直对齐变化"""
        if isinstance(self.current_layer, TextLayer):
            align_map = {
                "顶部": TextAlignment.TOP,
                "居中": TextAlignment.MIDDLE,
                "底部": TextAlignment.BOTTOM
            }
            self.current_layer.vertical_align = align_map.get(text, TextAlignment.TOP)
            self.update_layer()
            
    def browse_image(self):
        """浏览图片文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择图片",
            "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.tiff);;所有文件 (*)"
        )
        if file_path:
            self.image_path_edit.setText(file_path)
            
    def browse_font(self):
        """浏览字体文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择字体",
            "",
            "字体文件 (*.ttf *.otf);;所有文件 (*)"
        )
        if file_path:
            self.font_path_edit.setText(file_path)
            
    def choose_color(self):
        """选择颜色"""
        if isinstance(self.current_layer, TextLayer):
            current_color = QColor(*self.current_layer.color)
            color = QColorDialog.getColor(current_color, self, "选择文字颜色")
            if color.isValid():
                self.current_layer.color = (color.red(), color.green(), color.blue(), color.alpha())
                self.update_color_button(color)
                self.update_layer()
                
    def update_color_button(self, color: QColor):
        """更新颜色按钮显示"""
        self.color_btn.setStyleSheet(f"background-color: {color.name()};")
        self.color_label.setText(color.name())
        
    def update_layer(self):
        """更新图层"""
        if self.current_layer:
            self.project_model.update_layer(self.current_layer)
            
    def on_layer_updated(self, layer: BaseLayer):
        """处理图层更新信号"""
        # 如果更新的是当前选中的图层，则更新UI显示
        if self.current_layer and layer.id == self.current_layer.id:
            # 防止循环更新：先断开信号连接
            self.x_spinbox.blockSignals(True)
            self.y_spinbox.blockSignals(True)
            
            # 更新位置显示
            self.x_spinbox.setValue(layer.position.x)
            self.y_spinbox.setValue(layer.position.y)
            
            # 恢复信号连接
            self.x_spinbox.blockSignals(False)
            self.y_spinbox.blockSignals(False)
            
            # 更新当前图层引用
            self.current_layer = layer
            
    def on_base_image_parameter_changed(self, is_parameter: bool):
        """底图参数变化"""
        if isinstance(self.current_layer, BaseImageLayer):
            self.current_layer.is_path_parameter = is_parameter
            self.update_base_image()
            
    def on_base_image_param_name_changed(self, name: str):
        """底图参数名变化"""
        if isinstance(self.current_layer, BaseImageLayer):
            self.current_layer.parameter_name = name
            self.update_base_image()
            
    def browse_base_image(self):
        """浏览底图文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择底图",
            "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.tiff);;所有文件 (*)"
        )
        if file_path and isinstance(self.current_layer, BaseImageLayer):
            self.current_layer.image_path = file_path
            self.base_image_path_edit.setText(file_path)
            self.update_base_image()
            
    def update_base_image(self):
        """更新底图"""
        if isinstance(self.current_layer, BaseImageLayer):
            # 更新项目模型中的底图
            self.project_model._base_image = self.current_layer
            # 触发底图更新信号
            self.project_model.base_image_changed.emit(self.current_layer.image_path)
