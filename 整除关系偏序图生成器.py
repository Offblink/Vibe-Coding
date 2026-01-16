import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from collections import defaultdict, deque
import math
import itertools
import time
from typing import List, Dict, Set, Tuple

class DivisibilityLatticeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("整除关系偏序图生成器")
        self.root.geometry("1100x800")
        
        # 设置图标和样式
        self.setup_styles()
        
        # 创建界面
        self.create_widgets()
        
        # 初始化变量
        self.G = None
        self.pos = None
        
    def setup_styles(self):
        """设置界面样式"""
        try:
            style = ttk.Style()
            available_themes = style.theme_names()
            if 'clam' in available_themes:
                style.theme_use('clam')
            elif 'alt' in available_themes:
                style.theme_use('alt')
        except:
            pass
    
    def create_checkbox(self, parent, text, variable, command=None):
        """创建自定义勾选框"""
        frame = tk.Frame(parent, bg="white", cursor="hand2")
        
        # 画布用于绘制勾选框
        canvas = tk.Canvas(frame, width=20, height=20, bg="white", 
                          highlightthickness=0, bd=0)
        canvas.pack(side=tk.LEFT)
        
        # 绘制勾选框边框
        canvas.create_rectangle(2, 2, 18, 18, outline="#666", width=1)
        
        # 绘制勾选标记（初始隐藏）
        check_box = canvas.create_rectangle(4, 4, 16, 16, fill="", outline="")
        check_mark = canvas.create_line(6, 10, 9, 13, 14, 7, 
                                       fill="#4CAF50", width=2, state=tk.HIDDEN)
        
        # 标签
        label = tk.Label(frame, text=text, bg="white", font=("Arial", 10), 
                        cursor="hand2")
        label.pack(side=tk.LEFT, padx=(8, 0))
        
        def toggle_check(event=None):
            current = variable.get()
            variable.set(not current)
            if not current:  # 将被勾选
                canvas.itemconfig(check_box, fill="#4CAF50")
                canvas.itemconfig(check_mark, state=tk.NORMAL)
            else:  # 取消勾选
                canvas.itemconfig(check_box, fill="")
                canvas.itemconfig(check_mark, state=tk.HIDDEN)
            if command:
                command()
        
        # 绑定事件
        canvas.bind("<Button-1>", toggle_check)
        label.bind("<Button-1>", toggle_check)
        
        # 初始化状态
        if variable.get():
            canvas.itemconfig(check_box, fill="#4CAF50")
            canvas.itemconfig(check_mark, state=tk.NORMAL)
        
        return frame
    
    def create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_frame = tk.Frame(main_frame, bg="#4CAF50", height=60)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(title_frame, text="整除关系偏序图生成器", 
                              font=("Arial", 18, "bold"), fg="white", bg="#4CAF50")
        title_label.pack(expand=True)
        
        # 控制面板框架
        control_frame = ttk.LabelFrame(main_frame, text="参数设置", padding="15")
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 输入区域
        input_frame = tk.Frame(control_frame, bg="white")
        input_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20))
        
        tk.Label(input_frame, text="上限 (n):", font=("Arial", 10), 
                bg="white").pack(anchor=tk.W, pady=2)
        
        input_subframe = tk.Frame(input_frame, bg="white")
        input_subframe.pack(anchor=tk.W, pady=5)
        
        self.upper_limit_var = tk.StringVar(value="20")
        self.upper_limit_entry = ttk.Entry(input_subframe, textvariable=self.upper_limit_var, 
                                          width=10, font=("Arial", 10))
        self.upper_limit_entry.pack(side=tk.LEFT)
        
        ttk.Button(input_subframe, text="示例", width=6,
                  command=lambda: self.set_example_values()).pack(side=tk.LEFT, padx=5)
        
        tk.Label(input_frame, text="(下限固定为1)", font=("Arial", 9), 
                bg="white", fg="#666").pack(anchor=tk.W, pady=2)
        
        # 勾选框区域
        options_frame = tk.Frame(control_frame, bg="white")
        options_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 第一行勾选框
        checkbox_row1 = tk.Frame(options_frame, bg="white")
        checkbox_row1.pack(fill=tk.X, pady=2)
        
        self.show_numbers_var = tk.BooleanVar(value=True)
        self.show_numbers_cb = self.create_checkbox(checkbox_row1, "显示节点数字", 
                                                   self.show_numbers_var)
        self.show_numbers_cb.pack(side=tk.LEFT, padx=(0, 20))
        
        self.color_by_layer_var = tk.BooleanVar(value=True)
        self.color_by_layer_cb = self.create_checkbox(checkbox_row1, "按层次着色", 
                                                     self.color_by_layer_var)
        self.color_by_layer_cb.pack(side=tk.LEFT)
        
        # 第二行勾选框
        checkbox_row2 = tk.Frame(options_frame, bg="white")
        checkbox_row2.pack(fill=tk.X, pady=2)
        
        self.show_edge_labels_var = tk.BooleanVar(value=False)
        self.show_edge_labels_cb = self.create_checkbox(checkbox_row2, "显示边标签", 
                                                       self.show_edge_labels_var)
        self.show_edge_labels_cb.pack(side=tk.LEFT, padx=(0, 20))
        
        self.vertical_layout_var = tk.BooleanVar(value=True)
        self.vertical_layout_cb = self.create_checkbox(checkbox_row2, "垂直布局", 
                                                      self.vertical_layout_var)
        self.vertical_layout_cb.pack(side=tk.LEFT)
        
        # 第三行勾选框
        checkbox_row3 = tk.Frame(options_frame, bg="white")
        checkbox_row3.pack(fill=tk.X, pady=2)
        
        self.show_grid_var = tk.BooleanVar(value=True)
        self.show_grid_cb = self.create_checkbox(checkbox_row3, "显示网格", 
                                                self.show_grid_var)
        self.show_grid_cb.pack(side=tk.LEFT, padx=(0, 20))
        
        self.animate_var = tk.BooleanVar(value=False)
        self.animate_cb = self.create_checkbox(checkbox_row3, "动画效果", 
                                              self.animate_var)
        self.animate_cb.pack(side=tk.LEFT)
        
        # 按钮区域
        button_frame = tk.Frame(control_frame, bg="white")
        button_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        style = ttk.Style()
        style.configure("Accent.TButton", font=("Arial", 10, "bold"))
        
        self.generate_btn = ttk.Button(button_frame, text="生成偏序图", 
                                      command=self.generate_lattice, 
                                      style="Accent.TButton", width=12)
        self.generate_btn.pack(pady=2)
        
        self.clear_btn = ttk.Button(button_frame, text="清空", 
                                   command=self.clear_graph, width=12)
        self.clear_btn.pack(pady=2)
        
        self.export_btn = ttk.Button(button_frame, text="导出", 
                                    command=self.export_graph, width=12)
        self.export_btn.pack(pady=2)
        
        # 信息面板
        info_frame = ttk.LabelFrame(main_frame, text="图信息", padding="10")
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.info_text = tk.Text(info_frame, height=4, width=100, font=("Consolas", 9),
                                bg="#f8f9fa", relief=tk.FLAT, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(info_frame, orient="vertical", command=self.info_text.yview)
        self.info_text.configure(yscrollcommand=scrollbar.set)
        
        self.info_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.info_text.insert("1.0", "就绪。输入上限值（例如20）并点击'生成偏序图'。\n")
        self.info_text.insert("2.0", "示例：20会生成1到20的整除关系图。\n")
        self.info_text.insert("3.0", "注意：较大的数值（>100）可能需要较长时间计算。")
        self.info_text.config(state=tk.DISABLED)
        
        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, 
                                           maximum=100, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=(0, 5))
        
        # 图表框架
        graph_frame = ttk.LabelFrame(main_frame, text="整除关系偏序图", padding="5")
        graph_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建matplotlib图形
        self.figure, self.ax = plt.subplots(figsize=(10, 7), dpi=100)
        self.figure.patch.set_facecolor('#ffffff')
        self.ax.set_facecolor('#ffffff')
        
        # 初始提示文字
        # self.ax.text(0.5, 0.5, "整除关系偏序图生成器\n\n输入上限值（例如20）\n点击'生成偏序图'按钮", 
                   # horizontalalignment='center', verticalalignment='center',
                   # transform=self.ax.transAxes, fontsize=12, color='gray', 
                   # alpha=0.7, multialignment='center')
        self.ax.axis('off')
        
        # 创建canvas
        self.canvas = FigureCanvasTkAgg(self.figure, graph_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, 
                              relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X, pady=(5, 0))
        
        # 绑定事件
        self.upper_limit_entry.bind('<Return>', lambda e: self.generate_lattice())
        
    def set_example_values(self):
        """设置示例值"""
        examples = ["10", "20", "30", "50", "100"]
        
        def on_select():
            selection = listbox.curselection()
            if selection:
                value = listbox.get(selection[0])
                self.upper_limit_var.set(value)
            popup.destroy()
        
        popup = tk.Toplevel(self.root)
        popup.title("选择示例")
        popup.geometry("200x150")
        popup.transient(self.root)
        popup.grab_set()
        
        tk.Label(popup, text="选择上限示例:", font=("Arial", 10)).pack(pady=5)
        
        listbox = tk.Listbox(popup, height=5)
        for example in examples:
            listbox.insert(tk.END, example)
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        listbox.selection_set(0)
        
        ttk.Button(popup, text="确定", command=on_select).pack(pady=5)
        
    def update_progress(self, value, text=""):
        """更新进度条"""
        self.progress_var.set(value)
        if text:
            self.status_var.set(text)
        self.root.update_idletasks()
    
    def get_divisors(self, n: int) -> List[int]:
        """获取n的所有真因子（不包括n本身）"""
        divisors = []
        for i in range(1, int(math.sqrt(n)) + 1):
            if n % i == 0:
                divisors.append(i)
                if i != 1 and i != n // i and n // i != n:
                    divisors.append(n // i)
        return sorted(divisors)
    
    def is_prime(self, n: int) -> bool:
        """判断是否为质数"""
        if n < 2:
            return False
        for i in range(2, int(math.sqrt(n)) + 1):
            if n % i == 0:
                return False
        return True
    
    def compute_direct_edges(self, numbers: List[int]) -> List[Tuple[int, int]]:
        """计算直接整除关系（哈斯图边）"""
        edges = []
        n = len(numbers)
        
        for i in range(n):
            for j in range(i + 1, n):
                if numbers[j] % numbers[i] == 0:
                    # 检查是否直接关系
                    is_direct = True
                    for k in range(i + 1, j):
                        if (numbers[j] % numbers[k] == 0 and 
                            numbers[k] % numbers[i] == 0):
                            is_direct = False
                            break
                    if is_direct:
                        edges.append((numbers[i], numbers[j]))
        
        return edges
    
    def compute_direct_edges_optimized(self, numbers: List[int]) -> List[Tuple[int, int]]:
        """优化的直接整除关系计算"""
        edges = []
        num_set = set(numbers)
        
        for i, a in enumerate(numbers):
            # 只检查a的倍数
            for multiple in range(2 * a, numbers[-1] + 1, a):
                if multiple in num_set:
                    # 检查是否直接关系
                    is_direct = True
                    for b in numbers:
                        if a < b < multiple and multiple % b == 0 and b % a == 0:
                            is_direct = False
                            break
                    if is_direct:
                        edges.append((a, multiple))
        
        return edges
    
    def compute_levels(self, G: nx.DiGraph, numbers: List[int]) -> Dict[int, int]:
        """计算每个节点的层次（1在最底层）"""
        # 使用拓扑排序计算层次
        levels = {}
        
        # 找到所有入度为0的节点（最底层）
        for node in numbers:
            if G.in_degree(node) == 0:
                levels[node] = 0
        
        # 拓扑排序
        remaining = set(numbers) - set(levels.keys())
        
        while remaining:
            changed = False
            for node in list(remaining):
                # 获取所有前驱
                predecessors = list(G.predecessors(node))
                
                # 如果所有前驱都已分配层次
                if all(pred in levels for pred in predecessors) and predecessors:
                    # 层次是前驱的最大层次+1
                    max_pred_level = max(levels[pred] for pred in predecessors)
                    levels[node] = max_pred_level + 1
                    remaining.remove(node)
                    changed = True
            
            if not changed and remaining:
                # 处理循环依赖（应该不会发生）
                for node in list(remaining):
                    if node not in levels:
                        levels[node] = 0
                        remaining.remove(node)
        
        return levels
    
    def generate_lattice(self):
        """生成整除关系偏序图"""
        try:
            # 获取输入的上限
            upper_limit_str = self.upper_limit_var.get().strip()
            if not upper_limit_str:
                messagebox.showerror("错误", "请输入上限值")
                return
                
            upper_limit = int(upper_limit_str)
            
            if upper_limit < 1:
                messagebox.showerror("错误", "上限必须大于等于1")
                return
            elif upper_limit < 2:
                messagebox.showerror("错误", "上限必须大于等于2")
                return
            elif upper_limit > 200:
                if not messagebox.askyesno("提示", 
                    f"上限 {upper_limit} 较大，生成可能需要一些时间。\n是否继续？"):
                    return
            
            # 重置进度
            self.update_progress(0, "开始生成...")
            
            # 生成节点
            self.update_progress(10, "生成节点...")
            numbers = list(range(1, upper_limit + 1))
            
            # 创建有向图
            self.update_progress(20, "创建图结构...")
            G = nx.DiGraph()
            G.add_nodes_from(numbers)
            
            # 添加整除关系边
            self.update_progress(30, "计算整除关系...")
            if upper_limit <= 100:
                edges = self.compute_direct_edges(numbers)
            else:
                edges = self.compute_direct_edges_optimized(numbers)
            
            G.add_edges_from(edges)
            
            # 计算层次
            self.update_progress(50, "计算层次结构...")
            levels = self.compute_levels(G, numbers)
            
            # 按层次分组
            level_groups = defaultdict(list)
            for node, level in levels.items():
                level_groups[level].append(node)
            
            # 创建布局
            self.update_progress(60, "创建布局...")
            pos = {}
            
            # 找到最大层次
            max_level = max(levels.values()) if levels else 0
            
            for level, nodes in level_groups.items():
                nodes_sorted = sorted(nodes)
                n_nodes = len(nodes_sorted)
                
                if self.vertical_layout_var.get():
                    # 垂直布局
                    y_pos = level
                    if n_nodes == 1:
                        x_positions = [0]
                    else:
                        x_positions = [i - (n_nodes - 1) / 2 for i in range(n_nodes)]
                    
                    for node, x in zip(nodes_sorted, x_positions):
                        pos[node] = (x, y_pos)
                else:
                    # 水平布局
                    x_pos = level
                    if n_nodes == 1:
                        y_positions = [0]
                    else:
                        y_positions = [i - (n_nodes - 1) / 2 for i in range(n_nodes)]
                    
                    for node, y in zip(nodes_sorted, y_positions):
                        pos[node] = (x_pos, y)
            
            # 保存图数据
            self.G = G
            self.pos = pos
            
            # 绘制图形
            self.update_progress(80, "绘制图形...")
            self.draw_graph(G, pos, levels, level_groups, edges, numbers, upper_limit)
            
            # 更新信息
            self.update_progress(100, "完成！")
            
        except ValueError as e:
            messagebox.showerror("错误", f"请输入有效的数字\n错误: {str(e)}")
            self.status_var.set("错误：请输入有效的数字")
        except Exception as e:
            messagebox.showerror("错误", f"生成图表时出错:\n{str(e)}")
            self.status_var.set(f"错误: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def draw_graph(self, G, pos, levels, level_groups, edges, numbers, upper_limit):
        """绘制图形"""
        # 清空图形
        self.ax.clear()
        
        # 设置颜色
        if self.color_by_layer_var.get() and level_groups:
            num_levels = len(level_groups)
            if num_levels > 1:
                cmap = plt.cm.viridis
                colors = cmap([i/(num_levels-1) for i in range(num_levels)])
                node_colors = {node: colors[levels[node]] for node in numbers}
            else:
                node_colors = {node: '#4CAF50' for node in numbers}
        else:
            # 根据节点类型着色
            node_colors = {}
            for node in numbers:
                if node == 1:
                    node_colors[node] = '#2196F3'  # 蓝色
                elif self.is_prime(node):
                    node_colors[node] = '#F44336'  # 红色
                else:
                    node_colors[node] = '#4CAF50'  # 绿色
        
        # 绘制边
        edge_colors = ['#AAAAAA' for _ in G.edges()]
        nx.draw_networkx_edges(G, pos, ax=self.ax, 
                              arrows=True, arrowsize=15,
                              edge_color=edge_colors, width=1.2, alpha=0.6,
                              connectionstyle='arc3,rad=0.1')
        
        # 绘制节点
        node_size = 600 if len(numbers) <= 30 else 500 if len(numbers) <= 50 else 400
        nodes = nx.draw_networkx_nodes(G, pos, ax=self.ax, 
                                     node_size=node_size,
                                     node_color=[node_colors[node] for node in G.nodes()])
        nodes.set_edgecolor('black')
        nodes.set_linewidth(1.2)
        
        # 添加节点标签
        if self.show_numbers_var.get():
            labels = {node: str(node) for node in G.nodes()}
            font_size = 9 if len(numbers) <= 30 else 8 if len(numbers) <= 50 else 7
            nx.draw_networkx_labels(G, pos, labels, ax=self.ax, 
                                  font_size=font_size, font_weight='bold',
                                  font_family='Arial')
        
        # 添加边标签
        if self.show_edge_labels_var.get() and len(edges) <= 50:
            edge_labels = {(u, v): f"{v}/{u}={v//u}" for u, v in edges}
            nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, ax=self.ax,
                                        font_size=7, alpha=0.7, label_pos=0.5)
        
        # 设置标题
        layout_type = "Vertical" if self.vertical_layout_var.get() else "Plain"
        title = f"1 ~ {upper_limit}({layout_type})"
        self.ax.set_title(title, fontsize=14, pad=20, fontweight='bold')
        
        # 添加坐标轴和网格
        if self.show_grid_var.get():
            self.ax.grid(True, alpha=0.2, linestyle='--')
        
        if self.vertical_layout_var.get():
            self.ax.set_xlabel("Node", fontsize=10)
            self.ax.set_ylabel("Level", fontsize=10)
            
            # 反转y轴，使1在底部
            y_min, y_max = self.ax.get_ylim()
            self.ax.set_ylim(y_max, y_min)
        else:
            self.ax.set_xlabel("Level", fontsize=10)
            self.ax.set_ylabel("Node", fontsize=10)
        
        # 计算统计信息
        node_count = len(numbers)
        edge_count = len(edges)
        level_count = len(level_groups)
        
        prime_nodes = [n for n in numbers if self.is_prime(n) and n > 1]
        prime_count = len(prime_nodes)
        
        # 更新信息面板
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete("1.0", tk.END)
        
        info_lines = []
        info_lines.append(f"● 节点数: {node_count}, 边数: {edge_count}, 层次数: {level_count}")
        
        if prime_count > 0:
            info_lines.append(f"● 质数节点: {prime_count}个")
            if prime_count <= 15:
                primes_str = ", ".join(map(str, prime_nodes))
                info_lines.append(f"● 质数: {primes_str}")
        
        # 找到具有最多因子的节点
        max_divisors = 0
        max_divisors_node = 1
        for n in numbers:
            divisors = len(self.get_divisors(n)) + 1  # 包括自身
            if divisors > max_divisors:
                max_divisors = divisors
                max_divisors_node = n
        
        info_lines.append(f"● 最多因子的节点: {max_divisors_node} (有{max_divisors}个因子)")
        
        # 找到具有最多边的节点
        if G.edges():
            max_out_edges = max(G.out_degree(), key=lambda x: x[1])
            max_in_edges = max(G.in_degree(), key=lambda x: x[1])
            info_lines.append(f"● 最多出边: 节点{max_out_edges[0]} ({max_out_edges[1]}条)")
            info_lines.append(f"● 最多入边: 节点{max_in_edges[0]} ({max_in_edges[1]}条)")
        
        info_lines.append(f"● 生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 插入信息
        for i, line in enumerate(info_lines, 1):
            self.info_text.insert(tk.END, line + "\n")
        
        self.info_text.config(state=tk.DISABLED)
        
        # 调整布局
        plt.tight_layout()
        
        # 更新canvas
        self.canvas.draw()
        
        # 更新状态
        self.status_var.set(f"生成完成！节点: {node_count}, 边: {edge_count}, 层次: {level_count}")
    
    def clear_graph(self):
        """清空图表"""
        self.ax.clear()
        self.ax.set_facecolor('#ffffff')
        # self.ax.text(0.5, 0.5, "整除关系偏序图生成器\n\n输入上限值（例如20）\n点击'生成偏序图'按钮", 
                   # horizontalalignment='center', verticalalignment='center',
                   # transform=self.ax.transAxes, fontsize=12, color='gray', 
                   # alpha=0.7, multialignment='center')
        self.ax.axis('off')
        self.canvas.draw()
        
        # 清空信息面板
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete("1.0", tk.END)
        self.info_text.insert("1.0", "图表已清空。输入上限值并点击'生成偏序图'。")
        self.info_text.config(state=tk.DISABLED)
        
        # 重置进度
        self.update_progress(0, "就绪")
        
        self.G = None
        self.pos = None
        
        self.status_var.set("图表已清空")
    
    def export_graph(self):
        """导出图形"""
        if self.G is None or self.pos is None:
            messagebox.showwarning("警告", "没有可导出的图形")
            return
            
        filetypes = [
            ("PNG 文件", "*.png"),
            ("PDF 文件", "*.pdf"),
            ("SVG 文件", "*.svg"),
            ("所有文件", "*.*")
        ]
        
        filename = simpledialog.askstring("导出图形", "请输入文件名（不含扩展名）:")
        if not filename:
            return
            
        # 创建新图形用于导出
        export_fig, export_ax = plt.subplots(figsize=(12, 9), dpi=300)
        
        # 重新绘制
        numbers = list(self.G.nodes())
        edges = list(self.G.edges())
        
        # 计算层次（重新计算，因为可能已改变设置）
        if self.color_by_layer_var.get():
            levels = {}
            for node in self.G.nodes():
                predecessors = list(self.G.predecessors(node))
                if not predecessors:
                    levels[node] = 0
                else:
                    levels[node] = max(levels[p] for p in predecessors) + 1
            
            num_levels = max(levels.values()) + 1
            cmap = plt.cm.viridis
            colors = cmap([i/(num_levels-1) for i in range(num_levels)]) if num_levels > 1 else ['#4CAF50']
            node_colors = {node: colors[levels[node]] for node in numbers}
        else:
            node_colors = {node: '#4CAF50' for node in numbers}
        
        # 绘制
        nx.draw_networkx_edges(self.G, self.pos, ax=export_ax, 
                              arrows=True, arrowsize=20,
                              edge_color='gray', width=1.5, alpha=0.7,
                              connectionstyle='arc3,rad=0.1')
        
        nx.draw_networkx_nodes(self.G, self.pos, ax=export_ax, 
                             node_size=800,
                             node_color=[node_colors[node] for node in self.G.nodes()])
        
        if self.show_numbers_var.get():
            labels = {node: str(node) for node in self.G.nodes()}
            nx.draw_networkx_labels(self.G, self.pos, labels, ax=export_ax, 
                                  font_size=10, font_weight='bold')
        
        export_ax.axis('off')
        plt.tight_layout()
        
        # 保存文件
        try:
            for ext in ['.png', '.pdf', '.svg']:
                export_fig.savefig(f"{filename}{ext}", dpi=300, bbox_inches='tight')
            messagebox.showinfo("导出成功", f"图形已导出为:\n{filename}.png\n{filename}.pdf\n{filename}.svg")
        except Exception as e:
            messagebox.showerror("导出失败", f"导出图形时出错:\n{str(e)}")
        finally:
            plt.close(export_fig)

def main():
    try:
        root = tk.Tk()
        app = DivisibilityLatticeApp(root)
        
        # 设置窗口图标（可选）
        try:
            root.iconbitmap(default=None)  # 可以使用图标文件路径
        except:
            pass
            
        root.mainloop()
    except Exception as e:
        print(f"程序启动错误: {e}")
        import traceback
        traceback.print_exc()
        messagebox.showerror("启动错误", f"程序启动失败:\n{str(e)}")

if __name__ == "__main__":
    main()