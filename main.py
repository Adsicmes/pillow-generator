#!/usr/bin/env python3
"""
Pillow 代码生成器
可视化编排Pillow模板的桌面应用程序
"""
import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from src.ui.main_window import MainWindow


def main():
    """主函数"""
    # 创建应用程序
    app = QApplication(sys.argv)
    
    # 设置应用程序属性
    app.setApplicationName("Pillow Generator")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("PillowGenerator")
    app.setOrganizationDomain("github.com")
    
    # 设置高DPI支持（移除已弃用的属性）
    
    # 创建主窗口
    window = MainWindow()
    window.show()
    
    # 运行应用程序
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
