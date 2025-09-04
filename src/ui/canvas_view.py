"""
画布视图实现 - 使用QGraphicsView显示和编辑图层
"""
import os
from typing import Optional, Dict, Any

from PySide6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,
    QGraphicsTextItem, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QColor, QPen, QPainter, QFontDatabase

from ..core.models import ProjectModel, BaseLayer, ImageLayer, TextLayer, LayerType, TextAlignment


class LayerGraphicsItem(QGraphicsPixmapItem):
    """图层图形项基类"""
    
    def __init__(self, layer: BaseLayer, project_model: ProjectModel, parent=None):
        super().__init__(parent)
        self.layer = layer
        self.project_model = project_model
        self.setFlag(self.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(self.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(self.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        
    def itemChange(self, change, value):
        """处理项目变化"""
        if change == self.GraphicsItemChange.ItemPositionHasChanged:
            # 更新图层位置并通知模型
            pos = value
            self.layer.position.x = int(pos.x())
            self.layer.position.y = int(pos.y())
            # 通知模型图层已更新，这样属性面板会收到信号并更新UI
            self.project_model.update_layer(self.layer)
            
        return super().itemChange(change, value)


class ImageGraphicsItem(LayerGraphicsItem):
    """图片图形项"""
    
    def __init__(self, layer: ImageLayer, project_model: ProjectModel, parent=None):
        super().__init__(layer, project_model, parent)
        self.image_layer = layer
        self.update_pixmap()
        
    def update_pixmap(self):
        """更新显示的图片"""
        if not self.image_layer.image_path or not os.path.exists(self.image_layer.image_path):
            # 创建占位符
            pixmap = QPixmap(self.image_layer.size.width, self.image_layer.size.height)
            pixmap.fill(QColor(200, 200, 200, 100))
        else:
            try:
                # 加载并缩放图片
                pixmap = QPixmap(self.image_layer.image_path)
                pixmap = pixmap.scaled(
                    self.image_layer.size.width,
                    self.image_layer.size.height,
                    Qt.AspectRatioMode.IgnoreAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            except Exception:
                # 加载失败时使用占位符
                pixmap = QPixmap(self.image_layer.size.width, self.image_layer.size.height)
                pixmap.fill(QColor(255, 100, 100, 100))
                
        self.setPixmap(pixmap)
        self.setPos(self.image_layer.position.x, self.image_layer.position.y)
        
        # 设置透明度
        self.setOpacity(self.image_layer.opacity)
        
        # 设置旋转
        self.setRotation(self.image_layer.rotation)


class TextGraphicsItem(QGraphicsTextItem):
    """文字图形项"""
    
    # 类级别字体缓存，避免重复加载相同字体
    _font_cache: Dict[str, str] = {}  # font_path -> font_family_name
    
    def __init__(self, layer: TextLayer, project_model: ProjectModel, parent=None):
        super().__init__(parent)
        self.text_layer = layer
        self.project_model = project_model
        
        # 防止无限循环的标志
        self._updating_position = False
        self._dragging = False  # 是否正在拖动
        
        self.setFlag(self.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(self.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(self.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.update_text()
        
    def update_text(self):
        """更新显示的文字"""
        # 使用HTML来实现对齐，这是最可靠的方法
        html_text = self._create_html_text()
        self.setHtml(html_text)
        
        # 只有在不是在处理拖动位置更新时才应用对齐
        if not self._dragging:
            # 使用QTimer延迟应用垂直对齐，确保HTML布局完成
            from PySide6.QtCore import QTimer
            QTimer.singleShot(10, self._apply_vertical_alignment)
        
    def _apply_vertical_alignment(self):
        """应用对齐（延迟执行以确保HTML布局完成）"""
        # 如果正在更新位置，避免递归调用
        if self._updating_position:
            return
            
        # 设置更新标志
        self._updating_position = True
        
        try:
            # 从锚点位置计算实际显示位置
            anchor_x = self.text_layer.position.x
            anchor_y = self.text_layer.position.y
            
            # 获取文字尺寸
            text_rect = self.boundingRect()
            text_width = text_rect.width()
            text_height = text_rect.height()
            
            # 根据水平对齐计算显示X位置
            display_x = anchor_x
            if self.text_layer.horizontal_align == TextAlignment.CENTER:
                # 居中对齐：从锚点（中心）计算左边界
                display_x = anchor_x - text_width / 2
            elif self.text_layer.horizontal_align == TextAlignment.RIGHT:
                # 右对齐：从锚点（右边界）计算左边界
                display_x = anchor_x - text_width
            # 左对齐：锚点就是左边界，无需调整
            
            # 根据垂直对齐计算显示Y位置
            display_y = anchor_y
            if self.text_layer.vertical_align == TextAlignment.MIDDLE:
                # 居中对齐：从锚点（中心）计算顶边界
                display_y = anchor_y - text_height / 2
            elif self.text_layer.vertical_align == TextAlignment.BOTTOM:
                # 底部对齐：从锚点（底边界）计算顶边界
                display_y = anchor_y - text_height
            # 顶部对齐：锚点就是顶边界，无需调整
            
            # 设置最终显示位置
            self.setPos(display_x, display_y)
        finally:
            # 重置更新标志
            self._updating_position = False
        
    def _create_html_text(self):
        """创建带有样式的HTML文本"""
        # 获取字体信息
        font_family = "Arial"  # 默认字体
        if self.text_layer.font_path and os.path.exists(self.text_layer.font_path):
            # 检查字体缓存
            if self.text_layer.font_path in self._font_cache:
                font_family = self._font_cache[self.text_layer.font_path]
            else:
                # 加载自定义字体
                font_database = QFontDatabase()
                font_id = font_database.addApplicationFont(self.text_layer.font_path)
                if font_id != -1:
                    font_families = font_database.applicationFontFamilies(font_id)
                    if font_families:
                        font_family = font_families[0]
                        self._font_cache[self.text_layer.font_path] = font_family
                else:
                    print(f"警告: 无法加载字体文件 {self.text_layer.font_path}")
        
        # 获取颜色
        color = self.text_layer.color
        color_str = f"rgba({color[0]}, {color[1]}, {color[2]}, {color[3]/255})"
        
        # 获取对齐方式
        align_map = {
            TextAlignment.LEFT: "left",
            TextAlignment.CENTER: "center", 
            TextAlignment.RIGHT: "right"
        }
        text_align = align_map.get(self.text_layer.horizontal_align, "left")
        
        # 构建HTML（为对齐设置足够的宽度）
        html = f"""
        <div style="
            font-family: '{font_family}';
            font-size: {self.text_layer.font_size}px;
            color: {color_str};
            text-align: {text_align};
            width: 300px;
            white-space: nowrap;
        ">
            {self.text_layer.text}
        </div>
        """
        
        return html
        
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        self._dragging = True
        super().mousePressEvent(event)
        
    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        super().mouseReleaseEvent(event)
        # 延迟重置拖动状态，确保位置更新完成
        from PySide6.QtCore import QTimer
        QTimer.singleShot(100, lambda: setattr(self, '_dragging', False))
        
    def itemChange(self, change, value):
        """处理项目变化"""
        if change == self.GraphicsItemChange.ItemPositionHasChanged:
            # 如果正在更新位置，避免递归调用
            if self._updating_position:
                return super().itemChange(change, value)
                
            # 标记为拖动状态
            self._dragging = True
            
            try:
                # 计算锚点位置（根据对齐方式确定）
                pos = value
                current_x = int(pos.x())
                current_y = int(pos.y())
                
                # 获取文字尺寸
                text_rect = self.boundingRect()
                text_width = text_rect.width()
                text_height = text_rect.height()
                
                # 计算锚点位置
                anchor_x = current_x
                anchor_y = current_y
                
                # 根据水平对齐调整锚点X
                if self.text_layer.horizontal_align == TextAlignment.CENTER:
                    # 居中对齐：锚点为文字区域中心X
                    anchor_x = current_x + text_width / 2
                elif self.text_layer.horizontal_align == TextAlignment.RIGHT:
                    # 右对齐：锚点为文字区域右边界
                    anchor_x = current_x + text_width
                # 左对齐：锚点就是当前位置（文字区域左边界）
                
                # 根据垂直对齐调整锚点Y
                if self.text_layer.vertical_align == TextAlignment.MIDDLE:
                    # 居中对齐：锚点为文字区域中心Y
                    anchor_y = current_y + text_height / 2
                elif self.text_layer.vertical_align == TextAlignment.BOTTOM:
                    # 底部对齐：锚点为文字区域底边界
                    anchor_y = current_y + text_height
                # 顶部对齐：锚点就是当前位置（文字区域顶边界）
                
                # 更新图层的锚点位置
                self.text_layer.position.x = int(anchor_x)
                self.text_layer.position.y = int(anchor_y)
                
                # 通知模型图层已更新
                self.project_model.update_layer(self.text_layer)
            except Exception as e:
                print(f"拖动处理出错: {e}")
                self._dragging = False
            
        return super().itemChange(change, value)


class CanvasView(QGraphicsView):
    """画布视图"""
    
    # 信号定义
    layer_selected = Signal(str)  # layer_id
    
    def __init__(self, project_model: ProjectModel, parent=None):
        super().__init__(parent)
        
        self.project_model = project_model
        
        # 创建场景
        self.graphics_scene = QGraphicsScene(self)
        self.setScene(self.graphics_scene)
        
        # 设置视图属性
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setFrameStyle(QFrame.Shape.NoFrame)
        
        # 图形项缓存
        self.graphics_items: Dict[str, Any] = {}
        
        # 背景图形项
        self.base_image_item: Optional[QGraphicsPixmapItem] = None
        
        # 连接信号
        self.connect_signals()
        
        # 初始化场景
        self.init_scene()
        
    def init_scene(self):
        """初始化场景"""
        # 设置场景大小
        self.graphics_scene.setSceneRect(0, 0, 800, 600)
        
        # 添加背景网格
        self.add_background_grid()
        
    def add_background_grid(self):
        """添加背景网格"""
        pen = QPen(QColor(200, 200, 200, 50))
        pen.setWidth(1)
        
        # 绘制网格线
        grid_size = 20
        scene_rect = self.graphics_scene.sceneRect()
        
        # 垂直线
        x = 0
        while x <= scene_rect.width():
            line = self.graphics_scene.addLine(x, 0, x, scene_rect.height(), pen)
            line.setZValue(-1000)  # 确保在最底层
            x += grid_size
            
        # 水平线
        y = 0
        while y <= scene_rect.height():
            line = self.graphics_scene.addLine(0, y, scene_rect.width(), y, pen)
            line.setZValue(-1000)  # 确保在最底层
            y += grid_size
        
    def connect_signals(self):
        """连接信号槽"""
        self.project_model.base_image_changed.connect(self.update_base_image)
        self.project_model.layer_added.connect(self.add_layer_item)
        self.project_model.layer_removed.connect(self.remove_layer_item)
        self.project_model.layer_updated.connect(self.update_layer_item)
        
        # 场景选择变化
        self.graphics_scene.selectionChanged.connect(self.on_selection_changed)
        
    def update_base_image(self, image_path: str):
        """更新底图"""
        # 移除旧的底图
        if self.base_image_item:
            self.graphics_scene.removeItem(self.base_image_item)
            
        # 添加新的底图
        if image_path and os.path.exists(image_path):
            try:
                pixmap = QPixmap(image_path)
                self.base_image_item = self.graphics_scene.addPixmap(pixmap)
                if self.base_image_item:
                    self.base_image_item.setZValue(-100)  # 确保在背景
                
                # 更新场景大小
                self.graphics_scene.setSceneRect(pixmap.rect())
                
                # 适配视图
                self.fit_to_window()
                
            except Exception as e:
                print(f"加载底图失败: {e}")
                
    def add_layer_item(self, layer: BaseLayer):
        """添加图层图形项"""
        if layer.layer_type == LayerType.IMAGE and isinstance(layer, ImageLayer):
            item = ImageGraphicsItem(layer, self.project_model)
            self.graphics_scene.addItem(item)
            self.graphics_items[layer.id] = item
            
        elif layer.layer_type == LayerType.TEXT and isinstance(layer, TextLayer):
            item = TextGraphicsItem(layer, self.project_model)
            self.graphics_scene.addItem(item)
            self.graphics_items[layer.id] = item
            
    def remove_layer_item(self, layer_id: str):
        """移除图层图形项"""
        if layer_id in self.graphics_items:
            item = self.graphics_items[layer_id]
            self.graphics_scene.removeItem(item)
            del self.graphics_items[layer_id]
            
    def update_layer_item(self, layer: BaseLayer):
        """更新图层图形项"""
        if layer.id in self.graphics_items:
            item = self.graphics_items[layer.id]
            
            if isinstance(item, ImageGraphicsItem) and isinstance(layer, ImageLayer):
                item.image_layer = layer
                item.update_pixmap()
                
            elif isinstance(item, TextGraphicsItem) and isinstance(layer, TextLayer):
                item.text_layer = layer
                item.update_text()
                
    def on_selection_changed(self):
        """处理选择变化"""
        selected_items = self.graphics_scene.selectedItems()
        if selected_items:
            item = selected_items[0]
            if isinstance(item, LayerGraphicsItem) and hasattr(item, 'layer'):
                self.layer_selected.emit(item.layer.id)
            elif isinstance(item, TextGraphicsItem) and hasattr(item, 'text_layer'):
                self.layer_selected.emit(item.text_layer.id)
                
    def select_layer(self, layer_id: str):
        """选择指定图层"""
        if layer_id in self.graphics_items:
            # 清除当前选择
            self.graphics_scene.clearSelection()
            # 选择指定项
            item = self.graphics_items[layer_id]
            item.setSelected(True)
            
    def reset_view(self):
        """重置视图"""
        self.resetTransform()
        
    def fit_to_window(self):
        """适配窗口"""
        if self.base_image_item:
            self.fitInView(self.base_image_item.boundingRect(), Qt.AspectRatioMode.KeepAspectRatio)
        else:
            self.fitInView(self.graphics_scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
            
    def wheelEvent(self, event):
        """鼠标滚轮事件 - 缩放"""
        factor = 1.2 if event.angleDelta().y() > 0 else 1.0 / 1.2
        self.scale(factor, factor)
        
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.MouseButton.MiddleButton:
            # 中键拖拽
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        super().mousePressEvent(event)
        
    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if event.button() == Qt.MouseButton.MiddleButton:
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
        super().mouseReleaseEvent(event)
