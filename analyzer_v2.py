# analyzer_v2.py (最終決定版：過去の予定は全て到着とみなす・強制救出版)
from datetime import datetime, timedelta

def analyze_demand(flights):
    pax_t1 = pax_t2 = pax_t3 = 0
    now = datetime.now() + timedelta(hours=9)
    
    # ---------------------------------------------------------
    # 1. 生存率 & 絶対数チェック (異常検知)
    # ---------------------------------------------------------
    check_start = now - timedelta(minutes=90)
    past_planned = 0
    past_landed = 0
    seen_stats = set()
    
    for f in flights:
        t_str = str(f.get('arrival_time', ''))
        flight_num = f.get('flight_number', 'UNK')
        if 'T' not in t_str: continue
        f_time = datetime.strptime(t_str[:16], "%Y-%m-%dT%H:%M")
        
        if flight_num in seen_stats: continue
        seen_stats.add(flight_num)
        
        # 過去90分のデータ統計
        if check_start <= f_time <= now:
            past_planned += 1
            status = str(f.get('status', '')).lower()
            # 統計上も、キャンセルマークがついてなければ「到着」とみなす
            if status not in ['cancelled', 'diverted']:
                past_landed += 1

    # 絶対数チェック
    # (判定を甘くしたので、閾値も少し調整してバランスを取る)
    is_low_volume = (8 <= now.hour <= 23) and (past_landed < 10)
    
    if is_low_volume:
        survival_rate = 0.0
    elif past_planned > 5:
        survival_rate = past_landed / past_planned
        survival_rate = max(0.1, min(1.0, survival_rate))
    else:
        survival_rate = 1.0

    # ---------------------------------------------------------
    # 2. リスト作成（ここが修正の肝）
    # ---------------------------------------------------------
    # 範囲を少し広げて「60分」にして、17:00付近の便も逃さないようにする
    range_start = now - timedelta(minutes=60)
    range_end = now + timedelta(minutes=5)
    
    forecast_data = {"h1": 0, "h2": 0, "h3": 0}
    candidates = []
    processed_flight_numbers = set()
    
    for f in flights:
        t_str = str(f.get('arrival_time', ''))
        if 'T' not in t_str: continue
        f_time = datetime.strptime(t_str[:16], "%Y-%m-%dT%H:%M")
        f['parsed_time'] = f_time
        
        f_num = f.get('flight_number', 'UNK')
        
        # 便名重複チェック（完全一致のみ弾く。余計な推測削除はしない）
        if f_num in processed_flight_numbers: continue
        processed_flight_numbers.add(f_num)
        
        status = str(f.get('status', '')).lower()
        term = str(f.get('terminal', ''))
        
        # 国際線判定
        is_intl = any(x in term for x in ['3', 'I', 'Intl'])
        pax_base = 250 if is_intl else 150
        
        # --- 現在の実数 ---
        if range_start <= f_time <= range_end:
            # ★最重要ポイント★
            # 「欠航(cancelled)」以外なら、時間が過ぎていれば全て拾う
            # APIの Active や Scheduled のまま放置されている便を救出するため
            if status in ['cancelled', 'diverted']:
                continue
            
            # 時間チェックのみで通過させる
            if f_time <= now:
                f['pax_estimated'] = pax_base
                candidates.append(f)
                
                # 集計処理
                if is_intl: pax_t3 += pax_base
                elif '1' in term: pax_t1 += pax_base
                elif '2' in term: pax_t2 += pax_base
                else: pax_t3 += pax_base

        # --- 未来の予測 ---
        if f_time > now:
            diff_h = (f_time - now).total_seconds() / 3600
            if 0 <= diff_h < 1: forecast_data["h1"] += pax_base
            elif 1 <= diff_h < 2: forecast_data["h2"] += pax_base
            elif 2 <= diff_h < 3: forecast_data["h3"] += pax_base

    # ---------------------------------------------------------
    # 3. ソート & 表示
    # ---------------------------------------------------------
    candidates.sort(key=lambda x: x['parsed_time'])
    
    final_forecast = {}
    is_disaster_mode = (survival_rate < 0.5)

    for k, v in forecast_data.items():
        time_label = (now + timedelta(hours=int(k[1]))).strftime("%H:00〜")
        if is_disaster_mode:
            final_forecast[k] = {"label": time_label, "pax": 0, "status": "⛔ 停止", "comment": "欠航多発のため予測不能"}
        else:
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
