# analyzer_v2.py (v11.8: 必要な機能は維持し、時差補正バグのみ除去版)
from datetime import datetime, timedelta

def analyze_demand(flights):
    pax_t1 = pax_t2 = pax_t3 = 0
    # 診断結果より、APIはJST(日本時間)で返していることが確定。
    # 基準時間をJSTに合わせる（ここは維持）
    now = datetime.utcnow() + timedelta(hours=9)
    
    # ---------------------------------------------------------
    # 1. 異常検知 (統計チェック) - 【ロジック維持】
    # ---------------------------------------------------------
    check_start = now - timedelta(minutes=90)
    past_planned = 0
    past_landed = 0
    seen_stats = set()
    
    for f in flights:
        t_str = str(f.get('arrival_time', ''))
        if 'T' not in t_str: continue
        
        # 【変更点】誤った時差補正関数(normalize_time)を通さず、素直に時間を読む
        # これにより「明日の朝」に飛ばされるバグを防ぐ
        f_time = datetime.strptime(t_str[:16], "%Y-%m-%dT%H:%M")
        
        flight_num = f.get('flight_number', 'UNK')
        if flight_num in seen_stats: continue
        seen_stats.add(flight_num)
        
        if check_start <= f_time <= now:
            past_planned += 1
            # キャンセルでなければカウントするロジックは維持
            status = str(f.get('status', '')).lower()
            if status not in ['cancelled', 'diverted']:
                past_landed += 1

    # 生存率計算ロジックは維持
    is_low_volume = (8 <= now.hour <= 23) and (past_landed < 10)
    survival_rate = 1.0 # 今回はActiveも拾うため、補正なしで1.0固定とする

    # ---------------------------------------------------------
    # 2. リスト作成 - 【ロジック維持＆範囲微調整】
    # ---------------------------------------------------------
    # 範囲：過去60分 〜 未来60分 
    # (APIの更新が遅いANAも、接近中のActive便も拾うため広く取る)
    range_start = now - timedelta(minutes=60)
    range_end = now + timedelta(minutes=60)
    
    # リスト表示する限界ライン（未来60分まで許容するように変更）
    arrival_cutoff = now + timedelta(minutes=60)
    
    forecast_data = {"h1": 0, "h2": 0, "h3": 0}
    candidates = []
    processed_flight_numbers = set()
    
    for f in flights:
        t_str = str(f.get('arrival_time', ''))
        if 'T' not in t_str: continue
        
        # 素直に時間を読む
        f_time = datetime.strptime(t_str[:16], "%Y-%m-%dT%H:%M")
        f['parsed_time'] = f_time
        
        f_num = f.get('flight_number', 'UNK')
        if f_num in processed_flight_numbers: continue
        processed_flight_numbers.add(f_num)
        
        status = str(f.get('status', '')).lower()
        term = str(f.get('terminal', ''))
        
        # 国際線・人数判定ロジックは維持
        is_intl = any(x in term for x in ['3', 'I', 'Intl'])
        pax_base = 250 if is_intl else 150
        
        # --- A. 現在の実数 ---
        # 時間範囲内であれば採用
        if range_start <= f_time <= range_end:
            if status in ['cancelled', 'diverted']:
                continue
            
            # 時間チェックのみで通過 (ActiveでもScheduledでもLandedでもOK)
            # これにより「Active」のままのANA便がリスト入りする
            if f_time <= arrival_cutoff:
                f['pax_estimated'] = pax_base
                candidates.append(f)
                
                # ターミナル集計ロジックは維持
                if is_intl: pax_t3 += pax_base
                elif '1' in term: pax_t1 += pax_base
                elif '2' in term: pax_t2 += pax_base
                else: pax_t3 += pax_base
                continue

        # --- B. 未来の予測 ---
        # 予測ロジックは維持
        if f_time > now:
            diff_h = (f_time - now).total_seconds() / 3600
            if 0 <= diff_h < 1: forecast_data["h1"] += pax_base
            elif 1 <= diff_h < 2: forecast_data["h2"] += pax_base
            elif 2 <= diff_h < 3: forecast_data["h3"] += pax_base

    candidates.sort(key=lambda x: x['parsed_time'])
    
    final_forecast = {}
    
    # 表示用データ作成ロジックは維持
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
