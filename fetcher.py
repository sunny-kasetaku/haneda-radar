import requests
import os
from config import CONFIG

def run_fetch():
    url = "https://www.flightview.com/traveltools/FlightStatusByAirport.asp?airport=HND&at=A"
    try:
        print("Fetching flight data...")
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        r.raise_for_status()
        with open(CONFIG["DATA_FILE"], "w", encoding="utf-8") as f:
            f.write(r.text)
        print("Fetch success.")
        return True
    except Exception as e:
        print(f"Fetch failed: {e}")
        return False

if __name__ == "__main__":
    run_fetch()
