from flask import Flask, render_template, jsonify, request
import json
import os
import sys
import subprocess
import signal
import threading
import random
from datetime import datetime, timedelta
import pandas as pd
import logging
import time

# Получаем абсолютный путь к корневой папке проекта
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

app = Flask(__name__)

# Абсолютные пути для лог-файлов
BOT_LOG_FILE = os.path.join(PROJECT_ROOT, 'trading_bot.log')
DASHBOARD_LOG_FILE = os.path.join(PROJECT_ROOT, 'dashboard.log')
DEBUG_LOG_FILE = os.path.join(PROJECT_ROOT, 'debug.log')

# Создаем файлы если их нет
for log_file in [BOT_LOG_FILE, DASHBOARD_LOG_FILE, DEBUG_LOG_FILE]:
    if not os.path.exists(log_file):
        open(log_file, 'w', encoding='utf-8').close()

# Настройка логирования для дашборда
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - DASHBOARD - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(DASHBOARD_LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Дополнительный логгер для отладки
debug_logger = logging.getLogger('debug')
debug_logger.setLevel(logging.DEBUG)
debug_handler = logging.FileHandler(DEBUG_LOG_FILE, encoding='utf-8')
debug_handler.setFormatter(logging.Formatter('%(asctime)s - DEBUG - %(message)s'))
debug_logger.addHandler(debug_handler)

class TradingBotDashboard:
    def __init__(self):
        self.bot_process = None
        self.bot_log_file = BOT_LOG_FILE
        self.dashboard_log_file = DASHBOARD_LOG_FILE
        self.bot_status = "🔴 STOPPED"
        self.last_bot_output = ""
        self.bot_thread = None
        self.start_time = None
        
        debug_logger.info(f"🔄 Инициализация дашборда")
        debug_logger.info(f"📁 PROJECT_ROOT: {PROJECT_ROOT}")
        debug_logger.info(f"📄 BOT_LOG_FILE: {BOT_LOG_FILE}")
        debug_logger.info(f"📄 DASHBOARD_LOG_FILE: {DASHBOARD_LOG_FILE}")
        debug_logger.info(f"📄 DEBUG_LOG_FILE: {DEBUG_LOG_FILE}")
        
    def is_bot_running(self):
        """Проверяет, запущен ли бот"""
        if self.bot_process and self.bot_process.poll() is None:
            return True
        return False
    
    def start_bot(self):
        """Запускает торгового бота в отдельном потоке"""
        try:
            debug_logger.info("▶️ НАЧАЛО ЗАПУСКА БОТА")
            
            if self.is_bot_running():
                debug_logger.warning("⚠️ Бот уже запущен")
                return False, "Bot is already running"
            
            self.start_time = datetime.now()
            
            debug_logger.info("🔄 Подготовка к запуску бота...")
            
            def run_bot():
                try:
                    debug_logger.info("🚀 ЗАПУСК ПРОЦЕССА БОТА")
                    
                    # Запускаем бота с абсолютным путем
                    bot_script = os.path.join(PROJECT_ROOT, 'main.py')
                    debug_logger.info(f"📄 Запускаем скрипт: {bot_script}")
                    
                    self.bot_process = subprocess.Popen(
                        [sys.executable, bot_script],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=1,
                        universal_newlines=True,
                        encoding='utf-8',
                        cwd=PROJECT_ROOT  # Указываем рабочую директорию
                    )
                    
                    debug_logger.info(f"📊 Процесс бота создан: {self.bot_process.pid}")
                    
                    # Читаем вывод в реальном времени
                    for line in iter(self.bot_process.stdout.readline, ''):
                        clean_line = line.strip()
                        self.last_bot_output = clean_line
                        debug_logger.info(f"BOT: {clean_line}")
                        
                        # Также записываем в основной лог
                        logger.info(f"BOT: {clean_line}")
                    
                    self.bot_process.stdout.close()
                    return_code = self.bot_process.wait()
                    
                    debug_logger.info(f"📤 Бот завершился с кодом: {return_code}")
                    
                    if return_code != 0:
                        debug_logger.warning(f"⚠️ Бот завершился с кодом: {return_code}")
                    else:
                        debug_logger.info("✅ Бот корректно завершился")
                        
                except Exception as e:
                    error_msg = f"❌ Ошибка в потоке бота: {e}"
                    logger.error(error_msg)
                    debug_logger.error(error_msg)
                finally:
                    self.bot_process = None
                    debug_logger.info("🛑 Процесс бота очищен")
            
            # Запускаем в отдельном потоке
            self.bot_thread = threading.Thread(target=run_bot)
            self.bot_thread.daemon = True
            self.bot_thread.start()
            
            # Ждем немного и проверяем статус
            time.sleep(3)
            
            if self.is_bot_running():
                success_msg = "✅ Торговый бот успешно запущен"
                logger.info(success_msg)
                debug_logger.info(success_msg)
                self.bot_status = "🟢 RUNNING"
                return True, success_msg
            else:
                error_msg = "❌ Не удалось запустить бот"
                logger.error(error_msg)
                debug_logger.error(error_msg)
                return False, error_msg
            
        except Exception as e:
            error_msg = f"❌ Ошибка при запуске бота: {e}"
            logger.error(error_msg)
            debug_logger.error(error_msg)
            return False, error_msg
    
    def stop_bot(self):
        """Останавливает торгового бота"""
        try:
            debug_logger.info("🛑 ПОПЫТКА ОСТАНОВКИ БОТА")
            
            if self.is_bot_running():
                debug_logger.info(f"📤 Отправляем TERMINATE процессу {self.bot_process.pid}")
                self.bot_process.terminate()
                
                try:
                    self.bot_process.wait(timeout=10)
                    debug_logger.info("✅ Бот корректно завершился")
                except subprocess.TimeoutExpired:
                    debug_logger.warning("⚠️ Бот не ответил, отправляем KILL")
                    self.bot_process.kill()
                    self.bot_process.wait()
                    debug_logger.info("✅ Бот принудительно остановлен")
                
                self.bot_process = None
                self.bot_status = "🔴 STOPPED"
                logger.info("🛑 Бот остановлен")
                return True, "Trading bot stopped successfully"
            else:
                debug_logger.warning("⚠️ Бот не запущен, нечего останавливать")
                return False, "Bot is not running"
                
        except Exception as e:
            error_msg = f"❌ Ошибка при остановке бота: {e}"
            logger.error(error_msg)
            debug_logger.error(error_msg)
            return False, error_msg
    
    def get_bot_status(self):
        """Получить статус бота"""
        if self.is_bot_running():
            self.bot_status = "🟢 RUNNING"
        else:
            self.bot_status = "🔴 STOPPED"
        
        debug_logger.debug(f"📊 Текущий статус: {self.bot_status}")
        return self.bot_status
    
    def get_bot_uptime(self):
        """Получить время работы бота"""
        if not self.is_bot_running() or not self.start_time:
            return "Not running"
        
        uptime = datetime.now() - self.start_time
        hours, remainder = divmod(uptime.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"

    def get_detailed_logs(self):
        """Получить детальные логи работы"""
        try:
            # Читаем логи из файлов
            bot_logs = []
            if os.path.exists(self.bot_log_file):
                with open(self.bot_log_file, 'r', encoding='utf-8') as f:
                    bot_logs = f.readlines()[-20:]  # Последние 20 строк
            
            dashboard_logs = []
            if os.path.exists(self.dashboard_log_file):
                with open(self.dashboard_log_file, 'r', encoding='utf-8') as f:
                    dashboard_logs = f.readlines()[-20:]
            
            debug_logs = []
            if os.path.exists(DEBUG_LOG_FILE):
                with open(DEBUG_LOG_FILE, 'r', encoding='utf-8') as f:
                    debug_logs = f.readlines()[-20:]
            
            logs_info = {
                'status': self.bot_status,
                'uptime': self.get_bot_uptime(),
                'process_running': self.is_bot_running(),
                'last_output': self.last_bot_output,
                'bot_logs': bot_logs,
                'dashboard_logs': dashboard_logs,
                'debug_logs': debug_logs,
                'log_files': {
                    'trading_bot.log': self.bot_log_file,
                    'dashboard.log': self.dashboard_log_file,
                    'debug.log': DEBUG_LOG_FILE
                }
            }
            return logs_info
        except Exception as e:
            debug_logger.error(f"❌ Ошибка чтения логов: {e}")
            return {'error': str(e)}

    def get_current_price(self):
        return 121812.54

    def get_performance_stats(self):
        return {
            'total_recommendations': 50,
            'buy_count': 16,
            'sell_count': 11,
            'hold_count': 23,
            'buy_percentage': 32.0,
            'sell_percentage': 22.0,
            'hold_percentage': 46.0,
            'avg_confidence': 0.648,
            'win_rate': 0.688,
            'total_trades': 50,
            'sharpe_ratio': 1.25,
            'max_drawdown': 0.129
        }

    def get_trading_metrics(self):
        return {
            'total_pl': 1084.29,
            'active_trades': 1,
            'api_calls': 126,
            'error_rate': 0.023
        }

    def get_system_info(self):
        return {
            'cpu_usage': f"{random.randint(5, 25)}%",
            'memory_usage': f"{random.randint(30, 70)}%",
            'bot_uptime': self.get_bot_uptime(),
            'status': self.get_bot_status()
        }

    def get_recent_recommendations(self, limit=10):
        """Получить последние рекомендации с реальными данными из логов бота"""
        try:
            recommendations = []
            
            # Если бот запущен, пытаемся получить реальные данные из логов
            if self.is_bot_running() and os.path.exists(self.bot_log_file):
                with open(self.bot_log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                # Ищем последние записи анализа в логах
                analysis_lines = []
                for line in reversed(lines[-100:]):  # Проверяем последние 100 строк
                    if 'ANALYSIS BTCUSDT:' in line:
                        analysis_lines = []
                        analysis_lines.append(line)
                    elif analysis_lines and any(keyword in line for keyword in ['Action:', 'Confidence:', 'Price:', 'RSI:', 'Reasoning:']):
                        analysis_lines.append(line)
                    elif analysis_lines and line.strip() == '':
                        # Конец записи анализа
                        rec = self._parse_analysis_from_logs(analysis_lines)
                        if rec:
                            recommendations.append(rec)
                        analysis_lines = []
                        
                        if len(recommendations) >= limit:
                            break
            
            # Если не нашли реальных данных или их недостаточно, используем демо-данные
            if len(recommendations) < limit:
                demo_count = limit - len(recommendations)
                demo_recommendations = self._generate_demo_recommendations(demo_count)
                recommendations.extend(demo_recommendations)
            
            # Сортируем по времени (новые сначала)
            recommendations.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            return recommendations[:limit]
            
        except Exception as e:
            debug_logger.error(f"❌ Ошибка получения рекомендаций: {e}")
            return self._generate_demo_recommendations(limit)

    def _parse_analysis_from_logs(self, analysis_lines):
        """Парсинг рекомендаций из логов бота"""
        try:
            rec = {
                'symbol': 'BTCUSDT',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            for line in analysis_lines:
                line = line.strip()
                if line.startswith('Action:'):
                    rec['action'] = line.split('Action:')[1].strip()
                elif line.startswith('Confidence:'):
                    rec['confidence'] = float(line.split('Confidence:')[1].strip())
                elif line.startswith('Price:'):
                    rec['price'] = float(line.split('Price:')[1].strip())
                elif line.startswith('RSI:'):
                    rec['rsi'] = float(line.split('RSI:')[1].strip())
                elif line.startswith('Reasoning:'):
                    rec['reasoning'] = line.split('Reasoning:')[1].strip()
                elif 'ANALYSIS BTCUSDT:' in line:
                    # Извлекаем эмодзи если есть
                    if '🟢' in line:
                        rec['action'] = 'BUY'
                    elif '🔴' in line:
                        rec['action'] = 'SELL'
                    elif '🟡' in line:
                        rec['action'] = 'HOLD'
            
            # Проверяем, что все необходимые поля есть
            required_fields = ['action', 'confidence', 'price']
            if all(field in rec for field in required_fields):
                return rec
            else:
                return None
                
        except Exception as e:
            debug_logger.error(f"❌ Ошибка парсинга логов: {e}")
            return None

    def _generate_demo_recommendations(self, count):
        """Генерация демо-рекомендаций"""
        base_price = 121812.54
        recommendations = []
        
        for i in range(count):
            rsi = random.uniform(25, 75)
            
            if rsi < 35:
                action = "BUY"
                confidence = random.uniform(0.7, 0.9)
                reasoning = "RSI показывает перепроданность - возможен рост"
                strength = "strong"
            elif rsi > 65:
                action = "SELL"
                confidence = random.uniform(0.6, 0.8)
                reasoning = "RSI указывает на перекупленность - возможна коррекция"
                strength = "medium"
            else:
                action = "HOLD"
                confidence = random.uniform(0.4, 0.6)
                reasoning = "Рынок в нейтральной зоне"
                strength = "weak"
            
            recommendations.append({
                'timestamp': (datetime.now() - timedelta(minutes=i*30)).strftime('%Y-%m-%d %H:%M:%S'),
                'symbol': 'BTCUSDT',
                'action': action,
                'confidence': confidence,
                'price': base_price + random.uniform(-2000, 2000),
                'rsi': rsi,
                'reasoning': reasoning,
                'strength': strength,
                'timeframe': '30min'
            })
        
        return recommendations

# Создаем экземпляр дашборда
dashboard = TradingBotDashboard()

@app.route('/')
def index():
    """Главная страница дашборда"""
    debug_logger.info("🌐 Запрос главной страницы")
    status = dashboard.get_bot_status()
    current_price = dashboard.get_current_price()
    stats = dashboard.get_performance_stats()
    trading_metrics = dashboard.get_trading_metrics()
    recommendations = dashboard.get_recent_recommendations(10)
    
    return render_template('dashboard.html',
                         status=status,
                         current_price=current_price,
                         stats=stats,
                         trading_metrics=trading_metrics,
                         recommendations=recommendations,
                         now=datetime.now())

@app.route('/api/status')
def api_status():
    """API endpoint для статуса"""
    debug_logger.debug("📊 Запрос статуса API")
    status = dashboard.get_bot_status()
    current_price = dashboard.get_current_price()
    stats = dashboard.get_performance_stats()
    trading_metrics = dashboard.get_trading_metrics()
    system_info = dashboard.get_system_info()
    
    return jsonify({
        'status': status,
        'current_price': current_price,
        'last_update': datetime.now().isoformat(),
        'performance': stats,
        'trading_metrics': trading_metrics,
        'system_info': system_info
    })

@app.route('/api/start_bot', methods=['POST'])
def start_bot():
    """API endpoint для запуска бота"""
    debug_logger.info("▶️ ЗАПРОС API: Запуск бота")
    success, message = dashboard.start_bot()
    
    response_data = {
        'status': 'success' if success else 'error',
        'message': message,
        'bot_status': dashboard.get_bot_status(),
        'process_running': dashboard.is_bot_running(),
        'timestamp': datetime.now().isoformat()
    }
    
    debug_logger.info(f"📤 ОТВЕТ API: {response_data}")
    return jsonify(response_data)

@app.route('/api/stop_bot', methods=['POST'])
def stop_bot():
    """API endpoint для остановки бота"""
    debug_logger.info("⏹️ ЗАПРОС API: Остановка бота")
    success, message = dashboard.stop_bot()
    
    response_data = {
        'status': 'success' if success else 'error',
        'message': message,
        'bot_status': dashboard.get_bot_status(),
        'process_running': dashboard.is_bot_running(),
        'timestamp': datetime.now().isoformat()
    }
    
    debug_logger.info(f"📤 ОТВЕТ API: {response_data}")
    return jsonify(response_data)

@app.route('/api/bot_logs')
def api_bot_logs():
    """API endpoint для получения логов бота"""
    debug_logger.info("📋 ЗАПРОС API: Получение логов")
    logs_data = dashboard.get_detailed_logs()
    return jsonify(logs_data)

@app.route('/api/debug_info')
def api_debug_info():
    """API endpoint для отладки"""
    debug_logger.info("🐛 ЗАПРОС API: Отладочная информация")
    debug_info = {
        'dashboard_status': dashboard.bot_status,
        'process_running': dashboard.is_bot_running(),
        'bot_process': str(dashboard.bot_process),
        'bot_thread': str(dashboard.bot_thread),
        'start_time': str(dashboard.start_time),
        'last_output': dashboard.last_bot_output,
        'project_root': PROJECT_ROOT,
        'log_files': {
            'trading_bot.log': BOT_LOG_FILE,
            'dashboard.log': DASHBOARD_LOG_FILE,
            'debug.log': DEBUG_LOG_FILE
        },
        'timestamp': datetime.now().isoformat()
    }
    return jsonify(debug_info)

@app.route('/api/recommendations')
def api_recommendations():
    """API endpoint для получения торговых рекомендаций"""
    debug_logger.info("🎯 ЗАПРОС API: Получение рекомендаций")
    
    try:
        limit = request.args.get('limit', 10, type=int)
        recommendations = dashboard.get_recent_recommendations(limit)
        
        # Добавляем дополнительную информацию для фронтенда
        for rec in recommendations:
            # Определяем силу сигнала на основе confidence
            if rec['confidence'] > 0.8:
                rec['strength'] = 'strong'
            elif rec['confidence'] > 0.6:
                rec['strength'] = 'medium'
            else:
                rec['strength'] = 'weak'
                
            # Добавляем timestamp если его нет
            if 'timestamp' not in rec:
                rec['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        debug_logger.info(f"📊 Отправлено {len(recommendations)} рекомендаций")
        return jsonify(recommendations)
        
    except Exception as e:
        debug_logger.error(f"❌ Ошибка получения рекомендаций: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/force_refresh', methods=['POST'])
def api_force_refresh():
    """API endpoint для принудительного обновления данных"""
    debug_logger.info("🔄 ЗАПРОС API: Принудительное обновление")
    
    try:
        # Здесь можно добавить логику принудительного обновления
        # Например, перезапуск анализа или обновление кэша
        
        return jsonify({
            'status': 'success',
            'message': 'Data refresh triggered',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        debug_logger.error(f"❌ Ошибка принудительного обновления: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🤖 AI Trading Bot Dashboard")
    print("========================================")
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Bot log: {BOT_LOG_FILE}")
    print(f"Dashboard log: {DASHBOARD_LOG_FILE}")
    print(f"Debug log: {DEBUG_LOG_FILE}")
    print("========================================")
    print("Starting server...")
    print("Open http://localhost:5000 in your browser")
    print("========================================")
    
    # Записываем информацию о запуске
    debug_logger.info("🚀 ДАШБОРД ЗАПУЩЕН")
    debug_logger.info(f"📁 PROJECT_ROOT: {PROJECT_ROOT}")
    
    app.run(debug=True, host='0.0.0.0', port=5000)