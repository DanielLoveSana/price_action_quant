"""
价格行为学量化分析 - 可视化模块

提供完整的图表可视化功能，包括：
1. K线图绘制 (支持多种样式和技术指标)
2. 关键价位标注 (支撑阻力、枢轴点、成交量分布)
3. 市场结构可视化 (趋势线、结构突破点、摆动点)
4. 交互式图表 (缩放、平移、指标切换)

模块设计原则：
- 模块化：每个可视化功能独立可复用
- 高性能：支持大数据量快速渲染
- 易用性：简洁的API接口
- 可扩展：方便添加新的可视化功能
"""

from .base import BaseVisualizer
from .candlestick_chart import CandlestickChart
from .key_levels_plot import KeyLevelsPlotter
from .market_structure_plot import MarketStructurePlotter
from .interactive_chart import InteractiveChart
from .report_generator import ReportGenerator

__all__ = [
    'BaseVisualizer',
    'CandlestickChart',
    'KeyLevelsPlotter',
    'MarketStructurePlotter',
    'InteractiveChart',
    'ReportGenerator'
]

__version__ = '1.0.0'