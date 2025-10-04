import pandas as pd
import numpy as np
from typing import Dict, Tuple
import logging

class AIAnalysisEngine:
    def __init__(self, openai_api_key: str = None):
        self.openai_api_key = openai_api_key
        self.logger = logging.getLogger(__name__)
        
    def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Расчет расширенных технических индикаторов"""
        try:
            # RSI с улучшенной формулой
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).ewm(alpha=1/14).mean()
            loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            
            # Multiple Moving Averages
            for period in [5, 10, 20, 50]:
                df[f'ma_{period}'] = df['close'].rolling(window=period).mean()
            
            # MACD с гистограммой
            exp1 = df['close'].ewm(span=12).mean()
            exp2 = df['close'].ewm(span=26).mean()
            df['macd'] = exp1 - exp2
            df['macd_signal'] = df['macd'].ewm(span=9).mean()
            df['macd_histogram'] = df['macd'] - df['macd_signal']
            
            # Bollinger Bands
            df['bb_middle'] = df['close'].rolling(20).mean()
            bb_std = df['close'].rolling(20).std()
            df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
            df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
            df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
            
            # Volume indicators
            df['volume_sma'] = df['volume'].rolling(20).mean()
            df['volume_ratio'] = df['volume'] / df['volume_sma']
            
            # Price momentum
            df['price_change_1h'] = df['close'].pct_change(2)  # 2 periods for 30min = 1h
            df['price_change_4h'] = df['close'].pct_change(8)  # 8 periods for 30min = 4h
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error calculating indicators: {e}")
            return df
    
    def get_ai_recommendation(self, symbol: str, data: pd.DataFrame) -> Dict:
        """Получить улучшенную рекомендацию от AI"""
        try:
            df_with_indicators = self.calculate_technical_indicators(data)
            
            # Use last valid row
            latest = df_with_indicators.iloc[-1]
            
            # Multi-factor analysis
            recommendation = self._advanced_analysis(latest, symbol)
            
            return {
                'action': recommendation['action'],
                'confidence': recommendation['confidence'],
                'analysis': recommendation['analysis'],
                'reasoning': recommendation['reasoning']
            }
            
        except Exception as e:
            self.logger.error(f"Error in AI recommendation: {e}")
            return self._get_fallback_recommendation()
    
    def _advanced_analysis(self, data: pd.Series, symbol: str) -> Dict:
        """Продвинутый многофакторный анализ"""
        factors = []
        reasoning = []
        
        # 1. RSI Analysis
        rsi_score = 0
        if data['rsi'] < 30:
            rsi_score = 1.0
            reasoning.append("RSI в зоне перепроданности")
        elif data['rsi'] > 70:
            rsi_score = -1.0
            reasoning.append("RSI в зоне перекупленности")
        else:
            rsi_score = 0
        factors.append(('rsi', rsi_score, 0.2))  # Weight: 20%
        
        # 2. Moving Average Analysis
        ma_score = 0
        if data['ma_5'] > data['ma_20'] > data['ma_50']:
            ma_score = 1.0
            reasoning.append("Все скользящие средние выстроены в бычьем порядке")
        elif data['ma_5'] < data['ma_20'] < data['ma_50']:
            ma_score = -1.0
            reasoning.append("Все скользящие средние выстроены в медвежьем порядке")
        elif data['ma_5'] > data['ma_20']:
            ma_score = 0.5
            reasoning.append("Краткосрочный тренд восходящий")
        else:
            ma_score = -0.5
            reasoning.append("Краткосрочный тренд нисходящий")
        factors.append(('ma', ma_score, 0.25))  # Weight: 25%
        
        # 3. MACD Analysis
        macd_score = 0
        if data['macd'] > data['macd_signal'] and data['macd_histogram'] > 0:
            macd_score = 1.0
            reasoning.append("MACD показывает бычью дивергенцию")
        elif data['macd'] < data['macd_signal'] and data['macd_histogram'] < 0:
            macd_score = -1.0
            reasoning.append("MACD показывает медвежью дивергенцию")
        factors.append(('macd', macd_score, 0.15))  # Weight: 15%
        
        # 4. Bollinger Bands Analysis
        bb_score = 0
        if data['bb_position'] < 0.1:
            bb_score = 1.0
            reasoning.append("Цена у нижней границы Боллинджера")
        elif data['bb_position'] > 0.9:
            bb_score = -1.0
            reasoning.append("Цена у верхней границы Боллинджера")
        factors.append(('bb', bb_score, 0.15))  # Weight: 15%
        
        # 5. Volume Analysis
        volume_score = 0
        if data['volume_ratio'] > 1.5:
            volume_score = 0.5 * (1 if data['price_change_1h'] > 0 else -1)
            reasoning.append("Высокий объем подтверждает движение")
        factors.append(('volume', volume_score, 0.1))  # Weight: 10%
        
        # 6. Momentum Analysis
        momentum_score = 0
        if data['price_change_1h'] > 0.02:  # 2% growth in 1h
            momentum_score = 0.5
            reasoning.append("Сильный восходящий импульс")
        elif data['price_change_1h'] < -0.02:  # 2% drop in 1h
            momentum_score = -0.5
            reasoning.append("Сильный нисходящий импульс")
        factors.append(('momentum', momentum_score, 0.15))  # Weight: 15%
        
        # Calculate weighted score
        total_score = sum(score * weight for _, score, weight in factors)
        total_weight = sum(weight for _, _, weight in factors)
        
        if total_weight > 0:
            normalized_score = total_score / total_weight
        else:
            normalized_score = 0
        
        # Convert score to action and confidence
        if normalized_score > 0.3:
            action = "BUY"
            confidence = min(0.5 + (normalized_score * 0.5), 0.95)
        elif normalized_score < -0.3:
            action = "SELL"
            confidence = min(0.5 + (abs(normalized_score) * 0.5), 0.9)
        else:
            action = "HOLD"
            confidence = 0.5
        
        reasoning.append(f"Общий счет: {normalized_score:.2f}")
        
        return {
            'action': action,
            'confidence': confidence,
            'analysis': {
                'current_price': data['close'],
                'rsi': data['rsi'],
                'ma_20': data.get('ma_20', 0),
                'ma_50': data.get('ma_50', 0),
                'macd': data.get('macd', 0),
                'volume_ratio': data.get('volume_ratio', 0)
            },
            'reasoning': " | ".join(reasoning)
        }
    
    def _get_fallback_recommendation(self) -> Dict:
        """Резервная рекомендация при ошибках"""
        return {
            'action': 'HOLD',
            'confidence': 0.3,
            'analysis': {
                'current_price': 121812.54,
                'rsi': 50.0
            },
            'reasoning': 'Резервный режим: недостаточно данных для анализа'
        }