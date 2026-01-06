import datetime

CONFIG = {
    "WINDOW_PAST": -30,
    "WINDOW_FUTURE": 30,
    "CAPACITY": {"BIG": 350, "SMALL": 180, "INTL": 280},
    "LOAD_FACTORS": {"MIDNIGHT": 0.88, "RUSH": 0.82, "NORMAL": 0.65},
    "SOUTH_CITIES": ["福岡", "那覇", "伊丹", "鹿児島", "長崎", "熊本", "宮崎", "小松", "岡山", "広島", "高松", "松山", "高知"],
    "NORTH_CITIES": ["札幌", "千歳", "青森", "秋田", "山形", "三沢", "旭川", "女満別", "帯広", "釧路", "函館"],
    "DATA_FILE": "raw_flight.txt",  # 中継ファイル
    "RESULT_JSON": "analysis_result.json" # 解析結果
}
