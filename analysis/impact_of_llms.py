import matplotlib.pyplot as plt
import numpy as np

# 数据准备
models = ['Deepseek-v3', 'GPT-4o', 'Claude-3.5', 'Qwen-Coder-Plus']
compiled_overall = [95.65, 94.64, 83.56, 83.39]
passed_overall = [52.76, 49.07, 42.31, 37.84]
safe_loc = [100.00, 100.00, 100.00, 99.92]
safe_ref = [92.71, 94.37, 95.07, 94.39]

# 设置柱状图参数
x = np.arange(len(models))
bar_width = 0.35

# 创建画布
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# 第一个子图：Compiled 和 Passed
for i, (comp, pas) in enumerate(zip(compiled_overall, passed_overall)):
    # Compiled 柱状图
    bar1 = axes[0].bar(i - bar_width/2, comp, bar_width, color='#87CEEB', edgecolor='black')
    # Passed 柱状图
    bar2 = axes[0].bar(i + bar_width/2, pas, bar_width, color='#FFDAB9', edgecolor='black')
    
    # 添加数据标注
    axes[0].text(bar1[0].get_x() + bar1[0].get_width()/2, comp + 0.5,
                f'{comp:.1f}%', ha='center', va='bottom', fontsize=14)
    axes[0].text(bar2[0].get_x() + bar2[0].get_width()/2, pas + 0.5,
                f'{pas:.1f}%', ha='center', va='bottom', fontsize=14)

axes[0].set_xticks(x)
axes[0].set_xticklabels(models, rotation=45, ha='right', fontsize=14)
axes[0].set_ylabel('Percentage (%)', fontsize=16)
axes[0].set_title('Correctness Metrics', fontsize=18)
axes[0].legend(['Compiled', 'Passed'], loc='lower right', fontsize=14)  # 图例放到右下角
axes[0].grid(axis='y', linestyle='--', alpha=0.7)
axes[0].set_ylim(0, 115)  # 扩展y轴范围保证标注可见

# 第二个子图：Safe Loc 和 Safe Ref
for i, (loc, ref) in enumerate(zip(safe_loc, safe_ref)):
    # Safe Loc 柱状图
    bar1 = axes[1].bar(i - bar_width/2, loc, bar_width, color='#98FB98', edgecolor='black')
    # Safe Ref 柱状图
    bar2 = axes[1].bar(i + bar_width/2, ref, bar_width, color='#FFB6C1', edgecolor='black')
    
    # 添加数据标注
    axes[1].text(bar1[0].get_x() + bar1[0].get_width()/2, loc + 0.5,
                f'{loc:.1f}%', ha='center', va='bottom', fontsize=14)
    axes[1].text(bar2[0].get_x() + bar2[0].get_width()/2, ref + 0.5,
                f'{ref:.1f}%', ha='center', va='bottom', fontsize=14)

axes[1].set_xticks(x)
axes[1].set_xticklabels(models, rotation=45, ha='right', fontsize=14)
axes[1].set_ylabel('Percentage (%)', fontsize=16)
axes[1].set_title('Safety Metrics', fontsize=18)
axes[1].legend(['Safe Loc.', 'Safe Ref.'], loc='lower right', fontsize=14)  # 图例放到右下角
axes[1].grid(axis='y', linestyle='--', alpha=0.7)
axes[1].set_ylim(0, 115)

# 调整布局并保存
plt.tight_layout()
plt.savefig('impact_of_llms.png', dpi=300, bbox_inches='tight')
plt.show()