import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import random
import time
from collections import defaultdict, Counter
import numpy as np
from itertools import permutations, combinations
import copy
import threading
from queue import Queue
import warnings
warnings.filterwarnings('ignore')

class GraphComparisonGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("图比较与分析系统 v3.1")
        self.root.geometry("1350x810")
        
        # 创建两个图
        self.G1 = nx.Graph()
        self.G2 = nx.Graph()
        
        # 设置随机种子
        random.seed()
        
        self.setup_ui()
        
    def setup_ui(self):
        # 控制面板
        control_frame = ttk.LabelFrame(self.root, text="控制面板", padding=10)
        control_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        
        # 顶点数设置
        ttk.Label(control_frame, text="顶点数:").grid(row=0, column=0, padx=5)
        self.vertex_count = tk.StringVar(value="8")
        ttk.Spinbox(control_frame, from_=3, to=20, textvariable=self.vertex_count, 
                   width=8).grid(row=0, column=1, padx=5)
        
        # 图类型选择
        ttk.Label(control_frame, text="图类型:").grid(row=0, column=2, padx=5)
        self.graph_type = tk.StringVar(value="随机图")
        graph_types = [("随机图", "随机图"), 
                      ("平面图", "平面图"),
                      ("正则图", "正则图"),
                      ("二分图", "二分图"),
                      ("小世界图", "小世界图"),
                      ("无标度图", "无标度图")]
        
        graph_type_menu = ttk.Combobox(control_frame, textvariable=self.graph_type, 
                                      values=[g[1] for g in graph_types], width=10)
        graph_type_menu.grid(row=0, column=3, padx=5)
        
        # 连接概率/度参数
        ttk.Label(control_frame, text="连接概率:").grid(row=0, column=4, padx=5)
        self.edge_prob = tk.StringVar(value="0.5")
        ttk.Spinbox(control_frame, from_=0.1, to=0.9, increment=0.1, 
                    textvariable=self.edge_prob, width=8).grid(row=0, column=5, padx=5)
        
        # 布局选择
        ttk.Label(control_frame, text="布局:").grid(row=0, column=6, padx=5)
        self.layout_type = tk.StringVar(value="spring")
        layout_menu = ttk.Combobox(control_frame, textvariable=self.layout_type, 
                                  values=["spring", "circular", "shell", "kamada_kawai", "spectral", "random"], 
                                  width=10)
        layout_menu.grid(row=0, column=7, padx=5)
        
        # 生成按钮
        ttk.Button(control_frame, text="生成随机图", 
                  command=self.generate_graphs).grid(row=0, column=8, padx=5)
        
        # 图比较框架
        compare_frame = ttk.LabelFrame(self.root, text="图比较分析", padding=10)
        compare_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        
        # 比较按钮
        self.compare_button = ttk.Button(compare_frame, text="比较图属性", 
                                        command=self.compare_graphs)
        self.compare_button.pack(side=tk.LEFT, padx=5)
        
        # 状态标签
        self.status_label = ttk.Label(compare_frame, text="就绪")
        self.status_label.pack(side=tk.LEFT, padx=20)
        
        # 图显示框架
        graph_frame = ttk.Frame(self.root)
        graph_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=10, pady=5)
        
        # 左侧：图1显示
        graph1_frame = ttk.LabelFrame(graph_frame, text="图 G₁", padding=10)
        graph1_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # 右侧：图2显示
        graph2_frame = ttk.LabelFrame(graph_frame, text="图 G₂", padding=10)
        graph2_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        # 图1画布
        self.fig1 = Figure(figsize=(5.5, 4.5), dpi=100)
        self.canvas1 = FigureCanvasTkAgg(self.fig1, graph1_frame)
        self.canvas1.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 图2画布
        self.fig2 = Figure(figsize=(5.5, 4.5), dpi=100)
        self.canvas2 = FigureCanvasTkAgg(self.fig2, graph2_frame)
        self.canvas2.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 图信息标签
        self.info_frame = ttk.Frame(graph_frame)
        self.info_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=5)
        
        self.info_label1 = ttk.Label(self.info_frame, text="G₁: 等待生成...")
        self.info_label1.pack(side=tk.LEFT, padx=20)
        
        self.info_label2 = ttk.Label(self.info_frame, text="G₂: 等待生成...")
        self.info_label2.pack(side=tk.LEFT, padx=20)
        
        # 结果显示区域
        result_frame = ttk.LabelFrame(self.root, text="图比较结果与详细信息", padding=10)
        result_frame.grid(row=3, column=0, columnspan=2, sticky="nsew", padx=10, pady=5)
        
        # 创建结果标签页
        self.notebook = ttk.Notebook(result_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # 比较结果标签页
        compare_tab = ttk.Frame(self.notebook)
        self.notebook.add(compare_tab, text="图比较结果")
        
        self.compare_text = scrolledtext.ScrolledText(compare_tab, height=12, width=100)
        self.compare_text.pack(fill=tk.BOTH, expand=True)
        
        # 详细信息标签页
        detail_tab = ttk.Frame(self.notebook)
        self.notebook.add(detail_tab, text="图详细信息")
        
        self.detail_text = scrolledtext.ScrolledText(detail_tab, height=12, width=100)
        self.detail_text.pack(fill=tk.BOTH, expand=True)
        
        # 操作日志标签页
        self.log_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.log_tab, text="操作日志")
        
        self.log_text = scrolledtext.ScrolledText(self.log_tab, height=12, width=100)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 图属性说明标签页
        help_tab = ttk.Frame(self.notebook)
        self.notebook.add(help_tab, text="图属性说明")
        
        help_text = """
        图属性比较说明：
        
        1. 基本属性比较：
           - 顶点数和边数比较
           - 图密度比较
           - 平均度比较
        
        2. 度分布比较：
           - 度序列统计
           - 最大度、最小度比较
           - 度分布直方图
        
        3. 连通性分析：
           - 连通分支数量比较
           - 连通分支大小分布
           - 是否连通图
        
        4. 中心性度量：
           - 度中心性
           - 接近中心性
           - 介数中心性
        
        5. 路径分析：
           - 平均最短路径长度
           - 图的直径
           - 聚类系数
        
        6. 特殊结构检测：
           - 环检测
           - 完全子图检测
           - 割点检测
        """
        
        help_label = tk.Text(help_tab, wrap=tk.WORD, height=12)
        help_label.insert(1.0, help_text)
        help_label.config(state=tk.DISABLED)
        help_label.pack(fill=tk.BOTH, expand=True)
        
        # 操作按钮框架
        bottom_frame = ttk.Frame(self.root)
        bottom_frame.grid(row=4, column=0, columnspan=2, pady=5)
        
        ttk.Button(bottom_frame, text="设置同构图", 
                  command=self.set_isomorphic).pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="交换图", 
                  command=self.swap_graphs).pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="清空图", 
                  command=self.clear_graphs).pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="保存图", 
                  command=self.save_graphs).pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="重新布局", 
                  command=self.redraw_graphs).pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="分析单个图", 
                  command=self.analyze_single_graph).pack(side=tk.LEFT, padx=5)
        
        # 配置网格权重
        self.root.grid_rowconfigure(2, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(3, weight=1)
        self.root.grid_rowconfigure(4, weight=0)
        
        # 初始生成图
        self.generate_graphs()
    
    def generate_random_graph(self, graph_type, n, p):
        """生成各种类型的随机图"""
        if n < 3:
            n = 3
        
        if graph_type == "随机图":
            # 生成随机图
            G = nx.fast_gnp_random_graph(n, p, seed=random.randint(1, 1000))
            
        elif graph_type == "平面图":
            # 生成接近平面图的图
            G = nx.Graph()
            G.add_nodes_from(range(n))
            
            # 先构建一个环
            for i in range(n):
                G.add_edge(i, (i+1) % n)
            
            # 随机添加边，但不超过平面图的最大边数
            max_edges = 3*n - 6
            current_edges = n
            
            # 添加随机边
            for _ in range(int((max_edges - n) * p)):
                u, v = random.sample(range(n), 2)
                if not G.has_edge(u, v):
                    G.add_edge(u, v)
                    current_edges += 1
                    if current_edges >= max_edges:
                        break
        
        elif graph_type == "正则图":
            # 正则图
            k = int(p * (n-1))
            k = max(2, min(k, n-1))
            try:
                G = nx.random_regular_graph(k, n, seed=random.randint(1, 1000))
            except:
                # 如果无法生成正则图，则生成环图
                G = nx.cycle_graph(n)
        
        elif graph_type == "二分图":
            # 二分图
            n1 = n // 2
            n2 = n - n1
            G = nx.complete_bipartite_graph(n1, n2)
            # 随机删除边
            edges = list(G.edges())
            for u, v in edges:
                if random.random() > p:
                    G.remove_edge(u, v)
        
        elif graph_type == "小世界图":
            # 小世界图
            k = int(p * 4) + 2
            k = min(k, n-1)
            G = nx.watts_strogatz_graph(n, k, 0.3, seed=random.randint(1, 1000))
        
        elif graph_type == "无标度图":
            # 无标度图
            m = int(p * 3) + 1
            m = min(m, n-1)
            G = nx.barabasi_albert_graph(n, m, seed=random.randint(1, 1000))
        
        else:
            G = nx.fast_gnp_random_graph(n, p, seed=random.randint(1, 1000))
        
        # 确保图是连通的
        if not nx.is_connected(G):
            # 添加边使图连通
            components = list(nx.connected_components(G))
            for i in range(len(components)-1):
                node1 = random.choice(list(components[i]))
                node2 = random.choice(list(components[i+1]))
                G.add_edge(node1, node2)
        
        return G
    
    def generate_graphs(self):
        """生成两个随机图"""
        try:
            n = int(self.vertex_count.get())
            p = float(self.edge_prob.get())
            graph_type = self.graph_type.get()
            
            if n < 3:
                messagebox.showerror("错误", "顶点数至少为3")
                return
            
            if n > 20:
                messagebox.showwarning("警告", "顶点数过大可能导致性能问题，建议不超过20")
            
            # 清空日志
            self.log_text.delete(1.0, tk.END)
            self.log_text.insert(tk.END, f"正在生成随机图...\n")
            self.log_text.insert(tk.END, f"类型: {graph_type}, 顶点数: {n}, 连接概率: {p}\n")
            
            # 生成两个随机图
            self.G1 = self.generate_random_graph(graph_type, n, p)
            self.G2 = self.generate_random_graph(graph_type, n, p)
            
            # 确保顶点标签一致
            self.G1 = nx.convert_node_labels_to_integers(self.G1)
            self.G2 = nx.convert_node_labels_to_integers(self.G2)
            
            # 绘制图
            self.draw_graphs()
            
            # 更新信息标签
            self.update_graph_info()
            
            # 显示成功消息
            self.status_label.config(text=f"已生成{graph_type}图 (n={n}, p={p})")
            self.log_text.insert(tk.END, f"图生成完成！\n")
            self.log_text.see(tk.END)
            
        except Exception as e:
            messagebox.showerror("生成错误", f"生成图时出错: {str(e)}")
    
    def get_graph_layout(self, G, layout_method):
        """安全获取图布局"""
        try:
            if len(G) == 0:
                return {}
            elif len(G) == 1:
                return {0: (0, 0)}
            
            if layout_method == "spring":
                pos = nx.spring_layout(G, seed=random.randint(1, 1000), k=2/np.sqrt(len(G)))
            elif layout_method == "circular":
                pos = nx.circular_layout(G)
            elif layout_method == "shell":
                if len(G) <= 1:
                    pos = {0: (0, 0)} if len(G) == 1 else {}
                elif len(G) <= 5:
                    pos = nx.shell_layout(G, [list(G.nodes())])
                else:
                    # 将节点分成2-3个shell
                    nodes = list(G.nodes())
                    shells = []
                    if len(nodes) > 8:
                        shells = [nodes[:3], nodes[3:6], nodes[6:]]
                    else:
                        shells = [nodes[:len(nodes)//2], nodes[len(nodes)//2:]]
                    pos = nx.shell_layout(G, shells)
            elif layout_method == "kamada_kawai":
                pos = nx.kamada_kawai_layout(G)
            elif layout_method == "spectral":
                pos = nx.spectral_layout(G)
            elif layout_method == "random":
                pos = nx.random_layout(G, seed=random.randint(1, 1000))
            else:
                pos = nx.spring_layout(G, seed=random.randint(1, 1000), k=2/np.sqrt(len(G)))
            
            return pos
        except Exception as e:
            # 如果布局失败，使用spring布局
            try:
                return nx.spring_layout(G, seed=random.randint(1, 1000))
            except:
                return nx.random_layout(G, seed=random.randint(1, 1000))
    
    def normalize_positions(self, pos):
        """标准化位置坐标，使其在[-1, 1]范围内"""
        if not pos:
            return pos
            
        x_vals = [pos[node][0] for node in pos]
        y_vals = [pos[node][1] for node in pos]
        
        if not x_vals or not y_vals:
            return pos
        
        # 找到边界
        x_min, x_max = min(x_vals), max(x_vals)
        y_min, y_max = min(y_vals), max(y_vals)
        
        # 如果所有点在同一位置，创建一个小范围
        if x_max - x_min < 0.001:
            x_min, x_max = -0.5, 0.5
        if y_max - y_min < 0.001:
            y_min, y_max = -0.5, 0.5
        
        # 计算缩放因子
        x_range = x_max - x_min
        y_range = y_max - y_min
        
        # 归一化到[-1, 1]范围
        normalized_pos = {}
        for node in pos:
            x = pos[node][0]
            y = pos[node][1]
            
            # 归一化
            norm_x = 2 * (x - x_min) / x_range - 1 if x_range > 0 else 0
            norm_y = 2 * (y - y_min) / y_range - 1 if y_range > 0 else 0
            
            # 稍微缩放以避免边界
            scale = 0.9
            normalized_pos[node] = (norm_x * scale, norm_y * scale)
        
        return normalized_pos
    
    def draw_graphs(self):
        """绘制两个图"""
        try:
            # 清空图形
            self.fig1.clear()
            self.fig2.clear()
            
            # 获取布局类型
            layout_method = self.layout_type.get()
            
            # 安全获取布局
            pos1 = self.get_graph_layout(self.G1, layout_method)
            pos2 = self.get_graph_layout(self.G2, layout_method)
            
            # 标准化位置
            pos1 = self.normalize_positions(pos1)
            pos2 = self.normalize_positions(pos2)
            
            # 绘制图1
            ax1 = self.fig1.add_subplot(111)
            
            # 计算节点大小和颜色基于度数
            if len(self.G1) > 0:
                degrees1 = [self.G1.degree(n) for n in self.G1.nodes()]
                max_deg1 = max(degrees1) if degrees1 else 1
                node_size1 = [300 + d*50 for d in degrees1]
                node_color1 = plt.cm.viridis([d/max_deg1 if max_deg1 > 0 else 0.5 for d in degrees1])
                
                # 绘制节点
                nx.draw_networkx_nodes(self.G1, pos1, ax=ax1, node_size=node_size1, 
                                     node_color=node_color1, alpha=0.8, edgecolors='black')
                
                # 绘制边
                nx.draw_networkx_edges(self.G1, pos1, ax=ax1, alpha=0.5, width=1.5, 
                                     edge_color='gray')
                
                # 绘制标签
                nx.draw_networkx_labels(self.G1, pos1, ax=ax1, font_size=10, 
                                      font_weight='bold', font_color='black')
            
            # 设置统一的坐标轴范围
            ax1.set_xlim([-1.1, 1.1])
            ax1.set_ylim([-1.1, 1.1])
            ax1.set_aspect('equal')
            ax1.set_title(f"G₁ - {layout_method}", fontsize=12, fontweight='bold')
            ax1.axis('off')
            
            # 绘制图2
            ax2 = self.fig2.add_subplot(111)
            
            # 计算节点大小和颜色基于度数
            if len(self.G2) > 0:
                degrees2 = [self.G2.degree(n) for n in self.G2.nodes()]
                max_deg2 = max(degrees2) if degrees2 else 1
                node_size2 = [300 + d*50 for d in degrees2]
                node_color2 = plt.cm.plasma([d/max_deg2 if max_deg2 > 0 else 0.5 for d in degrees2])
                
                # 绘制节点
                nx.draw_networkx_nodes(self.G2, pos2, ax=ax2, node_size=node_size2, 
                                     node_color=node_color2, alpha=0.8, edgecolors='black')
                
                # 绘制边
                nx.draw_networkx_edges(self.G2, pos2, ax=ax2, alpha=0.5, width=1.5, 
                                     edge_color='gray')
                
                # 绘制标签
                nx.draw_networkx_labels(self.G2, pos2, ax=ax2, font_size=10, 
                                      font_weight='bold', font_color='black')
            
            # 设置统一的坐标轴范围
            ax2.set_xlim([-1.1, 1.1])
            ax2.set_ylim([-1.1, 1.1])
            ax2.set_aspect('equal')
            ax2.set_title(f"G₂ - {layout_method}", fontsize=12, fontweight='bold')
            ax2.axis('off')
            
            # 调整布局
            self.fig1.tight_layout()
            self.fig2.tight_layout()
            
            # 更新画布
            self.canvas1.draw()
            self.canvas2.draw()
            
        except Exception as e:
            print(f"绘制图时出错: {e}")
            # 如果出错，使用简单绘制
            self.fig1.clear()
            self.fig2.clear()
            
            ax1 = self.fig1.add_subplot(111)
            ax2 = self.fig2.add_subplot(111)
            
            if len(self.G1) > 0:
                pos1 = nx.spring_layout(self.G1, seed=42)
                nx.draw(self.G1, pos1, ax=ax1, with_labels=True, node_color='skyblue', 
                       node_size=500, edgecolors='black')
                ax1.set_xlim([-1, 1])
                ax1.set_ylim([-1, 1])
                ax1.set_aspect('equal')
                ax1.set_title(f"图 G₁")
            
            if len(self.G2) > 0:
                pos2 = nx.spring_layout(self.G2, seed=24)
                nx.draw(self.G2, pos2, ax=ax2, with_labels=True, node_color='lightgreen', 
                       node_size=500, edgecolors='black')
                ax2.set_xlim([-1, 1])
                ax2.set_ylim([-1, 1])
                ax2.set_aspect('equal')
                ax2.set_title(f"图 G₂")
            
            ax1.axis('off')
            ax2.axis('off')
            
            self.fig1.tight_layout()
            self.fig2.tight_layout()
            
            self.canvas1.draw()
            self.canvas2.draw()
    
    def redraw_graphs(self):
        """重新绘制图形（不重新生成图）"""
        try:
            self.draw_graphs()
            self.status_label.config(text="已重新布局")
        except Exception as e:
            messagebox.showerror("错误", f"重新布局时出错: {str(e)}")
    
    def update_graph_info(self):
        """更新图信息标签"""
        if len(self.G1) > 0:
            avg_deg1 = np.mean([d for n, d in self.G1.degree()]) if len(self.G1) > 0 else 0
            info1 = f"G₁: {self.G1.number_of_nodes()}顶点, {self.G1.number_of_edges()}边, 平均度: {avg_deg1:.2f}"
        else:
            info1 = "G₁: 空图"
            
        if len(self.G2) > 0:
            avg_deg2 = np.mean([d for n, d in self.G2.degree()]) if len(self.G2) > 0 else 0
            info2 = f"G₂: {self.G2.number_of_nodes()}顶点, {self.G2.number_of_edges()}边, 平均度: {avg_deg2:.2f}"
        else:
            info2 = "G₂: 空图"
        
        self.info_label1.config(text=info1)
        self.info_label2.config(text=info2)
        
        # 更新详细信息
        self.update_detailed_info()
    
    def update_detailed_info(self):
        """更新详细信息标签页"""
        self.detail_text.delete(1.0, tk.END)
        
        # 图1信息
        self.detail_text.insert(tk.END, "="*60 + "\n")
        self.detail_text.insert(tk.END, "图 G₁ 详细信息\n")
        self.detail_text.insert(tk.END, "="*60 + "\n")
        
        n1 = self.G1.number_of_nodes()
        m1 = self.G1.number_of_edges()
        self.detail_text.insert(tk.END, f"顶点数: {n1}\n")
        self.detail_text.insert(tk.END, f"边数: {m1}\n")
        
        if n1 > 0:
            # 度序列
            deg_seq1 = sorted([d for n, d in self.G1.degree()])
            self.detail_text.insert(tk.END, f"度序列: {deg_seq1}\n")
            
            # 最大度、最小度、平均度
            degrees1 = [d for n, d in self.G1.degree()]
            self.detail_text.insert(tk.END, f"最大度: {max(degrees1)}, 最小度: {min(degrees1)}, 平均度: {np.mean(degrees1):.2f}\n")
            
            # 连通性
            is_connected1 = nx.is_connected(self.G1)
            components1 = list(nx.connected_components(self.G1))
            self.detail_text.insert(tk.END, f"连通: {is_connected1}, 连通分支数: {len(components1)}\n")
            
            # 图密度
            density1 = nx.density(self.G1)
            self.detail_text.insert(tk.END, f"密度: {density1:.4f}\n")
            
            # 中心性度量
            if n1 <= 15:  # 对小图计算中心性
                try:
                    degree_centrality1 = nx.degree_centrality(self.G1)
                    max_deg_cent1 = max(degree_centrality1.values()) if degree_centrality1 else 0
                    self.detail_text.insert(tk.END, f"最大度中心性: {max_deg_cent1:.4f}\n")
                    
                    if is_connected1 and n1 > 2:
                        closeness_centrality1 = nx.closeness_centrality(self.G1)
                        max_close_cent1 = max(closeness_centrality1.values()) if closeness_centrality1 else 0
                        self.detail_text.insert(tk.END, f"最大接近中心性: {max_close_cent1:.4f}\n")
                except:
                    self.detail_text.insert(tk.END, "中心性计算跳过（图过大）\n")
        
        # 图2信息
        self.detail_text.insert(tk.END, "\n" + "="*60 + "\n")
        self.detail_text.insert(tk.END, "图 G₂ 详细信息\n")
        self.detail_text.insert(tk.END, "="*60 + "\n")
        
        n2 = self.G2.number_of_nodes()
        m2 = self.G2.number_of_edges()
        self.detail_text.insert(tk.END, f"顶点数: {n2}\n")
        self.detail_text.insert(tk.END, f"边数: {m2}\n")
        
        if n2 > 0:
            # 度序列
            deg_seq2 = sorted([d for n, d in self.G2.degree()])
            self.detail_text.insert(tk.END, f"度序列: {deg_seq2}\n")
            
            # 最大度、最小度、平均度
            degrees2 = [d for n, d in self.G2.degree()]
            self.detail_text.insert(tk.END, f"最大度: {max(degrees2)}, 最小度: {min(degrees2)}, 平均度: {np.mean(degrees2):.2f}\n")
            
            # 连通性
            is_connected2 = nx.is_connected(self.G2)
            components2 = list(nx.connected_components(self.G2))
            self.detail_text.insert(tk.END, f"连通: {is_connected2}, 连通分支数: {len(components2)}\n")
            
            # 图密度
            density2 = nx.density(self.G2)
            self.detail_text.insert(tk.END, f"密度: {density2:.4f}\n")
            
            # 中心性度量
            if n2 <= 15:  # 对小图计算中心性
                try:
                    degree_centrality2 = nx.degree_centrality(self.G2)
                    max_deg_cent2 = max(degree_centrality2.values()) if degree_centrality2 else 0
                    self.detail_text.insert(tk.END, f"最大度中心性: {max_deg_cent2:.4f}\n")
                    
                    if is_connected2 and n2 > 2:
                        closeness_centrality2 = nx.closeness_centrality(self.G2)
                        max_close_cent2 = max(closeness_centrality2.values()) if closeness_centrality2 else 0
                        self.detail_text.insert(tk.END, f"最大接近中心性: {max_close_cent2:.4f}\n")
                except:
                    self.detail_text.insert(tk.END, "中心性计算跳过（图过大）\n")
    
    def compare_graphs(self):
        """比较两个图的属性"""
        if len(self.G1) == 0 or len(self.G2) == 0:
            messagebox.showwarning("警告", "请先生成图")
            return
        
        self.status_label.config(text="比较中...")
        self.log_text.insert(tk.END, "开始比较图属性...\n")
        
        try:
            start_time = time.time()
            self.compare_text.delete(1.0, tk.END)
            
            self.compare_text.insert(tk.END, "="*80 + "\n")
            self.compare_text.insert(tk.END, "图属性比较结果\n")
            self.compare_text.insert(tk.END, "="*80 + "\n\n")
            
            # 基本属性比较
            self.compare_basic_properties()
            
            # 度分布比较
            self.compare_degree_distributions()
            
            # 连通性比较
            self.compare_connectivity()
            
            # 路径分析比较
            self.compare_path_analysis()
            
            # 特殊结构检测
            self.detect_special_structures()
            
            total_time = time.time() - start_time
            self.compare_text.insert(tk.END, f"\n比较完成，总耗时: {total_time:.4f}秒\n")
            
            self.status_label.config(text="比较完成")
            self.log_text.insert(tk.END, f"图属性比较完成，耗时: {total_time:.4f}秒\n")
            self.log_text.see(tk.END)
            
        except Exception as e:
            self.status_label.config(text="比较错误")
            self.log_text.insert(tk.END, f"比较过程中出错: {str(e)}\n")
            messagebox.showerror("错误", f"比较图属性时出错: {str(e)}")
    
    def compare_basic_properties(self):
        """比较基本属性"""
        self.compare_text.insert(tk.END, "1. 基本属性比较:\n")
        self.compare_text.insert(tk.END, "-"*50 + "\n")
        
        n1, m1 = self.G1.number_of_nodes(), self.G1.number_of_edges()
        n2, m2 = self.G2.number_of_nodes(), self.G2.number_of_edges()
        
        # 顶点数比较
        if n1 == n2:
            self.compare_text.insert(tk.END, f"✓ 顶点数相同: {n1}\n")
        else:
            self.compare_text.insert(tk.END, f"✗✗ 顶点数不同: G₁={n1}, G₂={n2}\n")
        
        # 边数比较
        if m1 == m2:
            self.compare_text.insert(tk.END, f"✓ 边数相同: {m1}\n")
        else:
            self.compare_text.insert(tk.END, f"✗✗ 边数不同: G₁={m1}, G₂={m2}\n")
        
        # 密度比较
        density1 = nx.density(self.G1) if n1 > 1 else 0
        density2 = nx.density(self.G2) if n2 > 1 else 0
        
        self.compare_text.insert(tk.END, f"图密度: G₁={density1:.4f}, G₂={density2:.4f}\n")
        
        # 平均度比较
        avg_deg1 = np.mean([d for n, d in self.G1.degree()]) if n1 > 0 else 0
        avg_deg2 = np.mean([d for n, d in self.G2.degree()]) if n2 > 0 else 0
        
        self.compare_text.insert(tk.END, f"平均度: G₁={avg_deg1:.2f}, G₂={avg_deg2:.2f}\n")
        
        self.compare_text.insert(tk.END, "\n")
    
    def compare_degree_distributions(self):
        """比较度分布"""
        self.compare_text.insert(tk.END, "2. 度分布比较:\n")
        self.compare_text.insert(tk.END, "-"*50 + "\n")
        
        n1, n2 = self.G1.number_of_nodes(), self.G2.number_of_nodes()
        
        if n1 > 0 and n2 > 0:
            deg_seq1 = sorted([d for n, d in self.G1.degree()])
            deg_seq2 = sorted([d for n, d in self.G2.degree()])
            
            # 度序列比较
            if deg_seq1 == deg_seq2:
                self.compare_text.insert(tk.END, f"✓ 度序列相同: {deg_seq1}\n")
            else:
                self.compare_text.insert(tk.END, f"✗✗ 度序列不同\n")
                self.compare_text.insert(tk.END, f"  G₁度序列: {deg_seq1}\n")
                self.compare_text.insert(tk.END, f"  G₂度序列: {deg_seq2}\n")
            
            # 最大度最小度比较
            max_deg1, min_deg1 = max(deg_seq1), min(deg_seq1)
            max_deg2, min_deg2 = max(deg_seq2), min(deg_seq2)
            
            self.compare_text.insert(tk.END, f"最大度: G₁={max_deg1}, G₂={max_deg2}\n")
            self.compare_text.insert(tk.END, f"最小度: G₁={min_deg1}, G₂={min_deg2}\n")
            
            # 度分布统计
            deg_dist1 = Counter(deg_seq1)
            deg_dist2 = Counter(deg_seq2)
            
            self.compare_text.insert(tk.END, "度分布:\n")
            for deg in sorted(set(deg_seq1 + deg_seq2)):
                count1 = deg_dist1.get(deg, 0)
                count2 = deg_dist2.get(deg, 0)
                status = "✓" if count1 == count2 else "✗✗"
                self.compare_text.insert(tk.END, f"  度{deg}: G₁有{count1}个, G₂有{count2}个 {status}\n")
        
        self.compare_text.insert(tk.END, "\n")
    
    def compare_connectivity(self):
        """比较连通性"""
        self.compare_text.insert(tk.END, "3. 连通性分析:\n")
        self.compare_text.insert(tk.END, "-"*50 + "\n")
        
        # 连通性
        connected1 = nx.is_connected(self.G1)
        connected2 = nx.is_connected(self.G2)
        
        self.compare_text.insert(tk.END, f"连通性: G₁={'是' if connected1 else '否'}, G₂={'是' if connected2 else '否'}\n")
        
        # 连通分支
        components1 = list(nx.connected_components(self.G1))
        components2 = list(nx.connected_components(self.G2))
        
        if len(components1) == len(components2):
            self.compare_text.insert(tk.END, f"✓ 连通分支数相同: {len(components1)}\n")
        else:
            self.compare_text.insert(tk.END, f"✗✗ 连通分支数不同: G₁={len(components1)}, G₂={len(components2)}\n")
        
        # 连通分支大小分布
        comp_sizes1 = sorted([len(comp) for comp in components1], reverse=True)
        comp_sizes2 = sorted([len(comp) for comp in components2], reverse=True)
        
        self.compare_text.insert(tk.END, f"连通分支大小分布:\n")
        self.compare_text.insert(tk.END, f"  G₁: {comp_sizes1}\n")
        self.compare_text.insert(tk.END, f"  G₂: {comp_sizes2}\n")
        
        if comp_sizes1 == comp_sizes2:
            self.compare_text.insert(tk.END, f"✓ 连通分支结构相同\n")
        else:
            self.compare_text.insert(tk.END, f"✗✗ 连通分支结构不同\n")
        
        self.compare_text.insert(tk.END, "\n")
    
    def compare_path_analysis(self):
        """比较路径分析"""
        self.compare_text.insert(tk.END, "4. 路径分析:\n")
        self.compare_text.insert(tk.END, "-"*50 + "\n")
        
        n1, n2 = self.G1.number_of_nodes(), self.G2.number_of_nodes()
        
        # 只对连通图进行路径分析
        if nx.is_connected(self.G1) and n1 > 1:
            try:
                avg_path1 = nx.average_shortest_path_length(self.G1)
                diameter1 = nx.diameter(self.G1)
                self.compare_text.insert(tk.END, f"G₁ - 平均最短路径: {avg_path1:.4f}, 直径: {diameter1}\n")
            except:
                self.compare_text.insert(tk.END, "G₁路径分析失败\n")
        else:
            self.compare_text.insert(tk.END, "G₁不连通，跳过路径分析\n")
        
        if nx.is_connected(self.G2) and n2 > 1:
            try:
                avg_path2 = nx.average_shortest_path_length(self.G2)
                diameter2 = nx.diameter(self.G2)
                self.compare_text.insert(tk.END, f"G₂ - 平均最短路径: {avg_path2:.4f}, 直径: {diameter2}\n")
            except:
                self.compare_text.insert(tk.END, "G₂路径分析失败\n")
        else:
            self.compare_text.insert(tk.END, "G₂不连通，跳过路径分析\n")
        
        # 聚类系数
        try:
            clustering1 = nx.average_clustering(self.G1)
            clustering2 = nx.average_clustering(self.G2)
            self.compare_text.insert(tk.END, f"平均聚类系数: G₁={clustering1:.4f}, G₂={clustering2:.4f}\n")
        except:
            self.compare_text.insert(tk.END, "聚类系数计算失败\n")
        
        self.compare_text.insert(tk.END, "\n")
    
    def detect_special_structures(self):
        """检测特殊结构"""
        self.compare_text.insert(tk.END, "5. 特殊结构检测:\n")
        self.compare_text.insert(tk.END, "-"*50 + "\n")
        
        n1, n2 = self.G1.number_of_nodes(), self.G2.number_of_nodes()
        
        # 环检测
        try:
            cycles1 = len(list(nx.cycle_basis(self.G1)))
            cycles2 = len(list(nx.cycle_basis(self.G2)))
            self.compare_text.insert(tk.END, f"基本环数量: G₁={cycles1}, G₂={cycles2}\n")
        except:
            self.compare_text.insert(tk.END, "环检测失败\n")
        
        # 完全子图检测（小图）
        if n1 <= 10:
            try:
                # 检测最大团
                max_clique1 = max(len(clique) for clique in nx.find_cliques(self.G1)) if n1 > 0 else 0
                max_clique2 = max(len(clique) for clique in nx.find_cliques(self.G2)) if n2 > 0 else 0
                self.compare_text.insert(tk.END, f"最大团大小: G₁={max_clique1}, G₂={max_clique2}\n")
            except:
                self.compare_text.insert(tk.END, "团检测失败\n")
        
        # 割点检测
        try:
            articulation1 = len(list(nx.articulation_points(self.G1))) if n1 > 2 else 0
            articulation2 = len(list(nx.articulation_points(self.G2))) if n2 > 2 else 0
            self.compare_text.insert(tk.END, f"割点数量: G₁={articulation1}, G₂={articulation2}\n")
        except:
            self.compare_text.insert(tk.END, "割点检测失败\n")
        
        self.compare_text.insert(tk.END, "\n")
    
    def set_isomorphic(self):
        """设置G2为G1的同构图"""
        try:
            n = len(self.G1)
            if n == 0:
                messagebox.showwarning("警告", "请先生成图")
                return
            
            # 生成一个随机排列
            permutation = list(range(n))
            random.shuffle(permutation)
            
            # 创建新的图G2，作为G1的重新标记
            self.G2.clear()
            self.G2.add_nodes_from(range(n))
            
            # 重新映射边
            for u, v in self.G1.edges():
                new_u = permutation[u]
                new_v = permutation[v]
                self.G2.add_edge(new_u, new_v)
            
            # 重新绘制
            self.draw_graphs()
            self.update_graph_info()
            
            messagebox.showinfo("设置成功", f"已设置G2为G1的同构版本\n顶点映射: {permutation}")
            self.log_text.insert(tk.END, f"已设置G2为G1的同构版本\n")
        except Exception as e:
            messagebox.showerror("错误", f"设置同构时出错: {str(e)}")
            self.log_text.insert(tk.END, f"设置同构时出错: {str(e)}\n")
    
    def swap_graphs(self):
        """交换两个图"""
        self.G1, self.G2 = self.G2, self.G1
        self.draw_graphs()
        self.update_graph_info()
        self.status_label.config(text="已交换两个图")
        self.log_text.insert(tk.END, "已交换图G₁和G₂\n")
    
    def clear_graphs(self):
        """清空图"""
        self.G1.clear()
        self.G2.clear()
        self.draw_graphs()
        self.update_graph_info()
        self.compare_text.delete(1.0, tk.END)
        self.detail_text.delete(1.0, tk.END)
        self.log_text.delete(1.0, tk.END)
        self.status_label.config(text="已清空图")
        self.log_text.insert(tk.END, "已清空所有图\n")
    
    def save_graphs(self):
        """保存图为图片"""
        try:
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 保存图1
            fig1 = Figure(figsize=(6, 5), dpi=150)
            ax1 = fig1.add_subplot(111)
            pos1 = nx.spring_layout(self.G1, seed=42)
            nx.draw(self.G1, pos1, ax=ax1, with_labels=True, 
                    node_color='skyblue', node_size=700, 
                    edge_color='gray', width=2, font_size=12)
            ax1.set_title(f"Graph G1: {self.G1.number_of_nodes()} nodes, {self.G1.number_of_edges()} edges")
            fig1.savefig(f"graph1_{timestamp}.png", bbox_inches='tight', dpi=150)
            
            # 保存图2
            fig2 = Figure(figsize=(6, 5), dpi=150)
            ax2 = fig2.add_subplot(111)
            pos2 = nx.spring_layout(self.G2, seed=24)
            nx.draw(self.G2, pos2, ax=ax2, with_labels=True, 
                    node_color='lightgreen', node_size=700, 
                    edge_color='gray', width=2, font_size=12)
            ax2.set_title(f"Graph G2: {self.G2.number_of_nodes()} nodes, {self.G2.number_of_edges()} edges")
            fig2.savefig(f"graph2_{timestamp}.png", bbox_inches='tight', dpi=150)
            
            messagebox.showinfo("保存成功", f"图已保存为 graph1_{timestamp}.png 和 graph2_{timestamp}.png")
            self.log_text.insert(tk.END, f"图已保存为 graph1_{timestamp}.png 和 graph2_{timestamp}.png\n")
        except Exception as e:
            messagebox.showerror("保存错误", f"保存图时出错: {str(e)}")
            self.log_text.insert(tk.END, f"保存图时出错: {str(e)}\n")
    
    def analyze_single_graph(self):
        """分析单个图的属性"""
        if len(self.G1) == 0 and len(self.G2) == 0:
            messagebox.showwarning("警告", "请先生成图")
            return
        
        # 选择要分析的图
        choice = tk.simpledialog.askstring("选择图", "分析哪个图? (输入1或2)", initialvalue="1")
        if choice not in ["1", "2"]:
            return
        
        graph = self.G1 if choice == "1" else self.G2
        graph_name = "G₁" if choice == "1" else "G₂"
        
        self.status_label.config(text=f"分析{graph_name}中...")
        self.log_text.insert(tk.END, f"开始分析{graph_name}...\n")
        
        try:
            # 在新窗口中显示详细分析
            analysis_window = tk.Toplevel(self.root)
            analysis_window.title(f"{graph_name}详细分析")
            analysis_window.geometry("800x600")
            
            text_area = scrolledtext.ScrolledText(analysis_window, wrap=tk.WORD, width=80, height=30)
            text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # 执行分析
            analysis_text = self.analyze_graph_properties(graph, graph_name)
            text_area.insert(tk.END, analysis_text)
            text_area.config(state=tk.DISABLED)
            
            self.status_label.config(text=f"{graph_name}分析完成")
            self.log_text.insert(tk.END, f"{graph_name}分析完成\n")
            
        except Exception as e:
            self.status_label.config(text="分析错误")
            self.log_text.insert(tk.END, f"分析{graph_name}时出错: {str(e)}\n")
            messagebox.showerror("错误", f"分析图时出错: {str(e)}")
    
    def analyze_graph_properties(self, graph, name):
        """分析单个图的属性"""
        result = f"{'='*60}\n"
        result += f"图 {name} 详细分析\n"
        result += f"{'='*60}\n\n"
        
        n = graph.number_of_nodes()
        m = graph.number_of_edges()
        
        result += f"基本属性:\n"
        result += f"- 顶点数: {n}\n"
        result += f"- 边数: {m}\n"
        result += f"- 图密度: {nx.density(graph):.4f}\n" if n > 1 else "- 图密度: 0\n"
        
        if n > 0:
            # 度信息
            degrees = [d for _, d in graph.degree()]
            result += f"- 平均度: {np.mean(degrees):.2f}\n"
            result += f"- 最大度: {max(degrees)}\n"
            result += f"- 最小度: {min(degrees)}\n"
            result += f"- 度序列: {sorted(degrees)}\n"
            
            # 连通性
            is_connected = nx.is_connected(graph)
            result += f"- 连通性: {'是' if is_connected else '否'}\n"
            
            components = list(nx.connected_components(graph))
            result += f"- 连通分支数: {len(components)}\n"
            result += f"- 连通分支大小: {[len(comp) for comp in components]}\n"
            
            # 中心性度量
            if n <= 20:
                try:
                    degree_centrality = nx.degree_centrality(graph)
                    max_deg_node = max(degree_centrality, key=degree_centrality.get)
                    result += f"- 最高度中心性节点: {max_deg_node} ({degree_centrality[max_deg_node]:.4f})\n"
                    
                    if is_connected and n > 2:
                        closeness_centrality = nx.closeness_centrality(graph)
                        max_close_node = max(closeness_centrality, key=closeness_centrality.get)
                        result += f"- 最高接近中心性节点: {max_close_node} ({closeness_centrality[max_close_node]:.4f})\n"
                        
                        betweenness_centrality = nx.betweenness_centrality(graph)
                        max_between_node = max(betweenness_centrality, key=betweenness_centrality.get)
                        result += f"- 最高介数中心性节点: {max_between_node} ({betweenness_centrality[max_between_node]:.4f})\n"
                except:
                    result += "- 中心性计算跳过\n"
            
            # 路径分析（仅连通图）
            if is_connected and n > 1:
                try:
                    avg_path = nx.average_shortest_path_length(graph)
                    diameter = nx.diameter(graph)
                    result += f"- 平均最短路径长度: {avg_path:.4f}\n"
                    result += f"- 图的直径: {diameter}\n"
                except:
                    result += "- 路径分析失败\n"
            
            # 聚类系数
            try:
                avg_clustering = nx.average_clustering(graph)
                result += f"- 平均聚类系数: {avg_clustering:.4f}\n"
            except:
                result += "- 聚类系数计算失败\n"
            
            # 特殊结构
            try:
                # 环检测
                cycles = len(list(nx.cycle_basis(graph)))
                result += f"- 基本环数量: {cycles}\n"
                
                # 最大团（小图）
                if n <= 10:
                    max_clique = max(len(clique) for clique in nx.find_cliques(graph))
                    result += f"- 最大团大小: {max_clique}\n"
                
                # 割点
                if n > 2:
                    articulation_points = list(nx.articulation_points(graph))
                    result += f"- 割点数量: {len(articulation_points)}\n"
                    if articulation_points:
                        result += f"- 割点: {articulation_points}\n"
            except:
                result += "- 特殊结构检测失败\n"
        
        return result

def main():
    root = tk.Tk()
    app = GraphComparisonGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()