"""
基础可视化类 - 提供通用的可视化功能和配置

设计模式：模板方法模式
- 定义可视化流程的骨架
- 子类实现具体的可视化细节
"""

import matplotlib.pyplot as plt
import matplotlib as mpl
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
import pandas as pd


class BaseVisualizer:
    """基础可视化类，提供通用的可视化功能和配置"""
    
    def __init__(self, 
                 figsize: Tuple[int, int] = (16, 9),
                 dpi: int = 100,
                 style: str = 'seaborn-v0_8-darkgrid',
                 color_palette: str = 'Set2'):
        """
        初始化基础可视化器
        
        Args:
            figsize: 图表尺寸 (宽度, 高度)
            dpi: 图表分辨率
            style: matplotlib样式
            color_palette: 颜色调色板
        """
        self.figsize = figsize
        self.dpi = dpi
        self.style = style
        self.color_palette = color_palette
        
        # 设置matplotlib样式
        plt.style.use(self.style)
        self.colors = plt.cm.get_cmap(color_palette)
        
        # 初始化图表对象
        self.fig = None
        self.ax = None
        self.axes = {}  # 多子图管理
        
        # 默认配置
        self.config = {
            'font_family': 'DejaVu Sans',
            'font_size': 10,
            'title_font_size': 14,
            'label_font_size': 12,
            'grid_alpha': 0.3,
            'line_width': 1.5,
            'marker_size': 50,
            'alpha': 0.7,
        }
        
        # 颜色定义
        self.color_definitions = {
            'up_candle': '#26a69a',    # 上涨蜡烛 - 绿色
            'down_candle': '#ef5350',  # 下跌蜡烛 - 红色
            'volume_up': '#4caf50',    # 上涨成交量 - 浅绿
            'volume_down': '#f44336',  # 下跌成交量 - 浅红
            'support': '#2196f3',      # 支撑线 - 蓝色
            'resistance': '#ff9800',   # 阻力线 - 橙色
            'trend_up': '#00c853',     # 上升趋势 - 亮绿
            'trend_down': '#ff1744',   # 下降趋势 - 亮红
            'pivot': '#9c27b0',        # 枢轴点 - 紫色
            'volume_profile': '#607d8b',  # 成交量分布 - 蓝灰
            'order_block': '#ff5722',  # 订单块 - 深橙
            'background': '#f5f5f5',   # 背景色 - 浅灰
            'grid': '#e0e0e0',         # 网格线 - 浅灰
            'text': '#212121',         # 文本色 - 深灰
        }
    
    def create_figure(self, 
                      nrows: int = 1, 
                      ncols: int = 1,
                      sharex: bool = False,
                      **kwargs) -> Tuple[plt.Figure, np.ndarray]:
        """
        创建图表和坐标轴
        
        Args:
            nrows: 行数
            ncols: 列数
            sharex: 是否共享x轴
            **kwargs: 传递给plt.subplots的额外参数
            
        Returns:
            (fig, axes): 图表对象和坐标轴数组
        """
        self.fig, axes = plt.subplots(
            nrows=nrows, 
            ncols=ncols,
            figsize=self.figsize,
            dpi=self.dpi,
            sharex=sharex,
            **kwargs
        )
        
        # 处理单子图情况
        if nrows == 1 and ncols == 1:
            self.ax = axes
            self.axes['main'] = axes
        else:
            # 多子图情况
            axes_flat = axes.flatten() if hasattr(axes, 'flatten') else [axes]
            for i, ax in enumerate(axes_flat):
                self.axes[f'ax{i+1}'] = ax
            self.ax = axes_flat[0]  # 默认使用第一个坐标轴
        
        return self.fig, axes
    
    def set_title(self, 
                  title: str, 
                  ax: Optional[plt.Axes] = None,
                  **kwargs) -> None:
        """
        设置图表标题
        
        Args:
            title: 标题文本
            ax: 坐标轴对象，默认为当前坐标轴
            **kwargs: 传递给set_title的额外参数
        """
        if ax is None:
            ax = self.ax
        
        title_kwargs = {
            'fontsize': self.config['title_font_size'],
            'fontweight': 'bold',
            'color': self.color_definitions['text'],
            'pad': 20,
        }
        title_kwargs.update(kwargs)
        
        ax.set_title(title, **title_kwargs)
    
    def set_labels(self, 
                   xlabel: str = '', 
                   ylabel: str = '',
                   ax: Optional[plt.Axes] = None,
                   **kwargs) -> None:
        """
        设置坐标轴标签
        
        Args:
            xlabel: x轴标签
            ylabel: y轴标签
            ax: 坐标轴对象，默认为当前坐标轴
            **kwargs: 传递给set_xlabel/set_ylabel的额外参数
        """
        if ax is None:
            ax = self.ax
        
        label_kwargs = {
            'fontsize': self.config['label_font_size'],
            'color': self.color_definitions['text'],
        }
        label_kwargs.update(kwargs)
        
        if xlabel:
            ax.set_xlabel(xlabel, **label_kwargs)
        if ylabel:
            ax.set_ylabel(ylabel, **label_kwargs)
    
    def set_grid(self, 
                 visible: bool = True,
                 which: str = 'both',
                 axis: str = 'both',
                 ax: Optional[plt.Axes] = None,
                 **kwargs) -> None:
        """
        设置网格线
        
        Args:
            visible: 是否显示网格
            which: 网格类型 ('major', 'minor', 'both')
            axis: 坐标轴 ('x', 'y', 'both')
            ax: 坐标轴对象，默认为当前坐标轴
            **kwargs: 传递给grid的额外参数
        """
        if ax is None:
            ax = self.ax
        
        grid_kwargs = {
            'alpha': self.config['grid_alpha'],
            'linestyle': '--',
            'linewidth': 0.5,
            'color': self.color_definitions['grid'],
        }
        grid_kwargs.update(kwargs)
        
        ax.grid(visible=visible, which=which, axis=axis, **grid_kwargs)
    
    def set_legend(self, 
                   ax: Optional[plt.Axes] = None,
                   **kwargs) -> None:
        """
        设置图例
        
        Args:
            ax: 坐标轴对象，默认为当前坐标轴
            **kwargs: 传递给legend的额外参数
        """
        if ax is None:
            ax = self.ax
        
        legend_kwargs = {
            'fontsize': self.config['font_size'] - 2,
            'frameon': True,
            'framealpha': 0.8,
            'edgecolor': self.color_definitions['grid'],
            'facecolor': 'white',
            'loc': 'best',
        }
        legend_kwargs.update(kwargs)
        
        ax.legend(**legend_kwargs)
    
    def add_hline(self, 
                  y: float, 
                  label: str = '',
                  color: Optional[str] = None,
                  linestyle: str = '--',
                  linewidth: float = 1.0,
                  alpha: float = 0.7,
                  ax: Optional[plt.Axes] = None,
                  **kwargs) -> plt.Line2D:
        """
        添加水平线
        
        Args:
            y: y轴位置
            label: 线条标签
            color: 线条颜色
            linestyle: 线条样式
            linewidth: 线条宽度
            alpha: 透明度
            ax: 坐标轴对象，默认为当前坐标轴
            **kwargs: 传递给axhline的额外参数
            
        Returns:
            线条对象
        """
        if ax is None:
            ax = self.ax
        
        if color is None:
            color = self.color_definitions['support']
        
        line_kwargs = {
            'color': color,
            'linestyle': linestyle,
            'linewidth': linewidth,
            'alpha': alpha,
            'label': label,
        }
        line_kwargs.update(kwargs)
        
        return ax.axhline(y=y, **line_kwargs)
    
    def add_vline(self, 
                  x: float, 
                  label: str = '',
                  color: Optional[str] = None,
                  linestyle: str = '--',
                  linewidth: float = 1.0,
                  alpha: float = 0.7,
                  ax: Optional[plt.Axes] = None,
                  **kwargs) -> plt.Line2D:
        """
        添加垂直线
        
        Args:
            x: x轴位置
            label: 线条标签
            color: 线条颜色
            linestyle: 线条样式
            linewidth: 线条宽度
            alpha: 透明度
            ax: 坐标轴对象，默认为当前坐标轴
            **kwargs: 传递给axvline的额外参数
            
        Returns:
            线条对象
        """
        if ax is None:
            ax = self.ax
        
        if color is None:
            color = self.color_definitions['text']
        
        line_kwargs = {
            'color': color,
            'linestyle': linestyle,
            'linewidth': linewidth,
            'alpha': alpha,
            'label': label,
        }
        line_kwargs.update(kwargs)
        
        return ax.axvline(x=x, **line_kwargs)
    
    def add_text(self, 
                 x: float, 
                 y: float, 
                 text: str,
                 ax: Optional[plt.Axes] = None,
                 **kwargs) -> plt.Text:
        """
        添加文本标注
        
        Args:
            x: x轴位置
            y: y轴位置
            text: 文本内容
            ax: 坐标轴对象，默认为当前坐标轴
            **kwargs: 传递给text的额外参数
            
        Returns:
            文本对象
        """
        if ax is None:
            ax = self.ax
        
        text_kwargs = {
            'fontsize': self.config['font_size'],
            'color': self.color_definitions['text'],
            'ha': 'center',
            'va': 'center',
            'bbox': dict(boxstyle='round,pad=0.3', 
                        facecolor='white', 
                        alpha=0.8,
                        edgecolor=self.color_definitions['grid']),
        }
        text_kwargs.update(kwargs)
        
        return ax.text(x, y, text, **text_kwargs)
    
    def add_rectangle(self, 
                      x1: float, 
                      x2: float, 
                      y1: float, 
                      y2: float,
                      label: str = '',
                      color: Optional[str] = None,
                      alpha: float = 0.3,
                      ax: Optional[plt.Axes] = None,
                      **kwargs) -> plt.Rectangle:
        """
        添加矩形区域
        
        Args:
            x1: 矩形左边界
            x2: 矩形右边界
            y1: 矩形下边界
            y2: 矩形上边界
            label: 区域标签
            color: 填充颜色
            alpha: 透明度
            ax: 坐标轴对象，默认为当前坐标轴
            **kwargs: 传递给Rectangle的额外参数
            
        Returns:
            矩形对象
        """
        if ax is None:
            ax = self.ax
        
        if color is None:
            color = self.color_definitions['order_block']
        
        from matplotlib.patches import Rectangle
        
        rect_kwargs = {
            'facecolor': color,
            'alpha': alpha,
            'edgecolor': color,
            'linewidth': 1,
            'label': label,
        }
        rect_kwargs.update(kwargs)
        
        rect = Rectangle((x1, y1), x2 - x1, y2 - y1, **rect_kwargs)
        ax.add_patch(rect)
        
        return rect
    
    def save_figure(self, 
                    filename: str, 
                    dpi: Optional[int] = None,
                    bbox_inches: str = 'tight',
                    pad_inches: float = 0.1,
                    **kwargs) -> None:
        """
        保存图表到文件
        
        Args:
            filename: 文件名
            dpi: 分辨率，默认为初始化时的dpi
            bbox_inches: 边界框设置
            pad_inches: 内边距
            **kwargs: 传递给savefig的额外参数
        """
        if self.fig is None:
            raise ValueError("没有可用的图表对象，请先创建图表")
        
        save_kwargs = {
            'dpi': dpi or self.dpi,
            'bbox_inches': bbox_inches,
            'pad_inches': pad_inches,
            'facecolor': 'white',
            'edgecolor': 'none',
        }
        save_kwargs.update(kwargs)
        
        self.fig.savefig(filename, **save_kwargs)
    
    def show(self, 
             block: bool = True,
             **kwargs) -> None:
        """
        显示图表
        
        Args:
            block: 是否阻塞显示
            **kwargs: 传递给show的额外参数
        """
        if self.fig is None:
            raise ValueError("没有可用的图表对象，请先创建图表")
        
        plt.show(block=block, **kwargs)
    
    def close(self) -> None:
        """关闭图表"""
        if self.fig is not None:
            plt.close(self.fig)
            self.fig = None
            self.ax = None
            self.axes = {}
    
    def clear(self, ax: Optional[plt.Axes] = None) -> None:
        """
        清除坐标轴内容
        
        Args:
            ax: 坐标轴对象，默认为当前坐标轴
        """
        if ax is None:
            ax = self.ax
        
        ax.clear()
    
    def get_color(self, 
                  name: str, 
                  alpha: float = 1.0) -> Tuple[float, float, float, float]:
        """
        获取预定义颜色
        
        Args:
            name: 颜色名称
            alpha: 透明度
            
        Returns:
            RGBA颜色元组
        """
        if name in self.color_definitions:
            color = mpl.colors.to_rgba(self.color_definitions[name], alpha)
        else:
            # 使用调色板
            idx = hash(name) % 256
            color = self.colors(idx / 255.0)
            color = (color[0], color[1], color[2], alpha)
        
        return color
    
    def format_xaxis_dates(self, 
                           ax: Optional[plt.Axes] = None,
                           rotation: int = 45,
                           **kwargs) -> None:
        """
        格式化x轴日期显示
        
        Args:
            ax: 坐标轴对象，默认为当前坐标轴
            rotation: 标签旋转角度
            **kwargs: 传递给tick_params的额外参数
        """
        if ax is None:
            ax = self.ax
        
        tick_kwargs = {
            'rotation': rotation,
            'ha': 'right',
        }
        tick_kwargs.update(kwargs)
        
        ax.tick_params(axis='x', **tick_kwargs)
        
        # 自动调整日期格式
        plt.gcf().autofmt_xdate()
    
    def set_background(self, 
                       color: Optional[str] = None,
                       ax: Optional[plt.Axes] = None) -> None:
        """
        设置坐标轴背景色
        
        Args:
            color: 背景颜色
            ax: 坐标轴对象，默认为当前坐标轴
        """
        if ax is None:
            ax = self.ax
        
        if color is None:
            color = self.color_definitions['background']
        
        ax.set_facecolor(color)
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口，自动关闭图表"""
        self.close()