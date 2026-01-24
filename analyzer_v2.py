# analyzer_v2.py (国際線救出・ソート・コードシェア完全対応版)
from datetime import datetime, timedelta

def analyze_demand(flights):
    pax_t1 = pax_t2 = pax_t3 = 0
    now = datetime.now() + timedelta(hours=9)
    
    # ---------------------------------------------------------
    # 1. 生存率 & 絶対数チェック（異常検知）
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
    # 2. データの整理と選別
    # ---------------------------------------------------------
    range_start = now - timedelta(minutes=40)
    range_end = now + timedelta(minutes=5)
    
    forecast_data = {"h1": 0, "h2": 0, "h3": 0}
    candidates = [] # 一旦全ての候補を入れるリスト
    
    for f in flights:
        t_str = str(f.get('arrival_time', ''))
        if 'T' not in t_str: continue
        f_time = datetime.strptime(t_str[:16], "%Y-%m-%dT%H:%M")
        f['parsed_time'] = f_time # ソート用
        
        status = str(f.get('status', '')).lower()
        term = str(f.get('terminal', ''))
        
        # 国際線判定を強化
        # ターミナルに3/I/Intlが含まれるか、または出発地が海外空港リストにあるか等
        is_intl = any(x in term for x in ['3', 'I', 'Intl'])
        
        pax_base = 250 if is_intl else 150
        
        # --- 現在の実数（着陸済みのみ）---
        if range_start <= f_time <= range_end:
            if status == 'landed':
                f['pax_estimated'] = pax_base
                f['is_intl'] = is_intl # 後で優先度判定に使う
                candidates.append(f)

        # --- 未来の予測 ---
        if f_time > now:
            diff_h = (f_time - now).total_seconds() / 3600
            if 0 <= diff_h < 1: forecast_data["h1"] += pax_base
            elif 1 <= diff_h < 2: forecast_data["h2"] += pax_base
            elif 2 <= diff_h < 3: forecast_data["h3"] += pax_base

    # ---------------------------------------------------------
    # 3. ソートと重複排除（国際線優先ロジック）
    # ---------------------------------------------------------
    # まず時間順に並べる
    candidates.sort(key=lambda x: x['parsed_time'])
    
    unique_flights = []
    seen_vessels = [] # (time, origin, is_intl)
    
    for f in candidates:
        f_time = f['parsed_time']
        origin = f.get('origin_iata', 'UNK')
        is_intl = f['is_intl']
        
        # 重複チェック (前後15分、同じ出発地)
        is_duplicate = False
        dup_idx = -1
        
        for i, (s_time, s_origin, s_is_intl) in enumerate(seen_vessels):
            if s_origin == origin and abs((f_time - s_time).total_seconds()) < 900:
                is_duplicate = True
                dup_idx = i
                break
        
        if is_duplicate:
            # 重複がある場合、「国際線(is_intl=True)」を優先して残す
            # 既存(seen)が国内で、今回(f)が国際なら、既存を消して今回を入れる
            if is_intl and not seen_vessels[dup_idx][2]:
                del unique_flights[dup_idx]
                del seen_vessels[dup_idx]
                # 下の追加処理へ
            else:
                # 既存の方が良い、または同じなら何もしない（今回は捨てる）
                continue

        # リストに追加
        unique_flights.append(f)
        seen_vessels.append((f_time, origin, is_intl))
        
        # 集計
        pax = f['pax_estimated']
        term = str(f.get('terminal', ''))
        # 国際線フラグが立っていれば強制的にT3カウントへ誘導も可能だが
        # 基本はターミナル情報に従う。ただしT3判定されていればT3へ。
        if is_intl: pax_t3 += pax
        elif '1' in term: pax_t1 += pax
        elif '2' in term: pax_t2 += pax
        else: pax_t3 += pax # ターミナル不明はT3へ（安全策）

    # 念のため再ソート
    unique_flights.sort(key=lambda x: x['parsed_time'])

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
        "unique_count": len(unique_flights), 
        "flights": unique_flights
    }
