import requests

class AviationStackHandler:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "http://api.aviationstack.com/v1/flights"

    def get_seat_capacity(self, aircraft_iata):
        """
        [機種別定員マスタ v2.0]
        """
        # --- [累積加算：旧暫定マスタ（20260108_1455）] ---
        # mapping = {
        #     "B773": 500, "B772": 500,
        #     "B789": 300, "B788": 300,
        #     "B763": 270, "B738": 170
        # }
        # return mapping.get(aircraft_iata, 200)
        # ----------------------------------------------

        # 精密マスタ（2026/01/08 最新実装）
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
            processed = []
            for flight in raw_data.get('data', []):
                aircraft = flight.get('aircraft')
                iata = aircraft.get('iata') if aircraft else "UNKNOWN"
                seats = self.get_seat_capacity(iata)
                arrival = flight.get('arrival', {})
                departure = flight.get('departure', {})
                processed.append({
                    "time": arrival.get('estimated', "捕捉済"),
                    "flight_no": flight.get('flight', {}).get('iata', "N/A"),
                    "airline": flight.get('airline', {}).get('name', "不明"),
                    "origin": departure.get('iata', "不明"),
                    "delay": arrival.get('delay') if arrival.get('delay') else 0,
                    "status": flight.get('flight_status', "unknown"),
                    "pax": int(seats * 0.8)
                })
            return processed
        except Exception as e:
            print(f"❌ API Error: {e}")
            return None
