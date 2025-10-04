# test_bot.py
from main import TradingBot

def test_bot():
    bot = TradingBot()
    bot.trade_enabled = False  # Только анализ без торговли
    
    # Тестовый запуск
    for i in range(3):
        print(f"Тестовый цикл {i+1}")
        bot.run_analysis_cycle()

if __name__ == "__main__":
    test_bot()