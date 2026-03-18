"""
数据模型定义
"""

import copy
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QColor, QFont
import uuid


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
    layer_type: LayerType = LayerType.BASE
    position: Position = field(default_factory=Position)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "visible": self.visible,
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

    def __init__(self, parent=None):
        super().__init__(parent)
        self._layers: List[BaseLayer] = []
        self._base_image: Optional[BaseImageLayer] = None
        self._project_name = "未命名项目"
        self._function_name = "generate_image"

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
        for i, l in enumerate(self._layers):
            if l.id == layer.id:
                self._layers[i] = layer
                self.layer_updated.emit(layer)
                break

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
