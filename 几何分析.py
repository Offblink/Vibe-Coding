import tkinter as tk
import random
import math
import time
from tkinter import messagebox, ttk

class MonteCarloAreaEstimator:
    def __init__(self, root):
        self.root = root
        self.root.title("几何分析")
        
        # 创建菜单栏
        menubar = tk.Menu(root)
        root.config(menu=menubar)
        
        # 添加帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="关于", command=self.show_about)
        
        # 创建主框架
        main_frame = tk.Frame(root)
        main_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # 左侧画布区域
        left_frame = tk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, padx=(0, 10), fill=tk.BOTH, expand=True)
        
        # 创建画布
        self.canvas = tk.Canvas(left_frame, width=500, height=400, bg="white")
        self.canvas.pack(pady=10, fill=tk.BOTH, expand=True)
        
        # 右侧结果区域
        right_frame = tk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 算法结果标题
        tk.Label(right_frame, text="几何属性分析", font=("Arial", 12, "bold")).pack(pady=(0, 10))
        
        # 扫描线算法结果
        scanline_frame = tk.LabelFrame(right_frame, text="扫描线算法", padx=10, pady=10)
        scanline_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 面积结果
        area_frame = tk.Frame(scanline_frame)
        area_frame.pack(fill=tk.X, pady=(0, 5))
        tk.Label(area_frame, text="面积:", font=("Arial", 10)).pack(side=tk.LEFT)
        self.scanline_area_label = tk.Label(area_frame, text="-", font=("Arial", 10))
        self.scanline_area_label.pack(side=tk.LEFT, padx=(5, 0))
        
        # 周长结果
        perimeter_frame = tk.Frame(scanline_frame)
        perimeter_frame.pack(fill=tk.X, pady=(0, 5))
        tk.Label(perimeter_frame, text="周长:", font=("Arial", 10)).pack(side=tk.LEFT)
        self.scanline_perimeter_label = tk.Label(perimeter_frame, text="-", font=("Arial", 10))
        self.scanline_perimeter_label.pack(side=tk.LEFT, padx=(5, 0))
        
        # 其他信息
        info_frame = tk.Frame(scanline_frame)
        info_frame.pack(fill=tk.X)
        tk.Label(info_frame, text="顶点数:", font=("Arial", 10)).pack(side=tk.LEFT)
        self.scanline_vertices_label = tk.Label(info_frame, text="-", font=("Arial", 10))
        self.scanline_vertices_label.pack(side=tk.LEFT, padx=(5, 0))
        
        tk.Label(info_frame, text="耗时:", font=("Arial", 10)).pack(side=tk.LEFT, padx=(10, 0))
        self.scanline_time_label = tk.Label(info_frame, text="-", font=("Arial", 10))
        self.scanline_time_label.pack(side=tk.LEFT, padx=(5, 0))
        
        # 蒙特卡洛方法结果 - 面积
        montecarlo_frame = tk.LabelFrame(right_frame, text="蒙特卡洛方法 - 面积", padx=10, pady=10)
        montecarlo_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 面积结果
        mc_area_frame = tk.Frame(montecarlo_frame)
        mc_area_frame.pack(fill=tk.X, pady=(0, 5))
        tk.Label(mc_area_frame, text="面积:", font=("Arial", 10)).pack(side=tk.LEFT)
        self.montecarlo_area_label = tk.Label(mc_area_frame, text="-", font=("Arial", 10))
        self.montecarlo_area_label.pack(side=tk.LEFT, padx=(5, 0))
        
        # 误差信息
        mc_error_frame = tk.Frame(montecarlo_frame)
        mc_error_frame.pack(fill=tk.X, pady=(0, 5))
        tk.Label(mc_error_frame, text="相对误差:", font=("Arial", 10)).pack(side=tk.LEFT)
        self.montecarlo_error_label = tk.Label(mc_error_frame, text="-", font=("Arial", 10))
        self.montecarlo_error_label.pack(side=tk.LEFT, padx=(5, 0))
        
        # 采样信息
        mc_info_frame = tk.Frame(montecarlo_frame)
        mc_info_frame.pack(fill=tk.X)
        tk.Label(mc_info_frame, text="采样点数:", font=("Arial", 10)).pack(side=tk.LEFT)
        self.montecarlo_points_label = tk.Label(mc_info_frame, text="-", font=("Arial", 10))
        self.montecarlo_points_label.pack(side=tk.LEFT, padx=(5, 0))
        
        tk.Label(mc_info_frame, text="内部点数:", font=("Arial", 10)).pack(side=tk.LEFT, padx=(10, 0))
        self.montecarlo_inside_label = tk.Label(mc_info_frame, text="-", font=("Arial", 10))
        self.montecarlo_inside_label.pack(side=tk.LEFT, padx=(5, 0))
        
        tk.Label(mc_info_frame, text="耗时:", font=("Arial", 10)).pack(side=tk.LEFT, padx=(10, 0))
        self.montecarlo_time_label = tk.Label(mc_info_frame, text="-", font=("Arial", 10))
        self.montecarlo_time_label.pack(side=tk.LEFT, padx=(5, 0))
        
        # 比较结果
        comparison_frame = tk.LabelFrame(right_frame, text="比较结果", padx=10, pady=10)
        comparison_frame.pack(fill=tk.X)
        
        self.comparison_label = tk.Label(comparison_frame, text="请先创建并计算一个图形", font=("Arial", 10), justify=tk.LEFT)
        self.comparison_label.pack(anchor=tk.W)
        
        # 控制区域
        control_frame = tk.Frame(left_frame)
        control_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 模式选择
        mode_frame = tk.Frame(control_frame)
        mode_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.mode_var = tk.StringVar(value="freehand")
        tk.Label(mode_frame, text="绘制模式:").pack(side=tk.LEFT)
        tk.Radiobutton(mode_frame, text="自由绘制", variable=self.mode_var, value="freehand").pack(side=tk.LEFT)
        tk.Radiobutton(mode_frame, text="选点连接", variable=self.mode_var, value="pointwise").pack(side=tk.LEFT)
        
        # 蒙特卡洛采样点数量滑块
        points_frame = tk.Frame(control_frame)
        points_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(points_frame, text="蒙特卡洛采样点数:").pack(side=tk.LEFT)
        self.points_var = tk.IntVar(value=10000)
        points_slider = ttk.Scale(points_frame, from_=1000, to=50000, orient=tk.HORIZONTAL, 
                                 variable=self.points_var, command=self.update_points_label)
        points_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
        self.points_value_label = tk.Label(points_frame, text="10000")
        self.points_value_label.pack(side=tk.RIGHT)
        
        # 按钮区域
        button_frame = tk.Frame(control_frame)
        button_frame.pack(fill=tk.X)
        
        self.clear_btn = tk.Button(button_frame, text="清除画布", command=self.clear_canvas)
        self.clear_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.complete_btn = tk.Button(button_frame, text="完成图形", command=self.complete_shape)
        self.complete_btn.pack(side=tk.LEFT, padx=5)
        
        self.estimate_btn = tk.Button(button_frame, text="计算几何属性", command=self.estimate_properties)
        self.estimate_btn.pack(side=tk.LEFT, padx=5)
        
        # 绑定鼠标事件
        self.canvas.bind("<ButtonPress-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.draw)
        self.canvas.bind("<ButtonRelease-1>", self.end_draw)
        
        # 初始化变量
        self.points = []
        self.drawing = False
        self.closed_shape = False
        self.shape_id = None
        self.point_handles = []  # 存储点的可视化句柄
        self.lines = []  # 存储线段的句柄
        self.dragging_point = None  # 当前拖动的点索引
        self.drag_start_pos = None  # 拖动开始的位置
        
    def update_points_label(self, value):
        """更新采样点数标签"""
        self.points_value_label.config(text=str(int(float(value))))
        
    def show_about(self):
        """显示关于窗口"""
        about_text = """
几何属性分析工具

扫描线算法（鞋带公式）：
- 面积精确性：100% 精确（数学上完美）
- 周长精确性：100% 精确（基于顶点距离计算）
- 原理：基于多边形的顶点坐标，使用确定的数学公式计算
- 复杂度：O(n)，其中n是多边形顶点数
- 适用性：仅限于可以用多边形表示的形状
- 优势：绝对精确，计算速度快

蒙特卡洛方法：
- 面积精确性：统计估计，存在误差
- 原理：通过随机采样来估计面积
- 方法：在边界框内生成随机点，统计落在图形内的比例
- 复杂度：O(m)，其中m是采样点数量
- 适用性：任何形状，甚至是无法用数学公式描述的复杂形状
- 误差特性：误差与采样点数量的平方根成反比（误差 ∝ 1/√N）
- 优势：适用于复杂形状，易于并行化

选择建议：
- 需要绝对精确值且形状可用多边形表示：使用扫描线算法
- 形状复杂或只能通过采样获得：使用蒙特卡洛方法
- 教育目的：比较两种方法以理解统计学原理
        """
        messagebox.showinfo("关于", about_text)
        
    def on_canvas_click(self, event):
        mode = self.mode_var.get()
        
        if mode == "freehand":
            self.start_draw(event)
        elif mode == "pointwise" and not self.closed_shape:
            # 检查是否点击了现有的点
            clicked_point = self.find_point_at(event.x, event.y)
            if clicked_point is not None:
                # 开始拖动点
                self.dragging_point = clicked_point
                self.drag_start_pos = (event.x, event.y)
            else:
                # 添加新点
                self.add_point(event.x, event.y)
            
    def find_point_at(self, x, y):
        """查找给定位置的点索引"""
        tolerance = 5  # 点击容差范围
        for i, point in enumerate(self.points):
            px, py = point
            if abs(px - x) <= tolerance and abs(py - y) <= tolerance:
                return i
        return None
            
    def start_draw(self, event):
        if not self.closed_shape:
            self.drawing = True
            self.points = [(event.x, event.y)]
            # 清除之前的填充
            if self.shape_id:
                self.canvas.delete(self.shape_id)
                self.shape_id = None
            
    def add_point(self, x, y):
        """在选点模式下添加一个点"""
        self.points.append((x, y))
        
        # 绘制点
        point_handle = self.canvas.create_oval(x-3, y-3, x+3, y+3, fill="red", outline="")
        self.point_handles.append(point_handle)
        
        # 如果至少有两个点，绘制线段
        if len(self.points) > 1:
            prev_x, prev_y = self.points[-2]
            line_handle = self.canvas.create_line(prev_x, prev_y, x, y, fill="blue", width=2)
            self.lines.append(line_handle)
        
        # 如果图形已经封闭，重新计算几何属性
        if self.closed_shape:
            self.update_properties()
    
    def draw(self, event):
        if self.dragging_point is not None:
            # 拖动点
            self.drag_point(event.x, event.y)
        elif self.mode_var.get() == "freehand" and self.drawing and not self.closed_shape:
            x, y = event.x, event.y
            self.points.append((x, y))
            
            # 绘制线段
            if len(self.points) > 1:
                prev_x, prev_y = self.points[-2]
                self.canvas.create_line(prev_x, prev_y, x, y, fill="blue", width=2)
    
    def drag_point(self, x, y):
        """拖动点到新位置"""
        if self.dragging_point is None:
            return
            
        # 更新点位置
        self.points[self.dragging_point] = (x, y)
        
        # 更新点可视化
        self.canvas.coords(self.point_handles[self.dragging_point], 
                          x-3, y-3, x+3, y+3)
        
        # 更新连接线
        n = len(self.points)
        if n > 1:
            # 更新前一条线
            if self.dragging_point > 0:
                prev_idx = self.dragging_point - 1
                prev_x, prev_y = self.points[prev_idx]
                self.canvas.coords(self.lines[prev_idx], prev_x, prev_y, x, y)
            
            # 更新后一条线
            if self.dragging_point < n - 1:
                next_idx = self.dragging_point
                next_x, next_y = self.points[self.dragging_point + 1]
                self.canvas.coords(self.lines[next_idx], x, y, next_x, next_y)
            elif self.closed_shape:
                # 更新最后一条线（连接首尾）
                first_x, first_y = self.points[0]
                self.canvas.coords(self.lines[-1], x, y, first_x, first_y)
        
        # 更新填充
        if self.closed_shape and self.shape_id:
            self.canvas.coords(self.shape_id, 
                              [coord for point in self.points for coord in point])
        
        # 实时更新几何属性
        if self.closed_shape:
            self.update_properties()
    
    def end_draw(self, event):
        if self.dragging_point is not None:
            # 结束拖动点
            self.dragging_point = None
            self.drag_start_pos = None
        elif self.mode_var.get() == "freehand" and self.drawing and not self.closed_shape and len(self.points) > 2:
            # 连接起点和终点形成封闭图形
            start_x, start_y = self.points[0]
            end_x, end_y = self.points[-1]
            self.canvas.create_line(end_x, end_y, start_x, start_y, fill="blue", width=2)
            self.drawing = False
            self.closed_shape = True
            
            # 添加半透明填充（阴影效果）
            self.add_shading()
            
            # 计算几何属性
            self.estimate_properties()
            
    def complete_shape(self):
        """完成图形（适用于选点模式）"""
        if self.mode_var.get() == "pointwise" and len(self.points) >= 3 and not self.closed_shape:
            # 连接起点和终点形成封闭图形
            start_x, start_y = self.points[0]
            end_x, end_y = self.points[-1]
            line_handle = self.canvas.create_line(end_x, end_y, start_x, start_y, fill="blue", width=2)
            self.lines.append(line_handle)
            self.closed_shape = True
            
            # 添加半透明填充（阴影效果）
            self.add_shading()
            
            # 计算几何属性
            self.estimate_properties()
            
    def add_shading(self):
        """为封闭图形添加半透明填充"""
        if len(self.points) > 2:
            # 创建半透明颜色（浅蓝色，半透明）
            self.shape_id = self.canvas.create_polygon(
                [coord for point in self.points for coord in point], 
                fill="#ADD8E6",  # 浅蓝色
                stipple="gray50",  # 使用点状图案创建半透明效果
                outline="blue",
                width=2
            )
            # 将填充置于底层，以便看到边界线
            self.canvas.lower(self.shape_id)
            
    def clear_canvas(self):
        self.canvas.delete("all")
        self.points = []
        self.drawing = False
        self.closed_shape = False
        self.shape_id = None
        self.point_handles = []
        self.lines = []
        self.dragging_point = None
        self.drag_start_pos = None
        
        # 重置结果显示
        self.scanline_area_label.config(text="-")
        self.scanline_perimeter_label.config(text="-")
        self.scanline_vertices_label.config(text="-")
        self.scanline_time_label.config(text="-")
        
        self.montecarlo_area_label.config(text="-")
        self.montecarlo_error_label.config(text="-")
        self.montecarlo_points_label.config(text="-")
        self.montecarlo_inside_label.config(text="-")
        self.montecarlo_time_label.config(text="-")
        
        self.comparison_label.config(text="请先创建并计算一个图形")
        
    def is_point_in_polygon(self, x, y, polygon):
        # 使用射线法判断点是否在多边形内部
        n = len(polygon)
        inside = False
        p1x, p1y = polygon[0]
        for i in range(n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        return inside
    
    def scanline_area(self, polygon):
        """使用扫描线算法计算多边形面积"""
        n = len(polygon)
        if n < 3:
            return 0.0
            
        # 使用鞋带公式（Shoelace formula）计算多边形面积
        area = 0.0
        for i in range(n):
            j = (i + 1) % n
            area += polygon[i][0] * polygon[j][1]
            area -= polygon[j][0] * polygon[i][1]
            
        return abs(area) / 2.0
    
    def scanline_perimeter(self, polygon):
        """使用扫描线算法计算多边形周长"""
        n = len(polygon)
        if n < 2:
            return 0.0
            
        perimeter = 0.0
        for i in range(n):
            j = (i + 1) % n
            dx = polygon[j][0] - polygon[i][0]
            dy = polygon[j][1] - polygon[i][1]
            perimeter += math.sqrt(dx*dx + dy*dy)
            
        return perimeter
    
    def update_properties(self):
        """更新几何属性显示（实时计算）"""
        if not self.closed_shape or len(self.points) < 3:
            return
            
        # 获取蒙特卡洛采样点数量
        num_points = self.points_var.get()
        
        # 使用扫描线算法计算精确面积和周长
        scanline_start = time.time()
        exact_area = self.scanline_area(self.points)
        exact_perimeter = self.scanline_perimeter(self.points)
        scanline_time = time.time() - scanline_start
        
        # 更新扫描线算法结果显示
        self.scanline_area_label.config(text=f"{exact_area:.2f} 像素²")
        self.scanline_perimeter_label.config(text=f"{exact_perimeter:.2f} 像素")
        self.scanline_vertices_label.config(text=str(len(self.points)))
        self.scanline_time_label.config(text=f"{scanline_time*1000:.2f} 毫秒")
        
        # 获取边界框
        x_coords = [p[0] for p in self.points]
        y_coords = [p[1] for p in self.points]
        min_x, max_x = min(x_coords), max(x_coords)
        min_y, max_y = min(y_coords), max(y_coords)
        bounding_area = (max_x - min_x) * (max_y - min_y)
        
        # 蒙特卡洛方法计算面积
        mc_start = time.time()
        points_inside = 0
        for i in range(num_points):
            x = random.uniform(min_x, max_x)
            y = random.uniform(min_y, max_y)
            
            if self.is_point_in_polygon(x, y, self.points):
                points_inside += 1
        
        # 计算估计面积
        estimated_area = (points_inside / num_points) * bounding_area
        mc_time = time.time() - mc_start
        
        # 计算面积相对误差
        area_error_percent = abs(estimated_area - exact_area) / exact_area * 100 if exact_area > 0 else 0
        
        # 更新蒙特卡洛方法结果显示
        self.montecarlo_area_label.config(text=f"{estimated_area:.2f} 像素²")
        self.montecarlo_error_label.config(text=f"{area_error_percent:.2f}%")
        self.montecarlo_points_label.config(text=str(num_points))
        self.montecarlo_inside_label.config(text=str(points_inside))
        self.montecarlo_time_label.config(text=f"{mc_time*1000:.2f} 毫秒")
        
        # 更新比较结果
        comparison_text = (
            f"面积比较:\n"
            f"  扫描线算法: {exact_area:.2f} 像素²\n"
            f"  蒙特卡洛方法: {estimated_area:.2f} 像素²\n"
            f"  差异: {abs(estimated_area - exact_area):.2f} 像素²\n"
            f"  相对误差: {area_error_percent:.2f}%\n\n"
            f"时间比较:\n"
            f"  扫描线算法耗时: {scanline_time*1000:.2f} 毫秒\n"
            f"  蒙特卡洛方法耗时: {mc_time*1000:.2f} 毫秒"
        )
        self.comparison_label.config(text=comparison_text)
    
    def estimate_properties(self):
        """计算几何属性（完整计算）"""
        if not self.closed_shape or len(self.points) < 3:
            messagebox.showwarning("警告", "请先创建并完成一个封闭图形!")
            return
            
        self.update_properties()

if __name__ == "__main__":
    root = tk.Tk()
    app = MonteCarloAreaEstimator(root)
    root.mainloop()