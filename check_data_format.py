import requests
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)

def check_mexc_data_format():
    """Check the exact data format returned by MEXC"""
    url = "https://api.mexc.com/api/v3/klines"
    params = {
        'symbol': 'BTCUSDT',
        'interval': '30m',
        'limit': 3
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            logging.info(f"Received {len(data)} klines")
            
            for i, kline in enumerate(data):
                logging.info(f"Kline {i+1}: {len(kline)} columns")
                logging.info(f"  Data: {kline}")
                
                # Try to create DataFrame
                df = pd.DataFrame([kline])
                logging.info(f"  DataFrame shape: {df.shape}")
                
        else:
            logging.error(f"API Error: {response.text}")
            
    except Exception as e:
        logging.error(f"Test failed: {e}")

if __name__ == "__main__":
    check_mexc_data_format()