# analyzer_v2.py (過去完了フィルター搭載・最終版)
from datetime import datetime, timedelta

def analyze_demand(flights):
    pax_t1 = pax_t2 = pax_t3 = 0
    now = datetime.now() + timedelta(hours=9)
    # 表示範囲: 到着済みも少し見たいが、ゴーストは消したい
    range_start = now - timedelta(minutes=30)
    range_end = now + timedelta(minutes=45)
    
    forecast = {"h1": {"pax": 0}, "h2": {"pax": 0}, "h3": {"pax": 0}}
    seen_vessels = []
    unique_flights = []

    for f in flights:
        t_str = str(f.get('arrival_time', ''))
        origin = f.get('origin_iata', 'UNK')
        status = str(f.get('status', '')).lower()
        if 'T' not in t_str: continue
        
        f_time = datetime.strptime(t_str[:16], "%Y-%m-%dT%H:%M")
        
        # 1. 重複排除 (時間ズレ対策)
        is_duplicate = False
        for seen_time, seen_origin in seen_vessels:
            if seen_origin == origin and abs((f_time - seen_time).total_seconds()) < 900:
                is_duplicate = True
                break
        if is_duplicate: continue
        seen_vessels.append((f_time, origin))

        # 2. 【最強】過去ゴースト＆未来ゴーストのダブル排除
        
        # A. 未来のゴースト対策 (35分ルール)
        # まだ着いていないのに「予定」のまま直前まで来ているやつは消す
        if f_time > now:
            if (status == 'scheduled' or status == 'unknown'):
                if (f_time - now).total_seconds() / 60 < 35:
                    continue 

        # B. 過去のゴースト対策 (新機能)
        # 到着時間を過ぎているのに、ステータスが「landed」になっていないやつは
        # APIが更新を放棄したゴースト便なので消す
        if f_time <= now:
            if status != 'landed':
                continue

        # 3. 人数計算
        airline = str(f.get('airline', '')).upper()
        term = str(f.get('terminal', ''))
        pax = 250 if any(x in term for x in ['3', 'I', 'Intl']) else 150
        f['pax_estimated'] = pax

        if range_start <= f_time <= range_end:
            unique_flights.append(f)
            if '1' in term: pax_t1 += pax
            elif '2' in term: pax_t2 += pax
            else: pax_t3 += pax

        # 4. 予測集計
        diff_h = (f_time - now).total_seconds() / 3600
        if 0 <= diff_h < 1: forecast["h1"]["pax"] += pax
        elif 1 <= diff_h < 2: forecast["h2"]["pax"] += pax
        elif 2 <= diff_h < 3: forecast["h3"]["pax"] += pax

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
