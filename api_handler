# ==========================================
# Project: KASETACK - 羽田レーダー
# Module: API Handler
# File: api_handler_20260108_1455.py
# ==========================================

import requests
import os

class AviationStackHandler:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "http://api.aviationstack.com/v1/flights"

    def get_seat_capacity(self, aircraft_iata):
        """
        指示に基づいた機種別・座席数マッピング（暫定ロジック）
        """
        mapping = {
            "B773": 500, "B772": 500,
            "B789": 300, "B788": 300,
            "B763": 270,
            "B738": 170, "B73L": 170
        }
        # マッピングにない場合は200席（デフォルト値）を返す
        return mapping.get(aircraft_iata, 200)

    def fetch_hnd_arrivals(self):
        """
        APIから羽田到着便を取得し、期待値(EV)を付与したリストを返す
        """
        params = {
            'access_key': self.api_key,
            'arr_iata': 'HND',
            'flight_status': 'active'
        }

        try:
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            raw_data = response.json()
            
            processed_flights = []
            for flight in raw_data.get('data', []):
                # 機種コードの取得
                aircraft = flight.get('aircraft')
                iata_code = aircraft.get('iata') if aircraft else "UNKNOWN"
                
                # 座席数と期待値(EV)の計算
                seats = self.get_seat_capacity(iata_code)
                ev_pax = int(seats * 0.8) # 搭乗率 0.8

                processed_flights.append({
                    "time": flight.get('arrival', {}).get('estimated', "捕捉済"),
                    "flight_no": flight.get('flight', {}).get('iata', "N/A"),
                    "airline": flight.get('airline', {}).get('name', "不明"),
                    "aircraft": iata_code,
                    "pax": ev_pax  # 期待値としての人数
                })
            return processed_flights

        except Exception as e:
            print(f"❌ API Handler Error: {e}")
            return None
