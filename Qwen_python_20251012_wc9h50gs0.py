import json
import os
from collections import defaultdict
import glob

# 速球系のコードを定義 (必要に応じて追加/変更)
FASTBALL_CODES = {"FF", "FT", "SI", "FC"}

def extract_max_and_avg_fastball_speeds_from_file(file_path):
    """
    個別のゲームJSONファイルからピッチャーごとの最高球速と速球平均球速を抽出します。

    Args:
        file_path (str): ゲームデータのJSONファイルパス。

    Returns:
        tuple: (max_speeds_dict, avg_fastball_speeds_dict)
               両方ともピッチャー名をキー、速度 (float) を値とする辞書。
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = f.read()

        try:
            game_data = json.loads(data)
        except json.JSONDecodeError:
            print(f"ファイル全体が有効なJSONではありません。抽出を試みます: {file_path}")
            # 必要に応じて、JSONの一部を抽出する処理をここに追加します。
            # 今回のファイルは、`liveData.plays` または `liveData.allPlays` を持つ完全な構造のはず。
            # よって、`json.loads(data)` が通常成功するはずです。
            # 失敗する場合、ファイルが破損しているか、想定外の形式です。
            # ここでは、エラーを出力してスキップします。
            return {}, {}

        # liveData.allPlays または liveData.plays.allPlays を取得
        all_plays_data = game_data.get("liveData", {}).get("allPlays")
        if all_plays_data is None:
            all_plays_data = game_data.get("liveData", {}).get("plays", {}).get("allPlays")

        if all_plays_data is None:
            print(f"  Warning: Could not find 'allPlays' in game data from {file_path}. Skipping.")
            return {}, {}

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

        # 投手ごとの最高球速を記録する辞書
        max_speeds = defaultdict(float)
        # 投手ごとの速球球速リストを記録する辞書
        fastball_speeds_dict = defaultdict(list)

        for play in all_plays_data: # 修正: all_plays_data に変更
            if 'playEvents' not in play:
                continue

            # プレイのmatchupからピッチャー情報を取得
            pitcher_info = play.get('matchup', {}).get('pitcher', {})
            pitcher_id = pitcher_info.get('id')
            pitcher_name_from_matchup = pitcher_info.get('fullName', 'Unknown_Pitcher_Id_' + str(pitcher_id))

            for event in play['playEvents']:
                pitch_data = event.get('pitchData')
                details = event.get('details')
                # pitchData と startSpeed と details と type が存在するか確認
                if pitch_data and 'startSpeed' in pitch_data and details and 'type' in details:
                    speed = float(pitch_data['startSpeed'])
                    pitch_code = details['type'].get('code')

                    # ピッチャー名を決定
                    if pitcher_id and pitcher_id in player_names:
                        final_pitcher_name = player_names[pitcher_id]
                    else:
                        final_pitcher_name = pitcher_name_from_matchup

                    # 最大球速を更新
                    if speed > max_speeds[final_pitcher_name]:
                        max_speeds[final_pitcher_name] = speed

                    # 速球系ピッチの場合は、平均計算用リストに追加
                    if pitch_code in FASTBALL_CODES:
                        fastball_speeds_dict[final_pitcher_name].append(speed)

        # 平均速球球速を計算 (速球リストが空でない場合)
        avg_fastball_speeds = {}
        for pitcher_name, speeds in fastball_speeds_dict.items():
            if speeds: # リストが空でなければ
                avg_fastball_speeds[pitcher_name] = sum(speeds) / len(speeds)

        return dict(max_speeds), avg_fastball_speeds

    except FileNotFoundError:
        print(f"ファイルが見つかりません: {file_path}")
        return {}, {}
    except json.JSONDecodeError as e:
        print(f"JSONの解析中にエラーが発生しました for {file_path}: {e}")
        return {}, {}
    except Exception as e:
        print(f"ファイル {file_path} の処理中に予期せぬエラーが発生しました: {e}")
        return {}, {}

def aggregate_max_and_avg_speeds_from_directory(directory_path):
    """
    指定されたディレクトリ内のすべてのゲームJSONファイルから
    投手別の最高球速と平均速球球速を統合して返します。

    Args:
        directory_path (str): ゲームデータJSONファイルが保存されているディレクトリパス。

    Returns:
        tuple: (all_max_speeds_dict, all_avg_fastball_speeds_dict)
               両方ともピッチャー名をキー、速度 (float) を値とする辞書。
    """
    all_max_speeds = defaultdict(float)
    all_avg_fastball_speeds = defaultdict(list) # 各選手の平均速球球速リスト（平均の平均を取るため）
    json_files = glob.glob(os.path.join(directory_path, "*.json"))
    total_files = len(json_files)
    processed_files = 0

    print(f"Found {total_files} JSON files in {directory_path}")

    for file_path in json_files:
        print(f"Processing file: {os.path.basename(file_path)}")
        game_max_speeds, game_avg_fastball_speeds = extract_max_and_avg_fastball_speeds_from_file(file_path)
        processed_files += 1

        # 最高球速の更新
        for pitcher_name, speed in game_max_speeds.items():
            if speed > all_max_speeds[pitcher_name]:
                all_max_speeds[pitcher_name] = speed

        # 平均速球球速の統合 (各ゲームでの平均をリストに追加)
        for pitcher_name, avg_speed in game_avg_fastball_speeds.items():
            all_avg_fastball_speeds[pitcher_name].append(avg_speed)

        if processed_files % 100 == 0: # 進行状況を100ファイルごとに表示
            print(f"  Processed {processed_files} / {total_files} files...")

    print(f"Finished processing all {total_files} files.")

    # 平均速球球速の最終計算: 各選手のゲームごとの平均の平均
    final_avg_fastball_speeds = {}
    for pitcher_name, avg_speeds_list in all_avg_fastball_speeds.items():
        if avg_speeds_list: # リストが空でなければ
            final_avg_fastball_speeds[pitcher_name] = sum(avg_speeds_list) / len(avg_speeds_list)

    return dict(all_max_speeds), final_avg_fastball_speeds

def save_combined_speeds_to_json(max_speeds_dict, avg_speeds_dict, output_file_path):
    """
    最高球速辞書と平均速球球速辞書を統合し、JSONファイルとして保存します。

    Args:
        max_speeds_dict (dict): 投手名をキー、最高球速を値とする辞書。
        avg_speeds_dict (dict): 投手名をキー、平均速球球速を値とする辞書。
        output_file_path (str): 保存先のJSONファイルパス。
    """
    try:
        # 両方の辞書を統合
        combined_dict = {}
        all_pitchers = set(max_speeds_dict.keys()).union(set(avg_speeds_dict.keys()))

        for pitcher_name in all_pitchers:
            combined_dict[pitcher_name] = {
                "max_speed": max_speeds_dict.get(pitcher_name, 0.0),
                "avg_fastball_speed": avg_speeds_dict.get(pitcher_name, 0.0)
            }

        # 球速が高い順に並べ替え (max_speed を基準に)
        sorted_combined_dict = dict(sorted(combined_dict.items(), key=lambda item: item[1]['max_speed'], reverse=True))

        with open(output_file_path, 'w', encoding='utf-8') as f:
            json.dump(sorted_combined_dict, f, ensure_ascii=False, indent=2)
        print(f"Combined speeds (max & avg fastball) successfully saved to {output_file_path}")
    except Exception as e:
        print(f"Error saving combined speeds to {output_file_path}: {e}")

# 使用例
if __name__ == "__main__":
    input_directory = r"E:\work\mlb\mlb_2025_data" # r'' はバックスラッシュをエスケープしないようにする
    output_file = r"E:\work\mlb\mlb_2025_pitcher_max_and_avg_fastball_speeds.json"

    print(f"--- Aggregating max speeds and avg fastball speeds from {input_directory} ---")
    all_max_speeds_2025, all_avg_fastball_speeds_2025 = aggregate_max_and_avg_speeds_from_directory(input_directory)

    if all_max_speeds_2025 or all_avg_fastball_speeds_2025: # どちらかの辞書にデータがあればOK
        print("\n--- Sorting and combining results ---")
        print(f"Found max speeds for {len(all_max_speeds_2025)} pitchers.")
        print(f"Found avg fastball speeds for {len(all_avg_fastball_speeds_2025)} pitchers.")

        print(f"\n--- Saving combined results to {output_file} ---")
        save_combined_speeds_to_json(all_max_speeds_2025, all_avg_fastball_speeds_2025, output_file)

        # 結果の上位をコンソールにも表示 (オプション)
        print("\n--- Top 10 Combined Results (sorted by max speed) ---")
        sorted_items = sorted(
            {k: v for k, v in all_max_speeds_2025.items()}.items(),
            key=lambda item: item[1],
            reverse=True
        )
        count = 0
        for name, max_speed in sorted_items:
            if count >= 10:
                break
            avg_speed = all_avg_fastball_speeds_2025.get(name, 0.0)
            print(f"{name}: Max Speed = {max_speed:.2f} mph, Avg Fastball Speed = {avg_speed:.2f} mph")
            count += 1

    else:
        print("\nディレクトリ内のファイルから最高球速または平均速球球速を抽出できませんでした。")
