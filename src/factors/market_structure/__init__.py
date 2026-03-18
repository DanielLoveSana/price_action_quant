"""
市场结构因子模块
包含趋势识别、结构突破、摆动点检测等功能
"""

from .trend_analyzer import TrendAnalyzer
from .structure_break import StructureBreakAnalyzer
from .swing_points import SwingPointDetector
from .market_structure_analyzer import MarketStructureAnalyzer

__all__ = [
    "TrendAnalyzer",
    "StructureBreakAnalyzer",
    "SwingPointDetector",
    "MarketStructureAnalyzer"
]