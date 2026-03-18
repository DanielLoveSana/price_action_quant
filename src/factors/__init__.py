"""
价格行为学量化因子模块
包含市场结构、关键价位、多时间框架等六大类因子
"""

__version__ = "1.0.0"
__author__ = "Price Action Quant Team"

from .market_structure import (
    MarketStructureAnalyzer,
    TrendAnalyzer,
    StructureBreakAnalyzer,
    SwingPointDetector
)

__all__ = [
    "MarketStructureAnalyzer",
    "TrendAnalyzer", 
    "StructureBreakAnalyzer",
    "SwingPointDetector"
]