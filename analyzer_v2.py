# analyzer_v2.py (余計な推測廃止・便名完全一致のみ重複削除版)
from datetime import datetime, timedelta

def analyze_demand(flights):
    pax_t1 = pax_t2 = pax_t3 = 0
    now = datetime.now() + timedelta(hours=9)
    
    # ---------------------------------------------------------
    # 1. 生存率 & 絶対数チェック
    # ---------------------------------------------------------
    check_start = now - timedelta(minutes=90)
    past_planned = 0
    past_landed = 0
    seen_stats = set()
    
    for f in flights:
        t_str = str(f.get('arrival_time', ''))
        flight_num = f.get('flight_number', 'UNK') # 便名で管理
        if 'T' not in t_str: continue
        f_time = datetime.strptime(t_str[:16], "%Y-%m-%dT%H:%M")
        
        # 統計用：同じ便名は1回しかカウントしない
        if flight_num in seen_stats: continue
        seen_stats.add(flight_num)
        
        if check_start <= f_time <= now:
            past_planned += 1
            if str(f.get('status', '')).lower() == 'landed':
                past_landed += 1

    # 絶対数チェック
    is_low_volume = (8 <= now.hour <= 23) and (past_landed < 15)
    if is_low_volume:
        survival_rate = 0.0
    elif past_planned > 5:
        survival_rate = past_landed / past_planned
        survival_rate = max(0.1, min(1.0, survival_rate))
    else:
        survival_rate = 1.0

    # ---------------------------------------------------------
    # 2. リスト作成（余計な重複判定を削除）
    # ---------------------------------------------------------
    range_start = now - timedelta(minutes=40)
    range_end = now + timedelta(minutes=5)
    
    forecast_data = {"h1": 0, "h2": 0, "h3": 0}
    candidates = []
    
    # 既にリストに入れた便名を記録するセット
    processed_flight_numbers = set()
    
    # まずAPIの生データを解析
    for f in flights:
        t_str = str(f.get('arrival_time', ''))
        if 'T' not in t_str: continue
        f_time = datetime.strptime(t_str[:16], "%Y-%m-%dT%H:%M")
        f['parsed_time'] = f_time
        
        # 便名を取得（例：JL912）
        f_num = f.get('flight_number', 'UNK')
        
        # ★ここが修正点★
        # 「便名」が既にあったらスキップ。無ければ登録。
        # これだけで二重カウントは防げる。時間や場所での推測削除はしない。
        if f_num in processed_flight_numbers:
            continue
        processed_flight_numbers.add(f_num)
        
        status = str(f.get('status', '')).lower()
        term = str(f.get('terminal', ''))
        
        # 国際線判定（人数計算用）
        is_intl = any(x in term for x in ['3', 'I', 'Intl'])
        pax_base = 250 if is_intl else 150
        
        # 現在の実数
        if range_start <= f_time <= range_end:
            if status == 'landed':
                f['pax_estimated'] = pax_base
                candidates.append(f)
                
                # 集計
                if is_intl: pax_t3 += pax_base # T3/IntlタグがあればT3へ
                elif '1' in term: pax_t1 += pax_base
                elif '2' in term: pax_t2 += pax_base
                else: pax_t3 += pax_base # 不明なら国際枠へ(安全策)

        # 未来の予測
        if f_time > now:
            diff_h = (f_time - now).total_seconds() / 3600
            if 0 <= diff_h < 1: forecast_data["h1"] += pax_base
            elif 1 <= diff_h < 2: forecast_data["h2"] += pax_base
            elif 2 <= diff_h < 3: forecast_data["h3"] += pax_base

    # ---------------------------------------------------------
    # 3. ソートして完了
    # ---------------------------------------------------------
    candidates.sort(key=lambda x: x['parsed_time'])
    
    # ---------------------------------------------------------
    # 4. 予測表示
    # ---------------------------------------------------------
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
