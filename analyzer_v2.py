# analyzer_v2.py (v11.7: 時差自動補正機能付き・ANA完全救出版)
from datetime import datetime, timedelta

def analyze_demand(flights):
    pax_t1 = pax_t2 = pax_t3 = 0
    # サーバー時間はUTCかもしれないので、念のため日本時間に合わせる基準を作る
    now = datetime.utcnow() + timedelta(hours=9)
    
    # === 【重要】時差補正関数 ===
    # JALはJST(17:00)、ANAはUTC(08:00)で来ることがあるため、
    # あまりにも時間がズレている場合は「UTCだ」とみなして9時間足す
    def normalize_time(t_str):
        try:
            # まずそのままパース
            t_val = datetime.strptime(str(t_str)[:16], "%Y-%m-%dT%H:%M")
            
            # 現在時刻との差を計算
            diff = (now - t_val).total_seconds() / 3600
            
            # もし「5時間以上昔」のデータなら、UTCの可能性が高いので9時間足してJSTにする
            # (羽田のフライトで5時間遅れはあっても、到着済みデータで5時間放置は稀なため)
            if diff > 5:
                t_val += timedelta(hours=9)
            
            return t_val
        except:
            return now # エラー時は現在時刻扱い（救済）

    # ---------------------------------------------------------
    # 1. 異常検知 (統計チェック)
    # ---------------------------------------------------------
    check_start = now - timedelta(minutes=90)
    past_planned = 0
    past_landed = 0
    seen_stats = set()
    
    for f in flights:
        f_time = normalize_time(f.get('arrival_time', '')) # 補正付き時間を使う
        flight_num = f.get('flight_number', 'UNK')
        
        if flight_num in seen_stats: continue
        seen_stats.add(flight_num)
        
        if check_start <= f_time <= now:
            past_planned += 1
            status = str(f.get('status', '')).lower()
            if status not in ['cancelled', 'diverted']:
                past_landed += 1

    is_low_volume = (8 <= now.hour <= 23) and (past_landed < 10)
    
    if is_low_volume:
        survival_rate = 0.0
    elif past_planned > 5:
        survival_rate = past_landed / past_planned
        survival_rate = max(0.1, min(1.0, survival_rate))
    else:
        survival_rate = 1.0

    # ---------------------------------------------------------
    # 2. リスト作成 (時差補正 ＆ 強制救出)
    # ---------------------------------------------------------
    range_start = now - timedelta(minutes=60)
    range_end = now + timedelta(minutes=60) # 未来側も広く取る
    
    # 到着済みとみなすライン（未来20分まで）
    arrival_cutoff = now + timedelta(minutes=20)
    
    forecast_data = {"h1": 0, "h2": 0, "h3": 0}
    candidates = []
    processed_flight_numbers = set()
    
    for f in flights:
        f_time = normalize_time(f.get('arrival_time', '')) # ★ここで時間をJSTに統一
        f['parsed_time'] = f_time
        
        f_num = f.get('flight_number', 'UNK')
        if f_num in processed_flight_numbers: continue
        processed_flight_numbers.add(f_num)
        
        status = str(f.get('status', '')).lower()
        term = str(f.get('terminal', ''))
        
        is_intl = any(x in term for x in ['3', 'I', 'Intl'])
        pax_base = 250 if is_intl else 150
        
        # --- A. 現在の実数 ---
        if range_start <= f_time <= range_end:
            if status in ['cancelled', 'diverted']:
                continue
            
            # 時間が来ていれば、Status関係なく採用
            if f_time <= arrival_cutoff:
                f['pax_estimated'] = pax_base
                candidates.append(f)
                
                if is_intl: pax_t3 += pax_base
                elif '1' in term: pax_t1 += pax_base
                elif '2' in term: pax_t2 += pax_base
                else: pax_t3 += pax_base # ターミナル不明はT3へ
                continue

        # --- B. 未来の予測 ---
        if f_time > now:
            diff_h = (f_time - now).total_seconds() / 3600
            if 0 <= diff_h < 1: forecast_data["h1"] += pax_base
            elif 1 <= diff_h < 2: forecast_data["h2"] += pax_base
            elif 2 <= diff_h < 3: forecast_data["h3"] += pax_base

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
