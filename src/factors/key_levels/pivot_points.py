"""
枢轴点计算器
计算经典枢轴点、Camarilla、Woodie、Fibonacci等各类枢轴点
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')


class PivotPointCalculator:
    """
    枢轴点计算器
    
    功能:
    1. 经典枢轴点 (Standard Pivot Points)
    2. Camarilla枢轴点
    3. Woodie枢轴点
    4. Fibonacci枢轴点
    5. 多时间框架枢轴点
    """
    
    def __init__(self, pivot_type: str = 'standard'):
        """
        初始化枢轴点计算器
        
        Args:
            pivot_type: 枢轴点类型 ('standard', 'camarilla', 'woodie', 'fibonacci')
        """
        self.pivot_type = pivot_type
        
        # Fibonacci比率
        self.fib_ratios = {
            'S1': 0.382, 'S2': 0.618, 'S3': 1.000,
            'R1': 0.382, 'R2': 0.618, 'R3': 1.000
        }
    
    def calculate_pivot_points(self, 
                              high: float, 
                              low: float, 
                              close: float,
                              open_price: Optional[float] = None) -> Dict:
        """
        计算枢轴点
        
        Args:
            high: 前一日最高价
            low: 前一日最低价
            close: 前一日收盘价
            open_price: 前一日开盘价 (Woodie方法需要)
            
        Returns:
            Dict: 枢轴点计算结果
        """
        if self.pivot_type == 'standard':
            return self._calculate_standard_pivots(high, low, close)
        elif self.pivot_type == 'camarilla':
            return self._calculate_camarilla_pivots(high, low, close)
        elif self.pivot_type == 'woodie':
            if open_price is None:
                open_price = close  # 默认使用收盘价作为开盘价
            return self._calculate_woodie_pivots(high, low, close, open_price)
        elif self.pivot_type == 'fibonacci':
            return self._calculate_fibonacci_pivots(high, low, close)
        else:
            raise ValueError(f"不支持的枢轴点类型: {self.pivot_type}")
    
    def _calculate_standard_pivots(self, high: float, low: float, close: float) -> Dict:
        """
        计算经典枢轴点
        """
        # 计算枢轴点 (PP)
        pivot = (high + low + close) / 3
        
        # 计算支撑阻力位
        r1 = 2 * pivot - low
        s1 = 2 * pivot - high
        r2 = pivot + (high - low)
        s2 = pivot - (high - low)
        r3 = high + 2 * (pivot - low)
        s3 = low - 2 * (high - pivot)
        
        # 中间支撑阻力
        m1 = (s1 + pivot) / 2
        m2 = (r1 + pivot) / 2
        m3 = (s2 + s1) / 2
        m4 = (r2 + r1) / 2
        
        return {
            'pivot': pivot,
            'supports': {
                'S1': s1, 'S2': s2, 'S3': s3,
                'M1': m1, 'M3': m3
            },
            'resistances': {
                'R1': r1, 'R2': r2, 'R3': r3,
                'M2': m2, 'M4': m4
            },
            'type': 'standard',
            'description': '经典枢轴点 (Standard Pivot Points)'
        }
    
    def _calculate_camarilla_pivots(self, high: float, low: float, close: float) -> Dict:
        """
        计算Camarilla枢轴点
        """
        range_val = high - low
        
        # Camarilla公式
        pivot = (high + low + close) / 3
        
        # 支撑位
        s1 = close - range_val * 0.0916
        s2 = close - range_val * 0.1833
        s3 = close - range_val * 0.2750
        s4 = close - range_val * 0.3666
        s5 = close - range_val * 0.55  # 额外支撑
        s6 = close - range_val * 0.75  # 额外支撑
        
        # 阻力位
        r1 = close + range_val * 0.0916
        r2 = close + range_val * 0.1833
        r3 = close + range_val * 0.2750
        r4 = close + range_val * 0.3666
        r5 = close + range_val * 0.55  # 额外阻力
        r6 = close + range_val * 0.75  # 额外阻力
        
        return {
            'pivot': pivot,
            'supports': {
                'S1': s1, 'S2': s2, 'S3': s3, 'S4': s4,
                'S5': s5, 'S6': s6
            },
            'resistances': {
                'R1': r1, 'R2': r2, 'R3': r3, 'R4': r4,
                'R5': r5, 'R6': r6
            },
            'type': 'camarilla',
            'description': 'Camarilla枢轴点 (日内交易常用)'
        }
    
    def _calculate_woodie_pivots(self, high: float, low: float, close: float, open_price: float) -> Dict:
        """
        计算Woodie枢轴点
        """
        # Woodie公式
        pivot = (high + low + 2 * close) / 4
        
        # 支撑阻力位
        r1 = 2 * pivot - low
        r2 = pivot + (high - low)
        r3 = r1 + (high - low)
        r4 = r3 + (high - low) * 0.618  # Fibonacci扩展
        
        s1 = 2 * pivot - high
        s2 = pivot - (high - low)
        s3 = s1 - (high - low)
        s4 = s3 - (high - low) * 0.618  # Fibonacci扩展
        
        # 开盘价相关水平
        open_r1 = open_price + (high - low) * 0.382
        open_r2 = open_price + (high - low) * 0.618
        open_s1 = open_price - (high - low) * 0.382
        open_s2 = open_price - (high - low) * 0.618
        
        return {
            'pivot': pivot,
            'supports': {
                'S1': s1, 'S2': s2, 'S3': s3, 'S4': s4,
                'OPEN_S1': open_s1, 'OPEN_S2': open_s2
            },
            'resistances': {
                'R1': r1, 'R2': r2, 'R3': r3, 'R4': r4,
                'OPEN_R1': open_r1, 'OPEN_R2': open_r2
            },
            'type': 'woodie',
            'description': 'Woodie枢轴点 (关注开盘价)'
        }
    
    def _calculate_fibonacci_pivots(self, high: float, low: float, close: float) -> Dict:
        """
        计算Fibonacci枢轴点
        """
        pivot = (high + low + close) / 3
        
        range_val = high - low
        
        # Fibonacci支撑位
        s1 = pivot - range_val * 0.382
        s2 = pivot - range_val * 0.618
        s3 = pivot - range_val * 1.000
        s4 = pivot - range_val * 1.382
        s5 = pivot - range_val * 1.618
        
        # Fibonacci阻力位
        r1 = pivot + range_val * 0.382
        r2 = pivot + range_val * 0.618
        r3 = pivot + range_val * 1.000
        r4 = pivot + range_val * 1.382
        r5 = pivot + range_val * 1.618
        
        # 扩展水平
        ext_s1 = low - range_val * 0.382
        ext_s2 = low - range_val * 0.618
        ext_r1 = high + range_val * 0.382
        ext_r2 = high + range_val * 0.618
        
        return {
            'pivot': pivot,
            'supports': {
                'S1': s1, 'S2': s2, 'S3': s3, 'S4': s4, 'S5': s5,
                'EXT_S1': ext_s1, 'EXT_S2': ext_s2
            },
            'resistances': {
                'R1': r1, 'R2': r2, 'R3': r3, 'R4': r4, 'R5': r5,
                'EXT_R1': ext_r1, 'EXT_R2': ext_r2
            },
            'type': 'fibonacci',
            'description': 'Fibonacci枢轴点 (黄金分割比率)'
        }
    
    def calculate_multi_timeframe_pivots(self, df: pd.DataFrame) -> Dict:
        """
        计算多时间框架枢轴点
        
        Args:
            df: 包含OHLC数据的DataFrame
            
        Returns:
            Dict: 多时间框架枢轴点结果
        """
        if len(df) < 2:
            raise ValueError("需要至少2个周期的数据来计算多时间框架枢轴点")
        
        results = {}
        
        # 日线枢轴点
        if len(df) >= 1:
            last_day = df.iloc[-1]
            results['daily'] = self.calculate_pivot_points(
                high=last_day['high'],
                low=last_day['low'],
                close=last_day['close']
            )
        
        # 周线枢轴点 (如果有足够数据)
        if len(df) >= 5:
            weekly_data = df.tail(5)
            weekly_high = weekly_data['high'].max()
            weekly_low = weekly_data['low'].min()
            weekly_close = df['close'].iloc[-1]
            
            results['weekly'] = self.calculate_pivot_points(
                high=weekly_high,
                low=weekly_low,
                close=weekly_close
            )
        
        # 月线枢轴点 (如果有足够数据)
        if len(df) >= 20:
            monthly_data = df.tail(20)
            monthly_high = monthly_data['high'].max()
            monthly_low = monthly_data['low'].min()
            monthly_close = df['close'].iloc[-1]
            
            results['monthly'] = self.calculate_pivot_points(
                high=monthly_high,
                low=monthly_low,
                close=monthly_close
            )
        
        # 计算枢轴点集群 (不同时间框架的汇聚)
        results['clusters'] = self._find_pivot_clusters(results)
        
        # 计算当前价格与各枢轴点的关系
        if len(df) > 0:
            current_price = df['close'].iloc[-1]
            results['price_relation'] = self._analyze_price_pivot_relation(
                current_price, results
            )
        
        return results
    
    def _find_pivot_clusters(self, multi_tf_results: Dict) -> Dict:
        """
        寻找不同时间框架的枢轴点集群
        """
        clusters = {
            'support_clusters': [],
            'resistance_clusters': [],
            'strong_clusters': []
        }
        
        # 收集所有支撑位
        all_supports = []
        for tf, result in multi_tf_results.items():
            if tf in ['daily', 'weekly', 'monthly']:
                supports = result.get('supports', {})
                for level_name, price in supports.items():
                    all_supports.append({
                        'price': price,
                        'timeframe': tf,
                        'level': level_name,
                        'type': 'support'
                    })
        
        # 收集所有阻力位
        all_resistances = []
        for tf, result in multi_tf_results.items():
            if tf in ['daily', 'weekly', 'monthly']:
                resistances = result.get('resistances', {})
                for level_name, price in resistances.items():
                    all_resistances.append({
                        'price': price,
                        'timeframe': tf,
                        'level': level_name,
                        'type': 'resistance'
                    })
        
        # 寻找支撑集群 (价格接近的支撑位)
        if all_supports:
            support_clusters = self._cluster_close_levels(all_supports)
            clusters['support_clusters'] = support_clusters
            
            # 识别强支撑集群 (多个时间框架汇聚)
            for cluster in support_clusters:
                timeframes = set(item['timeframe'] for item in cluster['items'])
                if len(timeframes) >= 2 and len(cluster['items']) >= 3:
                    clusters['strong_clusters'].append({
                        **cluster,
                        'strength': 'strong',
                        'description': f'强支撑集群 ({len(cluster["items"])}个水平)'
                    })
        
        # 寻找阻力集群
        if all_resistances:
            resistance_clusters = self._cluster_close_levels(all_resistances)
            clusters['resistance_clusters'] = resistance_clusters
            
            # 识别强阻力集群
            for cluster in resistance_clusters:
                timeframes = set(item['timeframe'] for item in cluster['items'])
                if len(timeframes) >= 2 and len(cluster['items']) >= 3:
                    clusters['strong_clusters'].append({
                        **cluster,
                        'strength': 'strong',
                        'description': f'强阻力集群 ({len(cluster["items"])}个水平)'
                    })
        
        return clusters
    
    def _cluster_close_levels(self, levels: List[Dict], threshold_pct: float = 0.01) -> List[Dict]:
        """
        聚类相近的价位
        """
        if not levels:
            return []
        
        # 按价格排序
        levels.sort(key=lambda x: x['price'])
        
        clusters = []
        current_cluster = [levels[0]]
        
        for i in range(1, len(levels)):
            last_price = current_cluster[-1]['price']
            current_price = levels[i]['price']
            
            price_change = abs(current_price - last_price) / last_price
            
            if price_change <= threshold_pct:
                # 价格相近，加入当前集群
                current_cluster.append(levels[i])
            else:
                # 价格差异大，创建新集群
                clusters.append(self._create_cluster_summary(current_cluster))
                current_cluster = [levels[i]]
        
        # 处理最后一个集群
        if current_cluster:
            clusters.append(self._create_cluster_summary(current_cluster))
        
        return clusters
    
    def _create_cluster_summary(self, cluster_items: List[Dict]) -> Dict:
        """
        创建集群摘要
        """
        prices = [item['price'] for item in cluster_items]
        avg_price = np.mean(prices)
        price_range = max(prices) - min(prices)
        
        # 统计时间框架分布
        timeframe_counts = {}
        for item in cluster_items:
            tf = item['timeframe']
            timeframe_counts[tf] = timeframe_counts.get(tf, 0) + 1
        
        # 计算集群强度
        strength = min(len(cluster_items) * 20, 100)  # 每多一个水平+20分
        
        return {
            'avg_price': avg_price,
            'price_range': price_range,
            'min_price': min(prices),
            'max_price': max(prices),
            'item_count': len(cluster_items),
            'timeframe_distribution': timeframe_counts,
            'strength': strength,
            'items': cluster_items,
            'description': f'价位集群 ({len(cluster_items)}个水平)'
        }
    
    def _analyze_price_pivot_relation(self, current_price: float, multi_tf_results: Dict) -> Dict:
        """
        分析当前价格与枢轴点的关系
        """
        relation = {
            'current_price': current_price,
            'nearest_pivot': None,
            'nearest_support': None,
            'nearest_resistance': None,
            'between_levels': False,
            'zone': 'unknown'
        }
        
        # 收集所有枢轴点水平
        all_levels = []
        
        for tf, result in multi_tf_results.items():
            if tf in ['daily', 'weekly', 'monthly']:
                # 添加枢轴点
                pivot = result.get('pivot')
                if pivot:
                    all_levels.append({
                        'price': pivot,
                        'type': 'pivot',
                        'timeframe': tf,
                        'name': 'Pivot'
                    })
                
                # 添加支撑位
                supports = result.get('supports', {})
                for name, price in supports.items():
                    all_levels.append({
                        'price': price,
                        'type': 'support',
                        'timeframe': tf,
                        'name': name
                    })
                
                # 添加阻力位
                resistances = result.get('resistances', {})
                for name, price in resistances.items():
                    all_levels.append({
                        'price': price,
                        'type': 'resistance',
                        'timeframe': tf,
                        'name': name
                    })
        
        if not all_levels:
            return relation
        
        # 找到最近的各个类型水平
        for level_type in ['pivot', 'support', 'resistance']:
            type_levels = [l for l in all_levels if l['type'] == level_type]
            if type_levels:
                nearest = min(type_levels, key=lambda x: abs(x['price'] - current_price))
                
                if level_type == 'pivot':
                    relation['nearest_pivot'] = nearest
                elif level_type == 'support':
                    relation['nearest_support'] = nearest
                elif level_type == 'resistance':
                    relation['nearest_resistance'] = nearest
        
        # 检查是否在两个水平之间
        if relation['nearest_support'] and relation['nearest_resistance']:
            support_price = relation['nearest_support']['price']
            resistance_price = relation['nearest_resistance']['price']
            
            if support_price < current_price < resistance_price:
                relation['between_levels'] = True
                
                # 确定所处区域
                pivot_price = relation['nearest_pivot']['price'] if relation['nearest_pivot'] else (support_price + resistance_price) / 2
                
                if current_price < pivot_price:
                    relation['zone'] = 'between_support_and_pivot'
                else:
                    relation['zone'] = 'between_pivot_and_resistance'
        
        # 确定价格区域
        if relation['nearest_pivot']:
            pivot_price = relation['nearest_pivot']['price']
            if current_price < pivot_price:
                relation['zone'] = 'below_pivot'
            else:
                relation['zone'] = 'above_pivot'
        
        return relation
    
    def get_pivot_summary(self, df: pd.DataFrame) -> str:
        """
        获取枢轴点分析摘要
        """
        results = self.calculate_multi_timeframe_pivots(df)
        
        summary = f"""
        🎯 枢轴点分析 ({self.pivot_type.upper()})
        {'='*40}
        当前价格: {df['close'].iloc[-1]:.2f}
        
        日线枢轴点:
        """
        
        if 'daily' in results:
            daily = results['daily']
            summary += f"\n  Pivot: {daily['pivot']:.2f}"
            
            # 显示关键支撑阻力
            if 'S1' in daily['supports'] and 'R1' in daily['resistances']:
                summary += f"\n  S1/R1: {daily['supports']['S1']:.2f} / {daily['resistances']['R1']:.2f}"
            if 'S2' in daily['supports'] and 'R2' in daily['resistances']:
                summary += f"\n  S2/R2: {daily['supports']['S2']:.2f} / {daily['resistances']['R2']:.2f}"
        
        # 多时间框架信息
        if 'weekly' in results or 'monthly' in results:
            summary += f"\n\n  多时间框架枢轴点:"
            
            if 'weekly' in results:
                weekly_pivot = results['weekly']['pivot']
                summary += f"\n    周线Pivot: {weekly_pivot:.2f}"
            
            if 'monthly' in results:
                monthly_pivot = results['monthly']['pivot']
                summary += f"\n    月线Pivot: {monthly_pivot:.2f}"
        
        # 集群信息
        if results.get('clusters', {}).get('strong_clusters'):
            strong_clusters = results['clusters']['strong_clusters']
            summary += f"\n\n  强价位集群 ({len(strong_clusters)}个):"
            
            for i, cluster in enumerate(strong_clusters[:3], 1):  # 显示前3个
                summary += f"\n    {i}. {cluster['avg_price']:.2f} ({cluster['description']})"
        
        # 价格关系分析
        if 'price_relation' in results:
            relation = results['price_relation']
            summary += f"\n\n  价格位置分析:"
            summary += f"\n    区域: {relation['zone'].replace('_', ' ').upper()}"
            summary += f"\n    在水平之间: {'✅' if relation['between_levels'] else '❌'}"
            
            if relation['nearest_support']:
                dist = abs(relation['current_price'] - relation['nearest_support']['price'])
                pct = dist / relation['current_price'] * 100
                summary += f"\n    最近支撑: {relation['nearest_support']['price']:.2f} (距离: {pct:.2f}%)"
            
            if relation['nearest_resistance']:
                dist = abs(relation['nearest_resistance']['price'] - relation['current_price'])
                pct = dist / relation['current_price'] * 100
                summary += f"\n    最近阻力: {relation['nearest_resistance']['price']:.2f} (距离: {pct:.2f}%)"
        
        return summary