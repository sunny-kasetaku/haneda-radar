from datetime import datetime, timedelta

def analyze_demand(flights):
    # 日本時間現在時刻
    now = datetime.utcnow() + timedelta(hours=9)
    
    # -------------------------------------------------
    # 1. 時間枠ごとの集計
    # -------------------------------------------------
    # 設定値 (分)
    PAST_MINUTES = 40
    FUTURE_MINUTES = 20

    # 基準となる時刻レンジ
    start_time = now - timedelta(minutes=PAST_MINUTES)
    end_time = now + timedelta(minutes=FUTURE_MINUTES)
    
    # リアルタイム表示用データ（リスト上部用）
    filtered_flights = []
    
    # 時間別集計用（リスト下部用）
    hourly_counts = {} # {0: 150, 1: 0, 2: 250...}

    # 重複排除用のセット (便名 + 日付)
    seen_flights = set()

    for f in flights:
        # 時刻情報の取得と変換
        arr_time_str = f.get('arrival_time', '')
        if not arr_time_str: continue
        
        # ISOフォーマット (YYYY-MM-DDTHH:MM:00+00:00) を想定
        # 簡易パース
        try:
            # タイムゾーン部分(+00:00等)の処理が面倒なので、文字列カットで対応
            # AviationStackはUTCで返ってくることが多いが、+09:00前提で計算
            # ここでは単純に文字列比較用にdatetimeオブジェクト化
            # 文字列例: "2026-01-26T00:20:00+00:00" -> 前方19文字を取る
            dt_str = arr_time_str[:19] 
            f_dt = datetime.strptime(dt_str, '%Y-%m-%dT%H:%M:%S')
            
            # UTCできていればJSTに変換、JSTできていればそのまま
            # ここでは簡易的に「APIはUTC」と仮定して +9時間 するのが安全
            f_dt_jst = f_dt + timedelta(hours=9)
            
        except:
            continue

        # 重複排除（同じ便名がactiveとscheduledで二重に来た場合など）
        flight_id = f"{f.get('flight_number')}_{f_dt_jst.day}"
        if flight_id in seen_flights:
            continue
        seen_flights.add(flight_id)

        # 1. リアルタイムリストへの振り分け
        if start_time <= f_dt_jst <= end_time:
            # 推計人数の計算 (機材や航空会社からざっくり)
            pax = estimate_pax(f)
            f['pax_estimated'] = pax
            filtered_flights.append(f)

        # 2. 時間別集計へのカウント (未来3時間分)
        # 0時台、1時台、2時台... と集計する
        h = f_dt_jst.hour
        pax = estimate_pax(f)
        hourly_counts[h] = hourly_counts.get(h, 0) + pax

    # ソート (到着時間順)
    filtered_flights.sort(key=lambda x: x.get('arrival_time'))

    # -------------------------------------------------
    # 2. ターミナル別・合計需要の算出
    # -------------------------------------------------
    terminal_counts = {
        "1号(T1南)": 0, "2号(T1北)": 0,
        "3号(T2)": 0, "4号(T2)": 0,
        "国際(T3)": 0
    }
    
    for f in filtered_flights:
        t_str = str(f.get('terminal', ''))
        # 国内線(T1/T2)か国際線(T3)か、さらに航空会社で北南を分ける簡易ロジック
        airline = f.get('airline', '').lower()
        pax = f.get('pax_estimated', 0)
        
        if t_str == '3':
            terminal_counts["国際(T3)"] += pax
        elif t_str == '2':
            # T2はANA系中心だが、便宜上半分に分けるか、まとめてT2とする
            # ここでは簡易的に 3号/4号 に均等配分、あるいは航空会社で分ける
            # 今回はシンプルに全部「3号(T2)」に入れてしまうか、
            # あるいは「3号」と「4号」にランダムまたは便名偶奇で分ける等の擬似処理
            # ※本来はスポット情報が必要だがAPIにないため
            # 暫定：便名の数字が偶数なら3号、奇数なら4号（あくまで分散表示のため）
            try:
                num = int(''.join(filter(str.isdigit, f.get('flight_number', '0'))))
            except:
                num = 0
            
            if num % 2 == 0:
                terminal_counts["3号(T2)"] += pax
            else:
                terminal_counts["4号(T2)"] += pax

        elif t_str == '1':
            # T1はJAL(北)とSKY/SFJ(南)など
            # JALなら北(2号)、それ以外(SKY, SFJ)なら南(1号)という簡易分け
            if 'japan airlines' in airline or 'jal' in airline:
                terminal_counts["2号(T1北)"] += pax
            else:
                terminal_counts["1号(T1南)"] += pax
        else:
            # ターミナル不明は国際(T3)に入れておく（リスクヘッジ）
            terminal_counts["国際(T3)"] += pax

    # -------------------------------------------------
    # 3. 未来予測データの整形 (ここを修正！)
    # -------------------------------------------------
    forecast_data = {}
    
    # 【変更点】range(1, 4) -> range(0, 3)
    # これにより、現在時刻(0時)〜、1時間後(1時)〜、2時間後(2時)〜 の3つを表示
    for i in range(0, 3):
        target_h = (now.hour + i) % 24
        count = hourly_counts.get(target_h, 0)
        
        # ステータス判定
        if count >= 1000: status = "🔥 高"
        elif count >= 300: status = "👀 通常"
        else: status = "📉 低"
        
        # コメント
        if count >= 1000: comment = "確変中"
        elif count >= 300: comment = "需要あり"
        else: comment = "静か"

        key = f"h{i+1}" # h1, h2, h3 のキー名はそのまま（rendererとの互換性のため）
        forecast_data[key] = {
            "label": f"{target_h:02d}:00〜",
            "pax": count,
            "status": status,
            "comment": comment
        }

    return {
        "flights": filtered_flights,
        "unique_count": len(filtered_flights),
        "setting_past": PAST_MINUTES,
        "setting_future": FUTURE_MINUTES,
        **terminal_counts,
        "forecast": forecast_data
    }

def estimate_pax(flight):
    """
    機材情報や航空会社から乗客数をざっくり推計する
    """
    # 1. 機材情報があればそれを使う
    # AviationStackの機材情報は flight.aircraft.iata などにある場合があるが
    # 無料版だと取れないことが多い。取れたらラッキー程度の実装
    
    # ここでは簡易的に「国際線なら多め、国内線なら少なめ」
    # あるいは便名から推測（3桁は大型、4桁は小型など）
    
    # デフォルト値
    base_pax = 150
    
    # 国際線(T3)判定
    term = flight.get('terminal')
    if term == '3':
        base_pax = 250 # 国際線は大型機が多いと仮定
        
    return base_pax
