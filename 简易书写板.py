import sys
import os
import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, 
                             QToolBar, QAction, QColorDialog, QFileDialog,
                             QSpinBox, QHBoxLayout, QPushButton, QSizePolicy, 
                             QVBoxLayout, QButtonGroup, QRadioButton, QMessageBox,
                             QLineEdit, QStackedWidget)
from PyQt5.QtGui import (QPainter, QPen, QColor, QImage, QPixmap, 
                         QIcon, QBrush, QLinearGradient, QKeySequence, QFont,
                         QFontMetrics)
from PyQt5.QtCore import Qt, QSize, QPoint, QRect

class TianZiGeCanvas(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 固定画布大小
        self.canvas_size = 600
        self.grid_size = 100  # 田字格大小
        
        # 创建画布 - 使用支持透明度的格式
        self.canvas = QImage(self.canvas_size, self.canvas_size, QImage.Format_ARGB32)
        # 初始填充为透明
        self.canvas.fill(Qt.transparent)
        self.setPixmap(QPixmap.fromImage(self.canvas))
        
        # 画笔设置
        self.pen_color = QColor(Qt.black)
        self.pen_width = 25
        self.drawing = False
        self.last_point = QPoint()
        
        # 橡皮擦设置
        self.eraser_mode = False
        self.eraser_color = QColor(Qt.transparent)
        self.eraser_width = 40
        
        # 田字格设置
        self.grid_color = QColor(200, 200, 255, 150)  # 浅蓝色，半透明
        
        # 设置固定大小
        self.setFixedSize(self.canvas_size, self.canvas_size)
        
        # 启用鼠标跟踪
        self.setMouseTracking(True)
        
        # 设置背景为白色
        self.setStyleSheet("background-color: white;")

    def paintEvent(self, event):
        """绘制田字格背景"""
        super().paintEvent(event)
        
        # 创建田字格
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制外边框
        painter.setPen(QPen(self.grid_color, 2))
        painter.drawRect(0, 0, self.width()-1, self.height()-1)
        
        # 计算网格数量
        grid_count_x = self.width() // self.grid_size
        grid_count_y = self.height() // self.grid_size
        
        # 绘制网格线
        painter.setPen(QPen(self.grid_color, 1))
        
        # 水平线
        for i in range(1, grid_count_y):
            y = i * self.grid_size
            painter.drawLine(0, y, self.width(), y)
            
            # 在中心线上加粗
            if i == grid_count_y // 2:
                painter.setPen(QPen(self.grid_color, 2))
                painter.drawLine(0, y, self.width(), y)
                painter.setPen(QPen(self.grid_color, 1))
        
        # 垂直线
        for i in range(1, grid_count_x):
            x = i * self.grid_size
            painter.drawLine(x, 0, x, self.height())
            
            # 在中心线上加粗
            if i == grid_count_x // 2:
                painter.setPen(QPen(self.grid_color, 2))
                painter.drawLine(x, 0, x, self.height())
                painter.setPen(QPen(self.grid_color, 1))
        
        painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = True
            self.last_point = event.pos()
            
    def mouseMoveEvent(self, event):
        if self.drawing and event.buttons() & Qt.LeftButton:
            # 绘制到画布上
            painter = QPainter(self.canvas)
            painter.setRenderHint(QPainter.Antialiasing)
            
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
        self.update()  # 重绘田字格
    
    def set_pen_color(self, color):
        self.pen_color = color
        
    def set_pen_width(self, width):
        self.pen_width = width
        
    def set_eraser_width(self, width):
        self.eraser_width = width
        
    def set_eraser_mode(self, enabled):
        self.eraser_mode = enabled
        
    def get_image(self):
        """获取当前画布图像"""
        return self.canvas.copy()
    
    def has_content(self):
        """检查画布上是否有内容"""
        # 检查是否有非透明像素
        for x in range(self.canvas.width()):
            for y in range(self.canvas.height()):
                pixel = self.canvas.pixelColor(x, y)
                if pixel.alpha() > 0:
                    return True
        return False
    
    def set_image(self, image):
        """设置画布为指定的图像"""
        if image:
            self.canvas = image.copy()
            self.setPixmap(QPixmap.fromImage(self.canvas))
        else:
            self.clear_canvas()

class ChineseWritingApp(QMainWindow):
    def __init__(self):
        super().__init__()
        # 初始化颜色属性 - 使用QColor对象
        self.current_color = QColor(Qt.black)
        self.current_size = 25
        self.eraser_size = 40
        
        # 存储所有汉字图像
        self.characters = []
        self.current_index = 0  # 当前显示的汉字索引
        
        # 设置窗口标题
        self.setWindowTitle("简易书写板")
        self.setGeometry(100, 100, 800, 600)
        
        # 创建主部件和布局
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # 创建手写模式容器
        self.handwriting_container = QWidget()
        self.handwriting_layout = QVBoxLayout(self.handwriting_container)
        self.handwriting_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建画布容器
        self.canvas_container = QWidget()
        self.canvas_layout = QVBoxLayout(self.canvas_container)
        self.canvas_layout.setContentsMargins(0, 0, 0, 0)
        self.canvas_layout.setAlignment(Qt.AlignCenter)
        
        # 创建画布
        self.canvas = TianZiGeCanvas()
        self.canvas_layout.addWidget(self.canvas)
        
        self.handwriting_layout.addWidget(self.canvas_container)
        
        # 创建状态栏
        self.status_label = QLabel("准备就绪 | 模式:手写 | 颜色:黑色 | 粗细:25px")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFixedHeight(30)
        self.status_label.setStyleSheet("background-color: #f0f0f0; border-top: 1px solid #cccccc;")
        
        self.layout.addWidget(self.handwriting_container)
        self.layout.addWidget(self.status_label)
        
        # 创建工具栏
        self.create_toolbar()
        
        # 添加快捷键
        self.add_shortcuts()
        
        # 初始化汉字计数器
        self.character_count = 0
        self.update_status("请书写第一个汉字")

    def add_shortcuts(self):
        """添加快捷键"""
        # 退出快捷键 (Esc)
        self.exit_action = QAction(self)
        self.exit_action.setShortcut(QKeySequence("Esc"))
        self.exit_action.triggered.connect(self.close)
        self.addAction(self.exit_action)
        
        # 下一个汉字快捷键 (Space)
        self.next_action = QAction(self)
        self.next_action.setShortcut(QKeySequence("Space"))
        self.next_action.triggered.connect(self.next_character)
        self.addAction(self.next_action)
        
        # 下一个汉字快捷键 (PgDn)
        self.pgdown_action = QAction(self)
        self.pgdown_action.setShortcut(QKeySequence("PgDown"))
        self.pgdown_action.triggered.connect(self.next_character)
        self.addAction(self.pgdown_action)
        
        # 上一个汉字快捷键 (PgUp)
        self.pgup_action = QAction(self)
        self.pgup_action.setShortcut(QKeySequence("PgUp"))
        self.pgup_action.triggered.connect(self.prev_character)
        self.addAction(self.pgup_action)
        
        # 保存当前修改 (Ctrl+S)
        self.save_action = QAction(self)
        self.save_action.setShortcut(QKeySequence("Ctrl+S"))
        self.save_action.triggered.connect(self.save_current)
        self.addAction(self.save_action)

    def create_toolbar(self):
        self.toolbar = QToolBar("工具栏")
        self.toolbar.setMovable(False)
        self.addToolBar(self.toolbar)
        
        # 清除按钮
        clear_btn = QPushButton("清除当前")
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
        self.pen_size_spin.setRange(10, 50)
        self.pen_size_spin.setValue(self.current_size)
        self.pen_size_spin.valueChanged.connect(self.set_pen_size)
        self.toolbar.addWidget(self.pen_size_spin)
        
        self.toolbar.addSeparator()
        
        # 橡皮擦大小
        self.toolbar.addWidget(QLabel("橡皮擦大小:"))
        
        self.eraser_size_spin = QSpinBox()
        self.eraser_size_spin.setRange(20, 80)
        self.eraser_size_spin.setValue(self.eraser_size)
        self.eraser_size_spin.valueChanged.connect(self.set_eraser_size)
        self.toolbar.addWidget(self.eraser_size_spin)
        
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
        
        # 灵活的空间
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.toolbar.addWidget(spacer)
        
        # 上一个汉字按钮
        prev_btn = QPushButton("上一个汉字")
        prev_btn.setStyleSheet("background-color: #FF9800; color: white; padding: 5px 15px;")
        prev_btn.clicked.connect(self.prev_character)
        self.toolbar.addWidget(prev_btn)
        
        # 下一个汉字按钮
        next_btn = QPushButton("下一个汉字")
        next_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 5px 15px;")
        next_btn.clicked.connect(self.next_character)
        self.toolbar.addWidget(next_btn)
        
        # 完成按钮
        finish_btn = QPushButton("完成")
        finish_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 5px 15px;")
        finish_btn.clicked.connect(self.finish_writing)
        self.toolbar.addWidget(finish_btn)
    
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
    
    def save_current(self):
        """保存当前汉字到历史记录"""
        if not self.canvas.has_content():
            return
            
        # 如果当前索引在有效范围内，则更新该汉字
        if 0 <= self.current_index < len(self.characters):
            # 更新当前汉字
            self.characters[self.current_index] = self.canvas.get_image()
            self.update_status(f"已保存当前汉字的修改（第 {self.current_index + 1} 个）")
        elif self.current_index == len(self.characters):
            # 添加新汉字
            current_image = self.canvas.get_image()
            self.characters.append(current_image)
            self.character_count = len(self.characters)
            self.update_status(f"已添加新汉字（共 {self.character_count} 个汉字）")
    
    def next_character(self):
        """保存当前汉字并准备下一个"""
        # 保存当前汉字
        self.save_current()
        
        # 准备下一个汉字
        self.current_index = min(self.current_index + 1, len(self.characters))
        
        # 如果当前索引在历史记录范围内，则显示该汉字
        if self.current_index < len(self.characters):
            self.canvas.set_image(self.characters[self.current_index])
            self.update_status(f"显示汉字 {self.current_index + 1}/{len(self.characters)}")
        else:
            # 新汉字，清空画布
            self.canvas.clear_canvas()
            self.update_status(f"准备书写新汉字（第 {self.current_index + 1} 个）")
    
    def prev_character(self):
        """返回上一个汉字"""
        # 保存当前汉字
        self.save_current()
        
        # 准备上一个汉字
        if self.current_index > 0:
            self.current_index -= 1
            self.canvas.set_image(self.characters[self.current_index])
            self.update_status(f"显示汉字 {self.current_index + 1}/{len(self.characters)}")
        else:
            self.update_status("已是第一个汉字")
    
    def finish_writing(self):
        """完成书写，水平拼接所有汉字成一句话"""
        # 保存当前汉字
        self.save_current()
        
        if not self.characters:
            QMessageBox.warning(self, "提示", "请先添加至少一个汉字")
            return
        
        try:
            # 获取桌面路径
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
            
            # 创建文件名
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"汉字句子_{timestamp}.png"
            filepath = os.path.join(desktop_path, filename)
            
            # 水平拼接汉字
            self.combine_characters_horizontally(filepath)
            
            # 显示成功消息
            self.update_status(f"已保存到桌面: {filename}")
            QMessageBox.information(self, "完成", f"汉字句子已保存到桌面:\n{filename}")
            
            # 重置应用
            self.characters = []
            self.current_index = -1
            self.character_count = 0
            self.canvas.clear_canvas()
            self.update_status("请添加第一个汉字")
            
        except Exception as e:
            self.update_status(f"错误: {str(e)}")
            QMessageBox.critical(self, "错误", f"保存失败: {str(e)}")
    
    def combine_characters_horizontally(self, filepath):
        """将所有汉字水平拼接成一句话"""
        # 计算总宽度和最大高度
        total_width = sum(img.width() for img in self.characters)
        max_height = max(img.height() for img in self.characters)
        
        # 创建新图像
        combined = QImage(total_width, max_height, QImage.Format_ARGB32)
        combined.fill(Qt.transparent)
        
        # 绘制所有汉字
        painter = QPainter(combined)
        x_offset = 0
        for img in self.characters:
            # 垂直居中绘制每个汉字
            y_offset = (max_height - img.height()) // 2
            painter.drawImage(x_offset, y_offset, img)
            x_offset += img.width()
        painter.end()
        
        # 保存图像
        combined.save(filepath, "PNG")
    
    def update_status(self, message=None):
        if message:
            self.status_label.setText(f"状态: {message}")
        else:
            mode = "橡皮擦" if self.eraser_mode_btn.isChecked() else "画笔"
            color = self.current_color.name()
            pen_size = self.pen_size_spin.value()
            eraser_size = self.eraser_size_spin.value()
            
            status = f"模式:手写 | 工具:{mode} | "
            if mode == "画笔":
                status += f"颜色:{color} | 粗细:{pen_size}px"
            else:
                status += f"大小:{eraser_size}px"
            
            # 添加汉字数量信息
            if self.characters:
                status += f" | 汉字: {len(self.characters)}个"
                if self.current_index >= 0:
                    status += f" (当前: {self.current_index + 1}/{len(self.characters)})"
            else:
                status += " | 尚未保存汉字"
            
            self.status_label.setText(f"状态: {status}")

if __name__ == "__main__":
    # 添加异常处理
    try:
        app = QApplication(sys.argv)
        window = ChineseWritingApp()
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        print(f"应用程序错误: {str(e)}")
        import traceback
        traceback.print_exc()
        QMessageBox.critical(None, "应用程序错误", f"发生错误: {str(e)}")