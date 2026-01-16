from datetime import datetime, timedelta

def analyze_demand(processed_flights):
    """
    精査されたフライトリストから、5つの乗り場別の1時間後需要を計算する
    """
    now = datetime.now()
    one_hour_later = now + timedelta(hours=1)
    
    # 5つの乗り場（バケツ）を準備
    stands = {
        "1号 (T1/JAL系)": 0,
        "2号 (T2/ANA系)": 0,
        "3号 (T3/国際)": 0,
        "4号 (T2/国際)": 0,
        "国際 (T3/全体)": 0
    }

    for flight in processed_flights:
        # 1. 到着時刻の解析
        try:
            arrival_time = datetime.fromisoformat(flight['arrival_time'].replace('Z', '+00:00'))
        except:
            continue

        # 2. 需要発生時間の計算（着陸30分後〜60分後）
        demand_start = arrival_time + timedelta(minutes=30)
        demand_end = arrival_time + timedelta(minutes=60)

        # 💡 ロジック：需要発生時間が「今から1時間以内」に重なっているか判定
        # (今〜1時間後) と (需要開始〜終了) が重なればカウント
        if not (demand_end < now or demand_start > one_hour_later):
            
            # 3. 乗り場の判定（便名とターミナルから仕分け）
            stand_key = determine_stand(flight)
            
            # 4. 人数の加算（一旦、1便あたり定員の10%＝約20人と仮定）
            # ※後に機体サイズに応じた計算にアップグレード可能
            if stand_key:
                stands[stand_key] += 20
                # 3号と「国際」は連動することが多いため両方に加算（現場の運用に合わせる）
                if stand_key == "3号 (T3/国際)":
                    stands["国際 (T3/全体)"] += 20

    return stands

def determine_stand(flight):
    """
    便名(IATA)とターミナル情報から、5つの乗り場のどこに行く客かを判定する
    """
    iata = flight.get('flight_iata', "")
    terminal = flight.get('terminal')
    
    # --- 救済ロジック：ターミナルがnullでも便名で判定 ---
    
    # 1号乗り場：JAL(JL), 日本トランスオーシャン(NU), スカイマーク(BC), スターフライヤー(7G)
    if any(iata.startswith(prefix) for prefix in ["JL", "NU", "BC", "7G"]):
        return "1号 (T1/JAL系)"
        
    # 2号乗り場：ANA(NH), エアドゥ(ADO/HD), ソラシド(6J) ※国内線
    if any(iata.startswith(prefix) for prefix in ["NH", "HD", "ADO", "6J"]):
        # ANA(NH)でターミナルが2以外（T3やT2国際）の場合は別途判定
        if terminal == "3":
            return "3号 (T3/国際)"
        return "2号 (T2/ANA系)"
    
    # 3号・国際：海外航空会社
    if terminal == "3":
        return "3号 (T3/国際)"
        
    # 4号：第2ターミナルの国際線（特定のANA国際便など）
    if terminal == "2" and not any(iata.startswith(prefix) for prefix in ["NH", "HD", "6J"]):
        return "4号 (T2/国際)"
        
    # 判定不能な場合は一旦「国際」へ
    return "国際 (T3/全体)"