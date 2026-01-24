from datetime import datetime, timedelta

def analyze_demand(flights):
    pax_t1 = pax_t2 = pax_t3 = 0
    now = datetime.now() + timedelta(hours=9)
    
    # ---------------------------------------------------------
    # 1. 生存率（Survival Rate）の計算
    # 過去90分間で「予定に対して何機実際に降りてきたか」を計算します。
    # ---------------------------------------------------------
    check_start = now - timedelta(minutes=90)
    past_planned = 0
    past_landed = 0
    seen_stats = set() # 統計用重複チェック
    
    for f in flights:
        t_str = str(f.get('arrival_time', ''))
        origin = f.get('origin_iata', 'UNK')
        if 'T' not in t_str: continue
        f_time = datetime.strptime(t_str[:16], "%Y-%m-%dT%H:%M")
        
        # 統計用の重複排除 (コードシェア対策)
        v_key = f"{t_str[:16]}_{origin}"
        if v_key in seen_stats: continue
        seen_stats.add(v_key)
        
        # 過去90分のデータを集計
        if check_start <= f_time <= now:
            past_planned += 1
            if str(f.get('status', '')).lower() == 'landed':
                past_landed += 1

    # 生存率の算出
    # 母数が少ない朝イチなどは、エラー防止のため「1.0(正常)」とする
    if past_planned > 5:
        survival_rate = past_landed / past_planned
        # どんなに悪くても10%は残し、良くても100%までとする
        survival_rate = max(0.1, min(1.0, survival_rate))
    else:
        survival_rate = 1.0 # データ不足時は性善説で動く

    # ---------------------------------------------------------
    # 2. 本番集計 (現在実数 & 未来予測)
    # ---------------------------------------------------------
    range_start = now - timedelta(minutes=60)
    range_end = now + timedelta(minutes=5)
    forecast = {"h1": {"pax": 0}, "h2": {"pax": 0}, "h3": {"pax": 0}}
    
    seen_vessels = []
    unique_flights = []

    for f in flights:
        t_str = str(f.get('arrival_time', ''))
        origin = f.get('origin_iata', 'UNK')
        status = str(f.get('status', '')).lower()
        if 'T' not in t_str: continue
        f_time = datetime.strptime(t_str[:16], "%Y-%m-%dT%H:%M")
        
        # 重複排除 (JAL等の時間ズレ対策)
        is_duplicate = False
        for seen_time, seen_origin in seen_vessels:
            if seen_origin == origin and abs((f_time - seen_time).total_seconds()) < 900:
                is_duplicate = True
                break
        if is_duplicate: continue
        seen_vessels.append((f_time, origin))

        # 人数定義
        airline = str(f.get('airline', '')).upper()
        term = str(f.get('terminal', ''))
        pax_base = 250 if any(x in term for x in ['3', 'I', 'Intl']) else 150
        
        # 【現在の実数】
        # ここは「超厳格」に、着陸済み(landed)しかカウントしない
        if range_start <= f_time <= range_end:
            if status == 'landed':
                f['pax_estimated'] = pax_base # 実績なので満額
                unique_flights.append(f)
                if '1' in term: pax_t1 += pax_base
                elif '2' in term: pax_t2 += pax_base
                else: pax_t3 += pax_base

        # 【未来の予測】
        # 未来の予定(scheduled)に、さっき計算した「生存率」を掛ける
        if f_time > now:
            predicted_pax = int(pax_base * survival_rate)
            
            diff_h = (f_time - now).total_seconds() / 3600
            if 0 <= diff_h < 1: forecast["h1"]["pax"] += predicted_pax
            elif 1 <= diff_h < 2: forecast["h2"]["pax"] += predicted_pax
            elif 2 <= diff_h < 3: forecast["h3"]["pax"] += predicted_pax

    # 表示用コメントの作成
    rate_disp = int(survival_rate * 100)
    if survival_rate < 0.5:
        fc_status = "⚠️ 警戒"
        fc_comment = f"生存率{rate_disp}% (欠航多)"
    else:
        fc_status = "👀 通常"
        fc_comment = "通常運行中"
    
    return {
        "1号(T1南)": int(pax_t1 * 0.5), "2号(T1北)": int(pax_t1 * 0.5),
        "3号(T2)": int(pax_t2 * 0.5), "4号(T2)": int(pax_t2 * 0.5),
        "国際(T3)": pax_t3, 
        "forecast": {k: {"label": (now + timedelta(hours=int(k[1]))).strftime("%H:00〜"), 
                        "pax": v["pax"], 
                        "status": fc_status, 
                        "comment": fc_comment} 
                    for k, v in forecast.items()},
        "unique_count": len(unique_flights), 
        "flights": unique_flights
    }
