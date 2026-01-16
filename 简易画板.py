import sys
import os
import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, 
                             QToolBar, QAction, QColorDialog, QFileDialog,
                             QSpinBox, QHBoxLayout, QPushButton, QSizePolicy, 
                             QVBoxLayout, QButtonGroup, QRadioButton)
from PyQt5.QtGui import (QPainter, QPen, QColor, QImage, QPixmap, 
                         QIcon, QBrush, QLinearGradient, QKeySequence)
from PyQt5.QtCore import Qt, QSize, QPoint, QTimer

class DrawingCanvas(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 初始画布大小
        self.initial_width = 800
        self.initial_height = 600
        
        # 创建画布 - 使用支持透明度的格式
        self.canvas = QImage(self.initial_width, self.initial_height, QImage.Format_ARGB32)
        # 初始填充为透明
        self.canvas.fill(Qt.transparent)
        self.setPixmap(QPixmap.fromImage(self.canvas))
        
        # 画笔设置
        self.pen_color = QColor(Qt.black)
        self.pen_width = 5
        self.drawing = False
        self.last_point = QPoint()
        
        # 橡皮擦设置
        self.eraser_mode = False
        self.eraser_color = QColor(Qt.transparent)
        self.eraser_width = 20
        
        # 设置最小大小
        self.setMinimumSize(self.initial_width, self.initial_height)
        
        # 启用鼠标跟踪
        self.setMouseTracking(True)
        
        # 设置背景为网格样式，方便用户看到透明区域
        self.setStyleSheet("""
            background-color: #f0f0f0;
            background-image: 
                linear-gradient(45deg, #e0e0e0 25%, transparent 25%), 
                linear-gradient(-45deg, #e0e0e0 25%, transparent 25%),
                linear-gradient(45deg, transparent 75%, #e0e0e0 75%),
                linear-gradient(-45deg, transparent 75%, #e0e0e0 75%);
            background-size: 20px 20px;
            background-position: 0 0, 0 10px, 10px -10px, -10px 0px;
        """)
    
    def resize_canvas(self, width, height):
        """调整画布大小以适应窗口变化"""
        # 创建新尺寸的画布
        new_canvas = QImage(width, height, QImage.Format_ARGB32)
        new_canvas.fill(Qt.transparent)
        
        # 将旧画布内容复制到新画布
        painter = QPainter(new_canvas)
        painter.drawImage(0, 0, self.canvas)
        painter.end()
        
        # 更新画布
        self.canvas = new_canvas
        self.setPixmap(QPixmap.fromImage(self.canvas))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = True
            self.last_point = event.pos()
            
    def mouseMoveEvent(self, event):
        if self.drawing and event.buttons() & Qt.LeftButton:
            # 绘制到画布上
            painter = QPainter(self.canvas)
            
            if self.eraser_mode:
                # 使用橡皮擦
                painter.setCompositionMode(QPainter.CompositionMode_Clear)
                painter.setPen(QPen(self.eraser_color, self.eraser_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            else:
                # 使用画笔
                painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
                painter.setPen(QPen(self.pen_color, self.pen_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            
            painter.drawLine(self.last_point, event.pos())
            painter.end()
            
            # 更新显示
            self.setPixmap(QPixmap.fromImage(self.canvas))
            self.last_point = event.pos()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = False
    
    def clear_canvas(self):
        # 清除为透明
        self.canvas.fill(Qt.transparent)
        self.setPixmap(QPixmap.fromImage(self.canvas))
    
    def set_pen_color(self, color):
        self.pen_color = color
        
    def set_pen_width(self, width):
        self.pen_width = width
        
    def set_eraser_width(self, width):
        self.eraser_width = width
        
    def set_eraser_mode(self, enabled):
        self.eraser_mode = enabled
        
    def save_to_image(self, filename):
        """保存图片为PNG格式"""
        try:
            return self.canvas.save(filename, "PNG")
        except Exception as e:
            print(f"保存图片时出错: {e}")
            return False

class HandwritingApp(QMainWindow):
    def __init__(self):
        super().__init__()
        # 初始化颜色属性 - 使用QColor对象
        self.current_color = QColor(Qt.black)
        self.current_size = 5
        self.eraser_size = 20
        self.transparent_bg = True  # 默认使用透明背景
        self.fullscreen_mode = True  # 默认全屏
        
        self.setWindowTitle("手写转图片工具")
        
        # 创建主部件和布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 创建画布
        self.canvas = DrawingCanvas()
        layout.addWidget(self.canvas)
        
        # 创建状态栏
        self.status_label = QLabel("准备就绪 | 模式:画笔 | 颜色:黑色 | 粗细:5px | 背景:透明")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFixedHeight(30)
        self.status_label.setStyleSheet("background-color: #f0f0f0; border-top: 1px solid #cccccc;")
        layout.addWidget(self.status_label)
        
        # 创建工具栏
        self.create_toolbar()
        
        # 添加全屏切换快捷键 (F11)
        self.toggle_fullscreen_action = QAction(self)
        self.toggle_fullscreen_action.setShortcut(QKeySequence("F11"))
        self.toggle_fullscreen_action.triggered.connect(self.toggle_fullscreen)
        self.addAction(self.toggle_fullscreen_action)
        
        # 添加退出快捷键 (Esc)
        self.exit_fullscreen_action = QAction(self)
        self.exit_fullscreen_action.setShortcut(QKeySequence("Esc"))
        self.exit_fullscreen_action.triggered.connect(self.exit_fullscreen)
        self.addAction(self.exit_fullscreen_action)
        
        # 启动时进入全屏模式
        QTimer.singleShot(100, self.enter_fullscreen)

    def enter_fullscreen(self):
        """进入全屏模式"""
        self.showFullScreen()
        self.fullscreen_mode = True
        self.fullscreen_btn.setText("退出全屏")
        self.status_label.setText("按 Esc 键退出全屏模式")
        
        # 调整画布大小以适应全屏
        self.adjust_canvas_size()

    def adjust_canvas_size(self):
        """调整画布大小以适应窗口"""
        # 获取窗口大小
        window_size = self.size()
        # 减去状态栏和工具栏的高度
        canvas_height = window_size.height() - self.status_label.height() - self.toolbar.height()
        
        # 调整画布大小
        self.canvas.resize_canvas(window_size.width(), canvas_height)
        self.canvas.setFixedSize(window_size.width(), canvas_height)

    def create_toolbar(self):
        self.toolbar = QToolBar("工具栏")
        self.toolbar.setMovable(False)
        self.addToolBar(self.toolbar)
        
        # 模式选择
        mode_group = QButtonGroup(self)
        
        # 画笔模式按钮
        self.pen_mode_btn = QRadioButton("画笔")
        self.pen_mode_btn.setChecked(True)
        self.pen_mode_btn.toggled.connect(self.set_pen_mode)
        mode_group.addButton(self.pen_mode_btn)
        self.toolbar.addWidget(self.pen_mode_btn)
        
        # 橡皮擦模式按钮
        self.eraser_mode_btn = QRadioButton("橡皮擦")
        self.eraser_mode_btn.toggled.connect(self.set_eraser_mode)
        mode_group.addButton(self.eraser_mode_btn)
        self.toolbar.addWidget(self.eraser_mode_btn)
        
        self.toolbar.addSeparator()
        
        # 清除按钮
        clear_btn = QPushButton("清除画布")
        clear_btn.clicked.connect(self.clear_canvas)
        self.toolbar.addWidget(clear_btn)
        
        self.toolbar.addSeparator()
        
        # 颜色预览
        self.color_preview = QLabel()
        self.color_preview.setFixedSize(24, 24)
        self.color_preview.setStyleSheet(f"background-color: {self.current_color.name()}; border: 1px solid #000;")
        self.toolbar.addWidget(self.color_preview)
        
        # 颜色选择
        color_btn = QPushButton("选择颜色")
        color_btn.clicked.connect(self.choose_color)
        self.toolbar.addWidget(color_btn)
        
        self.toolbar.addSeparator()
        
        # 画笔大小
        self.toolbar.addWidget(QLabel("画笔大小:"))
        
        self.pen_size_spin = QSpinBox()
        self.pen_size_spin.setRange(1, 30)
        self.pen_size_spin.setValue(self.current_size)
        self.pen_size_spin.valueChanged.connect(self.set_pen_size)
        self.toolbar.addWidget(self.pen_size_spin)
        
        self.toolbar.addSeparator()
        
        # 橡皮擦大小
        self.toolbar.addWidget(QLabel("橡皮擦大小:"))
        
        self.eraser_size_spin = QSpinBox()
        self.eraser_size_spin.setRange(5, 50)
        self.eraser_size_spin.setValue(self.eraser_size)
        self.eraser_size_spin.valueChanged.connect(self.set_eraser_size)
        self.toolbar.addWidget(self.eraser_size_spin)
        
        self.toolbar.addSeparator()
        
        # 背景选项
        self.bg_toggle = QPushButton("透明背景")
        self.bg_toggle.setCheckable(True)
        self.bg_toggle.setChecked(self.transparent_bg)
        self.bg_toggle.clicked.connect(self.toggle_background)
        self.toolbar.addWidget(self.bg_toggle)
        
        # 灵活的空间
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.toolbar.addWidget(spacer)
        
        # 全屏按钮
        self.fullscreen_btn = QPushButton("退出全屏")
        self.fullscreen_btn.setCheckable(True)
        self.fullscreen_btn.setChecked(True)
        self.fullscreen_btn.clicked.connect(self.toggle_fullscreen)
        self.toolbar.addWidget(self.fullscreen_btn)
        
        # 保存按钮
        save_btn = QPushButton("保存图片")
        save_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 5px 15px;")
        save_btn.clicked.connect(self.save_image)
        self.toolbar.addWidget(save_btn)
    
    def choose_color(self):
        color = QColorDialog.getColor(initial=self.current_color, parent=self)
        if color.isValid():
            self.current_color = color
            self.canvas.set_pen_color(color)
            self.color_preview.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #000;")
            self.update_status()
    
    def set_pen_size(self, size):
        self.current_size = size
        self.canvas.set_pen_width(size)
        self.update_status()
    
    def set_eraser_size(self, size):
        self.eraser_size = size
        self.canvas.set_eraser_width(size)
        self.update_status()
    
    def set_pen_mode(self, enabled):
        if enabled:
            self.canvas.set_eraser_mode(False)
            self.update_status()
    
    def set_eraser_mode(self, enabled):
        if enabled:
            self.canvas.set_eraser_mode(True)
            self.update_status()
    
    def clear_canvas(self):
        self.canvas.clear_canvas()
        self.update_status("画布已清除")
    
    def toggle_background(self):
        """切换背景透明/不透明选项"""
        self.transparent_bg = self.bg_toggle.isChecked()
        bg_text = "透明" if self.transparent_bg else "白色"
        self.bg_toggle.setText(f"{bg_text}背景")
        self.update_status()
    
    def toggle_fullscreen(self):
        """切换全屏模式"""
        self.fullscreen_mode = not self.fullscreen_mode
        
        if self.fullscreen_mode:
            self.showFullScreen()
            self.fullscreen_btn.setText("退出全屏")
            self.status_label.setText("按 Esc 键退出全屏模式")
        else:
            self.showNormal()
            self.fullscreen_btn.setText("全屏")
            self.update_status()
        
        # 调整画布大小
        self.adjust_canvas_size()
    
    def exit_fullscreen(self):
        """退出全屏模式"""
        if self.fullscreen_mode:
            self.toggle_fullscreen()
    
    def save_image(self):
        try:
            # 获取桌面路径
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
            
            # 创建文件名
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            bg_text = "透明" if self.transparent_bg else "白色"
            filename = f"手写笔记_{timestamp}_{bg_text}背景.png"
            filepath = os.path.join(desktop_path, filename)
            
            # 保存图片
            if self.canvas.save_to_image(filepath):
                self.update_status(f"图片已保存到桌面: {filename}")
            else:
                self.update_status("保存失败，请重试")
        except Exception as e:
            self.update_status(f"错误: {str(e)}")
    
    def update_status(self, message=None):
        if message:
            self.status_label.setText(f"状态: {message}")
        else:
            mode = "橡皮擦" if self.eraser_mode_btn.isChecked() else "画笔"
            color = self.current_color.name()
            pen_size = self.pen_size_spin.value()
            eraser_size = self.eraser_size_spin.value()
            bg_text = "透明" if self.transparent_bg else "白色"
            
            status = f"模式:{mode} | "
            if mode == "画笔":
                status += f"颜色:{color} | 粗细:{pen_size}px | "
            else:
                status += f"大小:{eraser_size}px | "
            status += f"背景:{bg_text}"
            
            self.status_label.setText(f"状态: {status}")
    
    def resizeEvent(self, event):
        """窗口大小改变时调整画布大小"""
        super().resizeEvent(event)
        self.adjust_canvas_size()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HandwritingApp()
    window.show()
    sys.exit(app.exec_())