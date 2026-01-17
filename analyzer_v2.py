from datetime import datetime, timedelta

def analyze_demand(flights):
    # APIから取得したデータを純粋に分析（Tさんロジック廃止）
    
    # 時間帯ごとの重み（最終的な微調整用として残すが、基本は実数ベース）
    WEIGHT_MASTER = {
        7:[2,0,1,0,8], 8:[8,9,13,4,0], 9:[10,9,16,3,1], 10:[6,8,9,4,0],
        11:[10,10,10,6,1], 12:[9,7,14,4,1], 13:[10,9,8,4,0], 14:[8,5,9,7,0],
        15:[7,7,13,3,0], 16:[7,12,10,5,2], 17:[10,7,10,4,6], 18:[10,8,11,9,1],
        19:[9,7,11,3,1], 20:[11,7,11,4,2], 21:[10,10,14,4,1], 22:[7,7,9,4,2], 23:[1,0,2,3,0]
    }

    pax_t1, pax_t2, pax_t3 = 0, 0, 0
    now = datetime.now()
    
    # 3時間予測の初期化
    forecast = {
        "h1": {"label": f"{(now + timedelta(hours=1)).hour}:00〜", "pax": 0, "status": "", "comment": ""},
        "h2": {"label": f"{(now + timedelta(hours=2)).hour}:00〜", "pax": 0, "status": "", "comment": ""},
        "h3": {"label": f"{(now + timedelta(hours=3)).hour}:00〜", "pax": 0, "status": "", "comment": ""}
    }

    seen_vessels = set() # 重複排除用
    unique_flights = []

    for f in flights:
        # 重複判定キー：到着時刻(分まで) ＋ 出発地
        # これで「コードシェア便」を1つにまとめる
        a_time_raw = str(f.get('arrival_time', ''))
        vessel_key = f"{a_time_raw[:16]}_{f.get('origin')}"
        
        if vessel_key not in seen_vessels:
            seen_vessels.add(vessel_key)
            
            # --- 機材サイズ推計 ---
            airline = str(f.get('airline', '')).upper()
            term = str(f.get('terminal', ''))
            
            if '3' in term or 'I' in term:
                pax = 250 # 国際線大型
            elif any(x in airline for x in ["ORC", "AMX", "COMMUTER"]):
                pax = 30  # 離島・超小型
            elif any(x in airline for x in ["WINGS", "J-AIR", "HAC", "IBEX"]):
                pax = 70  # 地方・小型
            else:
                pax = 150 # 標準国内線 (A320/B737/B767クラス)
            
            f['pax_estimated'] = pax
            unique_flights.append(f)
            
            # --- ターミナル集計 ---
            if '1' in term: pax_t1 += pax
            elif '2' in term: pax_t2 += pax
            else: pax_t3 += pax

            # --- 3時間予測への振り分け ---
            try:
                # ISO形式の日時文字列から時間を判定
                if 'T' in a_time_raw:
                    dt = datetime.fromisoformat(a_time_raw.replace('Z', '+00:00'))
                    # 現在時刻との差（時間単位）
                    diff = (dt.replace(tzinfo=None) - now).total_seconds() / 3600
                    
                    if 0 <= diff < 1: forecast["h1"]["pax"] += pax
                    elif 1 <= diff < 2: forecast["h2"]["pax"] += pax
                    elif 2 <= diff < 3: forecast["h3"]["pax"] += pax
            except:
                pass

    # --- 予測の判定ロジック（閾値は暫定） ---
    for key in ["h1", "h2", "h3"]:
        p = forecast[key]["pax"]
        if p >= 400:
            forecast[key]["status"] = "🚀 超高"
            forecast[key]["comment"] = "🔥 激アツ・第2波"
        elif p >= 200:
            forecast[key]["status"] = "⚠️ 中"
            forecast[key]["comment"] = "➡️ 需要継続"
        else:
            forecast[key]["status"] = "👀 低"
            forecast[key]["comment"] = "⬇️ 撤収準備・待機"

    # --- 最終集計 ---
    w = WEIGHT_MASTER.get(now.hour, [1,1,1,1,1])
    # ゼロ除算防止
    t1_w = (w[0] + w[1]) or 2
    t2_w = (w[2] + w[3] + w[4]) or 3

    return {
        "1号(T1南)": int(pax_t1 * w[0] / t1_w),
        "2号(T1北)": int(pax_t1 * w[1] / t1_w),
        "3号(T2)":   int(pax_t2 * w[2] / t2_w),
        "4号(T2)":   int(pax_t2 * w[3] / t2_w),
        "国際(T3)":  pax_t3 + int(pax_t2 * w[4] / t2_w),
        "forecast": forecast,
        "unique_count": len(unique_flights),
        "flights": unique_flights
    }