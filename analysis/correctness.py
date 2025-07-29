import os
import pandas as pd

def collect_correctness(root_dir='../comparisons'):
    data = []
    overall_data = []
    for method in os.listdir(root_dir):
        metrics_path = os.path.join(root_dir, method, 'overall_metrics.csv')
        if os.path.isfile(metrics_path):
            df = pd.read_csv(metrics_path)
            for _, row in df.iterrows():
                entry = {
                    'Source': row['Source'],
                    'Method': method,
                    'Compiled': row['Compiled'],
                    'Passed': row['Passed']
                }
                if row['Source'] == 'Overall':
                    overall_data.append(entry)
                else:
                    data.append(entry)
    df_all = pd.DataFrame(data)
    df_all = df_all.sort_values(['Source', 'Method'])
    # 追加 Overall 行
    if overall_data:
        df_overall = pd.DataFrame(overall_data)
        df_overall = df_overall.sort_values(['Method'])
        df_all = pd.concat([df_all, df_overall], ignore_index=True)
    df_all.to_csv('correctness.csv', index=False)

if __name__ == "__main__":
    collect_correctness()