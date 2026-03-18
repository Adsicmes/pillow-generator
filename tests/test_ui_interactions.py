import os
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from typing import cast

from src.core.models import Position, ProjectModel, TextLayer
from src.ui.canvas_view import CanvasView
from src.ui.code_generator import CodeGenerator
from src.ui.layer_panel import LayerPanel
from src.ui.property_panel import PropertyPanel


def get_qapplication() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return cast(QApplication, app)


def test_layer_panel_duplicate_and_canvas_selection_sync():
    get_qapplication()

    project = ProjectModel()
    layer_panel = LayerPanel(project)
    canvas_view = CanvasView(project)

    canvas_view.layer_selected.connect(layer_panel.select_layer)
    layer_panel.layer_selected.connect(canvas_view.select_layer)

    original_layer = TextLayer(name="标题", text="Hello", position=Position(10, 20))
    project.add_layer(original_layer)

    layer_panel.duplicate_layer(original_layer.id)

    all_layers = project.get_all_layers()
    assert len(all_layers) == 2

    duplicated_layer = all_layers[-1]
    assert duplicated_layer.id != original_layer.id
    assert duplicated_layer.name == "标题 副本"
    assert duplicated_layer.position.x == 30
    assert duplicated_layer.position.y == 40

    canvas_view.select_layer(duplicated_layer.id)

    assert layer_panel.current_layer_id == duplicated_layer.id
    assert layer_panel.layer_list.currentItem() is not None
    assert layer_panel.layer_list.currentItem().data(0x0100) == duplicated_layer.id


def test_base_image_actions_and_layer_order_refresh():
    get_qapplication()

    project = ProjectModel()
    layer_panel = LayerPanel(project)
    canvas_view = CanvasView(project)

    project.set_base_image("base.png", "底图")
    first_layer = TextLayer(name="第一层", text="A")
    second_layer = TextLayer(name="第二层", text="B")
    project.add_layer(first_layer)
    project.add_layer(second_layer)

    base_image = project.base_image
    assert base_image is not None

    layer_panel.select_layer(base_image.id)
    assert layer_panel.delete_btn.isEnabled()
    assert not layer_panel.move_up_btn.isEnabled()
    assert not layer_panel.move_down_btn.isEnabled()

    layer_panel.delete_selected_layer()
    assert project.base_image is None

    project.move_layer(first_layer.id, 1)
    first_item = canvas_view.graphics_items[first_layer.id]
    second_item = canvas_view.graphics_items[second_layer.id]
    assert first_item.zValue() > second_item.zValue()

    layer_panel.on_layer_visibility_changed(first_layer.id, False)
    updated_layer = project.get_layer(first_layer.id)
    assert updated_layer is not None
    assert not updated_layer.visible


def test_code_generator_supports_blank_canvas_output():
    get_qapplication()

    project = ProjectModel()
    generator = CodeGenerator(project)

    generator.generate_code()

    generated_code = generator.code_text.toPlainText()
    assert 'Image.new("RGBA", (800, 600), (255, 255, 255, 255))' in generated_code


def test_locked_layer_disables_canvas_and_panel_actions():
    get_qapplication()

    project = ProjectModel()
    layer_panel = LayerPanel(project)
    canvas_view = CanvasView(project)
    property_panel = PropertyPanel(project)

    canvas_view.layer_selected.connect(layer_panel.select_layer)
    layer_panel.layer_selected.connect(canvas_view.select_layer)
    layer_panel.layer_selected.connect(property_panel.set_current_layer)

    layer = TextLayer(name="锁定层", text="Lock me")
    project.add_layer(layer)

    property_panel.set_current_layer(layer.id)
    property_panel.locked_checkbox.setChecked(True)

    updated_layer = project.get_layer(layer.id)
    assert updated_layer is not None
    assert updated_layer.locked is True

    layer_panel.select_layer(layer.id)
    assert not layer_panel.delete_btn.isEnabled()
    assert not layer_panel.move_up_btn.isEnabled()
    assert not layer_panel.move_down_btn.isEnabled()

    canvas_item = canvas_view.graphics_items[layer.id]
    assert not bool(canvas_item.flags() & canvas_item.GraphicsItemFlag.ItemIsMovable)
    assert not property_panel.name_edit.isEnabled()
    assert property_panel.locked_checkbox.isEnabled()


def test_text_edit_history_is_coalesced_into_single_undo():
    app = get_qapplication()

    project = ProjectModel()
    property_panel = PropertyPanel(project)
    layer = TextLayer(name="标题", text="A")
    project.add_layer(layer)

    property_panel.set_current_layer(layer.id)
    property_panel.text_edit.setText("AB")
    property_panel.text_edit.setText("ABC")
    property_panel.text_edit.editingFinished.emit()
    app.processEvents()

    updated_layer = project.get_layer(layer.id)
    assert updated_layer is not None
    assert isinstance(updated_layer, TextLayer)
    assert updated_layer.text == "ABC"

    assert project.undo() is True
    reverted_layer = project.get_layer(layer.id)
    assert reverted_layer is not None
    assert isinstance(reverted_layer, TextLayer)
    assert reverted_layer.text == "A"
    assert project.can_undo is False


def test_slider_history_is_coalesced_into_single_undo():
    app = get_qapplication()

    project = ProjectModel()
    property_panel = PropertyPanel(project)
    layer = TextLayer(name="标题", text="A")
    project.add_layer(layer)

    property_panel.set_current_layer(layer.id)
    property_panel.font_size_spinbox.setValue(30)
    property_panel.font_size_spinbox.setValue(36)
    property_panel.font_size_spinbox.editingFinished.emit()
    app.processEvents()

    updated_layer = project.get_layer(layer.id)
    assert updated_layer is not None
    assert isinstance(updated_layer, TextLayer)
    assert updated_layer.font_size == 36

    assert project.undo() is True
    reverted_layer = project.get_layer(layer.id)
    assert reverted_layer is not None
    assert isinstance(reverted_layer, TextLayer)
    assert reverted_layer.font_size == 24
    assert project.can_undo is False


def test_undo_flushes_pending_history_group():
    app = get_qapplication()

    project = ProjectModel()
    property_panel = PropertyPanel(project)
    layer = TextLayer(name="标题", text="A")
    project.add_layer(layer)

    property_panel.set_current_layer(layer.id)
    property_panel.text_edit.setText("AB")
    app.processEvents()

    assert project.undo() is True
    reverted_layer = project.get_layer(layer.id)
    assert reverted_layer is not None
    assert isinstance(reverted_layer, TextLayer)
    assert reverted_layer.text == "A"


def test_switching_selected_layer_flushes_pending_history_group():
    app = get_qapplication()

    project = ProjectModel()
    property_panel = PropertyPanel(project)
    first_layer = TextLayer(name="一", text="A")
    second_layer = TextLayer(name="二", text="B")
    project.add_layer(first_layer)
    project.add_layer(second_layer)

    property_panel.set_current_layer(first_layer.id)
    property_panel.text_edit.setText("ABC")
    property_panel.set_current_layer(second_layer.id)
    app.processEvents()

    assert project.undo() is True
    reverted_layer = project.get_layer(first_layer.id)
    assert reverted_layer is not None
    assert isinstance(reverted_layer, TextLayer)
    assert reverted_layer.text == "A"


def test_timer_commits_pending_history_group():
    app = get_qapplication()

    project = ProjectModel()
    property_panel = PropertyPanel(project)
    layer = TextLayer(name="标题", text="A")
    project.add_layer(layer)

    property_panel.set_current_layer(layer.id)
    property_panel.text_edit.setText("AB")

    timeout_result = []
    property_panel.begin_history_group("timer_probe", "定时提交探针")
    property_panel.commit_history_group("timer_probe")

    from PySide6.QtCore import QTimer

    QTimer.singleShot(450, lambda: timeout_result.append(project.can_undo))
    deadline = time.time() + 1.0
    while not timeout_result and time.time() < deadline:
        app.processEvents()

    assert timeout_result == [True]
    assert project.undo() is True
    reverted_layer = project.get_layer(layer.id)
    assert reverted_layer is not None
    assert isinstance(reverted_layer, TextLayer)
    assert reverted_layer.text == "A"
