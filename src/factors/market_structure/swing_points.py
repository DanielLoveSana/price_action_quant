"""
摆动点检测器
专门化的ZigZag算法实现，用于检测关键转折点
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')


class SwingPointDetector:
    """
    摆动点检测器 - 专门化的ZigZag算法实现
    
    功能:
    1. 高效检测局部高点和低点
    2. 过滤噪音摆动点
    3. 计算摆动点统计信息
    4. 识别关键转折区域
    """
    
    def __init__(self, threshold: float = 0.03, lookback: int = 5, min_swing_distance: int = 10):
        """
        初始化摆动点检测器
        
        Args:
            threshold: 最小价格变化阈值 (百分比)
            lookback: 局部极值检测窗口
            min_swing_distance: 最小摆动点距离 (K线数量)
        """
        self.threshold = threshold
        self.lookback = lookback
        self.min_swing_distance = min_swing_distance
        
    def detect_swing_points(self, df: pd.DataFrame, use_advanced: bool = True) -> Dict:
        """
        检测摆动点
        
        Args:
            df: 包含OHLCV数据的DataFrame
            use_advanced: 是否使用高级算法
            
        Returns:
            Dict: 摆动点检测结果
        """
        if not {'high', 'low'}.issubset(df.columns):
            raise ValueError("DataFrame必须包含'high', 'low'列")
            
        if use_advanced:
            return self._detect_swing_points_advanced(df)
        else:
            return self._detect_swing_points_basic(df)
    
    def _detect_swing_points_basic(self, df: pd.DataFrame) -> Dict:
        """
        基础摆动点检测算法
        """
        highs = df['high'].values
        lows = df['low'].values
        
        swing_highs = []
        swing_lows = []
        
        # 简单的局部极值检测
        for i in range(self.lookback, len(highs) - self.lookback):
            # 检查局部高点
            if highs[i] == max(highs[i-self.lookback:i+self.lookback+1]):
                swing_highs.append((i, highs[i]))
            
            # 检查局部低点
            if lows[i] == min(lows[i-self.lookback:i+self.lookback+1]):
                swing_lows.append((i, lows[i]))
        
        # 过滤太接近的摆动点
        swing_highs = self._filter_close_points(swing_highs, is_high=True)
        swing_lows = self._filter_close_points(swing_lows, is_high=False)
        
        return self._format_swing_points(swing_highs, swing_lows, df)
    
    def _detect_swing_points_advanced(self, df: pd.DataFrame) -> Dict:
        """
        高级摆动点检测算法 (改进的ZigZag)
        """
        highs = df['high'].values
        lows = df['low'].values
        
        # 初始化
        swing_highs = []
        swing_lows = []
        last_extreme = None
        last_extreme_type = None  # 'high' 或 'low'
        last_extreme_idx = -1
        
        i = self.lookback
        while i < len(highs) - self.lookback:
            # 寻找局部高点
            local_high_idx = i
            local_high = highs[i]
            
            for j in range(i - self.lookback, min(i + self.lookback + 1, len(highs))):
                if highs[j] > local_high:
                    local_high = highs[j]
                    local_high_idx = j
            
            # 寻找局部低点
            local_low_idx = i
            local_low = lows[i]
            
            for j in range(i - self.lookback, min(i + self.lookback + 1, len(lows))):
                if lows[j] < local_low:
                    local_low = lows[j]
                    local_low_idx = j
            
            # 决定当前是高点还是低点
            if local_high_idx == local_low_idx:
                # 同一点，选择幅度更大的
                high_range = highs[local_high_idx] - lows[local_high_idx]
                i += 1
                continue
            
            # 检查是否满足阈值条件
            if last_extreme is not None:
                # 从上一个极值点到当前潜在极值点的变化
                if last_extreme_type == 'high':
                    # 上一个极值是高点，现在应该找低点
                    change = (last_extreme - local_low) / last_extreme
                    if change >= self.threshold and abs(local_low_idx - last_extreme_idx) >= self.min_swing_distance:
                        swing_lows.append((local_low_idx, local_low))
                        last_extreme = local_low
                        last_extreme_type = 'low'
                        last_extreme_idx = local_low_idx
                        i = local_low_idx + self.min_swing_distance
                        continue
                else:
                    # 上一个极值是低点，现在应该找高点
                    change = (local_high - last_extreme) / last_extreme
                    if change >= self.threshold and abs(local_high_idx - last_extreme_idx) >= self.min_swing_distance:
                        swing_highs.append((local_high_idx, local_high))
                        last_extreme = local_high
                        last_extreme_type = 'high'
                        last_extreme_idx = local_high_idx
                        i = local_high_idx + self.min_swing_distance
                        continue
            
            # 第一个极值点
            if last_extreme is None:
                # 选择第一个显著的极值点
                if local_high > df['close'].mean() * 1.05:  # 显著高于平均
                    swing_highs.append((local_high_idx, local_high))
                    last_extreme = local_high
                    last_extreme_type = 'high'
                    last_extreme_idx = local_high_idx
                elif local_low < df['close'].mean() * 0.95:  # 显著低于平均
                    swing_lows.append((local_low_idx, local_low))
                    last_extreme = local_low
                    last_extreme_type = 'low'
                    last_extreme_idx = local_low_idx
            
            i += 1
        
        # 过滤和格式化
        swing_highs = self._filter_close_points(swing_highs, is_high=True)
        swing_lows = self._filter_close_points(swing_lows, is_high=False)
        
        return self._format_swing_points(swing_highs, swing_lows, df)
    
    def _filter_close_points(self, points: List[Tuple], is_high: bool = True) -> List[Tuple]:
        """
        过滤太接近的摆动点
        """
        if not points:
            return points
        
        filtered = [points[0]]
        
        for i in range(1, len(points)):
            last_idx, last_price = filtered[-1]
            current_idx, current_price = points[i]
            
            # 检查距离和价格变化
            idx_distance = abs(current_idx - last_idx)
            price_change = abs(current_price - last_price) / last_price
            
            # 保留条件：足够远或价格变化足够大
            if idx_distance >= self.min_swing_distance or price_change >= self.threshold:
                # 对于高点，保留更高的；对于低点，保留更低的
                if is_high:
                    if current_price > last_price:
                        filtered[-1] = (current_idx, current_price)
                    else:
                        filtered.append((current_idx, current_price))
                else:
                    if current_price < last_price:
                        filtered[-1] = (current_idx, current_price)
                    else:
                        filtered.append((current_idx, current_price))
        
        return filtered
    
    def _format_swing_points(self, swing_highs: List, swing_lows: List, df: pd.DataFrame) -> Dict:
        """
        格式化摆动点数据
        """
        # 转换为DataFrame
        high_points = pd.DataFrame(swing_highs, columns=['index', 'price']) if swing_highs else pd.DataFrame(columns=['index', 'price'])
        low_points = pd.DataFrame(swing_lows, columns=['index', 'price']) if swing_lows else pd.DataFrame(columns=['index', 'price'])
        
        # 添加时间戳
        if 'timestamp' in df.columns or 'datetime' in df.columns:
            time_col = 'timestamp' if 'timestamp' in df.columns else 'datetime'
            high_points['timestamp'] = df.iloc[high_points['index'].values][time_col].values if len(high_points) > 0 else []
            low_points['timestamp'] = df.iloc[low_points['index'].values][time_col].values if len(low_points) > 0 else []
        
        # 计算统计信息
        stats = self._calculate_swing_stats(high_points, low_points)
        
        # 识别关键转折区域
        key_areas = self._identify_key_areas(high_points, low_points, df)
        
        return {
            'highs': high_points,
            'lows': low_points,
            'stats': stats,
            'key_areas': key_areas,
            'last_high': high_points.iloc[-1] if len(high_points) > 0 else None,
            'last_low': low_points.iloc[-1] if len(low_points) > 0 else None,
            'count': {
                'highs': len(high_points),
                'lows': len(low_points),
                'total': len(high_points) + len(low_points)
            }
        }
    
    def _calculate_swing_stats(self, high_points: pd.DataFrame, low_points: pd.DataFrame) -> Dict:
        """
        计算摆动点统计信息
        """
        stats = {}
        
        # 高点统计
        if len(high_points) > 0:
            stats['highs'] = {
                'count': len(high_points),
                'avg_price': high_points['price'].mean(),
                'min_price': high_points['price'].min(),
                'max_price': high_points['price'].max(),
                'std_price': high_points['price'].std(),
                'avg_distance': high_points['index'].diff().mean() if len(high_points) > 1 else 0
            }
        
        # 低点统计
        if len(low_points) > 0:
            stats['lows'] = {
                'count': len(low_points),
                'avg_price': low_points['price'].mean(),
                'min_price': low_points['price'].min(),
                'max_price': low_points['price'].max(),
                'std_price': low_points['price'].std(),
                'avg_distance': low_points['index'].diff().mean() if len(low_points) > 1 else 0
            }
        
        # 整体统计
        if len(high_points) > 0 and len(low_points) > 0:
            all_points = pd.concat([high_points, low_points]).sort_values('index')
            stats['overall'] = {
                'total_count': len(all_points),
                'price_range': all_points['price'].max() - all_points['price'].min(),
                'avg_swing_size': all_points['price'].diff().abs().mean(),
                'swing_density': len(all_points) / (all_points['index'].max() - all_points['index'].min() + 1) if len(all_points) > 1 else 0
            }
        
        return stats
    
    def _identify_key_areas(self, high_points: pd.DataFrame, low_points: pd.DataFrame, df: pd.DataFrame) -> Dict:
        """
        识别关键转折区域
        """
        key_areas = {
            'support_clusters': [],
            'resistance_clusters': [],
            'consolidation_zones': []
        }
        
        # 识别支撑集群 (低点聚集区域)
        if len(low_points) >= 3:
            low_prices = low_points['price'].values
            low_indices = low_points['index'].values
            
            # 简单的聚类算法
            clusters = []
            current_cluster = []
            
            for i in range(len(low_prices)):
                if not current_cluster:
                    current_cluster.append(i)
                else:
                    # 检查价格是否接近集群
                    last_price = low_prices[current_cluster[-1]]
                    current_price = low_prices[i]
                    price_diff = abs(current_price - last_price) / last_price
                    
                    if price_diff < self.threshold * 0.5:  # 更宽松的阈值
                        current_cluster.append(i)
                    else:
                        if len(current_cluster) >= 2:  # 至少2个点形成集群
                            clusters.append(current_cluster)
                        current_cluster = [i]
            
            if len(current_cluster) >= 2:
                clusters.append(current_cluster)
            
            # 格式化支撑集群
            for cluster in clusters:
                cluster_prices = low_prices[cluster]
                cluster_indices = low_indices[cluster]
                
                key_areas['support_clusters'].append({
                    'price_level': np.mean(cluster_prices),
                    'price_range': (np.min(cluster_prices), np.max(cluster_prices)),
                    'strength': len(cluster),  # 点数越多强度越高
                    'indices': cluster_indices.tolist(),
                    'description': f'支撑集群 ({len(cluster)}个低点)'
                })
        
        # 识别阻力集群 (高点聚集区域)
        if len(high_points) >= 3:
            high_prices = high_points['price'].values
            high_indices = high_points['index'].values
            
            clusters = []
            current_cluster = []
            
            for i in range(len(high_prices)):
                if not current_cluster:
                    current_cluster.append(i)
                else:
                    last_price = high_prices[current_cluster[-1]]
                    current_price = high_prices[i]
                    price_diff = abs(current_price - last_price) / last_price
                    
                    if price_diff < self.threshold * 0.5:
                        current_cluster.append(i)
                    else:
                        if len(current_cluster) >= 2:
                            clusters.append(current_cluster)
                        current_cluster = [i]
            
            if len(current_cluster) >= 2:
                clusters.append(current_cluster)
            
            # 格式化阻力集群
            for cluster in clusters:
                cluster_prices = high_prices[cluster]
                cluster_indices = high_indices[cluster]
                
                key_areas['resistance_clusters'].append({
                    'price_level': np.mean(cluster_prices),
                    'price_range': (np.min(cluster_prices), np.max(cluster_prices)),
                    'strength': len(cluster),
                    'indices': cluster_indices.tolist(),
                    'description': f'阻力集群 ({len(cluster)}个高点)'
                })
        
        # 识别震荡区域 (支撑和阻力接近)
        if key_areas['support_clusters'] and key_areas['resistance_clusters']:
            for support in key_areas['support_clusters']:
                for resistance in key_areas['resistance_clusters']:
                    support_level = support['price_level']
                    resistance_level = resistance['price_level']
                    
                    # 检查是否形成震荡区间
                    range_size = abs(resistance_level - support_level) / support_level
                    
                    if range_size < self.threshold * 2:  # 窄幅区间
                        key_areas['consolidation_zones'].append({
                            'support_level': support_level,
                            'resistance_level': resistance_level,
                            'range_size': range_size * 100,  # 百分比
                            'support_strength': support['strength'],
                            'resistance_strength': resistance['strength'],
                            'description': f'震荡区间 {support_level:.2f}-{resistance_level:.2f}'
                        })
        
        return key_areas
    
    def get_swing_summary(self, df: pd.DataFrame) -> str:
        """
        获取摆动点分析摘要
        """
        swing_data = self.detect_swing_points(df, use_advanced=True)
        
        summary = f"""
        📈 摆动点分析
        {'='*40}
        摆动点统计:
        - 高点摆动点: {swing_data['count']['highs']} 个
        - 低点摆动点: {swing_data['count']['lows']} 个
        - 总计: {swing_data['count']['total']} 个
        
        关键区域:
        - 支撑集群: {len(swing_data['key_areas']['support_clusters'])} 个
        - 阻力集群: {len(swing_data['key_areas']['resistance_clusters'])} 个
        - 震荡区间: {len(swing_data['key_areas']['consolidation_zones'])} 个
        
        最近摆动点:
        """
        
        if swing_data['last_high'] is not None:
            last_high = swing_data['last_high']
            summary += f"\n  🏔️ 最近高点: {last_high['price']:.2f}"
            if 'timestamp' in last_high:
                summary += f" (时间: {last_high['timestamp']})"
        
        if swing_data['last_low'] is not None:
            last_low = swing_data['last_low']
            summary += f"\n  ⛰️ 最近低点: {last_low['price']:.2f}"
            if 'timestamp' in last_low:
                summary += f" (时间: {last_low['timestamp']})"
        
        # 显示关键支撑阻力
        if swing_data['key_areas']['support_clusters']:
            strongest_support = max(swing_data['key_areas']['support_clusters'], key=lambda x: x['strength'])
            summary += f"\n  🛡️  最强支撑: {strongest_support['price_level']:.2f} (强度: {strongest_support['strength']})"
        
        if swing_data['key_areas']['resistance_clusters']:
            strongest_resistance = max(swing_data['key_areas']['resistance_clusters'], key=lambda x: x['strength'])
            summary += f"\n  🚧 最强阻力: {strongest_resistance['price_level']:.2f} (强度: {strongest_resistance['strength']})"
        
        if swing_data['key_areas']['consolidation_zones']:
            consolidation = swing_data['key_areas']['consolidation_zones'][0]
            summary += f"\n  🔄 震荡区间: {consolidation['support_level']:.2f} - {consolidation['resistance_level']:.2f}"
            summary += f" (宽度: {consolidation['range_size']:.1f}%)"
        
        return summary