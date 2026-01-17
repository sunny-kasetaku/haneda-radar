from datetime import datetime, timedelta, timezone

def analyze_demand(flights):
    """
    重複排除、機材推計、未来予測計算を行うロジックコア。
    Tさんの固定比率を廃止し、API実数ベースで計算。
    """
    
    # 1. バケツの初期化
    pax_t1 = 0
    pax_t2 = 0
    pax_t3 = 0
    
    # 時間計算の基準（タイムゾーン対応）
    # APIはUTC(+00:00)で来るため、比較用に現在時刻もUTC基準にする
    now_utc = datetime.now(timezone.utc)
    
    # 日本時間(JST)での表示用時刻（ラベル用）
    now_jst = datetime.now()
    
    # 3時間予測用バケツ（ラベルはJSTで作成）
    forecast = {
        "h1": {"label": (now_jst + timedelta(hours=1)).strftime("%H:00〜"), "pax": 0, "status": "", "comment": ""},
        "h2": {"label": (now_jst + timedelta(hours=2)).strftime("%H:00〜"), "pax": 0, "status": "", "comment": ""},
        "h3": {"label": (now_jst + timedelta(hours=3)).strftime("%H:00〜"), "pax": 0, "status": "", "comment": ""}
    }

    # 2. 重複排除と集計ループ
    seen_vessels = set()
    unique_flights = []

    for f in flights:
        # --- A. 重複排除ロジック ---
        # 「到着時刻(分まで)」＋「出発地」をキーにして、同じならコードシェアとみなす
        t_str = str(f.get('arrival_time', ''))
        origin = f.get('origin', 'UNK')
        
        # 時刻文字列の前半(2023-10-27T12:34)までを使用
        time_key = t_str[:16] 
        vessel_key = f"{time_key}_{origin}"

        if vessel_key in seen_vessels:
            continue # 既に登録済みならスキップ（これが2万人を防ぐ壁です）

        seen_vessels.add(vessel_key)
        
        # --- B. 機材サイズと人数の推計 ---
        airline = str(f.get('airline', '')).upper()
        term = str(f.get('terminal', ''))
        
        if '3' in term or 'I' in term:
            pax = 250 # 国際線大型
        elif any(x in airline for x in ["WINGS", "J-AIR", "HAC", "AMX", "ORC", "IBEX", "COMMUTER"]):
            pax = 50  # 地方・小型（プロデューサー指摘反映）
        else:
            pax = 150 # 標準国内線

        f['pax_estimated'] = pax
        unique_flights.append(f)

        # --- C. ターミナル別集計 ---
        if '1' in term:
            pax_t1 += pax
        elif '2' in term:
            pax_t2 += pax
        else:
            pax_t3 += pax

        # --- D. 3時間予測（未来判定） ---
        try:
            # APIの時刻(ISO format)を解析
            flight_time = datetime.fromisoformat(t_str.replace('Z', '+00:00'))
            
            # 現在時刻(UTC)との差分を時間単位で計算
            diff_hours = (flight_time - now_utc).total_seconds() / 3600

            if 0 <= diff_hours < 1:
                forecast["h1"]["pax"] += pax
            elif 1 <= diff_hours < 2:
                forecast["h2"]["pax"] += pax
            elif 2 <= diff_hours < 3:
                forecast["h3"]["pax"] += pax
        except:
            pass

    # 3. 予測ステータスの判定（閾値設定）
    for k in ["h1", "h2", "h3"]:
        val = forecast[k]["pax"]
        if val >= 400:
            forecast[k]["status"] = "🚀 超高"
            forecast[k]["comment"] = "🔥 激アツ・第2波到来"
        elif val >= 200:
            forecast[k]["status"] = "⚠️ 中"
            forecast[k]["comment"] = "➡️ 需要継続中"
        else:
            forecast[k]["status"] = "👀 低"
            forecast[k]["comment"] = "⬇️ 撤収準備・待機"

    # 4. 最終結果の返却
    # Tさん比率を廃止し、不明なウィング情報は単純等分(0.5)で表示
    return {
        "1号(T1南)": int(pax_t1 * 0.5),
        "2号(T1北)": int(pax_t1 * 0.5),
        "3号(T2)":   int(pax_t2 * 0.5),
        "4号(T2)":   int(pax_t2 * 0.5),
        "国際(T3)":  pax_t3,
        "forecast": forecast,
        "unique_count": len(unique_flights),
        "flights": unique_flights
    }