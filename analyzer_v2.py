from datetime import datetime, timedelta

def analyze_demand(flights):
    pax_t1 = pax_t2 = pax_t3 = 0
    now = datetime.now() + timedelta(hours=9)
    range_start = now - timedelta(minutes=30)
    range_end = now + timedelta(minutes=45)
    
    # 予測用
    forecast = {"h1": {"pax": 0}, "h2": {"pax": 0}, "h3": {"pax": 0}}
    seen_vessels = []
    unique_flights = []

    for f in flights:
        t_str = str(f.get('arrival_time', ''))
        origin = f.get('origin_iata', 'UNK')
        status = str(f.get('status', '')).lower()
        if 'T' not in t_str: continue
        
        f_time = datetime.strptime(t_str[:16], "%Y-%m-%dT%H:%M")
        
        # 1. 重複排除 (JAL等の重複対策)
        is_duplicate = False
        for seen_time, seen_origin in seen_vessels:
            if seen_origin == origin and abs((f_time - seen_time).total_seconds()) < 600:
                is_duplicate = True
                break
        if is_duplicate: continue
        seen_vessels.append((f_time, origin))

        # 2. 【核心】信頼度の動的判定
        # 通常は100%だが、到着20分前になってもステータスが"scheduled"（予定）のままなら、
        # 実際には飛んでいない「ゴースト便」とみなして、推計人数を10%まで落とす。
        confidence = 1.0
        if status == 'scheduled' or status == 'unknown':
            diff_to_arrival = (f_time - now).total_seconds() / 60
            if diff_to_arrival < 25: # 到着まで25分を切っても「予定」のままなら疑う
                confidence = 0.1 

        # 3. 人数計算
        airline = str(f.get('airline', '')).upper()
        term = str(f.get('terminal', ''))
        pax = 250 if any(x in term for x in ['3', 'I', 'Intl']) else 150
        
        # 信頼度を掛けて実数を算出
        estimated_pax = int(pax * confidence)
        f['pax_estimated'] = estimated_pax

        # 除外判定：極端に信頼度が低い便（欠航疑い）はリストにも出さないか、0名として扱う
        if confidence <= 0.1:
            continue # これでYahoo!の欠航便をリストから消し去ります

        if range_start <= f_time <= range_end:
            unique_flights.append(f)
            if '1' in term: pax_t1 += estimated_pax
            elif '2' in term: pax_t2 += estimated_pax
            else: pax_t3 += estimated_pax

        # 予測
        diff_h = (f_time - now).total_seconds() / 3600
        if 0 <= diff_h < 1: forecast["h1"]["pax"] += estimated_pax
        elif 1 <= diff_h < 2: forecast["h2"]["pax"] += estimated_pax
        elif 2 <= diff_h < 3: forecast["h3"]["pax"] += estimated_pax

    # 4. レンダラーへの返却
    return {
        "1号(T1南)": int(pax_t1 * 0.5), "2号(T1北)": int(pax_t1 * 0.5),
        "3号(T2)": int(pax_t2 * 0.5), "4号(T2)": int(pax_t2 * 0.5),
        "国際(T3)": pax_t3, 
        "forecast": {k: {"label": (now + timedelta(hours=int(k[1]))).strftime("%H:00〜"), 
                        "pax": v["pax"], 
                        "status": "🔥 高" if v["pax"] > 400 else "👀 低",
                        "comment": "需要あり" if v["pax"] > 400 else "待機"} 
                    for k, v in forecast.items()},
        "unique_count": len(unique_flights), 
        "flights": unique_flights
    }
