"""
项目文件管理器
处理项目的保存和加载
"""
import json
import os
from typing import Dict, Any, Optional
from pathlib import Path

from .models import (
    ProjectModel, BaseImageLayer, ImageLayer, TextLayer, 
    LayerType, TextAlignment, Position, Size
)


class ProjectManager:
    """项目文件管理器"""
    
    def __init__(self):
        self.current_file_path: Optional[str] = None
        
    def save_project(self, project_model: ProjectModel, file_path: str) -> bool:
        """保存项目到文件"""
        try:
            # 获取项目数据
            project_data = {
                'version': '1.0.0',
                'project_name': project_model.project_name,
                'base_image': None,
                'layers': []
            }
            
            # 保存底图信息
            if project_model.base_image:
                # 转换为相对路径
                base_path = os.path.dirname(file_path)
                relative_path = self.get_relative_path(project_model.base_image.image_path, base_path)
                
                project_data['base_image'] = {
                    'id': project_model.base_image.id,
                    'name': project_model.base_image.name,
                    'image_path': relative_path,
                    'layer_type': project_model.base_image.layer_type.value
                }
            
            # 保存图层信息
            for layer in project_model.get_all_layers():
                layer_data = layer.to_dict()
                
                # 如果是图片层，转换图片路径为相对路径
                if isinstance(layer, ImageLayer) and layer.image_path:
                    base_path = os.path.dirname(file_path)
                    layer_data['image_path'] = self.get_relative_path(layer.image_path, base_path)
                
                # 如果是文字层，转换字体路径为相对路径
                if isinstance(layer, TextLayer) and layer.font_path:
                    base_path = os.path.dirname(file_path)
                    layer_data['font_path'] = self.get_relative_path(layer.font_path, base_path)
                
                project_data['layers'].append(layer_data)
            
            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, indent=2, ensure_ascii=False)
                
            self.current_file_path = file_path
            return True
            
        except Exception as e:
            print(f"保存项目失败: {e}")
            return False
            
    def load_project(self, project_model: ProjectModel, file_path: str) -> bool:
        """从文件加载项目"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                project_data = json.load(f)
                
            # 清空当前项目
            project_model.clear_layers()
            project_model._base_image = None
            
            # 设置项目名称
            project_model.project_name = project_data.get('project_name', '未命名项目')
            
            # 加载底图
            if project_data.get('base_image'):
                base_data = project_data['base_image']
                base_path = os.path.dirname(file_path)
                absolute_path = self.get_absolute_path(base_data['image_path'], base_path)
                
                project_model.set_base_image(absolute_path, base_data['name'])
                
            # 加载图层
            for layer_data in project_data.get('layers', []):
                layer = self.create_layer_from_data(layer_data, file_path)
                if layer:
                    project_model.add_layer(layer)
                    
            self.current_file_path = file_path
            return True
            
        except Exception as e:
            print(f"加载项目失败: {e}")
            return False
            
    def create_layer_from_data(self, layer_data: Dict[str, Any], project_file_path: str):
        """从数据创建图层对象"""
        layer_type = LayerType(layer_data['layer_type'])
        base_path = os.path.dirname(project_file_path)
        
        if layer_type == LayerType.IMAGE:
            # 创建图片层
            layer = ImageLayer(
                id=layer_data['id'],
                name=layer_data['name'],
                visible=layer_data['visible'],
                position=Position(
                    layer_data['position']['x'],
                    layer_data['position']['y']
                )
            )
            
            # 设置图片路径
            if layer_data.get('image_path'):
                layer.image_path = self.get_absolute_path(layer_data['image_path'], base_path)
            
            # 设置其他属性
            if 'size' in layer_data:
                layer.size = Size(
                    layer_data['size']['width'],
                    layer_data['size']['height']
                )
            
            layer.rotation = layer_data.get('rotation', 0.0)
            layer.opacity = layer_data.get('opacity', 1.0)
            layer.is_path_parameter = layer_data.get('is_path_parameter', False)
            layer.parameter_name = layer_data.get('parameter_name', 'image_path')
            
            return layer
            
        elif layer_type == LayerType.TEXT:
            # 创建文字层
            layer = TextLayer(
                id=layer_data['id'],
                name=layer_data['name'],
                visible=layer_data['visible'],
                position=Position(
                    layer_data['position']['x'],
                    layer_data['position']['y']
                )
            )
            
            # 设置文字属性
            layer.text = layer_data.get('text', '示例文字')
            layer.font_size = layer_data.get('font_size', 24)
            layer.color = tuple(layer_data.get('color', [0, 0, 0, 255]))
            
            # 设置字体路径
            if layer_data.get('font_path'):
                layer.font_path = self.get_absolute_path(layer_data['font_path'], base_path)
            
            # 设置对齐
            h_align_str = layer_data.get('horizontal_align', 'left')
            layer.horizontal_align = TextAlignment(h_align_str)
            
            v_align_str = layer_data.get('vertical_align', 'top')
            layer.vertical_align = TextAlignment(v_align_str)
            
            # 设置参数选项
            layer.is_text_parameter = layer_data.get('is_text_parameter', False)
            layer.text_parameter_name = layer_data.get('text_parameter_name', 'text')
            layer.is_font_parameter = layer_data.get('is_font_parameter', False)
            layer.font_parameter_name = layer_data.get('font_parameter_name', 'font_path')
            
            return layer
            
        return None
        
    def get_relative_path(self, file_path: str, base_path: str) -> str:
        """获取相对路径"""
        try:
            return os.path.relpath(file_path, base_path)
        except ValueError:
            # 不同驱动器，返回绝对路径
            return file_path
            
    def get_absolute_path(self, relative_path: str, base_path: str) -> str:
        """获取绝对路径"""
        if os.path.isabs(relative_path):
            return relative_path
        else:
            return os.path.abspath(os.path.join(base_path, relative_path))
            
    def is_project_modified(self, project_model: ProjectModel) -> bool:
        """检查项目是否有修改"""
        # TODO: 实现项目修改检测逻辑
        return False
        
    @property
    def current_file(self) -> Optional[str]:
        """当前文件路径"""
        return self.current_file_path
        
    def set_current_file(self, file_path: Optional[str]):
        """设置当前文件路径"""
        self.current_file_path = file_path
