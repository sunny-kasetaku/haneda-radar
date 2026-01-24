# analyzer_v2.py (実績限定・超厳格モード)
from datetime import datetime, timedelta

def analyze_demand(flights):
    pax_t1 = pax_t2 = pax_t3 = 0
    now = datetime.now() + timedelta(hours=9)
    
    # 範囲：過去60分 〜 未来5分 (未来の予定は嘘が多いので見ない)
    range_start = now - timedelta(minutes=60)
    range_end = now + timedelta(minutes=5)
    
    forecast = {"h1": {"pax": 0}, "h2": {"pax": 0}, "h3": {"pax": 0}}
    seen_vessels = []
    unique_flights = []

    for f in flights:
        t_str = str(f.get('arrival_time', ''))
        origin = f.get('origin_iata', 'UNK')
        status = str(f.get('status', '')).lower()
        
        if 'T' not in t_str: continue
        f_time = datetime.strptime(t_str[:16], "%Y-%m-%dT%H:%M")
        
        # 1. 重複排除
        is_duplicate = False
        for seen_time, seen_origin in seen_vessels:
            if seen_origin == origin and abs((f_time - seen_time).total_seconds()) < 900:
                is_duplicate = True
                break
        if is_duplicate: continue
        seen_vessels.append((f_time, origin))

        # 2. 【超厳格フィルター】
        # 「着陸済み(landed)」以外はすべて無視します。
        # APIが「active」と言っても、プロデューサーの「ゼロ」という感覚を優先して無視します。
        if status != 'landed':
            continue

        # 3. 人数計算
        airline = str(f.get('airline', '')).upper()
        term = str(f.get('terminal', ''))
        pax = 250 if any(x in term for x in ['3', 'I', 'Intl']) else 150
        f['pax_estimated'] = pax

        # 4. 集計
        if range_start <= f_time <= range_end:
            unique_flights.append(f)
            if '1' in term: pax_t1 += pax
            elif '2' in term: pax_t2 += pax
            else: pax_t3 += pax

        # 予測用も、今回は「実績ベース」にするため、未来のscheduledは加算しません。
        # 必要であればここだけscheduledを許可することもできますが、今回は徹底します。

    return {
        "1号(T1南)": int(pax_t1 * 0.5), "2号(T1北)": int(pax_t1 * 0.5),
        "3号(T2)": int(pax_t2 * 0.5), "4号(T2)": int(pax_t2 * 0.5),
        "国際(T3)": pax_t3, 
        "forecast": {k: {"label": (now + timedelta(hours=int(k[1]))).strftime("%H:00〜"), 
                        "pax": 0,  # 予測も一旦ゼロベースにします
                        "status": "❓ 不明",
                        "comment": "荒天のため予測停止"} 
                    for k, v in forecast.items()},
        "unique_count": len(unique_flights), 
        "flights": unique_flights
    }
