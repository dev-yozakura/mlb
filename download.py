import requests
import json
import os
from datetime import datetime, timedelta

def get_schedule_data_for_date(date_str, sport_id=1):
    """
    指定された日付のゲームスケジュール情報を取得します。

    Args:
        date_str (str): "MM/DD/YYYY" 形式の日付文字列 (例: "08/11/2025")。
        sport_id (int): MLBの場合は1。

    Returns:
        dict: APIから取得したスケジュールデータ。
    """
    # APIの日付フォーマットは "MM/DD/YYYY"
    schedule_url = f"https://statsapi.mlb.com/api/v1/schedule/games/?sportId={sport_id}&date={date_str}"
    try:
        # print(f"Fetching schedule data for date {date_str} from {schedule_url}...")
        response = requests.get(schedule_url)
        response.raise_for_status()
        data = response.json()
        # print(f"Schedule data for {date_str} fetched successfully.")
        return data
    except requests.exceptions.RequestException as e:
        print(f"  スケジュールAPIリクエスト中にエラーが発生しました for {date_str}: {e}")
        return {}
    except json.JSONDecodeError as e:
        print(f"  スケジュールJSONの解析中にエラーが発生しました for {date_str}: {e}")
        return {}

def download_game_data(game_pk, output_dir="mlb_2025_data"):
    """
    個別のゲームAPIからデータを取得し、JSONファイルとして保存します。

    Args:
        game_pk (int): ゲームのID。
        output_dir (str): ファイルを保存するディレクトリ。

    Returns:
        bool: 成功したかどうか。
    """
    game_url = f"https://statsapi.mlb.com/api/v1.1/game/{game_pk}/feed/live"
    file_path = os.path.join(output_dir, f"game_{game_pk}.json")

    # 既にファイルが存在する場合はスキップ
    if os.path.exists(file_path):
        print(f"  Game {game_pk} already exists at {file_path}. Skipping.")
        return True

    try:
        print(f"  Fetching data for game {game_pk}...")
        response = requests.get(game_url)
        response.raise_for_status()
        data = response.json()

        # ディレクトリがなければ作成
        os.makedirs(output_dir, exist_ok=True)

        # JSONファイルとして保存
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"  Game {game_pk} data saved to {file_path}")
        return True

    except requests.exceptions.RequestException as e:
        print(f"  ゲームAPIリクエスト中にエラーが発生しました for {game_pk}: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"  ゲームJSONの解析中にエラーが発生しました for {game_pk}: {e}")
        return False
    except Exception as e:
        print(f"  ゲーム {game_pk} で予期せぬエラーが発生しました: {e}")
        return False

def download_all_games_for_year(start_date_str, end_date_str, output_dir="mlb_2025_data"):
    """
    指定された期間の各日付について、全ゲームのデータをダウンロードします。

    Args:
        start_date_str (str): "YYYY-MM-DD" 形式の開始日付。
        end_date_str (str): "YYYY-MM-DD" 形式の終了日付。
        output_dir (str): ファイルを保存するディレクトリ。
    """
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
    current_date = start_date

    total_games_processed = 0
    total_games_skipped = 0
    total_games_failed = 0

    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        api_date_str = current_date.strftime("%m/%d/%Y")
        print(f"\n--- Processing date: {date_str} (API: {api_date_str}) ---")

        schedule_data = get_schedule_data_for_date(api_date_str)
        dates_data = schedule_data.get("dates", [])

        if not dates_data:
            print(f"  No game dates found in schedule data for {date_str}. Skipping date.")
            current_date += timedelta(days=1)
            continue

        games_list = dates_data[0].get("games", [])
        print(f"  Found {len(games_list)} games on {date_str}.")

        for game in games_list:
            game_pk = game.get("gamePk")
            if not game_pk:
                print(f"    Warning: No gamePk found for a game in schedule data for {date_str}. Skipping.")
                continue

            print(f"    Attempting to download Game PK: {game_pk}")
            success = download_game_data(game_pk, output_dir)

            if success:
                # ファイルが既に存在してスキップされた場合も、processedとしてカウント
                if os.path.exists(os.path.join(output_dir, f"game_{game_pk}.json")):
                    total_games_skipped += 1
                else:
                    total_games_processed += 1
            else:
                total_games_failed += 1

        current_date += timedelta(days=1)

    print(f"\n--- Finished processing from {start_date_str} to {end_date_str} ---")
    print(f"Total games processed (newly downloaded): {total_games_processed}")
    print(f"Total games skipped (already existed): {total_games_skipped}")
    print(f"Total games failed: {total_games_failed}")

# 使用例
if __name__ == "__main__":
    # 保存先ディレクトリ
    output_directory = "mlb_2025_data"

    # 2025年1月1日から2025年10月12日までを処理範囲とする
    start_date = "2025-07-01"
    end_date = "2025-09-30" # 現在の日付

    print(f"--- Downloading all game data between {start_date} and {end_date} to '{output_directory}'... ---")
    download_all_games_for_year(start_date, end_date, output_directory)

    print("\nDownload process completed.")