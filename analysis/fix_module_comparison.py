import pandas as pd

# 读取 w/o fixing 的 Pass Rate
once_pass = pd.read_csv('../comparisons/MinsC2Rust/c_algorithm/Output/once_pass_rates.csv')
# 读取 with fixing 的 Pass Rate (without test)
compile_pass = pd.read_csv('../comparisons/MinsC2Rust/c_algorithm/Output/compile_pass_rate.csv')

# 只保留需要的列并重命名
once_pass = once_pass[['Source', 'Pass Rate']].rename(columns={'Pass Rate': 'w/o fixing'})
compile_pass = compile_pass[['Source', 'Pass Rate (without test)']].rename(columns={'Pass Rate (without test)': 'with fixing'})

# 合并
df = pd.merge(once_pass, compile_pass, on='Source', how='inner')

# 去掉百分号并转为float
df['w/o fixing'] = df['w/o fixing'].astype(str).str.rstrip('%').astype(float)
df['with fixing'] = df['with fixing'].astype(str).str.rstrip('%').astype(float)

# 计算提升
df['Improv.'] = (df['with fixing'] - df['w/o fixing']).round(1)
df['w/o fixing'] = df['w/o fixing'].round(1)
df['with fixing'] = df['with fixing'].round(1)

# 百分号格式
df['w/o fixing'] = df['w/o fixing'].astype(str) + '%'
df['with fixing'] = df['with fixing'].astype(str) + '%'
df['Improv.'] = '+' + df['Improv.'].astype(str)


# 保存为CSV
df.rename(columns={'Source': 'Program'}, inplace=True)
df.to_csv('fix_module_comparison.csv', index=False)