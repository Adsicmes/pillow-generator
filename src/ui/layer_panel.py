"""
图层面板实现
"""
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QHBoxLayout, QLabel, QCheckBox, QMenu
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QAction

from ..core.models import ProjectModel, BaseLayer, LayerType


class LayerItemWidget(QWidget):
    """图层项组件"""
    
    visibility_changed = Signal(str, bool)  # layer_id, visible
    
    def __init__(self, layer: BaseLayer, parent=None):
        super().__init__(parent)
        
        self.layer = layer
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        
        # 可见性复选框
        self.visibility_checkbox = QCheckBox()
        self.visibility_checkbox.setChecked(layer.visible)
        self.visibility_checkbox.toggled.connect(self.on_visibility_changed)
        layout.addWidget(self.visibility_checkbox)
        
        # 图层类型图标
        type_label = QLabel()
        if layer.layer_type == LayerType.BASE:
            type_label.setText("🖼️")
        elif layer.layer_type == LayerType.IMAGE:
            type_label.setText("🖼️")
        elif layer.layer_type == LayerType.TEXT:
            type_label.setText("📝")
        layout.addWidget(type_label)
        
        # 图层名称
        self.name_label = QLabel(layer.name)
        layout.addWidget(self.name_label)
        
        layout.addStretch()
        
    def on_visibility_changed(self, visible: bool):
        """可见性变化处理"""
        self.visibility_changed.emit(self.layer.id, visible)
        
    def update_layer(self, layer: BaseLayer):
        """更新图层信息"""
        self.layer = layer
        self.name_label.setText(layer.name)
        self.visibility_checkbox.setChecked(layer.visible)


class LayerPanel(QWidget):
    """图层面板"""
    
    # 信号定义
    layer_selected = Signal(str)  # layer_id
    layer_deleted = Signal(str)   # layer_id
    layer_duplicated = Signal(str)  # layer_id
    
    def __init__(self, project_model: ProjectModel, parent=None):
        super().__init__(parent)
        
        self.project_model = project_model
        self.current_layer_id: Optional[str] = None
        
        self.init_ui()
        self.connect_signals()
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel("图层")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title_label)
        
        # 按钮行
        button_layout = QHBoxLayout()
        
        self.add_image_btn = QPushButton("+ 图片")
        self.add_image_btn.clicked.connect(self.add_image_layer)
        button_layout.addWidget(self.add_image_btn)
        
        self.add_text_btn = QPushButton("+ 文字")
        self.add_text_btn.clicked.connect(self.add_text_layer)
        button_layout.addWidget(self.add_text_btn)
        
        self.delete_btn = QPushButton("删除")
        self.delete_btn.setEnabled(False)
        self.delete_btn.clicked.connect(self.delete_selected_layer)
        button_layout.addWidget(self.delete_btn)
        
        layout.addLayout(button_layout)
        
        # 图层列表
        self.layer_list = QListWidget()
        self.layer_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.layer_list.customContextMenuRequested.connect(self.show_context_menu)
        self.layer_list.itemSelectionChanged.connect(self.on_selection_changed)
        layout.addWidget(self.layer_list)
        
        # 上移下移按钮
        move_layout = QHBoxLayout()
        
        self.move_up_btn = QPushButton("上移")
        self.move_up_btn.setEnabled(False)
        self.move_up_btn.clicked.connect(self.move_layer_up)
        move_layout.addWidget(self.move_up_btn)
        
        self.move_down_btn = QPushButton("下移")
        self.move_down_btn.setEnabled(False)
        self.move_down_btn.clicked.connect(self.move_layer_down)
        move_layout.addWidget(self.move_down_btn)
        
        layout.addLayout(move_layout)
        
    def connect_signals(self):
        """连接信号槽"""
        self.project_model.layer_added.connect(self.add_layer_item)
        self.project_model.layer_removed.connect(self.remove_layer_item)
        self.project_model.layer_updated.connect(self.update_layer_item)
        self.project_model.base_image_changed.connect(self.update_base_image_item)
        
    def add_image_layer(self):
        """添加图片层"""
        # 触发父窗口的添加图片层功能
        parent = self.parent()
        while parent:
            if hasattr(parent, 'add_image_layer'):
                parent.add_image_layer()
                break
            parent = parent.parent()
            
    def add_text_layer(self):
        """添加文字层"""
        # 触发父窗口的添加文字层功能
        parent = self.parent()
        while parent:
            if hasattr(parent, 'add_text_layer'):
                parent.add_text_layer()
                break
            parent = parent.parent()
            
    def add_layer_item(self, layer: BaseLayer):
        """添加图层项"""
        item = QListWidgetItem()
        layer_widget = LayerItemWidget(layer)
        layer_widget.visibility_changed.connect(self.on_layer_visibility_changed)
        
        item.setSizeHint(layer_widget.sizeHint())
        item.setData(Qt.ItemDataRole.UserRole, layer.id)
        
        self.layer_list.addItem(item)
        self.layer_list.setItemWidget(item, layer_widget)
        
        # 选择新添加的图层
        self.layer_list.setCurrentItem(item)
        
    def remove_layer_item(self, layer_id: str):
        """移除图层项"""
        for i in range(self.layer_list.count()):
            item = self.layer_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == layer_id:
                self.layer_list.takeItem(i)
                break
                
    def update_layer_item(self, layer: BaseLayer):
        """更新图层项"""
        for i in range(self.layer_list.count()):
            item = self.layer_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == layer.id:
                widget = self.layer_list.itemWidget(item)
                if widget:
                    widget.update_layer(layer)
                break
                
    def update_base_image_item(self, image_path: str):
        """更新底图项显示"""
        # 如果有底图，在列表顶部显示
        base_image = self.project_model.base_image
        if base_image:
            # 检查是否已存在底图项
            base_item = None
            for i in range(self.layer_list.count()):
                item = self.layer_list.item(i)
                widget = self.layer_list.itemWidget(item)
                if widget and widget.layer.layer_type == LayerType.BASE:
                    base_item = item
                    break
                    
            if base_item:
                # 更新现有项
                widget = self.layer_list.itemWidget(base_item)
                widget.update_layer(base_image)
            else:
                # 添加新的底图项
                item = QListWidgetItem()
                layer_widget = LayerItemWidget(base_image)
                
                item.setSizeHint(layer_widget.sizeHint())
                item.setData(Qt.ItemDataRole.UserRole, base_image.id)
                
                # 插入到顶部
                self.layer_list.insertItem(0, item)
                self.layer_list.setItemWidget(item, layer_widget)
                
    def on_selection_changed(self):
        """处理选择变化"""
        current_item = self.layer_list.currentItem()
        if current_item:
            layer_id = current_item.data(Qt.ItemDataRole.UserRole)
            self.current_layer_id = layer_id
            self.layer_selected.emit(layer_id)
            
            # 更新按钮状态
            self.delete_btn.setEnabled(True)
            self.move_up_btn.setEnabled(self.layer_list.currentRow() > 0)
            self.move_down_btn.setEnabled(self.layer_list.currentRow() < self.layer_list.count() - 1)
        else:
            self.current_layer_id = None
            self.delete_btn.setEnabled(False)
            self.move_up_btn.setEnabled(False)
            self.move_down_btn.setEnabled(False)
            
    def on_layer_visibility_changed(self, layer_id: str, visible: bool):
        """处理图层可见性变化"""
        layer = self.project_model.get_layer(layer_id)
        if layer:
            layer.visible = visible
            self.project_model.update_layer(layer)
            
    def delete_selected_layer(self):
        """删除选中的图层"""
        if self.current_layer_id:
            self.project_model.remove_layer(self.current_layer_id)
            
    def move_layer_up(self):
        """上移图层"""
        current_row = self.layer_list.currentRow()
        if current_row > 0 and self.current_layer_id:
            self.project_model.move_layer(self.current_layer_id, current_row - 1)
            self.refresh_layer_list()
            self.layer_list.setCurrentRow(current_row - 1)
            
    def move_layer_down(self):
        """下移图层"""
        current_row = self.layer_list.currentRow()
        if current_row < self.layer_list.count() - 1 and self.current_layer_id:
            self.project_model.move_layer(self.current_layer_id, current_row + 1)
            self.refresh_layer_list()
            self.layer_list.setCurrentRow(current_row + 1)
            
    def show_context_menu(self, position):
        """显示右键菜单"""
        item = self.layer_list.itemAt(position)
        if item:
            menu = QMenu(self)
            
            duplicate_action = QAction("复制图层", self)
            duplicate_action.triggered.connect(lambda: self.duplicate_layer(item.data(Qt.ItemDataRole.UserRole)))
            menu.addAction(duplicate_action)
            
            delete_action = QAction("删除图层", self)
            delete_action.triggered.connect(lambda: self.project_model.remove_layer(item.data(Qt.ItemDataRole.UserRole)))
            menu.addAction(delete_action)
            
            menu.exec(self.layer_list.mapToGlobal(position))
            
    def duplicate_layer(self, layer_id: str):
        """复制图层"""
        layer = self.project_model.get_layer(layer_id)
        if layer:
            # TODO: 实现图层复制逻辑
            pass
            
    def refresh_layer_list(self):
        """刷新图层列表"""
        # 清空列表
        self.layer_list.clear()
        
        # 重新添加底图
        if self.project_model.base_image:
            self.update_base_image_item("")
            
        # 重新添加所有图层
        for layer in self.project_model.get_all_layers():
            self.add_layer_item(layer)
