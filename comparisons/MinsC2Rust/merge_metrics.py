import pandas as pd

# 读取两个csv
df1 = pd.read_csv('c_algorithm/Output/test_project/metrics.csv')
df2 = pd.read_csv('crown/Output/test_project/metrics.csv')

# 去掉各自的 Overall 行
df1_no_overall = df1[df1['Source'] != 'Overall']
df2_no_overall = df2[df2['Source'] != 'Overall']

# 合并数据
merged = pd.concat([df1_no_overall, df2_no_overall], ignore_index=True)

# 计算 Overall
overall1 = df1[df1['Source'] == 'Overall'].iloc[0]
overall2 = df2[df2['Source'] == 'Overall'].iloc[0]

def avg_percent(val1, val2):
    v1 = float(str(val1).replace('%',''))
    v2 = float(str(val2).replace('%',''))
    return f"{(v1 + v2) / 2:.2f}%"

overall_row = {
    'Source': 'Overall',
    'Loc': int(overall1['Loc']) + int(overall2['Loc']),
    'Fns': int(overall1['Fns']) + int(overall2['Fns']),
    'Compiled': avg_percent(overall1['Compiled'], overall2['Compiled']),
    'Passed': avg_percent(overall1['Passed'], overall2['Passed']),
    'Safe Loc': avg_percent(overall1['Safe Loc'], overall2['Safe Loc']),
    'Safe Ref': avg_percent(overall1['Safe Ref'], overall2['Safe Ref']),
}

# 添加 Overall 行
merged = pd.concat([merged, pd.DataFrame([overall_row])], ignore_index=True)

# 保存
merged.to_csv('overall_metrics.csv', index=False)