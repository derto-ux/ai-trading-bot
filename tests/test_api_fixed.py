import requests
import logging

logging.basicConfig(level=logging.INFO)

def test_mexc_intervals():
    """Test different MEXC API intervals"""
    
    # Правильные интервалы для MEXC API
    intervals = ['1m', '5m', '15m', '30m', '1H', '2H', '4H', '1D', '1W', '1M']
    
    for interval in intervals:
        url = "https://api.mexc.com/api/v3/klines"
        params = {
            'symbol': 'BTCUSDT',
            'interval': interval,
            'limit': 5
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            logging.info(f"Interval '{interval}': Status {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logging.info(f"  Success! Received {len(data)} klines")
                if data:
                    logging.info(f"  First kline: Open={data[0][1]}, Close={data[0][4]}")
            else:
                logging.error(f"  Error: {response.text}")
                
        except Exception as e:
            logging.error(f"  Failed: {e}")

def test_mexc_symbols():
    """Test if symbol exists"""
    symbols = ['BTCUSDT', 'ETHUSDT', 'BTCUSDC']  # Попробуем разные символы
    
    for symbol in symbols:
        url = "https://api.mexc.com/api/v3/klines"
        params = {
            'symbol': symbol,
            'interval': '1m',  # Самый простой интервал
            'limit': 1
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            logging.info(f"Symbol '{symbol}': Status {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logging.info(f"  Symbol exists! Data: {data[0] if data else 'No data'}")
            else:
                logging.error(f"  Symbol error: {response.text}")
                
        except Exception as e:
            logging.error(f"  Symbol test failed: {e}")

if __name__ == "__main__":
    logging.info("Testing MEXC API intervals...")
    test_mexc_intervals()
    
    logging.info("\nTesting MEXC API symbols...")
    test_mexc_symbols()