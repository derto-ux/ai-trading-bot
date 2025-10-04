import logging
import pandas as pd
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - BOT_TEST - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot_test.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def test_bot_data_flow():
    """Тестирование потока данных в боте"""
    print("🤖 ТЕСТИРУЕМ ПОТОК ДАННЫХ В БОТЕ")
    print("=" * 50)
    
    try:
        from main import TradingBot
        
        # Создаем бота
        bot = TradingBot()
        logging.info("✅ Бот создан")
        
        # Тест 1: Получение живой цены
        logging.info("🔍 ТЕСТ 1: Получение живой цены")
        price = bot.get_live_price()
        logging.info(f"💰 Живая цена: ${price}")
        
        # Тест 2: Получение данных с биржи
        logging.info("🔍 ТЕСТ 2: Получение данных с биржи")
        klines_data = bot.mexc_client.get_klines('BTCUSDT', '30m', 10)
        logging.info(f"📊 Данные от биржи: {len(klines_data) if klines_data else 0} записей")
        
        if klines_data:
            logging.info(f"📈 Пример данных: {klines_data[0]}")
        
        # Тест 3: Форматирование данных
        logging.info("🔍 ТЕСТ 3: Форматирование данных")
        if klines_data:
            formatted_data = bot._format_klines_data(klines_data)
            logging.info(f"✅ Данные отформатированы: {len(formatted_data)} строк")
            logging.info(f"📋 Колонки: {list(formatted_data.columns)}")
            logging.info(f"📊 Первые 3 строки:\n{formatted_data.head(3)}")
        else:
            logging.warning("⚠️ Нет данных для форматирования")
            
        # Тест 4: Генерация тестовых данных
        logging.info("🔍 ТЕСТ 4: Генерация тестовых данных")
        test_data = bot._generate_test_data(price)
        logging.info(f"✅ Тестовые данные созданы: {len(test_data)} строк")
        logging.info(f"📊 Первые 3 строки:\n{test_data.head(3)}")
        
    except Exception as e:
        logging.error(f"❌ ОШИБКА В БОТЕ: {e}")
        import traceback
        logging.error(f"🔍 СТЕК ВЫЗОВОВ: {traceback.format_exc()}")

def test_analysis_engine():
    """Тестирование AI анализа"""
    print("\n🧠 ТЕСТИРУЕМ AI АНАЛИЗ")
    print("=" * 50)
    
    try:
        from ai.analysis_engine import AIAnalysisEngine
        
        # Создаем анализатор
        engine = AIAnalysisEngine()
        logging.info("✅ AI анализатор создан")
        
        # Создаем тестовые данные
        dates = pd.date_range(start='2024-01-01', periods=100, freq='h')
        prices = 67500 + np.random.normal(0, 1000, 100).cumsum()
        
        df = pd.DataFrame({
            'open': prices * 0.999,
            'high': prices * 1.002,
            'low': prices * 0.998, 
            'close': prices,
            'volume': np.random.randint(1000, 5000, 100)
        })
        
        logging.info(f"📊 Тестовые данные созданы: {len(df)} строк")
        
        # Тест анализа
        logging.info("🔍 ТЕСТ: AI анализ")
        recommendation = engine.get_ai_recommendation('BTCUSDT', df)
        logging.info(f"✅ Рекомендация получена: {recommendation}")
        
    except Exception as e:
        logging.error(f"❌ ОШИБКА В АНАЛИЗАТОРЕ: {e}")
        import traceback
        logging.error(f"🔍 СТЕК ВЫЗОВОВ: {traceback.format_exc()}")

if __name__ == "__main__":
    print("🧪 ЗАПУСК ДИАГНОСТИКИ TRADING BOT")
    print("=" * 60)
    
    # Импортируем numpy для тестовых данных
    import numpy as np
    
    # Запускаем тесты
    test_bot_data_flow()
    test_analysis_engine()
    
    print("\n" + "=" * 60)
    print("📋 РЕЗУЛЬТАТЫ ЗАПИСАНЫ В ФАЙЛ: bot_test.log")
    print("🔍 Проверьте что происходит на каждом этапе!")