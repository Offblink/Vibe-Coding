import tkinter as tk
import math
import random
import time

class Boid:
    def __init__(self, canvas, width, height):
        self.canvas = canvas
        self.width = width
        self.height = height
        
        # 随机位置和速度
        self.x = random.randint(0, width)
        self.y = random.randint(0, height)
        angle = random.uniform(0, 2 * math.pi)
        self.vx = math.cos(angle) * 2
        self.vy = math.sin(angle) * 2
        
        # 绘制鸟
        size = 8
        self.triangle = self.canvas.create_polygon(
            self.x, self.y,
            self.x - size, self.y + size,
            self.x - size, self.y - size,
            fill=self.get_random_color()
        )
    
    def get_random_color(self):
        colors = ["#47B3FF", "#32CD9A", "#FF66CC", "#FFCC33"]
        return random.choice(colors)
    
    def update(self, boids):
        # 添加简单规则
        separation = self.apply_separation(boids)
        alignment = self.apply_alignment(boids)
        cohesion = self.apply_cohesion(boids)
        boundary = self.apply_boundary()  # 新增边界转向
        
        # 更新速度（包含边界转向）
        self.vx += (separation[0] + alignment[0] + cohesion[0] + boundary[0])
        self.vy += (separation[1] + alignment[1] + cohesion[1] + boundary[1])
        
        # 限制最大速度
        speed = math.sqrt(self.vx**2 + self.vy**2)
        if speed > 5:
            self.vx = (self.vx / speed) * 5
            self.vy = (self.vy / speed) * 5
        
        # 更新位置
        self.x += self.vx
        self.y += self.vy
        
        # 边界处理：转向而不是环形边界
        self.check_boundaries()
        
        # 更新画布上的形状
        points = self.calculate_triangle_points()
        self.canvas.coords(self.triangle, points)
    
    def apply_boundary(self):
        """新增：在边界附近施加转向力"""
        margin = 50  # 距离边界多远开始转向
        turn_factor = 0.2  # 转向力度
        
        boundary_x, boundary_y = 0, 0
        
        # 左边界
        if self.x < margin:
            boundary_x += turn_factor
        # 右边界
        if self.x > self.width - margin:
            boundary_x -= turn_factor
        # 上边界
        if self.y < margin:
            boundary_y += turn_factor
        # 下边界
        if self.y > self.height - margin:
            boundary_y -= turn_factor
        
        return boundary_x, boundary_y
    
    def check_boundaries(self):
        """确保鸟不会飞出边界（转向边界）"""
        # 如果飞出边界，将其推回并反转速度方向
        if self.x < 0:
            self.x = 0
            self.vx = abs(self.vx) * 0.5  # 反弹并减速
        elif self.x > self.width:
            self.x = self.width
            self.vx = -abs(self.vx) * 0.5  # 反弹并减速
            
        if self.y < 0:
            self.y = 0
            self.vy = abs(self.vy) * 0.5  # 反弹并减速
        elif self.y > self.height:
            self.y = self.height
            self.vy = -abs(self.vy) * 0.5  # 反弹并减速
    
    def apply_separation(self, boids):
        # 避免与附近的鸟太近
        steer_x, steer_y = 0, 0
        for other in boids:
            if other != self:
                dx = self.x - other.x
                dy = self.y - other.y
                distance = math.sqrt(dx**2 + dy**2)
                
                if 0 < distance < 50:  # 分离半径
                    steer_x += dx / distance
                    steer_y += dy / distance
        return steer_x * 0.1, steer_y * 0.1
    
    def apply_alignment(self, boids):
        # 与附近鸟的速度匹配
        avg_vx, avg_vy = 0, 0
        count = 0
        
        for other in boids:
            if other != self:
                dx = self.x - other.x
                dy = self.y - other.y
                distance = math.sqrt(dx**2 + dy**2)
                
                if 0 < distance < 100:  # 对齐半径
                    avg_vx += other.vx
                    avg_vy += other.vy
                    count += 1
        
        if count > 0:
            avg_vx /= count
            avg_vy /= count
            return (avg_vx - self.vx) * 0.1, (avg_vy - self.vy) * 0.1
        return 0, 0
    
    def apply_cohesion(self, boids):
        # 向附近鸟的中心移动
        center_x, center_y = 0, 0
        count = 0
        
        for other in boids:
            if other != self:
                dx = self.x - other.x
                dy = self.y - other.y
                distance = math.sqrt(dx**2 + dy**2)
                
                if 0 < distance < 80:  # 聚集半径
                    center_x += other.x
                    center_y += other.y
                    count += 1
        
        if count > 0:
            center_x /= count
            center_y /= count
            dx = center_x - self.x
            dy = center_y - self.y
            dist = math.sqrt(dx**2 + dy**2)
            if dist > 0:
                return (dx / dist) * 0.1, (dy / dist) * 0.1
        return 0, 0
    
    def calculate_triangle_points(self):
        # 计算三角形顶点
        angle = math.atan2(self.vy, self.vx)
        size = 8
        
        tip_x = self.x + size * math.cos(angle)
        tip_y = self.y + size * math.sin(angle)
        
        left_x = self.x - size/3 * math.cos(angle + 2.5)
        left_y = self.y - size/3 * math.sin(angle + 2.5)
        
        right_x = self.x - size/3 * math.cos(angle - 2.5)
        right_y = self.y - size/3 * math.sin(angle - 2.5)
        
        return tip_x, tip_y, left_x, left_y, right_x, right_y

class BoidSimulation:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Boids 鸟群模拟 - 使用Tkinter")
        
        # 获取屏幕尺寸并设置为全屏
        self.root.attributes('-fullscreen', True)  # 设置为全屏模式
        self.width = self.root.winfo_screenwidth()
        self.height = self.root.winfo_screenheight()
        
        # 创建画布（覆盖全屏）
        self.canvas = tk.Canvas(self.root, width=self.width, height=self.height, bg="#000A1E")
        self.canvas.pack()
        
        # 添加控制按钮（放置在底部中间）
        self.controls_frame = tk.Frame(self.root)
        self.controls_frame.place(relx=0.5, rely=0.95, anchor='center')
        
        # 创建按钮
        tk.Button(
            self.controls_frame, 
            text="添加鸟 (5只)", 
            command=self.add_boids,
            padx=10, pady=5,
            bg="#333333", fg="white"
        ).pack(side="left", padx=10)
        
        tk.Button(
            self.controls_frame, 
            text="移除鸟 (5只)", 
            command=self.remove_boids,
            padx=10, pady=5,
            bg="#333333", fg="white"
        ).pack(side="left", padx=10)
        
        tk.Button(
            self.controls_frame, 
            text="暂停", 
            command=self.toggle_pause,
            padx=10, pady=5,
            bg="#333333", fg="white"
        ).pack(side="left", padx=10)
        
        tk.Button(
            self.controls_frame, 
            text="退出", 
            command=self.on_close,
            padx=10, pady=5,
            bg="#ff5555", fg="white"
        ).pack(side="left", padx=10)
        
        # 添加鸟群数量显示
        self.boid_count = tk.Label(
            self.root, 
            text=f"鸟群数量: {0}", 
            fg="white", bg="#000A1E",
            font=("Arial", 14)
        )
        self.boid_count.place(relx=0.5, rely=0.05, anchor='center')
        
        # 添加标题
        self.title_label = tk.Label(
            self.root, 
            text="鸟群行为模拟 - Boids 模型", 
            fg="#47B3FF", bg="#000A1E",
            font=("Arial", 16, "bold")
        )
        self.title_label.place(relx=0.5, rely=0.01, anchor='center')
        
        # 初始化鸟群
        self.boids = []
        for _ in range(30):
            self.boids.append(Boid(self.canvas, self.width, self.height))
        
        # 状态
        self.paused = False
        self.running = True
        
        # 开始模拟
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.update()
        self.root.mainloop()
    
    def add_boids(self):
        for _ in range(5):
            self.boids.append(Boid(self.canvas, self.width, self.height))
        self.update_boid_count()
    
    def remove_boids(self):
        for _ in range(5):
            if self.boids:
                boid = self.boids.pop()
                self.canvas.delete(boid.triangle)
        self.update_boid_count()
    
    def toggle_pause(self):
        self.paused = not self.paused
        self.title_label.config(text="鸟群行为模拟 - 已暂停" if self.paused else "鸟群行为模拟 - Boids 模型")
    
    def update_boid_count(self):
        """更新鸟群数量显示"""
        self.boid_count.config(text=f"鸟群数量: {len(self.boids)}")
    
    def update(self):
        if not self.paused and self.running:
            for boid in self.boids:
                boid.update(self.boids)
        
        self.root.after(20, self.update)  # 每20ms更新一次
    
    def on_close(self):
        self.running = False
        self.root.destroy()

# 启动模拟
if __name__ == "__main__":
    simulation = BoidSimulation()