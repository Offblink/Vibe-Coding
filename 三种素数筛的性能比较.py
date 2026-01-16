import math
import time
import random
import matplotlib.pyplot as plt
import numpy as np
import sys

def is_prime_miller_rabin(n, k=5):
    """
    使用Miller-Rabin算法进行素数测试
    对于n < 2^64，使用确定的k=12可以保证正确性
    """
    if n < 2:
        return False
    if n == 2 or n == 3:
        return True
    if n % 2 == 0:
        return False
    
    # 将n-1分解为d*2^s
    d = n - 1
    s = 0
    while d % 2 == 0:
        d //= 2
        s += 1
    
    # 进行k次测试
    for _ in range(k):
        a = random.randint(2, n-2)
        x = pow(a, d, n)
        if x == 1 or x == n-1:
            continue
        for _ in range(s-1):
            x = pow(x, 2, n)
            if x == n-1:
                break
        else:
            return False
    return True

def is_prime_optimized(n):
    """使用6k±1优化法检查素数"""
    if n <= 1:
        return False
    if n <= 3:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    
    return True

def is_prime_original(n):
    """原始方法检查素数"""
    if n < 2:
        return False
    if n == 2:
        return True
    for i in range(2, int(math.sqrt(n)) + 1):
        if n % i == 0:
            return False
    return True

def compare_methods(max_num=100000):
    """比较三种素数检查方法的性能"""
    methods = [
        ("Original", is_prime_original),
        ("6k±1 Optimized", is_prime_optimized),
        ("Miller-Rabin", lambda n: is_prime_miller_rabin(n, k=5))
    ]
    
    # 设置图表
    plt.figure(figsize=(12, 8))
    colors = ['blue', 'red', 'green']
    
    results = {}
    
    for idx, (name, func) in enumerate(methods):
        print(f"Testing {name} method...")
        start_time = time.time()
        time_points = []
        count_points = []
        
        # 测试方法
        for i in range(1, max_num + 1):
            func(i)
            if i % 1000 == 0 or i == max_num:  # 每1000次记录一次
                elapsed = time.time() - start_time
                time_points.append(elapsed)
                count_points.append(i)
        
        total_time = time.time() - start_time
        results[name] = {
            'time_points': time_points,
            'count_points': count_points,
            'total_time': total_time
        }
        
        # 绘制曲线
        plt.plot(time_points, count_points, color=colors[idx], label=name, linewidth=2)
    
    # 计算性能提升
    original_time = results["Original"]['total_time']
    optimized_time = results["6k±1 Optimized"]['total_time']
    miller_time = results["Miller-Rabin"]['total_time']
    
    optimized_speedup = original_time / optimized_time
    miller_speedup = original_time / miller_time
    
    # 设置图表属性
    plt.xlabel('Time (seconds)')
    plt.ylabel('Numbers Checked')
    plt.title(f'Performance Comparison of Prime Checking Methods (Up to {max_num})')
    plt.legend()
    plt.grid(True)
    
    # 添加性能比较信息
    info_text = (f'Original Method: {original_time:.2f}s\n'
                 f'6k±1 Optimized: {optimized_time:.2f}s ({optimized_speedup:.1f}x faster)\n'
                 f'Miller-Rabin: {miller_time:.2f}s ({miller_speedup:.1f}x faster)')
    
    plt.text(0.02, 0.98, info_text, transform=plt.gca().transAxes, verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    # 保存图表
    plt.savefig('prime_methods_comparison_high_performance.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    return results

def generate_prime_table_high_performance(filename="prime_table.txt", start=1, columns=6, max_num=100000):
    """使用最高效方法生成素数表格"""
    black_char = '■'  # 黑格表示素数
    white_char = '□'  # 白格表示合数
    
    prime_count = 0
    start_time = time.time()
    last_update_time = time.time()
    
    # 设置实时图表
    plt.ion()
    fig, ax = plt.subplots(figsize=(10, 6))
    time_points = []
    count_points = []
    
    # 初始绘制
    ax.set_xlabel('Time (seconds)')
    ax.set_ylabel('Numbers Checked')
    ax.set_title(f'Prime Checking Progress (Miller-Rabin Method)')
    ax.grid(True)
    plt.draw()
    plt.pause(0.1)
    
    with open(filename, 'w', encoding='utf-8') as file:
        num = start
        try:
            while num <= max_num:
                # 生成一行
                row = []
                for _ in range(columns):
                    if num > max_num:
                        break
                    
                    # 使用最高效的Miller-Rabin方法
                    is_prime = is_prime_miller_rabin(num, k=5)
                    
                    if is_prime:
                        row.append(black_char)
                        prime_count += 1
                    else:
                        row.append(white_char)
                    
                    num += 1
                
                # 将行写入文件
                file.write(''.join(row) + '\n')
                
                # 定期更新图表（每秒最多更新一次）
                current_time = time.time()
                if current_time - last_update_time >= 0.5 or num > max_num:
                    elapsed = current_time - start_time
                    time_points.append(elapsed)
                    count_points.append(num - 1)
                    
                    # 更新图表
                    ax.clear()
                    if count_points:
                        ax.plot(time_points, count_points, 'b-', linewidth=2)
                    ax.set_xlabel('Time (seconds)')
                    ax.set_ylabel('Numbers Checked')
                    ax.set_title(f'Prime Checking Progress (Miller-Rabin Method) - {num-1}/{max_num}')
                    ax.grid(True)
                    
                    # 添加当前速度信息
                    if len(time_points) > 1:
                        # 计算平均速度
                        avg_speed = count_points[-1] / elapsed
                        ax.text(0.02, 0.98, f'Avg speed: {avg_speed:.1f} numbers/sec', 
                                transform=ax.transAxes, verticalalignment='top',
                                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
                    
                    plt.draw()
                    plt.pause(0.001)
                    last_update_time = current_time
                
            # 最终统计
            density = (prime_count / max_num) * 100
            total_time = time.time() - start_time
            
            print(f"\nCompleted. Checked {max_num} numbers.")
            print(f"Primes found: {prime_count}")
            print(f"Prime density: {density:.6f}%")
            print(f"Total time: {total_time:.2f} seconds")
            print(f"Average speed: {max_num/total_time:.1f} numbers/second")
            
        except KeyboardInterrupt:
            print(f"\nInterrupted at number {num}")
        
        finally:
            # 确保最终图表被保存
            plt.savefig('prime_check_progress_miller_rabin.png', dpi=300, bbox_inches='tight')
            plt.ioff()
            plt.show()

if __name__ == '__main__':
    print("High-Performance Prime Number Checker")
    print("1. Compare three methods")
    print("2. Generate prime table with Miller-Rabin method")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        max_num = int(input("Enter maximum number to check (default 100000): ") or "100000")
        compare_methods(max_num)
    else:
        filename = input("Enter output filename (default prime_table.txt): ").strip() or "prime_table.txt"
        start_num = int(input("Enter start number (default 1): ") or "1")
        columns = int(input("Enter columns per row (default 6): ") or "6")
        max_num = int(input("Enter maximum number to check (default 100000): ") or "100000")
        generate_prime_table_high_performance(filename, start_num, columns, max_num)
    
    input("\nPress Enter to exit...")