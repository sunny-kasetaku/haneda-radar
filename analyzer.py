from datetime import datetime, timedelta, timezone

# 日本時間(JST)の定義
JST = timezone(timedelta(hours=9))

def analyze_demand(processed_flights):
    """
    精査されたフライトリストから、5つの乗り場別の1時間後需要を計算する
    """
    # 💡 修正ポイント：現在時刻に「日本時間」のラベルを貼る
    now = datetime.now(JST)
    one_hour_later = now + timedelta(hours=1)
    
    stands = {
        "1号 (T1/JAL系)": 0,
        "2号 (T2/ANA系)": 0,
        "3号 (T3/国際)": 0,
        "4号 (T2/国際)": 0,
        "国際 (T3/全体)": 0
    }

    for flight in processed_flights:
        try:
            # 💡 修正ポイント：APIの時刻を読み込む際、タイムゾーンを正しく処理する
            # ISO形式を解析し、もしUTCならJSTに変換する
            dt_str = flight['arrival_time'].replace('Z', '+00:00')
            arrival_time = datetime.fromisoformat(dt_str).astimezone(JST)
        except Exception as e:
            continue

        demand_start = arrival_time + timedelta(minutes=30)
        demand_end = arrival_time + timedelta(minutes=60)

        # これで「ラベル付き」同士の比較になるのでエラーが出ません
        if not (demand_end < now or demand_start > one_hour_later):
            stand_key = determine_stand(flight)
            if stand_key:
                stands[stand_key] += 20
                if stand_key == "3号 (T3/国際)":
                    stands["国際 (T3/全体)"] += 20

    return stands

def determine_stand(flight):
    # (ここは変更なしでOKです)
    iata = flight.get('flight_iata', "") or ""
    terminal = str(flight.get('terminal', ""))
    
    if any(iata.startswith(prefix) for prefix in ["JL", "NU", "BC", "7G"]):
        return "1号 (T1/JAL系)"
    if any(iata.startswith(prefix) for prefix in ["NH", "HD", "ADO", "6J"]):
        if terminal == "3": return "3号 (T3/国際)"
        return "2号 (T2/ANA系)"
    if terminal == "3": return "3号 (T3/国際)"
    if terminal == "2": return "4号 (T2/国際)"
    return "国際 (T3/全体)"