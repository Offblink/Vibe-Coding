"""
CircleWindow 增强版
修复了事件处理，提供更好的API
"""

import sys
import random
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import Qt, QPoint, QTimer
from PyQt5.QtGui import QPainter, QBrush, QColor, QPen, QRadialGradient


class CircleWindow(QWidget):
    """
    圆形窗口类 - 增强版
    
    创建一个完美的圆形窗口，没有矩形边框，没有内部内容。
    支持拖动、缩放和颜色切换。
    
    参数:
        radius (int): 初始半径，默认300像素
        color (str|tuple): 颜色，可以是颜色名称或RGB元组，默认蓝色
        min_radius (int): 最小半径，默认100像素
        max_radius (int): 最大半径，默认500像素
        title (str): 窗口标题（仅用于调试），默认"○"
        stay_on_top (bool): 是否置顶显示，默认True
        show_console (bool): 是否在控制台显示操作提示，默认True
    """
    
    # 预定义颜色映射
    COLOR_MAP = {
        "blue": QColor(52, 152, 219),
        "red": QColor(231, 76, 60),
        "green": QColor(46, 204, 113),
        "yellow": QColor(241, 196, 15),
        "purple": QColor(155, 89, 182),
        "cyan": QColor(26, 188, 156),
        "white": QColor(236, 240, 241),
        "dark": QColor(44, 62, 80),
        "orange": QColor(230, 126, 34),
        "pink": QColor(255, 107, 129),
    }
    
    def __init__(self, radius=300, color="blue", min_radius=100, max_radius=500, 
                 title="○", stay_on_top=True, show_console=True):
        super().__init__()
        
        # 窗口参数
        self.radius = radius
        self.min_radius = min_radius
        self.max_radius = max_radius
        
        # 保存原始半径用于重置
        self._original_radius = radius
        
        # 颜色处理
        self._original_color = self._parse_color(color)
        self.color = self._original_color
        
        # 控制台显示
        self.show_console = show_console
        
        # 初始化窗口
        self._init_window(title, stay_on_top)
        
        # 拖拽状态
        self.dragging = False
        self.offset = QPoint()
        
        # 显示操作提示
        if self.show_console:
            self._print_instructions()
    
    def _parse_color(self, color):
        """解析颜色参数"""
        if isinstance(color, str):
            # 字符串颜色：预定义名称或十六进制
            color_lower = color.lower()
            if color_lower in self.COLOR_MAP:
                return self.COLOR_MAP[color_lower]
            elif color_lower.startswith('#'):
                # 十六进制颜色
                hex_color = color_lower.lstrip('#')
                if len(hex_color) == 6:
                    r = int(hex_color[0:2], 16)
                    g = int(hex_color[2:4], 16)
                    b = int(hex_color[4:6], 16)
                    return QColor(r, g, b)
                elif len(hex_color) == 8:
                    r = int(hex_color[0:2], 16)
                    g = int(hex_color[2:4], 16)
                    b = int(hex_color[4:6], 16)
                    a = int(hex_color[6:8], 16)
                    return QColor(r, g, b, a)
        elif isinstance(color, (tuple, list)):
            # RGB或RGBA元组
            if len(color) == 3:
                return QColor(color[0], color[1], color[2])
            elif len(color) == 4:
                return QColor(color[0], color[1], color[2], color[3])
        
        # 默认返回蓝色
        return QColor(52, 152, 219)
    
    def _init_window(self, title, stay_on_top):
        """初始化窗口属性"""
        # 设置窗口标志
        flags = Qt.FramelessWindowHint | Qt.Tool
        
        if stay_on_top:
            flags |= Qt.WindowStaysOnTopHint
        
        self.setWindowFlags(flags)
        
        # 设置透明背景
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 设置窗口标题
        self.setWindowTitle(title)
        
        # 设置窗口大小
        self.setFixedSize(self.radius * 2, self.radius * 2)
        
        # 居中显示
        self.center()
    
    def center(self):
        """将窗口居中显示"""
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
    
    def paintEvent(self, event):
        """绘制圆形窗口"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 创建径向渐变
        gradient = QRadialGradient(
            self.radius, self.radius,
            self.radius
        )
        gradient.setColorAt(0, self.color.lighter(120))
        gradient.setColorAt(1, self.color.darker(120))
        
        # 绘制圆形
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(self.color.darker(140), 2))
        painter.drawEllipse(0, 0, self.width(), self.height())
    
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.offset = event.pos()
        elif event.button() == Qt.RightButton:
            self.close()
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if self.dragging and event.buttons() & Qt.LeftButton:
            self.move(event.globalPos() - self.offset)
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if event.button() == Qt.LeftButton:
            self.dragging = False
    
    def mouseDoubleClickEvent(self, event):
        """鼠标双击事件：切换颜色"""
        if event.button() == Qt.LeftButton:
            self.random_color()
    
    def wheelEvent(self, event):
        """鼠标滚轮事件：缩放窗口"""
        if event.angleDelta().y() > 0:
            # 向上滚动 - 放大
            new_radius = min(self.radius + 20, self.max_radius)
        else:
            # 向下滚动 - 缩小
            new_radius = max(self.radius - 20, self.min_radius)
        
        if new_radius != self.radius:
            # 计算中心点
            center = self.geometry().center()
            new_size = new_radius * 2
            new_x = center.x() - new_radius
            new_y = center.y() - new_radius
            
            # 更新窗口
            self.radius = new_radius
            self.setFixedSize(new_size, new_size)
            self.move(new_x, new_y)
            self.update()
    
    def keyPressEvent(self, event):
        """键盘事件"""
        if event.key() == Qt.Key_Escape:
            self.close()
        elif event.key() == Qt.Key_C:
            self.random_color()
        elif event.key() == Qt.Key_R:
            self.reset_size()
        elif event.key() == Qt.Key_F:
            self.toggle_fullscreen()
        elif event.key() == Qt.Key_H:
            self._print_instructions()
        elif event.key() == Qt.Key_Plus or event.key() == Qt.Key_Equal:
            self.zoom_in()
        elif event.key() == Qt.Key_Minus:
            self.zoom_out()
    
    def zoom_in(self, delta=20):
        """放大窗口"""
        new_radius = min(self.radius + delta, self.max_radius)
        if new_radius != self.radius:
            center = self.geometry().center()
            new_size = new_radius * 2
            new_x = center.x() - new_radius
            new_y = center.y() - new_radius
            
            self.radius = new_radius
            self.setFixedSize(new_size, new_size)
            self.move(new_x, new_y)
            self.update()
    
    def zoom_out(self, delta=20):
        """缩小窗口"""
        new_radius = max(self.radius - delta, self.min_radius)
        if new_radius != self.radius:
            center = self.geometry().center()
            new_size = new_radius * 2
            new_x = center.x() - new_radius
            new_y = center.y() - new_radius
            
            self.radius = new_radius
            self.setFixedSize(new_size, new_size)
            self.move(new_x, new_y)
            self.update()
    
    def random_color(self):
        """随机切换颜色"""
        color_names = list(self.COLOR_MAP.keys())
        random_name = random.choice(color_names)
        self.color = self.COLOR_MAP[random_name]
        
        if self.show_console:
            print(f"○ 颜色切换为: {random_name}")
        
        self.update()
    
    def set_color(self, color):
        """设置指定颜色
        
        参数:
            color (str|tuple): 颜色名称或RGB元组
        """
        self.color = self._parse_color(color)
        self.update()
    
    def reset_color(self):
        """重置为初始颜色"""
        self.color = self._original_color
        self.update()
    
    def reset_size(self):
        """重置为初始大小"""
        center = self.geometry().center()
        new_size = self._original_radius * 2
        new_x = center.x() - self._original_radius
        new_y = center.y() - self._original_radius
        
        self.radius = self._original_radius
        self.setFixedSize(new_size, new_size)
        self.move(new_x, new_y)
        self.update()
    
    def toggle_fullscreen(self):
        """切换全屏模式（实际上是最大化到屏幕边界）"""
        screen = QApplication.primaryScreen().geometry()
        max_radius = min(screen.width(), screen.height()) // 2 - 20
        
        if self.radius < max_radius - 50:
            # 最大化
            new_radius = max_radius
            if self.show_console:
                print("○ 窗口最大化")
        else:
            # 恢复原始大小
            new_radius = self._original_radius
            if self.show_console:
                print("○ 窗口恢复原始大小")
        
        center = self.geometry().center()
        new_size = new_radius * 2
        new_x = center.x() - new_radius
        new_y = center.y() - new_radius
        
        self.radius = new_radius
        self.setFixedSize(new_size, new_size)
        self.move(new_x, new_y)
        self.update()
    
    def _print_instructions(self):
        """打印操作提示"""
        print("=" * 50)
        print("○ CIRCLE WINDOW - 圆形窗口控制说明")
        print("=" * 50)
        print("鼠标控制:")
        print("  - 左键拖动: 移动窗口")
        print("  - 双击左键: 随机切换颜色")
        print("  - 右键单击: 关闭窗口")
        print("  - 鼠标滚轮: 缩放窗口")
        print("键盘控制:")
        print("  - C 键: 随机切换颜色")
        print("  - R 键: 重置窗口大小")
        print("  - F 键: 切换最大化/原始大小")
        print("  - +/- 键: 放大/缩小窗口")
        print("  - H 键: 显示帮助信息")
        print("  - ESC 键: 关闭窗口")
        print("=" * 50)
    
    def show(self):
        """显示窗口"""
        super().show()
        if self.show_console:
            print("○ 圆形窗口已启动")
    
    def close(self):
        """关闭窗口"""
        super().close()
        if self.show_console:
            print("○ 圆形窗口已关闭")


def create_window(radius=300, color="blue", min_radius=100, max_radius=500, 
                  title="○", stay_on_top=True, show_console=True):
    """
    创建并返回一个圆形窗口实例
    
    参数:
        radius (int): 初始半径，默认300像素
        color (str|tuple): 颜色，可以是颜色名称或RGB元组，默认蓝色
        min_radius (int): 最小半径，默认100像素
        max_radius (int): 最大半径，默认500像素
        title (str): 窗口标题（仅用于调试），默认"○"
        stay_on_top (bool): 是否置顶显示，默认True
        show_console (bool): 是否在控制台显示操作提示，默认True
    
    返回:
        CircleWindow: 圆形窗口实例
    """
    # 保存原始半径用于重置
    window = CircleWindow(radius, color, min_radius, max_radius, 
                         title, stay_on_top, show_console)
    window._original_radius = radius
    
    return window


def show_window(radius=300, color="blue", **kwargs):
    """
    快速创建并显示一个圆形窗口
    
    参数:
        radius (int): 初始半径，默认300像素
        color (str|tuple): 颜色，可以是颜色名称或RGB元组，默认蓝色
        **kwargs: 传递给create_window的其他参数
    
    返回:
        int: 应用程序退出码
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    window = create_window(radius, color, **kwargs)
    window.show()
    
    return app.exec_()


def demo():
    """演示函数：显示一个默认的圆形窗口"""
    return show_window()


# 直接运行库文件时的入口
if __name__ == "__main__":
    print("○ CircleWindow库 - 直接运行")
    print("○ 正在启动圆形窗口...")
    sys.exit(demo())