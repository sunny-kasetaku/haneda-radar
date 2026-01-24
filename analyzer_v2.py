# analyzer_v2.py (コードシェア排除・強化版)
from datetime import datetime, timedelta

def analyze_demand(flights):
    pax_t1 = 0
    pax_t2 = 0
    pax_t3 = 0
    
    now = datetime.now() + timedelta(hours=9)
    range_start = now - timedelta(minutes=30)
    range_end = now + timedelta(minutes=45)
    
    forecast = {
        "h1": {"label": (now + timedelta(hours=1)).strftime("%H:00〜"), "pax": 0, "status": "", "comment": ""},
        "h2": {"label": (now + timedelta(hours=2)).strftime("%H:00〜"), "pax": 0, "status": "", "comment": ""},
        "h3": {"label": (now + timedelta(hours=3)).strftime("%H:00〜"), "pax": 0, "status": "", "comment": ""}
    }

    seen_vessels = set()
    unique_flights = []

    for f in flights:
        # --- 重複排除 (時間と出発地だけで判定) ---
        t_str = str(f.get('arrival_time', ''))
        origin = f.get('origin_iata', 'UNK')
        
        # 同じ時間に同じ場所から来る便は、1つの機体(コードシェア)とみなす
        vessel_key = f"{t_str[:16]}_{origin}"

        if vessel_key in seen_vessels:
            continue 
        seen_vessels.add(vessel_key)
        
        # --- 判定処理 ---
        airline = str(f.get('airline', '')).upper()
        term = str(f.get('terminal', ''))
        
        pax = 150 # デフォルト
        if '3' in term or 'I' in term or 'Intl' in term:
            pax = 250
        elif any(x in airline for x in ["WINGS", "J-AIR", "HAC", "AMX", "ORC", "IBEX"]):
            pax = 50

        f['pax_estimated'] = pax
        
        try:
            if 'T' in t_str:
                flight_time = datetime.strptime(t_str[:16], "%Y-%m-%dT%H:%M")
            else:
                continue

            # 集計
            if range_start <= flight_time <= range_end:
                unique_flights.append(f)
                if '1' in term:
                    pax_t1 += pax
                elif '2' in term:
                    pax_t2 += pax
                else:
                    pax_t3 += pax

            # 予測
            diff_hours = (flight_time - now).total_seconds() / 3600
            if 0 <= diff_hours < 1: forecast["h1"]["pax"] += pax
            elif 1 <= diff_hours < 2: forecast["h2"]["pax"] += pax
            elif 2 <= diff_hours < 3: forecast["h3"]["pax"] += pax

        except:
            continue

    # 最終集計 (T1を南北に分配)
    return {
        "1号(T1南)": int(pax_t1 * 0.5),
        "2号(T1北)": int(pax_t1 * 0.5),
        "3号(T2)":   int(pax_t2 * 0.5),
        "4号(T2)":   int(pax_t2 * 0.5),
        "国際(T3)":  pax_t3,
        "forecast": forecast,
        "unique_count": len(unique_flights),
        "flights": unique_flights
    }
