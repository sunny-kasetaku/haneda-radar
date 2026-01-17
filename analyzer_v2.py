from datetime import datetime, timedelta

def analyze_demand(flights):
    # Tさんの統計比率
    WEIGHT_MASTER = {
        7:[2,0,1,0,8], 8:[8,9,13,4,0], 9:[10,9,16,3,1], 10:[6,8,9,4,0],
        11:[10,10,10,6,1], 12:[9,7,14,4,1], 13:[10,9,8,4,0], 14:[8,5,9,7,0],
        15:[7,7,13,3,0], 16:[7,12,10,5,2], 17:[10,7,10,4,6], 18:[10,8,11,9,1],
        19:[9,7,11,3,1], 20:[11,7,11,4,2], 21:[10,10,14,4,1], 22:[7,7,9,4,2], 23:[1,0,2,3,0]
    }

    pax_t1, pax_t2, pax_t3 = 0, 0, 0
    now = datetime.now()
    
    forecast = {
        "h1": {"label": f"{(now + timedelta(hours=1)).hour}:00迄", "pax": 0},
        "h2": {"label": f"{(now + timedelta(hours=2)).hour}:00迄", "pax": 0},
        "h3": {"label": f"{(now + timedelta(hours=3)).hour}:00迄", "pax": 0}
    }

    seen_flights = set()
    unique_flights = []

    for f in flights:
        # 時刻・出発地・ターミナルが同じなら同一便とみなして重複排除
        f_key = f"{f.get('arrival_time')}_{f.get('origin')}_{f.get('terminal')}"
        
        if f_key not in seen_flights:
            seen_flights.add(f_key)
            unique_flights.append(f)
            
            pax = f.get('pax') or 150
            term = str(f.get('terminal', ''))
            
            if '1' in term: pax_t1 += pax
            elif '2' in term: pax_t2 += pax
            else: pax_t3 += pax

            arrival_str = f.get('arrival_time', '')
            try:
                t_part = arrival_str.split('T')[1][:5] if 'T' in arrival_str else arrival_str[:5]
                arrival_h = int(t_part.split(':')[0])
                diff = (arrival_h - now.hour) % 24
                if diff == 0: forecast["h1"]["pax"] += pax
                elif diff == 1: forecast["h2"]["pax"] += pax
                elif diff == 2: forecast["h3"]["pax"] += pax
            except:
                pass

    w = WEIGHT_MASTER.get(now.hour, [1,1,1,1,1])
    t1_total_w = (w[0] + w[1]) or 2
    t2_total_w = (w[2] + w[3] + w[4]) or 3

    results = {
        "1号(T1南)": int(pax_t1 * w[0] / t1_total_w),
        "2号(T1北)": int(pax_t1 * w[1] / t1_total_w),
        "3号(T2)":   int(pax_t2 * w[2] / t2_total_w),
        "4号(T2)":   int(pax_t2 * w[3] / t2_total_w),
        "国際(T3)":  pax_t3 + int(pax_t2 * w[4] / t2_total_w),
        "forecast": forecast,
        "unique_count": len(unique_flights)
    }
    return results