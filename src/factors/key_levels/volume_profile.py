"""
成交量分布分析器
分析成交量在不同价格区间的分布，识别高成交量节点和成交量缺口
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import warnings
warnings.filterwarnings('ignore')


class VolumeProfileAnalyzer:
    """
    成交量分布分析器
    
    功能:
    1. 成交量分布直方图分析
    2. 高成交量节点 (Volume Nodes) 识别
    3. 成交量缺口 (Volume Gaps) 检测
    4. 成交量控制点 (Points of Control) 计算
    5. 成交量分布形态分析
    """
    
    def __init__(self, 
                 num_bins: int = 50,
                 volume_threshold_pct: float = 0.7,
                 gap_threshold_pct: float = 0.3):
        """
        初始化成交量分布分析器
        
        Args:
            num_bins: 价格区间数量
            volume_threshold_pct: 高成交量阈值 (百分比)
            gap_threshold_pct: 成交量缺口阈值 (百分比)
        """
        self.num_bins = num_bins
        self.volume_threshold_pct = volume_threshold_pct
        self.gap_threshold_pct = gap_threshold_pct
        
    def analyze_volume_profile(self, df: pd.DataFrame) -> Dict:
        """
        分析成交量分布
        
        Args:
            df: 包含OHLCV数据的DataFrame
            
        Returns:
            Dict: 成交量分布分析结果
        """
        if not {'high', 'low', 'close', 'volume'}.issubset(df.columns):
            raise ValueError("DataFrame必须包含'high', 'low', 'close', 'volume'列")
            
        results = {}
        
        # 1. 计算基础成交量分布
        results['basic_profile'] = self._calculate_basic_volume_profile(df)
        
        # 2. 识别高成交量节点
        results['volume_nodes'] = self._identify_volume_nodes(results['basic_profile'])
        
        # 3. 检测成交量缺口
        results['volume_gaps'] = self._detect_volume_gaps(results['basic_profile'])
        
        # 4. 计算成交量控制点
        results['control_points'] = self._calculate_control_points(results['basic_profile'])
        
        # 5. 分析成交量分布形态
        results['profile_patterns'] = self._analyze_profile_patterns(results['basic_profile'])
        
        # 6. 计算当前价格与成交量分布的关系
        results['price_volume_relation'] = self._analyze_price_volume_relation(
            df, results['basic_profile'], results['volume_nodes']
        )
        
        return results
    
    def _calculate_basic_volume_profile(self, df: pd.DataFrame) -> Dict:
        """
        计算基础成交量分布
        """
        # 获取价格范围
        price_min = df['low'].min()
        price_max = df['high'].max()
        price_range = price_max - price_min
        
        if price_range == 0:
            return {
                'price_bins': [],
                'volume_bins': [],
                'price_centers': [],
                'total_volume': 0,
                'price_min': price_min,
                'price_max': price_max
            }
        
        # 创建价格区间
        price_bins = np.linspace(price_min, price_max, self.num_bins + 1)
        price_centers = (price_bins[:-1] + price_bins[1:]) / 2
        
        # 初始化成交量数组
        volume_bins = np.zeros(self.num_bins)
        
        # 分配成交量到各个价格区间
        for idx in range(len(df)):
            high = df['high'].iloc[idx]
            low = df['low'].iloc[idx]
            volume = df['volume'].iloc[idx]
            
            # 找到价格区间索引
            high_bin = np.digitize(high, price_bins) - 1
            low_bin = np.digitize(low, price_bins) - 1
            
            # 确保索引在有效范围内
            high_bin = min(max(high_bin, 0), self.num_bins - 1)
            low_bin = min(max(low_bin, 0), self.num_bins - 1)
            
            if high_bin == low_bin:
                # K线完全在一个区间内
                volume_bins[high_bin] += volume
            else:
                # K线跨越多个区间，按价格范围分配成交量
                bins_covered = high_bin - low_bin + 1
                price_per_bin = (high - low) / bins_covered
                
                for bin_idx in range(low_bin, high_bin + 1):
                    if 0 <= bin_idx < self.num_bins:
                        # 计算该区间占K线价格范围的比例
                        bin_low = max(price_bins[bin_idx], low)
                        bin_high = min(price_bins[bin_idx + 1], high)
                        bin_range = bin_high - bin_low
                        
                        if bin_range > 0:
                            volume_share = volume * (bin_range / (high - low))
                            volume_bins[bin_idx] += volume_share
        
        # 计算相对成交量
        max_volume = np.max(volume_bins) if len(volume_bins) > 0 else 0
        relative_volume = volume_bins / max_volume if max_volume > 0 else volume_bins
        
        return {
            'price_bins': price_bins,
            'volume_bins': volume_bins,
            'relative_volume': relative_volume,
            'price_centers': price_centers,
            'total_volume': np.sum(volume_bins),
            'max_volume': max_volume,
            'price_min': price_min,
            'price_max': price_max,
            'price_range': price_range
        }
    
    def _identify_volume_nodes(self, profile: Dict) -> Dict:
        """
        识别高成交量节点
        """
        volume_bins = profile['volume_bins']
        price_centers = profile['price_centers']
        relative_volume = profile['relative_volume']
        
        if len(volume_bins) == 0:
            return {'high_volume_nodes': [], 'low_volume_nodes': []}
        
        # 高成交量节点 (超过阈值)
        high_volume_threshold = np.percentile(volume_bins, self.volume_threshold_pct * 100)
        high_volume_indices = np.where(volume_bins >= high_volume_threshold)[0]
        
        high_volume_nodes = []
        for idx in high_volume_indices:
            high_volume_nodes.append({
                'price': price_centers[idx],
                'volume': volume_bins[idx],
                'relative_volume': relative_volume[idx],
                'type': 'high_volume_node',
                'strength': min(relative_volume[idx] * 100, 100)
            })
        
        # 低成交量节点 (低于阈值)
        low_volume_threshold = np.percentile(volume_bins, (1 - self.volume_threshold_pct) * 100)
        low_volume_indices = np.where(volume_bins <= low_volume_threshold)[0]
        
        low_volume_nodes = []
        for idx in low_volume_indices:
            low_volume_nodes.append({
                'price': price_centers[idx],
                'volume': volume_bins[idx],
                'relative_volume': relative_volume[idx],
                'type': 'low_volume_node',
                'strength': 100 - min(relative_volume[idx] * 100, 100)
            })
        
        # 按价格排序
        high_volume_nodes.sort(key=lambda x: x['price'])
        low_volume_nodes.sort(key=lambda x: x['price'])
        
        # 识别成交量集群
        high_clusters = self._cluster_volume_nodes(high_volume_nodes, 'high')
        low_clusters = self._cluster_volume_nodes(low_volume_nodes, 'low')
        
        return {
            'high_volume_nodes': high_volume_nodes,
            'low_volume_nodes': low_volume_nodes,
            'high_volume_clusters': high_clusters,
            'low_volume_clusters': low_clusters,
            'high_volume_threshold': high_volume_threshold,
            'low_volume_threshold': low_volume_threshold
        }
    
    def _cluster_volume_nodes(self, nodes: List[Dict], node_type: str) -> List[Dict]:
        """
        聚类相近的成交量节点
        """
        if not nodes:
            return []
        
        # 按价格排序
        nodes.sort(key=lambda x: x['price'])
        
        clusters = []
        current_cluster = [nodes[0]]
        
        for i in range(1, len(nodes)):
            last_price = current_cluster[-1]['price']
            current_price = nodes[i]['price']
            
            price_change = abs(current_price - last_price) / last_price
            
            if price_change <= 0.02:  # 2%阈值
                current_cluster.append(nodes[i])
            else:
                clusters.append(self._create_volume_cluster(current_cluster, node_type))
                current_cluster = [nodes[i]]
        
        if current_cluster:
            clusters.append(self._create_volume_cluster(current_cluster, node_type))
        
        return clusters
    
    def _create_volume_cluster(self, cluster_nodes: List[Dict], node_type: str) -> Dict:
        """
        创建成交量集群摘要
        """
        prices = [node['price'] for node in cluster_nodes]
        volumes = [node['volume'] for node in cluster_nodes]
        
        avg_price = np.mean(prices)
        total_volume = np.sum(volumes)
        avg_relative_volume = np.mean([node['relative_volume'] for node in cluster_nodes])
        
        # 计算集群强度
        if node_type == 'high':
            strength = min(avg_relative_volume * 100 * len(cluster_nodes), 100)
        else:
            strength = min((1 - avg_relative_volume) * 100 * len(cluster_nodes), 100)
        
        return {
            'avg_price': avg_price,
            'price_range': (min(prices), max(prices)),
            'total_volume': total_volume,
            'avg_relative_volume': avg_relative_volume,
            'node_count': len(cluster_nodes),
            'node_type': node_type,
            'strength': strength,
            'description': f'{node_type}成交量集群 ({len(cluster_nodes)}个节点)'
        }
    
    def _detect_volume_gaps(self, profile: Dict) -> Dict:
        """
        检测成交量缺口 (低成交量区域)
        """
        volume_bins = profile['volume_bins']
        price_bins = profile['price_bins']
        
        if len(volume_bins) < 3:
            return {'gaps': [], 'significant_gaps': []}
        
        # 计算成交量缺口
        gaps = []
        
        for i in range(1, len(volume_bins) - 1):
            left_volume = volume_bins[i-1]
            center_volume = volume_bins[i]
            right_volume = volume_bins[i+1]
            
            # 检查是否为缺口 (中间低，两边高)
            if (center_volume < left_volume * self.gap_threshold_pct and 
                center_volume < right_volume * self.gap_threshold_pct):
                
                gap_price_low = price_bins[i]
                gap_price_high = price_bins[i+1]
                gap_center = (gap_price_low + gap_price_high) / 2
                
                # 计算缺口深度
                avg_surrounding = (left_volume + right_volume) / 2
                gap_depth = 1 - (center_volume / avg_surrounding) if avg_surrounding > 0 else 1
                
                gaps.append({
                    'price_low': gap_price_low,
                    'price_high': gap_price_high,
                    'price_center': gap_center,
                    'volume': center_volume,
                    'gap_depth': gap_depth,
                    'type': 'volume_gap',
                    'strength': min(gap_depth * 100, 100)
                })
        
        # 识别显著缺口 (深度大于50%)
        significant_gaps = [gap for gap in gaps if gap['gap_depth'] > 0.5]
        
        # 合并相邻缺口
        merged_gaps = self._merge_adjacent_gaps(gaps)
        merged_significant = self._merge_adjacent_gaps(significant_gaps)
        
        return {
            'gaps': merged_gaps,
            'significant_gaps': merged_significant,
            'gap_count': len(merged_gaps),
            'significant_gap_count': len(merged_significant)
        }
    
    def _merge_adjacent_gaps(self, gaps: List[Dict]) -> List[Dict]:
        """
        合并相邻的成交量缺口
        """
        if not gaps:
            return []
        
        gaps.sort(key=lambda x: x['price_low'])
        
        merged = []
        current_gap = gaps[0]
        
        for i in range(1, len(gaps)):
            next_gap = gaps[i]
            
            # 检查是否相邻
            if next_gap['price_low'] <= current_gap['price_high'] * 1.01:  # 1%容差
                # 合并缺口
                current_gap['price_high'] = max(current_gap['price_high'], next_gap['price_high'])
                current_gap['price_center'] = (current_gap['price_low'] + current_gap['price_high']) / 2
                current_gap['volume'] = (current_gap['volume'] + next_gap['volume']) / 2
                current_gap['gap_depth'] = max(current_gap['gap_depth'], next_gap['gap_depth'])
                current_gap['strength'] = max(current_gap['strength'], next_gap['strength'])
            else:
                merged.append(current_gap)
                current_gap = next_gap
        
        merged.append(current_gap)
        return merged
    
    def _calculate_control_points(self, profile: Dict) -> Dict:
        """
        计算成交量控制点
        """
        volume_bins = profile['volume_bins']
        price_centers = profile['price_centers']
        
        if len(volume_bins) == 0:
            return {
                'poc': None,  # Point of Control
                'value_area': None,
                'single_print': None
            }
        
        # 1. 点控制 (POC) - 最高成交量的价格
        poc_index = np.argmax(volume_bins)
        poc_price = price_centers[poc_index]
        poc_volume = volume_bins[poc_index]
        
        # 2. 价值区域 (Value Area) - 包含70%成交量的价格区域
        total_volume = np.sum(volume_bins)
        target_volume = total_volume * 0.7
        
        # 从POC向两侧扩展，直到达到目标成交量
        sorted_indices = np.argsort(volume_bins)[::-1]  # 按成交量降序排序
        
        accumulated_volume = 0
        value_area_indices = []
        
        for idx in sorted_indices:
            accumulated_volume += volume_bins[idx]
            value_area_indices.append(idx)
            
            if accumulated_volume >= target_volume:
                break
        
        value_area_indices.sort()
        value_area_prices = [price_centers[i] for i in value_area_indices]
        
        # 3. 单打印区域 (Single Print) - 极低成交量的价格区域
        low_volume_threshold = np.percentile(volume_bins, 10)
        single_print_indices = np.where(volume_bins <= low_volume_threshold)[0]
        single_print_prices = [price_centers[i] for i in single_print_indices]
        
        # 计算价值区域的高低点
        if value_area_prices:
            value_area_low = min(value_area_prices)
            value_area_high = max(value_area_prices)
            value_area_center = (value_area_low + value_area_high) / 2
        else:
            value_area_low = value_area_high = value_area_center = poc_price
        
        return {
            'poc': {
                'price': poc_price,
                'volume': poc_volume,
                'relative_volume': poc_volume / profile['max_volume'] if profile['max_volume'] > 0 else 0,
                'description': '点控制 (最高成交量)'
            },
            'value_area': {
                'low': value_area_low,
                'high': value_area_high,
                'center': value_area_center,
                'price_range': value_area_high - value_area_low,
                'volume_percentage': accumulated_volume / total_volume * 100 if total_volume > 0 else 0,
                'description': f'价值区域 (包含{accumulated_volume/total_volume*100:.1f}%成交量)'
            },
            'single_print': {
                'prices': single_print_prices,
                'count': len(single_print_prices),
                'description': '单打印区域 (极低成交量)'
            }
        }
    
    def _analyze_profile_patterns(self, profile: Dict) -> Dict:
        """
        分析成交量分布形态
        """
        volume_bins = profile['volume_bins']
        price_centers = profile['price_centers']
        
        if len(volume_bins) < 5:
            return {'pattern': 'insufficient_data', 'confidence': 0}
        
        # 计算成交量分布的偏度和峰度
        from scipy import stats
        
        try:
            skewness = stats.skew(volume_bins)
            kurtosis = stats.kurtosis(volume_bins)
        except:
            skewness = kurtosis = 0
        
        # 识别分布形态
        pattern = 'normal'
        confidence = 0.5
        
        # 检查是否为钟形分布 (正常分布)
        if -0.5 < skewness < 0.5 and -1 < kurtosis < 1:
            pattern = 'bell_shaped'
            confidence = 0.7
        
        # 检查是否为双峰分布
        from scipy.signal import find_peaks
        peaks, _ = find_peaks(volume_bins, height=np.percentile(volume_bins, 50))
        
        if len(peaks) >= 2:
            # 检查峰值是否显著
            peak_heights = volume_bins[peaks]
            if max(peak_heights) > np.mean(volume_bins) * 1.5:
                pattern = 'bimodal'
                confidence = 0.6
        
        # 检查是否为均匀分布
        volume_std = np.std(volume_bins)
        volume_mean = np.mean(volume_bins)
        
        if volume_std < volume_mean * 0.3:  # 低标准差
            pattern = 'uniform'
            confidence = 0.6
        
        # 检查是否为偏态分布
        if skewness > 0.8:
            pattern = 'right_skewed'
            confidence = 0.7
        elif skewness < -0.8:
            pattern = 'left_skewed'
            confidence = 0.7
        
        # 分析价格与成交量的关系
        price_volume_corr = np.corrcoef(price_centers[:len(volume_bins)], volume_bins)[0, 1]
        
        return {
            'pattern': pattern,
            'pattern_description': self._get_pattern_description(pattern),
            'confidence': confidence,
            'skewness': skewness,
            'kurtosis': kurtosis,
            'price_volume_correlation': price_volume_corr,
            'volume_std': volume_std,
            'volume_mean': volume_mean,
            'peak_count': len(peaks)
        }
    
    def _get_pattern_description(self, pattern: str) -> str:
        """获取形态描述"""
        descriptions = {
            'bell_shaped': '钟形分布 - 成交量集中在中间价格',
            'bimodal': '双峰分布 - 两个高成交量区域',
            'uniform': '均匀分布 - 成交量分布均匀',
            'right_skewed': '右偏分布 - 高成交量在较高价格',
            'left_skewed': '左偏分布 - 高成交量在较低价格',
            'normal': '正常分布 - 无明显特殊形态',
            'insufficient_data': '数据不足'
        }
        return descriptions.get(pattern, '未知形态')
    
    def _analyze_price_volume_relation(self, 
                                     df: pd.DataFrame, 
                                     profile: Dict,
                                     volume_nodes: Dict) -> Dict:
        """
        分析当前价格与成交量分布的关系
        """
        current_price = df['close'].iloc[-1]
        
        relation = {
            'current_price': current_price,
            'in_high_volume_zone': False,
            'in_low_volume_zone': False,
            'in_volume_gap': False,
            'distance_to_poc': None,
            'volume_zone': 'unknown',
            'trading_implications': []
        }
        
        # 检查是否在高成交量区域
        for node in volume_nodes.get('high_volume_nodes', []):
            node_price = node['price']
            price_diff_pct = abs(current_price - node_price) / current_price * 100
            
            if price_diff_pct <= 1.0:  # 1%以内
                relation['in_high_volume_zone'] = True
                relation['volume_zone'] = 'high_volume'
                relation['trading_implications'].append(
                    '在高成交量区域 - 可能遇到较强支撑/阻力'
                )
                break
        
        # 检查是否在低成交量区域
        for node in volume_nodes.get('low_volume_nodes', []):
            node_price = node['price']
            price_diff_pct = abs(current_price - node_price) / current_price * 100
            
            if price_diff_pct <= 1.0:
                relation['in_low_volume_zone'] = True
                relation['volume_zone'] = 'low_volume'
                relation['trading_implications'].append(
                    '在低成交量区域 - 价格可能快速移动'
                )
                break
        
        # 检查是否在成交量缺口
        # 这里需要volume_gaps数据，但在这个函数中不可用
        # 实际实现中应该传递volume_gaps参数
        
        # 计算到POC的距离
        control_points = self._calculate_control_points(profile)
        if control_points['poc']:
            poc_price = control_points['poc']['price']
            distance_pct = abs(current_price - poc_price) / current_price * 100
            relation['distance_to_poc'] = distance_pct
            
            if distance_pct <= 2.0:
                relation['trading_implications'].append(
                    f'接近点控制(POC) - 距离{distance_pct:.1f}%'
                )
            else:
                relation['trading_implications'].append(
                    f'远离点控制(POC) - 距离{distance_pct:.1f}%'
                )
        
        # 确定交易含义
        if not relation['trading_implications']:
            if relation['in_high_volume_zone']:
                relation['trading_implications'].append('价格在高成交量区域，波动可能受限')
            elif relation['in_low_volume_zone']:
                relation['trading_implications'].append('价格在低成交量区域，可能快速突破')
            else:
                relation['trading_implications'].append('价格在中等成交量区域')
        
        return relation
    
    def get_volume_profile_summary(self, df: pd.DataFrame) -> str:
        """
        获取成交量分布分析摘要
        """
        analysis = self.analyze_volume_profile(df)
        
        summary = f"""
        📊 成交量分布分析
        {'='*40}
        当前价格: {df['close'].iloc[-1]:.2f}
        总成交量: {analysis['basic_profile']['total_volume']:,.0f}
        
        成交量节点:
        - 高成交量节点: {len(analysis['volume_nodes']['high_volume_nodes'])} 个
        - 低成交量节点: {len(analysis['volume_nodes']['low_volume_nodes'])} 个
        - 高成交量集群: {len(analysis['volume_nodes']['high_volume_clusters'])} 个
        - 低成交量集群: {len(analysis['volume_nodes']['low_volume_clusters'])} 个
        
        成交量缺口:
        - 总缺口: {analysis['volume_gaps']['gap_count']} 个
        - 显著缺口: {analysis['volume_gaps']['significant_gap_count']} 个
        
        控制点:
        """
        
        control_points = analysis['control_points']
        if control_points['poc']:
            poc = control_points['poc']
            summary += f"\n  点控制(POC): {poc['price']:.2f}"
            summary += f" (相对成交量: {poc['relative_volume']:.2f})"
        
        if control_points['value_area']:
            va = control_points['value_area']
            summary += f"\n  价值区域: {va['low']:.2f} - {va['high']:.2f}"
            summary += f" (宽度: {va['price_range']:.2f})"
        
        # 分布形态
        patterns = analysis['profile_patterns']
        summary += f"\n\n  分布形态: {patterns['pattern_description']}"
        summary += f"\n  置信度: {patterns['confidence']:.1%}"
        
        if patterns['price_volume_correlation'] > 0.3:
            summary += f"\n  价格-成交量正相关: {patterns['price_volume_correlation']:.2f}"
        elif patterns['price_volume_correlation'] < -0.3:
            summary += f"\n  价格-成交量负相关: {patterns['price_volume_correlation']:.2f}"
        
        # 价格关系
        relation = analysis['price_volume_relation']
        summary += f"\n\n  价格位置分析:"
        summary += f"\n    成交量区域: {relation['volume_zone'].replace('_', ' ').upper()}"
        
        if relation['distance_to_poc'] is not None:
            summary += f"\n    到POC距离: {relation['distance_to_poc']:.1f}%"
        
        if relation['trading_implications']:
            summary += f"\n\n  交易含义:"
            for implication in relation['trading_implications'][:3]:  # 显示前3个
                summary += f"\n    • {implication}"
        
        return summary
