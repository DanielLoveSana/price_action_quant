"""
支撑阻力位分析器
基于价格密集区、历史极值点和成交量加权识别支撑阻力区域
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import warnings
warnings.filterwarnings('ignore')


class SupportResistanceAnalyzer:
    """
    支撑阻力位分析器
    
    功能:
    1. 基于价格密集区识别支撑阻力
    2. 基于历史极值点识别关键价位
    3. 基于成交量加权提高准确性
    4. 计算价位强度和重要性
    """
    
    def __init__(self, 
                 zone_threshold: float = 0.02,
                 min_touch_count: int = 3,
                 lookback_period: int = 200):
        """
        初始化支撑阻力分析器
        
        Args:
            zone_threshold: 价格密集区阈值 (百分比)
            min_touch_count: 最小测试次数
            lookback_period: 回看周期
        """
        self.zone_threshold = zone_threshold
        self.min_touch_count = min_touch_count
        self.lookback_period = lookback_period
        
    def analyze_support_resistance(self, df: pd.DataFrame) -> Dict:
        """
        综合分析支撑阻力位
        
        Args:
            df: 包含OHLCV数据的DataFrame
            
        Returns:
            Dict: 支撑阻力分析结果
        """
        if not {'high', 'low', 'close', 'volume'}.issubset(df.columns):
            raise ValueError("DataFrame必须包含'high', 'low', 'close', 'volume'列")
            
        results = {}
        
        # 1. 基于价格密集区的支撑阻力
        results['price_density_zones'] = self._find_price_density_zones(df)
        
        # 2. 基于历史极值点的支撑阻力
        results['historical_extremes'] = self._find_historical_extremes(df)
        
        # 3. 基于成交量加权的支撑阻力
        results['volume_weighted_zones'] = self._find_volume_weighted_zones(df)
        
        # 4. 合并所有支撑阻力位
        results['merged_levels'] = self._merge_support_resistance_levels(
            results['price_density_zones'],
            results['historical_extremes'],
            results['volume_weighted_zones']
        )
        
        # 5. 计算当前价格与关键价位的距离
        results['proximity_analysis'] = self._analyze_price_proximity(
            df, results['merged_levels']
        )
        
        # 6. 计算价位强度评分
        results['strength_scores'] = self._calculate_strength_scores(
            results['merged_levels'], df
        )
        
        return results
    
    def _find_price_density_zones(self, df: pd.DataFrame) -> Dict:
        """
        基于价格密集区识别支撑阻力
        
        使用K-means聚类或直方图分析找到价格聚集区域
        """
        # 获取价格数据
        prices = pd.concat([df['high'], df['low'], df['close']])
        
        # 使用直方图分析价格分布
        price_min = prices.min()
        price_max = prices.max()
        price_range = price_max - price_min
        
        if price_range == 0:
            return {'supports': [], 'resistances': []}
        
        # 创建价格直方图
        num_bins = max(10, min(50, len(prices) // 20))
        hist, bin_edges = np.histogram(prices, bins=num_bins)
        
        # 找到高密度区域
        density_threshold = np.percentile(hist, 75)  # 前25%的高密度区域
        dense_bins = np.where(hist >= density_threshold)[0]
        
        supports = []
        resistances = []
        
        for bin_idx in dense_bins:
            bin_start = bin_edges[bin_idx]
            bin_end = bin_edges[bin_idx + 1]
            bin_center = (bin_start + bin_end) / 2
            bin_density = hist[bin_idx]
            
            # 判断是支撑还是阻力
            current_price = df['close'].iloc[-1]
            
            if bin_center < current_price:
                # 低于当前价格，可能是支撑
                supports.append({
                    'price': bin_center,
                    'range': (bin_start, bin_end),
                    'density': bin_density,
                    'type': 'price_density',
                    'strength': min(bin_density / len(prices) * 100, 100)
                })
            else:
                # 高于当前价格，可能是阻力
                resistances.append({
                    'price': bin_center,
                    'range': (bin_start, bin_end),
                    'density': bin_density,
                    'type': 'price_density',
                    'strength': min(bin_density / len(prices) * 100, 100)
                })
        
        # 按强度排序
        supports.sort(key=lambda x: x['strength'], reverse=True)
        resistances.sort(key=lambda x: x['strength'], reverse=True)
        
        return {
            'supports': supports[:10],  # 取前10个最强的
            'resistances': resistances[:10]
        }
    
    def _find_historical_extremes(self, df: pd.DataFrame) -> Dict:
        """
        基于历史极值点识别关键价位
        """
        # 获取最近的数据
        recent_data = df.tail(self.lookback_period)
        
        # 寻找局部极值点
        swing_highs = []
        swing_lows = []
        
        lookback = 5  # 局部极值检测窗口
        
        for i in range(lookback, len(recent_data) - lookback):
            # 检查局部高点
            if recent_data['high'].iloc[i] == max(
                recent_data['high'].iloc[i-lookback:i+lookback+1]
            ):
                swing_highs.append({
                    'price': recent_data['high'].iloc[i],
                    'index': i + len(df) - len(recent_data),
                    'type': 'swing_high',
                    'strength': 1.0
                })
            
            # 检查局部低点
            if recent_data['low'].iloc[i] == min(
                recent_data['low'].iloc[i-lookback:i+lookback+1]
            ):
                swing_lows.append({
                    'price': recent_data['low'].iloc[i],
                    'index': i + len(df) - len(recent_data),
                    'type': 'swing_low',
                    'strength': 1.0
                })
        
        # 过滤太接近的极值点
        swing_highs = self._filter_close_extremes(swing_highs, is_high=True)
        swing_lows = self._filter_close_extremes(swing_lows, is_high=False)
        
        # 计算测试次数和强度
        for high in swing_highs:
            high['test_count'] = self._count_price_tests(df, high['price'], 'resistance')
            high['strength'] = min(high['test_count'] * 10, 100)
        
        for low in swing_lows:
            low['test_count'] = self._count_price_tests(df, low['price'], 'support')
            low['strength'] = min(low['test_count'] * 10, 100)
        
        return {
            'supports': swing_lows,
            'resistances': swing_highs
        }
    
    def _find_volume_weighted_zones(self, df: pd.DataFrame) -> Dict:
        """
        基于成交量加权的支撑阻力识别
        
        高成交量区域通常代表重要价位
        """
        # 计算每个价格区间的成交量
        price_min = df['low'].min()
        price_max = df['high'].max()
        price_range = price_max - price_min
        
        if price_range == 0:
            return {'supports': [], 'resistances': []}
        
        # 创建价格-成交量分布
        num_bins = 50
        price_bins = np.linspace(price_min, price_max, num_bins + 1)
        
        volume_by_price = np.zeros(num_bins)
        
        for idx in range(len(df)):
            high = df['high'].iloc[idx]
            low = df['low'].iloc[idx]
            volume = df['volume'].iloc[idx]
            
            # 找到价格所在的bin
            high_bin = np.digitize(high, price_bins) - 1
            low_bin = np.digitize(low, price_bins) - 1
            
            # 将成交量分配到相关bins
            if high_bin == low_bin:
                volume_by_price[high_bin] += volume
            else:
                # 简单分配：平均分配到每个bin
                bins_covered = high_bin - low_bin + 1
                volume_per_bin = volume / bins_covered
                for bin_idx in range(low_bin, high_bin + 1):
                    if 0 <= bin_idx < num_bins:
                        volume_by_price[bin_idx] += volume_per_bin
        
        # 找到高成交量区域
        volume_threshold = np.percentile(volume_by_price, 75)
        high_volume_bins = np.where(volume_by_price >= volume_threshold)[0]
        
        supports = []
        resistances = []
        current_price = df['close'].iloc[-1]
        
        for bin_idx in high_volume_bins:
            bin_start = price_bins[bin_idx]
            bin_end = price_bins[bin_idx + 1]
            bin_center = (bin_start + bin_end) / 2
            bin_volume = volume_by_price[bin_idx]
            
            # 计算相对成交量强度
            volume_strength = min(bin_volume / np.max(volume_by_price) * 100, 100)
            
            if bin_center < current_price:
                supports.append({
                    'price': bin_center,
                    'range': (bin_start, bin_end),
                    'volume': bin_volume,
                    'volume_strength': volume_strength,
                    'type': 'volume_weighted',
                    'strength': volume_strength
                })
            else:
                resistances.append({
                    'price': bin_center,
                    'range': (bin_start, bin_end),
                    'volume': bin_volume,
                    'volume_strength': volume_strength,
                    'type': 'volume_weighted',
                    'strength': volume_strength
                })
        
        # 按强度排序
        supports.sort(key=lambda x: x['strength'], reverse=True)
        resistances.sort(key=lambda x: x['strength'], reverse=True)
        
        return {
            'supports': supports[:10],
            'resistances': resistances[:10]
        }
    
    def _filter_close_extremes(self, extremes: List[Dict], is_high: bool = True) -> List[Dict]:
        """
        过滤太接近的极值点
        """
        if not extremes:
            return extremes
        
        filtered = [extremes[0]]
        
        for i in range(1, len(extremes)):
            last_price = filtered[-1]['price']
            current_price = extremes[i]['price']
            
            price_change = abs(current_price - last_price) / last_price
            
            if price_change >= self.zone_threshold:
                # 对于高点，保留更高的；对于低点，保留更低的
                if is_high:
                    if current_price > last_price:
                        filtered[-1] = extremes[i]
                    else:
                        filtered.append(extremes[i])
                else:
                    if current_price < last_price:
                        filtered[-1] = extremes[i]
                    else:
                        filtered.append(extremes[i])
        
        return filtered
    
    def _count_price_tests(self, df: pd.DataFrame, level: float, level_type: str) -> int:
        """
        计算价格测试某个价位的次数
        """
        test_count = 0
        tolerance = level * self.zone_threshold
        
        for idx in range(len(df)):
            high = df['high'].iloc[idx]
            low = df['low'].iloc[idx]
            
            if level_type == 'support':
                # 支撑位：价格接近或轻微跌破后收回
                if abs(low - level) <= tolerance or (low < level and high > level):
                    test_count += 1
            else:  # resistance
                # 阻力位：价格接近或轻微突破后回落
                if abs(high - level) <= tolerance or (high > level and low < level):
                    test_count += 1
        
        return test_count
    
    def _merge_support_resistance_levels(self, 
                                        density_zones: Dict,
                                        historical_extremes: Dict,
                                        volume_zones: Dict) -> Dict:
        """
        合并来自不同方法的支撑阻力位
        """
        # 收集所有支撑位
        all_supports = []
        all_supports.extend(density_zones['supports'])
        all_supports.extend(historical_extremes['supports'])
        all_supports.extend(volume_zones['supports'])
        
        # 收集所有阻力位
        all_resistances = []
        all_resistances.extend(density_zones['resistances'])
        all_resistances.extend(historical_extremes['resistances'])
        all_resistances.extend(volume_zones['resistances'])
        
        # 合并相近的价位
        merged_supports = self._merge_close_levels(all_supports, 'support')
        merged_resistances = self._merge_close_levels(all_resistances, 'resistance')
        
        # 按强度排序
        merged_supports.sort(key=lambda x: x['strength'], reverse=True)
        merged_resistances.sort(key=lambda x: x['strength'], reverse=True)
        
        return {
            'supports': merged_supports[:15],  # 取前15个最强的
            'resistances': merged_resistances[:15],
            'nearest_support': merged_supports[0] if merged_supports else None,
            'nearest_resistance': merged_resistances[0] if merged_resistances else None
        }
    
    def _merge_close_levels(self, levels: List[Dict], level_type: str) -> List[Dict]:
        """
        合并相近的价位
        """
        if not levels:
            return levels
        
        # 按价格排序
        levels.sort(key=lambda x: x['price'])
        
        merged = []
        current_group = [levels[0]]
        
        for i in range(1, len(levels)):
            last_price = current_group[-1]['price']
            current_price = levels[i]['price']
            
            price_change = abs(current_price - last_price) / last_price
            
            if price_change <= self.zone_threshold:
                # 价格相近，合并到同一组
                current_group.append(levels[i])
            else:
                # 价格差异大，创建新组
                merged.append(self._create_merged_level(current_group, level_type))
                current_group = [levels[i]]
        
        # 处理最后一组
        if current_group:
            merged.append(self._create_merged_level(current_group, level_type))
        
        return merged
    
    def _create_merged_level(self, levels: List[Dict], level_type: str) -> Dict:
        """
        创建合并后的价位
        """
        if not levels:
            return None
        
        # 计算加权平均价格
        total_strength = sum(level.get('strength', 1) for level in levels)
        weighted_price = sum(level['price'] * level.get('strength', 1) for level in levels) / total_strength
        
        # 收集所有类型
        types = list(set(level.get('type', 'unknown') for level in levels))
        
        # 计算合并后的强度
        merged_strength = min(sum(level.get('strength', 0) for level in levels) / len(levels), 100)
        
        # 计算测试次数
        test_count = sum(level.get('test_count', 0) for level in levels)
        
        return {
            'price': weighted_price,
            'types': types,
            'strength': merged_strength,
            'test_count': test_count,
            'component_count': len(levels),
            'type': level_type,
            'description': f'合并价位 ({len(levels)}个来源)'
        }
    
    def _analyze_price_proximity(self, df: pd.DataFrame, merged_levels: Dict) -> Dict:
        """
        分析当前价格与关键价位的距离
        """
        current_price = df['close'].iloc[-1]
        
        proximity = {
            'current_price': current_price,
            'nearest_support': None,
            'nearest_resistance': None,
            'support_distance_pct': None,
            'resistance_distance_pct': None,
            'in_support_zone': False,
            'in_resistance_zone': False
        }
        
        # 找到最近的支撑位
        if merged_levels['supports']:
            nearest_support = min(
                merged_levels['supports'],
                key=lambda x: abs(x['price'] - current_price)
            )
            proximity['nearest_support'] = nearest_support
            proximity['support_distance_pct'] = abs(current_price - nearest_support['price']) / current_price * 100
            
            # 检查是否在支撑区域内
            if current_price <= nearest_support['price'] * (1 + self.zone_threshold):
                proximity['in_support_zone'] = True
        
        # 找到最近的阻力位
        if merged_levels['resistances']:
            nearest_resistance = min(
                merged_levels['resistances'],
                key=lambda x: abs(x['price'] - current_price)
            )
            proximity['nearest_resistance'] = nearest_resistance
            proximity['resistance_distance_pct'] = abs(nearest_resistance['price'] - current_price) / current_price * 100
            
            # 检查是否在阻力区域内
            if current_price >= nearest_resistance['price'] * (1 - self.zone_threshold):
                proximity['in_resistance_zone'] = True
        
        return proximity
    
    def _calculate_strength_scores(self, merged_levels: Dict, df: pd.DataFrame) -> Dict:
        """
        计算价位强度评分
        """
        scores = {}
        
        # 支撑位强度评分
        support_scores = []
        for support in merged_levels['supports']:
            score = {
                'price': support['price'],
                'base_strength': support['strength'],
                'test_count_score': min(support.get('test_count', 0) * 5, 50),
                'volume_confirmation': 0,
                'time_persistence': 0,
                'total_score': support['strength']
            }
            
            # 检查成交量确认
            if 'volume_weighted' in support.get('types', []):
                score['volume_confirmation'] = 20
            
            # 检查时间持久性 (如果价位存在时间较长)
            # 这里简化处理，实际需要更复杂的时间分析
            if support.get('component_count', 0) >= 2:
                score['time_persistence'] = 10
            
            score['total_score'] = min(
                score['base_strength'] + 
                score['test_count_score'] + 
                score['volume_confirmation'] + 
                score['time_persistence'], 
                100
            )
            
            support_scores.append(score)
        
        # 阻力位强度评分
        resistance_scores = []
        for resistance in merged_levels['resistances']:
            score = {
                'price': resistance['price'],
                'base_strength': resistance['strength'],
                'test_count_score': min(resistance.get('test_count', 0) * 5, 50),
                'volume_confirmation': 0,
                'time_persistence': 0,
                'total_score': resistance['strength']
            }
            
            if 'volume_weighted' in resistance.get('types', []):
                score['volume_confirmation'] = 20
            
            if resistance.get('component_count', 0) >= 2:
                score['time_persistence'] = 10
            
            score['total_score'] = min(
                score['base_strength'] + 
                score['test_count_score'] + 
                score['volume_confirmation'] + 
                score['time_persistence'], 
                100
            )
            
            resistance_scores.append(score)
        
        # 按总分排序
        support_scores.sort(key=lambda x: x['total_score'], reverse=True)
        resistance_scores.sort(key=lambda x: x['total_score'], reverse=True)
        
        scores['supports'] = support_scores
        scores['resistances'] = resistance_scores
        
        # 关键价位识别
        key_supports = [s for s in support_scores if s['total_score'] >= 70]
        key_resistances = [r for r in resistance_scores if r['total_score'] >= 70]
        
        scores['key_supports'] = key_supports[:5]  # 取前5个关键支撑
        scores['key_resistances'] = key_resistances[:5]  # 取前5个关键阻力
        
        return scores
    
    def get_support_resistance_summary(self, df: pd.DataFrame) -> str:
        """
        获取支撑阻力分析摘要
        """
        analysis = self.analyze_support_resistance(df)
        
        summary = f"""
        🏗️ 支撑阻力分析
        {'='*40}
        当前价格: {analysis['proximity_analysis']['current_price']:.2f}
        
        支撑位统计:
        - 识别到 {len(analysis['merged_levels']['supports'])} 个支撑位
        - 关键支撑: {len(analysis['strength_scores']['key_supports'])} 个
        
        阻力位统计:
        - 识别到 {len(analysis['merged_levels']['resistances'])} 个阻力位
        - 关键阻力: {len(analysis['strength_scores']['key_resistances'])} 个
        
        距离分析:
        """
        
        proximity = analysis['proximity_analysis']
        if proximity['nearest_support']:
            distance = proximity['support_distance_pct']
            in_zone = "✅" if proximity['in_support_zone'] else "❌"
            summary += f"\n  最近支撑: {proximity['nearest_support']['price']:.2f}"
            summary += f" (距离: {distance:.2f}%) {in_zone}"
        
        if proximity['nearest_resistance']:
            distance = proximity['resistance_distance_pct']
            in_zone = "✅" if proximity['in_resistance_zone'] else "❌"
            summary += f"\n  最近阻力: {proximity['nearest_resistance']['price']:.2f}"
            summary += f" (距离: {distance:.2f}%) {in_zone}"
        
        # 显示最强支撑阻力
        if analysis['strength_scores']['key_supports']:
            strongest_support = analysis['strength_scores']['key_supports'][0]
            summary += f"\n\n  最强支撑: {strongest_support['price']:.2f}"
            summary += f" (强度: {strongest_support['total_score']:.0f}/100)"
        
        if analysis['strength_scores']['key_resistances']:
            strongest_resistance = analysis['strength_scores']['key_resistances'][0]
            summary += f"\n  最强阻力: {strongest_resistance['price']:.2f}"
            summary += f" (强度: {strongest_resistance['total_score']:.0f}/100)"
        
        return summary