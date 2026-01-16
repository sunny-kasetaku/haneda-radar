from datetime import datetime, timedelta, timezone

JST = timezone(timedelta(hours=9))

def analyze_demand(processed_flights):
    now = datetime.now(JST)
    # 分析範囲を「今から1時間15分後まで」に少し広げ、
    # 乗り場に向かっている途中の客を漏らさずカウントします
    one_hour_later = now + timedelta(minutes=75)
    
    stands = {
        "1号 (T1/JAL系)": 0, "2号 (T2/ANA系)": 0, 
        "3号 (T3/国際)": 0, "4号 (T2/国際)": 0, "国際 (T3/全体)": 0
    }

    for flight in processed_flights:
        arrival_time = datetime.fromisoformat(flight['arrival_time'])

        # 需要発生：着陸から30分後 〜 75分後
        demand_start = arrival_time + timedelta(minutes=30)
        demand_end = arrival_time + timedelta(minutes=75)

        # 今の1時間枠と、需要時間が重なっているか
        if not (demand_end < now or demand_start > one_hour_later):
            stand_key = determine_stand(flight)
            if stand_key:
                # 深夜便は1便あたりの期待値を少し高め（30人）に設定
                stands[stand_key] += 30
                if stand_key == "3号 (T3/国際)":
                    stands["国際 (T3/全体)"] += 30

    return stands

def determine_stand(flight):
    iata = (flight.get('flight_iata') or "").upper()
    terminal = str(flight.get('terminal'))
    
    # ターミナル情報がある場合は最優先
    if terminal == "1": return "1号 (T1/JAL系)"
    if terminal == "3": return "3号 (T3/国際)"
    if terminal == "2":
        # 第2ターミナルでANA以外なら「4号(国際)」の可能性が高い
        if not any(iata.startswith(p) for p in ["NH", "HD", "6J"]):
            return "4号 (T2/国際)"
        return "2号 (T2/ANA系)"

    # ターミナルがない場合の便名判定
    if any(iata.startswith(p) for p in ["JL", "NU", "BC", "7G"]): return "1号 (T1/JAL系)"
    if any(iata.startswith(p) for p in ["NH", "HD", "6J"]): return "2号 (T2/ANA系)"
    
    return "3号 (T3/国際)" # 不明分は一旦3号へ