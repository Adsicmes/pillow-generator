"""
数据模型定义
"""

import copy
from copy import deepcopy
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QColor, QFont
import uuid

from .history import HistoryManager, SnapshotCommand


class LayerType(Enum):
    """图层类型枚举"""

    BASE = "base"  # 底图
    IMAGE = "image"  # 图片层
    TEXT = "text"  # 文字层


class TextAlignment(Enum):
    """文字对齐方式"""

    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"
    TOP = "top"
    MIDDLE = "middle"
    BOTTOM = "bottom"


class TextOverflowMode(Enum):
    """文字超宽处理模式"""

    TRUNCATE = "truncate"  # 截断处理


@dataclass
class Position:
    """位置信息"""

    x: int = 0
    y: int = 0


@dataclass
class Size:
    """尺寸信息"""

    width: int = 100
    height: int = 100


@dataclass
class BaseLayer:
    """图层基类"""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    visible: bool = True
    locked: bool = False
    layer_type: LayerType = LayerType.BASE
    position: Position = field(default_factory=Position)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "visible": self.visible,
            "locked": self.locked,
            "layer_type": self.layer_type.value,
            "position": {"x": self.position.x, "y": self.position.y},
        }


@dataclass
class BaseImageLayer(BaseLayer):
    """基础图片层（底图）"""

    image_path: str = ""
    is_path_parameter: bool = False  # 是否作为参数传入
    parameter_name: str = "base_image_path"  # 参数名
    layer_type: LayerType = LayerType.BASE

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update(
            {
                "image_path": self.image_path,
                "is_path_parameter": self.is_path_parameter,
                "parameter_name": self.parameter_name,
            }
        )
        return data


@dataclass
class ImageLayer(BaseLayer):
    """图片层"""

    image_path: str = ""
    size: Size = field(default_factory=Size)
    rotation: float = 0.0
    opacity: float = 1.0
    is_path_parameter: bool = False  # 是否作为参数传入
    parameter_name: str = "image_path"
    layer_type: LayerType = LayerType.IMAGE

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update(
            {
                "image_path": self.image_path,
                "size": {"width": self.size.width, "height": self.size.height},
                "rotation": self.rotation,
                "opacity": self.opacity,
                "is_path_parameter": self.is_path_parameter,
                "parameter_name": self.parameter_name,
            }
        )
        return data


@dataclass
class TextLayer(BaseLayer):
    """文字层"""

    text: str = "示例文字"
    font_path: str = ""
    font_size: int = 24
    color: Tuple[int, int, int, int] = (0, 0, 0, 255)  # RGBA
    horizontal_align: TextAlignment = TextAlignment.LEFT
    vertical_align: TextAlignment = TextAlignment.TOP
    is_text_parameter: bool = False  # 是否作为参数传入
    text_parameter_name: str = "text"
    is_font_parameter: bool = False  # 字体是否作为参数传入
    font_parameter_name: str = "font_path"
    layer_type: LayerType = LayerType.TEXT

    # 文字单元宽度限制功能
    max_width: Optional[int] = None  # 最大宽度限制（像素）
    overflow_mode: TextOverflowMode = TextOverflowMode.TRUNCATE  # 超宽处理模式
    truncate_suffix: str = "..."  # 截断后缀

    def __init__(
        self,
        name: str = "文字层",
        text: str = "",
        font_path: str = "",
        font_size: int = 24,
        color: str = "#000000",
        h_align: TextAlignment = TextAlignment.LEFT,
        v_align: TextAlignment = TextAlignment.TOP,
        max_width: Optional[int] = None,
        overflow_mode: Optional[TextOverflowMode] = None,
        truncate_suffix: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(name=name, layer_type=LayerType.TEXT, **kwargs)
        self.text = text
        self.font_path = font_path
        self.font_size = font_size
        # 处理颜色格式转换
        if isinstance(color, str):
            # 从十六进制转换为RGBA
            color = color.lstrip("#")
            r = int(color[0:2], 16)
            g = int(color[2:4], 16)
            b = int(color[4:6], 16)
            a = 255 if len(color) == 6 else int(color[6:8], 16)
            self.color = (r, g, b, a)
        else:
            self.color = color
        self.horizontal_align = h_align
        self.vertical_align = v_align
        self.max_width = max_width
        self.overflow_mode = overflow_mode or TextOverflowMode.TRUNCATE
        self.truncate_suffix = truncate_suffix or "..."

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update(
            {
                "text": self.text,
                "font_path": self.font_path,
                "font_size": self.font_size,
                "color": self.color,
                "horizontal_align": self.horizontal_align.value,
                "vertical_align": self.vertical_align.value,
                "is_text_parameter": self.is_text_parameter,
                "text_parameter_name": self.text_parameter_name,
                "is_font_parameter": self.is_font_parameter,
                "font_parameter_name": self.font_parameter_name,
                "max_width": self.max_width,
                "overflow_mode": self.overflow_mode.value,
                "truncate_suffix": self.truncate_suffix,
            }
        )
        return data


class ProjectModel(QObject):
    """项目数据模型"""

    # 信号定义
    layer_added = Signal(BaseLayer)
    layer_removed = Signal(str)  # layer_id
    layer_updated = Signal(BaseLayer)
    base_image_changed = Signal(str)  # image_path
    layer_order_changed = Signal()
    model_reset = Signal()
    history_changed = Signal(bool, bool)
    pending_history_commit_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._layers: List[BaseLayer] = []
        self._base_image: Optional[BaseImageLayer] = None
        self._project_name = "未命名项目"
        self._function_name = "generate_image"
        self._history_manager = HistoryManager()

    def _emit_history_state(self):
        self.history_changed.emit(
            self._history_manager.can_undo,
            self._history_manager.can_redo,
        )

    def capture_snapshot(self) -> Dict[str, Any]:
        return deepcopy(self.to_dict())

    def _restore_snapshot(self, snapshot: Dict[str, Any]):
        self._project_name = snapshot.get("project_name", "未命名项目")
        self._function_name = snapshot.get("function_name", "generate_image")
        base_image_data = snapshot.get("base_image")
        self._base_image = self._create_base_image_from_dict(base_image_data)
        self._layers = []
        for layer_data in snapshot.get("layers", []):
            layer = self._create_layer_from_dict(layer_data)
            if layer is not None:
                self._layers.append(layer)

        self.model_reset.emit()
        self.base_image_changed.emit(
            self._base_image.image_path if self._base_image else ""
        )
        self.layer_order_changed.emit()
        for layer in self._layers:
            self.layer_updated.emit(layer)

    def record_manual_change(
        self, before_snapshot: Dict[str, Any], description: str
    ) -> bool:
        after_snapshot = self.capture_snapshot()
        if after_snapshot == before_snapshot:
            return False

        self._history_manager.push(
            SnapshotCommand(
                description=description,
                before=before_snapshot,
                after=after_snapshot,
            )
        )
        self._emit_history_state()
        return True

    def apply_operation(self, description: str, operation) -> bool:
        before_snapshot = self.capture_snapshot()
        operation()
        return self.record_manual_change(before_snapshot, description)

    def undo(self) -> bool:
        self.pending_history_commit_requested.emit()
        command = self._history_manager.pop_undo()
        if command is None:
            return False

        self._history_manager.push_redo(command)
        self._restore_snapshot(command.before)
        self._emit_history_state()
        return True

    def redo(self) -> bool:
        self.pending_history_commit_requested.emit()
        command = self._history_manager.pop_redo()
        if command is None:
            return False

        self._history_manager.push(command)
        self._restore_snapshot(command.after)
        self._emit_history_state()
        return True

    def reset_history(self):
        self._history_manager.clear()
        self._emit_history_state()

    @property
    def can_undo(self) -> bool:
        return self._history_manager.can_undo

    @property
    def can_redo(self) -> bool:
        return self._history_manager.can_redo

    @property
    def project_name(self) -> str:
        return self._project_name

    @project_name.setter
    def project_name(self, name: str):
        self._project_name = name

    @property
    def function_name(self) -> str:
        return self._function_name

    @function_name.setter
    def function_name(self, name: str):
        self._function_name = name

    @property
    def base_image(self) -> Optional[BaseImageLayer]:
        return self._base_image

    def set_base_image(
        self,
        image_path: str,
        name: str = "底图",
        is_parameter: bool = False,
        parameter_name: str = "base_image_path",
    ):
        """设置底图"""
        self._base_image = BaseImageLayer(
            name=name,
            image_path=image_path,
            is_path_parameter=is_parameter,
            parameter_name=parameter_name,
        )
        self.base_image_changed.emit(image_path)

    def replace_base_image(self, base_image: BaseImageLayer | None):
        self._base_image = base_image
        self.base_image_changed.emit(base_image.image_path if base_image else "")

    def clear_base_image(self):
        self.replace_base_image(None)

    def replace_layer(self, layer: BaseLayer):
        for i, current_layer in enumerate(self._layers):
            if current_layer.id == layer.id:
                self._layers[i] = layer
                self.layer_updated.emit(layer)
                return

    def add_layer(self, layer: BaseLayer):
        """添加图层"""
        self._layers.append(layer)
        self.layer_added.emit(layer)
        self.layer_order_changed.emit()

    def remove_layer(self, layer_id: str):
        """移除图层"""
        self._layers = [l for l in self._layers if l.id != layer_id]
        self.layer_removed.emit(layer_id)
        self.layer_order_changed.emit()

    def duplicate_layer(self, layer_id: str) -> Optional[BaseLayer]:
        layer = self.get_layer(layer_id)
        if not layer:
            return None

        duplicated_layer = copy.deepcopy(layer)
        duplicated_layer.id = str(uuid.uuid4())
        duplicated_layer.name = f"{layer.name} 副本"
        duplicated_layer.position.x += 20
        duplicated_layer.position.y += 20
        self.add_layer(duplicated_layer)
        return duplicated_layer

    def get_layer(self, layer_id: str) -> Optional[BaseLayer]:
        """获取图层"""
        for layer in self._layers:
            if layer.id == layer_id:
                return layer
        return None

    def update_layer(self, layer: BaseLayer):
        """更新图层"""
        self.replace_layer(layer)

    def get_layers_by_type(self, layer_type: LayerType) -> List[BaseLayer]:
        """按类型获取图层"""
        return [l for l in self._layers if l.layer_type == layer_type]

    def get_all_layers(self) -> List[BaseLayer]:
        """获取所有图层"""
        return self._layers.copy()

    def clear_layers(self):
        """清空所有图层"""
        self._layers.clear()
        self.layer_order_changed.emit()

    def move_layer(self, layer_id: str, new_index: int):
        """移动图层位置（影响z-index）"""
        layer = None
        old_index = -1

        for i, l in enumerate(self._layers):
            if l.id == layer_id:
                layer = l
                old_index = i
                break

        if layer and 0 <= new_index < len(self._layers):
            self._layers.pop(old_index)
            self._layers.insert(new_index, layer)
            self.layer_order_changed.emit()

    def to_dict(self) -> Dict[str, Any]:
        """导出为字典"""
        return {
            "project_name": self._project_name,
            "function_name": self._function_name,
            "base_image": self._base_image.to_dict() if self._base_image else None,
            "layers": [layer.to_dict() for layer in self._layers],
        }

    def _create_base_image_from_dict(
        self, base_image_data: Dict[str, Any] | None
    ) -> Optional[BaseImageLayer]:
        if not base_image_data:
            return None

        return BaseImageLayer(
            id=base_image_data.get("id", str(uuid.uuid4())),
            name=base_image_data.get("name", "底图"),
            visible=base_image_data.get("visible", True),
            locked=base_image_data.get("locked", False),
            position=Position(
                base_image_data.get("position", {}).get("x", 0),
                base_image_data.get("position", {}).get("y", 0),
            ),
            image_path=base_image_data.get("image_path", ""),
            is_path_parameter=base_image_data.get("is_path_parameter", False),
            parameter_name=base_image_data.get("parameter_name", "base_image_path"),
        )

    def _create_layer_from_dict(
        self, layer_data: Dict[str, Any]
    ) -> Optional[BaseLayer]:
        layer_type = LayerType(layer_data["layer_type"])
        layer_id = str(layer_data.get("id", str(uuid.uuid4())))
        layer_name = str(layer_data.get("name", ""))
        layer_visible = bool(layer_data.get("visible", True))
        layer_locked = bool(layer_data.get("locked", False))
        layer_position = Position(
            int(layer_data.get("position", {}).get("x", 0)),
            int(layer_data.get("position", {}).get("y", 0)),
        )

        if layer_type == LayerType.IMAGE:
            layer = ImageLayer(
                id=layer_id,
                name=layer_name,
                visible=layer_visible,
                locked=layer_locked,
                position=layer_position,
            )
            layer.image_path = layer_data.get("image_path", "")
            layer.size = Size(
                layer_data.get("size", {}).get("width", 100),
                layer_data.get("size", {}).get("height", 100),
            )
            layer.rotation = layer_data.get("rotation", 0.0)
            layer.opacity = layer_data.get("opacity", 1.0)
            layer.is_path_parameter = layer_data.get("is_path_parameter", False)
            layer.parameter_name = layer_data.get("parameter_name", "image_path")
            return layer

        if layer_type == LayerType.TEXT:
            layer = TextLayer(
                id=layer_id,
                name=layer_name,
                visible=layer_visible,
                locked=layer_locked,
                position=layer_position,
            )
            layer.text = layer_data.get("text", "示例文字")
            layer.font_path = layer_data.get("font_path", "")
            layer.font_size = layer_data.get("font_size", 24)
            layer.color = tuple(layer_data.get("color", [0, 0, 0, 255]))
            layer.horizontal_align = TextAlignment(
                layer_data.get("horizontal_align", TextAlignment.LEFT.value)
            )
            layer.vertical_align = TextAlignment(
                layer_data.get("vertical_align", TextAlignment.TOP.value)
            )
            layer.is_text_parameter = layer_data.get("is_text_parameter", False)
            layer.text_parameter_name = layer_data.get("text_parameter_name", "text")
            layer.is_font_parameter = layer_data.get("is_font_parameter", False)
            layer.font_parameter_name = layer_data.get(
                "font_parameter_name", "font_path"
            )
            layer.max_width = layer_data.get("max_width")
            layer.overflow_mode = TextOverflowMode(
                layer_data.get("overflow_mode", TextOverflowMode.TRUNCATE.value)
            )
            layer.truncate_suffix = layer_data.get("truncate_suffix", "...")
            return layer

        return None
