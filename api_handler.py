# ==========================================
# Project: KASETACK - api_handler.py
# ==========================================
import requests

class AviationStackHandler:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "http://api.aviationstack.com/v1/flights"

    def get_seat_capacity(self, aircraft_iata):
        """精密マスタ v2.0"""
        mapping = {
            "B773": 500, "B772": 500,
            "B789": 400, "B781": 400,
            "B788": 300, "A359": 300,
            "B763": 250, "A321": 250,
            "B738": 170, "B73L": 170
        }
        return mapping.get(aircraft_iata, 150)

    def fetch_hnd_arrivals(self):
        params = {'access_key': self.api_key, 'arr_iata': 'HND', 'flight_status': 'active'}
        try:
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            raw_data = response.json()
            processed_flights = []
            
            for flight in raw_data.get('data', []):
                aircraft = flight.get('aircraft')
                iata_code = aircraft.get('iata') if aircraft else "UNKNOWN"
                seats = self.get_seat_capacity(iata_code)
                
                # 監査用データの抽出
                arrival = flight.get('arrival', {})
                departure = flight.get('departure', {})
                
                processed_flights.append({
                    "time": arrival.get('estimated', "捕捉済"),
                    "flight_no": flight.get('flight', {}).get('iata', "N/A"),
                    "airline": flight.get('airline', {}).get('name', "不明"),
                    "origin": departure.get('iata', "不明"), # 出身地
                    "delay": arrival.get('delay') if arrival.get('delay') else 0, # 遅延分
                    "status": flight.get('flight_status', "unknown"), # 運行ステータス
                    "aircraft": iata_code,
                    "pax": int(seats * 0.8)
                })
            return processed_flights
        except Exception as e:
            print(f"❌ API Error: {e}")
            return None
