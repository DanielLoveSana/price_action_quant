"""
关键价位标注器 - 在K线图上标注支撑阻力、枢轴点等关键价位

功能：
1. 支撑阻力水平线标注
2. 枢轴点系统标注
3. 成交量分布直方图
4. 订单块区域高亮显示
5. 智能标注布局避免重叠
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from matplotlib.patches import Rectangle, Polygon
from matplotlib.lines import Line2D

from .base import BaseVisualizer


class KeyLevelsPlotter(BaseVisualizer):
    """关键价位标注器"""
    
    def __init__(self, 
                 figsize: Tuple[int, int] = (16, 9),
                 dpi: int = 100,
                 style: str = 'seaborn-v0_8-darkgrid',
                 color_palette: str = 'Set2'):
        """
        初始化关键价位标注器
        
        Args:
            figsize: 图表尺寸
            dpi: 图表分辨率
            style: matplotlib样式
            color_palette: 颜色调色板
        """
        super().__init__(figsize, dpi, style, color_palette)
        
        # 标注样式配置
        self.annotation_styles = {
            'support': {
                'color': 'green',
                'linestyle': '--',
                'linewidth': 1.5,
                'alpha': 0.7,
                'label_prefix': 'S'
            },
            'resistance': {
                'color': 'red',
                'linestyle': '--',
                'linewidth': 1.5,
                'alpha': 0.7,
                'label_prefix': 'R'
            },
            'pivot': {
                'color': 'blue',
                'linestyle': '-',
                'linewidth': 1.0,
                'alpha': 0.5,
                'label_prefix': 'P'
            },
            'volume_profile': {
                'color': 'purple',
                'alpha': 0.3,
                'width': 0.8
            },
            'order_block': {
                'color': 'orange',
                'alpha': 0.2,
                'edgecolor': 'darkorange'
            }
        }
        
        # 标注存储
        self.annotations = {}
        self.levels = {}
        
    def plot_key_levels(self,
                       ax: plt.Axes,
                       data: pd.DataFrame,
                       support_levels: List[Dict],
                       resistance_levels: List[Dict],
                       pivot_points: Optional[Dict] = None,
                       volume_profile: Optional[Dict] = None,
                       order_blocks: Optional[List[Dict]] = None,
                       show_labels: bool = True,
                       max_levels: int = 10) -> Dict:
        """
        在指定坐标轴上绘制关键价位
        
        Args:
            ax: matplotlib坐标轴对象
            data: 价格数据
            support_levels: 支撑位列表
            resistance_levels: 阻力位列表
            pivot_points: 枢轴点数据
            volume_profile: 成交量分布数据
            order_blocks: 订单块数据
            show_labels: 是否显示标签
            max_levels: 最大显示级别数量
            
        Returns:
            Dict: 标注信息
        """
        # 存储数据
        self.chart_data = data
        self.ax = ax
        
        # 清空之前的标注
        self.clear_annotations()
        
        # 绘制支撑阻力线
        support_info = self.plot_support_resistance(
            ax, support_levels, resistance_levels, 
            show_labels, max_levels
        )
        
        # 绘制枢轴点
        pivot_info = {}
        if pivot_points:
            pivot_info = self.plot_pivot_points(ax, pivot_points, show_labels)
        
        # 绘制成交量分布
        volume_info = {}
        if volume_profile:
            volume_info = self.plot_volume_profile(ax, volume_profile)
        
        # 绘制订单块
        order_info = {}
        if order_blocks:
            order_info = self.plot_order_blocks(ax, order_blocks)
        
        # 更新标注存储
        self.annotations.update({
            'support_resistance': support_info,
            'pivot_points': pivot_info,
            'volume_profile': volume_info,
            'order_blocks': order_info
        })
        
        return self.annotations
    
    def plot_support_resistance(self,
                               ax: plt.Axes,
                               support_levels: List[Dict],
                               resistance_levels: List[Dict],
                               show_labels: bool = True,
                               max_levels: int = 10) -> Dict:
        """
        绘制支撑阻力线
        
        Args:
            ax: 坐标轴对象
            support_levels: 支撑位列表
            resistance_levels: 阻力位列表
            show_labels: 是否显示标签
            max_levels: 最大显示数量
            
        Returns:
            Dict: 支撑阻力标注信息
        """
        result = {
            'support_lines': [],
            'resistance_lines': [],
            'labels': []
        }
        
        # 限制显示数量
        support_levels = sorted(support_levels, key=lambda x: x.get('strength', 0), reverse=True)[:max_levels]
        resistance_levels = sorted(resistance_levels, key=lambda x: x.get('strength', 0), reverse=True)[:max_levels]
        
        # 绘制支撑线
        for i, level in enumerate(support_levels):
            price = level.get('price', 0)
            strength = level.get('strength', 0)
            
            if price > 0:
                # 绘制水平线
                line = ax.axhline(
                    y=price,
                    color=self.annotation_styles['support']['color'],
                    linestyle=self.annotation_styles['support']['linestyle'],
                    linewidth=self.annotation_styles['support']['linewidth'],
                    alpha=self.annotation_styles['support']['alpha'] * (0.5 + strength * 0.5)
                )
                
                # 添加标签
                if show_labels:
                    label_text = f"{self.annotation_styles['support']['label_prefix']}{i+1}: ${price:.2f}"
                    if strength > 0:
                        label_text += f" ({strength:.1f})"
                    
                    label = ax.text(
                        ax.get_xlim()[0],
                        price,
                        label_text,
                        color=self.annotation_styles['support']['color'],
                        fontsize=9,
                        verticalalignment='bottom',
                        backgroundcolor='white',
                        alpha=0.8
                    )
                    result['labels'].append(label)
                
                result['support_lines'].append({
                    'line': line,
                    'price': price,
                    'strength': strength,
                    'index': i
                })
        
        # 绘制阻力线
        for i, level in enumerate(resistance_levels):
            price = level.get('price', 0)
            strength = level.get('strength', 0)
            
            if price > 0:
                # 绘制水平线
                line = ax.axhline(
                    y=price,
                    color=self.annotation_styles['resistance']['color'],
                    linestyle=self.annotation_styles['resistance']['linestyle'],
                    linewidth=self.annotation_styles['resistance']['linewidth'],
                    alpha=self.annotation_styles['resistance']['alpha'] * (0.5 + strength * 0.5)
                )
                
                # 添加标签
                if show_labels:
                    label_text = f"{self.annotation_styles['resistance']['label_prefix']}{i+1}: ${price:.2f}"
                    if strength > 0:
                        label_text += f" ({strength:.1f})"
                    
                    label = ax.text(
                        ax.get_xlim()[0],
                        price,
                        label_text,
                        color=self.annotation_styles['resistance']['color'],
                        fontsize=9,
                        verticalalignment='top',
                        backgroundcolor='white',
                        alpha=0.8
                    )
                    result['labels'].append(label)
                
                result['resistance_lines'].append({
                    'line': line,
                    'price': price,
                    'strength': strength,
                    'index': i
                })
        
        return result
    
    def plot_pivot_points(self,
                         ax: plt.Axes,
                         pivot_points: Dict,
                         show_labels: bool = True) -> Dict:
        """
        绘制枢轴点
        
        Args:
            ax: 坐标轴对象
            pivot_points: 枢轴点数据
            show_labels: 是否显示标签
            
        Returns:
            Dict: 枢轴点标注信息
        """
        result = {
            'pivot_lines': [],
            'labels': []
        }
        
        # 绘制标准枢轴点
        if 'standard' in pivot_points:
            std_pivot = pivot_points['standard']
            
            # 绘制枢轴点线
            pivot_line = ax.axhline(
                y=std_pivot.get('pivot', 0),
                color=self.annotation_styles['pivot']['color'],
                linestyle=self.annotation_styles['pivot']['linestyle'],
                linewidth=self.annotation_styles['pivot']['linewidth'],
                alpha=self.annotation_styles['pivot']['alpha'],
                label='Pivot'
            )
            
            # 绘制支撑阻力线
            for i in range(1, 4):
                r_key = f'r{i}'
                s_key = f's{i}'
                
                if r_key in std_pivot:
                    ax.axhline(
                        y=std_pivot[r_key],
                        color='red',
                        linestyle=':',
                        linewidth=1.0,
                        alpha=0.4,
                        label=f'R{i}'
                    )
                
                if s_key in std_pivot:
                    ax.axhline(
                        y=std_pivot[s_key],
                        color='green',
                        linestyle=':',
                        linewidth=1.0,
                        alpha=0.4,
                        label=f'S{i}'
                    )
            
            # 添加标签
            if show_labels and std_pivot.get('pivot', 0) > 0:
                label = ax.text(
                    ax.get_xlim()[0],
                    std_pivot['pivot'],
                    f"P: ${std_pivot['pivot']:.2f}",
                    color=self.annotation_styles['pivot']['color'],
                    fontsize=9,
                    verticalalignment='center',
                    backgroundcolor='white',
                    alpha=0.8
                )
                result['labels'].append(label)
            
            result['pivot_lines'].append({
                'line': pivot_line,
                'price': std_pivot.get('pivot', 0),
                'type': 'standard'
            })
        
        return result
    
    def plot_volume_profile(self,
                           ax: plt.Axes,
                           volume_profile: Dict) -> Dict:
        """
        绘制成交量分布
        
        Args:
            ax: 坐标轴对象
            volume_profile: 成交量分布数据
            
        Returns:
            Dict: 成交量分布标注信息
        """
        result = {
            'profile_bars': [],
            'poc_line': None,
            'value_area': None
        }
        
        # 检查必要数据
        if 'profile' not in volume_profile or 'price_bins' not in volume_profile:
            return result
        
        profile = volume_profile['profile']
        price_bins = volume_profile['price_bins']
        
        if len(profile) == 0 or len(price_bins) == 0:
            return result
        
        # 创建右侧坐标轴用于成交量分布
        ax2 = ax.twinx()
        ax2.set_ylabel('成交量', fontsize=9)
        ax2.tick_params(axis='y', labelsize=8)
        
        # 绘制成交量分布直方图
        bars = ax2.barh(
            price_bins,
            profile,
            height=(price_bins[1] - price_bins[0]) * 0.8,
            color=self.annotation_styles['volume_profile']['color'],
            alpha=self.annotation_styles['volume_profile']['alpha']
        )
        
        result['profile_bars'] = bars
        
        # 绘制POC（成交量最大点）
        if 'poc_price' in volume_profile and volume_profile['poc_price'] > 0:
            poc_line = ax.axhline(
                y=volume_profile['poc_price'],
                color='yellow',
                linestyle='-',
                linewidth=2.0,
                alpha=0.7,
                label='POC'
            )
            result['poc_line'] = poc_line
        
        # 绘制价值区域
        if 'value_area_high' in volume_profile and 'value_area_low' in volume_profile:
            va_high = volume_profile['value_area_high']
            va_low = volume_profile['value_area_low']
            
            if va_high > 0 and va_low > 0:
                # 创建矩形区域
                x_limits = ax.get_xlim()
                width = x_limits[1] - x_limits[0]
                
                rect = Rectangle(
                    (x_limits[0], va_low),
                    width,
                    va_high - va_low,
                    color='yellow',
                    alpha=0.1,
                    label='Value Area'
                )
                ax.add_patch(rect)
                result['value_area'] = rect
        
        return result
    
    def plot_order_blocks(self,
                         ax: plt.Axes,
                         order_blocks: List[Dict]) -> Dict:
        """
        绘制订单块
        
        Args:
            ax: 坐标轴对象
            order_blocks: 订单块数据
            
        Returns:
            Dict: 订单块标注信息
        """
        result = {
            'blocks': [],
            'labels': []
        }
        
        for i, block in enumerate(order_blocks):
            # 检查必要字段
            if 'high' not in block or 'low' not in block or 'strength' not in block:
                continue
            
            high = block['high']
            low = block['low']
            strength = block['strength']
            
            if high <= low:
                continue
            
            # 计算颜色强度
            alpha = self.annotation_styles['order_block']['alpha'] * (0.3 + strength * 0.7)
            
            # 创建矩形区域
            x_limits = ax.get_xlim()
            width = x_limits[1] - x_limits[0]
            
            rect = Rectangle(
                (x_limits[0], low),
                width,
                high - low,
                color=self.annotation_styles['order_block']['color'],
                alpha=alpha,
                edgecolor=self.annotation_styles['order_block']['edgecolor'],
                linewidth=1,
                linestyle='--'
            )
            ax.add_patch(rect)
            
            # 添加标签
            label_text = f"OB{i+1}"
            if 'type' in block:
                label_text = f"{block['type']} {i+1}"
            
            label = ax.text(
                x_limits[0],
                (high + low) / 2,
                label_text,
                color='darkorange',
                fontsize=8,
                verticalalignment='center',
                backgroundcolor='white',
                alpha=0.8
            )
            
            result['blocks'].append({
                'rectangle': rect,
                'high': high,
                'low': low,
                'strength': strength
            })
            result['labels'].append(label)
        
        return result
    
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
            print(f"关键价位图表已保存到: {save_path}")
        else:
            print("警告: 没有可保存的图表，请先创建图表")
    
    def clear_annotations(self):
        """清除所有标注"""
        if hasattr(self, 'annotations'):
            for annotation_type, annotation_data in self.annotations.items():
                if isinstance(annotation_data, dict):
                    # 清除线条
                    for key in ['support_lines', 'resistance_lines', 'pivot_lines']:
                        if key in annotation_data:
                            for item in annotation_data[key]:
                                if 'line' in item:
                                    item['line'].remove()
                    
                    # 清除标签
                    if 'labels' in annotation_data:
                        for label in annotation_data['labels']:
                            label.remove()
            
            self.annotations = {}
    
    def get_legend_elements(self) -> List[Line2D]:
        """获取图例元素"""
        elements = []
        
        # 支撑线图例
        elements.append(Line2D([0], [0], 
                              color=self.annotation_styles['support']['color'],
                              linestyle=self.annotation_styles['support']['linestyle'],
                              linewidth=self.annotation_styles['support']['linewidth'],
                              label='支撑位'))
        
        # 阻力线图例
        elements.append(Line2D([0], [0], 
                              color=self.annotation_styles['resistance']['color'],
                              linestyle=self.annotation_styles['resistance']['linestyle'],
                              linewidth=self.annotation_styles['resistance']['linewidth'],
                              label='阻力位'))
        
        # 枢轴点图例
        elements.append(Line2D([0], [0], 
                              color=self.annotation_styles['pivot']['color'],
                              linestyle=self.annotation_styles['pivot']['linestyle'],
                              linewidth=self.annotation_styles['pivot']['linewidth'],
                              label='枢轴点'))
        
        return elements