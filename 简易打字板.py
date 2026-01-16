import sys
import os
import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, 
                             QToolBar, QAction, QColorDialog, QFileDialog,
                             QSpinBox, QHBoxLayout, QPushButton, QSizePolicy, 
                             QVBoxLayout, QButtonGroup, QRadioButton, QMessageBox,
                             QLineEdit, QStackedWidget, QTextEdit, QComboBox, QCheckBox,
                             QGroupBox, QGridLayout)
from PyQt5.QtGui import (QPainter, QPen, QColor, QImage, QPixmap, 
                         QIcon, QBrush, QLinearGradient, QKeySequence, QFont,
                         QFontMetrics, QTextCharFormat, QTextCursor)
from PyQt5.QtCore import Qt, QSize, QPoint, QRect, QEvent

class ChineseWritingApp(QMainWindow):
    def __init__(self):
        super().__init__()
        # 初始化颜色属性
        self.font_color = QColor(Qt.black)
        
        # 存储所有汉字图像（现在是二维列表，用于存储多行）
        self.characters = []  # 改为二维列表
        self.current_line = []  # 当前正在编辑的行
        
        # 字体设置 - 使用固定字体
        self.font = QFont("SimSun", 100)  # 默认字体：宋体
        
        # 对齐模式：0-中线对齐，1-左端对齐
        self.alignment_mode = 0
        
        # 背景模式：0-白色，1-透明
        self.background_mode = 0
        
        # 设置窗口标题
        self.setWindowTitle("简易打字板")
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet("""
            background-color: #f5f5f5;
            font-family: "Microsoft YaHei";
        """)  # 设置主窗口背景色和字体
        
        # 创建主部件和布局
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(15)
        
        # 创建标题栏
        self.header = QLabel("简易打字板")
        self.header.setStyleSheet("""
            color: #2c3e50;
            font-size: 24px;
            font-weight: bold;
            padding: 10px;
            qproperty-alignment: 'AlignCenter';
        """)
        self.layout.addWidget(self.header)
        
        # 创建输入区域
        input_group = QGroupBox("输入汉字")
        input_group.setStyleSheet("""
            QGroupBox {
                background-color: white;
                border-radius: 8px;
                padding: 15px;
                border: 1px solid #dcdcdc;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        input_layout = QVBoxLayout(input_group)
        
        # 输入框
        self.text_input = QTextEdit()
        self.text_input.setStyleSheet("""
            font-size: 24px; 
            padding: 15px; 
            border: 1px solid #ccc; 
            border-radius: 8px;
            background-color: #fff;
        """)
        self.text_input.setPlaceholderText("在此输入汉字...按Enter键添加整行")
        self.text_input.setMinimumHeight(100)
        input_layout.addWidget(self.text_input)
        
        # 添加行按钮
        self.add_text_button = QPushButton("添加整行")
        self.add_text_button.setStyleSheet("""
            background-color: #3498db; 
            color: white; 
            font-size: 14px; 
            padding: 10px;
            border-radius: 6px;
            font-weight: bold;
        """)
        self.add_text_button.clicked.connect(self.add_text_line)
        input_layout.addWidget(self.add_text_button)
        
        self.layout.addWidget(input_group)
        
        # 创建设置区域
        settings_group = QGroupBox("设置")
        settings_group.setStyleSheet("""
            QGroupBox {
                background-color: white;
                border-radius: 8px;
                padding: 15px;
                border: 1px solid #dcdcdc;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        settings_layout = QGridLayout(settings_group)
        settings_layout.setVerticalSpacing(15)
        settings_layout.setHorizontalSpacing(15)
        
        # 第一行设置
        # 字体大小
        size_label = QLabel("字体大小:")
        settings_layout.addWidget(size_label, 0, 0)
        
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(20, 200)
        self.font_size_spin.setValue(100)
        self.font_size_spin.valueChanged.connect(self.update_font_size)
        self.font_size_spin.setStyleSheet("padding: 5px;")
        settings_layout.addWidget(self.font_size_spin, 0, 1)
        
        # 字体颜色
        color_label = QLabel("字体颜色:")
        settings_layout.addWidget(color_label, 0, 2)
        
        self.font_color_button = QPushButton("选择")
        self.font_color_button.setStyleSheet("padding: 6px;")
        self.font_color_button.clicked.connect(self.choose_font_color)
        settings_layout.addWidget(self.font_color_button, 0, 3)
        
        self.font_color_preview = QLabel()
        self.font_color_preview.setFixedSize(20, 20)
        # 初始化时使用黑色
        self.font_color_preview.setStyleSheet("background-color: #000000; border: 1px solid #ccc; border-radius: 10px;")
        settings_layout.addWidget(self.font_color_preview, 0, 4)
        
        # 第二行设置
        # 对齐方式
        alignment_label = QLabel("对齐方式:")
        settings_layout.addWidget(alignment_label, 1, 0)
        
        self.alignment_combo = QComboBox()
        self.alignment_combo.addItem("中线对齐")
        self.alignment_combo.addItem("左端对齐")
        self.alignment_combo.setStyleSheet("padding: 6px;")
        self.alignment_combo.currentIndexChanged.connect(self.set_alignment_mode)
        settings_layout.addWidget(self.alignment_combo, 1, 1, 1, 2)
        
        # 背景选择
        background_label = QLabel("输出背景:")
        settings_layout.addWidget(background_label, 1, 3)
        
        self.background_combo = QComboBox()
        self.background_combo.addItem("白色背景")
        self.background_combo.addItem("透明背景")
        self.background_combo.setStyleSheet("padding: 6px;")
        self.background_combo.currentIndexChanged.connect(self.set_background_mode)
        settings_layout.addWidget(self.background_combo, 1, 4)
        
        # 第三行设置
        # 文字颜色按钮
        text_color_label = QLabel("选中文字颜色:")
        settings_layout.addWidget(text_color_label, 2, 0)
        
        self.text_color_button = QPushButton("设置")
        self.text_color_button.setStyleSheet("padding: 6px;")
        self.text_color_button.clicked.connect(self.set_text_color)
        settings_layout.addWidget(self.text_color_button, 2, 1)
        
        self.text_color_preview = QLabel()
        self.text_color_preview.setFixedSize(20, 20)
        # 初始化时使用黑色
        self.text_color_preview.setStyleSheet("background-color: #000000; border: 1px solid #ccc; border-radius: 10px;")
        settings_layout.addWidget(self.text_color_preview, 2, 2)
        
        # 已添加统计
        stats_label = QLabel("已添加:")
        settings_layout.addWidget(stats_label, 2, 3)
        
        self.stats_value = QLabel("0行, 0字")
        self.stats_value.setStyleSheet("font-weight: bold;")
        settings_layout.addWidget(self.stats_value, 2, 4)
        
        self.layout.addWidget(settings_group)
        
        # 创建操作按钮区域
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(15)
        
        # 完成按钮
        self.finish_btn = QPushButton("完成书写")
        self.finish_btn.setStyleSheet("""
            background-color: #27ae60; 
            color: white; 
            font-size: 16px; 
            padding: 12px;
            border-radius: 6px;
            font-weight: bold;
        """)
        self.finish_btn.clicked.connect(self.finish_writing)
        buttons_layout.addWidget(self.finish_btn)
        
        # 清除按钮
        self.clear_btn = QPushButton("清除所有")
        self.clear_btn.setStyleSheet("""
            background-color: #e74c3c; 
            color: white; 
            font-size: 16px; 
            padding: 12px;
            border-radius: 6px;
            font-weight: bold;
        """)
        self.clear_btn.clicked.connect(self.clear_all)
        buttons_layout.addWidget(self.clear_btn)
        
        self.layout.addLayout(buttons_layout)
        
        # 状态信息
        self.status_label = QLabel("准备就绪")
        self.status_label.setStyleSheet("color: #7f8c8d; font-size: 12px; padding-top: 10px;")
        self.layout.addWidget(self.status_label)
        
        # 初始化汉字计数器
        self.character_count = 0
        self.line_count = 0
        
        # 输入框的默认颜色
        self.text_input_color = self.font_color

        # 设置输入框焦点
        self.text_input.setFocus()

    def keyPressEvent(self, event):
        """处理键盘事件"""
        if event.key() in (Qt.Key_Return, Qt.Key_Enter) and self.text_input.hasFocus():
            self.add_text_line()
        else:
            super().keyPressEvent(event)
    
    def set_alignment_mode(self, index):
        """设置对齐方式"""
        self.alignment_mode = index
        self.update_status(f"对齐方式已设置为: {'中线对齐' if index == 0 else '左端对齐'}")
    
    def set_background_mode(self, index):
        """设置背景模式"""
        self.background_mode = index
        self.update_status(f"背景已设置为: {'白色背景' if index == 0 else '透明背景'}")
    
    def choose_font_color(self):
        """选择字体颜色"""
        color = QColorDialog.getColor(initial=self.font_color, parent=self)
        if color.isValid():
            self.font_color = color
            self.font_color_preview.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #ccc; border-radius: 10px;")
            self.update_status(f"字体颜色已设置为: {color.name()}")
    
    def set_text_color(self):
        """设置输入框中选中文字的颜色"""
        cursor = self.text_input.textCursor()
        if not cursor.hasSelection():
            QMessageBox.information(self, "提示", "请先选中要设置颜色的文字")
            return
            
        color = QColorDialog.getColor(initial=self.text_input_color, parent=self)
        if color.isValid():
            self.text_input_color = color
            self.text_color_preview.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #ccc; border-radius: 10px;")
            
            # 应用颜色到选中的文字
            format = QTextCharFormat()
            format.setForeground(color)
            cursor.mergeCharFormat(format)
            
            self.update_status(f"选中文字颜色已设置为: {color.name()}")
    
    def update_font_size(self, size):
        """更新字体大小"""
        self.font.setPointSize(size)
        self.update_status(f"字体大小已设置为: {size}px")
        
    def update_status(self, message=None):
        """更新状态栏"""
        if message:
            self.status_label.setText(f"状态: {message}")
        else:
            self.status_label.setText("状态: 就绪")

    def create_char_image(self, char, color=None):
        """创建单个汉字的图片"""
        if color is None:
            color = self.font_color
        
        # 计算字体大小
        font_metrics = QFontMetrics(self.font)
        text_width = font_metrics.width(char)
        text_height = font_metrics.height()
        
        # 创建图片（添加一些边距）
        padding = 20
        image_width = text_width + padding * 2
        image_height = text_height + padding * 2
        
        # 创建透明背景图片
        image = QImage(image_width, image_height, QImage.Format_ARGB32)
        image.fill(Qt.transparent)
        
        # 绘制汉字
        painter = QPainter(image)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setFont(self.font)
        painter.setPen(color)
        
        # 计算绘制位置（居中）
        x = (image_width - text_width) // 2
        y = padding + font_metrics.ascent()  # ascent()获取字体的上升高度
        
        painter.drawText(x, y, char)
        painter.end()
        
        return image

    def add_text_line(self):
        """将输入框中的当前行转化为图片并添加到当前行列表"""
        # 获取文本内容
        doc = self.text_input.document()
        text = doc.toPlainText().strip()
        if not text:
            self.update_status("请输入文字后再添加")
            return
        
        # 创建一个空行
        line = []
        
        # 遍历文档中的所有文本块
        block = doc.begin()
        while block.isValid():
            # 遍历块中的每个文本片段
            block_text = block.text()
            for i, char in enumerate(block_text):
                # 获取字符的位置
                position = block.position() + i
                
                # 创建一个光标以获取字符的格式
                cursor = QTextCursor(doc)
                cursor.setPosition(position)
                cursor.movePosition(QTextCursor.NextCharacter, QTextCursor.KeepAnchor)
                
                # 获取字符的颜色
                char_format = cursor.charFormat()
                color = char_format.foreground().color()
                if not color.isValid():
                    color = self.font_color
                
                # 创建汉字图片
                char_image = self.create_char_image(char, color)
                line.append(char_image)
                
                # 更新计数器
                self.character_count += 1
            
            block = block.next()
        
        # 添加到二维列表
        if line:
            self.characters.append(line)
            self.line_count += 1
            self.stats_value.setText(f"{self.line_count}行, {self.character_count}字")
            self.update_status(f"已添加第 {self.line_count} 行，共 {self.character_count} 个字")
        
        # 清空输入框
        self.text_input.clear()
        self.text_input_color = self.font_color  # 重置为默认颜色
        self.text_color_preview.setStyleSheet(f"background-color: {self.font_color.name()}; border: 1px solid #ccc; border-radius: 10px;")
        
        # 设置焦点回输入框
        self.text_input.setFocus()

    def clear_all(self):
        """清除所有内容"""
        reply = QMessageBox.question(self, '确认清除', 
                                    '确定要清除所有输入的内容吗？此操作不可撤销。',
                                    QMessageBox.Yes | QMessageBox.No, 
                                    QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.characters = []
            self.character_count = 0
            self.line_count = 0
            self.text_input.clear()
            self.text_input_color = self.font_color
            self.text_color_preview.setStyleSheet(f"background-color: {self.font_color.name()}; border: 1px solid #ccc; border-radius: 10px;")
            self.stats_value.setText("0行, 0字")
            self.update_status("所有内容已清除")
            
            # 设置焦点回输入框
            self.text_input.setFocus()
        else:
            self.update_status("清除操作已取消")

    def finish_writing(self):
        """完成书写，垂直拼接所有行成一段文字"""
        if not self.characters:
            QMessageBox.warning(self, "提示", "请先添加至少一行汉字")
            return
        
        try:
            # 获取桌面路径
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
            
            # 创建文件名
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"汉字书写_{timestamp}.png"
            filepath = os.path.join(desktop_path, filename)
            
            # 垂直拼接所有行
            self.combine_lines_vertically(filepath)
            
            # 显示成功消息
            QMessageBox.information(self, "完成", 
                                  f"汉字书写已保存到桌面:\n{filename}\n\n"
                                  f"行数: {self.line_count}\n"
                                  f"字数: {self.character_count}\n"
                                  f"背景: {'白色' if self.background_mode == 0 else '透明'}")
            
            # 重置应用
            self.characters = []
            self.character_count = 0
            self.line_count = 0
            self.text_input.clear()
            self.stats_value.setText("0行, 0字")
            self.update_status("请添加第一行汉字")
            
            # 设置焦点回输入框
            self.text_input.setFocus()
            
        except Exception as e:
            self.update_status(f"错误: {str(e)}")
            QMessageBox.critical(self, "错误", f"保存失败: {str(e)}")
    
    def combine_lines_vertically(self, filepath):
        """将所有行垂直拼接成一段文字"""
        # 计算总高度和最大行宽度
        max_line_width = 0
        total_height = 0
        
        # 第一遍：计算最大行宽和总高度
        for line in self.characters:
            line_width = sum(img.width() for img in line)
            line_height = max(img.height() for img in line) if line else 0
            
            if line_width > max_line_width:
                max_line_width = line_width
                
            total_height += line_height
        
        # 添加行间距（行高的20%）
        line_spacing = 30  # 固定行间距
        total_height += line_spacing * (len(self.characters) - 1)
        
        # 添加额外边距
        padding = 50
        total_height += padding * 2
        max_line_width += padding * 2
        
        # 创建新图像
        combined = QImage(max_line_width, total_height, QImage.Format_ARGB32)
        
        # 根据选择的背景模式设置背景
        if self.background_mode == 0:  # 白色背景
            combined.fill(Qt.white)
        else:  # 透明背景
            combined.fill(Qt.transparent)
        
        # 绘制所有行
        painter = QPainter(combined)
        painter.setRenderHint(QPainter.Antialiasing)
        y_offset = padding
        
        for line in self.characters:
            if not line:
                continue
                
            # 计算行高（取行中图片的最大高度）
            line_height = max(img.height() for img in line)
            
            # 计算行总宽度
            line_width = sum(img.width() for img in line)
            
            # 计算水平偏移
            if self.alignment_mode == 0:  # 中线对齐
                x_offset = (max_line_width - line_width) // 2
            else:  # 左端对齐
                x_offset = padding
                
            for img in line:
                # 垂直居中
                y_pos = y_offset + (line_height - img.height()) // 2
                painter.drawImage(x_offset, y_pos, img)
                x_offset += img.width()
            
            # 移动到下一行
            y_offset += line_height + line_spacing
        
        painter.end()
        
        # 保存图像
        combined.save(filepath, "PNG")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 设置应用样式
    app.setStyle("Fusion")
    
    # 设置全局字体
    font = QFont()
    font.setFamily("Microsoft YaHei")
    font.setPointSize(10)
    app.setFont(font)
    
    window = ChineseWritingApp()
    window.show()
    sys.exit(app.exec_())