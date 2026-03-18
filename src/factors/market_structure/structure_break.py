"""
结构突破检测因子
识别BOS (Break of Structure) 和 CHOCH (Change of Character) 信号
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')


class StructureBreakAnalyzer:
    """
    结构突破分析器
    
    功能:
    1. BOS (Break of Structure) 信号检测
    2. CHOCH (Change of Character) 信号检测  
    3. 市场结构评分计算
    """
    
    def __init__(self, lookback_period: int = 50, bos_threshold: float = 0.01):
        """
        初始化结构突破分析器
        
        Args:
            lookback_period: 结构分析回看周期
            bos_threshold: BOS突破阈值 (百分比)
        """
        self.lookback_period = lookback_period
        self.bos_threshold = bos_threshold
        
    def analyze_structure_breaks(self, df: pd.DataFrame, swing_points: Dict = None) -> Dict:
        """
        分析结构突破信号
        
        Args:
            df: 包含OHLCV数据的DataFrame
            swing_points: 可选的摆动点数据
            
        Returns:
            Dict: 结构突破分析结果
        """
        if not {'high', 'low', 'close'}.issubset(df.columns):
            raise ValueError("DataFrame必须包含'high', 'low', 'close'列")
            
        results = {}
        
        # 如果需要，重新计算摆动点
        if swing_points is None:
            from .trend_analyzer import TrendAnalyzer
            trend_analyzer = TrendAnalyzer()
            swing_points = trend_analyzer._detect_swing_points(df)
        
        # 1. BOS信号检测
        results['bos_signals'] = self._detect_bos_signals(df, swing_points)
        
        # 2. CHOCH信号检测
        results['choch_signals'] = self._detect_choch_signals(df, swing_points)
        
        # 3. 市场结构评分
        results['market_structure_score'] = self._calculate_structure_score(
            results['bos_signals'], results['choch_signals'], df
        )
        
        # 4. 结构健康度评估
        results['structure_health'] = self._assess_structure_health(df, swing_points)
        
        # 5. 最近突破信号
        results['recent_breaks'] = self._get_recent_break_signals(
            results['bos_signals'], results['choch_signals']
        )
        
        return results
    
    def _detect_bos_signals(self, df: pd.DataFrame, swing_points: Dict) -> List[Dict]:
        """
        检测BOS (Break of Structure) 信号
        
        BOS定义: 价格突破前高(上升趋势)或前低(下降趋势)
        """
        bos_signals = []
        
        highs = df['high'].values
        lows = df['low'].values
        closes = df['close'].values
        
        # 获取摆动高点
        swing_highs = swing_points['highs']
        if len(swing_highs) < 2:
            return bos_signals
            
        # 获取摆动低点
        swing_lows = swing_points['lows']
        if len(swing_lows) < 2:
            return bos_signals
        
        # 分析最近的价格行为
        recent_data = df.tail(self.lookback_period)
        
        for i in range(1, len(recent_data)):
            idx = len(df) - len(recent_data) + i
            current_high = highs[idx]
            current_low = lows[idx]
            current_close = closes[idx]
            
            # 检查上升趋势BOS (突破前高)
            if len(swing_highs) >= 2:
                last_swing_high = swing_highs.iloc[-1]['price']
                prev_swing_high = swing_highs.iloc[-2]['price'] if len(swing_highs) >= 2 else last_swing_high
                
                # 当前高点突破前高
                if current_high > last_swing_high * (1 + self.bos_threshold):
                    signal = {
                        'type': 'bos_bullish',
                        'index': idx,
                        'price': current_high,
                        'break_level': last_swing_high,
                        'strength': (current_high - last_swing_high) / last_swing_high * 100,
                        'confirmed': current_close > last_swing_high,  # 收盘确认
                        'description': f'突破前高 {last_swing_high:.2f}'
                    }
                    bos_signals.append(signal)
            
            # 检查下降趋势BOS (突破前低)
            if len(swing_lows) >= 2:
                last_swing_low = swing_lows.iloc[-1]['price']
                prev_swing_low = swing_lows.iloc[-2]['price'] if len(swing_lows) >= 2 else last_swing_low
                
                # 当前低点突破前低
                if current_low < last_swing_low * (1 - self.bos_threshold):
                    signal = {
                        'type': 'bos_bearish',
                        'index': idx,
                        'price': current_low,
                        'break_level': last_swing_low,
                        'strength': (last_swing_low - current_low) / last_swing_low * 100,
                        'confirmed': current_close < last_swing_low,  # 收盘确认
                        'description': f'突破前低 {last_swing_low:.2f}'
                    }
                    bos_signals.append(signal)
        
        return bos_signals
    
    def _detect_choch_signals(self, df: pd.DataFrame, swing_points: Dict) -> List[Dict]:
        """
        检测CHOCH (Change of Character) 信号
        
        CHOCH定义: 趋势特征改变，如上升趋势中出现更低的高点
        """
        choch_signals = []
        
        highs = df['high'].values
        lows = df['low'].values
        
        # 获取摆动点
        swing_highs = swing_points['highs']
        swing_lows = swing_points['lows']
        
        if len(swing_highs) < 3 or len(swing_lows) < 3:
            return choch_signals
        
        # 分析最近的摆动点序列
        recent_highs = swing_highs.tail(3)
        recent_lows = swing_lows.tail(3)
        
        # 检查上升趋势中的CHOCH (出现更低的高点)
        if len(recent_highs) >= 3:
            h3, h2, h1 = recent_highs.iloc[-3]['price'], recent_highs.iloc[-2]['price'], recent_highs.iloc[-1]['price']
            
            # 上升趋势: h1 > h2 > h3, 但最新高点 h1 < h2 (趋势改变)
            if h2 > h3 and h1 < h2:
                signal = {
                    'type': 'choch_bearish',
                    'description': '上升趋势中出现更低的高点',
                    'pattern': 'lower_high',
                    'highs': [h3, h2, h1],
                    'strength': (h2 - h1) / h2 * 100
                }
                choch_signals.append(signal)
        
        # 检查下降趋势中的CHOCH (出现更高的低点)
        if len(recent_lows) >= 3:
            l3, l2, l1 = recent_lows.iloc[-3]['price'], recent_lows.iloc[-2]['price'], recent_lows.iloc[-1]['price']
            
            # 下降趋势: l1 < l2 < l3, 但最新低点 l1 > l2 (趋势改变)
            if l2 < l3 and l1 > l2:
                signal = {
                    'type': 'choch_bullish',
                    'description': '下降趋势中出现更高的低点',
                    'pattern': 'higher_low',
                    'lows': [l3, l2, l1],
                    'strength': (l1 - l2) / l2 * 100
                }
                choch_signals.append(signal)
        
        # 检查市场结构破坏
        recent_data = df.tail(20)
        if len(recent_data) >= 10:
            # 检查是否形成区间震荡
            price_range = recent_data['high'].max() - recent_data['low'].min()
            avg_range = (recent_data['high'] - recent_data['low']).mean()
            
            if price_range < avg_range * 3:  # 窄幅震荡
                signal = {
                    'type': 'choch_consolidation',
                    'description': '市场进入震荡整理',
                    'range_ratio': price_range / avg_range,
                    'price_range': price_range
                }
                choch_signals.append(signal)
        
        return choch_signals
    
    def _calculate_structure_score(self, bos_signals: List, choch_signals: List, df: pd.DataFrame) -> float:
        """
        计算市场结构评分 (0-100)
        
        综合考虑:
        1. 趋势的清晰度
        2. 结构突破的强度
        3. 市场噪音水平
        """
        score = 50.0  # 基础分
        
        # 1. 基于趋势清晰度
        from .trend_analyzer import TrendAnalyzer
        trend_analyzer = TrendAnalyzer()
        trend_strength = trend_analyzer._calculate_trend_strength(df)
        score += trend_strength * 0.3  # 趋势强度贡献30%
        
        # 2. 基于BOS信号
        if bos_signals:
            recent_bos = bos_signals[-1] if bos_signals else None
            if recent_bos and recent_bos.get('confirmed', False):
                strength = min(recent_bos.get('strength', 0), 10)  # 限制最大强度为10%
                score += strength * 2  # 突破强度贡献
        
        # 3. 基于CHOCH信号 (负向影响)
        if choch_signals:
            # CHOCH信号通常表示结构弱化
            score -= len(choch_signals) * 5
        
        # 4. 基于价格波动性
        volatility = df['close'].pct_change().std() * 100  # 日波动率百分比
        if volatility < 1:  # 低波动性，结构可能更清晰
            score += 5
        elif volatility > 5:  # 高波动性，结构可能混乱
            score -= 10
        
        # 确保分数在0-100之间
        score = max(0, min(100, score))
        
        return round(score, 1)
    
    def _assess_structure_health(self, df: pd.DataFrame, swing_points: Dict) -> Dict:
        """
        评估市场结构健康度
        """
        health = {
            'overall': 'neutral',
            'trend_continuity': 'unknown',
            'breakout_quality': 'unknown',
            'noise_level': 'unknown'
        }
        
        # 检查趋势连续性
        if len(swing_points['highs']) >= 3 and len(swing_points['lows']) >= 3:
            highs = swing_points['highs']['price'].values[-3:]
            lows = swing_points['lows']['price'].values[-3:]
            
            # 检查是否形成HH/HL或LL/LH序列
            if highs[2] > highs[1] > highs[0] and lows[2] > lows[1] > lows[0]:
                health['trend_continuity'] = 'strong_uptrend'
            elif highs[2] < highs[1] < highs[0] and lows[2] < lows[1] < lows[0]:
                health['trend_continuity'] = 'strong_downtrend'
            else:
                health['trend_continuity'] = 'mixed'
        
        # 评估突破质量
        recent_closes = df['close'].tail(5)
        recent_highs = df['high'].tail(5)
        recent_lows = df['low'].tail(5)
        
        close_range = recent_closes.max() - recent_closes.min()
        high_low_range = (recent_highs.max() - recent_lows.min())
        
        if close_range < high_low_range * 0.3:
            health['breakout_quality'] = 'strong'  # 收盘价集中，突破质量高
        else:
            health['breakout_quality'] = 'weak'  # 收盘价分散，突破质量低
        
        # 评估噪音水平
        daily_ranges = (df['high'] - df['low']).tail(20)
        avg_range = daily_ranges.mean()
        current_range = daily_ranges.iloc[-1]
        
        if current_range < avg_range * 0.7:
            health['noise_level'] = 'low'
        elif current_range > avg_range * 1.3:
            health['noise_level'] = 'high'
        else:
            health['noise_level'] = 'normal'
        
        # 综合评估
        positive_factors = 0
        if health['trend_continuity'] in ['strong_uptrend', 'strong_downtrend']:
            positive_factors += 1
        if health['breakout_quality'] == 'strong':
            positive_factors += 1
        if health['noise_level'] == 'low':
            positive_factors += 1
        
        if positive_factors >= 2:
            health['overall'] = 'healthy'
        elif positive_factors >= 1:
            health['overall'] = 'moderate'
        else:
            health['overall'] = 'weak'
        
        return health
    
    def _get_recent_break_signals(self, bos_signals: List, choch_signals: List) -> List[Dict]:
        """
        获取最近的突破信号
        """
        recent_signals = []
        
        # 合并所有信号
        all_signals = []
        if bos_signals:
            all_signals.extend([(sig['index'], 'BOS', sig) for sig in bos_signals])
        if choch_signals:
            all_signals.extend([(len(all_signals) + i, 'CHOCH', sig) for i, sig in enumerate(choch_signals)])
        
        # 按时间排序（假设index越大越新）
        all_signals.sort(key=lambda x: x[0], reverse=True)
        
        # 取最近的3个信号
        for idx, signal_type, signal in all_signals[:3]:
            recent_signals.append({
                'type': signal_type,
                'signal_type': signal.get('type', 'unknown'),
                'description': signal.get('description', ''),
                'strength': signal.get('strength', 0),
                'confirmed': signal.get('confirmed', False)
            })
        
        return recent_signals
    
    def get_structure_summary(self, df: pd.DataFrame) -> str:
        """
        获取结构突破分析摘要
        """
        analysis = self.analyze_structure_breaks(df)
        
        summary = f"""
        🏗️ 市场结构分析
        {'='*40}
        结构评分: {analysis['market_structure_score']}/100
        
        结构健康度: {analysis['structure_health']['overall'].upper()}
        - 趋势连续性: {analysis['structure_health']['trend_continuity']}
        - 突破质量: {analysis['structure_health']['breakout_quality']}
        - 噪音水平: {analysis['structure_health']['noise_level']}
        
        突破信号统计:
        - BOS信号: {len(analysis['bos_signals'])} 个
        - CHOCH信号: {len(analysis['choch_signals'])} 个
        
        最近信号:
        """
        
        for i, signal in enumerate(analysis['recent_breaks'], 1):
            confirmed = "✅" if signal.get('confirmed', False) else "⚠️"
            summary += f"\n  {i}. {signal['type']}: {signal['signal_type']} {confirmed}"
            summary += f"\n     {signal['description']}"
            if signal.get('strength', 0) > 0:
                summary += f" (强度: {signal['strength']:.1f}%)"
        
        return summary