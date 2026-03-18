"""
市场结构标注器 - 在K线图上标注趋势线、结构突破点、摆动点等市场结构元素

功能：
1. 趋势线绘制（上升趋势线、下降趋势线）
2. 结构突破点标注
3. 摆动点标注（高点、低点）
4. 震荡区间可视化
5. 市场结构状态标注
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from matplotlib.lines import Line2D
from matplotlib.patches import Polygon, FancyArrowPatch
import warnings
warnings.filterwarnings('ignore')

from .base import BaseVisualizer


class MarketStructurePlotter(BaseVisualizer):
    """市场结构标注器"""
    
    def __init__(self, 
                 figsize: Tuple[int, int] = (16, 9),
                 dpi: int = 100,
                 style: str = 'seaborn-v0_8-darkgrid',
                 color_palette: str = 'Set2'):
        """
        初始化市场结构标注器
        
        Args:
            figsize: 图表尺寸
            dpi: 图表分辨率
            style: matplotlib样式
            color_palette: 颜色调色板
        """
        super().__init__(figsize, dpi, style, color_palette)
        
        # 市场结构标注样式
        self.structure_styles = {
            'uptrend_line': {
                'color': 'green',
                'linestyle': '-',
                'linewidth': 2.0,
                'alpha': 0.8,
                'label': '上升趋势线'
            },
            'downtrend_line': {
                'color': 'red',
                'linestyle': '-',
                'linewidth': 2.0,
                'alpha': 0.8,
                'label': '下降趋势线'
            },
            'structure_break': {
                'bullish': {
                    'color': 'lime',
                    'marker': '^',
                    'markersize': 100,
                    'alpha': 0.7,
                    'label': '看涨结构突破'
                },
                'bearish': {
                    'color': 'crimson',
                    'marker': 'v',
                    'markersize': 100,
                    'alpha': 0.7,
                    'label': '看跌结构突破'
                }
            },
            'swing_point': {
                'high': {
                    'color': 'red',
                    'marker': 'v',
                    'markersize': 80,
                    'alpha': 0.6,
                    'label': '摆动高点'
                },
                'low': {
                    'color': 'green',
                    'marker': '^',
                    'markersize': 80,
                    'alpha': 0.6,
                    'label': '摆动低点'
                }
            },
            'consolidation_zone': {
                'color': 'gray',
                'alpha': 0.2,
                'edgecolor': 'darkgray',
                'label': '震荡区间'
            }
        }
        
        # 标注存储
        self.structure_annotations = {}
        
    def plot_market_structure(self,
                             ax: plt.Axes,
                             data: pd.DataFrame,
                             market_structure_result: Dict,
                             show_labels: bool = True,
                             max_trend_lines: int = 3) -> Dict:
        """
        在指定坐标轴上绘制市场结构
        
        Args:
            ax: matplotlib坐标轴对象
            data: 价格数据
            market_structure_result: 市场结构分析结果
            show_labels: 是否显示标签
            max_trend_lines: 最大趋势线数量
            
        Returns:
            Dict: 市场结构标注信息
        """
        # 存储数据
        self.chart_data = data
        self.ax = ax
        
        # 清空之前的标注
        self.clear_structure_annotations()
        
        result = {}
        
        # 绘制趋势线
        if 'trend_lines' in market_structure_result:
            trend_info = self.plot_trend_lines(
                ax, market_structure_result['trend_lines'], 
                max_trend_lines, show_labels
            )
            result['trend_lines'] = trend_info
        
        # 绘制结构突破点
        if 'structure_breaks' in market_structure_result:
            break_info = self.plot_structure_breaks(
                ax, market_structure_result['structure_breaks'], show_labels
            )
            result['structure_breaks'] = break_info
        
        # 绘制摆动点
        if 'swing_points' in market_structure_result:
            swing_info = self.plot_swing_points(
                ax, market_structure_result['swing_points'], show_labels
            )
            result['swing_points'] = swing_info
        
        # 绘制震荡区间
        if 'consolidation_zones' in market_structure_result:
            zone_info = self.plot_consolidation_zones(
                ax, market_structure_result['consolidation_zones']
            )
            result['consolidation_zones'] = zone_info
        
        # 标注市场结构状态
        if 'market_structure_score' in market_structure_result:
            status_info = self.plot_market_status(
                ax, market_structure_result
            )
            result['market_status'] = status_info
        
        # 更新标注存储
        self.structure_annotations = result
        
        return result
    
    def plot_trend_lines(self,
                        ax: plt.Axes,
                        trend_lines: List[Dict],
                        max_lines: int = 3,
                        show_labels: bool = True) -> Dict:
        """
        绘制趋势线
        
        Args:
            ax: 坐标轴对象
            trend_lines: 趋势线数据
            max_lines: 最大趋势线数量
            show_labels: 是否显示标签
            
        Returns:
            Dict: 趋势线标注信息
        """
        result = {
            'lines': [],
            'labels': []
        }
        
        # 限制趋势线数量
        trend_lines = trend_lines[:max_lines]
        
        for i, trend_line in enumerate(trend_lines):
            if 'type' not in trend_line or 'points' not in trend_line:
                continue
            
            trend_type = trend_line['type']
            points = trend_line['points']
            
            if len(points) < 2:
                continue
            
            # 提取坐标
            x_coords = [p[0] for p in points]
            y_coords = [p[1] for p in points]
            
            # 选择样式
            if trend_type == 'uptrend':
                style = self.structure_styles['uptrend_line']
            elif trend_type == 'downtrend':
                style = self.structure_styles['downtrend_line']
            else:
                style = self.structure_styles['uptrend_line']
            
            # 绘制趋势线
            line = ax.plot(
                x_coords, y_coords,
                color=style['color'],
                linestyle=style['linestyle'],
                linewidth=style['linewidth'],
                alpha=style['alpha'],
                label=style['label'] if i == 0 else None
            )[0]
            
            # 添加标签
            if show_labels:
                # 计算标签位置（趋势线中点）
                mid_idx = len(x_coords) // 2
                if mid_idx < len(x_coords):
                    label_x = x_coords[mid_idx]
                    label_y = y_coords[mid_idx]
                    
                    label_text = f"{trend_type.capitalize()} Line"
                    if 'strength' in trend_line:
                        label_text += f" ({trend_line['strength']:.1f})"
                    
                    label = ax.text(
                        label_x, label_y,
                        label_text,
                        color=style['color'],
                        fontsize=8,
                        backgroundcolor='white',
                        alpha=0.8,
                        rotation=self.calculate_line_angle(x_coords, y_coords)
                    )
                    result['labels'].append(label)
            
            result['lines'].append({
                'line': line,
                'type': trend_type,
                'points': points,
                'index': i
            })
        
        return result
    
    def plot_structure_breaks(self,
                             ax: plt.Axes,
                             structure_breaks: List[Dict],
                             show_labels: bool = True) -> Dict:
        """
        绘制结构突破点
        
        Args:
            ax: 坐标轴对象
            structure_breaks: 结构突破点数据
            show_labels: 是否显示标签
            
        Returns:
            Dict: 结构突破点标注信息
        """
        result = {
            'breaks': [],
            'labels': []
        }
        
        for i, break_point in enumerate(structure_breaks):
            if 'type' not in break_point or 'price' not in break_point or 'date' not in break_point:
                continue
            
            break_type = break_point['type']
            price = break_point['price']
            date = break_point['date']
            
            # 选择样式
            if break_type == 'bullish':
                style = self.structure_styles['structure_break']['bullish']
            elif break_type == 'bearish':
                style = self.structure_styles['structure_break']['bearish']
            else:
                continue
            
            # 绘制突破点
            scatter = ax.scatter(
                date, price,
                color=style['color'],
                marker=style['marker'],
                s=style['markersize'],
                alpha=style['alpha'],
                label=style['label'] if i == 0 else None,
                zorder=5  # 确保在最上层
            )
            
            # 添加标签
            if show_labels:
                label_text = f"{break_type.capitalize()} Break"
                if 'strength' in break_point:
                    label_text += f" ({break_point['strength']:.1f})"
                
                label = ax.text(
                    date, price,
                    label_text,
                    color=style['color'],
                    fontsize=8,
                    backgroundcolor='white',
                    alpha=0.8,
                    verticalalignment='bottom' if break_type == 'bullish' else 'top'
                )
                result['labels'].append(label)
            
            result['breaks'].append({
                'scatter': scatter,
                'type': break_type,
                'price': price,
                'date': date,
                'index': i
            })
        
        return result
    
    def plot_swing_points(self,
                         ax: plt.Axes,
                         swing_points: Dict,
                         show_labels: bool = True) -> Dict:
        """
        绘制摆动点
        
        Args:
            ax: 坐标轴对象
            swing_points: 摆动点数据
            show_labels: 是否显示标签
            
        Returns:
            Dict: 摆动点标注信息
        """
        result = {
            'highs': [],
            'lows': [],
            'labels': []
        }
        
        # 绘制摆动高点
        if 'highs' in swing_points:
            for i, high_point in enumerate(swing_points['highs']):
                if 'price' not in high_point or 'date' not in high_point:
                    continue
                
                price = high_point['price']
                date = high_point['date']
                style = self.structure_styles['swing_point']['high']
                
                # 绘制高点
                scatter = ax.scatter(
                    date, price,
                    color=style['color'],
                    marker=style['marker'],
                    s=style['markersize'],
                    alpha=style['alpha'],
                    label=style['label'] if i == 0 else None,
                    zorder=4
                )
                
                # 添加标签
                if show_labels:
                    label_text = f"H{i+1}"
                    if 'strength' in high_point:
                        label_text += f" ({high_point['strength']:.1f})"
                    
                    label = ax.text(
                        date, price,
                        label_text,
                        color=style['color'],
                        fontsize=7,
                        backgroundcolor='white',
                        alpha=0.8,
                        verticalalignment='bottom'
                    )
                    result['labels'].append(label)
                
                result['highs'].append({
                    'scatter': scatter,
                    'price': price,
                    'date': date,
                    'index': i
                })
        
        # 绘制摆动低点
        if 'lows' in swing_points:
            for i, low_point in enumerate(swing_points['lows']):
                if 'price' not in low_point or 'date' not in low_point:
                    continue
                
                price = low_point['price']
                date = low_point['date']
                style = self.structure_styles['swing_point']['low']
                
                # 绘制低点
                scatter = ax.scatter(
                    date, price,
                    color=style['color'],
                    marker=style['marker'],
                    s=style['markersize'],
                    alpha=style['alpha'],
                    label=style['label'] if i == 0 else None,
                    zorder=4
                )
                
                # 添加标签
                if show_labels:
                    label_text = f"L{i+1}"
                    if 'strength' in low_point:
                        label_text += f" ({low_point['strength']:.1f})"
                    
                    label = ax.text(
                        date, price,
                        label_text,
                        color=style['color'],
                        fontsize=7,
                        backgroundcolor='white',
                        alpha=0.8,
                        verticalalignment='top'
                    )
                    result['labels'].append(label)
                
                result['lows'].append({
                    'scatter': scatter,
                    'price': price,
                    'date': date,
                    'index': i
                })
        
        return result
    
    def plot_consolidation_zones(self,
                                ax: plt.Axes,
                                consolidation_zones: List[Dict]) -> Dict:
        """
        绘制震荡区间
        
        Args:
            ax: 坐标轴对象
            consolidation_zones: 震荡区间数据
            
        Returns:
            Dict: 震荡区间标注信息
        """
        result = {
            'zones': [],
            'labels': []
        }
        
        for i, zone in enumerate(consolidation_zones):
            if 'high' not in zone or 'low' not in zone or 'start_date' not in zone or 'end_date' not in zone:
                continue
            
            high = zone['high']
            low = zone['low']
            start_date = zone['start_date']
            end_date = zone['end_date']
            
            if high <= low:
                continue
            
            style = self.structure_styles['consolidation_zone']
            
            # 创建矩形区域
            rect = plt.Rectangle(
                (start_date, low),
                (end_date - start_date).days,
                high - low,
                color=style['color'],
                alpha=style['alpha'],
                edgecolor=style['edgecolor'],
                linewidth=1,
                linestyle='--'
            )
            ax.add_patch(rect)
            
            # 添加标签
            label_text = f"Zone {i+1}"
            if 'strength' in zone:
                label_text += f" ({zone['strength']:.1f})"
            
            label = ax.text(
                start_date,
                (high + low) / 2,
                label_text,
                color='darkgray',
                fontsize=7,
                backgroundcolor='white',
                alpha=0.8,
                rotation=90
            )
            
            result['zones'].append({
                'rectangle': rect,
                'high': high,
                'low': low,
                'start_date': start_date,
                'end_date': end_date,
                'index': i
            })
            result['labels'].append(label)
        
        return result
    
    def plot_market_status(self,
                          ax: plt.Axes,
                          market_structure_result: Dict) -> Dict:
        """
        标注市场结构状态
        
        Args:
            ax: 坐标轴对象
            market_structure_result: 市场结构分析结果
            
        Returns:
            Dict: 市场状态标注信息
        """
        result = {
            'status_text': None,
            'score_indicator': None
        }
        
        # 提取市场状态信息
        trend_direction = market_structure_result.get('trend', {}).get('direction', 'neutral')
        trend_strength = market_structure_result.get('trend', {}).get('strength', 0)
        market_score = market_structure_result.get('market_structure_score', 0)
        
        # 创建状态文本
        status_text = f"趋势: {trend_direction.upper()}\n"
        status_text += f"强度: {trend_strength:.2f}\n"
        status_text += f"结构评分: {market_score:.2f}"
        
        # 在图表右上角添加状态框
        text_box = ax.text(
            0.98, 0.98,
            status_text,
            transform=ax.transAxes,
            fontsize=9,
            verticalalignment='top',
            horizontalalignment='right',
            bbox=dict(
                boxstyle='round,pad=0.5',
                facecolor='lightyellow',
                alpha=0.8,
                edgecolor='gray'
            )
        )
        
        result['status_text'] = text_box
        
        return result
    
    def calculate_line_angle(self, x_coords: List, y_coords: List) -> float:
        """
        计算趋势线的角度（用于标签旋转）
        
        Args:
            x_coords: X坐标列表
            y_coords: Y坐标列表
            
        Returns:
            float: 角度（度）
        """
        if len(x_coords) < 2:
            return 0
        
        # 计算斜率
        dx = x_coords[-1] - x_coords[0]
        dy = y_coords[-1] - y_coords[0]
        
        if dx == 0:
            return 90 if dy > 0 else -90
        
        # 计算角度（弧度转度）
        angle_rad = np.arctan(dy / dx)
        angle_deg = np.degrees(angle_rad)
        
        return angle_deg
    
    def create_figure(self) -> Tuple[plt.Figure, plt.Axes]:
        """创建图表和坐标轴"""
        fig, ax = plt.subplots(figsize=self.figsize, dpi=self.dpi)
        self.fig = fig
        self.ax = ax
        return fig, ax
    
    def save_figure(self, save_path: str, dpi: Optional[int] = None):
        """保存图表"""
        if self.fig is not None:
            self.fig.savefig(save_path, dpi=dpi or self.dpi, bbox_inches='tight')
            print(f"市场结构图表已保存到: {save_path}")
        else:
            print("警告: 没有可保存的图表，请先创建图表")
    
    def clear_structure_annotations(self):
        """清除所有市场结构标注"""
        if hasattr(self, 'structure_annotations'):
            for annotation_type, annotation_data in self.structure_annotations.items():
                if isinstance(annotation_data, dict):
                    # 清除线条
                    if 'lines' in annotation_data:
                        for line_data in annotation_data['lines']:
                            if 'line' in line_data:
                                line_data['line'].remove()
                    
                    # 清除散点
                    for key in ['breaks', 'highs', 'lows']:
                        if key in annotation_data:
                            for scatter_data in annotation_data[key]:
                                if 'scatter' in scatter_data:
                                    scatter_data['scatter'].remove()
                    
                    # 清除标签
                    if 'labels' in annotation_data:
                        for label in annotation_data['labels']:
                            label.remove()
            
            self.structure_annotations = {}
    
    def get_legend_elements(self) -> List[Line2D]:
        """获取图例元素"""
        elements = []
        
        # 上升趋势线图例
        elements.append(Line2D([0], [0], 
                              color=self.structure_styles['uptrend_line']['color'],
                              linestyle=self.structure_styles['uptrend_line']['linestyle'],
                              linewidth=self.structure_styles['uptrend_line']['linewidth'],
                              label=self.structure_styles['uptrend_line']['label']))
        
        # 下降趋势线图例
        elements.append(Line2D([0], [0], 
                              color=self.structure_styles['downtrend_line']['color'],
                              linestyle=self.structure_styles['downtrend_line']['linestyle'],
                              linewidth=self.structure_styles['downtrend_line']['linewidth'],
                              label=self.structure_styles['downtrend_line']['label']))
        
        # 看涨结构突破图例
        elements.append(Line2D([0], [0], 
                              color=self.structure_styles['structure_break']['bullish']['color'],
                              marker=self.structure_styles['structure_break']['bullish']['marker'],
                              linestyle='None',
                              markersize=8,
                              label=self.structure_styles['structure_break']['bullish']['label']))
        
        # 看跌结构突破图例
        elements.append(Line2D([0], [0], 
                              color=self.structure_styles['structure_break']['bearish']['color'],
                              marker=self.structure_styles['structure_break']['bearish']['marker'],
                              linestyle='None',
                              markersize=8,
                              label=self.structure_styles['structure_break']['bearish']['label']))
        
        return elements