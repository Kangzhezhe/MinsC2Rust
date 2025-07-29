import pandas as pd

# 读取 overall_metrics.csv
df = pd.read_csv('../comparisons/MinsC2Rust/overall_metrics.csv')

# 只保留 Source, Loc, Fns 三列
df_selected = df[['Source', 'Loc', 'Fns']]

# 保存为新的 CSV 文件
df_selected.to_csv('statistics_of_programs.csv', index=False)