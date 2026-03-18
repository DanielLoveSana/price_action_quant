"""
趋势状态识别因子
基于HH/HL（Higher High/Higher Low）或LL/LH（Lower Low/Lower High）序列判断趋势
"""

import pandas as pd
import numpy as np
from typing import Tuple, Dict, List, Optional
import warnings
warnings.filterwarnings('ignore')


class TrendAnalyzer:
    """
    趋势分析器 - 识别市场趋势方向和强度
    
    功能:
    1. 趋势方向判断 (上升/下降/横盘)
    2. 趋势强度量化 (ADX或价格与EMA偏离度)
    3. 摆动点检测 (ZigZag算法)
    """
    
    def __init__(self, window: int = 20, adx_period: int = 14, zigzag_threshold: float = 0.05):
        """
        初始化趋势分析器
        
        Args:
            window: 趋势判断窗口大小
            adx_period: ADX计算周期
            zigzag_threshold: ZigZag算法阈值 (百分比)
        """
        self.window = window
        self.adx_period = adx_period
        self.zigzag_threshold = zigzag_threshold
        
    def analyze_trend(self, df: pd.DataFrame) -> Dict:
        """
        综合分析趋势状态
        
        Args:
            df: 包含OHLCV数据的DataFrame，必须有'high', 'low', 'close'列
            
        Returns:
            Dict: 包含趋势分析结果的字典
        """
        if not {'high', 'low', 'close'}.issubset(df.columns):
            raise ValueError("DataFrame必须包含'high', 'low', 'close'列")
            
        results = {}
        
        # 1. 趋势方向判断
        results['trend_direction'] = self._get_trend_direction(df)
        
        # 2. 趋势强度计算
        results['trend_strength'] = self._calculate_trend_strength(df)
        
        # 3. 摆动点检测
        swing_points = self._detect_swing_points(df)
        results['swing_points'] = swing_points
        
        # 4. 趋势分类
        results['trend_class'] = self._classify_trend(
            results['trend_direction'], 
            results['trend_strength']
        )
        
        # 5. 趋势线计算
        if len(swing_points['highs']) >= 2:
            results['trendline_resistance'] = self._calculate_trendline(
                swing_points['highs'], 'resistance'
            )
        if len(swing_points['lows']) >= 2:
            results['trendline_support'] = self._calculate_trendline(
                swing_points['lows'], 'support'
            )
            
        return results
    
    def _get_trend_direction(self, df: pd.DataFrame) -> str:
        """
        判断趋势方向
        
        Returns:
            str: 'uptrend', 'downtrend', 或 'sideways'
        """
        # 方法1: 基于HH/HL和LL/LH序列
        highs = df['high'].values
        lows = df['low'].values
        
        # 检测最近的高点和低点序列
        recent_highs = highs[-self.window:]
        recent_lows = lows[-self.window:]
        
        # 计算高点和低点的变化
        high_changes = np.diff(recent_highs)
        low_changes = np.diff(recent_lows)
        
        # 判断序列特征
        higher_highs = np.sum(high_changes > 0) / len(high_changes) > 0.6
        higher_lows = np.sum(low_changes > 0) / len(low_changes) > 0.6
        lower_highs = np.sum(high_changes < 0) / len(high_changes) > 0.6
        lower_lows = np.sum(low_changes < 0) / len(low_changes) > 0.6
        
        if higher_highs and higher_lows:
            return 'uptrend'
        elif lower_highs and lower_lows:
            return 'downtrend'
        else:
            # 方法2: 使用移动平均线判断
            ma_short = df['close'].rolling(window=10).mean().iloc[-1]
            ma_long = df['close'].rolling(window=30).mean().iloc[-1]
            
            if ma_short > ma_long * 1.01:  # 短期均线高于长期均线1%以上
                return 'uptrend'
            elif ma_short < ma_long * 0.99:  # 短期均线低于长期均线1%以上
                return 'downtrend'
            else:
                return 'sideways'
    
    def _calculate_trend_strength(self, df: pd.DataFrame) -> float:
        """
        计算趋势强度 (0-100)
        
        使用ADX指标或价格与EMA的偏离度
        """
        try:
            # 尝试使用ADX指标
            from ta.trend import ADXIndicator
            
            high = df['high']
            low = df['low']
            close = df['close']
            
            adx_indicator = ADXIndicator(high=high, low=low, close=close, window=self.adx_period)
            adx = adx_indicator.adx()
            
            # 取最近的值
            recent_adx = adx.iloc[-min(5, len(adx)):].mean()
            
            # ADX值范围通常在0-100之间，但实际很少超过60
            strength = min(recent_adx / 60 * 100, 100)
            return max(strength, 0)
            
        except ImportError:
            # 如果ta库不可用，使用价格与EMA的偏离度
            ema_short = df['close'].ewm(span=10).mean()
            ema_long = df['close'].ewm(span=30).mean()
            
            # 计算价格与长期EMA的偏离度
            price = df['close'].iloc[-1]
            ema_value = ema_long.iloc[-1]
            
            if ema_value == 0:
                return 0
                
            deviation = abs(price - ema_value) / ema_value * 100
            
            # 标准化到0-100范围
            strength = min(deviation * 5, 100)  # 假设5%偏离对应100强度
            return strength
    
    def _detect_swing_points(self, df: pd.DataFrame) -> Dict:
        """
        使用ZigZag算法检测摆动点
        
        Returns:
            Dict: 包含高点和低点摆动点的字典
        """
        highs = df['high'].values
        lows = df['low'].values
        
        # 简化的ZigZag算法
        swing_highs = []
        swing_lows = []
        
        # 寻找局部极值点
        for i in range(1, len(highs) - 1):
            # 检查是否为局部高点
            if highs[i] > highs[i-1] and highs[i] > highs[i+1]:
                # 检查是否超过阈值
                if i > 0 and i < len(highs) - 1:
                    prev_extreme = max(swing_highs[-1][1] if swing_highs else highs[i-1], 
                                     swing_lows[-1][1] if swing_lows else lows[i-1])
                    change = abs(highs[i] - prev_extreme) / prev_extreme
                    if change >= self.zigzag_threshold:
                        swing_highs.append((i, highs[i]))
            
            # 检查是否为局部低点
            if lows[i] < lows[i-1] and lows[i] < lows[i+1]:
                if i > 0 and i < len(lows) - 1:
                    prev_extreme = min(swing_highs[-1][1] if swing_highs else highs[i-1],
                                     swing_lows[-1][1] if swing_lows else lows[i-1])
                    change = abs(lows[i] - prev_extreme) / prev_extreme
                    if change >= self.zigzag_threshold:
                        swing_lows.append((i, lows[i]))
        
        # 转换为DataFrame格式
        high_points = pd.DataFrame(swing_highs, columns=['index', 'price']) if swing_highs else pd.DataFrame(columns=['index', 'price'])
        low_points = pd.DataFrame(swing_lows, columns=['index', 'price']) if swing_lows else pd.DataFrame(columns=['index', 'price'])
        
        return {
            'highs': high_points,
            'lows': low_points,
            'last_high': high_points.iloc[-1] if len(high_points) > 0 else None,
            'last_low': low_points.iloc[-1] if len(low_points) > 0 else None
        }
    
    def _classify_trend(self, direction: str, strength: float) -> str:
        """
        根据方向和强度分类趋势
        
        Returns:
            str: 趋势分类描述
        """
        if strength < 20:
            return 'weak'
        elif strength < 50:
            if direction == 'uptrend':
                return 'moderate_uptrend'
            elif direction == 'downtrend':
                return 'moderate_downtrend'
            else:
                return 'weak_sideways'
        elif strength < 80:
            if direction == 'uptrend':
                return 'strong_uptrend'
            elif direction == 'downtrend':
                return 'strong_downtrend'
            else:
                return 'strong_sideways'
        else:
            if direction == 'uptrend':
                return 'very_strong_uptrend'
            elif direction == 'downtrend':
                return 'very_strong_downtrend'
            else:
                return 'very_strong_sideways'
    
    def _calculate_trendline(self, points: pd.DataFrame, line_type: str) -> Dict:
        """
        计算趋势线
        
        Args:
            points: 摆动点DataFrame
            line_type: 'support' 或 'resistance'
            
        Returns:
            Dict: 趋势线信息
        """
        if len(points) < 2:
            return None
            
        # 取最近的两个点
        recent_points = points.tail(2)
        
        if len(recent_points) < 2:
            return None
            
        x1, y1 = recent_points.iloc[0]['index'], recent_points.iloc[0]['price']
        x2, y2 = recent_points.iloc[1]['index'], recent_points.iloc[1]['price']
        
        # 计算斜率和截距
        if x2 != x1:
            slope = (y2 - y1) / (x2 - x1)
            intercept = y1 - slope * x1
            
            # 计算角度（度）
            angle = np.degrees(np.arctan(slope))
            
            return {
                'slope': slope,
                'intercept': intercept,
                'angle': angle,
                'start_point': (x1, y1),
                'end_point': (x2, y2),
                'type': line_type
            }
        
        return None
    
    def get_trend_summary(self, df: pd.DataFrame) -> str:
        """
        获取趋势分析摘要
        
        Returns:
            str: 趋势分析摘要文本
        """
        analysis = self.analyze_trend(df)
        
        summary = f"""
        📊 趋势分析摘要
        {'='*40}
        趋势方向: {analysis['trend_direction'].upper()}
        趋势强度: {analysis['trend_strength']:.1f}/100
        趋势分类: {analysis['trend_class'].replace('_', ' ').upper()}
        
        摆动点统计:
        - 高点摆动点: {len(analysis['swing_points']['highs'])} 个
        - 低点摆动点: {len(analysis['swing_points']['lows'])} 个
        
        趋势线:
        - 阻力线: {'已计算' if analysis.get('trendline_resistance') else '未计算'}
        - 支撑线: {'已计算' if analysis.get('trendline_support') else '未计算'}
        """
        
        return summary