"""
属性面板实现
"""

import copy
from typing import Callable

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ..core.models import (
    BaseImageLayer,
    BaseLayer,
    ImageLayer,
    LayerType,
    ProjectModel,
    TextAlignment,
    TextLayer,
)


class PropertyPanel(QWidget):
    """属性面板"""

    def __init__(self, project_model: ProjectModel, parent=None):
        super().__init__(parent)

        self.project_model = project_model
        self.current_layer: BaseLayer | None = None
        self._editor_widgets: list[QWidget] = []
        self._pending_history: dict[str, tuple[dict[str, object], str, QTimer]] = {}

        self.init_ui()
        self.connect_signals()

    def connect_signals(self):
        self.project_model.layer_updated.connect(self.on_layer_updated)
        self.project_model.model_reset.connect(self.on_model_reset)
        self.project_model.base_image_changed.connect(self.on_base_image_changed)
        self.project_model.pending_history_commit_requested.connect(
            self.commit_all_history_groups
        )

    def init_ui(self):
        layout = QVBoxLayout(self)

        title_label = QLabel("属性")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title_label)

        self.basic_group = QGroupBox("基本属性")
        layout.addWidget(self.basic_group)
        basic_layout = QFormLayout(self.basic_group)

        self.name_edit = QLineEdit()
        self.name_edit.textChanged.connect(self.on_name_changed)
        self.name_edit.editingFinished.connect(
            lambda: self.commit_history_group("layer_name")
        )
        basic_layout.addRow("名称:", self.name_edit)

        self.visible_checkbox = QCheckBox()
        self.visible_checkbox.toggled.connect(self.on_visibility_changed)
        basic_layout.addRow("可见:", self.visible_checkbox)

        self.locked_checkbox = QCheckBox()
        self.locked_checkbox.toggled.connect(self.on_locked_changed)
        basic_layout.addRow("锁定:", self.locked_checkbox)

        self.position_group = QGroupBox("位置")
        layout.addWidget(self.position_group)
        position_layout = QFormLayout(self.position_group)

        self.x_spinbox = QSpinBox()
        self.x_spinbox.setRange(-9999, 9999)
        self.x_spinbox.valueChanged.connect(self.on_position_changed)
        self.x_spinbox.editingFinished.connect(
            lambda: self.commit_history_group("layer_position")
        )
        position_layout.addRow("X:", self.x_spinbox)

        self.y_spinbox = QSpinBox()
        self.y_spinbox.setRange(-9999, 9999)
        self.y_spinbox.valueChanged.connect(self.on_position_changed)
        self.y_spinbox.editingFinished.connect(
            lambda: self.commit_history_group("layer_position")
        )
        position_layout.addRow("Y:", self.y_spinbox)

        self.image_group = QGroupBox("图片属性")
        layout.addWidget(self.image_group)
        image_layout = QFormLayout(self.image_group)

        image_path_layout = QHBoxLayout()
        self.image_path_edit = QLineEdit()
        self.image_path_edit.textChanged.connect(self.on_image_path_changed)
        self.image_path_edit.editingFinished.connect(
            lambda: self.commit_history_group("image_path")
        )
        image_path_layout.addWidget(self.image_path_edit)
        self.browse_image_btn = QPushButton("浏览")
        self.browse_image_btn.clicked.connect(self.browse_image)
        image_path_layout.addWidget(self.browse_image_btn)
        image_layout.addRow("图片路径:", image_path_layout)

        self.image_parameter_checkbox = QCheckBox()
        self.image_parameter_checkbox.toggled.connect(self.on_image_parameter_changed)
        image_layout.addRow("作为参数:", self.image_parameter_checkbox)

        self.image_param_name_edit = QLineEdit()
        self.image_param_name_edit.textChanged.connect(self.on_image_param_name_changed)
        self.image_param_name_edit.editingFinished.connect(
            lambda: self.commit_history_group("image_param_name")
        )
        image_layout.addRow("参数名:", self.image_param_name_edit)

        size_layout = QHBoxLayout()
        self.width_spinbox = QSpinBox()
        self.width_spinbox.setRange(1, 9999)
        self.width_spinbox.valueChanged.connect(self.on_size_changed)
        self.width_spinbox.editingFinished.connect(
            lambda: self.commit_history_group("image_size")
        )
        size_layout.addWidget(QLabel("宽:"))
        size_layout.addWidget(self.width_spinbox)
        self.height_spinbox = QSpinBox()
        self.height_spinbox.setRange(1, 9999)
        self.height_spinbox.valueChanged.connect(self.on_size_changed)
        self.height_spinbox.editingFinished.connect(
            lambda: self.commit_history_group("image_size")
        )
        size_layout.addWidget(QLabel("高:"))
        size_layout.addWidget(self.height_spinbox)
        image_layout.addRow("尺寸:", size_layout)

        opacity_layout = QHBoxLayout()
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.sliderPressed.connect(
            lambda: self.begin_history_group("image_opacity", "修改图片透明度")
        )
        self.opacity_slider.valueChanged.connect(self.on_opacity_changed)
        self.opacity_slider.sliderReleased.connect(
            lambda: self.commit_history_group("image_opacity")
        )
        opacity_layout.addWidget(self.opacity_slider)
        self.opacity_label = QLabel("100%")
        opacity_layout.addWidget(self.opacity_label)
        image_layout.addRow("透明度:", opacity_layout)

        self.rotation_spinbox = QDoubleSpinBox()
        self.rotation_spinbox.setRange(-360, 360)
        self.rotation_spinbox.setSuffix("°")
        self.rotation_spinbox.valueChanged.connect(self.on_rotation_changed)
        self.rotation_spinbox.editingFinished.connect(
            lambda: self.commit_history_group("image_rotation")
        )
        image_layout.addRow("旋转:", self.rotation_spinbox)

        self.base_image_group = QGroupBox("底图属性")
        layout.addWidget(self.base_image_group)
        base_image_layout = QFormLayout(self.base_image_group)

        base_path_layout = QHBoxLayout()
        self.base_image_path_edit = QLineEdit()
        self.base_image_path_edit.textChanged.connect(self.on_base_image_path_changed)
        self.base_image_path_edit.editingFinished.connect(
            lambda: self.commit_history_group("base_image_path")
        )
        base_path_layout.addWidget(self.base_image_path_edit)
        self.browse_base_image_btn = QPushButton("浏览")
        self.browse_base_image_btn.clicked.connect(self.browse_base_image)
        base_path_layout.addWidget(self.browse_base_image_btn)
        base_image_layout.addRow("底图路径:", base_path_layout)

        self.base_image_parameter_checkbox = QCheckBox()
        self.base_image_parameter_checkbox.toggled.connect(
            self.on_base_image_parameter_changed
        )
        base_image_layout.addRow("作为参数:", self.base_image_parameter_checkbox)

        self.base_image_param_name_edit = QLineEdit()
        self.base_image_param_name_edit.textChanged.connect(
            self.on_base_image_param_name_changed
        )
        self.base_image_param_name_edit.editingFinished.connect(
            lambda: self.commit_history_group("base_image_param_name")
        )
        base_image_layout.addRow("参数名:", self.base_image_param_name_edit)

        self.text_group = QGroupBox("文字属性")
        layout.addWidget(self.text_group)
        text_layout = QFormLayout(self.text_group)

        self.text_edit = QLineEdit()
        self.text_edit.textChanged.connect(self.on_text_changed)
        self.text_edit.editingFinished.connect(
            lambda: self.commit_history_group("text_content")
        )
        text_layout.addRow("文字:", self.text_edit)

        self.text_parameter_checkbox = QCheckBox()
        self.text_parameter_checkbox.toggled.connect(self.on_text_parameter_changed)
        text_layout.addRow("文字作为参数:", self.text_parameter_checkbox)

        self.text_param_name_edit = QLineEdit()
        self.text_param_name_edit.textChanged.connect(self.on_text_param_name_changed)
        self.text_param_name_edit.editingFinished.connect(
            lambda: self.commit_history_group("text_param_name")
        )
        text_layout.addRow("文字参数名:", self.text_param_name_edit)

        font_path_layout = QHBoxLayout()
        self.font_path_edit = QLineEdit()
        self.font_path_edit.textChanged.connect(self.on_font_path_changed)
        self.font_path_edit.editingFinished.connect(
            lambda: self.commit_history_group("font_path")
        )
        font_path_layout.addWidget(self.font_path_edit)
        self.browse_font_btn = QPushButton("浏览")
        self.browse_font_btn.clicked.connect(self.browse_font)
        font_path_layout.addWidget(self.browse_font_btn)
        text_layout.addRow("字体文件:", font_path_layout)

        self.font_parameter_checkbox = QCheckBox()
        self.font_parameter_checkbox.toggled.connect(self.on_font_parameter_changed)
        text_layout.addRow("字体作为参数:", self.font_parameter_checkbox)

        self.font_param_name_edit = QLineEdit()
        self.font_param_name_edit.textChanged.connect(self.on_font_param_name_changed)
        self.font_param_name_edit.editingFinished.connect(
            lambda: self.commit_history_group("font_param_name")
        )
        text_layout.addRow("字体参数名:", self.font_param_name_edit)

        self.font_size_spinbox = QSpinBox()
        self.font_size_spinbox.setRange(8, 200)
        self.font_size_spinbox.valueChanged.connect(self.on_font_size_changed)
        self.font_size_spinbox.editingFinished.connect(
            lambda: self.commit_history_group("font_size")
        )
        text_layout.addRow("字体大小:", self.font_size_spinbox)

        color_layout = QHBoxLayout()
        self.color_btn = QPushButton()
        self.color_btn.setFixedSize(50, 25)
        self.color_btn.clicked.connect(self.choose_color)
        color_layout.addWidget(self.color_btn)
        self.color_label = QLabel("#000000")
        color_layout.addWidget(self.color_label)
        text_layout.addRow("颜色:", color_layout)

        self.h_align_combo = QComboBox()
        self.h_align_combo.addItems(["左对齐", "居中", "右对齐"])
        self.h_align_combo.currentTextChanged.connect(self.on_h_align_changed)
        text_layout.addRow("水平对齐:", self.h_align_combo)

        self.v_align_combo = QComboBox()
        self.v_align_combo.addItems(["顶部", "居中", "底部"])
        self.v_align_combo.currentTextChanged.connect(self.on_v_align_changed)
        text_layout.addRow("垂直对齐:", self.v_align_combo)

        text_layout.addRow(QLabel(""))

        max_width_layout = QHBoxLayout()
        self.max_width_checkbox = QCheckBox("启用宽度限制")
        self.max_width_checkbox.toggled.connect(self.on_max_width_enabled_changed)
        max_width_layout.addWidget(self.max_width_checkbox)
        self.max_width_spinbox = QSpinBox()
        self.max_width_spinbox.setRange(50, 9999)
        self.max_width_spinbox.setSuffix("px")
        self.max_width_spinbox.valueChanged.connect(self.on_max_width_changed)
        self.max_width_spinbox.editingFinished.connect(
            lambda: self.commit_history_group("max_width")
        )
        max_width_layout.addWidget(self.max_width_spinbox)
        text_layout.addRow("宽度限制:", max_width_layout)

        self.truncate_suffix_edit = QLineEdit()
        self.truncate_suffix_edit.textChanged.connect(self.on_truncate_suffix_changed)
        self.truncate_suffix_edit.editingFinished.connect(
            lambda: self.commit_history_group("truncate_suffix")
        )
        text_layout.addRow("截断后缀:", self.truncate_suffix_edit)

        self.update_color_button(QColor(0, 0, 0))
        layout.addStretch()

        self._editor_widgets = [
            self.name_edit,
            self.visible_checkbox,
            self.x_spinbox,
            self.y_spinbox,
            self.image_path_edit,
            self.browse_image_btn,
            self.image_parameter_checkbox,
            self.image_param_name_edit,
            self.width_spinbox,
            self.height_spinbox,
            self.opacity_slider,
            self.rotation_spinbox,
            self.base_image_path_edit,
            self.base_image_parameter_checkbox,
            self.base_image_param_name_edit,
            self.browse_base_image_btn,
            self.text_edit,
            self.text_parameter_checkbox,
            self.text_param_name_edit,
            self.font_path_edit,
            self.browse_font_btn,
            self.font_parameter_checkbox,
            self.font_param_name_edit,
            self.font_size_spinbox,
            self.color_btn,
            self.h_align_combo,
            self.v_align_combo,
            self.max_width_checkbox,
            self.max_width_spinbox,
            self.truncate_suffix_edit,
        ]
        self.hide_all_groups()

    def hide_all_groups(self):
        self.basic_group.hide()
        self.position_group.hide()
        self.image_group.hide()
        self.base_image_group.hide()
        self.text_group.hide()

    def _set_editor_signals_blocked(self, blocked: bool):
        for widget in self._editor_widgets:
            widget.blockSignals(blocked)
        self.locked_checkbox.blockSignals(blocked)

    def _set_editable_state(self, editable: bool):
        for widget in self._editor_widgets:
            widget.setEnabled(editable)

        if self.current_layer and self.current_layer.layer_type == LayerType.BASE:
            self.visible_checkbox.setEnabled(False)
        else:
            self.visible_checkbox.setEnabled(editable)

        has_max_width = (
            isinstance(self.current_layer, TextLayer)
            and self.current_layer.max_width is not None
        )
        self.max_width_spinbox.setEnabled(editable and has_max_width)
        self.truncate_suffix_edit.setEnabled(editable and has_max_width)
        self.locked_checkbox.setEnabled(True)

    def begin_history_group(self, key: str, description: str):
        if key in self._pending_history or not self.current_layer:
            return

        timer = QTimer(self)
        timer.setSingleShot(True)
        timer.timeout.connect(lambda key=key: self.commit_history_group(key))
        before_snapshot = self.project_model.capture_snapshot()
        self._pending_history[key] = (before_snapshot, description, timer)

    def schedule_history_group_commit(self, key: str, delay_ms: int = 350):
        pending = self._pending_history.get(key)
        if not pending:
            return
        pending[2].start(delay_ms)

    def commit_history_group(self, key: str):
        pending = self._pending_history.pop(key, None)
        if not pending:
            return
        before_snapshot, description, timer = pending
        timer.stop()
        self.project_model.record_manual_change(before_snapshot, description)

    def commit_all_history_groups(self):
        for key in list(self._pending_history.keys()):
            self.commit_history_group(key)

    def _replace_updated_layer(self, updated_layer: BaseLayer):
        if isinstance(updated_layer, BaseImageLayer):
            self.project_model.replace_base_image(updated_layer)
        else:
            self.project_model.replace_layer(updated_layer)

    def _apply_current_layer_change(
        self,
        description: str,
        mutator: Callable[[BaseLayer], None],
        merge_key: str | None = None,
        auto_commit_delay_ms: int | None = 350,
    ):
        if not self.current_layer:
            return
        if self.current_layer.locked and description != "切换图层锁定":
            return

        before_snapshot: dict[str, object] | None = None
        if merge_key is None:
            before_snapshot = self.project_model.capture_snapshot()
        else:
            self.begin_history_group(merge_key, description)

        updated_layer = copy.deepcopy(self.current_layer)
        mutator(updated_layer)
        self._replace_updated_layer(updated_layer)

        if before_snapshot is not None:
            self.project_model.record_manual_change(before_snapshot, description)
        elif merge_key and auto_commit_delay_ms is not None:
            self.schedule_history_group_commit(merge_key, auto_commit_delay_ms)

    def set_current_layer(self, layer_id: str):
        self.commit_all_history_groups()
        layer = self.project_model.get_layer(layer_id)
        if not layer and self.project_model.base_image:
            if self.project_model.base_image.id == layer_id:
                layer = self.project_model.base_image

        if layer:
            self.current_layer = layer
            self.update_ui()
        else:
            self.current_layer = None
            self.hide_all_groups()

    def update_ui(self):
        if not self.current_layer:
            return

        self._set_editor_signals_blocked(True)
        self.basic_group.show()
        self.name_edit.setText(self.current_layer.name)
        self.visible_checkbox.setChecked(self.current_layer.visible)
        self.locked_checkbox.setChecked(self.current_layer.locked)

        if self.current_layer.layer_type != LayerType.BASE:
            self.position_group.show()
            self.x_spinbox.setValue(self.current_layer.position.x)
            self.y_spinbox.setValue(self.current_layer.position.y)
        else:
            self.position_group.hide()

        self.image_group.hide()
        self.base_image_group.hide()
        self.text_group.hide()

        if isinstance(self.current_layer, ImageLayer):
            layer = self.current_layer
            self.image_group.show()
            self.image_path_edit.setText(layer.image_path)
            self.image_parameter_checkbox.setChecked(layer.is_path_parameter)
            self.image_param_name_edit.setText(layer.parameter_name)
            self.width_spinbox.setValue(layer.size.width)
            self.height_spinbox.setValue(layer.size.height)
            self.opacity_slider.setValue(int(layer.opacity * 100))
            self.opacity_label.setText(f"{int(layer.opacity * 100)}%")
            self.rotation_spinbox.setValue(layer.rotation)
        elif isinstance(self.current_layer, TextLayer):
            layer = self.current_layer
            self.text_group.show()
            self.text_edit.setText(layer.text)
            self.text_parameter_checkbox.setChecked(layer.is_text_parameter)
            self.text_param_name_edit.setText(layer.text_parameter_name)
            self.font_path_edit.setText(layer.font_path)
            self.font_parameter_checkbox.setChecked(layer.is_font_parameter)
            self.font_param_name_edit.setText(layer.font_parameter_name)
            self.font_size_spinbox.setValue(layer.font_size)
            self.update_color_button(QColor(*layer.color))
            self.h_align_combo.setCurrentIndex(
                {
                    TextAlignment.LEFT: 0,
                    TextAlignment.CENTER: 1,
                    TextAlignment.RIGHT: 2,
                }.get(layer.horizontal_align, 0)
            )
            self.v_align_combo.setCurrentIndex(
                {
                    TextAlignment.TOP: 0,
                    TextAlignment.MIDDLE: 1,
                    TextAlignment.BOTTOM: 2,
                }.get(layer.vertical_align, 0)
            )
            has_max_width = layer.max_width is not None
            self.max_width_checkbox.setChecked(has_max_width)
            if layer.max_width is not None:
                self.max_width_spinbox.setValue(layer.max_width)
            self.truncate_suffix_edit.setText(layer.truncate_suffix)
        elif isinstance(self.current_layer, BaseImageLayer):
            layer = self.current_layer
            self.base_image_group.show()
            self.base_image_path_edit.setText(layer.image_path)
            self.base_image_parameter_checkbox.setChecked(layer.is_path_parameter)
            self.base_image_param_name_edit.setText(layer.parameter_name)

        self._set_editable_state(not self.current_layer.locked)
        self._set_editor_signals_blocked(False)

    def on_name_changed(self, text: str):
        self._apply_current_layer_change(
            "修改图层名称",
            lambda layer: setattr(layer, "name", text),
            merge_key="layer_name",
        )

    def on_visibility_changed(self, visible: bool):
        self._apply_current_layer_change(
            "切换图层可见性", lambda layer: setattr(layer, "visible", visible)
        )

    def on_locked_changed(self, locked: bool):
        self._apply_current_layer_change(
            "切换图层锁定", lambda layer: setattr(layer, "locked", locked)
        )

    def on_position_changed(self):
        x_value = self.x_spinbox.value()
        y_value = self.y_spinbox.value()

        def mutate_position(layer: BaseLayer):
            layer.position.x = x_value
            layer.position.y = y_value

        self._apply_current_layer_change(
            "修改图层位置", mutate_position, merge_key="layer_position"
        )

    def on_image_path_changed(self, path: str):
        self._apply_current_layer_change(
            "修改图片路径",
            lambda layer: setattr(layer, "image_path", path),
            merge_key="image_path",
        )

    def on_image_parameter_changed(self, is_parameter: bool):
        self._apply_current_layer_change(
            "切换图片参数",
            lambda layer: setattr(layer, "is_path_parameter", is_parameter),
        )

    def on_image_param_name_changed(self, name: str):
        self._apply_current_layer_change(
            "修改图片参数名",
            lambda layer: setattr(layer, "parameter_name", name),
            merge_key="image_param_name",
        )

    def on_size_changed(self):
        width = self.width_spinbox.value()
        height = self.height_spinbox.value()

        def mutate_size(layer: BaseLayer):
            if isinstance(layer, ImageLayer):
                layer.size.width = width
                layer.size.height = height

        self._apply_current_layer_change(
            "修改图片尺寸", mutate_size, merge_key="image_size"
        )

    def on_opacity_changed(self, value: int):
        self.opacity_label.setText(f"{value}%")
        self._apply_current_layer_change(
            "修改图片透明度",
            lambda layer: setattr(layer, "opacity", value / 100.0),
            merge_key="image_opacity",
            auto_commit_delay_ms=None if self.opacity_slider.isSliderDown() else 350,
        )

    def on_rotation_changed(self, value: float):
        self._apply_current_layer_change(
            "修改图片旋转",
            lambda layer: setattr(layer, "rotation", value),
            merge_key="image_rotation",
        )

    def on_text_changed(self, text: str):
        self._apply_current_layer_change(
            "修改文字内容",
            lambda layer: setattr(layer, "text", text),
            merge_key="text_content",
        )

    def on_text_parameter_changed(self, is_parameter: bool):
        self._apply_current_layer_change(
            "切换文字参数",
            lambda layer: setattr(layer, "is_text_parameter", is_parameter),
        )

    def on_text_param_name_changed(self, name: str):
        self._apply_current_layer_change(
            "修改文字参数名",
            lambda layer: setattr(layer, "text_parameter_name", name),
            merge_key="text_param_name",
        )

    def on_font_path_changed(self, path: str):
        self._apply_current_layer_change(
            "修改字体路径",
            lambda layer: setattr(layer, "font_path", path),
            merge_key="font_path",
        )

    def on_font_parameter_changed(self, is_parameter: bool):
        self._apply_current_layer_change(
            "切换字体参数",
            lambda layer: setattr(layer, "is_font_parameter", is_parameter),
        )

    def on_font_param_name_changed(self, name: str):
        self._apply_current_layer_change(
            "修改字体参数名",
            lambda layer: setattr(layer, "font_parameter_name", name),
            merge_key="font_param_name",
        )

    def on_font_size_changed(self, size: int):
        self._apply_current_layer_change(
            "修改字体大小",
            lambda layer: setattr(layer, "font_size", size),
            merge_key="font_size",
        )

    def on_h_align_changed(self, text: str):
        align_map = {
            "左对齐": TextAlignment.LEFT,
            "居中": TextAlignment.CENTER,
            "右对齐": TextAlignment.RIGHT,
        }
        self._apply_current_layer_change(
            "修改水平对齐",
            lambda layer: setattr(
                layer, "horizontal_align", align_map.get(text, TextAlignment.LEFT)
            ),
        )

    def on_v_align_changed(self, text: str):
        align_map = {
            "顶部": TextAlignment.TOP,
            "居中": TextAlignment.MIDDLE,
            "底部": TextAlignment.BOTTOM,
        }
        self._apply_current_layer_change(
            "修改垂直对齐",
            lambda layer: setattr(
                layer, "vertical_align", align_map.get(text, TextAlignment.TOP)
            ),
        )

    def on_max_width_enabled_changed(self, enabled: bool):
        self._apply_current_layer_change(
            "切换宽度限制",
            lambda layer: setattr(
                layer,
                "max_width",
                self.max_width_spinbox.value() if enabled else None,
            ),
            merge_key="max_width",
        )

    def on_max_width_changed(self, value: int):
        self._apply_current_layer_change(
            "修改最大宽度",
            lambda layer: setattr(layer, "max_width", value),
            merge_key="max_width",
        )

    def on_truncate_suffix_changed(self, text: str):
        self._apply_current_layer_change(
            "修改截断后缀",
            lambda layer: setattr(layer, "truncate_suffix", text),
            merge_key="truncate_suffix",
        )

    def browse_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择图片",
            "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.tiff);;所有文件 (*)",
        )
        if file_path:
            self._apply_current_layer_change(
                "选择图片文件", lambda layer: setattr(layer, "image_path", file_path)
            )

    def browse_font(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择字体", "", "字体文件 (*.ttf *.otf);;所有文件 (*)"
        )
        if file_path:
            self._apply_current_layer_change(
                "选择字体文件", lambda layer: setattr(layer, "font_path", file_path)
            )

    def choose_color(self):
        if not isinstance(self.current_layer, TextLayer):
            return

        current_color = QColor(*self.current_layer.color)
        color = QColorDialog.getColor(current_color, self, "选择文字颜色")
        if color.isValid():
            self.update_color_button(color)
            rgba = (color.red(), color.green(), color.blue(), color.alpha())
            self._apply_current_layer_change(
                "修改文字颜色", lambda layer: setattr(layer, "color", rgba)
            )

    def update_color_button(self, color: QColor):
        self.color_btn.setStyleSheet(f"background-color: {color.name()};")
        self.color_label.setText(color.name())

    def on_layer_updated(self, layer: BaseLayer):
        if self.current_layer and layer.id == self.current_layer.id:
            self.current_layer = layer
            self.update_ui()

    def on_model_reset(self):
        self.commit_all_history_groups()
        if not self.current_layer:
            self.hide_all_groups()
            return
        self.set_current_layer(self.current_layer.id)

    def on_base_image_changed(self, _image_path: str):
        if isinstance(self.current_layer, BaseImageLayer):
            if self.project_model.base_image is None:
                self.current_layer = None
                self.hide_all_groups()
            else:
                self.current_layer = self.project_model.base_image
                self.update_ui()

    def on_base_image_path_changed(self, path: str):
        self._apply_current_layer_change(
            "修改底图路径",
            lambda layer: setattr(layer, "image_path", path),
            merge_key="base_image_path",
        )

    def on_base_image_parameter_changed(self, is_parameter: bool):
        self._apply_current_layer_change(
            "切换底图参数",
            lambda layer: setattr(layer, "is_path_parameter", is_parameter),
        )

    def on_base_image_param_name_changed(self, name: str):
        self._apply_current_layer_change(
            "修改底图参数名",
            lambda layer: setattr(layer, "parameter_name", name),
            merge_key="base_image_param_name",
        )

    def browse_base_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择底图",
            "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.tiff);;所有文件 (*)",
        )
        if file_path:
            self._apply_current_layer_change(
                "选择底图文件", lambda layer: setattr(layer, "image_path", file_path)
            )
