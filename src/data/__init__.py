"""
价格行为学量化分析 - 数据模块
提供统一的多市场数据接入接口
"""

from .base import DataFetcher
from .yfinance_fetcher import YFinanceFetcher
from .akshare_fetcher import AkshareFetcher
from .manager import DataManager

__all__ = [
    'DataFetcher',
    'YFinanceFetcher', 
    'AkshareFetcher',
    'DataManager'
]

__version__ = '0.1.0'