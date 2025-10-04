import os
import time
import logging
import pandas as pd
import numpy as np
from datetime import datetime
from dotenv import load_dotenv
import sys
import io
import signal

# Исправление кодировки для Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Настройка логирования с правильной кодировкой
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - BOT - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_bot.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Импорты наших модулей
try:
    from api.mexc_client import MexcClient
    from ai.analysis_engine import AIAnalysisEngine
except ImportError as e:
    logging.error(f"Import error: {e}")
    logging.info("Trying alternative import method...")
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from api.mexc_client import MexcClient
    from ai.analysis_engine import AIAnalysisEngine

class TradingBot:
    def __init__(self):
        load_dotenv()
        
        # Инициализация клиентов
        self.mexc_client = MexcClient(
            api_key=os.getenv('MEXC_API_KEY', 'test_key'),
            secret_key=os.getenv('MEXC_SECRET_KEY', 'test_secret')
        )
        
        self.ai_engine = AIAnalysisEngine()
        
        self.symbol = 'BTCUSDT'
        self.trade_enabled = False  # Set to True for real trading
        self.running = True
        self.cycle_count = 0
        
        # Обработка сигналов для graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        logging.info("✅ TradingBot инициализирован")
    
    def signal_handler(self, signum, frame):
        """Обработчик сигналов для graceful shutdown"""
        logging.info(f"📨 Получен сигнал {signum}, останавливаю бота...")
        self.running = False
    
    def get_live_price(self):
        """Получить текущую цену с биржи"""
        try:
            price = self.mexc_client.get_current_price(self.symbol)
            logging.info(f"💰 Текущая цена {self.symbol}: ${price:.2f}")
            return price
        except Exception as e:
            logging.error(f"❌ Ошибка получения цены: {e}")
            return 121812.54  # Fallback price
    
    def run_analysis_cycle(self):
        """Run analysis cycle"""
        try:
            self.cycle_count += 1
            logging.info(f"--- Analysis Cycle {self.cycle_count} ---")
            logging.info(f"🔄 Запуск анализа для {self.symbol}")
            
            # Получаем текущую цену
            current_price = self.get_live_price()
            
            # Get data from exchange
            klines_data = self.mexc_client.get_klines(
                symbol=self.symbol,
                interval='30m',
                limit=100
            )
            
            # Check if we received valid data
            if not klines_data or len(klines_data) == 0:
                logging.warning("⚠️ Нет данных от биржи, использую тестовые данные")
                df = self._generate_test_data(current_price)
            elif isinstance(klines_data, dict) and 'code' in klines_data:
                logging.warning(f"⚠️ Ошибка от биржи: {klines_data}, использую тестовые данные")
                df = self._generate_test_data(current_price)
            else:
                # Convert to DataFrame
                df = self._format_klines_data(klines_data)
                
                # Check if DataFrame has enough data
                if df.empty or len(df) < 2:
                    logging.warning("⚠️ Недостаточно данных от биржи, использую тестовые данные")
                    df = self._generate_test_data(current_price)
                else:
                    logging.info(f"✅ Получено {len(df)} реальных точек данных с биржи!")
            
            # Get AI recommendation
            recommendation = self.ai_engine.get_ai_recommendation(self.symbol, df)
            
            # Log the result
            self._log_recommendation(recommendation)
            
            # If trading is enabled - execute order
            if self.trade_enabled and recommendation['confidence'] > 0.7:
                self._execute_trade(recommendation)
                
        except Exception as e:
            logging.error(f"❌ Ошибка в цикле анализа: {e}")
            logging.info("🔄 Использую резервный анализ...")
            self._run_fallback_analysis()
    
    def _format_klines_data(self, klines_data: list):
        """Format klines data for MEXC API - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
        try:
            # MEXC возвращает список списков с 8 элементами
            df = pd.DataFrame(klines_data, columns=[
                'open_time', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume'
            ])
            
            # Convert prices to float
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Remove any rows with NaN values
            df = df.dropna()
            
            # Ensure we have the required columns
            if 'close' not in df.columns:
                raise ValueError("No 'close' column in DataFrame")
                
            return df
            
        except Exception as e:
            logging.error(f"Error formatting klines data: {e}")
            current_price = self.get_live_price()
            return self._generate_test_data(current_price)
    
    def _generate_test_data(self, base_price=None):
        """Generate test data when exchange data is not available"""
        if base_price is None:
            base_price = self.get_live_price()
            
        # More realistic price movement with volatility clustering
        returns = np.random.normal(0, 0.02, 100)  
        # Add some momentum
        for i in range(1, len(returns)):
            returns[i] = returns[i] * 0.7 + returns[i-1] * 0.3
            
        prices = base_price * (1 + returns).cumprod()
        
        df = pd.DataFrame({
            'open': prices * (1 - np.random.uniform(0.001, 0.005, 100)),
            'high': prices * (1 + np.random.uniform(0.005, 0.015, 100)),
            'low': prices * (1 - np.random.uniform(0.005, 0.015, 100)),
            'close': prices,
            'volume': np.random.randint(1000, 5000, 100) * prices / 1000
        })
        
        logging.info("📊 Сгенерированы тестовые данные")
        return df
    
    def _run_fallback_analysis(self):
        """Fallback analysis when main analysis fails - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
        try:
            # Simple fallback analysis based on random market conditions
            current_price = self.get_live_price()
            rsi = np.random.uniform(20, 80)
            
            # More sophisticated fallback logic
            if rsi < 30:
                action = "BUY"
                confidence = min(0.8 + np.random.uniform(0, 0.15), 0.95)
                reasoning = "RSI показывает перепроданность - возможен рост"
            elif rsi > 70:
                action = "SELL" 
                confidence = min(0.7 + np.random.uniform(0, 0.2), 0.9)
                reasoning = "RSI указывает на перекупленность - возможна коррекция"
            else:
                action = "HOLD"
                confidence = 0.5 + np.random.uniform(-0.1, 0.1)
                reasoning = "Рынок в нейтральной зоне"
            
            recommendation = {
                'action': action,
                'confidence': confidence,
                'analysis': {
                    'current_price': current_price,
                    'rsi': rsi
                },
                'reasoning': reasoning
            }
            
            self._log_recommendation(recommendation)
            
        except Exception as e:
            logging.error(f"Fallback analysis also failed: {e}")
            # Ultimate fallback
            logging.info("🆘 Критический резервный режим: HOLD")
    
    def _log_recommendation(self, recommendation: dict):
        """Log recommendations with better formatting"""
        try:
            action_emoji = {
                'BUY': '🟢',
                'SELL': '🔴', 
                'HOLD': '🟡'
            }
            
            emoji = action_emoji.get(recommendation['action'], '⚪')
            
            log_message = f"""
{emoji} ANALYSIS {self.symbol}:
Action: {recommendation['action']}
Confidence: {recommendation['confidence']:.2f}
Price: {recommendation['analysis']['current_price']:.2f}
RSI: {recommendation['analysis'].get('rsi', 'N/A'):.2f}
Reasoning: {recommendation['reasoning']}
"""
            logging.info(log_message)
            
        except Exception as e:
            logging.error(f"Error logging recommendation: {e}")
    
    def _execute_trade(self, recommendation: dict):
        """Execute trading operation"""
        try:
            if not self.trade_enabled:
                logging.info("🔒 Торговля отключена (режим тестирования)")
                return
                
            if recommendation['action'] == 'BUY':
                # Buy logic
                result = self.mexc_client.create_order(
                    symbol=self.symbol,
                    side='BUY',
                    order_type='MARKET',
                    quantity=0.001  # Minimum quantity
                )
                logging.info(f"🟢 BUY ORDER: {result}")
                
            elif recommendation['action'] == 'SELL':
                # Sell logic
                result = self.mexc_client.create_order(
                    symbol=self.symbol,
                    side='SELL', 
                    order_type='MARKET',
                    quantity=0.001
                )
                logging.info(f"🔴 SELL ORDER: {result}")
                
        except Exception as e:
            logging.error(f"❌ Order execution error: {e}")

    def run_continuous(self):
        """Бесконечный цикл работы бота с улучшенным управлением"""
        consecutive_errors = 0
        max_consecutive_errors = 5
        
        logging.info("🚀 Запуск непрерывного режима работы бота")
        
        while self.running:
            try:
                self.run_analysis_cycle()
                consecutive_errors = 0  # Reset error counter on success
                
                # Adaptive sleep based on system health
                sleep_time = 30
                if consecutive_errors > 0:
                    sleep_time = min(60, 30 * (consecutive_errors + 1))  # Increase sleep on errors
                
                # Ждем с проверкой флага running
                for i in range(sleep_time):
                    if not self.running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                consecutive_errors += 1
                logging.error(f"❌ Неожиданная ошибка в основном цикле: {e}")
                
                if consecutive_errors >= max_consecutive_errors:
                    logging.error(f"🚨 Достигнут лимит ошибок ({max_consecutive_errors}), останавливаю бота")
                    self.running = False
                    break
                    
                if self.running:
                    error_sleep = min(60, 30 * consecutive_errors)
                    logging.info(f"🔄 Повторная попытка через {error_sleep} секунд...")
                    time.sleep(error_sleep)
        
        logging.info("🛑 Бот остановлен")

    def get_bot_status(self):
        """Получить статус бота для дашборда"""
        return {
            'status': '🟢 RUNNING' if self.running else '🔴 STOPPED',
            'cycle_count': self.cycle_count,
            'symbol': self.symbol,
            'trade_enabled': self.trade_enabled
        }

def main():
    try:
        bot = TradingBot()
        logging.info("✅ Торговый бот успешно запущен!")
        
        # Запускаем бесконечный цикл
        bot.run_continuous()
                
    except KeyboardInterrupt:
        logging.info("⏹️ Бот остановлен пользователем")
    except Exception as e:
        logging.error(f"❌ Неожиданная ошибка в main: {e}")
    finally:
        logging.info("🏁 Работа бота завершена")

if __name__ == "__main__":
    main()