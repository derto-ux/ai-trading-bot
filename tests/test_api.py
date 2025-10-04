import requests
import logging

logging.basicConfig(level=logging.INFO)

def test_mexc_api():
    """Test MEXC API connection"""
    url = "https://api.mexc.com/api/v3/klines"
    params = {
        'symbol': 'BTCUSDT',
        'interval': '1h',
        'limit': 10
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        logging.info(f"Status Code: {response.status_code}")
        logging.info(f"Response: {response.text[:200]}...")
        
        if response.status_code == 200:
            data = response.json()
            logging.info(f"Received {len(data)} klines")
            if data:
                logging.info(f"Sample kline: {data[0]}")
        else:
            logging.error(f"API Error: {response.text}")
            
    except Exception as e:
        logging.error(f"Test failed: {e}")

if __name__ == "__main__":
    test_mexc_api()