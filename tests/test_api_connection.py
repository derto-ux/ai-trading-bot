import requests
import json
import logging
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - TEST - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('api_test.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def test_mexc_api():
    """Тестирование подключения к MEXC API"""
    print("🚀 ЗАПУСК ТЕСТА MEXC API")
    print("=" * 50)
    
    base_url = "https://api.mexc.com"
    
    # Тест 1: Получение текущей цены BTC
    logging.info("🔍 ТЕСТ 1: Получение текущей цены BTC")
    try:
        response = requests.get(
            f"{base_url}/api/v3/ticker/price",
            params={'symbol': 'BTCUSDT'},
            timeout=10
        )
        
        logging.info(f"📊 Статус ответа: {response.status_code}")
        logging.info(f"📋 Заголовки ответа: {dict(response.headers)}")
        logging.info(f"📦 Тело ответа: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            logging.info(f"✅ УСПЕХ: Цена BTC = ${data['price']}")
        else:
            logging.error(f"❌ ОШИБКА: HTTP {response.status_code}")
            
    except Exception as e:
        logging.error(f"❌ ИСКЛЮЧЕНИЕ: {e}")
    
    print("-" * 50)
    
    # Тест 2: Получение свечных данных
    logging.info("🔍 ТЕСТ 2: Получение свечных данных")
    try:
        response = requests.get(
            f"{base_url}/api/v3/klines",
            params={
                'symbol': 'BTCUSDT',
                'interval': '30m',
                'limit': 5
            },
            timeout=10
        )
        
        logging.info(f"📊 Статус ответа: {response.status_code}")
        logging.info(f"📋 Заголовки ответа: {dict(response.headers)}")
        logging.info(f"📦 Длина ответа: {len(response.text)} символов")
        
        if response.status_code == 200:
            data = response.json()
            logging.info(f"✅ УСПЕХ: Получено {len(data)} свечей")
            if data:
                latest_candle = data[-1]
                logging.info(f"📈 Последняя свеча: {latest_candle}")
        else:
            logging.error(f"❌ ОШИБКА: HTTP {response.status_code}")
            
    except Exception as e:
        logging.error(f"❌ ИСКЛЮЧЕНИЕ: {e}")
    
    print("-" * 50)
    
    # Тест 3: Проверка доступности API
    logging.info("🔍 ТЕСТ 3: Проверка доступности API")
    try:
        response = requests.get(
            f"{base_url}/api/v3/ping",
            timeout=10
        )
        
        logging.info(f"📊 Статус ответа: {response.status_code}")
        logging.info(f"📋 Ответ: {response.text}")
        
        if response.status_code == 200:
            logging.info("✅ УСПЕХ: API доступен")
        else:
            logging.error(f"❌ ОШИБКА: API недоступен")
            
    except Exception as e:
        logging.error(f"❌ ИСКЛЮЧЕНИЕ: {e}")
    
    print("=" * 50)
    print("🏁 ТЕСТ ЗАВЕРШЕН")

def test_mexc_client():
    """Тестирование нашего MexcClient"""
    print("\n🚀 ТЕСТИРУЕМ НАШ MEXC CLIENT")
    print("=" * 50)
    
    try:
        from api.mexc_client import MexcClient
        
        # Создаем клиент с тестовыми ключами
        client = MexcClient(api_key='test_key', secret_key='test_secret')
        
        # Тест получения цены
        logging.info("🔍 ТЕСТ: client.get_current_price()")
        price = client.get_current_price('BTCUSDT')
        logging.info(f"💰 Полученная цена: ${price}")
        
        # Тест получения свечей
        logging.info("🔍 ТЕСТ: client.get_klines()")
        klines = client.get_klines('BTCUSDT', '30m', 5)
        logging.info(f"📊 Получено свечей: {len(klines) if klines else 0}")
        
        if klines and len(klines) > 0:
            logging.info(f"📈 Первая свеча: {klines[0]}")
        
    except Exception as e:
        logging.error(f"❌ ОШИБКА В MEXC CLIENT: {e}")

def test_direct_vs_client():
    """Сравнение прямого запроса и через наш клиент"""
    print("\n🔍 СРАВНЕНИЕ: Прямой запрос vs Наш клиент")
    print("=" * 50)
    
    base_url = "https://api.mexc.com"
    
    try:
        # Прямой запрос
        logging.info("📡 ПРЯМОЙ ЗАПРОС К API")
        direct_response = requests.get(
            f"{base_url}/api/v3/ticker/price",
            params={'symbol': 'BTCUSDT'},
            timeout=10
        )
        
        if direct_response.status_code == 200:
            direct_data = direct_response.json()
            direct_price = float(direct_data['price'])
            logging.info(f"✅ Прямой запрос: ${direct_price}")
        else:
            logging.error(f"❌ Прямой запрос не удался: {direct_response.status_code}")
            return
        
        # Через наш клиент
        logging.info("🤖 ЗАПРОС ЧЕРЕЗ НАШ CLIENT")
        from api.mexc_client import MexcClient
        client = MexcClient(api_key='test_key', secret_key='test_secret')
        client_price = client.get_current_price('BTCUSDT')
        logging.info(f"✅ Наш клиент: ${client_price}")
        
        # Сравнение
        difference = abs(direct_price - client_price)
        logging.info(f"📊 Разница: ${difference:.4f}")
        
        if difference < 1.0:  # Допустимая разница $1
            logging.info("🎯 ЦЕНЫ СОВПАДАЮТ! Наш клиент работает корректно")
        else:
            logging.warning("⚠️ ЦЕНЫ РАЗЛИЧАЮТСЯ! Возможно проблема в клиенте")
            
    except Exception as e:
        logging.error(f"❌ ОШИБКА СРАВНЕНИЯ: {e}")

if __name__ == "__main__":
    print("🧪 ЗАПУСК ДИАГНОСТИКИ MEXC API")
    print("=" * 60)
    
    # Запускаем все тесты
    test_mexc_api()
    test_mexc_client() 
    test_direct_vs_client()
    
    print("\n" + "=" * 60)
    print("📋 РЕЗУЛЬТАТЫ ЗАПИСАНЫ В ФАЙЛ: api_test.log")
    print("🔍 Проверьте логи для детального анализа проблем!")