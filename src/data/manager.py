"""
数据管理器
统一管理不同数据源，提供一致的接口
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Tuple
import logging
import re

from .yfinance_fetcher import YFinanceFetcher
from .akshare_fetcher import AkshareFetcher

logger = logging.getLogger(__name__)


class DataManager:
    """数据管理器"""
    
    def __init__(self, cache_dir: str = "./cache"):
        """
        初始化数据管理器
        
        Args:
            cache_dir: 缓存目录
        """
        self.cache_dir = cache_dir
        
        # 初始化数据获取器
        self.yfinance_fetcher = YFinanceFetcher(cache_dir)
        self.akshare_fetcher = AkshareFetcher(cache_dir)
        
        # 数据源映射
        self.source_mapping = {
            'yfinance': self.yfinance_fetcher,
            'akshare': self.akshare_fetcher
        }
        
        # 标的类型识别规则
        self.symbol_patterns = {
            'yfinance': [
                r'^[A-Z]{1,5}$',  # 美股: AAPL, TSLA
                r'^\d{4}\.[A-Z]{2}$',  # 港股: 0700.HK
                r'^[A-Z]+\.[A-Z]{2}$',  # 其他: BABA.N
            ],
            'akshare': [
                r'^\d{6}$',  # A股: 000001
                r'^sh\d{6}$',  # 上证指数: sh000001
                r'^sz\d{6}$',  # 深证指数: sz399001
            ]
        }
    
    def detect_symbol_type(self, symbol: str) -> str:
        """
        自动检测标的类型
        
        Args:
            symbol: 标的代码
            
        Returns:
            数据源类型: 'yfinance', 'akshare', 或 'unknown'
        """
        symbol = str(symbol).upper().strip()
        
        # 检查akshare模式
        for pattern in self.symbol_patterns['akshare']:
            if re.match(pattern, symbol):
                return 'akshare'
        
        # 检查yfinance模式
        for pattern in self.symbol_patterns['yfinance']:
            if re.match(pattern, symbol):
                return 'yfinance'
        
        # 默认使用yfinance（支持更多市场）
        return 'yfinance'
    
    def get_fetcher(self, symbol: Optional[str] = None, source: Optional[str] = None):
        """
        获取数据获取器
        
        Args:
            symbol: 标的代码（用于自动检测）
            source: 指定数据源
            
        Returns:
            数据获取器实例
        """
        if source:
            return self.source_mapping.get(source, self.yfinance_fetcher)
        
        if symbol:
            source_type = self.detect_symbol_type(symbol)
            return self.source_mapping.get(source_type, self.yfinance_fetcher)
        
        # 默认返回yfinance
        return self.yfinance_fetcher
    
    def fetch_data(self, symbol: str, start_date: str, end_date: str, 
                  interval: str = "1d", source: Optional[str] = None) -> pd.DataFrame:
        """
        获取历史数据（自动选择数据源）
        
        Args:
            symbol: 标的代码
            start_date: 开始日期
            end_date: 结束日期
            interval: 时间间隔
            source: 指定数据源
            
        Returns:
            DataFrame with price data
        """
        fetcher = self.get_fetcher(symbol, source)
        
        logger.info(f"使用数据源: {fetcher.__class__.__name__} 获取 {symbol}")
        
        # 获取数据
        df = fetcher.fetch_with_cache(symbol, start_date, end_date, interval)
        
        if df.empty:
            logger.warning(f"数据获取失败: {symbol}")
        
        return df
    
    def fetch_realtime(self, symbol: str, source: Optional[str] = None) -> Dict:
        """
        获取实时数据
        
        Args:
            symbol: 标的代码
            source: 指定数据源
            
        Returns:
            实时数据字典
        """
        fetcher = self.get_fetcher(symbol, source)
        return fetcher.fetch_realtime_data(symbol)
    
    def fetch_multiple_symbols(self, symbols: List[str], start_date: str, 
                              end_date: str, interval: str = "1d") -> Dict[str, pd.DataFrame]:
        """
        批量获取多个标的的数据
        
        Args:
            symbols: 标的代码列表
            start_date: 开始日期
            end_date: 结束日期
            interval: 时间间隔
            
        Returns:
            字典: {symbol: DataFrame}
        """
        results = {}
        
        for symbol in symbols:
            try:
                df = self.fetch_data(symbol, start_date, end_date, interval)
                if not df.empty:
                    results[symbol] = df
                    logger.info(f"成功获取 {symbol}: {len(df)} 行数据")
                else:
                    logger.warning(f"获取失败: {symbol}")
            except Exception as e:
                logger.error(f"获取 {symbol} 时出错: {e}")
        
        return results
    
    def get_data_summary(self, df: pd.DataFrame) -> Dict:
        """获取数据摘要"""
        if df.empty:
            return {"error": "数据为空"}
        
        # 使用基础类的标准化方法
        from .base import DataFetcher
        base_fetcher = DataFetcher()
        return base_fetcher.get_data_summary(df)
    
    def validate_dates(self, start_date: str, end_date: str) -> Tuple[bool, str]:
        """
        验证日期范围
        
        Returns:
            (是否有效, 错误信息)
        """
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            
            if start > end:
                return False, "开始日期不能晚于结束日期"
            
            if start < datetime(1900, 1, 1):
                return False, "开始日期太早"
            
            if end > datetime.now() + timedelta(days=365):
                return False, "结束日期不能超过当前日期一年后"
            
            return True, ""
            
        except ValueError:
            return False, "日期格式错误，请使用 YYYY-MM-DD 格式"
    
    def get_available_intervals(self, symbol: str) -> List[str]:
        """
        获取可用的时间间隔
        
        Args:
            symbol: 标的代码
            
        Returns:
            可用的时间间隔列表
        """
        fetcher = self.get_fetcher(symbol)
        
        if isinstance(fetcher, YFinanceFetcher):
            return list(fetcher.supported_intervals.keys())
        elif isinstance(fetcher, AkshareFetcher):
            return ['1d', '1w', '1m', 'daily', 'weekly', 'monthly']
        else:
            return ['1d']
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        数据清洗
        
        Args:
            df: 原始数据
            
        Returns:
            清洗后的数据
        """
        if df.empty:
            return df
        
        # 复制数据避免修改原始数据
        df_clean = df.copy()
        
        # 1. 处理缺失值
        numeric_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_cols:
            if col in df_clean.columns:
                # 前向填充缺失的价格数据
                df_clean[col] = df_clean[col].ffill()
        
        # 2. 处理异常值（使用3σ原则）
        for col in ['open', 'high', 'low', 'close']:
            if col in df_clean.columns:
                mean = df_clean[col].mean()
                std = df_clean[col].std()
                
                # 标记异常值但不删除（在量化分析中可能需要特殊处理）
                df_clean[f'{col}_is_outlier'] = abs(df_clean[col] - mean) > 3 * std
        
        # 3. 确保时间序列连续
        if 'timestamp' in df_clean.columns:
            df_clean = df_clean.sort_values('timestamp')
            df_clean = df_clean.drop_duplicates(subset=['timestamp'])
        
        # 4. 计算衍生指标
        if all(col in df_clean.columns for col in ['high', 'low', 'close']):
            df_clean['range'] = df_clean['high'] - df_clean['low']
            df_clean['body'] = abs(df_clean['close'] - df_clean['open'])
            df_clean['upper_shadow'] = df_clean['high'] - df_clean[['open', 'close']].max(axis=1)
            df_clean['lower_shadow'] = df_clean[['open', 'close']].min(axis=1) - df_clean['low']
        
        return df_clean
    
    def resample_data(self, df: pd.DataFrame, new_interval: str) -> pd.DataFrame:
        """
        重采样数据
        
        Args:
            df: 原始数据
            new_interval: 新的时间间隔
            
        Returns:
            重采样后的数据
        """
        if df.empty or 'timestamp' not in df.columns:
            return df
        
        # 设置时间索引
        df_resampled = df.set_index('timestamp')
        
        # 定义重采样规则
        ohlc_dict = {
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }
        
        # 转换间隔字符串为pandas频率
        interval_map = {
            '1m': '1T',
            '5m': '5T',
            '15m': '15T',
            '30m': '30T',
            '1h': '1H',
            '1d': '1D',
            '1w': '1W',
            '1mo': '1M'
        }
        
        freq = interval_map.get(new_interval, '1D')
        
        try:
            # 执行重采样
            df_resampled = df_resampled.resample(freq).agg(ohlc_dict)
            
            # 删除全为NaN的行
            df_resampled = df_resampled.dropna(subset=['open', 'high', 'low', 'close'])
            
            # 重置索引
            df_resampled = df_resampled.reset_index()
            
            logger.info(f"数据重采样完成: {len(df)} -> {len(df_resampled)} 行")
            
            return df_resampled
            
        except Exception as e:
            logger.error(f"重采样失败: {e}")
            return df
    
    def export_data(self, df: pd.DataFrame, format: str = 'csv', 
                   filename: Optional[str] = None) -> str:
        """
        导出数据
        
        Args:
            df: 数据
            format: 导出格式 (csv, excel, parquet, json)
            filename: 文件名
            
        Returns:
            文件路径
        """
        if df.empty:
            raise ValueError("数据为空，无法导出")
        
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"export_{timestamp}.{format}"
        
        filepath = f"./exports/{filename}"
        
        try:
            if format == 'csv':
                df.to_csv(filepath, index=False)
            elif format == 'excel':
                df.to_excel(filepath, index=False)
            elif format == 'parquet':
                df.to_parquet(filepath, index=False)
            elif format == 'json':
                df.to_json(filepath, orient='records', indent=2)
            else:
                raise ValueError(f"不支持的格式: {format}")
            
            logger.info(f"数据已导出: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"导出失败: {e}")
            raise