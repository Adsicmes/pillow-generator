"""
图层面板实现
"""

from typing import Optional

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QHBoxLayout,
    QLabel,
    QCheckBox,
    QMenu,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction

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
        self.visibility_checkbox.setEnabled(layer.layer_type != LayerType.BASE)
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

        self.lock_label = QLabel("🔒" if layer.locked else "")
        layout.addWidget(self.lock_label)

        layout.addStretch()

    def on_visibility_changed(self, visible: bool):
        """可见性变化处理"""
        self.visibility_changed.emit(self.layer.id, visible)

    def update_layer(self, layer: BaseLayer):
        """更新图层信息"""
        self.layer = layer
        self.name_label.setText(layer.name)
        self.visibility_checkbox.setChecked(layer.visible)
        self.visibility_checkbox.setEnabled(
            layer.layer_type != LayerType.BASE and not layer.locked
        )
        self.lock_label.setText("🔒" if layer.locked else "")


class LayerPanel(QWidget):
    """图层面板"""

    # 信号定义
    layer_selected = Signal(str)  # layer_id
    layer_deleted = Signal(str)  # layer_id
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
        self.project_model.model_reset.connect(self.refresh_layer_list)

    def _set_button_states(self):
        current_item = self.layer_list.currentItem()
        if not current_item:
            self.delete_btn.setEnabled(False)
            self.move_up_btn.setEnabled(False)
            self.move_down_btn.setEnabled(False)
            return

        layer_id = current_item.data(Qt.ItemDataRole.UserRole)
        is_base_image = bool(
            self.project_model.base_image
            and self.project_model.base_image.id == layer_id
        )
        layer = (
            self.project_model.base_image
            if is_base_image
            else self.project_model.get_layer(layer_id)
        )
        is_locked = bool(layer and layer.locked)
        current_row = self.layer_list.currentRow()

        self.delete_btn.setEnabled(not is_locked)
        self.move_up_btn.setEnabled(
            not is_base_image and not is_locked and current_row > 0
        )
        self.move_down_btn.setEnabled(
            not is_base_image
            and not is_locked
            and current_row < self.layer_list.count() - 1
        )

    def _find_parent_handler(self, handler_name: str):
        parent = self.parent()
        while parent:
            handler = getattr(parent, handler_name, None)
            if callable(handler):
                return handler
            parent = parent.parent()
        return None

    def _is_base_image_id(self, layer_id: str | None) -> bool:
        return bool(
            layer_id
            and self.project_model.base_image
            and self.project_model.base_image.id == layer_id
        )

    def add_image_layer(self):
        """添加图片层"""
        handler = self._find_parent_handler("add_image_layer")
        if handler:
            handler()

    def add_text_layer(self):
        """添加文字层"""
        handler = self._find_parent_handler("add_text_layer")
        if handler:
            handler()

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
                if isinstance(widget, LayerItemWidget):
                    widget.update_layer(layer)
                if self.current_layer_id == layer.id:
                    self._set_button_states()
                break

    def update_base_image_item(self, image_path: str):
        """更新底图项显示"""
        base_image = self.project_model.base_image
        base_item = None
        for i in range(self.layer_list.count()):
            item = self.layer_list.item(i)
            widget = self.layer_list.itemWidget(item)
            if (
                isinstance(widget, LayerItemWidget)
                and widget.layer.layer_type == LayerType.BASE
            ):
                base_item = item
                break

        if not base_image:
            if base_item:
                self.layer_list.takeItem(self.layer_list.row(base_item))
            self._set_button_states()
            return

        if base_image:
            if base_item:
                widget = self.layer_list.itemWidget(base_item)
                if isinstance(widget, LayerItemWidget):
                    widget.update_layer(base_image)
            else:
                item = QListWidgetItem()
                layer_widget = LayerItemWidget(base_image)
                layer_widget.visibility_changed.connect(
                    self.on_layer_visibility_changed
                )

                item.setSizeHint(layer_widget.sizeHint())
                item.setData(Qt.ItemDataRole.UserRole, base_image.id)

                self.layer_list.insertItem(0, item)
                self.layer_list.setItemWidget(item, layer_widget)
        self._set_button_states()

    def on_selection_changed(self):
        """处理选择变化"""
        current_item = self.layer_list.currentItem()
        if current_item:
            layer_id = current_item.data(Qt.ItemDataRole.UserRole)
            self.current_layer_id = layer_id
            self.layer_selected.emit(layer_id)
        else:
            self.current_layer_id = None
        self._set_button_states()

    def select_layer(self, layer_id: str):
        if not layer_id:
            self.layer_list.clearSelection()
            self.current_layer_id = None
            self._set_button_states()
            return

        for i in range(self.layer_list.count()):
            item = self.layer_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == layer_id:
                self.current_layer_id = layer_id
                if self.layer_list.currentItem() is not item:
                    self.layer_list.setCurrentItem(item)
                self._set_button_states()
                return

    def on_layer_visibility_changed(self, layer_id: str, visible: bool):
        """处理图层可见性变化"""
        if self._is_base_image_id(layer_id):
            return
        layer = self.project_model.get_layer(layer_id)
        if layer and not layer.locked:
            self.project_model.apply_operation(
                "切换图层可见性",
                lambda: self._apply_layer_visibility(layer_id, visible),
            )

    def _apply_layer_visibility(self, layer_id: str, visible: bool):
        layer = self.project_model.get_layer(layer_id)
        if layer:
            layer.visible = visible
            self.project_model.update_layer(layer)

    def delete_selected_layer(self):
        """删除选中的图层"""
        if self.current_layer_id:
            if self._is_base_image_id(self.current_layer_id):
                base_image = self.project_model.base_image
                if base_image and not base_image.locked:
                    self.project_model.apply_operation(
                        "删除底图", self.project_model.clear_base_image
                    )
                self.layer_list.clearSelection()
                self.current_layer_id = None
                self._set_button_states()
                return
            layer = self.project_model.get_layer(self.current_layer_id)
            if layer and not layer.locked:
                self.project_model.apply_operation(
                    "删除图层",
                    lambda: self.project_model.remove_layer(
                        self.current_layer_id or ""
                    ),
                )

    def move_layer_up(self):
        """上移图层"""
        current_row = self.layer_list.currentRow()
        if (
            current_row > 0
            and self.current_layer_id
            and not self._is_base_image_id(self.current_layer_id)
        ):
            layer = self.project_model.get_layer(self.current_layer_id)
            if layer and layer.locked:
                return
            self.project_model.apply_operation(
                "上移图层",
                lambda: self.project_model.move_layer(
                    self.current_layer_id or "", current_row - 1
                ),
            )
            self.refresh_layer_list()
            self.layer_list.setCurrentRow(current_row - 1)

    def move_layer_down(self):
        """下移图层"""
        current_row = self.layer_list.currentRow()
        if (
            current_row < self.layer_list.count() - 1
            and self.current_layer_id
            and not self._is_base_image_id(self.current_layer_id)
        ):
            layer = self.project_model.get_layer(self.current_layer_id)
            if layer and layer.locked:
                return
            self.project_model.apply_operation(
                "下移图层",
                lambda: self.project_model.move_layer(
                    self.current_layer_id or "", current_row + 1
                ),
            )
            self.refresh_layer_list()
            self.layer_list.setCurrentRow(current_row + 1)

    def show_context_menu(self, position):
        """显示右键菜单"""
        item = self.layer_list.itemAt(position)
        if item:
            menu = QMenu(self)
            layer_id = item.data(Qt.ItemDataRole.UserRole)
            is_base_image = self._is_base_image_id(layer_id)
            layer = (
                self.project_model.base_image
                if is_base_image
                else self.project_model.get_layer(layer_id)
            )
            is_locked = bool(layer and layer.locked)

            if not is_base_image:
                duplicate_action = QAction("复制图层", self)
                duplicate_action.triggered.connect(
                    lambda: self.duplicate_layer(layer_id)
                )
                menu.addAction(duplicate_action)

            if layer:
                lock_action = QAction("解锁图层" if layer.locked else "锁定图层", self)
                lock_action.triggered.connect(lambda: self.toggle_layer_lock(layer_id))
                menu.addAction(lock_action)

            delete_action = QAction("删除底图" if is_base_image else "删除图层", self)
            delete_action.setEnabled(not is_locked)
            delete_action.triggered.connect(
                lambda: (
                    self.project_model.apply_operation(
                        "删除底图", self.project_model.clear_base_image
                    )
                    if is_base_image
                    else self.project_model.apply_operation(
                        "删除图层", lambda: self.project_model.remove_layer(layer_id)
                    )
                )
            )
            menu.addAction(delete_action)

            menu.exec(self.layer_list.mapToGlobal(position))

    def duplicate_layer(self, layer_id: str):
        """复制图层"""
        duplicated_layer = None
        self.project_model.apply_operation(
            "复制图层",
            lambda: self._duplicate_layer_internal(layer_id),
        )
        duplicated_layer = (
            self.project_model.get_all_layers()[-1]
            if self.project_model.get_all_layers()
            else None
        )
        if duplicated_layer:
            self.select_layer(duplicated_layer.id)

    def _duplicate_layer_internal(self, layer_id: str):
        self.project_model.duplicate_layer(layer_id)

    def toggle_layer_lock(self, layer_id: str):
        if self._is_base_image_id(layer_id):
            base_image = self.project_model.base_image
            if not base_image:
                return
            self.project_model.apply_operation(
                "切换底图锁定",
                lambda: self._set_base_lock(not base_image.locked),
            )
            return

        layer = self.project_model.get_layer(layer_id)
        if not layer:
            return
        self.project_model.apply_operation(
            "切换图层锁定",
            lambda: self._set_layer_lock(layer_id, not layer.locked),
        )

    def _set_layer_lock(self, layer_id: str, locked: bool):
        layer = self.project_model.get_layer(layer_id)
        if layer:
            layer.locked = locked
            self.project_model.update_layer(layer)

    def _set_base_lock(self, locked: bool):
        if self.project_model.base_image:
            self.project_model.base_image.locked = locked
            self.project_model.replace_base_image(self.project_model.base_image)

    def refresh_layer_list(self):
        """刷新图层列表"""
        self.layer_list.clear()

        if self.project_model.base_image:
            self.update_base_image_item("")

        for layer in self.project_model.get_all_layers():
            self.add_layer_item(layer)

        self._set_button_states()
