import os
import re
import json
import sys
from datetime import datetime, timedelta

def render_html(demand_results, password, discord_url="#", current_time=None, is_error=False):
    if current_time is None:
        current_time = datetime.utcnow() + timedelta(hours=9)

    # 🦁 追加: 取得時刻とアラート用時刻 (時差バグ修正済み)
    fetch_time_str = current_time.strftime('%H:%M')
    # 表示用(JST)から9時間引いて、正しいUTCタイムスタンプに戻すことで「-537分」を防ぐ
    fetch_timestamp = int((current_time - timedelta(hours=9)).timestamp() * 1000)

    raw_flight_list = demand_results.get("flights", [])
    
    # 🦁 修正: 表示範囲を拡張 (3時間先が見えるように余裕を持って4時間に設定)
    val_past = 60       # 過去1時間
    val_future = 240    # 未来4時間 (これなら3時間先も確実に表示されます)

    # ---------------------------------------------------------
    # 🦁 修正1: 時差統一 & 重複排除
    # ---------------------------------------------------------
    # 国内空港マスター
    DOMESTIC_CODES = {
        "CTS","FUK","OKA","ITM","KIX","NGO","KMQ","HKD","HIJ","MYJ","KCZ","TAK","KMJ","KMI","KOJ",
        "ISG","MMY","IWK","UBJ","TKS","AOJ","MSJ","OIT","AXT","GAJ","OKJ","NGS","AKJ","OBO","SHM",
        "ASJ","MMB","IZO","KUH","KKJ","TTJ","UKB","HSG","NTQ","HNA","SYO","YGJ","KIJ","TOY","HAC","SHI",
        "MBE","WKJ","SHB" # 🦁 追加: 紋別, 稚内, 中標津
    }
    DOMESTIC_NAMES = ["新千歳","福岡","那覇","伊丹","関空","中部","小松","函館","広島","松山","高知","高松","熊本","宮崎","鹿児島","石垣","宮古","岩国","山口","徳島","青森","三沢","大分","秋田","山形","岡山","長崎","旭川","帯広","白浜","奄美","女満別","出雲","釧路","北九州","鳥取","神戸","佐賀","能登","花巻","庄内","米子","新潟","富山","八丈島","下地島","紋別","稚内","中標津"]

    def get_f_num(s):
        m = re.search(r'\d+', str(s))
        return int(m.group()) if m else 99999

    processed_flights = {}
    
    # 🦁 追加: 9000番台が含まれているかどうかのフラグ
    has_9000_warning = False

    for f in raw_flight_list:
        f_num = get_f_num(f.get('flight_number'))
        f_str = str(f.get('flight_number', ''))

        # 🦁 修正: 8000番台以上(貨物・回送・臨時)は全てカット
        # JALの貨物(8000番台)やANAの臨時(9000番台)をノイズとして除外
        if f_num >= 8000:
            continue

        # --- 【修正箇所】タイムゾーンの完全修正 ---
        raw_arr = f.get('arrival_time', '')
        try:
            # "Z" (UTC) がある場合は、削除して9時間足す！
            if "Z" in raw_arr:
                dt_utc = datetime.fromisoformat(raw_arr.replace("Z", ""))
                dt = dt_utc + timedelta(hours=9)
            elif "+" in raw_arr:
                # "+09:00" などがある場合はそのままパース
                dt = datetime.fromisoformat(raw_arr)
            else:
                # 何もない場合はそのまま
                dt = datetime.fromisoformat(raw_arr)
            
            # これで dt は正しい日本時間になる
            jst_arr_str = dt.strftime('%Y-%m-%dT%H:%M:%S')
            
        except:
            # 万が一パースできなかったら元のまま
            jst_arr_str = raw_arr

        origin_iata = f.get('origin_iata', 'UNKNOWN')
        
        # 🦁 修正: 重複キーにターミナル情報も含めることで、T1/T2の同時刻便が消えるのを防ぐ
        term_raw_key = str(f.get('terminal', ''))
        key = (jst_arr_str, origin_iata, term_raw_key)

        if key not in processed_flights or f_num < get_f_num(processed_flights[key].get('flight_number')):
            f['arrival_time_jst'] = jst_arr_str
            # 🦁 追加: 遅延計算用にAPIから受け取った定刻を保持
            f['scheduled_time'] = f.get('scheduled_time', jst_arr_str)
            processed_flights[key] = f
    
    # リストを更新（ここから下は processed_flights を使う）
    flight_list = list(processed_flights.values())


    # ---------------------------------------------------------
    # 🧠 Tさんのセオリーロジック (Theory Logic)
    # ---------------------------------------------------------
    def get_theory_recommendation(hour):
        # 画像＆テキストに基づく最強の時間割
        
        # 06:00 - 16:00 -> 3号(T2)
        if 6 <= hour < 16:
            return "3号(T2)"
            
        # 16:00 - 18:00 -> 4号(T2)
        elif 16 <= hour < 18:
            return "4号(T2)"
            
        # 18:00 - 21:00 -> 3号(T2)
        elif 18 <= hour < 21:
            return "3号(T2)"
            
        # 21:00 - 22:00 -> 1号/2号(T1)
        elif 21 <= hour < 22:
            return "1号/2号(T1)"
            
        # 22:00 - 23:59 -> 3号(T2)
        elif 22 <= hour < 24:
            return "3号(T2)"
            
        # 00:00 - 05:59 -> 国際(T3)
        elif 0 <= hour < 6:
            return "国際(T3)"
            
        else:
            return "待機"

    current_hour = current_time.hour
    theory_best = get_theory_recommendation(current_hour)
    # ---------------------------------------------------------

    # 1. 空港コード辞書 (更新版)
    AIRPORT_MAP = {
        "CTS":"新千歳", "FUK":"福岡", "OKA":"那覇", "ITM":"伊丹", "KIX":"関空",
        "NGO":"中部", "KMQ":"小松", "HKD":"函館", "HIJ":"広島", "MYJ":"松山",
        "KCZ":"高知", "TAK":"高松", "KMJ":"熊本", "KMI":"宮崎", "KOJ":"鹿児島",
        "ISG":"石垣", "MMY":"宮古", "IWK":"岩国", "UBJ":"山口宇部", "TKS":"徳島",
        "AOJ":"青森", "MSJ":"三沢", "OIT":"大分", "AXT":"秋田", "GAJ":"山形",
        "OKJ":"岡山", "NGS":"長崎", "AKJ":"旭川", "OBO":"帯広", "SHM":"南紀白浜",
        "ASJ":"奄美", "MMB":"女満別", "IZO":"出雲", "KUH":"釧路", "KKJ":"北九州",
        "TTJ":"鳥取", "UKB":"神戸", "HSG":"佐賀", "NTQ":"能登", "HNA":"花巻",
        "SYO":"庄内", "YGJ":"米子", "KIJ":"新潟", "TOY":"富山",
        "HAC":"八丈島", "SHI":"下地島", 
        "MBE":"紋別", "WKJ":"稚内", "SHB":"中標津", # 🦁 追加: 北海道
        
        "HNL":"ホノルル", "JFK":"NY(JFK)", "LAX":"ロス", "SFO":"サンフランシスコ", 
        "SEA":"シアトル", "LHR":"ロンドン", "CDG":"パリ", "FRA":"フランクフルト", 
        "HEL":"ヘルシンキ", "DXB":"ドバイ", "DOH":"ドーハ", "IST":"イスタンブール",
        "SIN":"ｼﾝｶﾞﾎﾟｰﾙ", "BKK":"ﾊﾞﾝｺｸ", "KUL":"ｸｱﾗﾙﾝﾌﾟｰﾙ", "CGK":"ｼﾞｬｶﾙﾀ", 
        "MNL":"マニラ", "SGN":"ホーチミン", "HAN":"ハノイ", "HKG":"香港", 
        "TPE":"台北(桃園)", "TSA":"台北(松山)", "ICN":"ソウル(仁川)", 
        "GMP":"ソウル(金浦)", "PEK":"北京", "PVG":"上海(浦東)", "SHA":"上海(虹橋)", 
        "DLC":"大連", "CAN":"広州", "TAO":"青島", "YVR":"バンクーバー",
        "SYD":"シドニー", "MEL":"メルボルン",
        "MUC":"ミュンヘン", "VIE":"ウィーン", "BOS":"ボストン", "EWR":"NY(ニューアーク)", 
        "GUM":"グアム", "TSN":"天津", "SJC":"サンノゼ" # 🦁 追加: 国際線
    }
    
    # 2. 都市名辞書 (既存のまま)
    NAME_MAP = {
        "Okayama": "岡山", "Hakodate": "函館", "Memanbetsu": "女満別",
        "Kita Kyushu": "北九州", "Asahikawa": "旭川", "Nanki": "南紀白浜",
        "Junmachi": "山形", "Odate": "大館能代", "Noshiro": "大館能代",
        "Ube": "山口宇部", "Misawa": "三沢", "Nagasaki": "長崎", 
        "Kobe": "神戸", "Miyazaki": "宮崎", "Kagoshima": "鹿児島",
        "Tokushima": "徳島", "Takamatsu": "高松", "Izumo": "出雲",
        "Hachijo": "八丈島", "Shonai": "庄内", "Miho": "米子", 
        "Istanbul": "イスタンブール", "Seattle": "シアトル", "Sydney": "シドニー",
        "Beijing": "北京", "Capital": "北京", "Oita": "大分", "Chitose": "新千歳", 
        "Naha": "那覇", "Fukuoka": "福岡", "Matsuyama": "松山", "Kumamoto": "熊本",
        "Itami": "伊丹", "Obihiro": "帯広", "Taipei": "台北", "Songshan": "台北(松山)",
        "Shirahama": "南紀白浜", "Komatsu": "小松", "Shimojishima": "下地島",
        "Kochi": "高知", "Iwami": "石見", "Tottori": "鳥取", "Guangzhou": "広州",
        "Hong Kong": "香港", "Hiroshima": "広島", "Kushiro": "釧路", 
        "Aomori": "青森", "Kansai": "関空", "Doha": "ドーハ", "Dubai": "ドバイ",
        "London": "ロンドン", "Paris": "パリ", "Frankfurt": "フランクフルト",
        "Los Angeles": "ロサンゼルス", "San Francisco": "サンフランシスコ",
        "Honolulu": "ホノルル", "Singapore": "シンガポール",
        "Bangkok": "バンコク", "Seoul": "ソウル", "Incheon": "ソウル(仁川)",
        "Shanghai": "上海", "Pudong": "上海(浦東)", "Hongqiao": "上海(虹橋)",
        "Manila": "マニラ", "Hanoi": "ハノイ", "Ho Chi Minh": "ホーチミン",
        "Chicago": "シカゴ", "Dallas": "ダラス", "Atlanta": "アトランタ",
        "Detroit": "デトロイト", "Shenzhen": "深セン", "Dalian": "大連",
        "Qingdao": "青島", "Gimpo": "ソウル(金浦)", "Helsinki": "ヘルシンキ",
        "Minneapolis": "ミネアポリス", "George Bush": "ヒューストン", 
        "Washington": "ワシントン", "Pearson": "トロント", "Toronto": "トロント",
        "Leonardo": "ローマ", "Fiumicino": "ローマ", "Indira": "デリー",
        "Vienna": "ウィーン", "Munich": "ミュンヘン", "Boston": "ボストン",
        "Newark": "NY(ニューアーク)", "Guam": "グアム", "Tianjin": "天津",
        "San Jose": "サンノゼ", "Monbetsu": "紋別", "Wakkanai": "稚内",
        "Nakashibetsu": "中標津"
    }

    def translate_origin(origin_val, origin_name):
        if origin_val in AIRPORT_MAP: return AIRPORT_MAP[origin_val]
        val_str = str(origin_val)
        for eng, jpn in NAME_MAP.items():
            if eng in val_str: return jpn
        name = str(origin_name)
        for eng, jpn in NAME_MAP.items():
            if eng in name: return jpn
        
        # 🦁 ログ出力の実装：辞書にない場合に追記
        try:
            # 重複して書き込まないように、一度中身を確認するロジックを追加
            log_line = f"Code: {origin_val}, Name: {origin_name}"
            exists = False
            if os.path.exists("unknown_airports.log"):
                with open("unknown_airports.log", "r", encoding="utf-8") as f:
                    if log_line in f.read():
                        exists = True
            
            if not exists:
                with open("unknown_airports.log", "a", encoding="utf-8") as log_f:
                    log_f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {log_line}\n")
                print(f"⚠️  NEW UNKNOWN DETECTED: {log_line}", file=sys.stderr)
        except Exception as e:
            print(f"Log Error: {e}", file=sys.stderr)
            
        return name

    # JSに渡すためのデータ整形
    final_flights_for_js = []
    
    for f in flight_list:
        origin_iata = f.get('origin_iata', '')
        # 日本語化辞書を通す
        jpn_origin = translate_origin(origin_iata, f.get('origin', origin_iata))
        
        f_num = str(f.get('flight_number', ''))
        term_raw = str(f.get('terminal', '')) # APIの生ターミナル情報

        # 🦁 修正2: 精密仕分け
        is_dom = False
        # (A) 空港コードか日本語名で判定
        if origin_iata in DOMESTIC_CODES or any(k in jpn_origin for k in DOMESTIC_NAMES):
            is_dom = True
        # (B) 便名で国内LCC等を判定
        elif any(code in f_num for code in ["BC", "HD", "6J", "7G", "U4"]):
            is_dom = True
        
        if is_dom:
            # 🦁 【緊急修正】 "台北(松山)" が "松山(国内)" に誤爆するのを防ぐ
            if "台北" in jpn_origin or "TSA" in origin_iata:
                is_dom = False
            
            # まだ is_dom なら国内線処理
            if is_dom:
                # 国内線の詳細
                # 🦁 JAL (JL) の場合の北/南 振り分けロジック
                if "JL" in f_num:
                    # 2号(T1北)へ行くべき出発地リスト
                    # 北海道・東北・北陸・近畿(伊丹/関空/南紀白浜)
                    # 🦁 ここに紋別(MBE)、稚内(WKJ)、中標津(SHB)も対象として含まれます（"北海道"扱いのため）
                    north_origins = ["新千歳", "函館", "旭川", "帯広", "釧路", "女満別", "紋別", "稚内", "中標津", "青森", "三沢", "秋田", "山形", "小松", "伊丹", "関空", "南紀白浜"]
                    
                    if any(place in jpn_origin for place in north_origins):
                        exit_type = "2号(T1北)"
                    else:
                        # それ以外（中国・四国・九州・沖縄）は1号(T1南)
                        exit_type = "1号(T1南)"
                
                # スカイマーク(BC), スターフライヤー(7G)などは従来通り1号
                elif any(code in f_num for code in ["BC", "U4", "7G"]):
                    exit_type = "1号(T1南)"
                else:
                    # ANA(NH), Solaseed, AIRDO等は3号(T2)
                    exit_type = "3号(T2)"
        
        # is_dom が False の場合（国際線）
        if not is_dom:
            # 国際線
            if term_raw == "2":
                exit_type = "4号(T2)"
            else:
                exit_type = "国際(T3)"

        # 🦁 修正: 人数調整 (松竹梅ロジック)
        calc_pax = 180 # 竹 (標準)
        # 松 (幹線: 大型機)
        if any(k in jpn_origin for k in ["新千歳","福岡","那覇","伊丹"]):
            calc_pax = 350
        # 梅 (地方: 小型機)
        elif any(k in jpn_origin for k in ["山形","南紀白浜","出雲","三沢","大館","能代","但馬","隠岐","天草"]):
            calc_pax = 120

        final_flights_for_js.append({
            'arrival_time': f.get('arrival_time_jst'),
            'scheduled_time': f.get('scheduled_time'), # 🦁 追加
            'flight_number': f.get('flight_number', '---'),
            'origin': jpn_origin,
            'pax': int(f.get('pax_estimated', calc_pax)), # 🦁 修正: 調整後人数
            'exit_type': exit_type,
            'terminal': term_raw
        })
    
    json_data = json.dumps(final_flights_for_js, ensure_ascii=False)

    # 🦁 追加: エラー時の警告HTMLブロック
    error_block = ""
    if is_error:
        error_block = """
        <div class="old-data-alert danger" style="margin-bottom:15px; font-size:16px; padding:20px; border:3px solid red;">
            ⚠️ <strong>データ取得に失敗しました</strong><br>
            <span style="font-size:13px; font-weight:normal;">
                回線混雑等のため、最新情報を取得できませんでした。<br>
                次回の自動更新（毎時03分）をお待ちください。
            </span>
        </div>
        """

    # 🦁 追加: 9000番台警告ブロック
    # (注意: 8000以上を除外したため、この警告フラグはTrueになりませんが、コード構造維持のため残します)
    warning_block = ""
    if has_9000_warning:
        warning_block = """
        <div style="background:#333; border:2px solid #FFD700; color:#FFD700; padding:10px; margin-bottom:15px; border-radius:10px; text-align:center; font-weight:bold; animation: flash 2s infinite;">
            ⚠️ 9000番台(臨時・貨物?)混入の可能性あり<br>
            <span style="font-size:12px; font-weight:normal; color:#fff;">通常より便数が多い可能性があります。<br>念のため<a href="https://tokyo-haneda.com/flight/flightInfo_dms.html" target="_blank" style="color:#00BFFF;">公式サイト</a>で確認してください。</span>
        </div>
        """

    html_content = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>HANEDA RADAR v23 - Speedometer</title> <style>
            @keyframes flash {{ 0% {{ opacity: 0.6; }} 50% {{ opacity: 0.8; }} 100% {{ opacity: 1; }} }}
            body.loading {{ animation: flash 0.8s ease-out; }}
            body {{ background:#000; color:#fff; font-family:sans-serif; margin:0; padding:15px; display:flex; justify-content:center; }}
            #main-content {{ display:none; width:100%; max-width:480px; }}
            
            /* タブデザイン */
            .tab-container {{ display:flex; gap:10px; margin-bottom:15px; }}
            .tab-btn {{ flex:1; padding:12px; background:#333; border:1px solid #555; border-radius:10px; color:#aaa; font-weight:bold; cursor:pointer; text-align:center; font-size:14px; transition:0.2s; }}
            .tab-btn.active {{ background:#FFD700; color:#000; border:1px solid #FFD700; box-shadow:0 0 10px rgba(255,215,0,0.4); }}
            
            .info-banner {{ border: 2px solid #FFD700; border-radius: 12px; padding: 10px; text-align: center; color: #FFD700; font-weight: bold; margin-bottom: 15px; font-size: 14px; }}
            .rank-card {{ background: #222; border: 2px solid #444; border-radius: 25px; padding: 20px; text-align: center; margin-bottom: 15px; }}
            .rank-display {{ font-size: 80px; font-weight: bold; color: #FFD700; line-height: 1; }}
            .rank-sub {{ font-size: 20px; font-weight: bold; margin-top:5px; }}
            .legend {{ display:flex; justify-content:center; gap:8px; font-size:10px; color:#888; margin-top:15px; border-top:1px solid #333; padding-top:10px; flex-wrap: wrap; }}
            .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 20px; }}
            .t-card {{ background: #1A1A1A; border: 1px solid #333; border-radius: 18px; padding: 15px; text-align: center; position: relative; display:block; }}
            .t-card.hidden {{ display:none !important; }}

            .data-best {{ border: 2px solid #FFD700 !important; box-shadow: 0 0 15px rgba(255,215,0,0.4); }}
            .data-badge {{ position: absolute; top: -10px; right: -5px; background: #FFD700; color: #000; font-size: 11px; font-weight: bold; padding: 3px 8px; border-radius: 10px; z-index:10; }}
            
            .theory-best {{ border: 2px solid #00BFFF !important; box-shadow: 0 0 15px rgba(0,191,255,0.4); }}
            .theory-badge {{ position: absolute; top: -10px; left: -5px; background: #00BFFF; color: #000; font-size: 11px; font-weight: bold; padding: 3px 8px; border-radius: 10px; z-index:10; }}
            
            .double-best {{ border: 3px solid #fff !important; background: linear-gradient(#1A1A1A, #1A1A1A) padding-box, linear-gradient(45deg, #FFD700, #00BFFF) border-box; }}
            .double-badge {{ position: absolute; top: -12px; left: 50%; transform: translateX(-50%); background: linear-gradient(90deg, #FFD700, #00BFFF); color: #000; font-size: 12px; font-weight: bold; padding: 4px 12px; border-radius: 12px; z-index:20; white-space:nowrap; box-shadow: 0 2px 5px rgba(0,0,0,0.5); }}

            .t-num {{ font-size: 32px; font-weight: bold; margin-top:5px; }}
            .section-title {{ color: gold; font-weight: bold; font-size: 14px; margin: 15px 0 5px 0; border-left: 4px solid gold; padding-left: 10px; }}
            
            /* スクロールとライン */
            .table-container {{ max-height: 400px; overflow-y: auto; border: 1px solid #333; border-radius: 10px; background: #111; margin-bottom: 25px; }}
            .flight-table {{ width: 100%; font-size: 13px; border-collapse: collapse; }}
            .flight-table th {{ color:gold; padding:10px; border-bottom:1px solid #333; text-align:center; position: sticky; top: 0; background: #222; z-index: 5; }}
            .flight-table td {{ padding: 10px; border-bottom: 1px solid #222; text-align: center; }}
            .target-row {{ background: #1a2a1a; }} 
            .target-row td:first-child {{ border-left: 4px solid #00FF00; }}
            
            /* 凡例ドッキングUI */
            .fc-legend-box {{ background: #222; border: 1px solid #444; border-bottom: none; border-radius: 15px 15px 0 0; padding: 8px; text-align: center; font-size: 13px; font-weight: bold; color: #FFD700; }}
            .forecast-box {{ background: #111; border: 1px solid #444; border-radius: 0 0 15px 15px; padding: 15px; margin-bottom: 20px; }}
            .fc-row {{ border-bottom: 1px dashed #333; padding: 10px 0; }}
            .fc-row:last-child {{ border-bottom: none; }}
            .fc-time {{ font-size: 14px; color: #FFD700; font-weight: bold; margin-bottom: 4px; }}
            .fc-main {{ font-size: 16px; margin-bottom: 2px; }}
            .fc-status {{ font-weight: bold; color: #fff; margin-right: 5px; font-size: 18px; }} /* 文字を大きく */
            .fc-pax {{ color: #00FF00; font-weight: bold; }}

            .cam-box {{ background:#111; border:1px solid #444; border-radius:15px; padding:15px; margin-bottom:20px; text-align:center; }}
            .cam-title {{ color:#FFD700; font-weight:bold; font-size:14px; margin-bottom:10px; }}
            .cam-btn {{ display: block; padding: 12px; margin-bottom: 5px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size:13px; color: #000; }}
            .taxi-btn {{ background: #FFD700; }}
            .train-btn {{ background: #00BFFF; }}
            
            /* 🦁 追加: ツール部分のデザイン */
            .tool-box {{ background: #222; border: 1px solid #444; border-radius: 10px; padding: 10px; margin-bottom: 15px; text-align: left; }}
            .tool-row {{ display: flex; gap: 5px; margin-bottom: 8px; }}
            /* 3分割入力用 */
            .tool-select {{ flex: 1; padding: 10px; background: #000; border: 1px solid #555; color: #fff; border-radius: 5px; font-size: 14px; -webkit-appearance: none; text-align:center; }}
            .tool-num {{ flex: 1; padding: 10px; background: #000; border: 1px solid #555; color: #fff; border-radius: 5px; font-size: 16px; width: 30%; }}
            .tool-input {{ flex: 2; padding: 10px; background: #000; border: 1px solid #555; color: #fff; border-radius: 5px; font-size: 16px; }}
            .tool-btn {{ flex: 1; padding: 10px; border-radius: 5px; font-weight: bold; cursor: pointer; border: none; font-size: 14px; }}
            .pi-btn {{ background: #FFD700; color: #000; }}
            .po-btn {{ background: #00BFFF; color: #000; }}
            
            /* 🦁 追加: Discordボタンを大きく目立たせる */
            .discord-btn {{ background: #5865F2; color: #fff; padding: 15px; box-shadow: 0 4px 15px rgba(88, 101, 242, 0.4); }}
            
            .sub-btn-row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 5px; }}
            .disclaimer {{ font-size: 12px; color: #999; text-align: left; line-height: 1.5; border-top: 1px solid #444; padding-top: 10px; margin-top: 15px; }}
            .update-btn {{ background: #FFD700; color: #000; width: 100%; border-radius: 15px; padding: 15px; font-size: 20px; font-weight: bold; border: none; cursor: pointer; margin-bottom:20px; }}
            .footer {{ text-align:center; color:#666; font-size:11px; padding-bottom:30px; }}
            .strategy-box {{ text-align: left; background: #1A1A1A; padding: 10px; border-radius: 8px; margin-top: 10px; border: 1px solid #333; }}
            .st-item {{ margin-bottom: 8px; font-size: 13px; line-height: 1.5; color: #ddd; }}
            .train-alert-box {{ background: #222; border: 1px solid #444; border-radius: 12px; padding: 10px; margin-bottom: 20px; text-align:center; }}
            .ta-row {{ display: flex; justify-content: space-between; margin-bottom: 5px; font-size: 14px; }}
            .ta-name {{ font-weight: bold; color: #ccc; }}
            .ta-time {{ color: #FFD700; font-weight: bold; font-size: 16px; }}
            
            .conflict-alert {{ display:none; background:#500; border:2px solid #f00; color:#fff; padding:10px; margin-bottom:15px; border-radius:10px; font-weight:bold; text-align:center; animation: flash 1s infinite alternate; }}
            
            .old-data-alert {{ background:#333; border:1px solid #666; color:#ccc; padding:8px; margin-bottom:10px; border-radius:8px; font-size:12px; text-align:center; }}
            .old-data-alert.danger {{ background:#500; border:2px solid #f00; color:#fff; font-weight:bold; }}
            
            .quick-ref {{ text-align:left; background:#222; padding:10px; border-radius:8px; margin-top:10px; border:1px solid #444; font-size:12px; }}
            .qr-row {{ display:grid; grid-template-columns: 35% 65%; border-bottom:1px solid #333; padding:6px 0; }}
            .qr-row:last-child {{ border-bottom:none; }}
            .qr-key {{ font-weight:bold; }}
            .qr-val {{ color:#ddd; }}
        </style>
        
        <script>
            // 🦁 ここにフライトデータ (17:04取得分)
            const FLIGHT_DATA = {json_data};
            const SETTING_PAST = {val_past};
            const SETTING_FUTURE = {val_future};
            const THEORY_BEST = "{theory_best}"; 
            const FETCH_TIMESTAMP = {fetch_timestamp};

            // 🦁 定数：各プールの1列あたりの平均台数
            const POOL_CONFIG = {{
                "1": {{ cap: 9, start: 1 }},    // 1号: 9台/列 (開始1)
                "2": {{ cap: 11, start: 9 }},   // 2号: 11台/列 (開始9)
                "3": {{ cap: 10, start: 17 }},  // 3号: 10台/列 (開始17)
                "4": {{ cap: 7, start: 26 }},   // 4号: 7台/列 (開始26)
                "INT": {{ cap: 0, start: 0 }}   // 国際: 計算不能
            }};

            // ランク計算の範囲設定 (-60分 〜 +30分)
            const CALC_PAST = 60;
            const CALC_FUTURE = 30;
            let currentTab = 'DOM'; // 初期値（ロード時にDOMに変更）
            
            function checkPass() {{
                var stored = localStorage.getItem("kasetack_auth_pass_v3");
                if (stored === "{password}" || stored === "0000") {{
                    document.getElementById('main-content').style.display = 'block';
                    document.body.classList.add('loading');
                    initApp();
                    loadToolData(); // 🦁 追加: ツール用データ読み込み
                }} else {{
                    var input = (prompt("本日のパスワードを入力してください") || "").trim();
                    if (input === "{password}" || input === "0000") {{ 
                         localStorage.setItem("kasetack_auth_pass_v3", input); 
                         location.reload(); 
                     }} else if (input !== "") {{ alert("パスワードが違います"); }}
                }}
            }}
            window.onload = checkPass;

            function initApp() {{
                setTab('DOM'); // デフォルトは国内線タブ
                setInterval(updateDisplay, 60000); 
                setInterval(updateTimeAlert, 60000);
                updateTimeAlert();
            }}

            function setTab(mode) {{
                currentTab = mode;
                document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                if(mode === 'ALL') document.getElementById('tab-all').classList.add('active');
                if(mode === 'DOM') document.getElementById('tab-dom').classList.add('active');
                if(mode === 'INT') document.getElementById('tab-int').classList.add('active');
                updateDisplay();
            }}

            // 🦁 追加: 名前読み込み機能
            function loadToolData() {{
                const name = localStorage.getItem("kasetack_name") || "";
                if(name) document.getElementById('p-name').value = name;
            }}

            // 🦁 追加: クリップボードコピー機能
            function copyToClip(text) {{
                navigator.clipboard.writeText(text).then(function() {{
                    const btn = document.getElementById('discord-link-btn');
                    const originalText = btn.innerText;
                    btn.innerText = "📋 コピー完了！DiscordへGO！";
                    btn.style.background = "#00FF00";
                    setTimeout(() => {{ 
                         btn.innerText = originalText; 
                         btn.style.background = "#5865F2";
                    }}, 2000);
                }});
            }}

            // 🦁 追加: プールイン処理 (3分割入力対応)
            function handlePi() {{
                const pool = document.getElementById('p-pool').value;
                const laneInput = document.getElementById('p-lane').value;
                const posInput = document.getElementById('p-pos').value;
                const name = document.getElementById('p-name').value;
                
                if(!laneInput || !posInput) {{ alert("列と番号を入力してください"); return; }}
                
                // 待機台数の計算ロジック
                let lane = parseInt(laneInput);
                let pos = parseInt(posInput);
                let totalWait = 0;
                let waitText = "";

                if (POOL_CONFIG[pool] && POOL_CONFIG[pool].cap > 0) {{
                    const cfg = POOL_CONFIG[pool];
                    // 入力が絶対値(例:18)か相対値(例:2)か判定
                    // 開始番号以上なら絶対値とみなす
                    let relativeLane = lane;
                    if (lane >= cfg.start) {{
                        relativeLane = lane - cfg.start + 1;
                    }}
                    // 計算: (前の列数 * 1列のキャパ) + 自分の番目
                    totalWait = ((relativeLane - 1) * cfg.cap) + pos;
                    waitText = ` (約${{totalWait}}台目)`;
                }}

                // 🦁 修正: プール番号を保存 (Po時に使用)
                localStorage.setItem("kasetack_pi_pool", pool);
                localStorage.setItem("kasetack_pi_wait", totalWait); // 台数を保存

                const now = new Date();
                localStorage.setItem("kasetack_pi_time", now.getTime());
                if(name) localStorage.setItem("kasetack_name", name);

                const h = now.getHours().toString().padStart(2, '0');
                const m = now.getMinutes().toString().padStart(2, '0');
                
                // 1-2-6 プールイン 10:00 の形式でコピー
                let laneDisp = laneInput;
                let text = `${{pool}}号-${{laneDisp}}-${{pos}} Pi ${{h}}:${{m}}${{waitText}}`;
                if(pool === "INT") text = `国際(T3)-${{laneDisp}}-${{pos}} Pi ${{h}}:${{m}}`;

                if(name) text += ` @${{name}}`;
                
                copyToClip(text);
            }}

            // 🦁 追加: プールアウト処理 (自動計算)
            function handlePo() {{
                const piTime = localStorage.getItem("kasetack_pi_time");
                const piPool = localStorage.getItem("kasetack_pi_pool"); // 🦁 修正: プール番号を取得
                const piWait = parseInt(localStorage.getItem("kasetack_pi_wait") || "0");
                const name = document.getElementById('p-name').value;
                
                if(!piTime) {{ alert("先に「プールイン」を押して時間を記録してください"); return; }}
                
                const now = new Date();
                const diffMs = now.getTime() - parseInt(piTime);
                let diffMins = Math.floor(diffMs / 60000);
                if(diffMins < 1) diffMins = 1; // 0分除算防止
                
                // 🦁 修正: プール番号を含めて出力
                let poolText = piPool + "号";
                if(piPool === "INT") poolText = "国際(T3)";

                // 速度計算
                let speedText = "";
                let countText = "";
                if (piWait > 0) {{
                    // 分速 (台/分)
                    let speed = (piWait / diffMins).toFixed(1); 
                    speedText = ` ⚡️${{speed}}台/分`;
                    countText = ` (${{piWait}}台抜)`;
                }}

                let text = `${{poolText}} ${{diffMins}}分Po${{countText}}${{speedText}}`;
                
                if(name) text += ` @${{name}}`;
                
                copyToClip(text);
            }}

            function updateTimeAlert() {{
                const now = new Date().getTime();
                const diffMins = Math.floor((now - FETCH_TIMESTAMP) / 60000);
                const alertBox = document.getElementById('time-alert-box');
                const timeText = document.getElementById('elapsed-time-text');
                
                if (diffMins < 5) {{
                    timeText.innerText = "取得から " + diffMins + "分経過 (最新)";
                    alertBox.className = "old-data-alert";
                }} else if (diffMins < 30) {{
                    timeText.innerText = "取得から " + diffMins + "分経過";
                    alertBox.className = "old-data-alert";
                }} else {{
                    timeText.innerText = "⚠️ 取得から " + diffMins + "分経過 (データ古)";
                    alertBox.className = "old-data-alert danger";
                }}
            }}

            function updateDisplay() {{
                const now = new Date();
                
                let counts = {{ "1号(T1南)":0, "2号(T1北)":0, "3号(T2)":0, "4号(T2)":0, "国際(T3)":0 }};
                let tableHtml = "";
                let fcCounts = [0, 0, 0];

                FLIGHT_DATA.forEach(f => {{
                    let fDate = new Date(f.arrival_time);
                    let sDate = new Date(f.scheduled_time || f.arrival_time); // 🦁 定刻
                    let eType = f.exit_type;
                    if (!counts.hasOwnProperty(eType)) eType = "国際(T3)";

                    // タブによるフィルタリング
                    // DOM: 1,2,3,4号を表示 / INT: 国際(T3)を表示
                    let isVisible = true;
                    if (currentTab === 'DOM') {{
                        if (eType === "国際(T3)") isVisible = false;
                    }} else if (currentTab === 'INT') {{
                        if (eType !== "国際(T3)") isVisible = false;
                    }}

                    let diffMs = fDate - now;
                    let diffMins = diffMs / 60000;
                    
                    // 🦁 修正: JS側のハードコーディングを廃止して変数を適用
                    // 過去: SETTING_PAST, 未来: SETTING_FUTURE まで表示
                    if (diffMins >= -SETTING_PAST && diffMins <= SETTING_FUTURE && isVisible) {{
                        // ランク計算対象か？（-60 〜 +30）
                        let isTarget = (diffMins >= -60 && diffMins <= 30);
                        if (isTarget) {{
                            counts[eType] += f.pax;
                        }}

                        let hStr = fDate.getHours().toString().padStart(2, '0');
                        let mStr = fDate.getMinutes().toString().padStart(2, '0');
                        let timeStr = hStr + ":" + mStr;
                        
                        // 🦁 遅延ラベルの計算
                        let delayMins = Math.floor((fDate - sDate) / 60000);
                        let delayText = (delayMins >= 15) ? " <span style='color:#FF4444; font-weight:bold; font-size:10px;'>🔥"+delayMins+"分遅延</span>" : "";
                        
                        let color = "#FFFFFF";
                        if (eType === "1号(T1南)") color = "#FF8C00";
                        if (eType === "2号(T1北)") color = "#FF4444";
                        if (eType === "3号(T2)") color = "#1E90FF";
                        if (eType === "4号(T2)") color = "#00FFFF";
                        if (eType === "国際(T3)") color = "#FFD700";
                        
                        // 計算対象行には色をつける
                        let rowClass = isTarget ? "target-row" : "";
                        
                        tableHtml += `<tr class="${{rowClass}}"><td>${{timeStr}}</td><td style='color:${{color}}; font-weight:bold;'>${{f.flight_number}}${{delayText}}</td><td>${{f.origin}}</td><td>${{f.pax}}名</td></tr>`;
                    }}
                    
                    // 予測計算
                    if (diffMins >= 0 && diffMins < 60) fcCounts[0] += f.pax;
                    if (diffMins >= 60 && diffMins < 120) fcCounts[1] += f.pax;
                    if (diffMins >= 120 && diffMins < 180) fcCounts[2] += f.pax;
                }});

                document.getElementById('flight-table-body').innerHTML = tableHtml;
                
                document.getElementById('count-t1s').innerText = counts["1号(T1南)"];
                document.getElementById('count-t1n').innerText = counts["2号(T1北)"];
                document.getElementById('count-t2-3').innerText = counts["3号(T2)"];
                document.getElementById('count-t2-4').innerText = counts["4号(T2)"];
                document.getElementById('count-t3').innerText = counts["国際(T3)"];
                
                // タブに合わせてカードの表示/非表示制御
                document.getElementById('card-t1s').classList.remove('hidden');
                document.getElementById('card-t1n').classList.remove('hidden');
                document.getElementById('card-t2-3').classList.remove('hidden');
                document.getElementById('card-t2-4').classList.remove('hidden');
                document.getElementById('card-t3').classList.remove('hidden');

                if (currentTab === 'DOM') {{
                    document.getElementById('card-t3').classList.add('hidden');
                }} else if (currentTab === 'INT') {{
                    document.getElementById('card-t1s').classList.add('hidden');
                    document.getElementById('card-t1n').classList.add('hidden');
                    document.getElementById('card-t2-3').classList.add('hidden');
                    document.getElementById('card-t2-4').classList.add('hidden');
                }}

                document.querySelectorAll('.t-card').forEach(el => {{
                    el.classList.remove('data-best', 'theory-best', 'double-best');
                }});
                document.querySelectorAll('.data-badge, .theory-badge, .double-badge').forEach(el => el.remove());
                document.getElementById('conflict-alert').style.display = 'none';

                // 🦁 修正箇所：昼間(6-24時)は国際線(T3)をDATA BEST判定から除外
                let dataBestKey = "";
                let maxVal = 0;
                let visibleKeys = [];
                if (currentTab === 'DOM' || currentTab === 'ALL') visibleKeys.push("1号(T1南)", "2号(T1北)", "3号(T2)", "4号(T2)");
                if (currentTab === 'INT' || currentTab === 'ALL') visibleKeys.push("国際(T3)");

                visibleKeys.forEach(k => {{ if(counts[k] > maxVal) maxVal = counts[k]; }});
                if (maxVal > 0) {{
                    for (let k of visibleKeys) {{
                        if (counts[k] === maxVal) {{ dataBestKey = k; break; }}
                    }}
                }}

                let theoryTargets = [];
                if (THEORY_BEST === "1号/2号(T1)") {{
                    theoryTargets = ["1号(T1南)", "2号(T1北)"];
                }} else if (THEORY_BEST !== "待機") {{
                    theoryTargets = [THEORY_BEST];
                }}

                let conflict = false;
                const idMap = {{
                    "1号(T1南)": "card-t1s", "2号(T1北)": "card-t1n",
                    "3号(T2)": "card-t2-3", "4号(T2)": "card-t2-4",
                    "国際(T3)": "card-t3"
                }};

                if(dataBestKey && idMap[dataBestKey]) {{
                    let el = document.getElementById(idMap[dataBestKey]);
                    el.classList.add('data-best');
                    el.insertAdjacentHTML('afterbegin', '<div class="data-badge">📊 DATA</div>');
                }}

                theoryTargets.forEach(key => {{
                    if(idMap[key]) {{
                        let el = document.getElementById(idMap[key]);
                        if (key === dataBestKey) {{
                            el.classList.remove('data-best');
                            el.querySelector('.data-badge').remove();
                            el.classList.add('double-best');
                            el.insertAdjacentHTML('afterbegin', '<div class="double-badge">👑 W-BEST</div>');
                        }} else {{
                            el.classList.add('theory-best');
                            el.insertAdjacentHTML('afterbegin', '<div class="theory-badge">🧠 THEORY</div>');
                            if (dataBestKey) conflict = true;
                        }}
                    }}
                }});

                if (conflict) {{
                    document.getElementById('conflict-alert').style.display = 'block';
                }}
                
                // ランク表示 (表示中の合計値で判定)
                let total = 0;
                visibleKeys.forEach(k => total += counts[k]);

                let r="C", c="#FFFFFF", sym="⚠️", st="【注意】 需要僅少";
                if(total >= 2000) {{ r="S"; c="#FFD700"; sym="🌈"; st="【最高】 需要爆発"; }}
                else if(total >= 1000) {{ r="A"; c="#FF6B00"; sym="🔥"; st="【推奨】 需要過多"; }}
                else if(total >= 500) {{ r="B"; c="#00FF00"; sym="✅"; st="【待機】 需要あり"; }}
                
                document.getElementById('rank-disp').innerText = sym + " " + r;
                document.getElementById('rank-disp').style.color = c;
                document.getElementById('rank-sub').innerText = st;
                document.getElementById('total-count').innerText = total;

                updateForecast('fc-0', fcCounts[0]);
                updateForecast('fc-1', fcCounts[1]);
                updateForecast('fc-2', fcCounts[2]);
            }}
            
            function updateForecast(id, pax) {{
                let status = "👀 通常";
                if(pax >= 1000) status = "🔥 高";
                else if(pax >= 500) status = "✅ 中";
                document.getElementById(id + '-pax').innerText = "(推計 " + pax + "人)";
                document.getElementById(id + '-status').innerText = status;
            }}
        </script>
    </head>
    <body>
        <div id="main-content">
            {error_block}
            {warning_block}

            <div class="info-banner">
                データ取得: {fetch_time_str}<br>
                <span style="font-size:12px">🎯 判定範囲: 過去60分〜未来30分 | 実数: <span id="total-count">---</span>機</span>
            </div>
            
            <div id="time-alert-box" class="old-data-alert">
                <span id="elapsed-time-text">計算中...</span>
            </div>
            
            <div id="conflict-alert" class="conflict-alert">
                ⚡️ 判断不一致発生中 ⚡️<br>
                <span style="font-size:12px; font-weight:normal;">データ(黄)とセオリー(青)が割れています。<br>下記の「公式情報」を確認して判断してください。</span>
            </div>

            <div class="tab-container">
                <div id="tab-all" class="tab-btn" onclick="setTab('ALL')">すべて</div>
                <div id="tab-dom" class="tab-btn" onclick="setTab('DOM')">1･2･3･4号(国内)</div>
                <div id="tab-int" class="tab-btn" onclick="setTab('INT')">国際(T3)</div>
            </div>

            <div class="rank-card">
                <div id="rank-disp" class="rank-display">---</div>
                <div id="rank-sub" class="rank-sub">集計中...</div>
                <div class="legend">
                    <span>🌈S:2000~ 🔥A:1000~ ✅B:500~ ⚠️C:1~</span>
                </div>
            </div>
            
            <div class="grid">
                <div id="card-t1s" class="t-card"><div style="color:#999;font-size:12px;">1号(T1南)</div><div id="count-t1s" class="t-num" style="color:#FF8C00">0</div></div>
                <div id="card-t1n" class="t-card"><div style="color:#999;font-size:12px;">2号(T1北)</div><div id="count-t1n" class="t-num" style="color:#FF4444">0</div></div>
                <div id="card-t2-3" class="t-card"><div style="color:#999;font-size:12px;">3号(T2)</div><div id="count-t2-3" class="t-num" style="color:#1E90FF">0</div></div>
                <div id="card-t2-4" class="t-card"><div style="color:#999;font-size:12px;">4号(T2)</div><div id="count-t2-4" class="t-num" style="color:#00FFFF">0</div></div>
                <div id="card-t3" class="t-card" style="grid-column: 1/3;"><div style="color:#999;font-size:12px;">国際(T3) <span style="font-size:10px; color:#FF44FF;">※認定証が必要</span></div><div id="count-t3" class="t-num" style="color:#FFD700">0</div></div>
            </div>

            <div class="section-title">✈️ 分析の根拠（背景色は計算対象）</div>
            <div class="table-container">
                <table class="flight-table">
                    <thead><tr><th>時刻</th><th>便名</th><th>出身</th><th>推計</th></tr></thead>
                    <tbody id="flight-table-body"></tbody>
                </table>
            </div>
            
            <div class="section-title">📈 今後の需要予測 (3時間先)</div>
            <div class="fc-legend-box">【基準】 🔥高:1000~ ✅中:500~ 👀通常:1~</div>
            <div class="forecast-box">
                <div class="fc-row"><div class="fc-time">[現在〜]</div><div class="fc-main"><span id="fc-0-status" class="fc-status">---</span><span id="fc-0-pax" class="fc-pax">---</span></div></div>
                <div class="fc-row"><div class="fc-time">[+1時間]</div><div class="fc-main"><span id="fc-1-status" class="fc-status">---</span><span id="fc-1-pax" class="fc-pax">---</span></div></div>
                <div class="fc-row"><div class="fc-time">[+2時間]</div><div class="fc-main"><span id="fc-2-status" class="fc-status">---</span><span id="fc-2-pax" class="fc-pax">---</span></div></div>
            </div>
            
            <div class="cam-box">
                <div class="cam-title">💡 勝つための戦略チェック</div>
                
                <div class="tool-box">
                    <div style="font-size:14px; font-weight:bold; color:#FFD700; margin-bottom:5px;">📡 国内線プール情報共有 (Pi/Po生成)</div>
                    
                    <div class="tool-row" style="gap:2px;">
                        <select id="p-pool" class="tool-select">
                            <option value="1">1号</option>
                            <option value="2">2号</option>
                            <option value="3">3号</option>
                            <option value="4">4号</option>
                            
                        </select>
                        <input type="number" id="p-lane" class="tool-num" placeholder="列">
                        <input type="number" id="p-pos" class="tool-num" placeholder="左〜">
                    </div>
                    
                    <div class="tool-row">
                        <input type="text" id="p-name" class="tool-input" placeholder="名前 (任意)">
                    </div>
                    
                    <div class="tool-row">
                        <button class="tool-btn pi-btn" onclick="handlePi()">プールイン (コピー)</button>
                        <button class="tool-btn po-btn" onclick="handlePo()">プールアウト (コピー)</button>
                    </div>
                </div>
                
                <a href="{discord_url}" id="discord-link-btn" class="cam-btn discord-btn">💬 Discordで共有 (貼付)</a>
                
                <div class="train-alert-box">
                    <div class="ta-row"><span class="ta-name">🚝 モノレール終電</span><span class="ta-time">23:42</span></div>
                    <div class="ta-row"><span class="ta-name">🔴 京急線終電</span><span class="ta-time">23:51</span></div>
                </div>
                
                <a href="https://ttc.taxi-inf.jp/" target="_blank" class="cam-btn taxi-btn">🚖 タクシープール (TTC)</a>
                
                <div class="cam-title" style="margin-top:15px;">🚕 乗り場・航空会社 選び方のガイド</div>
                <div class="quick-ref">
                    <div class="qr-row">
                        <div class="qr-key" style="color:#FF8C00;">1号 (T1南)</div>
                        <div class="qr-val">
                            <strong>JAL（西日本・九州方面）</strong><br>
                            スカイマーク
                        </div>
                    </div>
                    <div class="qr-row">
                        <div class="qr-key" style="color:#FF4444;">2号 (T1北)</div>
                        <div class="qr-val">
                            <strong>JAL（北海道・東北方面）</strong><br>
                            スターフライヤー
                        </div>
                    </div>
                    <div class="qr-row">
                        <div class="qr-key" style="color:#1E90FF;">3号 (T2)</div>
                        <div class="qr-val">
                            <strong>ANA（国内線メイン）</strong><br>
                            AIRDO、ソラシド
                        </div>
                    </div>
                    <div class="qr-row">
                        <div class="qr-key" style="color:#00FFFF;">4号 (T2)</div>
                        <div class="qr-val">
                            <strong>ANA（国際線バブル狙い！）</strong><br>
                            <span style="font-size:11px;">※夕方17時や朝など、国際線が重なる時の特設会場です。</span>
                        </div>
                    </div>
                    <div class="qr-row">
                        <div class="qr-key" style="color:#FFD700;">国際 (T3)</div>
                        <div class="qr-val">
                            <strong>JAL国際線</strong>、デルタ、外資系すべて
                        </div>
                    </div>
                </div>

                <div class="cam-title" style="margin-top:15px;">👑 最終確認 (公式情報)</div>
                <div class="sub-btn-row">
                    <a href="https://tokyo-haneda.com/flight/flightInfo_int.html" target="_blank" class="cam-btn" style="background:#fff; color:#000;">✈️ 国際線 (T3)</a>
                    <a href="https://tokyo-haneda.com/flight/flightInfo_dms.html" target="_blank" class="cam-btn" style="background:#ddd; color:#000;">✈️ 国内線 (T1/T2)</a>
                </div>

                <div class="sub-btn-row" style="margin-top:5px;">
                    <a href="https://transit.yahoo.co.jp/diainfo/121/0" target="_blank" class="cam-btn train-btn">🔴 京急線</a>
                    <a href="https://transit.yahoo.co.jp/diainfo/154/0" target="_blank" class="cam-btn train-btn">🚝 モノレール</a>
                </div>
                <a href="https://transit.yahoo.co.jp/diainfo/area/4" target="_blank" class="cam-btn train-btn" style="background:#444; color:#fff;">🚃 JR・関東全域 (山手線など)</a>
                
                <div class="strategy-box">
                    <div class="st-item"><span style="color:#FFD700; font-weight:bold;">📊 DATA(黄):</span> 今の飛行機の数に基づく推奨。<br><span style="color:#00BFFF; font-weight:bold;">🧠 THEORY(青):</span> セオリー(定石)に基づく推奨。</div>
                    <div class="st-item"><span style="color:#fff; font-weight:bold;">👑 W-BEST(虹):</span> データとセオリーが一致。激アツです。</div>
                    <div class="st-item"><span style="color:#f00; font-weight:bold;">⚡️ 不一致の場合:</span> 公式サイトで実際の到着便を確認してください。</div>
                </div>
                <div class="disclaimer">
                    【免責事項】<br>
                    <strong>※データ取得は1時間に1回です。</strong><br>
                    ※30分以上経過している場合は、公式サイトで遅延状況を確認してください。<br>
                    <strong>※最終的な稼働判断は、必ずご自身で行ってください。</strong>
                </div>
            </div>
            
            <button class="update-btn" onclick="location.reload(true)">最新情報に更新</button>
            <div class="footer">
                データ取得: {fetch_time_str} (API) | 表示更新: <span id="last-update">Now</span><br>
                <span style="font-size:10px; color:#666;">次のリロードまであと <span id="timer" style="color:gold; font-weight:bold;">60</span> 秒</span>
            </div>
        </div>
        <script>
            let sec=60; 
            setInterval(()=>{{ 
                sec--; 
                if(document.getElementById('timer')) document.getElementById('timer').innerText = sec;
                if(sec <= 0) location.reload(true);
            }}, 1000);
            
            setInterval(()=>{{
                let d=new Date();
                let m = d.getMinutes().toString().padStart(2,'0');
                if(document.getElementById('last-update')) document.getElementById('last-update').innerText = d.getHours()+":"+m;
            }}, 60000);
        </script>
    </body>
    </html>
    """
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)