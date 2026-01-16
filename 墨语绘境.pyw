import pygame
import sys
import json
import os
import tkinter as tk
from tkinter import filedialog
import random
import math
import codecs

# 初始化pygame
pygame.init()

# 获取当前屏幕信息
screen_info = pygame.display.Info()
SCREEN_WIDTH = screen_info.current_w
SCREEN_HEIGHT = screen_info.current_h

# 创建全屏窗口
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("WeChat Chat Simulator")

# 颜色定义
BACKGROUND = (240, 240, 240)
NARRATOR_BG = (220, 220, 220)   # 旁白背景色
TEXT_COLOR = (0, 0, 0)
TIME_COLOR = (150, 150, 150)
HEADER_COLOR = (237, 237, 237)
SEARCH_BAR = (250, 250, 250)
BUTTON_COLOR = (79, 195, 68)  # 微信绿色
BUTTON_HOVER_COLOR = (90, 210, 78)  # 更亮的绿色
EXIT_BUTTON_COLOR = (255, 100, 100)  # 退出按钮颜色
SCROLL_BAR = (200, 200, 200)  # 滚动条颜色
SCROLL_BAR_ACTIVE = (150, 150, 150)  # 滚动条激活颜色
CHOICE_BG = (240, 240, 240)  # 选择背景色
CHOICE_BUTTON = (200, 200, 200)  # 选择按钮颜色
CHOICE_BUTTON_HOVER = (180, 180, 180)  # 选择按钮悬停颜色

# 新增：颜色生成函数
def generate_readable_color(existing_colors=None, min_lightness=0.6):
    """生成随机但可读的颜色，确保足够的亮度"""
    while True:
        # 使用HSV色彩空间更容易控制亮度和饱和度
        h = random.randint(0, 360)  # 色调 (0-360)
        s = random.uniform(0.4, 0.7)  # 饱和度 (40%-70%)
        v = random.uniform(min_lightness, 0.9)  # 亮度 (60%-90%)
        
        # 将HSV转换为RGB
        c = v * s
        x = c * (1 - abs((h / 60) % 2 - 1))
        m = v - c
        
        if 0 <= h < 60:
            r, g, b = c, x, 0
        elif 60 <= h < 120:
            r, g, b = x, c, 0
        elif 120 <= h < 180:
            r, g, b = 0, c, x
        elif 180 <= h < 240:
            r, g, b = 0, x, c
        elif 240 <= h < 300:
            r, g, b = x, 0, c
        else:  # 300 <= h < 360
            r, g, b = c, 0, x
            
        r = int((r + m) * 255)
        g = int((g + m) * 255)
        b = int((b + m) * 255)
        
        # 确保与现有颜色有足够差异
        if existing_colors:
            too_similar = False
            for color in existing_colors:
                # 计算颜色差异
                dr = r - color[0]
                dg = g - color[1]
                db = b - color[2]
                distance = math.sqrt(dr*dr + dg*dg + db*db)
                
                # 如果颜色太相似，重新生成
                if distance < 100:  # 调整阈值以确保足够差异
                    too_similar = True
                    break
            
            if not too_similar:
                return (r, g, b)
        else:
            return (r, g, b)

# 字体
font_small = pygame.font.SysFont("Arial", 14)
font_medium = pygame.font.SysFont("Arial", 16)
font_large = pygame.font.SysFont("Arial", 18, bold=True)
font_xlarge = pygame.font.SysFont("Arial", 24, bold=True)  # 更大的字体用于全屏

# 聊天记录数据结构
class ChatMessage:
    def __init__(self, sender, content, timestamp, is_me, screen_width, my_name):
        self.sender = sender
        self.content = content
        self.timestamp = timestamp
        self.is_me = is_me
        self.rendered_content = []
        self.height = 0
        self.width = 0
        self.my_name = my_name  # 存储当前用户的名称
        self.render_content(screen_width)
    
    def render_content(self, screen_width):
        """Render message content as multi-line text"""
        self.rendered_content = []
        words = self.content.split()
        lines = []
        current_line = ""
        
        # 最大气泡宽度设为屏幕宽度的50%
        max_bubble_width = min(600, screen_width * 0.5)
        
        for word in words:
            test_line = current_line + word + " "
            # 检查文本宽度是否超过最大宽度
            if font_medium.size(test_line)[0] < (max_bubble_width - 40):  # 留出边距
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word + " "
        
        if current_line:
            lines.append(current_line)
        
        # 计算气泡宽度（基于最长的行）
        self.width = 0
        for line in lines:
            rendered_line = font_medium.render(line, True, TEXT_COLOR)
            self.rendered_content.append(rendered_line)
            if rendered_line.get_width() > self.width:
                self.width = rendered_line.get_width()
        
        # 增加边距
        self.width = min(self.width + 40, max_bubble_width)
        
        # 计算消息高度
        # 旁白消息高度较低，普通消息需要显示发送者名称
        if self.sender == "*":
            self.height = len(self.rendered_content) * 24 + 20  # 旁白行高较低
        else:
            self.height = len(self.rendered_content) * 30 + 45  # 普通消息有发送者名称

# 聊天记录模拟器
class WeChatSimulator:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.messages = []
        self.displayed_messages = []
        self.current_index = 0
        self.scroll_offset = 0
        self.target_scroll_offset = 0  # 目标滚动位置（用于平滑滚动）
        self.scroll_speed = 0.1  # 平滑滚动速度因子
        self.loaded = False
        self.chat_name = "No chat history loaded"
        self.my_name = "Me"
        self.other_name = "Friend"
        self.import_button = pygame.Rect(screen_width - 220, screen_height - 40, 200, 30)
        self.exit_button = pygame.Rect(screen_width - 40, 20, 20, 20)  # 添加退出按钮
        self.button_hover = False
        self.exit_button_hover = False
        self.max_bubble_width = min(600, screen_width * 0.5)  # 最大气泡宽度
        self.scroll_bar = pygame.Rect(screen_width - 10, 80, 8, 200)  # 滚动条
        self.dragging_scroll = False  # 是否正在拖动滚动条
        self.scroll_bar_active = False  # 滚动条是否激活（鼠标悬停）
        self.total_chat_height = 0  # 聊天区域总高度
        self.participants = {}  # 存储参与者名称和颜色的映射
        self.color_palette = []  # 存储已使用的颜色
        
        # 分支选择功能新增变量
        self.showing_choices = False  # 是否正在显示选择项
        self.choice_message = None  # 当前的选择消息
        self.choice_buttons = []  # 选择按钮的矩形
        self.choice_results = []  # 选择对应的结果
		
    def load_chat_history(self, file_path):
        """从JSON文件加载聊天记录，支持中文"""
        try:
            # 使用codecs.open确保正确处理中文
            with codecs.open(file_path, 'r', 'utf-8') as f:
                data = json.load(f)
                
            # 使用json.dump确保中文字符正确输出
            # 在实际加载中，我们不需要dump，这里只是为了演示如何正确处理中文
            # 在实际应用中，json.load已经可以正确处理中文
            self.chat_name = data.get("chat_name", "聊天记录")
            self.my_name = data.get("my_name", "我")
            self.other_name = data.get("other_name", "朋友")
            
            # 初始化参与者颜色 - 使用随机颜色生成
            self.participants = {
                self.my_name: (157, 223, 94),  # 自己保持固定颜色
                "*": NARRATOR_BG  # 旁白特殊颜色
            }
            # 添加自己的颜色到调色板
            self.color_palette = [self.participants[self.my_name]]
            
            self.messages = []
            for msg in data.get("messages", []):
                # 检查是否是选择消息
                if "choices" in msg:
                    sender = msg.get("sender", "*")
                    is_me = sender == self.my_name
                    
                    # 创建选择消息对象
                    choice_msg = ChatMessage(
                        sender,
                        msg.get("content", ""),
                        msg.get("timestamp", ""),
                        is_me,
                        self.screen_width,
                        self.my_name
                    )
                    
                    # 添加选择消息的特殊属性
                    choice_msg.is_choice = True
                    choice_msg.choices = msg["choices"]
                    
                    self.messages.append(choice_msg)
                else:
                    sender = msg.get("sender", "未知")
                    is_me = sender == self.my_name
                    
                    # 为其他参与者分配颜色
                    if sender not in self.participants and sender != "*":
                        # 生成新颜色，确保与现有颜色有足够差异
                        new_color = self.generate_readable_color()
                        self.participants[sender] = new_color
                        self.color_palette.append(new_color)
                    
                    self.messages.append(ChatMessage(
                        sender,
                        msg.get("content", ""),
                        msg.get("timestamp", ""),
                        is_me,
                        self.screen_width,
                        self.my_name
                    ))
            
            self.displayed_messages = []
            self.current_index = 0
            self.scroll_offset = 0
            self.target_scroll_offset = 0
            self.loaded = True
            self.showing_choices = False
            return True
        except Exception as e:
            print(f"加载聊天记录失败: {e}")
            return False
    
    def generate_readable_color(self):
        """生成一个易读的颜色，确保与现有颜色有足够差异"""
        import random
        # 生成随机颜色
        color = (random.randint(100, 255), random.randint(100, 255), random.randint(100, 255))
        
        # 检查与现有颜色的差异
        for existing_color in self.color_palette:
            # 计算颜色差异
            diff = sum(abs(c1 - c2) for c1, c2 in zip(color, existing_color))
            if diff < 150:  # 如果差异太小，重新生成
                return self.generate_readable_color()
        
        return color
    
    def show_next_message(self):
        """Show next message"""
        if self.current_index < len(self.messages):
            next_message = self.messages[self.current_index]
            
            # 检查是否是选择消息
            if hasattr(next_message, 'is_choice') and next_message.is_choice:
                self.show_choices(next_message)
                return
            
            self.displayed_messages.append(next_message)
            self.current_index += 1
            
            # 计算聊天区域总高度
            self.calculate_total_height()
            
            # 自动滚动到底部
            self.scroll_to_bottom()
    
    def show_choices(self, message):
        """显示选择项"""
        self.showing_choices = True
        self.choice_message = message
        self.choice_buttons = []
        self.choice_results = []
        
        # 创建选择按钮
        button_height = 40
        button_width = self.screen_width * 0.6
        start_y = self.screen_height - 100 - len(message.choices) * (button_height + 10)
        
        for i, choice in enumerate(message.choices):
            button_y = start_y + i * (button_height + 10)
            button_rect = pygame.Rect(
                (self.screen_width - button_width) // 2,
                button_y,
                button_width,
                button_height
            )
            self.choice_buttons.append(button_rect)
            self.choice_results.append(choice["result"])
    
    def make_choice(self, index):
        """处理用户的选择"""
        if index < 0 or index >= len(self.choice_results):
            return
        
        # 添加选择消息到显示
        self.displayed_messages.append(self.choice_message)
        
        # 添加用户选择
        choice_text = f"{self.choice_message.choices[index]['text']}"
        choice_msg = ChatMessage(
            self.my_name,
            choice_text,
            "",
            True,
            self.screen_width,
            self.my_name
        )
        self.displayed_messages.append(choice_msg)
        
        # 添加选择结果
        result_msg = ChatMessage(
            self.choice_message.sender,
            self.choice_results[index],
            "",
            False,
            self.screen_width,
            self.my_name
        )
        self.displayed_messages.append(result_msg)
        
        # 重置选择状态
        self.showing_choices = False
        self.choice_message = None
        self.choice_buttons = []
        self.choice_results = []
        
        # 移动到下一条消息
        self.current_index += 1
        
        # 计算聊天区域总高度
        self.calculate_total_height()
        
        # 自动滚动到底部
        self.scroll_to_bottom()
    
    def calculate_total_height(self):
        """计算聊天区域总高度"""
        self.total_chat_height = 0
        for msg in self.displayed_messages:
            self.total_chat_height += msg.height + 30  # 30像素的消息间距
    
    def scroll_to_bottom(self):
        """滚动到底部"""
        chat_area_height = self.screen_height - 200
        if self.total_chat_height > chat_area_height:
            self.target_scroll_offset = self.total_chat_height - chat_area_height
        else:
            self.target_scroll_offset = 0
    
    def update_scroll(self):
        """更新滚动位置（实现平滑滚动）"""
        # 平滑滚动到目标位置
        if abs(self.target_scroll_offset - self.scroll_offset) > 1:
            self.scroll_offset += (self.target_scroll_offset - self.scroll_offset) * self.scroll_speed
        else:
            self.scroll_offset = self.target_scroll_offset
        
        # 限制滚动范围
        chat_area_height = self.screen_height - 200
        if self.total_chat_height < chat_area_height:
            self.scroll_offset = 0
            self.target_scroll_offset = 0
        else:
            if self.scroll_offset < 0:
                self.scroll_offset = 0
                self.target_scroll_offset = 0
            elif self.scroll_offset > self.total_chat_height - chat_area_height:
                self.scroll_offset = self.total_chat_height - chat_area_height
                self.target_scroll_offset = self.scroll_offset
        
        # 更新滚动条位置
        self.update_scroll_bar()
    
    def update_scroll_bar(self):
        """更新滚动条位置和大小"""
        chat_area_height = self.screen_height - 200
        if self.total_chat_height > chat_area_height:
            # 计算滚动条高度（根据聊天区域比例）
            scroll_bar_height = max(50, int(chat_area_height * chat_area_height / self.total_chat_height))
            
            # 计算滚动条位置
            scroll_pos = int((self.scroll_offset / (self.total_chat_height - chat_area_height)) * 
                            (chat_area_height - scroll_bar_height))
            
            self.scroll_bar.height = scroll_bar_height
            self.scroll_bar.y = 80 + scroll_pos
        else:
            # 如果不需要滚动，隐藏滚动条
            self.scroll_bar.height = 0
    
    def handle_scroll(self, dy):
        """处理滚动事件"""
        # 如果正在拖动滚动条，不处理鼠标滚轮
        if self.dragging_scroll or self.showing_choices:
            return
        
        # 计算滚动步长（根据总高度调整）
        step = max(30, self.total_chat_height // 20)
        self.target_scroll_offset += dy * step
        
        # 确保目标位置在合理范围内
        chat_area_height = self.screen_height - 200
        if self.target_scroll_offset < 0:
            self.target_scroll_offset = 0
        elif self.target_scroll_offset > self.total_chat_height - chat_area_height:
            self.target_scroll_offset = self.total_chat_height - chat_area_height
    
    def draw(self, screen):
        """Draw entire interface"""
        # 先计算总高度
        self.calculate_total_height()
        
        # Draw background
        screen.fill(BACKGROUND)
        
        # Draw top status bar
        pygame.draw.rect(screen, HEADER_COLOR, (0, 0, self.screen_width, 80))
        title = font_xlarge.render(self.chat_name, True, TEXT_COLOR)
        screen.blit(title, (20, 25))
        
        # Draw search box
        pygame.draw.rect(screen, SEARCH_BAR, (self.screen_width - 250, 20, 230, 35), border_radius=18)
        search_text = font_medium.render("Search", True, (180, 180, 180))
        screen.blit(search_text, (self.screen_width - 230, 25))
        
        # Draw exit button
        exit_color = EXIT_BUTTON_COLOR if self.exit_button_hover else (200, 200, 200)
        pygame.draw.rect(screen, exit_color, self.exit_button, border_radius=10)
        exit_text = font_medium.render("X", True, TEXT_COLOR)
        text_rect = exit_text.get_rect(center=self.exit_button.center)
        screen.blit(exit_text, text_rect)
        
        # Draw chat area
        chat_area = pygame.Rect(0, 80, self.screen_width, self.screen_height - 140)
        pygame.draw.rect(screen, BACKGROUND, chat_area)
        
        # Draw messages
        y_pos = 100 - self.scroll_offset
        for msg in self.displayed_messages:
            # 如果消息在可见区域外，跳过绘制
            if y_pos + msg.height < 80 or y_pos > self.screen_height - 60:
                y_pos += msg.height + 30
                continue
            
            # Draw timestamp
            if msg.timestamp:
                time_text = font_small.render(msg.timestamp, True, TIME_COLOR)
                time_rect = time_text.get_rect(center=(self.screen_width//2, y_pos))
                screen.blit(time_text, time_rect)
                y_pos += 30
            
            # 旁白消息特殊处理
            if msg.sender == "*":
                # 旁白背景
                bubble_width = min(self.screen_width * 0.9, max(msg.width, 400))
                bubble_height = msg.height
                bubble_x = (self.screen_width - bubble_width) // 2
                
                # 绘制旁白背景
                pygame.draw.rect(screen, NARRATOR_BG, (bubble_x, y_pos, bubble_width, bubble_height), border_radius=10)
                
                # 绘制旁白标记
                narrator_text = font_small.render("Narrator", True, (100, 100, 100))
                screen.blit(narrator_text, (bubble_x + 10, y_pos + 5))
                
                # 绘制消息内容
                content_y = y_pos + 25
                for line in msg.rendered_content:
                    screen.blit(line, (bubble_x + 20, content_y))
                    content_y += 24
                
                y_pos += bubble_height + 30
                continue
            
            # 普通消息
            # 获取气泡颜色
            bubble_color = self.participants.get(msg.sender, (200, 230, 255))  # 默认蓝色
            
            # 绘制消息气泡
            bubble_width = min(msg.width, self.max_bubble_width)
            bubble_height = msg.height
            
            # 气泡位置 - 自己的消息在右侧，其他人在左侧
            is_me = msg.sender == self.my_name
            bubble_x = self.screen_width - bubble_width - 40 if is_me else 40
            
            # 绘制气泡
            pygame.draw.rect(screen, bubble_color, 
                            (bubble_x, y_pos, bubble_width, bubble_height), 
                            border_radius=15)
            
            # 绘制三角形指示器
            if is_me:
                pygame.draw.polygon(screen, bubble_color, [
                    (bubble_x + bubble_width, y_pos + 15),
                    (bubble_x + bubble_width + 10, y_pos + 20),
                    (bubble_x + bubble_width, y_pos + 25)
                ])
            else:
                pygame.draw.polygon(screen, bubble_color, [
                    (bubble_x, y_pos + 15),
                    (bubble_x - 10, y_pos + 20),
                    (bubble_x, y_pos + 25)
                ])
            
            # 绘制发送者名称
            sender_text = font_small.render(msg.sender, True, (80, 80, 80))
            sender_x = bubble_x + 15 if not is_me else bubble_x + bubble_width - sender_text.get_width() - 15
            screen.blit(sender_text, (sender_x, y_pos + 8))
            
            # 绘制消息内容
            content_y = y_pos + 35
            for line in msg.rendered_content:
                screen.blit(line, (bubble_x + 15, content_y))
                content_y += 30
            
            y_pos += bubble_height + 30
        
        # Draw scroll bar if needed
        chat_area_height = self.screen_height - 200
        if self.total_chat_height > chat_area_height and self.scroll_bar.height > 0:
            bar_color = SCROLL_BAR_ACTIVE if self.scroll_bar_active else SCROLL_BAR
            pygame.draw.rect(screen, bar_color, self.scroll_bar, border_radius=4)
        
        # Draw bottom status bar
        pygame.draw.rect(screen, HEADER_COLOR, (0, self.screen_height - 60, self.screen_width, 60))
        
        # Draw progress
        if self.loaded:
            if self.showing_choices:
                status = "Your Choice:"
            else:
                status = f"Press Enter to show next message ({self.current_index}/{len(self.messages)})"
            status_text = font_medium.render(status, True, TEXT_COLOR)
            screen.blit(status_text, (30, self.screen_height - 30))
        else:
            status = "No chat history loaded. Import a chat history file to start."
            status_text = font_medium.render(status, True, TEXT_COLOR)
            screen.blit(status_text, (30, self.screen_height - 30))
        
        # Draw import button
        if not self.showing_choices:  # 选择时不显示导入按钮
            button_color = BUTTON_HOVER_COLOR if self.button_hover else BUTTON_COLOR
            pygame.draw.rect(screen, button_color, self.import_button, border_radius=15)
            button_text = font_medium.render("Import Chat History", True, (255, 255, 255))
            text_rect = button_text.get_rect(center=self.import_button.center)
            screen.blit(button_text, text_rect)
        
        # 绘制选择项
        if self.showing_choices and self.choice_message:
            # 绘制半透明背景
            s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            s.fill((0, 0, 0, 128))  # 半透明黑色背景
            screen.blit(s, (0, 0))
            
            # 绘制选择对话框
            dialog_width = SCREEN_WIDTH * 0.5
            dialog_height = len(self.choice_message.choices) * 60 + 100
            dialog_x = (SCREEN_HEIGHT - dialog_height) // 2 - 170
            dialog_y = (SCREEN_HEIGHT - dialog_height) // 2
            
            # 绘制对话框背景
            pygame.draw.rect(screen, CHOICE_BG, (dialog_x, dialog_y, dialog_width, dialog_height), border_radius=15)
            pygame.draw.rect(screen, (100, 100, 100), (dialog_x, dialog_y, dialog_width, dialog_height), 2, border_radius=15)
            
            # 绘制标题
            title = font_large.render("Your Choice:", True, TEXT_COLOR)
            screen.blit(title, (dialog_x + 20, dialog_y + 20))
            
            # 绘制问题
            question = font_medium.render(self.choice_message.content, True, TEXT_COLOR)
            screen.blit(question, (dialog_x + 20, dialog_y + 60))
            
            # 绘制选择按钮
            self.choice_buttons = []
            for i, choice in enumerate(self.choice_message.choices):
                button_y = dialog_y + 100 + i * 60
                button_rect = pygame.Rect(
                    dialog_x + 40,
                    button_y,
                    dialog_width - 80,
                    50
                )
                self.choice_buttons.append(button_rect)
                
                # 绘制按钮
                button_color = CHOICE_BUTTON_HOVER if button_rect.collidepoint(pygame.mouse.get_pos()) else CHOICE_BUTTON
                pygame.draw.rect(screen, button_color, button_rect, border_radius=10)
                pygame.draw.rect(screen, (100, 100, 100), button_rect, 1, border_radius=10)
                
                # 绘制按钮文字
                choice_text = font_medium.render(choice["text"], True, TEXT_COLOR)
                text_rect = choice_text.get_rect(center=button_rect.center)
                screen.blit(choice_text, text_rect)

# 文件选择对话框
def open_file_dialog():
    # 初始化tkinter并隐藏主窗口
    root = tk.Tk()
    root.withdraw()
    
    # 设置文件选择对话框
    file_path = filedialog.askopenfilename(
        title="Select Chat History File",
        filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
    )
    
    # 关闭tkinter
    root.destroy()
    
    return file_path

# 主程序
def main():
    # 获取屏幕尺寸
    screen_info = pygame.display.Info()
    SCREEN_WIDTH = screen_info.current_w
    SCREEN_HEIGHT = screen_info.current_h
    
    # 创建全屏窗口
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
    pygame.display.set_caption("WeChat Chat Simulator")
    
    simulator = WeChatSimulator(SCREEN_WIDTH, SCREEN_HEIGHT)
    clock = pygame.time.Clock()
    
    # 检查是否有命令行参数
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        if os.path.exists(file_path):
            simulator.load_chat_history(file_path)
    
    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        
        # 更新滚动
        simulator.update_scroll()
        
        # 检查鼠标是否在UI元素上
        simulator.button_hover = simulator.import_button.collidepoint(mouse_pos) and not simulator.showing_choices
        simulator.exit_button_hover = simulator.exit_button.collidepoint(mouse_pos)
        simulator.scroll_bar_active = simulator.scroll_bar.collidepoint(mouse_pos)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and not simulator.showing_choices:
                    simulator.show_next_message()
                elif event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_UP:  # 上箭头键向上滚动
                    simulator.handle_scroll(-1)
                elif event.key == pygame.K_DOWN:  # 下箭头键向下滚动
                    simulator.handle_scroll(1)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 左键点击
                    if simulator.showing_choices:
                        # 检查是否点击了选择按钮
                        for i, button in enumerate(simulator.choice_buttons):
                            if button.collidepoint(mouse_pos):
                                simulator.make_choice(i)
                                break
                    elif simulator.import_button.collidepoint(mouse_pos):
                        # 打开文件选择对话框
                        file_path = open_file_dialog()
                        if file_path and os.path.exists(file_path):
                            simulator.load_chat_history(file_path)
                    elif simulator.exit_button.collidepoint(mouse_pos):
                        running = False
                    elif simulator.scroll_bar.collidepoint(mouse_pos):
                        simulator.dragging_scroll = True
                        simulator.drag_start_y = mouse_pos[1]
                        simulator.drag_start_offset = simulator.scroll_offset
                elif event.button == 4:  # 鼠标滚轮向上
                    simulator.handle_scroll(-1)
                elif event.button == 5:  # 鼠标滚轮向下
                    simulator.handle_scroll(1)
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:  # 左键释放
                    simulator.dragging_scroll = False
            elif event.type == pygame.MOUSEMOTION:
                if simulator.dragging_scroll:
                    # 计算拖动距离对应的滚动量
                    chat_area_height = simulator.screen_height - 200
                    delta_y = mouse_pos[1] - simulator.drag_start_y
                    
                    # 计算新的滚动位置
                    scroll_range = simulator.total_chat_height - chat_area_height
                    if scroll_range > 0:
                        scroll_factor = scroll_range / (chat_area_height - simulator.scroll_bar.height)
                        new_offset = simulator.drag_start_offset + delta_y * scroll_factor
                        
                        # 设置目标滚动位置
                        simulator.target_scroll_offset = new_offset
        
        simulator.draw(screen)
        pygame.display.flip()
        clock.tick(60)  # 增加帧率以获得更平滑的滚动
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()