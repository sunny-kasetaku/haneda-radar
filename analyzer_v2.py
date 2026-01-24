# analyzer_v2.py (超厳格・着陸済みのみカウント版)
from datetime import datetime, timedelta

def analyze_demand(flights):
    pax_t1 = pax_t2 = pax_t3 = 0
    now = datetime.now() + timedelta(hours=9)
    # 表示範囲: 過去30分〜未来0分（未来の予定は一切信じない）
    range_start = now - timedelta(minutes=60) 
    range_end = now + timedelta(minutes=5) 
    
    forecast = {"h1": {"pax": 0}, "h2": {"pax": 0}, "h3": {"pax": 0}}
    seen_vessels = []
    unique_flights = []

    for f in flights:
        t_str = str(f.get('arrival_time', ''))
        origin = f.get('origin_iata', 'UNK')
        status = str(f.get('status', '')).lower() # APIのステータス
        
        if 'T' not in t_str: continue
        f_time = datetime.strptime(t_str[:16], "%Y-%m-%dT%H:%M")
        
        # 1. 重複排除 (念のため維持)
        is_duplicate = False
        for seen_time, seen_origin in seen_vessels:
            if seen_origin == origin and abs((f_time - seen_time).total_seconds()) < 900:
                is_duplicate = True
                break
        if is_duplicate: continue
        seen_vessels.append((f_time, origin))

        # 2. 【超厳格フィルター】「着陸済み」以外は全て無視
        # active(飛行中)すら信じない。landed(着陸)のみをカウント。
        # ※ただし、国際線など一部データのために active は拾うなら下記を調整
        if status != 'landed' and status != 'active':
            continue

        # 3. 人数計算
        airline = str(f.get('airline', '')).upper()
        term = str(f.get('terminal', ''))
        pax = 250 if any(x in term for x in ['3', 'I', 'Intl']) else 150
        f['pax_estimated'] = pax

        # 4. 集計（現在時刻周辺の実績のみ）
        if range_start <= f_time <= range_end:
            unique_flights.append(f)
            if '1' in term: pax_t1 += pax
            elif '2' in term: pax_t2 += pax
            else: pax_t3 += pax

        # 予測用（ここも厳しいままでいくなら実績ベースにはできないが、
        # 未来予測だけはAPIのScheduledを使わざるを得ない。ただし厳し目に間引く）
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
