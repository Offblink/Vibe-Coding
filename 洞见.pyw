"""
鼠标放大镜 - 圆形放大镜窗口
简化版本：去掉快捷键和系统托盘，修改按钮功能
"""

import sys
import math
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                           QLabel, QSlider, QPushButton, QDesktopWidget)
from PyQt5.QtCore import Qt, QTimer, QPoint, QPropertyAnimation, pyqtProperty
from PyQt5.QtGui import (QPainter, QBrush, QColor, QPen, QCursor, QPixmap, 
                        QScreen, QPainterPath, QRegion)


class MagnifierWindow(QWidget):
    """
    鼠标放大镜 - 圆形放大镜窗口
    
    参数:
        size (int): 圆形直径
        zoom_factor (float): 放大倍数
    """
    
    def __init__(self, size=200, zoom_factor=2.0):
        super().__init__()
        
        # 窗口参数
        self.size = size
        self.radius = size // 2
        self.zoom_factor = zoom_factor
        self.border_width = 3
        self._opacity = 1.0  # 用于动画的透明度属性
        
        # 初始化窗口
        self._init_window()
        
        # 追踪相关
        self.tracking = False
        self.track_timer = None
        
        # 动画相关
        self.animation = None
    
    # 添加透明度属性，用于动画
    def get_opacity(self):
        return self._opacity
    
    def set_opacity(self, value):
        self._opacity = value
        self.setWindowOpacity(value)
    
    opacity = pyqtProperty(float, get_opacity, set_opacity)
    
    def _init_window(self):
        """初始化窗口属性"""
        # 设置窗口标志：无边框、工具窗口、置顶
        flags = (Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setWindowFlags(flags)
        
        # 设置透明背景
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 设置窗口标题
        self.setWindowTitle("鼠标放大镜")
        
        # 设置窗口大小
        self.setFixedSize(self.size, self.size)
        
        # 设置圆形区域，实现真正的圆形窗口
        region = QRegion(0, 0, self.size, self.size, QRegion.Ellipse)
        self.setMask(region)
        
        # 设置初始位置（避开鼠标位置）
        self.update_position()
        
        # 关键修改：允许鼠标事件穿透
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
    
    def update_position(self):
        """更新窗口位置到鼠标偏移位置"""
        cursor_pos = QCursor.pos()
        
        # 将窗口放置在鼠标右下方，避免遮挡
        x = cursor_pos.x() + 15  # 向右偏移15像素
        y = cursor_pos.y() + 15  # 向下偏移15像素
        
        # 边界检查：如果右边或下边空间不够，则放在左上方
        screen = QApplication.primaryScreen().geometry()
        
        if x + self.size > screen.width():
            x = cursor_pos.x() - self.size - 15  # 放在鼠标左边
        
        if y + self.size > screen.height():
            y = cursor_pos.y() - self.size - 15  # 放在鼠标上方
        
        # 确保窗口在屏幕内
        x = max(0, min(x, screen.width() - self.size))
        y = max(0, min(y, screen.height() - self.size))
        
        self.move(int(x), int(y))
        self.update()  # 触发重绘以更新放大内容
    
    def grab_screen_area(self):
        """捕获屏幕区域用于放大显示 - 修正版本"""
        cursor_pos = QCursor.pos()
        
        # 计算要捕获的区域大小（原始大小）
        # 捕获的区域大小 = 窗口大小 / 放大倍数
        grab_size = int(self.size / self.zoom_factor)
        
        # 计算捕获区域的左上角坐标（以鼠标为中心）
        grab_x = cursor_pos.x() - grab_size // 2
        grab_y = cursor_pos.y() - grab_size // 2
        
        # 确保捕获区域在屏幕范围内
        screen = QApplication.primaryScreen().geometry()
        grab_x = max(0, min(grab_x, screen.width() - grab_size))
        grab_y = max(0, min(grab_y, screen.height() - grab_size))
        
        try:
            # 捕获屏幕区域
            pixmap = QApplication.primaryScreen().grabWindow(
                0,  # 桌面窗口
                grab_x, grab_y, 
                grab_size, grab_size
            )
            
            # 放大到窗口大小 - 这是真正的放大实现
            return pixmap.scaled(
                self.size, self.size, 
                Qt.IgnoreAspectRatio,  # 忽略宽高比
                Qt.SmoothTransformation  # 平滑变换
            )
        except Exception as e:
            # 如果捕获失败，返回一个默认图像
            print(f"捕获屏幕失败: {e}")
            default_pixmap = QPixmap(self.size, self.size)
            default_pixmap.fill(Qt.white)
            return default_pixmap
    
    def paintEvent(self, event):
        """绘制放大镜窗口"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制放大后的屏幕内容
        screen_pixmap = self.grab_screen_area()
        painter.drawPixmap(0, 0, screen_pixmap)
        
        # 绘制圆形边框
        painter.setPen(QPen(QColor(0, 0, 0, 200), self.border_width))
        painter.drawEllipse(self.border_width//2, self.border_width//2, 
                          self.size-self.border_width, self.size-self.border_width)
        
        # 绘制十字准星
        center = self.radius
        painter.setPen(QPen(QColor(255, 0, 0, 150), 1))
        painter.drawLine(center, center - 10, center, center + 10)  # 垂直线
        painter.drawLine(center - 10, center, center + 10, center)  # 水平线
        
        # 绘制中心点
        painter.setBrush(QBrush(QColor(255, 0, 0)))
        painter.drawEllipse(center - 2, center - 2, 4, 4)
    
    def set_zoom_factor(self, factor):
        """设置放大倍数"""
        self.zoom_factor = max(1.0, min(5.0, factor))  # 限制在1-5倍之间
        self.update()
    
    def set_size(self, size):
        """设置窗口大小"""
        self.size = max(100, min(400, size))  # 限制在100-400之间
        self.radius = self.size // 2
        
        # 重新设置窗口大小和形状
        self.setFixedSize(self.size, self.size)
        region = QRegion(0, 0, self.size, self.size, QRegion.Ellipse)
        self.setMask(region)
        self.update_position()
        self.update()
    
    def start_tracking(self):
        """开始追踪鼠标"""
        if not self.tracking:
            self.tracking = True
            self.track_timer = QTimer()
            self.track_timer.timeout.connect(self.update_position)
            self.track_timer.start(16)  # 约60fps
    
    def stop_tracking(self):
        """停止追踪鼠标"""
        if self.tracking and self.track_timer:
            self.tracking = False
            self.track_timer.stop()
            self.track_timer = None
    
    def show_with_animation(self):
        """带淡入动画的显示"""
        if self.isVisible():
            return
            
        # 停止任何正在进行的动画
        if self.animation:
            self.animation.stop()
            
        # 设置初始透明度
        self.setWindowOpacity(0)
        super().show()
        
        # 创建淡入动画
        self.animation = QPropertyAnimation(self, b"opacity")
        self.animation.setDuration(300)  # 300ms动画
        self.animation.setStartValue(0)
        self.animation.setEndValue(1.0)
        self.animation.start()
        
        # 开始追踪
        self.start_tracking()
    
    def hide_with_animation(self):
        """带淡出动画的隐藏"""
        if not self.isVisible():
            return
            
        # 停止任何正在进行的动画
        if self.animation:
            self.animation.stop()
            
        # 停止追踪
        self.stop_tracking()
        
        # 创建淡出动画
        self.animation = QPropertyAnimation(self, b"opacity")
        self.animation.setDuration(300)  # 300ms动画
        self.animation.setStartValue(self.opacity)
        self.animation.setEndValue(0)
        
        # 修复：使用正确的方式调用父类的hide方法
        def on_animation_finished():
            QWidget.hide(self)  # 直接调用父类的hide方法
        
        self.animation.finished.connect(on_animation_finished)
        self.animation.start()
    
    def toggle_visibility(self):
        """切换显示/隐藏状态"""
        if self.isVisible():
            self.hide_with_animation()
        else:
            self.show_with_animation()
    
    def showEvent(self, event):
        """显示事件 - 用于直接调用show()时确保动画正确"""
        if not self.animation or self.animation.state() != QPropertyAnimation.Running:
            self.setWindowOpacity(1.0)
        super().showEvent(event)
    
    def closeEvent(self, event):
        """关闭事件 - 退出程序"""
        self.stop_tracking()
        super().closeEvent(event)


class ConsoleWindow(QWidget):
    """
    控制台窗口 - 用于调整放大镜参数
    """
    
    def __init__(self, magnifier_window):
        super().__init__()
        self.magnifier_window = magnifier_window
        self._opacity = 1.0
        self.animation = None
        self.init_ui()
    
    # 添加透明度属性，用于动画
    def get_opacity(self):
        return self._opacity
    
    def set_opacity(self, value):
        self._opacity = value
        self.setWindowOpacity(value)
    
    opacity = pyqtProperty(float, get_opacity, set_opacity)
    
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("放大镜控制台")
        self.setFixedSize(300, 200)
        
        # 创建布局
        layout = QVBoxLayout()
        
        # 放大倍数调节
        zoom_layout = QHBoxLayout()
        zoom_label = QLabel("放大倍数:")
        self.zoom_value_label = QLabel(f"{self.magnifier_window.zoom_factor:.1f}x")
        
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setMinimum(10)  # 1.0倍
        self.zoom_slider.setMaximum(50)  # 5.0倍
        self.zoom_slider.setValue(int(self.magnifier_window.zoom_factor * 10))
        self.zoom_slider.valueChanged.connect(self.on_zoom_changed)
        
        zoom_layout.addWidget(zoom_label)
        zoom_layout.addWidget(self.zoom_slider)
        zoom_layout.addWidget(self.zoom_value_label)
        
        # 窗口大小调节
        size_layout = QHBoxLayout()
        size_label = QLabel("窗口大小:")
        self.size_value_label = QLabel(f"{self.magnifier_window.size}px")
        
        self.size_slider = QSlider(Qt.Horizontal)
        self.size_slider.setMinimum(100)
        self.size_slider.setMaximum(400)
        self.size_slider.setValue(self.magnifier_window.size)
        self.size_slider.valueChanged.connect(self.on_size_changed)
        
        size_layout.addWidget(size_label)
        size_layout.addWidget(self.size_slider)
        size_layout.addWidget(self.size_value_label)
        
        # 控制按钮
        button_layout = QHBoxLayout()
        
        # 修改：将"隐藏"按钮改为"隐藏/显示"按钮
        self.toggle_button = QPushButton("隐藏/显示")
        self.toggle_button.clicked.connect(self.toggle_magnifier)
        
        self.close_button = QPushButton("退出程序")
        self.close_button.clicked.connect(self.close_app)
        
        button_layout.addWidget(self.toggle_button)
        button_layout.addWidget(self.close_button)
        
        # 添加到主布局
        layout.addLayout(zoom_layout)
        layout.addLayout(size_layout)
        layout.addStretch(1)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def on_zoom_changed(self, value):
        """放大倍数改变事件"""
        zoom_factor = value / 10.0
        self.zoom_value_label.setText(f"{zoom_factor:.1f}x")
        self.magnifier_window.set_zoom_factor(zoom_factor)
    
    def on_size_changed(self, value):
        """窗口大小改变事件"""
        self.size_value_label.setText(f"{value}px")
        self.magnifier_window.set_size(value)
    
    def toggle_magnifier(self):
        """切换放大镜显示状态"""
        self.magnifier_window.toggle_visibility()
        # # 更新按钮文本
        # if self.magnifier_window.isVisible():
            # self.toggle_button.setText("隐藏放大镜")
        # else:
            # self.toggle_button.setText("显示放大镜")
    
    def show_with_animation(self):
        """带淡入动画的显示"""
        if self.isVisible():
            return
            
        # 停止任何正在进行的动画
        if self.animation:
            self.animation.stop()
            
        # 设置初始透明度
        self.setWindowOpacity(0)
        super().show()
        
        # 创建淡入动画
        self.animation = QPropertyAnimation(self, b"opacity")
        self.animation.setDuration(300)  # 300ms动画
        self.animation.setStartValue(0)
        self.animation.setEndValue(1.0)
        self.animation.start()
    
    def hide_with_animation(self):
        """带淡出动画的隐藏"""
        if not self.isVisible():
            return
            
        # 停止任何正在进行的动画
        if self.animation:
            self.animation.stop()
            
        # 创建淡出动画
        self.animation = QPropertyAnimation(self, b"opacity")
        self.animation.setDuration(300)  # 300ms动画
        self.animation.setStartValue(self.opacity)
        self.animation.setEndValue(0)
        
        # 修复：使用正确的方式调用父类的hide方法
        def on_animation_finished():
            QWidget.hide(self)  # 直接调用父类的hide方法
        
        self.animation.finished.connect(on_animation_finished)
        self.animation.start()
    
    def close_app(self):
        """关闭应用程序"""
        QApplication.quit()
    
    def closeEvent(self, event):
        """窗口关闭事件 - 退出程序"""
        self.magnifier_window.close()
        super().closeEvent(event)


def main():
    """主函数 - 处理命令行参数"""
    # 默认参数
    size = 200
    zoom_factor = 2.0
    
    # 解析命令行参数
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] in ['-s', '--size'] and i + 1 < len(args):
            try:
                size = max(100, min(400, int(args[i + 1])))  # 限制大小在100-400之间
            except ValueError:
                print(f"错误: 大小参数应为整数，使用默认值 {size}")
            i += 2
        elif args[i] in ['-z', '--zoom'] and i + 1 < len(args):
            try:
                zoom_factor = max(1.0, min(5.0, float(args[i + 1])))  # 限制放大倍数在1-5之间
            except ValueError:
                print(f"错误: 放大倍数参数应为数字，使用默认值 {zoom_factor}")
            i += 2
        elif args[i] in ['-h', '--help']:
            print("用法: python mouse_magnifier.py [选项]")
            print("选项:")
            print("  -s, --size SIZE      设置圆形直径 (100-400, 默认: 200)")
            print("  -z, --zoom ZOOM      设置放大倍数 (1.0-5.0, 默认: 2.0)")
            print("  -h, --help           显示此帮助信息")
            return
        else:
            i += 1
    
    # 创建应用
    app = QApplication(sys.argv)
    
    # 创建放大镜窗口
    magnifier_window = MagnifierWindow(size=size, zoom_factor=zoom_factor)
    
    # 创建控制台窗口
    console_window = ConsoleWindow(magnifier_window)
    
    # 将控制台窗口放置在屏幕右上角
    screen_geometry = QDesktopWidget().screenGeometry()
    console_x = screen_geometry.width() - console_window.width() - 20
    console_y = 20  # 距离顶部20像素
    console_window.move(console_x, console_y)
    
    # 显示窗口
    magnifier_window.show_with_animation()
    console_window.show_with_animation()
    
    # 运行应用
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()