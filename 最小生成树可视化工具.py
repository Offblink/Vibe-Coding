import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog
import math
import os
from PIL import Image, ImageDraw, ImageTk
import tempfile

class GraphNode:
    """表示图中的节点"""
    def __init__(self, x, y, id):
        self.x = x
        self.y = y
        self.id = id
        self.radius = 15
        self.color = "lightblue"
        self.highlight_color = "yellow"
        self.dragging = False
        
    def contains_point(self, x, y):
        """检查点(x,y)是否在节点内"""
        distance = math.sqrt((x - self.x)**2 + (y - self.y)**2)
        return distance <= self.radius
    
    def draw(self, canvas, highlight=False):
        """在画布上绘制节点"""
        color = self.highlight_color if highlight else self.color
        canvas.create_oval(
            self.x - self.radius, self.y - self.radius,
            self.x + self.radius, self.y + self.radius,
            fill=color, outline="black", width=2, tags=f"node_{self.id}"
        )
        canvas.create_text(
            self.x, self.y, 
            text=str(self.id), 
            font=("Arial", 12, "bold"), 
            tags=f"node_text_{self.id}"
        )

class GraphEdge:
    """表示图中的边"""
    def __init__(self, node1, node2, weight=1):
        self.node1 = node1
        self.node2 = node2
        self.weight = weight
        self.color = "black"
        self.width = 2
        self.highlight_color = "red"
        self.highlight_width = 4
        self.weight_bbox = None  # 权重椭圆的位置
        
    def draw(self, canvas, highlight=False):
        """在画布上绘制边"""
        color = self.highlight_color if highlight else self.color
        width = self.highlight_width if highlight else self.width
        
        # 绘制边
        canvas.create_line(
            self.node1.x, self.node1.y,
            self.node2.x, self.node2.y,
            fill=color, width=width, tags=f"edge_{self.node1.id}_{self.node2.id}"
        )
        
        # 计算权重文本位置
        mid_x = (self.node1.x + self.node2.x) / 2
        mid_y = (self.node1.y + self.node2.y) / 2
        
        # 计算垂直于边的偏移量
        dx = self.node2.x - self.node1.x
        dy = self.node2.y - self.node1.y
        length = math.sqrt(dx*dx + dy*dy)
        
        if length > 0:
            offset_x = -dy / length * 20
            offset_y = dx / length * 20
        else:
            offset_x, offset_y = 0, 0
        
        # 权重椭圆的边界框
        self.weight_bbox = (
            mid_x + offset_x - 20, mid_y + offset_y - 12,
            mid_x + offset_x + 20, mid_y + offset_y + 12
        )
        
        # 绘制权重椭圆
        canvas.create_oval(
            self.weight_bbox[0], self.weight_bbox[1],
            self.weight_bbox[2], self.weight_bbox[3],
            fill="white", outline=color, width=2, tags=f"weight_box_{self.node1.id}_{self.node2.id}"
        )
        
        # 绘制权重文本
        canvas.create_text(
            mid_x + offset_x, mid_y + offset_y,
            text=str(self.weight), 
            font=("Arial", 10, "bold"), 
            fill=color,
            tags=f"weight_text_{self.node1.id}_{self.node2.id}"
        )
    
    def weight_contains_point(self, x, y):
        """检查点是否在权重椭圆内"""
        if not self.weight_bbox:
            return False
            
        # 检查点是否在椭圆内
        # 椭圆方程: ((x - cx)/a)^2 + ((y - cy)/b)^2 <= 1
        cx = (self.weight_bbox[0] + self.weight_bbox[2]) / 2
        cy = (self.weight_bbox[1] + self.weight_bbox[3]) / 2
        a = (self.weight_bbox[2] - self.weight_bbox[0]) / 2
        b = (self.weight_bbox[3] - self.weight_bbox[1]) / 2
        
        return ((x - cx) / a) ** 2 + ((y - cy) / b) ** 2 <= 1

class MinimumSpanningTreeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("最小生成树可视化工具")
        self.root.geometry("1100x750")
        
        # 初始化数据结构
        self.nodes = []
        self.edges = []
        self.mst_edges = []  # 最小生成树的边
        self.next_node_id = 1
        self.mode = "add_node"  # 当前模式: add_node, add_edge, set_weight, drag_node
        self.selected_node = None
        self.dragged_node = None
        
        # 创建UI
        self.create_widgets()
        
    def create_widgets(self):
        # 控制面板
        control_frame = tk.Frame(self.root, bg="#f0f0f0", width=250)
        control_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        # 标题
        title_label = tk.Label(
            control_frame, 
            text="最小生成树可视化工具", 
            font=("Arial", 16, "bold"),
            bg="#f0f0f0",
            fg="#2c3e50"
        )
        title_label.pack(pady=20)
        
        # 模式选择
        mode_label = tk.Label(
            control_frame, 
            text="选择模式:", 
            font=("Arial", 12, "bold"),
            bg="#f0f0f0",
            fg="#34495e"
        )
        mode_label.pack(pady=10)
        
        # 模式按钮
        self.node_mode_btn = tk.Button(
            control_frame, 
            text="添加节点", 
            width=20, 
            command=self.set_add_node_mode,
            font=("Arial", 10),
            bg="#3498db",
            fg="white",
            activebackground="#2980b9"
        )
        self.node_mode_btn.pack(pady=5)
        
        self.edge_mode_btn = tk.Button(
            control_frame, 
            text="连接节点", 
            width=20, 
            command=self.set_add_edge_mode,
            font=("Arial", 10),
            bg="#3498db",
            fg="white",
            activebackground="#2980b9"
        )
        self.edge_mode_btn.pack(pady=5)
        
        self.weight_mode_btn = tk.Button(
            control_frame, 
            text="设置权重", 
            width=20, 
            command=self.set_set_weight_mode,
            font=("Arial", 10),
            bg="#3498db",
            fg="white",
            activebackground="#2980b9"
        )
        self.weight_mode_btn.pack(pady=5)
        
        self.drag_mode_btn = tk.Button(
            control_frame, 
            text="拖动节点", 
            width=20, 
            command=self.set_drag_node_mode,
            font=("Arial", 10),
            bg="#3498db",
            fg="white",
            activebackground="#2980b9"
        )
        self.drag_mode_btn.pack(pady=5)
        
        # 分隔线
        separator = tk.Frame(control_frame, height=2, bg="#bdc3c7")
        separator.pack(fill=tk.X, pady=20, padx=10)
        
        # 算法操作按钮
        self.calc_mst_btn = tk.Button(
            control_frame, 
            text="计算最小生成树", 
            width=20, 
            command=self.calculate_mst,
            font=("Arial", 11, "bold"),
            bg="#27ae60",
            fg="white",
            activebackground="#219653"
        )
        self.calc_mst_btn.pack(pady=10)
        
        self.clear_mst_btn = tk.Button(
            control_frame, 
            text="清除高亮", 
            width=20, 
            command=self.clear_mst,
            font=("Arial", 10),
            bg="#e67e22",
            fg="white",
            activebackground="#d35400"
        )
        self.clear_mst_btn.pack(pady=5)
        
        # 分隔线
        separator2 = tk.Frame(control_frame, height=2, bg="#bdc3c7")
        separator2.pack(fill=tk.X, pady=20, padx=10)
        
        # 导出功能
        export_label = tk.Label(
            control_frame, 
            text="导出功能:", 
            font=("Arial", 12, "bold"),
            bg="#f0f0f0",
            fg="#34495e"
        )
        export_label.pack(pady=10)
        
        self.export_btn = tk.Button(
            control_frame, 
            text="导出为图片", 
            width=20, 
            command=self.export_as_image,
            font=("Arial", 10),
            bg="#9b59b6",
            fg="white",
            activebackground="#8e44ad"
        )
        self.export_btn.pack(pady=5)
        
        # 重置按钮
        self.reset_btn = tk.Button(
            control_frame, 
            text="重置画布", 
            width=20, 
            command=self.reset_canvas,
            font=("Arial", 10),
            bg="#e74c3c",
            fg="white",
            activebackground="#c0392b"
        )
        self.reset_btn.pack(pady=20)
        
        # 分隔线
        separator3 = tk.Frame(control_frame, height=2, bg="#bdc3c7")
        separator3.pack(fill=tk.X, pady=20, padx=10)
        
        # 状态显示
        self.status_label = tk.Label(
            control_frame, 
            text="模式: 添加节点", 
            font=("Arial", 10),
            bg="#f0f0f0",
            fg="#2c3e50",
            wraplength=220
        )
        self.status_label.pack(pady=20)
        
        # 分隔线
        separator4 = tk.Frame(control_frame, height=2, bg="#bdc3c7")
        separator4.pack(fill=tk.X, pady=20, padx=10)
        
        # 帮助文本
        help_text = """
使用说明:
1. 添加节点: 在画布上点击添加节点
2. 连接节点: 点击一个节点，再点击另一个节点
3. 设置权重: 点击边上的权重椭圆，输入权重
4. 拖动节点: 点击并拖动节点调整位置
5. 计算MST: 计算最小生成树
6. 导出图片: 将当前图形保存为图片
7. 重置: 清空画布重新开始

注意: 只有连通图才有生成树
        """
        help_label = tk.Label(
            control_frame, 
            text=help_text, 
            font=("Arial", 9),
            bg="#f0f0f0",
            fg="#2c3e50",
            justify=tk.LEFT
        )
        help_label.pack(pady=10, padx=5)
        
        # 画布区域
        canvas_frame = tk.Frame(self.root, bg="#2c3e50")
        canvas_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 画布标题
        canvas_title = tk.Label(
            canvas_frame,
            text="绘图区域 (在空白处点击添加节点)",
            font=("Arial", 12, "bold"),
            bg="#34495e",
            fg="white"
        )
        canvas_title.pack(fill=tk.X)
        
        self.canvas = tk.Canvas(canvas_frame, bg="white", width=850, height=700)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # 绑定画布事件
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        
        # 初始模式
        self.set_add_node_mode()
        
    def set_add_node_mode(self):
        """设置添加节点模式"""
        self.mode = "add_node"
        self.selected_node = None
        self.dragged_node = None
        self.update_status("模式: 添加节点 - 在画布上点击添加节点")
        self.update_button_colors("add_node")
        
    def set_add_edge_mode(self):
        """设置添加边模式"""
        self.mode = "add_edge"
        self.selected_node = None
        self.dragged_node = None
        self.update_status("模式: 连接节点 - 点击一个节点，再点击另一个节点")
        self.update_button_colors("add_edge")
        
    def set_set_weight_mode(self):
        """设置权重模式"""
        self.mode = "set_weight"
        self.selected_node = None
        self.dragged_node = None
        self.update_status("模式: 设置权重 - 点击边上的权重椭圆，输入新权重")
        self.update_button_colors("set_weight")
        
    def set_drag_node_mode(self):
        """设置拖动节点模式"""
        self.mode = "drag_node"
        self.selected_node = None
        self.dragged_node = None
        self.update_status("模式: 拖动节点 - 点击并拖动节点调整位置")
        self.update_button_colors("drag_node")
        
    def update_button_colors(self, active_mode):
        """更新按钮颜色以指示当前模式"""
        buttons = {
            "add_node": self.node_mode_btn,
            "add_edge": self.edge_mode_btn,
            "set_weight": self.weight_mode_btn,
            "drag_node": self.drag_mode_btn
        }
        
        # 重置所有按钮颜色
        for btn in buttons.values():
            btn.config(bg="#3498db")
        
        # 设置活动按钮颜色
        if active_mode in buttons:
            buttons[active_mode].config(bg="#2c3e50")
        
    def update_status(self, text):
        """更新状态标签"""
        self.status_label.config(text=text)
        
    def on_canvas_click(self, event):
        """处理画布点击事件"""
        x, y = event.x, event.y
        
        if self.mode == "add_node":
            # 添加新节点
            new_node = GraphNode(x, y, self.next_node_id)
            self.nodes.append(new_node)
            self.next_node_id += 1
            self.draw_graph()
            
        elif self.mode == "add_edge":
            # 检查是否点击了节点
            clicked_node = None
            for node in self.nodes:
                if node.contains_point(x, y):
                    clicked_node = node
                    break
                    
            if clicked_node:
                if self.selected_node is None:
                    # 选择第一个节点
                    self.selected_node = clicked_node
                    self.update_status(f"已选择节点 {clicked_node.id}，请选择第二个节点")
                else:
                    # 选择第二个节点，创建边
                    if self.selected_node.id != clicked_node.id:
                        # 检查边是否已存在
                        edge_exists = False
                        for edge in self.edges:
                            if (edge.node1.id == self.selected_node.id and edge.node2.id == clicked_node.id) or \
                               (edge.node1.id == clicked_node.id and edge.node2.id == self.selected_node.id):
                                edge_exists = True
                                break
                        
                        if not edge_exists:
                            # 添加新边，默认权重为1
                            new_edge = GraphEdge(self.selected_node, clicked_node, 1)
                            self.edges.append(new_edge)
                            self.update_status(f"已添加边: {self.selected_node.id} - {clicked_node.id}")
                        else:
                            self.update_status(f"边 {self.selected_node.id} - {clicked_node.id} 已存在")
                        
                        # 重置选中的节点
                        self.selected_node = None
                        self.draw_graph()
                    else:
                        self.update_status("不能连接节点到自身")
                        self.selected_node = None
            else:
                self.update_status("请点击节点进行连接")
                self.selected_node = None
                
        elif self.mode == "set_weight":
            # 查找点击的边（通过权重椭圆）
            clicked_edge = self.find_edge_by_weight_box(x, y)
            if clicked_edge:
                # 弹出对话框输入权重
                weight_str = simpledialog.askstring(
                    "设置权重", 
                    f"输入边 {clicked_edge.node1.id} - {clicked_edge.node2.id} 的权重:",
                    initialvalue=str(clicked_edge.weight)
                )
                
                if weight_str:
                    try:
                        weight = float(weight_str)
                        if weight <= 0:
                            messagebox.showerror("错误", "权重必须为正数")
                        else:
                            clicked_edge.weight = weight
                            self.draw_graph()
                            self.update_status(f"边 {clicked_edge.node1.id} - {clicked_edge.node2.id} 权重设置为 {weight}")
                    except ValueError:
                        messagebox.showerror("错误", "请输入有效的数字")
            else:
                # 如果没有点击到权重椭圆，尝试查找点击的边本身
                clicked_edge = self.find_edge_at_point(x, y)
                if clicked_edge:
                    # 弹出对话框输入权重
                    weight_str = simpledialog.askstring(
                        "设置权重", 
                        f"输入边 {clicked_edge.node1.id} - {clicked_edge.node2.id} 的权重:",
                        initialvalue=str(clicked_edge.weight)
                    )
                    
                    if weight_str:
                        try:
                            weight = float(weight_str)
                            if weight <= 0:
                                messagebox.showerror("错误", "权重必须为正数")
                            else:
                                clicked_edge.weight = weight
                                self.draw_graph()
                                self.update_status(f"边 {clicked_edge.node1.id} - {clicked_edge.node2.id} 权重设置为 {weight}")
                        except ValueError:
                            messagebox.showerror("错误", "请输入有效的数字")
                else:
                    self.update_status("请点击边上的权重椭圆来设置权重")
                    
        elif self.mode == "drag_node":
            # 检查是否点击了节点
            for node in self.nodes:
                if node.contains_point(x, y):
                    self.dragged_node = node
                    node.dragging = True
                    self.update_status(f"正在拖动节点 {node.id}")
                    break
                    
    def on_canvas_drag(self, event):
        """处理画布拖动事件"""
        if self.mode == "drag_node" and self.dragged_node:
            # 更新节点位置
            self.dragged_node.x = event.x
            self.dragged_node.y = event.y
            
            # 重新绘制图
            self.draw_graph()
            
    def on_canvas_release(self, event):
        """处理画布释放事件"""
        if self.mode == "drag_node" and self.dragged_node:
            self.dragged_node.dragging = False
            self.dragged_node = None
            self.update_status("节点拖动完成")
            
    def find_edge_at_point(self, x, y, threshold=8):
        """查找点击位置附近的边"""
        for edge in self.edges:
            # 计算点到线段的距离
            if self.point_to_line_distance(x, y, edge.node1.x, edge.node1.y, edge.node2.x, edge.node2.y) < threshold:
                return edge
        return None
        
    def find_edge_by_weight_box(self, x, y):
        """通过权重椭圆查找边"""
        for edge in self.edges:
            if edge.weight_contains_point(x, y):
                return edge
        return None
        
    def point_to_line_distance(self, px, py, x1, y1, x2, y2):
        """计算点到线段的距离"""
        # 线段长度
        line_len = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        
        if line_len == 0:
            # 如果线段退化为点
            return math.sqrt((px - x1)**2 + (py - y1)**2)
            
        # 计算投影比例
        t = ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / (line_len * line_len)
        t = max(0, min(1, t))  # 限制在0到1之间
        
        # 计算投影点
        projection_x = x1 + t * (x2 - x1)
        projection_y = y1 + t * (y2 - y1)
        
        # 计算点到投影点的距离
        return math.sqrt((px - projection_x)**2 + (py - projection_y)**2)
        
    def draw_graph(self):
        """绘制整个图"""
        self.canvas.delete("all")
        
        # 绘制边
        for edge in self.edges:
            highlight = edge in self.mst_edges
            edge.draw(self.canvas, highlight)
            
        # 绘制节点
        for node in self.nodes:
            highlight = False
            # 检查节点是否在MST中
            for edge in self.mst_edges:
                if edge.node1 == node or edge.node2 == node:
                    highlight = True
                    break
            node.draw(self.canvas, highlight)
            
        # 如果有一个节点被选中，高亮显示
        if self.selected_node:
            self.canvas.create_oval(
                self.selected_node.x - self.selected_node.radius - 5,
                self.selected_node.y - self.selected_node.radius - 5,
                self.selected_node.x + self.selected_node.radius + 5,
                self.selected_node.y + self.selected_node.radius + 5,
                outline="red", width=3, dash=(5, 3)
            )
            
        # 显示图的信息
        info_text = f"节点数: {len(self.nodes)} | 边数: {len(self.edges)}"
        if self.mst_edges:
            total_weight = sum(edge.weight for edge in self.mst_edges)
            info_text += f" | MST权重: {total_weight}"
            
        self.canvas.create_text(10, 20, text=info_text, anchor=tk.W, font=("Arial", 10), fill="gray")
    
    def calculate_mst(self):
        """计算最小生成树"""
        if len(self.nodes) == 0:
            messagebox.showwarning("警告", "图中没有节点")
            return
            
        if len(self.nodes) == 1:
            messagebox.showwarning("警告", "图中只有一个节点，无法生成树")
            return
            
        # 检查图是否连通
        if not self.is_graph_connected():
            messagebox.showerror("错误", "图不连通！只有连通图才有生成树。")
            return
            
        # 使用Kruskal算法计算最小生成树
        mst_edges = self.kruskal_mst()
        
        # 保存结果
        self.mst_edges = mst_edges
        
        # 重新绘制图
        self.draw_graph()
        
        # 显示结果
        total_weight = sum(edge.weight for edge in mst_edges)
        self.update_status(f"最小生成树计算完成，总权重: {total_weight}")
        messagebox.showinfo("最小生成树", f"最小生成树计算完成！\n总权重: {total_weight}\n边数: {len(mst_edges)}")
        
    def is_graph_connected(self):
        """检查图是否连通"""
        if not self.nodes:
            return False
            
        # 使用BFS检查连通性
        visited = set()
        stack = [self.nodes[0]]
        
        while stack:
            node = stack.pop()
            if node in visited:
                continue
                
            visited.add(node)
            
            # 查找与当前节点相邻的节点
            for edge in self.edges:
                if edge.node1 == node and edge.node2 not in visited:
                    stack.append(edge.node2)
                elif edge.node2 == node and edge.node1 not in visited:
                    stack.append(edge.node1)
                    
        return len(visited) == len(self.nodes)
        
    def kruskal_mst(self):
        """使用Kruskal算法计算最小生成树"""
        # 初始化并查集
        parent = {}
        rank = {}
        
        def find(node):
            if parent[node] != node:
                parent[node] = find(parent[node])
            return parent[node]
            
        def union(node1, node2):
            root1 = find(node1)
            root2 = find(node2)
            
            if root1 != root2:
                if rank[root1] > rank[root2]:
                    parent[root2] = root1
                elif rank[root1] < rank[root2]:
                    parent[root1] = root2
                else:
                    parent[root2] = root1
                    rank[root1] += 1
                    
        # 初始化并查集
        for node in self.nodes:
            parent[node] = node
            rank[node] = 0
            
        # 按权重排序边
        sorted_edges = sorted(self.edges, key=lambda e: e.weight)
        
        mst_edges = []
        
        # 遍历所有边
        for edge in sorted_edges:
            if find(edge.node1) != find(edge.node2):
                union(edge.node1, edge.node2)
                mst_edges.append(edge)
                
            # 如果已经找到n-1条边，提前结束
            if len(mst_edges) == len(self.nodes) - 1:
                break
                
        return mst_edges
        
    def clear_mst(self):
        """清除最小生成树的高亮显示"""
        self.mst_edges = []
        self.draw_graph()
        self.update_status("已清除最小生成树高亮")
        
    def reset_canvas(self):
        """重置画布"""
        if messagebox.askyesno("确认", "确定要重置画布吗？所有节点和边都将被清除。"):
            self.nodes = []
            self.edges = []
            self.mst_edges = []
            self.next_node_id = 1
            self.selected_node = None
            self.dragged_node = None
            self.draw_graph()
            self.set_add_node_mode()
            self.update_status("画布已重置")
            
    def export_as_image(self):
        """将当前画布导出为图片"""
        if not self.nodes and not self.edges:
            messagebox.showwarning("警告", "没有可导出的图形")
            return
            
        # 询问保存路径
        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[
                ("PNG文件", "*.png"),
                ("JPEG文件", "*.jpg"),
                ("所有文件", "*.*")
            ],
            title="保存图片"
        )
        
        if not file_path:
            return  # 用户取消
            
        try:
            # 获取画布尺寸
            x = self.canvas.winfo_rootx()
            y = self.canvas.winfo_rooty()
            width = self.canvas.winfo_width()
            height = self.canvas.winfo_height()
            
            # 使用PIL创建图片
            from PIL import ImageGrab
            import pyautogui
            
            # 获取画布在屏幕上的位置
            canvas_x = self.canvas.winfo_rootx()
            canvas_y = self.canvas.winfo_rooty()
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            # 截取画布区域
            screenshot = pyautogui.screenshot(region=(canvas_x, canvas_y, canvas_width, canvas_height))
            
            # 保存图片
            screenshot.save(file_path)
            
            messagebox.showinfo("成功", f"图片已保存到:\n{file_path}")
            self.update_status(f"图片已保存: {os.path.basename(file_path)}")
            
        except Exception as e:
            messagebox.showerror("错误", f"保存图片时出错:\n{str(e)}")
            # 如果pyautogui不可用，使用Tkinter内置的PostScript功能
            try:
                self.canvas.postscript(file=file_path + ".eps", colormode="color")
                messagebox.showinfo("成功", f"图片已保存为EPS格式:\n{file_path}.eps\n(某些功能可能无法保存)")
                self.update_status(f"图片已保存为EPS格式")
            except Exception as e2:
                messagebox.showerror("错误", f"两种保存方法都失败了:\n1. {str(e)}\n2. {str(e2)}")

def main():
    root = tk.Tk()
    app = MinimumSpanningTreeApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()