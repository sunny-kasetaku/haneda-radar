from datetime import datetime, timedelta

def analyze_demand(flights):
    pax_t1 = pax_t2 = pax_t3 = 0
    # APIは日本時間(JST)で返してくるため、基準もJSTにする
    now = datetime.utcnow() + timedelta(hours=9)
    
    # ---------------------------------------------------------
    # 1. 異常検知
    # ---------------------------------------------------------
    check_start = now - timedelta(minutes=90)
    past_planned = 0
    past_landed = 0
    seen_unique_flights = set() # 統計用の重複排除セット
    
    for f in flights:
        t_str = str(f.get('arrival_time', ''))
        if 'T' not in t_str: continue
        f_time = datetime.strptime(t_str[:16], "%Y-%m-%dT%H:%M")
        
        # 【重複排除キー】 時間_出発地 (例: "18:30_CTS")
        # これでコードシェア便(JL514とHA5000など)を1機としてカウントできる
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
    # 範囲：過去60分 〜 未来60分
    range_start = now - timedelta(minutes=60)
    range_end = now + timedelta(minutes=60)
    
    # リスト表示リミット
    arrival_cutoff = now + timedelta(minutes=60)
    
    forecast_data = {"h1": 0, "h2": 0, "h3": 0}
    candidates = []
    processed_keys = set() # リスト作成用の重複排除セット
    
    for f in flights:
        t_str = str(f.get('arrival_time', ''))
        if 'T' not in t_str: continue
        f_time = datetime.strptime(t_str[:16], "%Y-%m-%dT%H:%M")
        f['parsed_time'] = f_time
        
        # 【ここが修正点】便名(JLxxx)ではなく、「時間+場所」で重複チェック
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
            
            # ActiveでもScheduledでも、時間が来ていれば採用
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
        "flights": candidates
    }
