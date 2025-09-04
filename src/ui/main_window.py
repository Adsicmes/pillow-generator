"""
主窗口实现
"""
import os
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QSplitter, QMenuBar, QMenu, QToolBar, QStatusBar,
    QFileDialog, QMessageBox, QDockWidget, QApplication,
    QDialog, QDialogButtonBox, QFormLayout, QCheckBox, QLineEdit
)
from PySide6.QtCore import Qt, QSettings, Signal
from PySide6.QtGui import QAction, QIcon, QKeySequence

from ..core.models import ProjectModel
from ..core.project_manager import ProjectManager
from .canvas_view import CanvasView
from .layer_panel import LayerPanel
from .property_panel import PropertyPanel
from .code_generator import CodeGenerator


class BaseImageDialog(QDialog):
    """底图设置对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("底图设置")
        self.setModal(True)
        self.resize(400, 200)
        
        layout = QVBoxLayout(self)
        
        # 表单布局
        form_layout = QFormLayout()
        layout.addLayout(form_layout)
        
        # 作为参数选项
        self.parameter_checkbox = QCheckBox()
        self.parameter_checkbox.setChecked(False)
        self.parameter_checkbox.toggled.connect(self.on_parameter_toggled)
        form_layout.addRow("作为函数参数:", self.parameter_checkbox)
        
        # 参数名输入
        self.parameter_name_edit = QLineEdit("base_image_path")
        self.parameter_name_edit.setEnabled(False)
        form_layout.addRow("参数名:", self.parameter_name_edit)
        
        # 按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
    def on_parameter_toggled(self, checked: bool):
        """参数选项切换"""
        self.parameter_name_edit.setEnabled(checked)
        if not checked:
            self.parameter_name_edit.setText("base_image_path")
            
    def get_parameter_settings(self):
        """获取参数设置"""
        return {
            'is_parameter': self.parameter_checkbox.isChecked(),
            'parameter_name': self.parameter_name_edit.text() or "base_image_path"
        }


class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 初始化数据模型
        self.project_model = ProjectModel(self)
        
        # 初始化项目管理器
        self.project_manager = ProjectManager()
        
        # 初始化设置
        self.settings = QSettings("PillowGenerator", "PillowGenerator")
        
        # 设置窗口属性
        self.setWindowTitle("Pillow 代码生成器")
        self.setMinimumSize(1200, 800)
        
        # 恢复窗口状态
        self.restore_window_state()
        
        # 初始化UI
        self.init_ui()
        
        # 连接信号槽
        self.connect_signals()
        
    def init_ui(self):
        """初始化用户界面"""
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建工具栏
        self.create_toolbar()
        
        # 创建状态栏
        self.create_status_bar()
        
        # 创建停靠窗口
        self.create_dock_widgets()
        
        # 创建中央组件
        self.create_central_widget()
        
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")
        
        # 新建项目
        new_action = QAction("新建项目(&N)", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.setStatusTip("创建新的Pillow模板项目")
        new_action.triggered.connect(self.new_project)
        file_menu.addAction(new_action)
        
        # 打开项目
        open_action = QAction("打开项目(&O)", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.setStatusTip("打开现有的项目文件")
        open_action.triggered.connect(self.open_project)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        # 保存项目
        save_action = QAction("保存项目(&S)", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.setStatusTip("保存当前项目")
        save_action.triggered.connect(self.save_project)
        file_menu.addAction(save_action)
        
        # 另存为
        save_as_action = QAction("另存为(&A)", self)
        save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        save_as_action.setStatusTip("将项目保存到指定位置")
        save_as_action.triggered.connect(self.save_project_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        # 设置底图
        base_image_action = QAction("设置底图(&B)", self)
        base_image_action.setStatusTip("选择模板的底图")
        base_image_action.triggered.connect(self.set_base_image)
        file_menu.addAction(base_image_action)
        
        file_menu.addSeparator()
        
        # 退出
        exit_action = QAction("退出(&X)", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.setStatusTip("退出应用程序")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 编辑菜单
        edit_menu = menubar.addMenu("编辑(&E)")
        
        # 添加图片层
        add_image_action = QAction("添加图片层(&I)", self)
        add_image_action.setStatusTip("添加一个新的图片层")
        add_image_action.triggered.connect(self.add_image_layer)
        edit_menu.addAction(add_image_action)
        
        # 添加文字层
        add_text_action = QAction("添加文字层(&T)", self)
        add_text_action.setStatusTip("添加一个新的文字层")
        add_text_action.triggered.connect(self.add_text_layer)
        edit_menu.addAction(add_text_action)
        
        # 代码菜单
        code_menu = menubar.addMenu("代码(&C)")
        
        # 生成代码
        generate_action = QAction("生成Pillow代码(&G)", self)
        generate_action.setStatusTip("生成可调用的Pillow代码")
        generate_action.triggered.connect(self.generate_code)
        code_menu.addAction(generate_action)
        
        # 预览结果
        preview_action = QAction("预览结果(&P)", self)
        preview_action.setStatusTip("预览生成的图片效果")
        preview_action.triggered.connect(self.preview_result)
        code_menu.addAction(preview_action)
        
        # 视图菜单
        view_menu = menubar.addMenu("视图(&V)")
        
        # 重置视图
        reset_view_action = QAction("重置视图(&R)", self)
        reset_view_action.setStatusTip("重置画布视图到默认状态")
        reset_view_action.triggered.connect(self.reset_view)
        view_menu.addAction(reset_view_action)
        
        # 适配窗口
        fit_window_action = QAction("适配窗口(&F)", self)
        fit_window_action.setStatusTip("将画布内容适配到窗口大小")
        fit_window_action.triggered.connect(self.fit_to_window)
        view_menu.addAction(fit_window_action)
        
    def create_toolbar(self):
        """创建工具栏"""
        toolbar = self.addToolBar("主工具栏")
        toolbar.setObjectName("MainToolBar")
        
        # 新建按钮
        new_action = QAction("新建", self)
        new_action.setStatusTip("创建新项目")
        new_action.triggered.connect(self.new_project)
        toolbar.addAction(new_action)
        
        # 打开按钮
        open_action = QAction("打开", self)
        open_action.setStatusTip("打开项目")
        open_action.triggered.connect(self.open_project)
        toolbar.addAction(open_action)
        
        # 保存按钮
        save_action = QAction("保存", self)
        save_action.setStatusTip("保存项目")
        save_action.triggered.connect(self.save_project)
        toolbar.addAction(save_action)
        
        toolbar.addSeparator()
        
        # 设置底图按钮
        base_image_action = QAction("设置底图", self)
        base_image_action.triggered.connect(self.set_base_image)
        toolbar.addAction(base_image_action)
        
        # 添加图片层按钮
        add_image_action = QAction("添加图片", self)
        add_image_action.triggered.connect(self.add_image_layer)
        toolbar.addAction(add_image_action)
        
        # 添加文字层按钮
        add_text_action = QAction("添加文字", self)
        add_text_action.triggered.connect(self.add_text_layer)
        toolbar.addAction(add_text_action)
        
        toolbar.addSeparator()
        
        # 生成代码按钮
        generate_action = QAction("生成代码", self)
        generate_action.triggered.connect(self.generate_code)
        toolbar.addAction(generate_action)
        
        # 预览按钮
        preview_action = QAction("预览", self)
        preview_action.triggered.connect(self.preview_result)
        toolbar.addAction(preview_action)
        
    def create_status_bar(self):
        """创建状态栏"""
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("准备就绪")
        
    def create_dock_widgets(self):
        """创建停靠窗口"""
        # 图层面板
        self.layer_dock = QDockWidget("图层", self)
        self.layer_dock.setObjectName("LayerDock")  # 设置对象名以避免警告
        self.layer_panel = LayerPanel(self.project_model, self)
        self.layer_dock.setWidget(self.layer_panel)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.layer_dock)
        
        # 属性面板
        self.property_dock = QDockWidget("属性", self)
        self.property_dock.setObjectName("PropertyDock")  # 设置对象名以避免警告
        self.property_panel = PropertyPanel(self.project_model, self)
        self.property_dock.setWidget(self.property_panel)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.property_dock)
        
        # 代码生成器面板
        self.code_dock = QDockWidget("代码生成器", self)
        self.code_dock.setObjectName("CodeDock")  # 设置对象名以避免警告
        self.code_generator = CodeGenerator(self.project_model, self)
        self.code_dock.setWidget(self.code_generator)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.code_dock)
        
    def create_central_widget(self):
        """创建中央组件"""
        # 创建画布视图
        self.canvas_view = CanvasView(self.project_model, self)
        self.setCentralWidget(self.canvas_view)
        
    def connect_signals(self):
        """连接信号槽"""
        # 连接图层面板和属性面板的信号
        self.layer_panel.layer_selected.connect(self.property_panel.set_current_layer)
        
        # 连接画布和图层面板的选择信号
        self.canvas_view.layer_selected.connect(self.property_panel.set_current_layer)
        self.layer_panel.layer_selected.connect(self.canvas_view.select_layer)
        
        # 连接代码生成器的参数刷新信号
        self.project_model.layer_added.connect(self.code_generator.refresh_parameters)
        self.project_model.layer_removed.connect(self.code_generator.refresh_parameters)
        self.project_model.layer_updated.connect(self.code_generator.refresh_parameters)
        
    # 槽函数实现
    def new_project(self):
        """新建项目"""
        # 检查是否有未保存的更改
        if self.check_unsaved_changes():
            return
            
        # 清空当前项目
        self.project_model.clear_layers()
        self.project_model._base_image = None
        self.project_model.project_name = "未命名项目"
        self.project_model.function_name = "generate_image"
        
        # 更新代码生成器UI
        self.code_generator.update_from_project()
        
        self.status_bar.showMessage("已创建新项目")
        
    def open_project(self):
        """打开项目"""
        if self.check_unsaved_changes():
            return
            
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "打开项目",
            "",
            "Pillow Generator项目 (*.pgp);;所有文件 (*)"
        )
        
        if file_path:
            if self.project_manager.load_project(self.project_model, file_path):
                # 确保项目名称与文件名一致
                project_name = os.path.splitext(os.path.basename(file_path))[0]
                self.project_model.project_name = project_name
                
                # 更新代码生成器UI
                self.code_generator.update_from_project()
                
                self.setWindowTitle(f"Pillow 代码生成器 - {os.path.basename(file_path)}")
                self.status_bar.showMessage(f"已打开项目: {os.path.basename(file_path)}")
            else:
                QMessageBox.critical(self, "错误", "打开项目失败！")
            
    def save_project(self):
        """保存项目"""
        if self.project_manager.current_file:
            if self.project_manager.save_project(self.project_model, self.project_manager.current_file):
                self.status_bar.showMessage("项目已保存")
            else:
                QMessageBox.critical(self, "错误", "保存项目失败！")
        else:
            self.save_project_as()
        
    def save_project_as(self):
        """另存为"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "另存为",
            f"{self.project_model.project_name}.pgp",
            "Pillow Generator项目 (*.pgp);;所有文件 (*)"
        )
        
        if file_path:
            # 更新项目名称为文件名（去掉扩展名）
            project_name = os.path.splitext(os.path.basename(file_path))[0]
            self.project_model.project_name = project_name
            
            if self.project_manager.save_project(self.project_model, file_path):
                self.setWindowTitle(f"Pillow 代码生成器 - {os.path.basename(file_path)}")
                self.status_bar.showMessage(f"项目已保存至: {os.path.basename(file_path)}")
            else:
                QMessageBox.critical(self, "错误", "保存项目失败！")
            
    def set_base_image(self):
        """设置底图"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择底图",
            "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.tiff);;所有文件 (*)"
        )
        
        if file_path:
            # 显示底图设置对话框
            dialog = BaseImageDialog(self)
            
            # 如果已经有底图，加载现有设置
            if self.project_model.base_image:
                base_img = self.project_model.base_image
                dialog.parameter_checkbox.setChecked(base_img.is_path_parameter)
                dialog.parameter_name_edit.setText(base_img.parameter_name)
                dialog.parameter_name_edit.setEnabled(base_img.is_path_parameter)
            
            if dialog.exec() == QDialog.DialogCode.Accepted:
                settings = dialog.get_parameter_settings()
                self.project_model.set_base_image(
                    file_path, 
                    f"底图 - {os.path.basename(file_path)}",
                    settings['is_parameter'],
                    settings['parameter_name']
                )
                
                param_text = f" (参数: {settings['parameter_name']})" if settings['is_parameter'] else ""
                self.status_bar.showMessage(f"已设置底图: {os.path.basename(file_path)}{param_text}")
            
    def add_image_layer(self):
        """添加图片层"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择图片",
            "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.tiff);;所有文件 (*)"
        )
        
        if file_path:
            from ..core.models import ImageLayer, Size
            layer = ImageLayer(
                name=f"图片 - {os.path.basename(file_path)}",
                image_path=file_path,
                size=Size(200, 200)
            )
            self.project_model.add_layer(layer)
            self.status_bar.showMessage(f"已添加图片层: {os.path.basename(file_path)}")
            
    def add_text_layer(self):
        """添加文字层"""
        from ..core.models import TextLayer
        layer = TextLayer(
            name="文字层",
            text="示例文字"
        )
        self.project_model.add_layer(layer)
        self.status_bar.showMessage("已添加文字层")
        
    def generate_code(self):
        """生成代码"""
        self.code_generator.generate_code()
        self.status_bar.showMessage("代码生成完成")
        
    def preview_result(self):
        """预览结果"""
        # TODO: 实现预览功能
        self.status_bar.showMessage("预览功能正在开发中...")
        
    def reset_view(self):
        """重置视图"""
        self.canvas_view.reset_view()
        self.status_bar.showMessage("视图已重置")
        
    def fit_to_window(self):
        """适配窗口"""
        self.canvas_view.fit_to_window()
        self.status_bar.showMessage("已适配窗口")
        
    def check_unsaved_changes(self) -> bool:
        """检查未保存的更改"""
        if self.project_manager.is_project_modified(self.project_model):
            reply = QMessageBox.question(
                self, 
                "未保存的更改", 
                "当前项目有未保存的更改，是否保存？",
                QMessageBox.StandardButton.Save | 
                QMessageBox.StandardButton.Discard | 
                QMessageBox.StandardButton.Cancel
            )
            
            if reply == QMessageBox.StandardButton.Save:
                self.save_project()
                return False
            elif reply == QMessageBox.StandardButton.Cancel:
                return True
                
        return False
        
    def save_window_state(self):
        """保存窗口状态"""
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        
    def restore_window_state(self):
        """恢复窗口状态"""
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
            
        window_state = self.settings.value("windowState")
        if window_state:
            self.restoreState(window_state)
            
    def closeEvent(self, event):
        """窗口关闭事件"""
        if self.check_unsaved_changes():
            event.ignore()
            return
            
        self.save_window_state()
        event.accept()
