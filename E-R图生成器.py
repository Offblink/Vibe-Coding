#!/usr/bin/env python3
"""
单表DDL解析器与ER图生成器 - GUI版本
矩形实体 + 椭圆属性，只支持单个表
增加主属性标识功能
增加属性操作框：去除属性和设置主属性
"""

import re
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Ellipse, Rectangle
import numpy as np
from typing import Dict, List, Tuple
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os

class DDLParser:
    """DDL解析器类"""
    
    def __init__(self):
        self.tables = {}
        self.relationships = []
        self.manual_attributes = []  # 存储手动添加的属性
        self.primary_attributes = []  # 存储主属性
        self.removed_attributes = []  # 存储被移除的属性
        
    def parse_ddl(self, ddl_text: str):
        """解析DDL文本"""
        # 清空之前的数据
        self.tables = {}
        self.relationships = []
        self.manual_attributes = []
        self.primary_attributes = []
        self.removed_attributes = []
        
        # 按表分割DDL文本
        table_blocks = re.split(r'CREATE TABLE ', ddl_text)
        
        for block in table_blocks:
            if not block.strip():
                continue
                
            # 提取表名
            table_match = re.match(r'`?(\w+)`?\s*\(', block)
            if not table_match:
                continue
                
            table_name = table_match.group(1)
            self.tables[table_name] = {
                'columns': [],
                'primary_keys': [],
                'foreign_keys': []
            }
            
            # 提取表内容
            content_match = re.search(r'\((.*)\)[^)]*ENGINE', block, re.DOTALL)
            if not content_match:
                # 尝试其他匹配模式
                content_match = re.search(r'\((.*)\)[^)]*COMMENT', block, re.DOTALL)
                if not content_match:
                    continue
                    
            table_content = content_match.group(1)
            
            # 解析列定义
            self._parse_columns(table_name, table_content)
            
            # 解析主键和外键
            self._parse_constraints(table_name, table_content)
            
            # 识别主属性
            self._identify_primary_attributes(table_name)
            
            # 只处理第一个表
            break
    
    def _parse_columns(self, table_name: str, content: str):
        """解析列定义"""
        # 分割列定义
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip().strip(',')
            if not line or line.startswith('PRIMARY KEY') or line.startswith('FOREIGN KEY') or line.startswith('UNIQUE KEY'):
                continue
                
            # 提取列名和类型
            col_match = re.match(r'`?(\w+)`?\s+([\w\(\)\d,\.]+)', line)
            if col_match:
                col_name = col_match.group(1)
                col_type = col_match.group(2)
                
                # 检查是否是主键（在列定义中）
                is_primary = 'PRIMARY KEY' in line.upper()
                
                self.tables[table_name]['columns'].append({
                    'name': col_name,
                    'type': col_type,
                    'is_primary': is_primary
                })
    
    def _parse_constraints(self, table_name: str, content: str):
        """解析约束（主键、外键）"""
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip().strip(',')
            
            # 解析主键约束
            pk_match = re.search(r'PRIMARY KEY\s*\(([^)]+)\)', line, re.IGNORECASE)
            if pk_match:
                pk_columns = [col.strip('` ') for col in pk_match.group(1).split(',')]
                self.tables[table_name]['primary_keys'].extend(pk_columns)
                
            # 解析外键约束（虽然单表模式不处理外键，但保留解析逻辑）
            fk_match = re.search(r'FOREIGN KEY\s*\(([^)]+)\)\s*REFERENCES\s*`?(\w+)`?\s*\(([^)]+)\)', line, re.IGNORECASE)
            if fk_match:
                fk_column = fk_match.group(1).strip('` ')
                ref_table = fk_match.group(2)
                ref_column = fk_match.group(3).strip('` ')
                
                self.tables[table_name]['foreign_keys'].append({
                    'column': fk_column,
                    'ref_table': ref_table,
                    'ref_column': ref_column
                })
                
                # 添加关系到列表
                self.relationships.append((table_name, ref_table, fk_column, ref_column))
    
    def _identify_primary_attributes(self, table_name: str):
        """识别主属性"""
        if table_name not in self.tables:
            return
            
        table_info = self.tables[table_name]
        
        # 清空之前的主属性
        self.primary_attributes = []
        
        # 1. 检查列定义中的主键
        for col in table_info['columns']:
            if col['is_primary']:
                self.primary_attributes.append(col['name'])
        
        # 2. 检查主键约束
        for pk_col in table_info['primary_keys']:
            if pk_col not in self.primary_attributes:
                self.primary_attributes.append(pk_col)
        
        # 3. 检查常见的主键命名模式
        for col in table_info['columns']:
            col_name = col['name'].lower()
            # 常见的主键命名模式
            if (col_name in ['id', 'uuid'] or 
                col_name.endswith('_id') or 
                col_name.endswith('_key') or
                col_name.endswith('_pk') or
                'id' in col_name and col_name.startswith(('pk_', 'id_'))):
                if col['name'] not in self.primary_attributes:
                    self.primary_attributes.append(col['name'])
    
    def add_manual_attribute(self, table_name: str, attribute_name: str, attribute_type: str = "VARCHAR(100)"):
        """手动添加属性"""
        if table_name not in self.tables:
            return False
            
        # 检查属性是否已存在
        for col in self.tables[table_name]['columns']:
            if col['name'] == attribute_name:
                return False
                
        # 添加属性
        self.tables[table_name]['columns'].append({
            'name': attribute_name,
            'type': attribute_type,
            'is_primary': False
        })
        
        # 记录手动添加的属性
        self.manual_attributes.append(attribute_name)
        
        return True
    
    def remove_attribute(self, table_name: str, attribute_name: str):
        """移除属性"""
        if table_name not in self.tables:
            return False
            
        # 从表中移除属性
        for i, col in enumerate(self.tables[table_name]['columns']):
            if col['name'] == attribute_name:
                # 移除属性
                removed_col = self.tables[table_name]['columns'].pop(i)
                
                # 记录被移除的属性
                self.removed_attributes.append(attribute_name)
                
                # 如果属性是主属性，也从主属性列表中移除
                if attribute_name in self.primary_attributes:
                    self.primary_attributes.remove(attribute_name)
                
                # 如果属性是手动添加的，也从手动添加列表中移除
                if attribute_name in self.manual_attributes:
                    self.manual_attributes.remove(attribute_name)
                
                return True
                
        return False
    
    def toggle_primary_attribute(self, table_name: str, attribute_name: str):
        """切换主属性状态"""
        if table_name not in self.tables:
            return False
            
        # 检查属性是否存在
        attribute_exists = False
        for col in self.tables[table_name]['columns']:
            if col['name'] == attribute_name:
                attribute_exists = True
                break
                
        if not attribute_exists:
            return False
            
        # 切换主属性状态
        if attribute_name in self.primary_attributes:
            # 如果已经是主属性，则移除
            self.primary_attributes.remove(attribute_name)
            return False  # 返回False表示现在不是主属性
        else:
            # 如果不是主属性，则添加
            self.primary_attributes.append(attribute_name)
            return True  # 返回True表示现在是主属性
    
    def get_all_attributes(self, table_name: str):
        """获取所有属性（包括状态信息）"""
        if table_name not in self.tables:
            return []
            
        attributes = []
        for col in self.tables[table_name]['columns']:
            attributes.append({
                'name': col['name'],
                'type': col['type'],
                'is_primary': col['name'] in self.primary_attributes,
                'is_manual': col['name'] in self.manual_attributes,
                'is_removed': col['name'] in self.removed_attributes
            })
            
        return attributes


class ERDiagramGenerator:
    """ER图生成器类 - 矩形实体 + 椭圆属性（单表版本）"""
    
    def __init__(self, figsize=(12, 10)):
        self.fig, self.ax = plt.subplots(figsize=figsize)
        self.ax.set_xlim(0, 1)
        self.ax.set_ylim(0, 1)
        self.ax.axis('off')
        self.entity_positions = {}  # 实体位置
        self.attribute_positions = {}  # 属性位置
        self.connections = []  # 连接关系
        
    def generate_er_diagram(self, tables: Dict, manual_attributes: List[str] = None, primary_attributes: List[str] = None, removed_attributes: List[str] = None):
        """生成ER图（只处理第一个表）"""
        if not tables:
            return
            
        # 只取第一个表
        table_name = list(tables.keys())[0]
        table_info = tables[table_name]
        
        # 计算布局（单表居中，属性环绕）
        self._calculate_single_entity_layout(table_name, table_info, removed_attributes)
        
        # 1. 先绘制连接线（zorder=1，在最底层）
        for conn in self.connections:
            self._draw_connection(conn)
        
        # 2. 再绘制实体（矩形）（zorder=2，在中间层）
        for entity_name, pos in self.entity_positions.items():
            self._draw_entity(entity_name, pos)
        
        # 3. 最后绘制属性（椭圆）（zorder=3，在最顶层）
        for attr_name, pos in self.attribute_positions.items():
            # 提取属性名称（去掉表名前缀）
            attr_short_name = attr_name.split('.')[-1]
            
            # 检查是否是手动添加的属性
            is_manual = manual_attributes and attr_short_name in manual_attributes
            
            # 检查是否是主属性
            is_primary = primary_attributes and attr_short_name in primary_attributes
            
            # 检查是否是被移除的属性（不显示）
            is_removed = removed_attributes and attr_short_name in removed_attributes
            
            if not is_removed:  # 只绘制未被移除的属性
                self._draw_attribute(attr_name, attr_short_name, pos, is_manual, is_primary)
        
        # 添加标题
        plt.title(f'E-R Diagram: {table_name}', fontsize=16, pad=20)
        
        return self.fig
    
    def _calculate_single_entity_layout(self, table_name: str, table_info: Dict, removed_attributes: List[str] = None):
        """计算单个实体的布局（实体居中，属性360度环绕）"""
        # 实体居中
        center_x, center_y = 0.5, 0.5
        self.entity_positions[table_name] = (center_x, center_y)
        
        # 计算属性位置（360度均匀分布）
        # 过滤掉被移除的属性
        valid_attrs = []
        for col in table_info['columns']:
            if removed_attributes and col['name'] in removed_attributes:
                continue
            valid_attrs.append(col)
            
        num_attrs = len(valid_attrs)
        if num_attrs > 0:
            # 属性排列的半径（根据属性数量调整）
            if num_attrs <= 8:
                attr_radius = 0.3
            elif num_attrs <= 16:
                attr_radius = 0.4
            else:
                attr_radius = 0.5
            
            # 计算每个属性的角度（360度均匀分布）
            angles = np.linspace(0, 2*np.pi, num_attrs, endpoint=False)
            
            for i, col in enumerate(valid_attrs):
                angle = angles[i]
                attr_x = center_x + attr_radius * np.cos(angle)
                attr_y = center_y + attr_radius * np.sin(angle)
                
                attr_name = f"{table_name}.{col['name']}"
                self.attribute_positions[attr_name] = (attr_x, attr_y)
                
                # 添加实体到属性的连接
                self.connections.append(('entity', 'attribute', table_name, attr_name))
    
    def _draw_entity(self, entity_name: str, pos: Tuple[float, float]):
        """绘制实体（矩形）"""
        x, y = pos
        width, height = 0.12, 0.06
        
        # 绘制矩形（zorder=2，在中间层）
        rect = Rectangle((x - width/2, y - height/2), width, height,
                        linewidth=2, edgecolor='blue', facecolor='lightblue', alpha=1,
                        zorder=2)
        self.ax.add_patch(rect)
        
        # 添加实体名称（zorder=2，与矩形同一层）
        self.ax.text(x, y, entity_name, ha='center', va='center', 
                    fontsize=10, fontweight='bold', zorder=2)
    
    def _draw_attribute(self, attr_full_name: str, attr_name: str, pos: Tuple[float, float], 
                       is_manual: bool = False, is_primary: bool = False):
        """绘制属性（椭圆）"""
        x, y = pos
        width, height = 0.1, 0.05
        
        # 根据属性类型选择颜色和样式
        if is_primary:
            # 主属性：金色边框，黄色背景，加粗边框
            edge_color = 'goldenrod'
            face_color = 'lightyellow'
            linewidth = 3
        elif is_manual:
            # 手动添加的属性：红色边框，浅红色背景
            edge_color = 'red'
            face_color = 'lightcoral'
            linewidth = 1.5
        else:
            # 普通属性：绿色边框，浅绿色背景
            edge_color = 'green'
            face_color = 'lightgreen'
            linewidth = 1.5
        
        # 绘制椭圆（zorder=3，在最顶层）
        ellipse = Ellipse((x, y), width, height,
                         linewidth=linewidth, edgecolor=edge_color, facecolor=face_color, alpha=1,
                         zorder=3)
        self.ax.add_patch(ellipse)
        
        # 添加属性名称（zorder=3，与椭圆同一层）
        self.ax.text(x, y, attr_name, ha='center', va='center', 
                    fontsize=8, zorder=3)
    
    def _draw_connection(self, conn: Tuple):
        """绘制连接线"""
        conn_type, _, from_name, to_name = conn
        
        if conn_type == 'entity' and to_name.startswith(from_name + '.'):
            # 实体到属性的连接
            if from_name in self.entity_positions and to_name in self.attribute_positions:
                x1, y1 = self.entity_positions[from_name]
                x2, y2 = self.attribute_positions[to_name]
                
                # 绘制无向线段（zorder=1，在最底层）
                self.ax.plot([x1, x2], [y1, y2], 'k-', linewidth=1, alpha=0.7, zorder=1)


class DDLERDiagramApp:
    """DDL ER图生成器GUI应用"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("DDL ER图生成器")
        self.root.geometry("1000x700")
        
        # 创建主框架
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=1)
        self.main_frame.rowconfigure(1, weight=1)
        
        # 存储当前图形引用
        self.canvas = None
        self.save_btn = None
        self.right_button_frame = None
        self.current_parser = None  # 存储当前解析器实例
        self.attributes_listbox = None  # 属性列表框
        self.attributes_var = tk.StringVar()  # 列表框内容变量
        
        # 创建界面元素
        self._create_widgets()
        
    def _create_widgets(self):
        """创建界面组件"""
        # 标题
        title_label = ttk.Label(self.main_frame, text="DDL ER图生成器", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 10))
        
        # DDL输入标签
        ddl_label = ttk.Label(self.main_frame, text="请输入DDL语句:")
        ddl_label.grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        
        # DDL输入文本框
        self.ddl_text = scrolledtext.ScrolledText(self.main_frame, width=60, height=15)
        self.ddl_text.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # 属性操作框架（新增加）
        attr_ops_frame = ttk.LabelFrame(self.main_frame, text="属性操作", padding="5")
        attr_ops_frame.grid(row=2, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(10, 0), pady=(0, 10))
        attr_ops_frame.columnconfigure(0, weight=1)
        attr_ops_frame.rowconfigure(1, weight=1)
        
        # 属性列表框标签
        attr_list_label = ttk.Label(attr_ops_frame, text="当前属性列表:")
        attr_list_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        # 属性列表框
        list_frame = ttk.Frame(attr_ops_frame)
        list_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        self.attributes_listbox = tk.Listbox(list_frame, selectmode=tk.SINGLE, height=10)
        self.attributes_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 列表框滚动条
        list_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.attributes_listbox.yview)
        list_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.attributes_listbox.configure(yscrollcommand=list_scrollbar.set)
        
        # 属性操作按钮框架
        attr_buttons_frame = ttk.Frame(attr_ops_frame)
        attr_buttons_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
        # 移除属性按钮
        remove_attr_btn = ttk.Button(attr_buttons_frame, text="移除选中属性", command=self.remove_selected_attribute)
        remove_attr_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # 切换主属性按钮
        toggle_primary_btn = ttk.Button(attr_buttons_frame, text="切换主属性状态", command=self.toggle_primary_attribute)
        toggle_primary_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # 恢复所有属性按钮
        restore_attrs_btn = ttk.Button(attr_buttons_frame, text="恢复所有属性", command=self.restore_all_attributes)
        restore_attrs_btn.pack(side=tk.LEFT)
        
        # 手动添加属性框架
        manual_attr_frame = ttk.LabelFrame(self.main_frame, text="手动添加属性", padding="5")
        manual_attr_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 属性名输入
        attr_label = ttk.Label(manual_attr_frame, text="属性名:")
        attr_label.grid(row=0, column=0, padx=(0, 5))
        
        self.attr_entry = ttk.Entry(manual_attr_frame, width=30)
        self.attr_entry.grid(row=0, column=1, padx=(0, 10))
        
        # 属性类型输入
        type_label = ttk.Label(manual_attr_frame, text="类型:")
        type_label.grid(row=0, column=2, padx=(0, 5))
        
        self.type_entry = ttk.Entry(manual_attr_frame, width=20)
        self.type_entry.insert(0, "VARCHAR(100)")  # 默认类型
        self.type_entry.grid(row=0, column=3, padx=(0, 10))
        
        # 添加属性按钮
        self.add_attr_btn = ttk.Button(manual_attr_frame, text="添加此属性", command=self.add_manual_attribute)
        self.add_attr_btn.grid(row=0, column=4)
        
        # 按钮框架
        button_frame = ttk.Frame(self.main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 按钮 - 左对齐
        left_button_frame = ttk.Frame(button_frame)
        left_button_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 示例DDL按钮
        example_btn = ttk.Button(left_button_frame, text="加载示例DDL", command=self._load_example_ddl)
        example_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 按钮 - 右对齐
        self.right_button_frame = ttk.Frame(button_frame)
        self.right_button_frame.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        
        # 生成按钮
        generate_btn = ttk.Button(self.right_button_frame, text="生成ER图", command=self.generate_diagram)
        generate_btn.pack(side=tk.RIGHT)
        
        # 结果显示区域
        result_frame = ttk.LabelFrame(self.main_frame, text="ER图预览", padding="5")
        result_frame.grid(row=10, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(0, weight=1)
        
        # 图形显示区域
        self.figure_frame = ttk.Frame(result_frame)
        self.figure_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.figure_frame.columnconfigure(0, weight=1)
        self.figure_frame.rowconfigure(0, weight=1)
        
        # 状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        status_bar = ttk.Label(self.main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E))
        
        # 配置网格权重
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=0)
        self.main_frame.columnconfigure(2, weight=0)
        self.main_frame.rowconfigure(2, weight=0)
        self.main_frame.rowconfigure(5, weight=1)
        
        # 加载示例DDL
        self._load_example_ddl()
    
    def _load_example_ddl(self):
        """加载示例DDL"""
        example_ddl = """CREATE TABLE students (
    student_id INT PRIMARY KEY AUTO_INCREMENT COMMENT '学生ID',
    student_number VARCHAR(20) UNIQUE NOT NULL COMMENT '学号',
    student_name VARCHAR(50) NOT NULL COMMENT '学生姓名',
    gender ENUM('男', '女', '其他') NOT NULL COMMENT '性别',
    birth_date DATE COMMENT '出生日期',
    enrollment_year YEAR NOT NULL COMMENT '入学年份',
    major_id INT NOT NULL COMMENT '专业ID',
    class_name VARCHAR(50) COMMENT '班级名称',
    phone VARCHAR(15) COMMENT '联系电话',
    email VARCHAR(100) COMMENT '邮箱',
    status TINYINT DEFAULT 1 COMMENT '学生状态（1：在读，0：休学，2：毕业）',
    created_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学生信息表';"""
        
        self.ddl_text.delete(1.0, tk.END)
        self.ddl_text.insert(1.0, example_ddl)
        self.status_var.set("已加载示例DDL")
    
    def update_attributes_list(self):
        """更新属性列表框"""
        if not self.current_parser or not self.current_parser.tables:
            return
            
        # 清空列表框
        self.attributes_listbox.delete(0, tk.END)
        
        # 获取表名
        table_name = list(self.current_parser.tables.keys())[0]
        
        # 获取所有属性
        attributes = self.current_parser.get_all_attributes(table_name)
        
        # 添加属性到列表框
        for attr in attributes:
            # 构建显示字符串
            display_text = f"{attr['name']} ({attr['type']})"
            if attr['is_primary']:
                display_text += " ★"  # 主属性标识
            if attr['is_manual']:
                display_text += " [手动添加]"
            if attr['is_removed']:
                display_text += " [已移除]"
                
            self.attributes_listbox.insert(tk.END, display_text)
    
    def generate_diagram(self):
        """生成ER图"""
        # 获取DDL文本
        ddl_text = self.ddl_text.get(1.0, tk.END).strip()
        
        if not ddl_text:
            messagebox.showerror("错误", "请输入DDL语句")
            return
        
        try:
            # 解析DDL
            self.current_parser = DDLParser()
            self.current_parser.parse_ddl(ddl_text)
            
            if not self.current_parser.tables:
                messagebox.showerror("错误", "未找到有效的表定义")
                return
            
            # 显示解析结果
            table_name = list(self.current_parser.tables.keys())[0]
            table_info = self.current_parser.tables[table_name]
            
            # 显示主属性信息
            primary_info = ""
            if self.current_parser.primary_attributes:
                primary_info = f"，主属性: {', '.join(self.current_parser.primary_attributes)}"
            
            self.status_var.set(f"解析成功: {table_name}表 ({len(table_info['columns'])}个列{primary_info})")
            
            # 更新属性列表框
            self.update_attributes_list()
            
            # 生成ER图
            self._update_diagram()
            
        except Exception as e:
            messagebox.showerror("错误", f"生成ER图时出错: {str(e)}")
            self.status_var.set("生成ER图时出错")
    
    def _update_diagram(self):
        """更新ER图显示"""
        if not self.current_parser or not self.current_parser.tables:
            return
            
        table_name = list(self.current_parser.tables.keys())[0]
        table_info = self.current_parser.tables[table_name]
        
        # 生成ER图
        generator = ERDiagramGenerator()
        fig = generator.generate_er_diagram(
            self.current_parser.tables, 
            self.current_parser.manual_attributes,
            self.current_parser.primary_attributes,
            self.current_parser.removed_attributes
        )
        
        # 清除之前的图形
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
        
        # 显示新图形
        self.canvas = FigureCanvasTkAgg(fig, self.figure_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 添加保存按钮
        if self.save_btn:
            self.save_btn.destroy()
            
        self.save_btn = ttk.Button(
            self.right_button_frame, 
            text="保存ER图", 
            command=lambda: self.save_diagram(fig)
        )
        self.save_btn.pack(side=tk.RIGHT, padx=(10, 0))
    
    def add_manual_attribute(self):
        """手动添加属性"""
        if not self.current_parser or not self.current_parser.tables:
            messagebox.showwarning("警告", "请先生成ER图，然后再添加属性")
            return
            
        # 获取属性名和类型
        attr_name = self.attr_entry.get().strip()
        attr_type = self.type_entry.get().strip()
        
        if not attr_name:
            messagebox.showwarning("警告", "请输入属性名")
            return
            
        # 获取表名
        table_name = list(self.current_parser.tables.keys())[0]
        
        # 添加属性
        success = self.current_parser.add_manual_attribute(table_name, attr_name, attr_type)
        
        if success:
            self.status_var.set(f"已添加属性: {attr_name}")
            
            # 更新属性列表框
            self.update_attributes_list()
            
            # 更新ER图
            self._update_diagram()
            
            # 清空输入框
            self.attr_entry.delete(0, tk.END)
        else:
            messagebox.showwarning("警告", f"属性 '{attr_name}' 已存在")
    
    def remove_selected_attribute(self):
        """移除选中的属性"""
        if not self.current_parser or not self.current_parser.tables:
            messagebox.showwarning("警告", "请先生成ER图")
            return
            
        # 获取选中的属性
        selection = self.attributes_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个属性")
            return
            
        # 获取属性名（从显示文本中提取）
        display_text = self.attributes_listbox.get(selection[0])
        attr_name = display_text.split(' ')[0]  # 取第一个空格前的部分作为属性名
        
        # 获取表名
        table_name = list(self.current_parser.tables.keys())[0]
        
        # 移除属性
        success = self.current_parser.remove_attribute(table_name, attr_name)
        
        if success:
            self.status_var.set(f"已移除属性: {attr_name}")
            
            # 更新属性列表框
            self.update_attributes_list()
            
            # 更新ER图
            self._update_diagram()
        else:
            messagebox.showerror("错误", f"移除属性 '{attr_name}' 失败")
    
    def toggle_primary_attribute(self):
        """切换主属性状态"""
        if not self.current_parser or not self.current_parser.tables:
            messagebox.showwarning("警告", "请先生成ER图")
            return
            
        # 获取选中的属性
        selection = self.attributes_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个属性")
            return
            
        # 获取属性名（从显示文本中提取）
        display_text = self.attributes_listbox.get(selection[0])
        attr_name = display_text.split(' ')[0]  # 取第一个空格前的部分作为属性名
        
        # 获取表名
        table_name = list(self.current_parser.tables.keys())[0]
        
        # 切换主属性状态
        is_now_primary = self.current_parser.toggle_primary_attribute(table_name, attr_name)
        
        if is_now_primary:
            self.status_var.set(f"已将 '{attr_name}' 设置为主属性")
        else:
            self.status_var.set(f"已取消 '{attr_name}' 的主属性状态")
            
        # 更新属性列表框
        self.update_attributes_list()
        
        # 更新ER图
        self._update_diagram()
    
    def restore_all_attributes(self):
        """恢复所有被移除的属性"""
        if not self.current_parser or not self.current_parser.tables:
            messagebox.showwarning("警告", "请先生成ER图")
            return
            
        # 获取表名
        table_name = list(self.current_parser.tables.keys())[0]
        
        # 恢复所有被移除的属性
        restored_count = 0
        for attr_name in self.current_parser.removed_attributes[:]:  # 使用切片创建副本
            # 重新添加属性到表中
            for col in self.current_parser.tables[table_name]['columns']:
                if col['name'] == attr_name:
                    # 从移除列表中移除
                    self.current_parser.removed_attributes.remove(attr_name)
                    restored_count += 1
                    break
        
        if restored_count > 0:
            self.status_var.set(f"已恢复 {restored_count} 个属性")
            
            # 更新属性列表框
            self.update_attributes_list()
            
            # 更新ER图
            self._update_diagram()
        else:
            messagebox.showinfo("提示", "没有可恢复的属性")
    
    def save_diagram(self, fig):
        """保存ER图"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[
                    ("PNG 图像", "*.png"),
                    ("PDF 文档", "*.pdf"),
                    ("所有文件", "*.*")
                ],
                title="保存ER图"
            )
            
            if filename:
                # 根据文件扩展名选择保存格式
                if filename.lower().endswith('.pdf'):
                    fig.savefig(filename, bbox_inches='tight', facecolor='white')
                else:
                    fig.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white')
                
                messagebox.showinfo("成功", f"ER图已保存: {filename}")
                self.status_var.set(f"ER图已保存: {os.path.basename(filename)}")
                
        except Exception as e:
            messagebox.showerror("错误", f"保存ER图时出错: {str(e)}")


def main():
    """主函数"""
    # 检查依赖
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("错误：请先安装matplotlib库")
        print("安装命令: pip install matplotlib")
        return
    
    # 创建GUI界面
    root = tk.Tk()
    app = DDLERDiagramApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()