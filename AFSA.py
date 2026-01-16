import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.collections import PathCollection
import matplotlib.patches as patches
import random

class Fish:
    def __init__(self, fish_id, x, y, max_speed=2.0, visual_range=25.0, crowd_factor=0.9, step_size=0.5):
        self.id = fish_id
        self.x = x
        self.y = y
        # 随机初始速度（方向）
        angle = random.uniform(0, 2 * np.pi)
        self.vx = np.cos(angle) * max_speed
        self.vy = np.sin(angle) * max_speed
        self.max_speed = max_speed
        self.visual_range = visual_range
        self.crowd_factor = crowd_factor
        self.step_size = step_size
        self.state = "exploring"  # 初始状态：探索
        self.hunger = random.random()  # 初始饥饿度
        self.target_food = None  # 追踪的目标食物

    def move(self, fishes, foods, width, height):
        # 降低饥饿度
        self.hunger = min(1.0, self.hunger + 0.001)
        
        # 食物处理逻辑
        if self.target_food is not None and self.target_food not in foods:
            self.target_food = None
        
        # 优先寻找食物
        self.find_food(fishes, foods)
        
        # 根据状态选择行为
        if self.state == "following":
            self.follow(fishes)
        elif self.state == "crowding":
            self.crowd(fishes)
        elif self.state == "exploring":
            self.explore()
        
        # 确保速度不超过最大值
        speed = np.sqrt(self.vx**2 + self.vy**2)
        if speed > self.max_speed:
            self.vx = self.vx * self.max_speed / speed
            self.vy = self.vy * self.max_speed / speed
        
        # 移动并处理边界
        self.x += self.vx
        self.y += self.vy
        
        # 边界处理
        if self.x < 0: 
            self.x = width
        elif self.x > width: 
            self.x = 0
        if self.y < 0: 
            self.y = height
        elif self.y > height: 
            self.y = 0
    
    def find_food(self, fishes, foods):
        if not foods:
            return
            
        min_dist = float('inf')
        closest_food = None
        
        # 找到最近的食物
        for food in foods:
            dx = food.x - self.x
            dy = food.y - self.y
            dist = np.sqrt(dx**2 + dy**2)
            
            if dist < min_dist:
                min_dist = dist
                closest_food = food
        
        # 如果饥饿或食物很近
        if self.hunger < 0.3 or min_dist < self.visual_range * 0.6:
            self.target_food = closest_food
            self.state = "following"
            
            # 移向食物
            dx = closest_food.x - self.x
            dy = closest_food.y - self.y
            dist = np.sqrt(dx**2 + dy**2)
            
            if dist > 0:
                self.vx += (dx / dist) * self.step_size * 1.5
                self.vy += (dy / dist) * self.step_size * 1.5
                
                # 吃到食物
                if dist < 2:
                    if closest_food in foods:
                        foods.remove(closest_food)
                        self.target_food = None
                        self.hunger = min(1.0, self.hunger + 0.3)
                        self.state = "crowding"
    
    def follow(self, fishes):
        # 在视野范围内寻找其他鱼
        nearby_fishes = []
        for other in fishes:
            if other.id != self.id:
                dx = other.x - self.x
                dy = other.y - self.y
                dist = np.sqrt(dx**2 + dy**2)
                
                if dist < self.visual_range:
                    nearby_fishes.append((other, dist))
        
        if not nearby_fishes:
            self.state = "exploring"
            return
        
        # 找到最近的前方鱼
        leader = None
        min_dist = float('inf')
        for fish, dist in nearby_fishes:
            # 计算鱼的方向和视线方向的角度
            dx = fish.x - self.x
            dy = fish.y - self.y
            direction = np.array([dx, dy])
            fish_dir = np.array([fish.vx, fish.vy])
            fish_dir = fish_dir / np.linalg.norm(fish_dir)
            
            # 如果鱼在视野前部区域(角度小于45度)
            if np.dot(direction, fish_dir) > 0.5:
                if dist < min_dist:
                    min_dist = dist
                    leader = fish
        
        # 如果找到了引导鱼
        if leader:
            # 朝引导鱼方向移动
            dx = leader.x - self.x
            dy = leader.y - self.y
            dist = np.sqrt(dx**2 + dy**2)
            
            if dist > 0:
                self.vx += (dx / dist) * self.step_size
                self.vy += (dy / dist) * self.step_size
        else:
            self.state = "crowding"
    
    def crowd(self, fishes):
        # 计算群体中心
        center_x, center_y = 0.0, 0.0
        count = 0
        
        # 计算视野内鱼的中心
        for other in fishes:
            if other.id != self.id:
                dx = other.x - self.x
                dy = other.y - self.y
                dist = np.sqrt(dx**2 + dy**2)
                
                if dist < self.visual_range:
                    center_x += other.x
                    center_y += other.y
                    count += 1
        
        if count > 0:
            center_x /= count
            center_y /= count
            
            # 朝中心移动
            dx = center_x - self.x
            dy = center_y - self.y
            dist = np.sqrt(dx**2 + dy**2)
            
            if dist > 0:
                # 避免过度拥挤
                desired_distance = self.crowd_factor * self.visual_range
                if dist < desired_distance:
                    # 离开群体中心
                    self.vx -= (dx / dist) * self.step_size * 0.5
                    self.vy -= (dy / dist) * self.step_size * 0.5
                else:
                    # 靠近群体中心
                    self.vx += (dx / dist) * self.step_size
                    self.vy += (dy / dist) * self.step_size
                    
                    # 有50%的几率切换到跟随状态
                    if random.random() < 0.5:
                        self.state = "following"
        else:
            self.state = "exploring"
    
    def explore(self):
        # 随机探索
        self.vx += random.uniform(-0.5, 0.5) * self.step_size
        self.vy += random.uniform(-0.5, 0.5) * self.step_size
        
        # 有20%的几率开始聚集
        if random.random() < 0.2:
            self.state = "crowding"

class Food:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class Aquarium:
    def __init__(self, width=600, height=400, num_fish=30, num_food=5):
        self.width = width
        self.height = height
        self.fishes = [Fish(i, 
                           random.uniform(50, width-50), 
                           random.uniform(50, height-50),
                           max_speed=random.uniform(1.5, 2.5),
                           visual_range=random.uniform(20, 30))
                     for i in range(num_fish)]
        self.foods = [Food(random.uniform(0, width), 
                          random.uniform(0, height)) 
                     for _ in range(num_food)]
        
        # 创建图形
        self.fig, self.ax = plt.subplots(figsize=(10, 6.7))
        self.ax.set_xlim(0, width)
        self.ax.set_ylim(0, height)
        self.ax.set_facecolor('#1a5276')
        self.ax.set_title("Artificial Fish Swarm Algorithm Simulation", color='white', fontsize=14)
        self.ax.set_aspect('equal')
        self.fig.patch.set_facecolor('#073b4c')
        
        # 绘制鱼群
        self.fish_scatter = self.ax.scatter([], [], color='orange', s=80, 
                                          edgecolor='darkorange', label='Fish')
        
        # 绘制食物
        self.food_scatter = self.ax.scatter([], [], color='yellow', s=100, 
                                          marker='*', alpha=0.8, label='Food')
        
        # 添加图例
        self.ax.legend(loc='upper right', facecolor='#073b4c', edgecolor='cyan', 
                     labelcolor='white')
        
        # 添加水草装饰
        for _ in range(10):
            grass_x = random.uniform(0, width)
            height = random.uniform(5, 20)
            grass = patches.Rectangle((grass_x, 0), width=1, height=height, 
                                    facecolor='green', alpha=0.5)
            self.ax.add_patch(grass)
        
        # 添加石头
        for _ in range(5):
            stone_x = random.uniform(0, width)
            stone_y = random.uniform(0, height/4)
            stone_size = random.uniform(5, 15)
            stone = patches.Circle((stone_x, stone_y), stone_size, 
                                 facecolor='#333333', alpha=0.7)
            self.ax.add_patch(stone)
        
        # 状态文本
        self.status_text = self.ax.text(10, height-20, "", fontsize=10, color='white')
        
        # 添加水波纹
        self.ripples = []
        for _ in range(15):
            ripple = patches.Circle((random.uniform(0, width), 
                                   random.uniform(0, height)), 
                                   random.uniform(1, 5),
                                   facecolor='none', edgecolor='lightblue', 
                                   alpha=0.6, linewidth=0.5)
            self.ax.add_patch(ripple)
            self.ripples.append(ripple)

    def update_ripples(self):
        # 更新水波纹效果
        for ripple in self.ripples:
            center = ripple.get_center()
            alpha = ripple.get_alpha()
            radius = ripple.get_radius()
            
            # 轻微移动位置
            new_x = center[0] + random.uniform(-1, 1)
            new_y = center[1] + random.uniform(-1, 1)
            
            # 限制在鱼缸内
            if new_x < 0 or new_x > self.width or new_y < 0 or new_y > self.height:
                new_x = random.uniform(0, self.width)
                new_y = random.uniform(0, self.height)
            
            # 更新半径和透明度
            new_radius = radius + random.uniform(-0.2, 0.2)
            if new_radius > 6 or new_radius < 1:
                new_radius = random.uniform(1, 5)
            
            ripple.set_center((new_x, new_y))
            ripple.set_radius(new_radius)
    
    def update(self, frame):
        # 随机添加新食物（20%概率）
        if len(self.foods) < 10 and random.random() < 0.2:
            self.foods.append(Food(random.uniform(0, self.width), 
                                 random.uniform(0, self.height)))
        
        # 移动所有鱼
        for fish in self.fishes:
            fish.move(self.fishes, self.foods, self.width, self.height)
        
        # 更新鱼的位置
        fish_positions = np.array([(fish.x, fish.y) for fish in self.fishes])
        self.fish_scatter.set_offsets(fish_positions)
        
        # 计算鱼群的移动方向并设置角度
        angles = []
        for fish in self.fishes:
            angle = np.arctan2(fish.vy, fish.vx) * 180 / np.pi
            angles.append(angle)
            
        # 设置鱼图标的方向（注意：这个模拟中我们用圆点代替，实际实现可以用三角形）
        sizes = [80 for _ in self.fishes]
        self.fish_scatter.set_sizes(sizes)
        
        # 更新食物位置
        if self.foods:
            food_positions = np.array([(food.x, food.y) for food in self.foods])
            self.food_scatter.set_offsets(food_positions)
        else:
            self.food_scatter.set_offsets([])
        
        # 更新水波纹
        self.update_ripples()
        
        # 更新状态文本
        states = {"following": 0, "crowding": 0, "exploring": 0}
        for fish in self.fishes:
            states[fish.state] += 1
        
        status_str = (f"Total Fish: {len(self.fishes)}  "
                      f"Food: {len(self.foods)}  "
                      f"Following: {states['following']}  "
                      f"Crowding: {states['crowding']}  "
                      f"Exploring: {states['exploring']}")
        self.status_text.set_text(status_str)
        
        return self.fish_scatter, self.food_scatter, self.status_text, *self.ripples

    def animate(self):
        anim = FuncAnimation(self.fig, self.update, frames=200, 
                           interval=50, blit=True)
        plt.show()

# 创建并运行动画
if __name__ == "__main__":
    aquarium = Aquarium(num_fish=30, num_food=8)
    aquarium.animate()