"""
K线图绘制器 - 专业的金融图表可视化

功能：
1. 标准K线图（蜡烛图）绘制
2. 技术指标叠加（MA、EMA、MACD、RSI、布林带等）
3. 成交量显示
4. 多时间框架支持
5. 图表导出功能
"""

import mplfinance as mpf
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import warnings
warnings.filterwarnings('ignore')

from .base import BaseVisualizer


class CandlestickChart(BaseVisualizer):
    """K线图绘制器"""
    
    def __init__(self, 
                 figsize: Tuple[int, int] = (16, 9),
                 dpi: int = 100,
                 style: str = 'seaborn-v0_8-darkgrid',
                 color_palette: str = 'Set2',
                 mpf_style: str = 'yahoo'):
        """
        初始化K线图绘制器
        
        Args:
            figsize: 图表尺寸
            dpi: 图表分辨率
            style: matplotlib样式
            color_palette: 颜色调色板
            mpf_style: mplfinance样式
        """
        super().__init__(figsize, dpi, style, color_palette)
        self.mpf_style = mpf_style
        
        # 技术指标配置
        self.indicators_config = {
            'sma': {'periods': [20, 50, 200], 'colors': ['blue', 'orange', 'red']},
            'ema': {'periods': [12, 26], 'colors': ['green', 'purple']},
            'bb': {'period': 20, 'std': 2, 'colors': ['gray', 'gray', 'gray']},
            'macd': {'fast': 12, 'slow': 26, 'signal': 9, 'colors': ['blue', 'red', 'green']},
            'rsi': {'period': 14, 'colors': ['purple']}
        }
        
        # 图表状态
        self.chart_data = None
        self.technical_data = {}
        
    def plot_candlestick(self, 
                        data: pd.DataFrame,
                        title: str = 'K线图',
                        volume: bool = True,
                        type: str = 'candle',
                        mav: Optional[List[int]] = None,
                        indicators: Optional[List[str]] = None,
                        save_path: Optional[str] = None,
                        show: bool = True,
                        **kwargs) -> Dict:
        """
        绘制K线图
        
        Args:
            data: 包含OHLCV数据的DataFrame，索引为日期时间
            title: 图表标题
            volume: 是否显示成交量
            type: 图表类型 ('candle', 'line', 'ohlc', 'renko', 'pnf')
            mav: 移动平均线周期列表
            indicators: 技术指标列表
            save_path: 保存路径
            show: 是否显示图表
            **kwargs: 传递给mplfinance的额外参数
            
        Returns:
            Dict: 包含图表对象的字典
        """
        if indicators is None:
            indicators = ['sma', 'ema', 'bb', 'macd', 'rsi']
        
        # 创建技术指标面板
        tech_config = self.create_technical_panel(data, indicators)
        
        # 构建mpf参数
        mpf_kwargs = {
            'type': 'candle',
            'volume': True,
            'title': title,
            'style': self.mpf_style,
            'addplot': tech_config['addplot'],
            'returnfig': True,
            'figratio': (self.figsize[0]/self.figsize[1], 1),
            'figscale': 1.0,
        }
        
        # 处理面板配置
        if 'macd_panel' in tech_config['panel_config']:
            mpf_kwargs['panel_ratios'] = (3, 1, 1)  # 主图:MACD:RSI
        elif 'rsi_panel' in tech_config['panel_config']:
            mpf_kwargs['panel_ratios'] = (3, 1)  # 主图:RSI
        
        mpf_kwargs.update(kwargs)
        
        # 绘制图表
        fig, axes = mpf.plot(data, **mpf_kwargs)
        
        # 保存图表
        if save_path:
            fig.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
        
        # 显示图表
        if show:
            plt.show()
        
        # 存储图表对象
        self.fig = fig
        if isinstance(axes, np.ndarray):
            self.axes = {f'ax{i+1}': ax for i, ax in enumerate(axes.flatten())}
            self.ax = axes[0]
        else:
            self.ax = axes
            self.axes = {'main': axes}
        
        return {
            'fig': fig,
            'axes': axes,
            'data': data,
            'technical_data': self.technical_data
        }
    
    def create_technical_panel(self, 
                              data: pd.DataFrame,
                              indicators: List[str]) -> Dict:
        """
        创建技术指标面板
        
        Args:
            data: 价格数据
            indicators: 技术指标列表
            
        Returns:
            Dict: 技术指标配置
        """
        addplot = []
        panel_config = {}
        
        # 计算技术指标
        for indicator in indicators:
            if indicator == 'sma':
                sma_data = self.calculate_sma(data, self.indicators_config['sma']['periods'])
                for i, period in enumerate(self.indicators_config['sma']['periods']):
                    addplot.append(
                        mpf.make_addplot(sma_data[f'SMA_{period}'], 
                                        color=self.indicators_config['sma']['colors'][i],
                                        label=f'SMA {period}')
                    )
            
            elif indicator == 'ema':
                ema_data = self.calculate_ema(data, self.indicators_config['ema']['periods'])
                for i, period in enumerate(self.indicators_config['ema']['periods']):
                    addplot.append(
                        mpf.make_addplot(ema_data[f'EMA_{period}'], 
                                        color=self.indicators_config['ema']['colors'][i],
                                        label=f'EMA {period}')
                    )
            
            elif indicator == 'bb':
                bb_data = self.calculate_bollinger_bands(data, 
                                                        self.indicators_config['bb']['period'],
                                                        self.indicators_config['bb']['std'])
                addplot.extend([
                    mpf.make_addplot(bb_data['BB_upper'], 
                                    color=self.indicators_config['bb']['colors'][0],
                                    label='BB Upper'),
                    mpf.make_addplot(bb_data['BB_middle'], 
                                    color=self.indicators_config['bb']['colors'][1],
                                    label='BB Middle'),
                    mpf.make_addplot(bb_data['BB_lower'], 
                                    color=self.indicators_config['bb']['colors'][2],
                                    label='BB Lower')
                ])
            
            elif indicator == 'macd':
                macd_data = self.calculate_macd(data,
                                               self.indicators_config['macd']['fast'],
                                               self.indicators_config['macd']['slow'],
                                               self.indicators_config['macd']['signal'])
                panel_config['macd_panel'] = True
                addplot.append(
                    mpf.make_addplot(macd_data['MACD'], 
                                    panel=1,
                                    color=self.indicators_config['macd']['colors'][0],
                                    label='MACD')
                )
                addplot.append(
                    mpf.make_addplot(macd_data['Signal'], 
                                    panel=1,
                                    color=self.indicators_config['macd']['colors'][1],
                                    label='Signal')
                )
                addplot.append(
                    mpf.make_addplot(macd_data['Histogram'], 
                                    panel=1,
                                    type='bar',
                                    color=self.indicators_config['macd']['colors'][2],
                                    label='Histogram')
                )
            
            elif indicator == 'rsi':
                rsi_data = self.calculate_rsi(data, self.indicators_config['rsi']['period'])
                panel_config['rsi_panel'] = True
                addplot.append(
                    mpf.make_addplot(rsi_data['RSI'], 
                                    panel=2 if 'macd_panel' in panel_config else 1,
                                    color=self.indicators_config['rsi']['colors'][0],
                                    ylabel='RSI',
                                    label='RSI')
                )
                # 添加RSI超买超卖线
                addplot.append(
                    mpf.make_addplot([70] * len(data), 
                                    panel=2 if 'macd_panel' in panel_config else 1,
                                    color='red',
                                    linestyle='--',
                                    label='Overbought')
                )
                addplot.append(
                    mpf.make_addplot([30] * len(data), 
                                    panel=2 if 'macd_panel' in panel_config else 1,
                                    color='green',
                                    linestyle='--',
                                    label='Oversold')
                )
        
        return {
            'addplot': addplot,
            'panel_config': panel_config
        }
    
    def calculate_sma(self, data: pd.DataFrame, periods: List[int]) -> pd.DataFrame:
        """计算简单移动平均线"""
        result = pd.DataFrame(index=data.index)
        for period in periods:
            result[f'SMA_{period}'] = data['Close'].rolling(window=period).mean()
        return result
    
    def calculate_ema(self, data: pd.DataFrame, periods: List[int]) -> pd.DataFrame:
        """计算指数移动平均线"""
        result = pd.DataFrame(index=data.index)
        for period in periods:
            result[f'EMA_{period}'] = data['Close'].ewm(span=period, adjust=False).mean()
        return result
    
    def calculate_bollinger_bands(self, 
                                 data: pd.DataFrame, 
                                 period: int = 20, 
                                 std: float = 2) -> pd.DataFrame:
        """计算布林带"""
        sma = data['Close'].rolling(window=period).mean()
        std_dev = data['Close'].rolling(window=period).std()
        
        result = pd.DataFrame(index=data.index)
        result['BB_upper'] = sma + (std_dev * std)
        result['BB_middle'] = sma
        result['BB_lower'] = sma - (std_dev * std)
        
        return result
    
    def calculate_macd(self, 
                      data: pd.DataFrame, 
                      fast: int = 12, 
                      slow: int = 26, 
                      signal: int = 9) -> pd.DataFrame:
        """计算MACD指标"""
        ema_fast = data['Close'].ewm(span=fast, adjust=False).mean()
        ema_slow = data['Close'].ewm(span=slow, adjust=False).mean()
        
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        
        result = pd.DataFrame(index=data.index)
        result['MACD'] = macd_line
        result['Signal'] = signal_line
        result['Histogram'] = histogram
        
        return result
    
    def calculate_rsi(self, data: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """计算RSI指标"""
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        result = pd.DataFrame(index=data.index)
        result['RSI'] = rsi
        
        return result
    
    def save_figure(self, save_path: str, dpi: Optional[int] = None):
        """保存图表"""
        if self.fig is not None:
            self.fig.savefig(save_path, dpi=dpi or self.dpi, bbox_inches='tight')
            print(f"图表已保存到: {save_path}")
        else:
            print("警告: 没有可保存的图表，请先调用plot_candlestick()")
    
    def export_to_html(self, save_path: str):
        """导出为交互式HTML图表"""
        try:
            import plotly.graph_objects as go
            from plotly.subplots import make_subplots
            
            # 创建Plotly图表
            fig = make_subplots(
                rows=3, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.03,
                subplot_titles=('价格', '成交量', 'RSI'),
                row_heights=[0.6, 0.2, 0.2]
            )
            
            # 添加K线图
            fig.add_trace(
                go.Candlestick(
                    x=self.chart_data.index,
                    open=self.chart_data['Open'],
                    high=self.chart_data['High'],
                    low=self.chart_data['Low'],
                    close=self.chart_data['Close'],
                    name='价格'
                ),
                row=1, col=1
            )
            
            # 添加成交量
            colors = ['red' if row['Close'] >= row['Open'] else 'green' 
                     for _, row in self.chart_data.iterrows()]
            
            fig.add_trace(
                go.Bar(
                    x=self.chart_data.index,
                    y=self.chart_data['Volume'],
                    name='成交量',
                    marker_color=colors
                ),
                row=2, col=1
            )
            
            # 添加RSI
            if 'RSI' in self.technical_data:
                fig.add_trace(
                    go.Scatter(
                        x=self.technical_data['RSI'].index,
                        y=self.technical_data['RSI']['RSI'],
                        name='RSI',
                        line=dict(color='purple')
                    ),
                    row=3, col=1
                )
            
            # 更新布局
            fig.update_layout(
                title='交互式K线图',
                xaxis_title='日期',
                yaxis_title='价格',
                template='plotly_white',
                height=800,
                showlegend=True
            )
            
            # 保存为HTML
            fig.write_html(save_path)
            
            print(f"交互式图表已保存到: {save_path}")
            
        except ImportError:
            print("导出HTML需要安装plotly: pip install plotly")
        except Exception as e:
            print(f"导出HTML失败: {e}")
    
    def clear(self):
        """清除图表状态"""
        self.fig = None
        self.ax = None
        self.axes = {}
        self.chart_data = None
        self.technical_data = {}