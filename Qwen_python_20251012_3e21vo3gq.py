import json
import pandas as pd

# JSONファイルを読み込む
json_file_path = r"E:\work\mlb\mlb_2025_pitcher_max_and_avg_fastball_speeds.json"

with open(json_file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# data が辞書であることを確認
if not isinstance(data, dict):
    raise ValueError("Loaded JSON data is not a dictionary. Expected structure: {pitcher_name: {stats}}")

# 辞書から直接DataFrameを作成
# orient='index' で、キー（選手名）が行インデックス、値（統計辞書）が列になります。
# その後、.T で転置し、選手名が行、統計が列になります。
df = pd.DataFrame.from_dict(data, orient='index')

# インデックス名を設定
df.index.name = 'Pitcher'

print("--- DataFrame Info ---")
print(df.info())

print("\n--- DataFrame Head ---")
print(df.head())

# 列名を確認
print(f"\n--- DataFrame Columns ---")
print(df.columns.tolist())

# 'max_speed' と 'avg_fastball_speed' が存在するか確認
required_columns = ['max_speed', 'avg_fastball_speed']
missing_columns = [col for col in required_columns if col not in df.columns]
if missing_columns:
    raise KeyError(f"Required columns are missing from the DataFrame: {missing_columns}")

# 数値データであることを確認
df['max_speed'] = pd.to_numeric(df['max_speed'], errors='coerce')
df['avg_fastball_speed'] = pd.to_numeric(df['avg_fastball_speed'], errors='coerce')

# NaN（データがない場合）を削除 (オプション)
# df.dropna(subset=required_columns, inplace=True)

print("\n--- Basic Statistics ---")
print(df[required_columns].describe())

# Excelファイルとして保存
excel_file_path = r"E:\work\mlb\mlb_2025_pitcher_speeds.xlsx"
df.to_excel(excel_file_path, index=True, sheet_name='Pitcher_Speeds')

print(f"\nDataFrame has been successfully saved to {excel_file_path}")

# Excelでグラフや統計を行うための基本統計情報を別シートに追加する例
with pd.ExcelWriter(excel_file_path, engine='openpyxl', mode='a') as writer: # mode='a' で追記
    stats_summary = df[required_columns].describe()
    stats_summary.to_excel(writer, sheet_name='Basic_Stats')

print(f"Basic statistics have been added to the 'Basic_Stats' sheet in {excel_file_path}")