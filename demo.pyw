"""
CircleWindow - 一个完美的圆形窗口库

这是一个打破传统矩形窗口的库，提供纯圆形的窗口界面。
设计理念：打破成见，解放思维，让用户知道图形界面窗口不只有方形。

使用方法：
    from circle_window import CircleWindow
    
    # 创建默认圆形窗口
    window = CircleWindow()
    
    # 或者自定义参数
    window = CircleWindow(
        radius=200,
        color="blue",
        min_radius=100,
        max_radius=400
    )
    
    window.show()
"""

import sys
import random
import math
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import Qt, QPoint, QTimer
from PyQt5.QtGui import QPainter, QBrush, QColor, QPen, QRadialGradient, QCursor


class CircleWindow(QWidget):
    """
    圆形窗口类
    
    创建一个完美的圆形窗口，没有矩形边框，没有内部内容。
    支持拖动、缩放和颜色切换，以及物理模拟和窗口间碰撞。
    
    参数:
        radius (int): 初始半径，默认300像素
        color (str|tuple): 颜色，可以是颜色名称或RGB元组，默认蓝色
        min_radius (int): 最小半径，默认100像素
        max_radius (int): 最大半径，默认500像素
        title (str): 窗口标题（仅用于调试），默认"○"
        stay_on_top (bool): 是否置顶显示，默认True
        show_console (bool): 是否在控制台显示操作提示，默认True
        physics_enabled (bool): 是否启用物理模拟，默认True
        collision_enabled (bool): 是否启用窗口间碰撞，默认True
        x (int): 窗口初始X坐标，默认None（居中）
        y (int): 窗口初始Y坐标，默认None（居中）
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
    
    # 类变量，用于跟踪所有创建的窗口
    windows = []
    
    def __init__(self, radius=300, color="blue", min_radius=100, max_radius=500, 
                 title="○", stay_on_top=True, show_console=True, physics_enabled=True,
                 collision_enabled=True, x=None, y=None):
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
        
        # 物理模拟参数
        self.physics_enabled = physics_enabled
        self.collision_enabled = collision_enabled
        self.gravity = 0.5
        self.elasticity = 0.8
        self.friction = 0.99
        self.border_friction = 0.7  # 屏幕边框摩擦力系数
        self.vx = 0  # 水平速度
        self.vy = 0  # 垂直速度
        self.trail = []  # 轨迹点
        self.max_trail_length = 20
        
        # 初始化窗口
        self._init_window(title, stay_on_top, x, y)
        
        # 拖拽状态
        self.dragging = False
        self.offset = QPoint()
        self.drag_velocity = []  # 拖拽速度记录
        self.last_mouse_pos = QPoint()
        
        # 添加到窗口列表
        CircleWindow.windows.append(self)
        
        # 物理定时器（全局共享）
        if not hasattr(CircleWindow, 'physics_timer'):
            CircleWindow.physics_timer = QTimer()
            CircleWindow.physics_timer.timeout.connect(self._update_all_physics)
            CircleWindow.physics_timer.start(16)  # ~60fps
        
        # 显示操作提示
        if self.show_console:
            self._print_instructions()
    
    def _parse_color(self, color):
        """解析颜色参数"""
        if isinstance(color, str) and color.lower() in self.COLOR_MAP:
            return self.COLOR_MAP[color.lower()]
        return QColor(52, 152, 219)  # 默认蓝色
    
    def _init_window(self, title, stay_on_top, x=None, y=None):
        """初始化窗口属性"""
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowTitle(title)
        
        # 设置窗口大小
        self.setFixedSize(self.radius * 2, self.radius * 2)
        
        # 设置初始位置
        if x is not None and y is not None:
            self.move(x, y)
        else:
            self.center()
    
    def center(self):
        """将窗口居中显示"""
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
    
    def _update_all_physics(self):
        """更新所有窗口的物理状态（类方法）"""
        # 先更新所有窗口的位置
        for window in CircleWindow.windows[:]:  # 使用副本遍历，避免在循环中修改列表
            if window.physics_enabled and not window.dragging:
                window._update_position()
        
        # 然后检测和处理碰撞
        if any(window.collision_enabled for window in CircleWindow.windows):
            self._handle_collisions()
    
    def _update_position(self):
        """更新单个窗口的位置（不处理碰撞）"""
        if not self.physics_enabled or self.dragging:
            return
        
        # 应用重力
        self.vy += self.gravity
        
        # 应用空气摩擦力
        self.vx *= self.friction
        self.vy *= self.friction
        
        # 计算新位置
        new_x = self.x() + self.vx
        new_y = self.y() + self.vy
        
        # 获取屏幕边界
        screen = QApplication.primaryScreen().geometry()
        screen_width = screen.width()
        screen_height = screen.height()
        
        # 边界碰撞检测
        collision_occurred = False
        
        # 左边界
        if new_x <= 0:
            new_x = 0
            self.vx = -self.vx * self.elasticity
            # 应用边框摩擦力 - 垂直方向速度减小
            self.vy *= self.border_friction
            collision_occurred = True
        
        # 右边界
        if new_x + self.width() >= screen_width:
            new_x = screen_width - self.width()
            self.vx = -self.vx * self.elasticity
            # 应用边框摩擦力 - 垂直方向速度减小
            self.vy *= self.border_friction
            collision_occurred = True
        
        # 上边界
        if new_y <= 0:
            new_y = 0
            self.vy = -self.vy * self.elasticity
            # 应用边框摩擦力 - 水平方向速度减小
            self.vx *= self.border_friction
            collision_occurred = True
        
        # 下边界
        if new_y + self.height() >= screen_height:
            new_y = screen_height - self.height()
            self.vy = -self.vy * self.elasticity
            # 应用边框摩擦力 - 水平方向速度减小
            self.vx *= self.border_friction
            collision_occurred = True
        
        # 添加轨迹点
        self.trail.append((self.x() + self.radius, self.y() + self.radius))
        if len(self.trail) > self.max_trail_length:
            self.trail.pop(0)
        
        # 更新位置
        self.move(int(new_x), int(new_y))
        
        # 检测是否接近底部（距离底部小于10像素）
        bottom_threshold = 10
        distance_to_bottom = screen_height - (self.y() + self.height())
        
        if distance_to_bottom < bottom_threshold and distance_to_bottom >= 0:
            # 计算速度大小
            speed = math.sqrt(self.vx**2 + self.vy**2)
            
            # 如果速度很小，则停止运动
            if speed < 1.5:  # 稍微提高阈值
                self.vx = 0
                self.vy = 0
                # if self.show_console and self.trail:  # 只在有轨迹时打印（避免重复打印）
                    # print("○ 窗口已停止运动")
    
    @classmethod
    def _handle_collisions(cls):
        """处理所有窗口间的碰撞"""
        # 检测所有窗口对之间的碰撞
        for i, window1 in enumerate(cls.windows):
            if not window1.collision_enabled or window1.dragging:
                continue
                
            for j, window2 in enumerate(cls.windows[i+1:], i+1):
                if not window2.collision_enabled or window2.dragging:
                    continue
                
                # 计算两个窗口中心点之间的距离
                x1, y1 = window1.x() + window1.radius, window1.y() + window1.radius
                x2, y2 = window2.x() + window2.radius, window2.y() + window2.radius
                dx, dy = x2 - x1, y2 - y1
                distance = math.sqrt(dx*dx + dy*dy)
                
                # 如果距离小于两半径之和，则发生碰撞
                min_distance = window1.radius + window2.radius
                if distance < min_distance and distance > 0:
                    # 计算碰撞法线（单位向量）
                    nx, ny = dx/distance, dy/distance
                    
                    # 计算相对速度
                    dvx = window2.vx - window1.vx
                    dvy = window2.vy - window1.vy
                    
                    # 计算相对速度在法线方向的分量
                    velocity_along_normal = dvx * nx + dvy * ny
                    
                    # 如果物体正在分离，不处理碰撞
                    if velocity_along_normal > 0:
                        continue
                    
                    # 计算反弹系数（弹性）
                    restitution = min(window1.elasticity, window2.elasticity)
                    
                    # 计算冲量
                    impulse = -(1 + restitution) * velocity_along_normal
                    impulse /= (1/window1.radius + 1/window2.radius)  # 使用半径作为质量近似
                    
                    # 应用冲量
                    window1.vx -= impulse * nx / window1.radius
                    window1.vy -= impulse * ny / window1.radius
                    window2.vx += impulse * nx / window2.radius
                    window2.vy += impulse * ny / window2.radius
                    
                    # 分离重叠的窗口
                    overlap = min_distance - distance
                    if overlap > 0:
                        # 根据质量（半径）比例移动窗口
                        total_mass = window1.radius + window2.radius
                        correction = overlap * 0.5  # 分离系数
                        
                        # 移动窗口使其刚好接触
                        window1.move(
                            int(window1.x() - correction * nx * (window2.radius / total_mass)),
                            int(window1.y() - correction * ny * (window2.radius / total_mass))
                        )
                        window2.move(
                            int(window2.x() + correction * nx * (window1.radius / total_mass)),
                            int(window2.y() + correction * ny * (window1.radius / total_mass))
                        )
                    
                    # # 可选：在控制台输出碰撞信息
                    # if window1.show_console or window2.show_console:
                        # speed = math.sqrt(dvx**2 + dvy**2)
                        # print(f"○ 窗口碰撞！速度: {speed:.2f}")
    
    def paintEvent(self, event):
        """绘制圆形窗口"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制轨迹（如果启用了物理模拟）
        if self.physics_enabled and len(self.trail) > 1:
            for i in range(len(self.trail) - 1):
                alpha = int(255 * i / len(self.trail))
                color = QColor(self.color)
                color.setAlpha(alpha)
                
                pos1 = self.trail[i]
                pos2 = self.trail[i + 1]
                
                # 将屏幕坐标转换为窗口坐标
                x1 = pos1[0] - self.x()
                y1 = pos1[1] - self.y()
                x2 = pos2[0] - self.x()
                y2 = pos2[1] - self.y()
                
                pen = QPen(color, 2)
                painter.setPen(pen)
                painter.drawLine(int(x1), int(y1), int(x2), int(y2))
        
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
        
        # 如果启用了碰撞检测，绘制碰撞体积指示器
        if self.collision_enabled and self.show_console:
            # 绘制半透明外圈表示碰撞体积
            painter.setPen(QPen(QColor(255, 255, 255, 100), 1))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(2, 2, self.width()-4, self.height()-4)
    
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.offset = event.pos()
            self.last_mouse_pos = event.globalPos()
            self.drag_velocity = []
            
            # 停止物理运动
            if self.physics_enabled:
                self.vx = 0
                self.vy = 0
        elif event.button() == Qt.RightButton:
            self.close()
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if self.dragging and event.buttons() & Qt.LeftButton:
            # 记录拖拽速度
            current_mouse_pos = event.globalPos()
            if hasattr(self, 'last_mouse_pos'):
                dx = current_mouse_pos.x() - self.last_mouse_pos.x()
                dy = current_mouse_pos.y() - self.last_mouse_pos.y()
                self.drag_velocity.append((dx, dy))
                
                # 只保留最近5帧的速度记录
                if len(self.drag_velocity) > 5:
                    self.drag_velocity.pop(0)
            
            # 移动窗口
            self.move(event.globalPos() - self.offset)
            
            # 更新鼠标位置
            self.last_mouse_pos = current_mouse_pos
            
            # 清空轨迹
            if self.physics_enabled:
                self.trail = []
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if event.button() == Qt.LeftButton and self.dragging:
            self.dragging = False
            
            # 如果启用了物理模拟，给予初速度
            if self.physics_enabled and self.drag_velocity:
                # 计算平均速度
                avg_vx = sum(v[0] for v in self.drag_velocity) / len(self.drag_velocity)
                avg_vy = sum(v[1] for v in self.drag_velocity) / len(self.drag_velocity)
                
                # 给予速度
                self.vx = avg_vx * 0.5
                self.vy = avg_vy * 0.5
            
            # 清空速度记录
            self.drag_velocity = []
    
    def mouseDoubleClickEvent(self, event):
        """鼠标双击事件：切换颜色"""
        if event.button() == Qt.LeftButton:
            self.random_color()
    
    def wheelEvent(self, event):
        """鼠标滚轮事件：缩放窗口"""
        # 检查是否按下了Ctrl键
        if event.modifiers() & Qt.ControlModifier:
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
        if event.key() == Qt.Key_Space:
            # 暂停/继续物理模拟
            self.physics_enabled = not self.physics_enabled
            if self.physics_enabled:
                if self.show_console:
                    print("○ 物理模拟已启用")
            else:
                if self.show_console:
                    print("○ 物理模拟已禁用")
        elif event.key() == Qt.Key_B:
            # 在鼠标位置创建新窗口
            self.create_window_at_cursor()
        elif event.key() == Qt.Key_T:
            # 切换碰撞检测
            self.collision_enabled = not self.collision_enabled
            if self.show_console:
                status = "启用" if self.collision_enabled else "禁用"
                print(f"○ 窗口间碰撞检测: {status}")
        elif event.key() == Qt.Key_F:
            # 调整边框摩擦力
            if self.border_friction >= 1.0:
                self.border_friction = 0.1
            else:
                self.border_friction = min(1.0, self.border_friction + 0.1)
            
            if self.show_console:
                print(f"○ 边框摩擦力: {self.border_friction:.1f}")
    
    def create_window_at_cursor(self):
        """在鼠标位置创建新窗口"""
        # 获取鼠标位置
        cursor_pos = QCursor.pos()
        
        # 随机颜色
        color_names = list(self.COLOR_MAP.keys())
        random_color = random.choice(color_names)
        
        # 获取屏幕尺寸
        screen = QApplication.primaryScreen().geometry()
        max_radius = min(screen.width(), screen.height()) // 4  # 最大半径为屏幕尺寸的1/4
        
        # 随机半径
        random_radius = random.randint(30, max_radius)
        
        # 确保窗口不会超出屏幕边界
        x = max(0, min(cursor_pos.x() - random_radius, screen.width() - random_radius * 2))
        y = max(0, min(cursor_pos.y() - random_radius, screen.height() - random_radius * 2))
        
        # 创建新窗口
        new_window = CircleWindow(
            radius=random_radius,
            color=random_color,
            min_radius=20,
            max_radius=max_radius,
            x=x,
            y=y,
            show_console=self.show_console,
            collision_enabled=True  # 默认启用碰撞检测
        )
        
        # 随机初始速度
        if new_window.physics_enabled:
            new_window.vx = random.uniform(-8, 8)
            new_window.vy = random.uniform(-8, 8)
        
        new_window.show()
        
        if self.show_console:
            print(f"○ 在 ({cursor_pos.x()}, {cursor_pos.y()}) 创建了半径为 {random_radius} 的新窗口")
    
    def random_color(self):
        """随机切换颜色"""
        color_names = list(self.COLOR_MAP.keys())
        random_name = random.choice(color_names)
        self.color = self.COLOR_MAP[random_name]
        
        if self.show_console:
            print(f"○ 颜色切换为: {random_name}")
        
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
        print("  - Ctrl+滚轮: 缩放窗口")
        print("键盘控制:")
        print("  - 空格键: 暂停/继续物理模拟")
        print("  - B 键: 在鼠标位置创建新窗口")
        print("  - T 键: 切换窗口间碰撞检测")
        print("  - F 键: 调整边框摩擦力")
        print("=" * 50)
        if self.physics_enabled:
            print("物理模拟已启用:")
            print("  - 拖动释放后窗口会做抛体运动")
            print("  - 窗口会与屏幕边界碰撞")
            print("  - 接近底部时窗口会自然停止")
            print(f"  - 边框摩擦力: {self.border_friction:.1f}")
            print("  - 按空格键可暂停物理模拟")
        if self.collision_enabled:
            print("窗口间碰撞检测已启用:")
            print("  - 窗口之间会相互碰撞")
            print("  - 碰撞后会反弹并交换动量")
            print("  - 按T键可禁用碰撞检测")
        print("=" * 50)
    
    def show(self):
        """显示窗口"""
        super().show()
        if self.show_console:
            print("○ 圆形窗口已启动")
    
    # def closeEvent(self, event):
        # """窗口关闭事件"""
        # # 从窗口列表中移除
        # if self in CircleWindow.windows:
            # CircleWindow.windows.remove(self)
        
        # if self.show_console:
            # print("○ 圆形窗口已关闭")
        
        # event.accept()
        
    # 在CircleWindow类的closeEvent方法中修改
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 从窗口列表中移除
        if self in CircleWindow.windows:
            CircleWindow.windows.remove(self)
        
        if self.show_console:
            print("○ 圆形窗口已关闭")
        
        # 检查是否所有窗口都已关闭
        if len(CircleWindow.windows) == 0:
            if self.show_console:
                print("○ 所有窗口已关闭，程序将退出")
            
            # 停止物理定时器
            if hasattr(CircleWindow, 'physics_timer') and CircleWindow.physics_timer.isActive():
                CircleWindow.physics_timer.stop()
            
            # 退出应用程序
            app = QApplication.instance()
            if app is not None:
                app.quit()
        
        event.accept()

# def create_window(radius=300, color="blue", min_radius=100, max_radius=500, 
                  # title="○", stay_on_top=True, show_console=True, physics_enabled=True,
                  # collision_enabled=True, x=None, y=None):
    # """
    # 创建并返回一个圆形窗口实例
    
    # 参数:
        # radius (int): 初始半径，默认300像素
        # color (str|tuple): 颜色，可以是颜色名称或RGB元组，默认蓝色
        # min_radius (int): 最小半径，默认100像素
        # max_radius (int): 最大半径，默认500像素
        # title (str): 窗口标题（仅用于调试），默认"○"
        # stay_on_top (bool): 是否置顶显示，默认True
        # show_console (bool): 是否在控制台显示操作提示，默认True
        # physics_enabled (bool): 是否启用物理模拟，默认True
        # collision_enabled (bool): 是否启用窗口间碰撞，默认True
        # x (int): 窗口初始X坐标，默认None（居中）
        # y (int): 窗口初始Y坐标，默认None（居中）
    
    # 返回:
        # CircleWindow: 圆形窗口实例
    # """
    # window = CircleWindow(radius, color, min_radius, max_radius, 
                         # title, stay_on_top, show_console, physics_enabled,
                         # collision_enabled, x, y)
    # return window
    
def create_window(radius=300, color="blue", min_radius=100, max_radius=500, 
                  title="○", stay_on_top=True, show_console=True, physics_enabled=True,
                  collision_enabled=True, x=None, y=None):
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
        physics_enabled (bool): 是否启用物理模拟，默认True
        collision_enabled (bool): 是否启用窗口间碰撞，默认True
        x (int): 窗口初始X坐标，默认None（居中）
        y (int): 窗口初始Y坐标，默认None（居中）
    
    返回:
        CircleWindow: 圆形窗口实例
    """
    try:
        window = CircleWindow(radius, color, min_radius, max_radius, 
                             title, stay_on_top, show_console, physics_enabled,
                             collision_enabled, x, y)
        return window
    except Exception as e:
        # 如果创建窗口失败，检查是否没有其他窗口，如果是则退出程序
        if len(CircleWindow.windows) == 0:
            app = QApplication.instance()
            if app is not None:
                if show_console:
                    print(f"○ 创建窗口失败: {e}")
                    print("○ 没有其他窗口，程序将退出")
                app.quit()
        return None

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


# 演示函数：创建多个相互碰撞的窗口
def demo_collision():
    """演示窗口间碰撞功能"""
    app = QApplication(sys.argv)
    
    # 创建多个窗口
    windows = []
    colors = ["blue", "red", "green", "yellow", "purple", "cyan", "orange", "pink"]
    
    # 获取屏幕尺寸
    screen = QApplication.primaryScreen().geometry()
    
    for i in range(5):  # 创建5个窗口
        radius = random.randint(40, 80)
        color = colors[i % len(colors)]
        
        # 随机位置，确保不会一开始就重叠
        x = random.randint(radius, screen.width() - radius * 2)
        y = random.randint(radius, screen.height() - radius * 2)
        
        # 检查是否与现有窗口重叠
        overlap = True
        attempts = 0
        while overlap and attempts < 10:  # 最多尝试10次
            overlap = False
            for existing in windows:
                dx = (x + radius) - (existing.x() + existing.radius)
                dy = (y + radius) - (existing.y() + existing.radius)
                distance = math.sqrt(dx*dx + dy*dy)
                if distance < radius + existing.radius + 20:  # 保持20像素的安全距离
                    overlap = True
                    x = random.randint(radius, screen.width() - radius * 2)
                    y = random.randint(radius, screen.height() - radius * 2)
                    break
            attempts += 1
        
        window = CircleWindow(
            radius=radius,
            color=color,
            min_radius=30,
            max_radius=100,
            x=x,
            y=y,
            show_console=True,
            physics_enabled=True,
            collision_enabled=True
        )
        
        # 随机初始速度
        window.vx = random.uniform(-5, 5)
        window.vy = random.uniform(-5, 5)
        
        window.show()
        windows.append(window)
    
    print("=" * 50)
    print("○ 窗口碰撞演示已启动")
    print("○ 创建了5个具有碰撞检测的窗口")
    print("○ 窗口会相互碰撞并反弹")
    print("○ 按T键可切换碰撞检测")
    print("○ 按F键可调整边框摩擦力")
    print("=" * 50)
    
    return app.exec_()


# 简单测试函数
def demo():
    """演示函数：显示一个默认的圆形窗口"""
    return show_window()


# 直接运行库文件时的入口
if __name__ == "__main__":
    print("○ CircleWindow库 - 直接运行")
    print("○ 正在启动圆形窗口...")
    
    # 检查是否启用碰撞演示
    if len(sys.argv) > 1 and sys.argv[1] == "collision":
        sys.exit(demo_collision())
    else:
        sys.exit(demo())