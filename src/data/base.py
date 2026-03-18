"""
数据获取基类
定义统一的数据接口和缓存机制
"""

import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional, Union, Tuple
import os
import json

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataFetcher(ABC):
    """数据获取器基类"""
    
    def __init__(self, cache_dir: str = "./cache", cache_ttl: int = 3600):
        """
        初始化数据获取器
        
        Args:
            cache_dir: 缓存目录
            cache_ttl: 缓存有效期（秒）
        """
        self.cache_dir = cache_dir
        self.cache_ttl = cache_ttl
        os.makedirs(cache_dir, exist_ok=True)
        
    @abstractmethod
    def fetch_historical_data(self, symbol: str, start_date: str, end_date: str, 
                             interval: str = "1d") -> pd.DataFrame:
        """
        获取历史数据
        
        Args:
            symbol: 标的代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            interval: 时间间隔 (1d, 1h, 1m等)
            
        Returns:
            DataFrame with columns: ['open', 'high', 'low', 'close', 'volume']
        """
        pass
    
    @abstractmethod
    def fetch_realtime_data(self, symbol: str) -> Dict:
        """
        获取实时数据
        
        Args:
            symbol: 标的代码
            
        Returns:
            实时数据字典
        """
        pass
    
    def get_cache_key(self, symbol: str, start_date: str, end_date: str, 
                     interval: str) -> str:
        """生成缓存键"""
        return f"{symbol}_{start_date}_{end_date}_{interval}"
    
    def get_cache_path(self, cache_key: str) -> str:
        """获取缓存文件路径"""
        return os.path.join(self.cache_dir, f"{cache_key}.parquet")
    
    def is_cache_valid(self, cache_path: str) -> bool:
        """检查缓存是否有效"""
        if not os.path.exists(cache_path):
            return False
        
        # 检查文件修改时间
        mtime = os.path.getmtime(cache_path)
        current_time = datetime.now().timestamp()
        
        return (current_time - mtime) < self.cache_ttl
    
    def load_from_cache(self, cache_path: str) -> Optional[pd.DataFrame]:
        """从缓存加载数据"""
        try:
            if os.path.exists(cache_path):
                df = pd.read_parquet(cache_path)
                logger.info(f"从缓存加载数据: {cache_path}")
                return df
        except Exception as e:
            logger.warning(f"缓存加载失败: {e}")
        return None
    
    def save_to_cache(self, df: pd.DataFrame, cache_path: str):
        """保存数据到缓存"""
        try:
            df.to_parquet(cache_path)
            logger.info(f"数据保存到缓存: {cache_path}")
        except Exception as e:
            logger.error(f"缓存保存失败: {e}")
    
    def fetch_with_cache(self, symbol: str, start_date: str, end_date: str, 
                        interval: str = "1d") -> pd.DataFrame:
        """
        带缓存的数据获取
        
        Args:
            symbol: 标的代码
            start_date: 开始日期
            end_date: 结束日期
            interval: 时间间隔
            
        Returns:
            DataFrame with price data
        """
        cache_key = self.get_cache_key(symbol, start_date, end_date, interval)
        cache_path = self.get_cache_path(cache_key)
        
        # 尝试从缓存加载
        if self.is_cache_valid(cache_path):
            cached_data = self.load_from_cache(cache_path)
            if cached_data is not None:
                return cached_data
        
        # 从源获取数据
        logger.info(f"从源获取数据: {symbol} ({start_date} 到 {end_date})")
        df = self.fetch_historical_data(symbol, start_date, end_date, interval)
        
        # 标准化数据格式
        df = self._standardize_data(df)
        
        # 保存到缓存
        if not df.empty:
            self.save_to_cache(df, cache_path)
        
        return df
    
    def _standardize_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        标准化数据格式
        
        Returns:
            标准化的DataFrame with columns: 
            ['open', 'high', 'low', 'close', 'volume', 'timestamp']
        """
        # 确保必要的列存在
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        
        # 重命名列（如果使用不同的列名）
        column_mapping = {
            'Open': 'open', 'High': 'high', 'Low': 'low', 
            'Close': 'close', 'Volume': 'volume',
            '开盘': 'open', '最高': 'high', '最低': 'low',
            '收盘': 'close', '成交量': 'volume'
        }
        
        df = df.rename(columns=column_mapping)
        
        # 确保所有必需的列都存在
        for col in required_columns:
            if col not in df.columns:
                logger.warning(f"缺少列: {col}")
                # 如果缺少重要列，返回空DataFrame
                if col in ['open', 'high', 'low', 'close']:
                    return pd.DataFrame()
        
        # 确保数据类型正确
        for col in required_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 添加时间戳列（如果不存在）
        if 'timestamp' not in df.columns:
            if df.index.name == 'Date' or 'Date' in df.columns:
                df['timestamp'] = pd.to_datetime(df.index if df.index.name == 'Date' else df['Date'])
            else:
                # 使用索引作为时间戳
                df['timestamp'] = df.index
        
        # 按时间排序
        df = df.sort_values('timestamp')
        
        # 删除重复的时间戳
        df = df.drop_duplicates(subset=['timestamp'])
        
        # 重置索引
        df = df.reset_index(drop=True)
        
        return df
    
    def get_data_summary(self, df: pd.DataFrame) -> Dict:
        """获取数据摘要"""
        if df.empty:
            return {"error": "数据为空"}
        
        summary = {
            "start_date": df['timestamp'].min().strftime('%Y-%m-%d'),
            "end_date": df['timestamp'].max().strftime('%Y-%m-%d'),
            "data_points": len(df),
            "symbols": list(df.get('symbol', pd.Series([None])).unique()),
            "price_range": {
                "min": float(df['close'].min()),
                "max": float(df['close'].max()),
                "current": float(df['close'].iloc[-1])
            },
            "volume_stats": {
                "avg": float(df['volume'].mean()),
                "max": float(df['volume'].max())
            }
        }
        
        return summary