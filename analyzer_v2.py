from datetime import datetime, timedelta

def analyze_demand(flights):
    pax_t1 = pax_t2 = pax_t3 = 0
    now = datetime.now() + timedelta(hours=9)
    
    # ---------------------------------------------------------
    # 1. 生存率（Survival Rate）の計算
    # ---------------------------------------------------------
    check_start = now - timedelta(minutes=90)
    past_planned = 0
    past_landed = 0
    seen_stats = set()
    
    for f in flights:
        t_str = str(f.get('arrival_time', ''))
        origin = f.get('origin_iata', 'UNK')
        if 'T' not in t_str: continue
        f_time = datetime.strptime(t_str[:16], "%Y-%m-%dT%H:%M")
        
        v_key = f"{t_str[:16]}_{origin}"
        if v_key in seen_stats: continue
        seen_stats.add(v_key)
        
        if check_start <= f_time <= now:
            past_planned += 1
            if str(f.get('status', '')).lower() == 'landed':
                past_landed += 1

    # 生存率算出 (データ不足時は性善説で1.0)
    if past_planned > 5:
        survival_rate = past_landed / past_planned
    else:
        survival_rate = 1.0

    print(f"DEBUG: Survival Rate = {survival_rate:.2f}")

    # ---------------------------------------------------------
    # 2. 集計処理
    # ---------------------------------------------------------
    range_start = now - timedelta(minutes=60)
    range_end = now + timedelta(minutes=5)
    
    # 予測用の一時コンテナ
    forecast_data = {"h1": 0, "h2": 0, "h3": 0}
    
    seen_vessels = []
    unique_flights = []

    for f in flights:
        t_str = str(f.get('arrival_time', ''))
        origin = f.get('origin_iata', 'UNK')
        status = str(f.get('status', '')).lower()
        if 'T' not in t_str: continue
        f_time = datetime.strptime(t_str[:16], "%Y-%m-%dT%H:%M")
        
        # 重複排除
        is_duplicate = False
        for seen_time, seen_origin in seen_vessels:
            if seen_origin == origin and abs((f_time - seen_time).total_seconds()) < 900:
                is_duplicate = True
                break
        if is_duplicate: continue
        seen_vessels.append((f_time, origin))

        # 人数定義
        term = str(f.get('terminal', ''))
        pax_base = 250 if any(x in term for x in ['3', 'I', 'Intl']) else 150
        
        # 【現在の実数】(着陸済みのみ・超厳格)
        if range_start <= f_time <= range_end:
            if status == 'landed':
                f['pax_estimated'] = pax_base
                unique_flights.append(f)
                if '1' in term: pax_t1 += pax_base
                elif '2' in term: pax_t2 += pax_base
                else: pax_t3 += pax_base

        # 【未来の予測】(ベース計算)
        if f_time > now:
            diff_h = (f_time - now).total_seconds() / 3600
            if 0 <= diff_h < 1: forecast_data["h1"] += pax_base
            elif 1 <= diff_h < 2: forecast_data["h2"] += pax_base
            elif 2 <= diff_h < 3: forecast_data["h3"] += pax_base

    # ---------------------------------------------------------
    # 3. 予測結果の判定 (足切りスイッチ)
    # ---------------------------------------------------------
    final_forecast = {}
    
    # 生存率が50%を切るような日は、予測を出しても意味がないので「停止」にする
    is_disaster_mode = (survival_rate < 0.5)

    for k, v in forecast_data.items():
        time_label = (now + timedelta(hours=int(k[1]))).strftime("%H:00〜")
        
        if is_disaster_mode:
            # 異常時：予測を停止してゼロにする
            final_forecast[k] = {
                "label": time_label,
                "pax": 0, 
                "status": "⛔ 停止",
                "comment": "欠航多発のため予測不能"
            }
        else:
            # 正常時：生存率を掛けて補正した値を出す
            pred_pax = int(v * survival_rate)
            
            if pred_pax > 400:
                st, cm = "🔥 高", "需要あり"
            elif pred_pax > 100:
                st, cm = "👀 通常", "通常運行"
            else:
                st, cm = "📉 低", "静か"
                
            final_forecast[k] = {
                "label": time_label,
                "pax": pred_pax,
                "status": st,
                "comment": cm
            }

    return {
        "1号(T1南)": int(pax_t1 * 0.5), "2号(T1北)": int(pax_t1 * 0.5),
        "3号(T2)": int(pax_t2 * 0.5), "4号(T2)": int(pax_t2 * 0.5),
        "国際(T3)": pax_t3, 
        "forecast": final_forecast,
        "unique_count": len(unique_flights), 
        "flights": unique_flights
    }
