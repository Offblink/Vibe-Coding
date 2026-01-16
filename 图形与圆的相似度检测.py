import tkinter as tk
from tkinter import ttk, messagebox
import math
import numpy as np

class ShapeAnalyzer:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("图形与圆的相似度检测")
        self.root.geometry("900x700")
        self.root.configure(bg="#f0f0f0")
        
        # 设置主题样式
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # 配置按钮样式
        self.style.configure('TButton', 
                            font=('Arial', 10),
                            padding=6,
                            background='#4CAF50',
                            foreground='white')
        self.style.map('TButton', 
                      background=[('active', '#45a049')])
        
        # 配置标签样式
        self.style.configure('Title.TLabel', 
                            font=('Arial', 16, 'bold'),
                            background='#f0f0f0',
                            foreground='#333333')
        self.style.configure('Result.TLabel', 
                            font=('Arial', 11),
                            background='#f9f9f9',
                            foreground='#333333',
                            padding=10)
        
        # 创建标题
        title_label = ttk.Label(self.root, text="图形与圆的相似度检测", style='Title.TLabel')
        title_label.pack(pady=15)
        
        # 创建说明标签
        instruction_label = ttk.Label(self.root, 
                                     text="直接在画布上绘制封闭图形，程序会自动平滑闭合图形并计算与圆的相似度",
                                     font=('Arial', 10),
                                     background='#f0f0f0',
                                     foreground='#666666')
        instruction_label.pack(pady=5)
        
        # 创建主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # 创建画布框架
        canvas_frame = ttk.LabelFrame(main_frame, text="绘图区域", padding=10)
        canvas_frame.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        # 创建画布
        self.canvas = tk.Canvas(canvas_frame, width=500, height=400, bg="white", 
                               highlightbackground="#cccccc", highlightthickness=2)
        self.canvas.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 创建右侧信息框架
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=tk.BOTH, expand=True, side=tk.RIGHT, padx=(20, 0))
        
        # 创建结果框架
        result_frame = ttk.LabelFrame(info_frame, text="计算结果", padding=10)
        result_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 创建结果显示标签
        self.result_label = ttk.Label(result_frame, 
                                     text="请直接在画布上绘制封闭图形",
                                     style='Result.TLabel',
                                     relief=tk.SUNKEN,
                                     anchor=tk.CENTER,
                                     justify=tk.CENTER)
        self.result_label.pack(fill=tk.BOTH, expand=True)
        
        # 创建按钮框架
        button_frame = ttk.Frame(info_frame)
        button_frame.pack(fill=tk.X)
        
        # 创建清除按钮
        self.clear_btn = ttk.Button(button_frame, text="清除画布", command=self.clear_canvas)
        self.clear_btn.pack(fill=tk.X, pady=5)
        
        # 创建平滑度调整滑块
        smooth_frame = ttk.Frame(button_frame)
        smooth_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(smooth_frame, text="平滑度:").pack(side=tk.LEFT)
        self.smooth_var = tk.IntVar(value=5)
        smooth_scale = ttk.Scale(smooth_frame, from_=1, to=10, variable=self.smooth_var, 
                                orient=tk.HORIZONTAL)
        smooth_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(smooth_frame, textvariable=self.smooth_var).pack(side=tk.RIGHT)
        
        # 创建信息面板
        info_panel = ttk.LabelFrame(info_frame, text="数学原理", padding=10)
        info_panel.pack(fill=tk.BOTH, expand=True)
        
        info_text = """
对于圆形，周长平方与面积之比等于4π：
  P²/A = 4π  ⇒  P²/(4A) = π

对于其他形状，这个比值会大于π（根据等周不等式）。

因此，我们可以通过计算这个比值与π的接近程度来衡量图形与圆的相似度。

相似度 = (1 - |比值 - π|/π) × 100%
        """
        info_label = ttk.Label(info_panel, text=info_text, justify=tk.LEFT, background='#f9f9f9')
        info_label.pack(fill=tk.BOTH, expand=True)
        
        # 初始化变量
        self.drawing = False
        self.points = []
        self.line_id = None
        self.closing_line_id = None  # 自动闭合线的ID
        self.auto_calculate = True
        
        # 绑定鼠标事件
        self.canvas.bind("<ButtonPress-1>", self.start_drawing)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.finish_drawing)
        
        # 添加状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.root.mainloop()
    
    def start_drawing(self, event):
        self.drawing = True
        self.points = [(event.x, event.y)]
        self.result_label.config(text="正在绘制...")
        self.status_var.set("正在绘制图形...")
    
    def on_drag(self, event):
        if self.drawing:
            self.points.append((event.x, event.y))
            self.draw_shape()
            
            # 绘制平滑闭合线（从当前点到起点）
            if len(self.points) > 2:  # 至少需要3个点才能形成闭合
                if self.closing_line_id:
                    self.canvas.delete(self.closing_line_id)
                
                # 使用贝塞尔曲线创建平滑闭合线
                smooth_points = self.create_smooth_closure(self.points[-1], self.points[0])
                self.closing_line_id = self.canvas.create_line(
                    smooth_points, fill="#FF9800", width=2, dash=(5, 2), smooth=True
                )
    
    def finish_drawing(self, event):
        if self.drawing:
            self.drawing = False
            
            # 删除自动闭合线
            if self.closing_line_id:
                self.canvas.delete(self.closing_line_id)
                self.closing_line_id = None
            
            # 确保图形平滑闭合
            if len(self.points) > 2 and self.points[0] != self.points[-1]:
                # 添加平滑闭合段
                closure_points = self.create_smooth_closure(self.points[-1], self.points[0])
                # 只取中间的点，避免重复
                self.points.extend(closure_points[1:-1])
                self.points.append(self.points[0])  # 确保闭合
                self.draw_shape()
            
            # 自动计算相似度
            if self.auto_calculate and len(self.points) > 2:
                self.status_var.set("正在计算相似度...")
                self.calculate_similarity()
    
    def create_smooth_closure(self, start_point, end_point):
        """创建平滑闭合曲线"""
        x1, y1 = start_point
        x2, y2 = end_point
        
        # 计算中点
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        
        # 计算控制点 - 使用垂直于连接线的方向
        dx, dy = x2 - x1, y2 - y1
        length = math.sqrt(dx*dx + dy*dy)
        
        if length < 1:  # 避免除以零
            return [start_point, end_point]
        
        # 归一化方向向量
        dx, dy = dx/length, dy/length
        
        # 计算垂直方向
        perp_dx, perp_dy = -dy, dx
        
        # 根据平滑度调整控制点的距离
        smooth_factor = self.smooth_var.get() / 5.0
        control_distance = length * 0.3 * smooth_factor
        
        # 计算控制点
        control1_x = x1 + perp_dx * control_distance
        control1_y = y1 + perp_dy * control_distance
        control2_x = x2 + perp_dx * control_distance
        control2_y = y2 + perp_dy * control_distance
        
        # 生成贝塞尔曲线上的点
        bezier_points = []
        for t in np.linspace(0, 1, 10):  # 生成10个点
            # 三次贝塞尔曲线公式
            x = (1-t)**3 * x1 + 3*(1-t)**2*t * control1_x + 3*(1-t)*t**2 * control2_x + t**3 * x2
            y = (1-t)**3 * y1 + 3*(1-t)**2*t * control1_y + 3*(1-t)*t**2 * control2_y + t**3 * y2
            bezier_points.append((x, y))
        
        return bezier_points
    
    def draw_shape(self):
        if len(self.points) < 2:
            return
            
        if self.line_id:
            self.canvas.delete(self.line_id)
        
        # 绘制图形
        self.line_id = self.canvas.create_line(self.points, fill="#2196F3", width=3, smooth=True)
    
    def clear_canvas(self):
        self.canvas.delete("all")
        self.drawing = False
        self.points = []
        self.line_id = None
        self.closing_line_id = None
        self.result_label.config(text="请直接在画布上绘制封闭图形")
        self.status_var.set("已清除画布")
    
    def calculate_similarity(self):
        if len(self.points) < 3:
            messagebox.showerror("错误", "请绘制至少3个点的封闭图形")
            self.status_var.set("错误: 点数不足")
            return
        
        # 计算周长
        perimeter = self.calculate_perimeter()
        
        # 计算面积
        area = self.calculate_area()
        
        if area <= 0:
            messagebox.showerror("错误", "无法计算面积，请绘制有效的封闭图形")
            self.status_var.set("错误: 无效的封闭图形")
            return
        
        # 计算周长平方与面积比值的四分之一
        ratio = (perimeter ** 2) / (4 * area)
        
        # 计算与π的误差
        error = abs(ratio - math.pi)
        similarity = (1 - error / math.pi) * 100  # 相似度百分比
        
        # 根据相似度设置颜色
        color = "#F44336"  # 红色 - 低相似度
        if similarity > 80:
            color = "#4CAF50"  # 绿色 - 高相似度
        elif similarity > 60:
            color = "#FF9800"  # 橙色 - 中等相似度
        
        # 显示结果
        result_text = f"周长: {perimeter:.2f} px\n面积: {area:.2f} px²\n\n"
        result_text += f"周长²/(4×面积) = {ratio:.4f}\nπ = {math.pi:.4f}\n\n"
        result_text += f"误差: {error:.4f}\n"
        result_text += f"与圆的相似度: {similarity:.2f}%"
        
        self.result_label.config(text=result_text, foreground=color)
        self.status_var.set(f"计算完成: 相似度 {similarity:.2f}%")
    
    def calculate_perimeter(self):
        perimeter = 0
        for i in range(len(self.points) - 1):
            x1, y1 = self.points[i]
            x2, y2 = self.points[i + 1]
            perimeter += math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
        return perimeter
    
    def calculate_area(self):
        # 使用鞋带公式计算多边形面积
        area = 0
        n = len(self.points)
        for i in range(n - 1):
            x1, y1 = self.points[i]
            x2, y2 = self.points[i + 1]
            area += (x1 * y2) - (x2 * y1)
        return abs(area) / 2

if __name__ == "__main__":
    app = ShapeAnalyzer()