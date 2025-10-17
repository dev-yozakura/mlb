import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# JSONファイルを読み込む
json_file_path = r"E:\work\mlb\mlb_2025_pitcher_max_and_avg_fastball_speeds.json"

with open(json_file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# data が辞書であることを確認
if not isinstance(data, dict):
    raise ValueError("Loaded JSON data is not a dictionary. Expected structure: {pitcher_name: {stats}}")

# データの構造を確認 (最初の2つを表示)
print("--- Sample of loaded data structure ---")
for i, (k, v) in enumerate(data.items()):
    if i >= 2:
        break
    print(f"  {k}: {v}")

# pandas DataFrameに変換
# orient='index' で、入力辞書のキーを行インデックスとします。
# これにより、選手名が行インデックス、統計辞書が列になります。
# 次に .T で転置し、選手名が列インデックス、統計項目が行インデックスになります。
# 最後に .T で転置し、選手名が行インデックス、統計(max_speed, avg_fastball_speed)が列になります。
# つまり、json_normalize(data, orient='index').T が正しい処理です。
df = pd.json_normalize(data).T

print("--- DataFrame Info (Before Filter) ---")
print(df.info())

print("\n--- DataFrame Head (Before Filter) ---")
print(df.head())

# 'max_speed' と 'avg_fastball_speed' が存在するか確認
required_columns = ['max_speed', 'avg_fastball_speed']
missing_columns = [col for col in required_columns if col not in df.columns]
if missing_columns:
    raise KeyError(f"Required columns are missing from the DataFrame: {missing_columns}")

# 数値データであることを確認
df['max_speed'] = pd.to_numeric(df['max_speed'], errors='coerce')
df['avg_fastball_speed'] = pd.to_numeric(df['avg_fastball_speed'], errors='coerce')

# 修正: avg_fastball_speed が 0 より大きい選手のみにフィルタリング
df = df[df['avg_fastball_speed'] > 0]

# NaN（データがない場合）を削除 (フィルタリング後にもNaNが発生する可能性があるため)
df.dropna(subset=required_columns, inplace=True)

print("\n--- DataFrame Info (After Filter) ---")
print(df.info())

print("\n--- DataFrame Head (After Filter) ---")
print(df.head())

print("\n--- Basic Statistics (After Filter) ---")
print(df[required_columns].describe())

# --- グラフ1: 最高球速 vs 平均速球球速 (散布図) ---
plt.figure(figsize=(10, 8))
sns.scatterplot(data=df, x='avg_fastball_speed', y='max_speed', alpha=0.7)
plt.title('2025 MLB Season: Max Speed vs Avg Fastball Speed\n(Only Pitchers with Avg Fastball Speed > 0 mph)')
plt.xlabel('Average Fastball Speed (mph)')
plt.ylabel('Max Speed (mph)')
plt.grid(True, linestyle='--', alpha=0.6)
plt.tight_layout()
plt.show()

# --- グラフ2: 最高球速の上位10人 ---
top_max = df.nlargest(10, 'max_speed')
plt.figure(figsize=(12, 6))
sns.barplot(data=top_max.reset_index(), x='Pitcher', y='max_speed', palette='viridis')
plt.title('2025 MLB Season: Top 10 Max Speeds\n(Only Pitchers with Avg Fastball Speed > 0 mph)')
plt.xlabel('Pitcher')
plt.ylabel('Max Speed (mph)')
plt.xticks(rotation=45, ha="right") # 選手名が長いため回転させる
plt.tight_layout()
plt.show()

# --- グラフ3: 平均速球球速の上位10人 ---
top_avg = df.nlargest(10, 'avg_fastball_speed')
plt.figure(figsize=(12, 6))
sns.barplot(data=top_avg.reset_index(), x='Pitcher', y='avg_fastball_speed', palette='plasma')
plt.title('2025 MLB Season: Top 10 Average Fastball Speeds\n(Only Pitchers with Avg Fastball Speed > 0 mph)')
plt.xlabel('Pitcher')
plt.ylabel('Average Fastball Speed (mph)')
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.show()

# --- グラフ4: 最高球速のヒストグラム ---
plt.figure(figsize=(10, 6))
sns.histplot(data=df, x='max_speed', bins=20, kde=True)
plt.title('Distribution of Max Speeds (2025 Season)\n(Only Pitchers with Avg Fastball Speed > 0 mph)')
plt.xlabel('Max Speed (mph)')
plt.ylabel('Number of Pitchers')
plt.tight_layout()
plt.show()

# --- グラフ5: 平均速球球速のヒストグラム ---
plt.figure(figsize=(10, 6))
sns.histplot(data=df, x='avg_fastball_speed', bins=20, kde=True)
plt.title('Distribution of Average Fastball Speeds (2025 Season)\n(Only Pitchers with Avg Fastball Speed > 0 mph)')
plt.xlabel('Average Fastball Speed (mph)')
plt.ylabel('Number of Pitchers')
plt.tight_layout()
plt.show()

# --- その他の統計 ---
print("\n--- Pitchers with Max Speed >= 100 mph (Filtered) ---")
print(df[df['max_speed'] >= 100][required_columns])

print("\n--- Pitchers with Avg Fastball Speed >= 95 mph (Filtered) ---")
print(df[df['avg_fastball_speed'] >= 95][required_columns])

print("\n--- Correlation between Max Speed and Avg Fastball Speed (Filtered) ---")
correlation = df['max_speed'].corr(df['avg_fastball_speed'])
print(f"Correlation coefficient: {correlation:.3f}")