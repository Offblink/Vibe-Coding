import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np
import colorsys

class PointLocator:
    def __init__(self):
        self.fig, self.ax = plt.subplots(figsize=(8, 8))
        self.ax.set_xlim(0, 10)
        self.ax.set_ylim(0, 10)
        self.ax.set_aspect('equal')
        self.ax.set_title('Cllck to select your point...')
        self.ax.set_xlabel('X')
        self.ax.set_ylabel('Y')
        self.ax.grid(True)
        
        # 绘制初始正方形
        self.original_rect = Rectangle((0, 0), 10, 10, fill=False, edgecolor='blue', lw=2)
        self.ax.add_patch(self.original_rect)
        
        self.target_point = None
        self.current_bounds = [0, 10, 0, 10]  # [xmin, xmax, ymin, ymax]
        self.fill_params = []  # 存储填充区域的参数
        self.lines = []  # 存储所有绘制的线条
        self.iteration_count = 0  # 跟踪迭代次数
        self.fig.canvas.mpl_connect('button_press_event', self.on_click)
        plt.show()
    
    def on_click(self, event):
        if not event.inaxes:
            return
        
        # 第一次点击记录目标点
        if self.target_point is None:
            self.target_point = (event.xdata, event.ydata)
            # 隐藏目标点（只用于定位）
            self.ax.plot(event.xdata, event.ydata, 'ro', alpha=0)
            self.ax.set_title('Locating...')
            plt.draw()
            self.locate_point()
    
    def locate_point(self):
        xmin, xmax, ymin, ymax = self.current_bounds
        width = xmax - xmin
        height = ymax - ymin
        
        # 终止条件：区域小于0.1单位
        if width < 0.1 or height < 0.1:
            self.show_result()
            return
        
        # 计算中点
        mid_x = (xmin + xmax) / 2
        mid_y = (ymin + ymax) / 2
        
        # 为当前搜索区域添加彩色填充
        self.iteration_count += 1
        
        # 使用HSV颜色空间，根据迭代次数改变色相
        hue = (self.iteration_count * 30) % 360  # 每步旋转30度
        saturation = 0.6
        value = 0.9 - min(0.3, self.iteration_count * 0.03)  # 随着迭代次数增加，亮度略微降低
        
        # 将HSV转换为RGB
        r, g, b = colorsys.hsv_to_rgb(hue/360, saturation, value)
        color = (r, g, b)
        
        # 保存填充参数（不创建实际对象）
        fill_params = {
            'xy': (xmin, ymin),
            'width': width,
            'height': height,
            'facecolor': color,
            'alpha': 0.3
        }
        self.fill_params.append(fill_params)
        
        # 创建并添加填充矩形到当前图形
        fill_patch = Rectangle((xmin, ymin), width, height, 
                              facecolor=color, alpha=0.3, edgecolor='none')
        self.ax.add_patch(fill_patch)
        
        # 绘制田字格并保存线条参数
        # 水平线（从当前左边界到右边界，高度为mid_y）
        hline, = self.ax.plot([xmin, xmax], [mid_y, mid_y], color='blue', alpha=0.7)
        # 垂直线（从当前下边界到上边界，位置为mid_x）
        vline, = self.ax.plot([mid_x, mid_x], [ymin, ymax], color='blue', alpha=0.7)
        
        # 保存线条参数
        self.lines.append({
            'points': [(xmin, mid_y), (xmax, mid_y)],
            'color': hline.get_color(),
            'alpha': hline.get_alpha(),
            'linewidth': hline.get_linewidth()
        })
        self.lines.append({
            'points': [(mid_x, ymin), (mid_x, ymax)],
            'color': vline.get_color(),
            'alpha': vline.get_alpha(),
            'linewidth': vline.get_linewidth()
        })
        
        plt.draw()
        
        # 确定点在哪个象限
        tx, ty = self.target_point
        if tx <= mid_x:
            if ty <= mid_y:
                self.current_bounds = [xmin, mid_x, ymin, mid_y]
            else:
                self.current_bounds = [xmin, mid_x, mid_y, ymax]
        else:
            if ty <= mid_y:
                self.current_bounds = [mid_x, xmax, ymin, mid_y]
            else:
                self.current_bounds = [mid_x, xmax, mid_y, ymax]
        
        # 递归细分
        plt.pause(0.5)  # 暂停以便观察
        self.locate_point()
    
    def show_result(self):
        x, y = self.target_point
        
        # 创建新图形显示最终结果
        result_fig, result_ax = plt.subplots(figsize=(8, 8))
        result_ax.set_xlim(0, 10)
        result_ax.set_ylim(0, 10)
        result_ax.set_aspect('equal')
        result_ax.set_title(f'Location is completed!')
        result_ax.grid(True)
        
        # 显示目标点
        result_ax.plot(x, y, 'ro', markersize=8)
        
        # 添加坐标信息
        result_ax.text(x, y + 0.3, f'({x:.3f}, {y:.3f})', 
                      fontsize=12, ha='center', 
                      bbox=dict(facecolor='white', alpha=0.8))
        
        # 重新创建所有填充区域
        for params in self.fill_params:
            rect = Rectangle(params['xy'], params['width'], params['height'],
                            facecolor=params['facecolor'], alpha=params['alpha'],
                            edgecolor='none')
            result_ax.add_patch(rect)
        
        # 重新绘制田字格线条
        for line_params in self.lines:
            points = line_params['points']
            xdata = [p[0] for p in points]
            ydata = [p[1] for p in points]
            result_ax.plot(xdata, ydata, 
                          color=line_params['color'],
                          alpha=line_params['alpha'],
                          linewidth=line_params['linewidth'])
        
        # 重新绘制原正方形
        result_ax.add_patch(Rectangle((0, 0), 10, 10, 
                                    fill=False, edgecolor='blue', lw=1))
        
        # 添加图例说明
        result_ax.text(0.1, 9.9, f'Return Times: {self.iteration_count}', 
                      fontsize=12, va='top', ha='left',
                      bbox=dict(facecolor='white', alpha=0.8))
        
        plt.tight_layout()
        plt.show()

if __name__ == "__main__":
    locator = PointLocator()