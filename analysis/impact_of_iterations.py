import matplotlib.pyplot as plt

# 数据
max_iterations = [3, 6, 9, 12, 15, 18, 21]
compilation_success = [71.1, 79.7, 92.8, 96.3, 98.8, 98.8, 99.1]
execution_success = [23.6, 32.3, 40.2, 48.2, 52.5, 52.5, 52.5]
transpilation_time = [28, 33, 69, 115, 198, 255, 328]

# 创建图表和主坐标轴
fig, ax1 = plt.subplots(figsize=(10, 8))

# 左轴：成功率（蓝色线）
ax1.set_xlabel('Maximum Iterations', fontsize=14)
ax1.set_ylabel('Success Rate (%)', color='tab:blue', fontsize=14)
ax1.plot(max_iterations, compilation_success, 'D-', color='tab:blue', label='Compilation Success')
ax1.plot(max_iterations, execution_success, 's-', color='tab:blue', label='Execution Success')

# 添加成功率标签
for x, y in zip(max_iterations, compilation_success):
    ax1.text(x, y + 2, f'{y}%', color='tab:blue', ha='center', fontsize=11, fontweight='bold')
for x, y in zip(max_iterations, execution_success):
    ax1.text(x, y + 2, f'{y}%', color='tab:blue', ha='center', fontsize=11, fontweight='bold')

# 左轴设置
ax1.tick_params(axis='y', labelcolor='tab:blue', labelsize=12)
ax1.set_ylim(0, 110)
ax1.set_xticks(max_iterations)
ax1.tick_params(axis='x', labelsize=12, width=2)
ax1.tick_params(axis='y', width=2)

# 背景网格线：虚线，添加竖直网格线
ax1.grid(True, axis='y', linestyle='dashed', linewidth=0.8, color='lightgray')
ax1.grid(True, axis='x', linestyle='dashed', linewidth=0.8, color='lightgray')

# 右轴：转译时间（绿色线）
ax2 = ax1.twinx()
ax2.set_ylabel('Transpilation Time (min)', color='tab:green', fontsize=14)
ax2.plot(max_iterations, transpilation_time, 'o-', color='tab:green', label='Transpilation Time')

# 添加时间标签
for x, y in zip(max_iterations, transpilation_time):
    ax2.text(x, y + 5, f'{y}', color='tab:green', ha='center', fontsize=11, fontweight='bold')

# 右轴设置
ax2.tick_params(axis='y', labelcolor='tab:green', labelsize=12, width=2)
ax2.set_ylim(0, 350)

# 图例设置
fig.legend(loc='upper left', bbox_to_anchor=(0.08, 0.97), fontsize=13, frameon=True, framealpha=0.9)

# 坐标轴框线对齐
ax1.spines['right'].set_position(('axes', 1.0))
ax2.spines['right'].set_position(('axes', 1.0))

# 布局优化并显示图表
plt.tight_layout()

plt.savefig('impact_of_iterations.png', dpi=300)