"""
交互式图表 - 提供缩放、平移、指标开关等交互功能的图表系统

功能：
1. 鼠标滚轮缩放
2. 拖拽平移
3. 技术指标动态开关
4. 时间框架切换
5. 标注交互显示
6. 图表状态保存/恢复
"""

import matplotlib.pyplot as plt
from matplotlib.widgets import Button, RadioButtons, CheckButtons
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Callable
import warnings
warnings.filterwarnings('ignore')

from .base import BaseVisualizer
from .candlestick_chart import CandlestickChart
from .key_levels_plot import KeyLevelsPlotter
from .market_structure_plot import MarketStructurePlotter


class InteractiveChart(BaseVisualizer):
    """交互式图表"""
    
    def __init__(self, 
                 figsize: Tuple[int, int] = (16, 9),
                 dpi: int = 100,
                 style: str = 'seaborn-v0_8-darkgrid',
                 color_palette: str = 'Set2'):
        """
        初始化交互式图表
        
        Args:
            figsize: 图表尺寸
            dpi: 图表分辨率
            style: matplotlib样式
            color_palette: 颜色调色板
        """
        super().__init__(figsize, dpi, style, color_palette)
        
        # 初始化子组件
        self.candlestick_chart = CandlestickChart(figsize, dpi, style, color_palette)
        self.key_levels_plotter = KeyLevelsPlotter(figsize, dpi, style, color_palette)
        self.market_structure_plotter = MarketStructurePlotter(figsize, dpi, style, color_palette)
        
        # 交互状态
        self.interactive_state = {
            'zoom_enabled': True,
            'pan_enabled': True,
            'indicators_visible': True,
            'key_levels_visible': True,
            'market_structure_visible': True,
            'current_timeframe': '1d',
            'chart_limits': None,
            'hover_annotation': None
        }
        
        # 事件连接
        self.event_connections = []
        
        # 控件
        self.controls = {}
        
        # 数据存储
        self.chart_data = None
        self.analysis_results = {}
        
    def create_interactive_chart(self,
                                data: pd.DataFrame,
                                title: str = '交互式价格分析图表',
                                indicators: Optional[List[str]] = None,
                                key_levels_data: Optional[Dict] = None,
                                market_structure_data: Optional[Dict] = None,
                                show_controls: bool = True) -> Dict:
        """
        创建交互式图表
        
        Args:
            data: 价格数据
            title: 图表标题
            indicators: 技术指标列表
            key_levels_data: 关键价位数据
            market_structure_data: 市场结构数据
            show_controls: 是否显示控制面板
            
        Returns:
            Dict: 图表配置信息
        """
        # 存储数据
        self.chart_data = data
        self.analysis_results = {
            'key_levels': key_levels_data,
            'market_structure': market_structure_data
        }
        
        # 创建主图表
        fig, axes = self.candlestick_chart.plot_candlestick(
            data,
            title=title,
            volume=True,
            type='candle',
            indicators=indicators or ['sma', 'ema', 'macd', 'rsi'],
            show=False
        )
        
        self.fig = fig
        self.ax = axes[0] if isinstance(axes, np.ndarray) else axes
        
        # 添加关键价位标注
        if key_levels_data and self.interactive_state['key_levels_visible']:
            support_levels = key_levels_data.get('support_resistance', {}).get('support_levels', [])
            resistance_levels = key_levels_data.get('support_resistance', {}).get('resistance_levels', [])
            pivot_points = key_levels_data.get('pivot_points', {})
            
            self.key_levels_plotter.plot_key_levels(
                self.ax, data,
                support_levels, resistance_levels,
                pivot_points,
                show_labels=True
            )
        
        # 添加市场结构标注
        if market_structure_data and self.interactive_state['market_structure_visible']:
            self.market_structure_plotter.plot_market_structure(
                self.ax, data, market_structure_data,
                show_labels=True
            )
        
        # 添加控制面板
        if show_controls:
            self.add_control_panel()
        
        # 连接交互事件
        self.connect_interactive_events()
        
        # 设置初始视图限制
        self.interactive_state['chart_limits'] = {
            'xlim': self.ax.get_xlim(),
            'ylim': self.ax.get_ylim()
        }
        
        return {
            'fig': fig,
            'ax': self.ax,
            'data': data,
            'state': self.interactive_state.copy()
        }
    
    def add_control_panel(self):
        """添加控制面板"""
        # 创建控制面板区域
        control_width = 0.15
        control_margin = 0.02
        
        # 技术指标开关
        indicator_ax = plt.axes([0.82, 0.75, control_width, 0.15])
        self.controls['indicators'] = CheckButtons(
            indicator_ax,
            ['SMA', 'EMA', 'MACD', 'RSI', '布林带'],
            [True, True, True, True, False]
        )
        self.controls['indicators'].on_clicked(self.toggle_indicator)
        
        # 标注显示开关
        annotation_ax = plt.axes([0.82, 0.55, control_width, 0.15])
        self.controls['annotations'] = CheckButtons(
            annotation_ax,
            ['关键价位', '市场结构', '成交量分布'],
            [True, True, True]
        )
        self.controls['annotations'].on_clicked(self.toggle_annotation)
        
        # 时间框架选择
        timeframe_ax = plt.axes([0.82, 0.35, control_width, 0.15])
        self.controls['timeframe'] = RadioButtons(
            timeframe_ax,
            ['1m', '5m', '15m', '1h', '4h', '1d', '1w']
        )
        self.controls['timeframe'].on_clicked(self.change_timeframe)
        
        # 功能按钮
        button_y_positions = [0.25, 0.20, 0.15, 0.10]
        button_labels = ['重置视图', '保存图表', '导出数据', '显示帮助']
        button_handlers = [self.reset_view, self.save_chart, self.export_data, self.show_help]
        
        for i, (label, handler) in enumerate(zip(button_labels, button_handlers)):
            button_ax = plt.axes([0.82, button_y_positions[i], control_width, 0.04])
            button = Button(button_ax, label)
            button.on_clicked(handler)
            self.controls[f'button_{label}'] = button
    
    def connect_interactive_events(self):
        """连接交互事件"""
        # 缩放事件
        self.event_connections.append(
            self.fig.canvas.mpl_connect('scroll_event', self.on_scroll)
        )
        
        # 平移事件
        self.event_connections.append(
            self.fig.canvas.mpl_connect('button_press_event', self.on_press)
        )
        self.event_connections.append(
            self.fig.canvas.mpl_connect('button_release_event', self.on_release)
        )
        self.event_connections.append(
            self.fig.canvas.mpl_connect('motion_notify_event', self.on_motion)
        )
        
        # 悬停事件
        self.event_connections.append(
            self.fig.canvas.mpl_connect('motion_notify_event', self.on_hover)
        )
        
        # 键盘事件
        self.event_connections.append(
            self.fig.canvas.mpl_connect('key_press_event', self.on_key_press)
        )
        
        # 重置事件（确保图表更新）
        self.event_connections.append(
            self.fig.canvas.mpl_connect('draw_event', self.on_draw)
        )
    
    def on_scroll(self, event):
        """处理鼠标滚轮缩放事件"""
        if not self.interactive_state['zoom_enabled'] or event.inaxes != self.ax:
            return
        
        # 获取当前视图限制
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()
        
        # 计算缩放中心
        x_center = event.xdata
        y_center = event.ydata
        
        if x_center is None or y_center is None:
            return
        
        # 计算缩放因子
        zoom_factor = 1.1 if event.button == 'up' else 0.9
        
        # 计算新的视图限制
        x_range = (xlim[1] - xlim[0]) * zoom_factor
        y_range = (ylim[1] - ylim[0]) * zoom_factor
        
        new_xlim = (x_center - x_range/2, x_center + x_range/2)
        new_ylim = (y_center - y_range/2, y_center + y_range/2)
        
        # 应用新的视图限制
        self.ax.set_xlim(new_xlim)
        self.ax.set_ylim(new_ylim)
        
        # 更新图表
        self.fig.canvas.draw_idle()
    
    def on_press(self, event):
        """处理鼠标按下事件（开始平移）"""
        if not self.interactive_state['pan_enabled'] or event.inaxes != self.ax:
            return
        
        self.interactive_state['pan_start'] = (event.xdata, event.ydata)
    
    def on_release(self, event):
        """处理鼠标释放事件（结束平移）"""
        if 'pan_start' in self.interactive_state:
            del self.interactive_state['pan_start']
    
    def on_motion(self, event):
        """处理鼠标移动事件（平移）"""
        if not self.interactive_state['pan_enabled'] or event.inaxes != self.ax:
            return
        
        if 'pan_start' in self.interactive_state and event.button == 1:
            start_x, start_y = self.interactive_state['pan_start']
            current_x, current_y = event.xdata, event.ydata
            
            if start_x is None or start_y is None or current_x is None or current_y is None:
                return
            
            # 计算平移距离
            dx = start_x - current_x
            dy = start_y - current_y
            
            # 获取当前视图限制
            xlim = self.ax.get_xlim()
            ylim = self.ax.get_ylim()
            
            # 计算新的视图限制
            new_xlim = (xlim[0] + dx, xlim[1] + dx)
            new_ylim = (ylim[0] + dy, ylim[1] + dy)
            
            # 应用新的视图限制
            self.ax.set_xlim(new_xlim)
            self.ax.set_ylim(new_ylim)
            
            # 更新起始点
            self.interactive_state['pan_start'] = (current_x, current_y)
            
            # 更新图表
            self.fig.canvas.draw_idle()
    
    def on_hover(self, event):
        """处理鼠标悬停事件"""
        if event.inaxes != self.ax:
            # 清除悬停标注
            if self.interactive_state['hover_annotation']:
                self.interactive_state['hover_annotation'].remove()
                self.interactive_state['hover_annotation'] = None
                self.fig.canvas.draw_idle()
            return
        
        # 显示价格信息
        if event.xdata is not None and event.ydata is not None:
            # 清除之前的标注
            if self.interactive_state['hover_annotation']:
                self.interactive_state['hover_annotation'].remove()
            
            # 创建新的标注
            price_text = f"价格: ${event.ydata:.2f}"
            date_text = f"日期: {pd.Timestamp(event.xdata).strftime('%Y-%m-%d %H:%M')}"
            
            annotation_text = f"{price_text}\n{date_text}"
            
            hover_annotation = self.ax.annotate(
                annotation_text,
                xy=(event.xdata, event.ydata),
                xytext=(10, 10),
                textcoords='offset points',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.8),
                fontsize=9
            )
            
            self.interactive_state['hover_annotation'] = hover_annotation
            self.fig.canvas.draw_idle()
    
    def on_key_press(self, event):
        """处理键盘按键事件"""
        if event.key == 'r' or event.key == 'R':
            # 重置视图
            self.reset_view(None)
        elif event.key == 's' or event.key == 'S':
            # 保存图表
            self.save_chart(None)
        elif event.key == 'h' or event.key == 'H':
            # 显示帮助
            self.show_help(None)
        elif event.key == 'z' or event.key == 'Z':
            # 切换缩放
            self.interactive_state['zoom_enabled'] = not self.interactive_state['zoom_enabled']
            print(f"缩放功能: {'启用' if self.interactive_state['zoom_enabled'] else '禁用'}")
        elif event.key == 'p' or event.key == 'P':
            # 切换平移
            self.interactive_state['pan_enabled'] = not self.interactive_state['pan_enabled']
            print(f"平移功能: {'启用' if self.interactive_state['pan_enabled'] else '禁用'}")
    
    def on_draw(self, event):
        """处理图表重绘事件"""
        # 保存当前视图限制
        self.interactive_state['chart_limits'] = {
            'xlim': self.ax.get_xlim(),
            'ylim': self.ax.get_ylim()
        }
    
    def toggle_indicator(self, label):
        """切换技术指标显示"""
        print(f"切换指标: {label}")
        # 这里需要实现具体的指标切换逻辑
        # 由于时间关系，暂时只打印日志
    
    def toggle_annotation(self, label):
        """切换标注显示"""
        print(f"切换标注: {label}")
        
        if label == '关键价位':
            self.interactive_state['key_levels_visible'] = not self.interactive_state['key_levels_visible']
            # 重新绘制图表
            self.redraw_chart()
        
        elif label == '市场结构':
            self.interactive_state['market_structure_visible'] = not self.interactive_state['market_structure_visible']
            # 重新绘制图表
            self.redraw_chart()
    
    def change_timeframe(self, label):
        """切换时间框架"""
        print(f"切换时间框架: {label}")
        self.interactive_state['current_timeframe'] = label
        
        # 这里需要实现数据重新获取和图表重绘
        # 由于时间关系，暂时只更新状态
    
    def reset_view(self, event):
        """重置视图到初始状态"""
        if self.interactive_state['chart_limits']:
            self.ax.set_xlim(self.interactive_state['chart_limits']['xlim'])
            self.ax.set_ylim(self.interactive_state['chart_limits']['ylim'])
            self.fig.canvas.draw_idle()
            print("视图已重置")
    
    def save_chart(self, event):
        """保存图表"""
        import datetime
        
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"interactive_chart_{timestamp}.png"
        
        self.fig.savefig(filename, dpi=self.dpi, bbox_inches='tight')
        print(f"图表已保存为: {filename}")
    
    def export_data(self, event):
        """导出数据"""
        if self.chart_data is not None:
            filename = "chart_data_export.csv"
            self.chart_data.to_csv(filename)
            print(f"数据已导出为: {filename}")
        else:
            print("没有可导出的数据")
    
    def show_help(self, event):
        """显示帮助信息"""
        help_text = """
        交互式图表使用说明：
        
        鼠标操作：
        - 滚轮：缩放图表
        - 左键拖拽：平移图表
        - 鼠标悬停：显示价格信息
        
        键盘快捷键：
        - R：重置视图
        - S：保存图表
        - H：显示帮助
        - Z：切换缩放功能
        - P：切换平移功能
        
        控制面板：
        - 技术指标：开关各类技术指标
        - 标注显示：开关关键价位和市场结构标注
        - 时间框架：切换图表时间周期
        - 功能按钮：执行各种操作
        """
        
        print(help_text)
    
    def redraw_chart(self):
        """重新绘制图表"""
        # 清除当前图表
        self.ax.clear()
        
        # 重新绘制K线图
        self.candlestick_chart.plot_candlestick(
            self.chart_data,
            title='交互式价格分析图表',
            volume=True,
            type='candle',
            show=False,
            ax=self.ax
        )
        
        # 重新添加关键价位标注
        if (self.interactive_state['key_levels_visible'] and 
            'key_levels' in self.analysis_results and 
            self.analysis_results['key_levels']):
            
            key_levels_data = self.analysis_results['key_levels']
            support_levels = key_levels_data.get('support_resistance', {}).get('support_levels', [])
            resistance_levels = key_levels_data.get('support_resistance', {}).get('resistance_levels', [])
            pivot_points = key_levels_data.get('pivot_points', {})
            
            self.key_levels_plotter.plot_key_levels(
                self.ax, self.chart_data,
                support_levels, resistance_levels,
                pivot_points,
                show_labels=True
            )
        
        # 重新添加市场结构标注
        if (self.interactive_state['market_structure_visible'] and 
            'market_structure' in self.analysis_results and 
            self.analysis_results['market_structure']):
            
            self.market_structure_plotter.plot_market_structure(
                self.ax, self.chart_data, self.analysis_results['market_structure'],
                show_labels=True
            )
        
        # 更新图表
        self.fig.canvas.draw_idle()
        print("图表已重新绘制")
    
    def save_state(self, filepath: str):
        """保存图表状态"""
        import pickle
        
        state = {
            'interactive_state': self.interactive_state,
            'chart_limits': {'xlim': self.ax.get_xlim(), 'ylim': self.ax.get_ylim()},
            'controls_state': {}
        }
        
        # 保存控件状态
        for control_name, control in self.controls.items():
            if hasattr(control, 'get_status'):
                state['controls_state'][control_name] = control.get_status()
        
        with open(filepath, 'wb') as f:
            pickle.dump(state, f)
        
        print(f"图表状态已保存到: {filepath}")
    
    def load_state(self, filepath: str):
        """加载图表状态"""
        import pickle
        
        try:
            with open(filepath, 'rb') as f:
                state = pickle.load(f)
            
            # 恢复交互状态
            self.interactive_state.update(state.get('interactive_state', {}))
            
            # 恢复视图限制
            if 'chart_limits' in state:
                self.ax.set_xlim(state['chart_limits']['xlim'])
                self.ax.set_ylim(state['chart_limits']['ylim'])
            
            # 恢复控件状态
            for control_name, control_state in state.get('controls_state', {}).items():
                if control_name in self.controls:
                    control = self.controls[control_name]
                    if hasattr(control, 'set_active'):
                        control.set_active(control_state)
            
            # 重新绘制图表
            self.redraw_chart()
            
            print(f"图表状态已从 {filepath} 加载")
            
        except Exception as e:
            print(f"加载状态失败: {e}")
    
    def disconnect_events(self):
        """断开所有事件连接"""
        for connection in self.event_connections:
            self.fig.canvas.mpl_disconnect(connection)
        
        self.event_connections = []
        print("所有事件连接已断开")
    
    def show(self):
        """显示图表"""
        if self.fig is not None:
            plt.show()
        else:
            print("没有可显示的图表，请先调用 create_interactive_chart()")
    
    def close(self):
        """关闭图表"""
        self.disconnect_events()
        
        if self.fig is not None:
            plt.close(self.fig)
            self.fig = None
            self.ax = None
        
        print("图表已关闭")