import re
import datetime
import json
import os
from config import CONFIG

def run_analyze():
    if not os.path.exists(CONFIG["DATA_FILE"]):
        return None

    jst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(jst)
    
    with open(CONFIG["DATA_FILE"], "r", encoding="utf-8") as f:
        html_content = f.read()

    stands = {"P1": 0, "P2": 0, "P3": 0, "P4": 0, "P5": 0}
    flight_rows = []
    total_pax = 0

    # 正規表現での解析
    flights = re.findall(r'(\d{1,2}):(\d{2})\s?([AP]M)?.*?(\w{2,3})\s?(\d+).*?<td>(.*?)</td>', html_content, re.DOTALL)
    
    rate = CONFIG["LOAD_FACTORS"]["NORMAL"]
    if 22 <= now.hour or now.hour <= 2: rate = CONFIG["LOAD_FACTORS"]["MIDNIGHT"]
    elif 7 <= now.hour <= 9 or 17 <= now.hour <= 20: rate = CONFIG["LOAD_FACTORS"]["RUSH"]

    for h, m, ampm, carrier, fnum, origin in flights:
        f_h = int(h)
        if ampm == "PM" and f_h < 12: f_h += 12
        elif ampm == "AM" and f_h == 12: f_h = 0
        f_t = now.replace(hour=f_h % 24, minute=int(m), second=0, microsecond=0)
        
        diff = (f_t - now).total_seconds() / 60
        if CONFIG["WINDOW_PAST"] <= diff <= CONFIG["WINDOW_FUTURE"]:
            is_big = int(fnum) < 1000 if fnum.isdigit() else False
            cap = CONFIG["CAPACITY"]["BIG"] if is_big else CONFIG["CAPACITY"]["SMALL"]
            if carrier not in ["JL", "NH", "BC", "7G", "6J", "ADO", "SNA", "SFJ"]: cap = CONFIG["CAPACITY"]["INTL"]
            
            pax = int(cap * rate)
            total_pax += pax
            
            s_key = "P5"
            if carrier == "JL":
                if any(city in origin for city in CONFIG["SOUTH_CITIES"]): s_key = "P1"
                elif any(city in origin for city in CONFIG["NORTH_CITIES"]): s_key = "P2"
                else: s_key = "P1"
            elif carrier == "BC": s_key = "P1"
            elif carrier == "NH": s_key = "P3"
            elif carrier in ["ADO", "SNA", "SFJ", "7G"]: s_key = "P4"
            
            stands[s_key] += pax
            flight_rows.append({"time": f"{f_h:02d}:{m}", "flight": f"{carrier}{fnum}", "origin": origin[:6], "pax": pax})

    result = {
        "stands": stands,
        "total_pax": total_pax,
        "rows": flight_rows,
        "update_time": now.strftime("%H:%M")
    }
    
    with open(CONFIG["RESULT_JSON"], "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    return result

if __name__ == "__main__":
    run_analyze()
