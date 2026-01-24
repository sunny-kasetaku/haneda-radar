# analyzer_v2.py (JAL重複排除・最強版)
from datetime import datetime, timedelta

def analyze_demand(flights):
    pax_t1 = 0
    pax_t2 = 0
    pax_t3 = 0
    
    now = datetime.now() + timedelta(hours=9)
    range_start = now - timedelta(minutes=30)
    range_end = now + timedelta(minutes=45)
    
    forecast = {
        "h1": {"label": (now + timedelta(hours=1)).strftime("%H:00〜"), "pax": 0},
        "h2": {"label": (now + timedelta(hours=2)).strftime("%H:00〜"), "pax": 0},
        "h3": {"label": (now + timedelta(hours=3)).strftime("%H:00〜"), "pax": 0}
    }

    seen_vessels = [] # リストに変更して時間幅でチェック
    unique_flights = []

    for f in flights:
        t_str = str(f.get('arrival_time', ''))
        origin = f.get('origin_iata', 'UNK')
        if 'T' not in t_str: continue
        
        f_time = datetime.strptime(t_str[:16], "%Y-%m-%dT%H:%M")
        
        # --- 最強の重複排除ロジック ---
        # 前後10分以内に、同じ空港から来る便は「同一機体」とみなして無視する
        is_duplicate = False
        for seen_time, seen_origin in seen_vessels:
            if seen_origin == origin and abs((f_time - seen_time).total_seconds()) < 600:
                is_duplicate = True
                break
        
        if is_duplicate:
            continue
            
        seen_vessels.append((f_time, origin))
        # ----------------------------

        airline = str(f.get('airline', '')).upper()
        term = str(f.get('terminal', ''))
        
        pax = 150
        if any(x in term for x in ['3', 'I', 'Intl']): pax = 250
        elif any(x in airline for x in ["WINGS", "J-AIR", "HAC", "AMX", "ORC", "IBEX"]): pax = 50

        f['pax_estimated'] = pax
        
        if range_start <= f_time <= range_end:
            unique_flights.append(f)
            if '1' in term: pax_t1 += pax
            elif '2' in term: pax_t2 += pax
            else: pax_t3 += pax

        diff_hours = (f_time - now).total_seconds() / 3600
        if 0 <= diff_hours < 1: forecast["h1"]["pax"] += pax
        elif 1 <= diff_hours < 2: forecast["h2"]["pax"] += pax
        elif 2 <= diff_hours < 3: forecast["h3"]["pax"] += pax

    return {
        "1号(T1南)": int(pax_t1 * 0.5), "2号(T1北)": int(pax_t1 * 0.5),
        "3号(T2)": int(pax_t2 * 0.5), "4号(T2)": int(pax_t2 * 0.5),
        "国際(T3)": pax_t3, "forecast": forecast,
        "unique_count": len(unique_flights), "flights": unique_flights
    }
