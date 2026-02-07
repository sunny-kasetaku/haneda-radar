import requests
import time
import sys
import json # [2026-02-07] 🦁 追加: ログ保存用
from datetime import datetime, timedelta

def fetch_flight_data(api_key, date_str=None):
    """
    【v24.0 Plan C (Full Fetch)】
    ・[2026-02-06] ロジック刷新。Offset 0から全件取得する「底引き網方式」へ変更。
    ・旧ロジック（v23.9c）はバックアップとしてコメントアウトで保存。
    
    【v23.6 Midnight-Bridge】API回数12回/run
    ・現在時刻に連動してOffsetを自動計算（スライド方式）。
    ・夜21時以降は「明日出発(Tomorrow)」の100件をブリッジし、0時〜1時の欠落を完全解消。
    ・サニーさんの以前の知見（出発日基準）に基づき、日付の壁を突破するロジック。
    [2026-02-06] 🦁 v23.7追記: UTC基準に同期。JST深夜のOffsetリセットを防止。
    [2026-02-06 02:40] 🦁 v23.8追記: 深夜の取りこぼしを防ぐためOffsetに上限(Cap)を設定。
    [2026-02-06 03:15] 🦁 v23.9追記: Cap700軍でも3時台を取りこぼしたため, Cap500/Depth600に拡張。
    [2026-02-06 03:30] 🦁 v23.9b追記: API回数を12回に戻すため, ActiveのDepthを500→300に削減(相殺)。
    [2026-02-06 12:50] 🦁 v23.9c追記: 午前中にOffsetが効きすぎて当日分を通り越すバグ修正。14:00まではOffset0固定。
    """
    # =========================================================================
    # ▼ [OLD LOGIC v23.9c] BACKUP (COMMENTED OUT ONLY)
    # =========================================================================
    # base_url = "http://api.aviationstack.com/v1/flights"
    # 
    # all_flights = []
    # 
    # # 時間計算
    # now_jst = datetime.utcnow() + timedelta(hours=9)
    # yesterday_jst = now_jst - timedelta(days=1)
    # yesterday_str = yesterday_jst.strftime('%Y-%m-%d')
    # 
    # # 🦁 修正: 明日の日付を計算
    # tomorrow_jst = now_jst + timedelta(days=1)
    # tomorrow_str = tomorrow_jst.strftime('%Y-%m-%d')
    # 
    # # 🦁 修正: 日付指定がない場合は今日とする
    # # target_date = date_str if date_str else now_jst.strftime('%Y-%m-%d')
    # 
    # # [2026-02-06] 🦁 追記: APIのUTC基準に合わせるための補正ロジック
    # # APIの日付更新はUTC 0時(日本時間9時)のため、JST 0時の切り替わりでOffsetをリセットさせない
    # now_utc = datetime.utcnow()
    # target_date = date_str if date_str else now_utc.strftime('%Y-%m-%d') # APIが現在「当日」と認識している日付
    # yesterday_str = (now_utc - timedelta(days=1)).strftime('%Y-%m-%d')
    # # [2026-02-06] 終
    # 
    # # 🦁 修正: 全自動スライド・ロジック (CVT方式)
    # current_hour = now_jst.hour
    # base_offset = 0
    # 
    # # if 0 <= current_hour < 21:
    # #     # 【昼間スライドモード】時刻に合わせて網を自動でスライドさせる
    # #     sched_sort = 'scheduled_arrival'
    # #     base_offset = max(0, (current_hour - 2) * 55)
    # # else:
    # #     # 【深夜逆算モード】21時以降は、24時から遡って拾うのが最も確実
    # #     sched_sort = 'scheduled_arrival.desc'
    # #     base_offset = 0
    # 
    # # [2026-02-06] 🦁 追記: UTC基準のOffset計算 (JST深夜의 データ消失を防止)
    # # UTC基準(朝9時=0時)でOffsetを計算することで、24時間連続したスライドを実現する
    # current_hour_utc = now_utc.hour
    # 
    # # [2026-02-06 02:50] 🦁 修正: Offset上限(Cap)とソート順の強制
    # # 計算値が900を超えると、リスト末尾にある深夜便(JL78等)をスキップしてしまうため、上限を700に固定する
    # # また、深夜帯もスライド方式を維持するため、JST側で設定された .desc を昇順に上書きする
    # # calc_offset = current_hour_utc * 55
    # # base_offset = min(700, max(0, calc_offset)) 
    # 
    # # [2026-02-06 03:15] 🦁 再修正: 700だと04:00着(IT216)をまたぐため、500まで下げる
    # # base_offset = min(500, max(0, calc_offset)) 
    # 
    # # [2026-02-06 12:50] 🦁 v23.9c 修正: 午前中のスライド禁止 (Morning-Safety)
    # # UTC 0時〜5時（JST 9:00〜14:00）は、リストがまだ短いのでOffsetをかけると当日分を通り越してしまう。
    # # よって、JST 14:00までは強制的にOffset 0とし、それ以降からスライドを開始する。
    # safe_slide_hour = max(0, current_hour_utc - 5) # UTC 5時までは0、6時から1,2...と増える
    # calc_offset = safe_slide_hour * 55
    # base_offset = min(500, calc_offset) # 上限は500のまま維持
    # # [2026-02-06 12:50] 修正終了
    # 
    # sched_sort = 'scheduled_arrival'
    # # [2026-02-06] 終
    # 
    # # 深夜21時〜翌9時の間、Offsetがリセットされるのを防ぐための最終防衛ライン
    # if current_hour >= 21 or current_hour < 9:
    #     # 夜間は「今日(UTC)」の後半を狙い撃つため、Offsetを固定気味に維持
    #     # Scheduled(400件)で「今日(UTC)」の終わり=JST 09:00までを確実にカバー
    #     pass 
    # # [2026-02-06] 終
    # 
    # print(f"DEBUG: Start API Fetch v23.9c Morning-Safety. Hour_JST={current_hour}, Offset={base_offset}", file=sys.stderr)
    # 
    # # 🦁 修正：戦略リストを動的に構築
    # strategies = [
    #     # 1. Active: 今飛んでいる便（絶対削らない）
    #     # [2026-02-06 03:30] 🦁 コメントアウト: コスト削減のため300に減らす(-2回)
    #     # {'desc': '1. Active', 'params': {'flight_status': 'active', 'sort': sched_sort, 'flight_date': target_date}, 'max_depth': 500, 'use_offset': False},
    #     
    #     # [2026-02-06 03:30] 🦁 追記: 12回/run維持のためActiveを縮小
    #     {'desc': '1. Active', 'params': {'flight_status': 'active', 'sort': sched_sort, 'flight_date': target_date}, 'max_depth': 300, 'use_offset': False},
    #     
    #     # 2. Landed: 着いたばかりの便（振り返り用）
    #     {'desc': '2. Landed', 'params': {'flight_status': 'landed', 'sort': 'scheduled_arrival.desc', 'flight_date': target_date}, 'max_depth': 200, 'use_offset': False},
    #     
    #     # 3. Scheduled: これからの便（スライド方式適用）
    #     # [2026-02-06 03:15] 🦁 コメントアウト: 深夜便捕捉のため拡張
    #     # {'desc': '3. Scheduled', 'params': {'flight_status': 'scheduled', 'sort': sched_sort, 'flight_date': target_date}, 'max_depth': 400, 'use_offset': True},
    #     
    #     # [2026-02-06 03:15] 🦁 追記: Offsetを下げた分、Depthを600に拡張(+2回)
    #     {'desc': '3. Scheduled', 'params': {'flight_status': 'scheduled', 'sort': sched_sort, 'flight_date': target_date}, 'max_depth': 600, 'use_offset': True},
    # ]
    # 
    # # 🦁 4番目の枠（100件分）を, サニーさんのロジックで昼夜切り替え
    # # [2026-02-06] 🦁 修正：JST深夜0時〜9時の間も「明日(APIにとっての当日)」を拾い続けるよう条件を拡張
    # if current_hour >= 21 or current_hour < 9:
    #     # 夜間：日付の壁を越えるため「明日出発」の便を拾う
    #     strategies.append({'desc': '4. Tomorrow', 'params': {'flight_date': tomorrow_str, 'sort': 'scheduled_arrival'}, 'max_depth': 100, 'use_offset': False})
    # else:
    #     # 昼間：昨日分の振り返りを入れる
    #     strategies.append({'desc': '4. Yesterday', 'params': {'flight_date': yesterday_str, 'sort': 'scheduled_arrival.desc'}, 'max_depth': 100, 'use_offset': False})
    # # [2026-02-06] 修正終了
    # 
    # for strat in strategies:
    #     if strat.get('use_offset'):
    #         current_offset = base_offset
    #     else:
    #         current_offset = 0
    #         
    #     fetched_count = 0
    #     target_depth = strat['max_depth']
    #     
    #     while fetched_count < target_depth:
    #         params = {
    #             'access_key': api_key,
    #             'arr_iata': 'HND',
    #             'limit': 100, 
    #             'offset': current_offset
    #         }
    #         params.update(strat['params'])
    #         
    #         try:
    #             print(f"DEBUG: Fetching [{strat['desc']}] offset={current_offset} date={strat['params'].get('flight_date')}...", file=sys.stderr)
    #             
    #             response = requests.get(base_url, params=params, timeout=30)
    #             response.raise_for_status()
    #             data = response.json()
    #             raw_data = data.get('data', [])
    #             
    #             if not raw_data:
    #                 break
    #             
    #             for f in raw_data:
    #                 info = extract_flight_info(f)
    #                 if info:
    #                     same_flight_index = -1
    #                     for i, existing in enumerate(all_flights):
    #                         if existing['flight_number'] == info['flight_number']:
    #                             same_flight_index = i
    #                             break
    #                     
    #                     if same_flight_index != -1:
    #                         all_flights[same_flight_index] = info
    #                         continue
    # 
    #                     duplicate_index = -1
    #                     for i, existing in enumerate(all_flights):
    #                         if (existing['arrival_time'] == info['arrival_time'] and 
    #                             existing['terminal'] == info['terminal'] and 
    #                             existing['origin_iata'] == info['origin_iata']):
    #                             duplicate_index = i
    #                             break
    #                     
    #                     if duplicate_index != -1:
    #                         existing_flight = all_flights[duplicate_index]
    #                         is_new_japanese = info['flight_number'].startswith(('JL', 'NH'))
    #                         is_existing_japanese = existing_flight['flight_number'].startswith(('JL', 'NH'))
    #                         
    #                         if is_new_japanese and not is_existing_japanese:
    #                             all_flights[duplicate_index] = info
    #                         continue
    # 
    #                     all_flights.append(info)
    #             
    #             got_num = len(raw_data)
    #             current_offset += got_num
    #             fetched_count += got_num
    #             
    #             if got_num < 100:
    #                 break
    #             
    #             time.sleep(0.5)
    # 
    #         except Exception as e:
    #             print(f"Error fetching flights: {e}", file=sys.stderr)
    #             break

    # =========================================================================
    # ▼ [NEW LOGIC v24.0] Plan C: Full Fetch (Bottom Trawling)
    # =========================================================================
    print(f"DEBUG: Start API Fetch v24.0 Plan C (Full Fetch)", file=sys.stderr)
    
    base_url = "http://api.aviationstack.com/v1/flights"
    all_flights = []
    
    # 日付計算（日付指定がない場合のみ使用）
    now_utc = datetime.utcnow()
    # target_date = date_str if date_str else now_utc.strftime('%Y-%m-%d')

    offset = 0
    limit = 100
    has_more = True
    SAFETY_BREAK = 6000 # ループ暴走防止用
    
    # [2026-02-07] 🦁 追加: 生ログ保存用のバッファ
    raw_log_buffer = []

    while has_more:
        # パラメータ: 単純にoffset 0から順番に全件取る
        params = {
            'access_key': api_key,
            'arr_iata': 'HND',
            'limit': limit,
            'offset': offset
        }
        
        # 日付指定があればparamsに追加（基本はNoneでAPI任せ=全件）
        if date_str:
            params['flight_date'] = date_str

        try:
            print(f"DEBUG: Fetching [Plan C] offset={offset}...", file=sys.stderr)
            
            response = requests.get(base_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            raw_data = data.get('data', [])
            
            # [2026-02-07] 🦁 追加: 生データをバッファに追加
            raw_log_buffer.extend(raw_data)

            # データが尽きたら終了
            if not raw_data:
                print(f"✅ Data End. Total fetched: {len(all_flights)}", file=sys.stderr)
                has_more = False
                break

            # === サニーさん仕様の重複排除・優先順位ロジック (完全移植) ===
            for f in raw_data:
                info = extract_flight_info(f)
                if info:
                    # 1. 完全に同一の便名があれば上書き (Update)
                    same_flight_index = -1
                    for i, existing in enumerate(all_flights):
                        if existing['flight_number'] == info['flight_number']:
                            same_flight_index = i
                            break
                    
                    if same_flight_index != -1:
                        all_flights[same_flight_index] = info
                        continue

                    # 2. コードシェア判定 (時刻・ターミナル・出発地が同じ)
                    duplicate_index = -1
                    for i, existing in enumerate(all_flights):
                        if (existing['arrival_time'] == info['arrival_time'] and 
                            existing['terminal'] == info['terminal'] and 
                            existing['origin_iata'] == info['origin_iata']):
                            duplicate_index = i
                            break
                    
                    if duplicate_index != -1:
                        # 日本の航空会社(JL, NH)を優先してリストに残す
                        existing_flight = all_flights[duplicate_index]
                        is_new_japanese = info['flight_number'].startswith(('JL', 'NH'))
                        is_existing_japanese = existing_flight['flight_number'].startswith(('JL', 'NH'))
                        
                        # 新しい方が日本勢で、既存が海外勢なら入れ替える
                        if is_new_japanese and not is_existing_japanese:
                            all_flights[duplicate_index] = info
                        # 既存が日本勢なら何もしない(キープ)
                        continue

                    # 3. 新規追加
                    all_flights.append(info)
            # ==========================================================

            # 次のページへ
            got_num = len(raw_data)
            offset += limit
            
            if offset >= SAFETY_BREAK:
                print("⚠️ Safety Break: Limit reached.", file=sys.stderr)
                break
            
            time.sleep(0.5)

        except Exception as e:
            print(f"Error fetching flights: {e}", file=sys.stderr)
            break
            
    # [2026-02-07] 🦁 追加: 生ログをファイルに書き出し (上書き)
    try:
        log_filename = "latest_api_log.json"
        with open(log_filename, 'w', encoding='utf-8') as f:
            json.dump(raw_log_buffer, f, indent=2, ensure_ascii=False)
        print(f"✅ Raw Log Saved: {log_filename} ({len(raw_log_buffer)} records)", file=sys.stderr)
    except Exception as e:
        print(f"⚠️ Log Save Error: {e}", file=sys.stderr)

    return all_flights

def extract_flight_info(flight):
    arr = flight.get('arrival', {})
    airline = flight.get('airline', {})
    flight_data = flight.get('flight', {})
    dep = flight.get('departure', {})
    aircraft = flight.get('aircraft', {})
    aircraft_iata = aircraft.get('iata', 'none') if aircraft else 'none'
    
    s_time = arr.get('scheduled')
    e_time = arr.get('estimated')
    a_time = arr.get('actual')
    
    time_candidates = [t for t in [s_time, e_time, a_time] if t]
    if not time_candidates: return None
    
    arrival_time = max(time_candidates)
    scheduled_time = s_time 
    
    # [2026-02-07] 🦁 追加: JS側での時差計算(UTC/JST)の狂いを防ぐため、タイムゾーン表記を強制除去
    if scheduled_time: scheduled_time = str(scheduled_time).split("+")[0].replace("Z", "")

    # [2026-02-07] 🦁 追加: 遅延(delay)を考慮した「真の到着時刻」計算ロジック
    # APIのdelayフィールド(分)が存在する場合、定刻に加算してarrival_timeを補正する
    delay_min = arr.get('delay')
    if delay_min and isinstance(delay_min, int) and delay_min > 0 and s_time:
        try:
            # s_time가 "2026-02-07T12:00:00+00:00" のような形式を想定し、Zやタイムゾーンを除去して計算
            clean_time = s_time.replace("Z", "").split("+")[0]
            dt = datetime.fromisoformat(clean_time)
            dt_delayed = dt + timedelta(minutes=delay_min)
            # 簡易的にISO形式に戻す (元の文字列に+が含まれていれば考慮すべきだが、ここでは比較用として単純化)
            arrival_time = dt_delayed.isoformat()
        except Exception:
            # 計算失敗時は、元の max(time_candidates) の結果を採用する (何もしない)
            pass

    term = arr.get('terminal')
    f_num_str = str(flight_data.get('number', ''))
    airline_iata = airline.get('iata', '??')
    origin_iata = dep.get('iata', 'UNK')

    if term in ["I", "INT", "i", "int"]:
        term = "3"

    if term is None or term == "" or term == "None":
        domestic_carriers = ["JL", "NH", "BC", "7G", "6J", "HD", "NU", "FW"]
        
        if airline_iata in domestic_carriers:
            if airline_iata in ["NH", "HD"]: 
                term = "2"
            elif airline_iata == "JL" and (f_num_str.startswith("5") or f_num_str.startswith("8") or len(f_num_str) <= 3):
                term = "3"
            else: 
                term = "1"
        else:
            term = "3"

    # 🦁 [2026-02-07] 追加：4号振り分けと人数精緻化ロジック
    e_type = f"その他(T{term})"
    if term == "1":
        e_type = "1号(T1南)"
        if airline_iata == "JL" and (f_num_str.startswith("5") or f_num_str.startswith("1")):
            e_type = "2号(T1北)"
    elif term == "2":
        north_codes = ["CTS", "HKD", "AKJ", "MMB", "KUH", "OBO", "WKJ", "SHB", "AOJ", "MSJ", "AXT", "ODA", "SYO", "HNA", "FKS", "GAJ"]
        if origin_iata in north_codes or (arr.get('iata') == "HND" and flight.get('airline', {}).get('name') == "International"):
            e_type = "4号(T2)"
        else:
            e_type = "3号(T2)"
    elif term == "3":
        e_type = "国際(T3)"

    p_count = 150
    pax_m = {"B773":400, "B772":400, "B77L":400, "B77W":400, "A359":320, "B789":320, "B781":320, "B788":240, "B763":240, "A333":240, "B738":136, "A321":150, "A320":130}
    if aircraft_iata in pax_m: p_count = pax_m[aircraft_iata]
    elif term == "3": p_count = 250

    # =========================================================================
    # [2026-02-07] 🦁 v24.2 付け加え：辞書による最終防衛ライン (データ欠落対策)
    # 既存のロジックをすり抜けた場合のみ, ここで空港コード辞書を使って補完する。
    # =========================================================================
    safe_origin = str(origin_iata).strip().upper()
    
    # 1. 4号(T2)への再振り分け（北海道・東北便の徹底合流）
    if term == "2" and e_type != "4号(T2)":
        north_airports = ["CTS", "HKD", "AKJ", "MMB", "KUH", "OBO", "WKJ", "SHB", "AOJ", "MSJ", "AXT", "ODA", "SYO", "HNA", "FKS", "GAJ"]
        if safe_origin in north_airports:
            e_type = "4号(T2)"

    # 2. 人数補正（aircraft: null 対策の辞書判定）
    if p_count == 150:
        # 北海道・東北・主要幹線は大型機が多いため、機材不明でも推計を底上げする
        major_trunk_lines = ["FUK", "ITM", "OKA", "CTS", "HIJ", "KGS"]
        if e_type == "4号(T2)": 
            p_count = 240 # 函館・新千歳などの4号便
        elif safe_origin in major_trunk_lines:
            p_count = 280 # 福岡・伊丹・沖縄などの3号幹線
        elif term == "3":
            p_count = 250 # 国際線

    # =========================================================================
    # [2026-02-07] 🦁 v24.7 付け加え：機材不明（null）時の「出身地別」機材推計辞書
    # サニーさんの仰る通り「コードではなく辞書」で機材サイズを判定する最終検問所。
    # =========================================================================
    airport_full_name = str(dep.get('airport', 'Unknown')).upper()
    
    # 【救済辞書：名前】地名が含まれていれば強制的に 4号(T2) へ引きずり戻す
    rescue_dict = ["HAKODATE", "函館", "CHITOSE", "千歳", "SAPPORO", "札幌", "ASAHIKAWA", "旭川", "AOMORI", "青森", "AKITA", "秋田"]
    if term == "2" and any(kw in airport_full_name for kw in rescue_dict):
        e_type = "4号(T2)"
        # 4号(北日本)かつ機材不明なら、中型機サイズ(240名)に決定
        if p_count == 150: p_count = 240

    # 【機材推計辞書：路線別】機材がnullでも、出身地が幹線なら大型機サイズに決定
    # 福岡、伊丹、那覇などの「名前」が入っていれば、150名を280〜300名へ上書き
    trunk_rescue_dict = ["FUKUOKA", "福岡", "ITAMI", "伊丹", "NAHA", "那覇", "OKINAWA", "沖縄"]
    if p_count == 150:
        if any(kw in airport_full_name for kw in trunk_rescue_dict):
            p_count = 280 # 幹線大型機推計

    # 表示地名の日本語化辞書 (イベント情報修正)
    origin_jp_map = {"GIMPO": "ソウル(金浦)", "INCHEON": "ソウル(仁川)", "松山": "台北(松山)", "TAIPEI": "台北(松山)", "PUDONG": "上海(浦東)", "NEW CHITOSE": "新千歳", "HAKODATE": "函館"}
    final_origin = dep.get('airport', 'Unknown')
    for eng, jap in origin_jp_map.items():
        if eng in str(final_origin).upper(): 
            final_origin = jap
            break

    # スプリングジャパン(IJ)の3分割入力対応（国際枠へ強制）
    if airline_iata == "IJ":
        term = "3"
        e_type = "国際(T3)"
        if p_count == 150: p_count = 180

    # =========================================================================
    # [2026-02-07] 🦁 v24.13 最終付け足し：判定漏れ都市の救済と表示日本語化の補完
    # 既存のロジック・リストには一切触れず、不足分をここで「足し算」して最終確定させます。
    # =========================================================================
    if p_count == 150:
        # 北日本の追加キーワード救済（既存のrescue_dictを補完）
        v24_north_extra = ["MEMANBETSU", "女満別", "KUSHIRO", "釧路", "WAKKANAI", "稚内", "OBIHIRO", "帯広", "MISAWA", "三沢"]
        if any(kw in airport_full_name for kw in v24_north_extra):
            e_type, p_count = "4号(T2)", 240
        # 幹線の追加キーワード救済（既存のtrunk_rescue_dictを補完）
        v24_trunk_extra = ["KAGOSHIMA", "鹿児島", "HIROSHIMA", "広島", "KUMAMOTO", "熊本", "MATSUYAMA", "松山", "OKAYAMA", "岡山"]
        if any(kw in airport_full_name for kw in v24_trunk_extra):
            p_count = 280

    # 表示地名の最終翻訳（イベント表示用）
    # return行の赤（削除）を避けるため、ここでfinal_origin変数を最終補正します
    v24_extra_jp = {"FUKUOKA": "福岡", "ITAMI": "伊丹", "NAHA": "那覇", "OKINAWA": "沖縄", "KAGOSHIMA": "鹿児島", "HIROSHIMA": "広島", "SAPPORO": "札幌"}
    for k, v in v24_extra_jp.items():
        if k in airport_full_name:
            final_origin = v
            break

    # =========================================================================
    # [2026-02-07] 🦁 v24.14 最終決定：名前ベースの「出口・人数」絶対確定ロジック
    # 「if p_count == 150」の関所を撤去し、地名が合致すれば人数に関わらず 100% 4号(T2) や 幹線大型機 に仕分けます。
    # =========================================================================
    # 判定用の名前文字列（日本語と英語の両方に対応）
    check_name_final = (str(final_origin) + str(dep.get('airport', ''))).upper()
    
    # 1. 【北日本便】を強制的に4号(T2)へ、人数も最低240名へ引き上げる
    north_target_list = ["函館", "HAKODATE", "千歳", "CHITOSE", "札幌", "SAPPORO", "旭川", "ASAHIKAWA", "青森", "AOMORI", "秋田", "AKITA", "女満別", "MEMANBETSU", "釧路", "KUSHIRO", "稚内", "WAKKANAI", "帯広", "OBIHIRO", "三沢", "MISAWA"]
    if term == "2" and any(kw in check_name_final for kw in north_target_list):
        e_type = "4号(T2)"
        if p_count < 240: p_count = 240

    # 2. 【主要幹線便】を強制的に最低280名へ引き上げる
    trunk_target_list = ["福岡", "FUKUOKA", "伊丹", "ITAMI", "那覇", "NAHA", "沖縄", "OKINAWA", "鹿児島", "KAGOSHIMA", "広島", "HIROSHIMA", "熊本", "KUMAMOTO", "松山", "MATSUYAMA", "岡山", "OKAYAMA"]
    if any(kw in check_name_final for kw in trunk_target_list):
        if p_count < 280: p_count = 280

    # =========================================================================
    # [2026-02-07] 🦁 v24.15 最終ロック：else漏れを許さない「完全指名制」
    # 既存の判定に頼らず、ターミナル番号（3, 2, 1）ごとに正解の出口を「指名」します。
    # =========================================================================
    # 判定用の全キーワード（日本語名・空港コード・API名を合体）
    f_key = (str(final_origin) + str(dep.get('airport', '')) + str(origin_iata)).upper()

    # 第3ターミナルの場合：100%「国際(T3)」として固定
    if term == "3":
        e_type = "国際(T3)"
        if airline_iata == "IJ": p_count = max(p_count, 180)
        else: p_count = max(p_count, 250)

    # 第2ターミナルの場合：4号か3号かを「指名」で分ける
    elif term == "2":
        # 4号指名リスト：北日本キーワード または T2到着の国際線
        is_n = any(kw in f_key for kw in ["函館","HAKODATE","千歳","CHITOSE","札幌","SAPPORO","旭川","ASAHIKAWA","青森","AOMORI","秋田","AKITA","女満別","MEMANBETSU","釧路","KUSHIRO","三沢","MISAWA","KUH","HKD","CTS","AKJ","MMB"])
        # 国内幹線リストに含まれないコード（かつ空でない）ならT2国際線(4号)とみなす
        is_i = (origin_iata != "UNK" and origin_iata != "" and origin_iata not in ["FUK","ITM","OKA","HIJ","KGS","MYJ","OKJ","KMQ","TKS","KUM","NGS","OIT","KMI","UKB","NGO","KIX","TOTTORI","YONAGO","IWAKUNI","TOYAMA","SHONAI","NOTO","HACHIJOJIMA","IZUMO"])
        
        if is_n or is_i:
            e_type = "4号(T2)"
            p_count = max(p_count, 240)
        else:
            # それ以外（西日本幹線・地方便）は3号(T2)として指名
            e_type = "3号(T2)"
            if any(kw in f_seed for kw in ["FUK","ITM","OKA","HIJ","KGS","FUKUOKA","ITAMI","NAHA","沖縄","OKINAWA"]):
                p_count = max(p_count, 280)

    return {
        "flight_number": f"{airline_iata}{f_num_str}",
        "airline": airline.get('name', 'Unknown'),
        "origin": final_origin, # 🦁 修正: 翻訳後の日本語名を使用
        "origin_iata": origin_iata,
        "terminal": str(term),
        "exit_type": e_type,
        "pax": p_count,
        "arrival_time": arrival_time,
        "scheduled_time": scheduled_time,
        "status": flight.get('flight_status', 'unknown'),
        "aircraft": aircraft_iata
    }