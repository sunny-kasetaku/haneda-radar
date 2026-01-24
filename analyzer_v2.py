from datetime import datetime, timedelta

def analyze_demand(flights):
    pax_t1 = pax_t2 = pax_t3 = 0
    now = datetime.utcnow() + timedelta(hours=9)
    
    # ==========================================
    # ⚙️ 設定：集計範囲の変数化
    # ここに数字を入れるだけで、ロジックも表示も全部変わります
    # ==========================================
    MINUTES_PAST = 40    # 過去何分まで遡るか
    MINUTES_FUTURE = 20  # 未来何分まで見るか
    # ==========================================

    # ---------------------------------------------------------
    # 1. 異常検知
    # ---------------------------------------------------------
    check_start = now - timedelta(minutes=90)
    past_planned = 0
    past_landed = 0
    seen_unique_flights = set()
    
    for f in flights:
        t_str = str(f.get('arrival_time', ''))
        if 'T' not in t_str: continue
        f_time = datetime.strptime(t_str[:16], "%Y-%m-%dT%H:%M")
        
        origin_key = f.get('origin_iata', 'UNK')
        unique_key = f"{t_str}_{origin_key}"
        
        if unique_key in seen_unique_flights: continue
        seen_unique_flights.add(unique_key)
        
        if check_start <= f_time <= now:
            past_planned += 1
            status = str(f.get('status', '')).lower()
            if status not in ['cancelled', 'diverted']:
                past_landed += 1

    is_low_volume = (8 <= now.hour <= 23) and (past_landed < 10)
    survival_rate = 1.0

    # ---------------------------------------------------------
    # 2. リスト作成
    # ---------------------------------------------------------
    # ★ 変数を使って範囲を決める（自動連動）
    range_start = now - timedelta(minutes=MINUTES_PAST)
    range_end = now + timedelta(minutes=MINUTES_FUTURE)
    
    # ★ 変数を使って足切りラインを決める
    arrival_cutoff = now + timedelta(minutes=MINUTES_FUTURE)
    
    forecast_data = {"h1": 0, "h2": 0, "h3": 0}
    candidates = []
    processed_keys = set()
    
    for f in flights:
        t_str = str(f.get('arrival_time', ''))
        if 'T' not in t_str: continue
        f_time = datetime.strptime(t_str[:16], "%Y-%m-%dT%H:%M")
        f['parsed_time'] = f_time
        
        origin_key = f.get('origin_iata', 'UNK')
        unique_key = f"{t_str}_{origin_key}"
        
        if unique_key in processed_keys: continue
        processed_keys.add(unique_key)
        
        status = str(f.get('status', '')).lower()
        term = str(f.get('terminal', ''))
        
        is_intl = any(x in term for x in ['3', 'I', 'Intl'])
        pax_base = 250 if is_intl else 150
        
        # --- A. 現在の実数 ---
        if range_start <= f_time <= range_end:
            if status in ['cancelled', 'diverted']:
                continue
            
            if f_time <= arrival_cutoff:
                f['pax_estimated'] = pax_base
                candidates.append(f)
                
                if is_intl: pax_t3 += pax_base
                elif '1' in term: pax_t1 += pax_base
                elif '2' in term: pax_t2 += pax_base
                else: pax_t3 += pax_base
                continue

        # --- B. 未来の予測 ---
        if f_time > now:
            diff_h = (f_time - now).total_seconds() / 3600
            if 0 <= diff_h < 1: forecast_data["h1"] += pax_base
            elif 1 <= diff_h < 2: forecast_data["h2"] += pax_base
            elif 2 <= diff_h < 3: forecast_data["h3"] += pax_base

    candidates.sort(key=lambda x: x['parsed_time'])
    
    final_forecast = {}
    
    for k, v in forecast_data.items():
        time_label = (now + timedelta(hours=int(k[1]))).strftime("%H:00〜")
        pred_pax = int(v * survival_rate)
        if pred_pax > 400: st, cm = "🔥 高", "需要あり"
        elif pred_pax > 100: st, cm = "👀 通常", "通常運行"
        else: st, cm = "📉 低", "静か"
        final_forecast[k] = {"label": time_label, "pax": pred_pax, "status": st, "comment": cm}

    return {
        "1号(T1南)": int(pax_t1 * 0.5), "2号(T1北)": int(pax_t1 * 0.5),
        "3号(T2)": int(pax_t2 * 0.5), "4号(T2)": int(pax_t2 * 0.5),
        "国際(T3)": pax_t3, 
        "forecast": final_forecast,
        "unique_count": len(candidates), 
        "flights": candidates,
        # ★ ここで「設定値」も一緒に渡す
        "setting_past": MINUTES_PAST,
        "setting_future": MINUTES_FUTURE
    }
