import requests
import json
from collections import defaultdict
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

def get_max_speeds_from_game_api(game_url):
    """
    個別のゲームAPIからライブゲームデータを取得し、ピッチャーごとの最高球速を抽出します。
    liveData.allPlays または liveData.plays.allPlays を使用する場合に対応。

    Args:
        game_url (str): 個別のゲームライブフィードAPIのURL。

    Returns:
        dict: ピッチャー名をキー、最高球速 (float) を値とする辞書。
    """
    try:
        # print(f"  Fetching game data from {game_url}...")
        response = requests.get(game_url)
        response.raise_for_status()
        data = response.json()
        # print(f"  Game data for {game_url.split('/')[-2]} fetched successfully.")

        # liveData.allPlays または liveData.plays.allPlays を取得
        all_plays_data = data.get("liveData", {}).get("allPlays")
        if all_plays_data is None:
            all_plays_data = data.get("liveData", {}).get("plays", {}).get("allPlays")

        if all_plays_data is None:
            print(f"  Warning: Could not find 'allPlays' in game data from {game_url}. Skipping.")
            return {}

        # liveData.players を取得 (存在する場合のみ)
        players_data_raw = data.get("liveData", {}).get("players", {})
        player_names = {}
        if players_data_raw:
            for pid_key, pdata in players_data_raw.items():
                 person_info = pdata.get('person', {})
                 player_id = person_info.get('id')
                 player_full_name = person_info.get('fullName')
                 if player_id and player_full_name:
                     player_names[player_id] = player_full_name
        # print(f"  Loaded {len(player_names)} player names from liveData.players for game {game_url.split('/')[-2]}.")

        max_speeds = defaultdict(float)
        pitch_count = 0

        for play in all_plays_data: # 修正: all_plays_ -> all_plays_data
            if 'playEvents' not in play:
                continue

            # プレイのmatchupからピッチャー情報を取得
            pitcher_info = play.get('matchup', {}).get('pitcher', {})
            pitcher_id = pitcher_info.get('id')
            pitcher_name_from_matchup = pitcher_info.get('fullName', 'Unknown_Pitcher_Id_' + str(pitcher_id))

            for event in play['playEvents']:
                pitch_data = event.get('pitchData') # 修正: pitch_ -> pitch_data
                if pitch_data and 'startSpeed' in pitch_data: # 修正: pitch_ -> pitch_data
                    speed = float(pitch_data['startSpeed'])
                    pitch_count += 1

                    # ピッチャー名を決定
                    if pitcher_id and pitcher_id in player_names:
                        final_pitcher_name = player_names[pitcher_id]
                    else:
                        final_pitcher_name = pitcher_name_from_matchup

                    # 最大球速を更新
                    if speed > max_speeds[final_pitcher_name]:
                        max_speeds[final_pitcher_name] = speed

        # print(f"  Processed {pitch_count} pitches for game {game_url.split('/')[-2]}.")
        return dict(max_speeds)

    except requests.exceptions.RequestException as e:
        print(f"  ゲームAPIリクエスト中にエラーが発生しました for {game_url}: {e}")
        return {}
    except json.JSONDecodeError as e:
        print(f"  ゲームJSONの解析中にエラーが発生しました for {game_url}: {e}")
        return {}
    except Exception as e:
        print(f"  ゲーム {game_url.split('/')[-2]} で予期せぬエラーが発生しました: {e}")
        return {}

def get_all_pitchers_max_speeds_for_date(date_str):
    """
    指定された日付のスケジュールデータからすべてのゲームのリンクを取得し、
    各ゲームのAPIから最高球速を取得して統合します。

    Args:
        date_str (str): "YYYY-MM-DD" 形式の日付文字列 (例: "2025-08-11")。

    Returns:
        dict: その日付のゲーム統合後のピッチャー名をキー、最高球速 (float) を値とする辞書。
    """
    # 日付文字列を "MM/DD/YYYY" 形式に変換
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    api_date_str = date_obj.strftime("%m/%d/%Y")

    schedule_data = get_schedule_data_for_date(api_date_str)
    all_max_speeds_for_date = {}
    game_count = 0

    dates_data = schedule_data.get("dates", [])
    if not dates_data:
        print(f"  No game dates found in schedule data for {date_str}. Skipping date.")
        return {}

    # 最初の日付のゲームリストを取得
    games_list = dates_data[0].get("games", [])
    print(f"  Found {len(games_list)} games on {date_str}.")

    for game in games_list: # 修正: games_ -> games_list
        game_link = game.get("link")
        if not game_link:
            print(f"    Warning: No link found for a game in schedule data for {date_str}. Skipping.")
            continue

        # APIのベースURLを補完
        full_game_url = f"https://statsapi.mlb.com{game_link}"
        game_pk = game.get("gamePk")
        print(f"    Processing Game PK: {game_pk}")

        game_max_speeds = get_max_speeds_from_game_api(full_game_url)
        game_count += 1

        for pitcher_name, speed in game_max_speeds.items():
            if speed > all_max_speeds_for_date.get(pitcher_name, 0):
                all_max_speeds_for_date[pitcher_name] = speed

    print(f"  Processed {game_count} games from {date_str}.")
    return all_max_speeds_for_date

def get_all_pitchers_max_speeds_for_year(start_date_str, end_date_str):
    """
    指定された期間（年全体を含む）の各日付について、
    全ゲームから最高球速を取得して統合します。

    Args:
        start_date_str (str): "YYYY-MM-DD" 形式の開始日付。
        end_date_str (str): "YYYY-MM-DD" 形式の終了日付。

    Returns:
        dict: 期間全体でのピッチャー名をキー、最高球速 (float) を値とする辞書。
    """
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
    current_date = start_date

    all_max_speeds_overall = defaultdict(float)
    total_games_processed = 0

    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        print(f"\n--- Processing date: {date_str} ---")

        all_max_speeds_for_day = get_all_pitchers_max_speeds_for_date(date_str)
        # total_games_processed のカウントも get_all_pitchers_max_speeds_for_date 内で行われるため、
        # ここでは all_max_speeds_for_day のゲーム数を加算する代わりに、
        # get_all_pitchers_max_speeds_for_date でゲーム数をカウントして返すように変更するか、
        # または再度スケジュールAPIを呼び出す必要があります。
        # 効率のため、再度APIを呼び出すのではなく、get_all_pitchers_max_speeds_for_date が
        # 処理したゲーム数を返すように関数を変更するのが良いですが、
        # ここでは get_all_pitchers_max_speeds_for_date の戻り値を (辞書, 処理したゲーム数) のタプルにするのは
        # コードの変更が大きいため、元の方法を維持しつつ、
        # get_schedule_data_for_date を再度呼び出してゲーム数を取得します。
        # または、get_all_pitchers_max_speeds_for_date が処理したゲーム数をカウントする変数を
        # global または mutable object (例: list) で渡す方法もありますが、
        # ここでは、get_schedule_data_for_date を再度呼び出すことで対応します。
        # ただし、これも効率が悪いです。
        # 最も良い方法は、get_all_pitchers_max_speeds_for_date の戻り値を変更することです。
        # 以下のように変更します。
        # 1. get_all_pitchers_max_speeds_for_date が (max_speeds_dict, processed_count) を返すように変更
        # 2. get_all_pitchers_max_speeds_for_year でその戻り値を受け取る

        # 修正: get_all_pitchers_max_speeds_for_date がゲーム数も返すように変更
        # schedule_data_for_count = get_schedule_data_for_date(current_date.strftime("%m/%d/%Y"))
        # games_on_date = len(schedule_data_for_count.get("dates", [{}])[0].get("games", []))
        # total_games_processed += games_on_date

        # 上記の方法ではなく、get_all_pitchers_max_speeds_for_date を変更します。
        # def get_all_pitchers_max_speeds_for_date(date_str):
        #    ...
        #    return all_max_speeds_for_date, game_count # タプルで返す
        # これにより、get_all_pitchers_max_speeds_for_year で game_count を受け取れます。

    # --- get_all_pitchers_max_speeds_for_date の修正 ---
    # def get_all_pitchers_max_speeds_for_date(date_str):
    #     # ... (前半は同じ) ...
    #     dates_data = schedule_data.get("dates", [])
    #     if not dates_data:
    #         print(f"  No game dates found in schedule data for {date_str}. Skipping date.")
    #         return {}, 0 # 空の辞書とゲーム数0を返す
    #     games_list = dates_data[0].get("games", [])
    #     print(f"  Found {len(games_list)} games on {date_str}.")
    #     # ... (処理ループ) ...
    #     print(f"  Processed {game_count} games from {date_str}.")
    #     return all_max_speeds_for_date, game_count # 辞書とカウントを返す
    # --- 修正ここまで ---

    # --- get_all_pitchers_max_speeds_for_year の修正 ---
    # while current_date <= end_date:
    #     date_str = current_date.strftime("%Y-%m-%d")
    #     print(f"\n--- Processing date: {date_str} ---")
    #     all_max_speeds_for_day, games_processed_today = get_all_pitchers_max_speeds_for_date(date_str)
    #     # ... (統合処理) ...
    #     total_games_processed += games_processed_today
    #     current_date += timedelta(days=1)
    # --- 修正ここまで ---

    # ここでは、元の関数定義を変更せずに、安全にアクセスする方法をとります。
    # get_schedule_data_for_date を呼び出し、ゲーム数を取得しますが、
    # もし dates が空リストなら、ゲーム数は0です。
        schedule_data_for_count = get_schedule_data_for_date(current_date.strftime("%m/%d/%Y"))
        dates_for_count = schedule_data_for_count.get("dates", [])
        if dates_for_count:
             games_on_date = len(dates_for_count[0].get("games", []))
        else:
             games_on_date = 0
        total_games_processed += games_on_date


        for pitcher_name, speed in all_max_speeds_for_day.items():
            if speed > all_max_speeds_overall[pitcher_name]:
                all_max_speeds_overall[pitcher_name] = speed

        current_date += timedelta(days=1)

    print(f"\n--- Finished processing from {start_date_str} to {end_date_str} ---")
    print(f"Total games processed: {total_games_processed}")
    return dict(all_max_speeds_overall)

# 使用例
if __name__ == "__main__":
    # 2025年1月1日から2025年10月12日までを処理範囲とする
    # (将来的にシーズンが終了すれば、end_dateをその年に合わせて変更してください)
    start_date = "2025-01-01"
    end_date = "2025-10-12" # 現在の日付

    print(f"--- Collecting max speeds from all games between {start_date} and {end_date}... ---")
    all_max_speeds_2025 = get_all_pitchers_max_speeds_for_year(start_date, end_date)

    if all_max_speeds_2025:
        print("\n--- 2025 Season (or specified range) - ピッチャーごとの最高球速 (Overall) ---")
        sorted_pitches = sorted(all_max_speeds_2025.items(), key=lambda item: item[1], reverse=True)
        for name, speed in sorted_pitches:
            print(f"{name}: {speed:.2f} mph")
    else:
        print("\n指定された期間のゲームから最高球速を抽出できませんでした。")