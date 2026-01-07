import datetime

# KASETACK 究極詳細仕様書 (2026/01/06版) 準拠
CONFIG = {
    # 🌟 ターゲットURLをYahoo!空路情報（羽田到着・国内線）へ変更
    "TARGET_URL": "https://transit.yahoo.co.jp/airplane/status/list?a=HND&type=1",

    # 時間軸: T-30分(今出ている客) 〜 T+45分(これから着く便) までを捕捉
    "WINDOW_PAST": -30,
    "WINDOW_FUTURE": 45, 
    
    # 搭乗人数予測定数
    "CAPACITY": {"BIG": 350, "SMALL": 180, "INTL": 250},
    
    # 搭乗率係数 (深夜帯 0.85 を適用予定)
    "LOAD_FACTORS": {"MIDNIGHT": 0.85, "RUSH": 0.82, "NORMAL": 0.65},
    
    # JAL1号(南)判定用
    "SOUTH_CITIES": [
        "福岡", "那覇", "伊丹", "鹿児島", "長崎", "熊本", "宮崎", "小松", 
        "岡山", "広島", "高松", "松山", "高知", "徳島", "南紀白浜", "北九州", "大分", "奄美", "関西"
    ],
    
    # JAL2号(北)判定用
    "NORTH_CITIES": [
        "札幌", "千歳", "青森", "秋田", "山形", "三沢", "旭川", "女満別", 
        "帯広", "釧路", "函館", "大館能代", "庄内", "新潟", "富山"
    ],
    
    "DATA_FILE": "raw_flight.txt",
    "RESULT_JSON": "analysis_result.json"
}
