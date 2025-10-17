import json
import os
from collections import defaultdict
import glob

def extract_max_speeds_from_file(file_path):
    """
    個別のゲームJSONファイルからピッチャーごとの最高球速を抽出します。

    Args:
        file_path (str): ゲームデータのJSONファイルパス。

    Returns:
        dict: ピッチャー名をキー、最高球速 (float) を値とする辞書。
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = f.read()

        # 生のテキストからJSON部分を抽出する
        # 与えられたファイルの内容は、JSONの一部である可能性があります。
        # まずは、ファイル全体をJSONとして解析を試みます。
        try:
            game_data = json.loads(data)
        except json.JSONDecodeError:
            print(f"ファイル全体が有効なJSONではありません。抽出を試みます: {file_path}")
            # 必要に応じて、JSONの一部を抽出する処理をここに追加します。
            # 例: { "liveData": { ... } } のような部分を正規表現で探す。
            # 今回のファイルは、`liveData.plays` または `liveData.allPlays` を持つ完全な構造のはず。
            # しかし、Pasted_Text_1760250288585.txt は断片的なもの。
            # 実際に保存されたファイルは `{"liveData": {...}}` のような完全な構造。
            # よって、`json.loads(data)` が通常成功するはずです。
            # 失敗する場合、ファイルが破損しているか、想定外の形式です。
            # ここでは、エラーを出力してスキップします。
            return {}

        # liveData.allPlays または liveData.plays.allPlays を取得
        all_plays_data = game_data.get("liveData", {}).get("allPlays")
        if all_plays_data is None:
            all_plays_data = game_data.get("liveData", {}).get("plays", {}).get("allPlays")

        if all_plays_data is None:
            print(f"  Warning: Could not find 'allPlays' in game data from {file_path}. Skipping.")
            return {}

        # liveData.players を取得 (存在する場合のみ)
        players_data_raw = game_data.get("liveData", {}).get("players", {})
        player_names = {}
        if players_data_raw:
            for pid_key, pdata in players_data_raw.items():
                 person_info = pdata.get('person', {})
                 player_id = person_info.get('id')
                 player_full_name = person_info.get('fullName')
                 if player_id and player_full_name:
                     player_names[player_id] = player_full_name

        max_speeds = defaultdict(float)

        # 修正: all_plays_data に変更 & コロン追加
        for play in all_plays_data:
            if 'playEvents' not in play:
                continue

            # プレイのmatchupからピッチャー情報を取得
            pitcher_info = play.get('matchup', {}).get('pitcher', {})
            pitcher_id = pitcher_info.get('id')
            pitcher_name_from_matchup = pitcher_info.get('fullName', 'Unknown_Pitcher_Id_' + str(pitcher_id))

            for event in play['playEvents']:
                # 修正: pitch_data に変更 & コロン追加
                pitch_data = event.get('pitchData')
                if pitch_data and 'startSpeed' in pitch_data: # 修正: pitch_ -> pitch_data
                    speed = float(pitch_data['startSpeed'])

                    # ピッチャー名を決定
                    if pitcher_id and pitcher_id in player_names:
                        final_pitcher_name = player_names[pitcher_id]
                    else:
                        final_pitcher_name = pitcher_name_from_matchup

                    # 最大球速を更新
                    if speed > max_speeds[final_pitcher_name]:
                        max_speeds[final_pitcher_name] = speed

        return dict(max_speeds)

    except FileNotFoundError:
        print(f"ファイルが見つかりません: {file_path}")
        return {}
    except json.JSONDecodeError as e:
        print(f"JSONの解析中にエラーが発生しました for {file_path}: {e}")
        return {}
    except Exception as e:
        print(f"ファイル {file_path} の処理中に予期せぬエラーが発生しました: {e}")
        return {}

def aggregate_max_speeds_from_directory(directory_path):
    """
    指定されたディレクトリ内のすべてのゲームJSONファイルから
    投手別の最高球速を統合して返します。

    Args:
        directory_path (str): ゲームデータJSONファイルが保存されているディレクトリパス。

    Returns:
        dict: 投手名をキー、2025年通算最高球速 (float) を値とする辞書。
    """
    all_max_speeds = defaultdict(float)
    json_files = glob.glob(os.path.join(directory_path, "*.json"))
    total_files = len(json_files)
    processed_files = 0

    print(f"Found {total_files} JSON files in {directory_path}")

    for file_path in json_files:
        print(f"Processing file: {os.path.basename(file_path)}")
        game_max_speeds = extract_max_speeds_from_file(file_path)
        processed_files += 1

        for pitcher_name, speed in game_max_speeds.items():
            if speed > all_max_speeds[pitcher_name]:
                all_max_speeds[pitcher_name] = speed

        if processed_files % 100 == 0: # 進行状況を100ファイルごとに表示
            print(f"  Processed {processed_files} / {total_files} files...")

    print(f"Finished processing all {total_files} files.")
    return dict(all_max_speeds)

def save_max_speeds_to_json(max_speeds_dict, output_file_path):
    """
    投手別の最高球速辞書をJSONファイルとして保存します。

    Args:
        max_speeds_dict (dict): 投手名をキー、最高球速を値とする辞書。
        output_file_path (str): 保存先のJSONファイルパス。
    """
    try:
        with open(output_file_path, 'w', encoding='utf-8') as f:
            json.dump(max_speeds_dict, f, ensure_ascii=False, indent=2)
        print(f"Max speeds successfully saved to {output_file_path}")
    except Exception as e:
        print(f"Error saving max speeds to {output_file_path}: {e}")

# 使用例
if __name__ == "__main__":
    input_directory = r"E:\work\mlb\mlb_2025_data" # r'' はバックスラッシュをエスケープしないようにする
    output_file = r"E:\work\mlb\mlb_2025_pitcher_max_speeds.json"

    print(f"--- Aggregating max speeds from {input_directory} ---")
    all_max_speeds_2025 = aggregate_max_speeds_from_directory(input_directory)

    if all_max_speeds_2025:
        print("\n--- Sorting results ---")
        # 球速が高い順に並べ替え
        sorted_max_speeds = dict(sorted(all_max_speeds_2025.items(), key=lambda item: item[1], reverse=True))
        print(f"Found max speeds for {len(sorted_max_speeds)} pitchers.")

        print(f"\n--- Saving results to {output_file} ---")
        save_max_speeds_to_json(sorted_max_speeds, output_file)

        # 結果の上位をコンソールにも表示 (オプション)
        print("\n--- Top 10 Max Speeds (2025) ---")
        for i, (name, speed) in enumerate(sorted_max_speeds.items()):
            if i >= 10:
                break
            print(f"{name}: {speed:.2f} mph")

    else:
        print("\nディレクトリ内のファイルから最高球速を抽出できませんでした。")
