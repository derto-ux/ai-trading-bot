import requests
import logging

logging.basicConfig(level=logging.INFO)

def test_all_intervals():
    """Test all possible MEXC intervals"""
    
    # Все возможные интервалы из документации MEXC
    all_intervals = ['1m', '5m', '15m', '30m', '60m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w', '1M']
    
    working_intervals = []
    
    for interval in all_intervals:
        url = "https://api.mexc.com/api/v3/klines"
        params = {
            'symbol': 'BTCUSDT',
            'interval': interval,
            'limit': 2
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                working_intervals.append(interval)
                logging.info(f"✅ Interval '{interval}': WORKS - {len(data)} klines")
            else:
                logging.info(f"❌ Interval '{interval}': FAILS - {response.text}")
                
        except Exception as e:
            logging.error(f"❌ Interval '{interval}': ERROR - {e}")
    
    logging.info(f"\n🎯 WORKING INTERVALS: {working_intervals}")

if __name__ == "__main__":
    test_all_intervals()