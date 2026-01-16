import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog
import threading
import time
import queue
import traceback

class BrainfuckInterpreter:
    def __init__(self, memory_size=30000):
        self.memory_size = memory_size
        self.memory = [0] * memory_size
        self.pointer = 0
        self.code = ""
        self.code_ptr = 0
        self.output = ""
        self.input_buffer = ""
        self.input_ptr = 0
        self.is_running = False
        self.speed = 1.0
        self.update_callback = None
        self.output_callback = None
        self.error_callback = None
        self.max_steps = 1000000  # 最大执行步数，防止无限循环
        self.step_count = 0
        
    def load_code(self, code):
        """加载 Brainfuck 代码"""
        try:
            # 过滤掉非 Brainfuck 命令的字符
            self.code = ''.join(c for c in code if c in '><+-.,[]')
            self.code_ptr = 0
            self.pointer = 0
            self.memory = [0] * self.memory_size
            self.output = ""
            self.input_buffer = ""
            self.input_ptr = 0
            self.step_count = 0
        except Exception as e:
            if self.error_callback:
                self.error_callback(f"加载代码时出错: {str(e)}")
        
    def set_input(self, input_str):
        """设置输入"""
        self.input_buffer = input_str
        self.input_ptr = 0
        
    def set_speed(self, speed):
        """设置执行速度（1.0 = 正常，0.5 = 两倍速，2.0 = 半速）"""
        self.speed = max(0.01, min(10.0, speed))  # 限制速度范围
        
    def run(self):
        """运行 Brainfuck 代码"""
        try:
            self.is_running = True
            bracket_stack = []
            bracket_pairs = {}
            
            # 预处理括号匹配
            for i, cmd in enumerate(self.code):
                if cmd == '[':
                    bracket_stack.append(i)
                elif cmd == ']':
                    if bracket_stack:
                        start = bracket_stack.pop()
                        bracket_pairs[start] = i
                        bracket_pairs[i] = start
                    else:
                        raise SyntaxError(f"未匹配的 ']' 在位置 {i}")
            
            if bracket_stack:
                raise SyntaxError(f"未匹配的 '[' 在位置 {bracket_stack[-1]}")
            
            # 执行代码
            while self.is_running and self.code_ptr < len(self.code):
                if self.step_count > self.max_steps:
                    raise Exception(f"超过最大执行步数 ({self.max_steps})，可能陷入无限循环")
                
                cmd = self.code[self.code_ptr]
                self.step_count += 1
                
                if cmd == '>':
                    self.pointer = (self.pointer + 1) % self.memory_size
                elif cmd == '<':
                    self.pointer = (self.pointer - 1) % self.memory_size
                elif cmd == '+':
                    self.memory[self.pointer] = (self.memory[self.pointer] + 1) % 256
                elif cmd == '-':
                    self.memory[self.pointer] = (self.memory[self.pointer] - 1) % 256
                elif cmd == '.':
                    char = chr(self.memory[self.pointer])
                    self.output += char
                    if self.output_callback:
                        self.output_callback(char)
                elif cmd == ',':
                    if self.input_ptr < len(self.input_buffer):
                        self.memory[self.pointer] = ord(self.input_buffer[self.input_ptr])
                        self.input_ptr += 1
                    else:
                        # 如果没有输入，设置为 0（EOF）
                        self.memory[self.pointer] = 0
                elif cmd == '[':
                    if self.memory[self.pointer] == 0:
                        self.code_ptr = bracket_pairs[self.code_ptr]
                elif cmd == ']':
                    if self.memory[self.pointer] != 0:
                        self.code_ptr = bracket_pairs[self.code_ptr]
                
                self.code_ptr += 1
                
                # 更新 GUI
                if self.update_callback:
                    self.update_callback()
                    
                # 控制执行速度
                if self.speed > 0:
                    time.sleep(0.01 / self.speed)
        
        except Exception as e:
            if self.error_callback:
                self.error_callback(str(e))
        
        finally:
            self.is_running = False
        
    def stop(self):
        """停止执行"""
        self.is_running = False
        
    def get_memory_dump(self, start=0, count=20):
        """获取内存转储"""
        try:
            start = max(0, min(start, self.memory_size - 1))
            end = min(start + count, self.memory_size)
            return self.memory[start:end]
        except:
            return []
        
    def get_status(self):
        """获取当前状态"""
        try:
            return {
                'pointer': self.pointer,
                'code_ptr': self.code_ptr,
                'current_cell': self.memory[self.pointer] if 0 <= self.pointer < self.memory_size else -1,
                'output': self.output,
                'step_count': self.step_count
            }
        except:
            return {
                'pointer': 0,
                'code_ptr': 0,
                'current_cell': 0,
                'output': '',
                'step_count': 0
            }


class BrainfuckGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Brainfuck 解释器")
        self.root.geometry("1000x700")
        
        # 设置协议，处理窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 存储示例代码
        self.examples = {
            "Hello World": "++++++++[>++++[>++>+++>+++>+<<<<-]>+>+>->>+[<]<-]>>.>---.+++++++..+++.>>.<-.<.+++.------.--------.>>+.>++.",
            "斐波那契数列": ">++++++++++>+>+[[+++++[>++++++++<-]>.<++++++[>--------<-]+<<<]>.>>[[-]<[>+<-]>>[<<+>+>-]<[>+<-[>+<-[>+<-[>+<-[>+<-[>+<-[>+<-[>+<-[>+<-[>[-]>+>+<<<-[>+<-]]]]]]]]]]]+>>>]<<<]",
            "乘法（3×2）": "+++>++<<[->[->+>+<<]>[-<+>]<<]>>>[-]++++++++++[>++++++++++<-]>>.",
            "字符A输出": "++++++++[>++++++++<-]>+.",
            "简单循环": "+++[>+++<-]>.",
            "猫程序（回显输入）": ",[.,]",
            "平方数": "++++++++[>++++++<-]>>+++<[>[>+>+<<-]>>[-<<+>>]<<<-]>>>."
        }
        
        # 初始化解释器
        self.interpreter = BrainfuckInterpreter()
        self.interpreter.update_callback = self.update_display
        self.interpreter.output_callback = self.append_output
        self.interpreter.error_callback = self.handle_error
        
        # 创建界面
        self.create_widgets()
        
        # 用于线程安全的GUI更新队列
        self.gui_queue = queue.Queue()
        self.process_gui_queue()
        
        # 插入示例代码
        self.insert_example("Hello World")
        
    def process_gui_queue(self):
        """处理GUI更新队列"""
        try:
            while True:
                task = self.gui_queue.get_nowait()
                if callable(task):
                    task()
        except queue.Empty:
            pass
        finally:
            # 每100毫秒检查一次队列
            self.root.after(100, self.process_gui_queue)
        
    def safe_gui_call(self, func):
        """安全地调用GUI函数（通过队列）"""
        self.gui_queue.put(func)
        
    def create_widgets(self):
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # 菜单栏
        self.create_menu_bar()
        
        # 代码编辑区域
        code_frame = ttk.LabelFrame(main_frame, text="Brainfuck 代码", padding="5")
        code_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.code_editor = scrolledtext.ScrolledText(
            code_frame, 
            width=80, 
            height=10,
            wrap=tk.NONE,
            font=("Courier New", 10)
        )
        self.code_editor.pack(fill=tk.BOTH, expand=True)
        
        # 控制面板
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 速度控制
        ttk.Label(control_frame, text="速度:").pack(side=tk.LEFT, padx=(0, 5))
        self.speed_var = tk.DoubleVar(value=1.0)
        speed_scale = ttk.Scale(control_frame, from_=0.1, to=5.0, variable=self.speed_var, 
                               orient=tk.HORIZONTAL, length=100)
        speed_scale.pack(side=tk.LEFT, padx=(0, 10))
        
        # 按钮
        self.run_btn = ttk.Button(control_frame, text="运行", command=self.run_code)
        self.run_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.step_btn = ttk.Button(control_frame, text="单步执行", command=self.step_code)
        self.step_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stop_btn = ttk.Button(control_frame, text="停止", command=self.stop_code, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.clear_btn = ttk.Button(control_frame, text="清除", command=self.clear_all)
        self.clear_btn.pack(side=tk.LEFT)
        
        # 输入和输出区域
        io_frame = ttk.Frame(main_frame)
        io_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 输入区域
        input_frame = ttk.LabelFrame(io_frame, text="输入", padding="5")
        input_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.input_var = tk.StringVar()
        self.input_entry = ttk.Entry(input_frame, textvariable=self.input_var)
        self.input_entry.pack(fill=tk.X)
        
        # 输出区域
        output_frame = ttk.LabelFrame(io_frame, text="输出", padding="5")
        output_frame.pack(fill=tk.BOTH, expand=True)
        
        self.output_text = scrolledtext.ScrolledText(
            output_frame, 
            width=80, 
            height=8,
            state=tk.DISABLED,
            wrap=tk.WORD
        )
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
        # 内存和状态显示
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.BOTH, expand=True)
        
        # 内存显示
        memory_frame = ttk.LabelFrame(status_frame, text="内存", padding="5")
        memory_frame.pack(fill=tk.BOTH, expand=True, side=tk.LEFT, padx=(0, 5))
        
        self.memory_text = scrolledtext.ScrolledText(
            memory_frame, 
            width=40, 
            height=6,
            state=tk.DISABLED,
            font=("Courier New", 9)
        )
        self.memory_text.pack(fill=tk.BOTH, expand=True)
        
        # 状态显示
        state_frame = ttk.LabelFrame(status_frame, text="状态", padding="5")
        state_frame.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        self.state_text = scrolledtext.ScrolledText(
            state_frame, 
            width=40, 
            height=6,
            state=tk.DISABLED
        )
        self.state_text.pack(fill=tk.BOTH, expand=True)
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(fill=tk.X, pady=(10, 0))
    
    def create_menu_bar(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="新建", command=self.new_file)
        file_menu.add_command(label="打开", command=self.open_file)
        file_menu.add_command(label="保存", command=self.save_file)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.on_closing)
        
        # 示例菜单
        example_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="示例", menu=example_menu)
        
        for example_name in self.examples.keys():
            example_menu.add_command(
                label=example_name, 
                command=lambda name=example_name: self.insert_example(name)
            )
        
        # 设置菜单
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="设置", menu=settings_menu)
        settings_menu.add_command(label="设置内存大小", command=self.set_memory_size)
        settings_menu.add_command(label="设置最大步数", command=self.set_max_steps)
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="Brainfuck 语法", command=self.show_syntax_help)
        help_menu.add_command(label="关于", command=self.show_about)
    
    def insert_example(self, example_name):
        """插入示例代码"""
        if example_name in self.examples:
            self.code_editor.delete(1.0, tk.END)
            self.code_editor.insert(1.0, self.examples[example_name])
            self.status_var.set(f"已加载示例: {example_name}")
    
    def append_output(self, text):
        """向输出区域添加文本"""
        self.safe_gui_call(lambda: self._append_output(text))
    
    def _append_output(self, text):
        """实际的输出添加函数（在主线程中执行）"""
        self.output_text.config(state=tk.NORMAL)
        self.output_text.insert(tk.END, text)
        self.output_text.see(tk.END)
        self.output_text.config(state=tk.DISABLED)
    
    def update_display(self):
        """更新内存和状态显示"""
        self.safe_gui_call(self._update_display)
    
    def _update_display(self):
        """实际的显示更新函数（在主线程中执行）"""
        try:
            # 更新内存显示
            memory_dump = self.interpreter.get_memory_dump(
                max(0, self.interpreter.pointer - 10), 
                20
            )
            
            self.memory_text.config(state=tk.NORMAL)
            self.memory_text.delete(1.0, tk.END)
            
            for i, value in enumerate(memory_dump):
                addr = max(0, self.interpreter.pointer - 10) + i
                pointer_indicator = " <--" if addr == self.interpreter.pointer else ""
                char_repr = chr(value) if 32 <= value <= 126 else '?'
                self.memory_text.insert(tk.END, f"[{addr:4d}] = {value:3d} ({char_repr}){pointer_indicator}\n")
            
            self.memory_text.config(state=tk.DISABLED)
            
            # 更新状态显示
            state = self.interpreter.get_status()
            self.state_text.config(state=tk.NORMAL)
            self.state_text.delete(1.0, tk.END)
            
            self.state_text.insert(tk.END, f"数据指针: {state['pointer']}\n")
            self.state_text.insert(tk.END, f"代码指针: {state['code_ptr']}\n")
            self.state_text.insert(tk.END, f"当前字节值: {state['current_cell']}\n")
            if state['code_ptr'] > 0 and state['code_ptr'] <= len(self.interpreter.code):
                current_cmd = self.interpreter.code[state['code_ptr']-1]
                self.state_text.insert(tk.END, f"当前命令: {current_cmd}\n")
            else:
                self.state_text.insert(tk.END, f"当前命令: N/A\n")
            self.state_text.insert(tk.END, f"输出长度: {len(state['output'])}\n")
            self.state_text.insert(tk.END, f"已执行步数: {state['step_count']}\n")
            
            self.state_text.config(state=tk.DISABLED)
            
            # 更新代码高亮
            self.highlight_current_command()
        except Exception as e:
            # 忽略显示更新中的错误，避免连锁崩溃
            pass
    
    def highlight_current_command(self):
        """高亮显示当前执行的命令"""
        try:
            # 移除之前的高亮
            self.code_editor.tag_remove("current", "1.0", tk.END)
            
            # 添加新的高亮
            if (self.interpreter.code_ptr < len(self.interpreter.code) and 
                self.interpreter.code_ptr >= 0):
                line_start = f"1.0+{self.interpreter.code_ptr}c"
                line_end = f"1.0+{self.interpreter.code_ptr+1}c"
                self.code_editor.tag_add("current", line_start, line_end)
                self.code_editor.tag_config("current", background="yellow")
                self.code_editor.see(line_start)
        except:
            # 忽略高亮错误
            pass
    
    def run_code(self):
        """运行代码"""
        code = self.code_editor.get(1.0, tk.END).strip()
        input_text = self.input_var.get()
        
        if not code:
            messagebox.showwarning("警告", "请输入 Brainfuck 代码")
            return
        
        # 设置解释器
        self.interpreter.load_code(code)
        self.interpreter.set_input(input_text)
        self.interpreter.set_speed(self.speed_var.get())
        
        # 清除输出
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        self.output_text.config(state=tk.DISABLED)
        
        # 更新按钮状态
        self.run_btn.config(state=tk.DISABLED)
        self.step_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        
        # 在新线程中运行代码
        def run():
            self.safe_gui_call(lambda: self.status_var.set("正在运行..."))
            try:
                self.interpreter.run()
                self.safe_gui_call(lambda: self.status_var.set("运行完成"))
            except Exception as e:
                error_msg = f"运行错误: {str(e)}"
                self.safe_gui_call(lambda: self.handle_error(error_msg))
            finally:
                # 恢复按钮状态
                self.safe_gui_call(lambda: self.run_btn.config(state=tk.NORMAL))
                self.safe_gui_call(lambda: self.step_btn.config(state=tk.NORMAL))
                self.safe_gui_call(lambda: self.stop_btn.config(state=tk.DISABLED))
        
        thread = threading.Thread(target=run)
        thread.daemon = True  # 设置为守护线程，主线程退出时自动结束
        thread.start()
    
    def step_code(self):
        """单步执行代码"""
        try:
            code = self.code_editor.get(1.0, tk.END).strip()
            input_text = self.input_var.get()
            
            if not code:
                messagebox.showwarning("警告", "请输入 Brainfuck 代码")
                return
            
            # 如果是第一次单步执行，初始化解释器
            if self.interpreter.code_ptr == 0 and not self.interpreter.is_running:
                self.interpreter.load_code(code)
                self.interpreter.set_input(input_text)
            
            # 检查是否已完成
            if self.interpreter.code_ptr >= len(self.interpreter.code):
                self.status_var.set("执行已完成")
                return
            
            # 执行一步
            if self.interpreter.step_count > self.interpreter.max_steps:
                raise Exception(f"超过最大执行步数 ({self.interpreter.max_steps})")
            
            cmd = self.interpreter.code[self.interpreter.code_ptr]
            self.interpreter.step_count += 1
            
            if cmd == '>':
                self.interpreter.pointer = (self.interpreter.pointer + 1) % self.interpreter.memory_size
            elif cmd == '<':
                self.interpreter.pointer = (self.interpreter.pointer - 1) % self.interpreter.memory_size
            elif cmd == '+':
                self.interpreter.memory[self.interpreter.pointer] = (self.interpreter.memory[self.interpreter.pointer] + 1) % 256
            elif cmd == '-':
                self.interpreter.memory[self.interpreter.pointer] = (self.interpreter.memory[self.interpreter.pointer] - 1) % 256
            elif cmd == '.':
                char = chr(self.interpreter.memory[self.interpreter.pointer])
                self.interpreter.output += char
                self.append_output(char)
            elif cmd == ',':
                if self.interpreter.input_ptr < len(self.interpreter.input_buffer):
                    self.interpreter.memory[self.interpreter.pointer] = ord(self.interpreter.input_buffer[self.interpreter.input_ptr])
                    self.interpreter.input_ptr += 1
                else:
                    self.interpreter.memory[self.interpreter.pointer] = 0
            elif cmd == '[':
                if self.interpreter.memory[self.interpreter.pointer] == 0:
                    # 查找匹配的 ]
                    bracket_count = 1
                    while bracket_count > 0 and self.interpreter.code_ptr < len(self.interpreter.code) - 1:
                        self.interpreter.code_ptr += 1
                        if self.interpreter.code[self.interpreter.code_ptr] == '[':
                            bracket_count += 1
                        elif self.interpreter.code[self.interpreter.code_ptr] == ']':
                            bracket_count -= 1
            elif cmd == ']':
                if self.interpreter.memory[self.interpreter.pointer] != 0:
                    # 查找匹配的 [
                    bracket_count = 1
                    while bracket_count > 0 and self.interpreter.code_ptr > 0:
                        self.interpreter.code_ptr -= 1
                        if self.interpreter.code[self.interpreter.code_ptr] == ']':
                            bracket_count += 1
                        elif self.interpreter.code[self.interpreter.code_ptr] == '[':
                            bracket_count -= 1
            
            self.interpreter.code_ptr += 1
            
            # 更新显示
            self.update_display()
            self.status_var.set(f"单步执行: {cmd} (步骤: {self.interpreter.step_count})")
            
            # 检查是否完成
            if self.interpreter.code_ptr >= len(self.interpreter.code):
                self.status_var.set("执行完成")
                
        except Exception as e:
            self.handle_error(f"单步执行错误: {str(e)}")
    
    def stop_code(self):
        """停止执行"""
        self.interpreter.stop()
        self.status_var.set("已停止")
        self.run_btn.config(state=tk.NORMAL)
        self.step_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
    
    def clear_all(self):
        """清除所有内容"""
        self.code_editor.delete(1.0, tk.END)
        self.input_var.set("")
        
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        self.output_text.config(state=tk.DISABLED)
        
        self.memory_text.config(state=tk.NORMAL)
        self.memory_text.delete(1.0, tk.END)
        self.memory_text.config(state=tk.DISABLED)
        
        self.state_text.config(state=tk.NORMAL)
        self.state_text.delete(1.0, tk.END)
        self.state_text.config(state=tk.DISABLED)
        
        self.status_var.set("已清除所有内容")
        
        # 重置解释器
        self.interpreter = BrainfuckInterpreter()
        self.interpreter.update_callback = self.update_display
        self.interpreter.output_callback = self.append_output
        self.interpreter.error_callback = self.handle_error
    
    def handle_error(self, error_msg):
        """处理错误"""
        self.safe_gui_call(lambda: self._handle_error(error_msg))
    
    def _handle_error(self, error_msg):
        """实际的错误处理函数（在主线程中执行）"""
        self.append_output(f"\n错误: {error_msg}")
        self.status_var.set(f"错误: {error_msg}")
        
        # 恢复按钮状态
        self.run_btn.config(state=tk.NORMAL)
        self.step_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        
        # 显示错误对话框
        messagebox.showerror("错误", error_msg)
    
    def new_file(self):
        """新建文件"""
        self.code_editor.delete(1.0, tk.END)
        self.status_var.set("已创建新文件")
    
    def open_file(self):
        """打开文件"""
        from tkinter import filedialog
        file_path = filedialog.askopenfilename(
            title="打开 Brainfuck 文件",
            filetypes=[("Brainfuck 文件", "*.b;*.bf"), ("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    code_content = file.read()
                
                self.code_editor.delete(1.0, tk.END)
                self.code_editor.insert(1.0, code_content)
                self.status_var.set(f"已打开文件: {file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"无法打开文件: {str(e)}")
    
    def save_file(self):
        """保存文件"""
        from tkinter import filedialog
        file_path = filedialog.asksaveasfilename(
            title="保存 Brainfuck 文件",
            defaultextension=".bf",
            filetypes=[("Brainfuck 文件", "*.bf"), ("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        
        if file_path:
            try:
                code_content = self.code_editor.get(1.0, tk.END)
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(code_content)
                
                self.status_var.set(f"文件已保存: {file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"无法保存文件: {str(e)}")
    
    def set_memory_size(self):
        """设置内存大小"""
        try:
            current_size = self.interpreter.memory_size
            new_size = simpledialog.askinteger(
                "设置内存大小", 
                f"请输入内存大小 (当前: {current_size}):", 
                parent=self.root,
                minvalue=100,
                maxvalue=1000000
            )
            
            if new_size:
                self.interpreter.memory_size = new_size
                self.interpreter.memory = [0] * new_size
                self.status_var.set(f"内存大小已设置为: {new_size}")
        except Exception as e:
            messagebox.showerror("错误", f"设置内存大小时出错: {str(e)}")
    
    def set_max_steps(self):
        """设置最大步数"""
        try:
            current_max = self.interpreter.max_steps
            new_max = simpledialog.askinteger(
                "设置最大步数", 
                f"请输入最大执行步数 (当前: {current_max}):", 
                parent=self.root,
                minvalue=1000,
                maxvalue=10000000
            )
            
            if new_max:
                self.interpreter.max_steps = new_max
                self.status_var.set(f"最大步数已设置为: {new_max}")
        except Exception as e:
            messagebox.showerror("错误", f"设置最大步数时出错: {str(e)}")
    
    def show_syntax_help(self):
        """显示 Brainfuck 语法帮助"""
        help_text = """Brainfuck 语言语法

Brainfuck 是一种极简的图灵完备编程语言，只有 8 个命令：

>   指针加一（指向下一个字节）
<   指针减一（指向上一个字节）
+   指针指向的字节值加一
-   指针指向的字节值减一
.   输出指针指向的字节（ASCII 码）
,   输入一个字节到指针指向的位置
[   如果指针指向的字节值为 0，跳转到对应的 ] 之后
]   如果指针指向的字节值不为 0，跳转到对应的 [ 之后

示例：

Hello World 程序：
++++++++[>++++[>++>+++>+++>+<<<<-]>+>+>->>+[<]<-]>>.>---.+++++++..+++.>>.<-.<.+++.------.--------.>>+.>++.

简单循环（输出 3 个 'A'）：
+++[>++++++++++<-]>.

猫程序（回显输入，直到 EOF）：
,[.,]

注意：
- Brainfuck 使用一个字节数组（通常 30000 字节）作为内存
- 所有字节初始值为 0
- 指针初始指向数组的第一个字节
- 字节值在 0-255 之间循环（溢出时会回绕）"""

        help_window = tk.Toplevel(self.root)
        help_window.title("Brainfuck 语法帮助")
        help_window.geometry("600x500")
        
        help_text_area = scrolledtext.ScrolledText(help_window, wrap=tk.WORD)
        help_text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        help_text_area.insert(1.0, help_text)
        help_text_area.config(state=tk.DISABLED)
    
    def show_about(self):
        """显示关于信息"""
        about_text = """Brainfuck 解释器

一个带有 GUI 界面的 Brainfuck 语言解释器。

Brainfuck 是一种极简的图灵完备编程语言，由 Urban Müller 在 1993 年创建。

特性：
- 完整的 Brainfuck 语言支持
- 实时内存和状态显示
- 可调节的执行速度
- 单步执行模式
- 多种示例代码
- 错误处理和稳定性改进

版本: 1.1 (修复版)"""
        
        messagebox.showinfo("关于 Brainfuck 解释器", about_text)
    
    def on_closing(self):
        """处理窗口关闭事件"""
        # 停止解释器执行
        self.interpreter.stop()
        
        # 等待一段时间让线程结束
        self.root.after(100, self.root.destroy)


# 主程序
if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = BrainfuckGUI(root)
        root.mainloop()
    except Exception as e:
        # 捕获并显示未处理的异常
        error_msg = f"程序崩溃: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        
        with open("brainfuck_crash.log", "w", encoding="utf-8") as f:
            f.write(error_msg)
        
        # 尝试显示错误消息
        try:
            tk.messagebox.showerror(
                "程序错误", 
                f"程序发生意外错误:\n{str(e)}\n\n详细信息已保存到 brainfuck_crash.log"
            )
        except:
            pass