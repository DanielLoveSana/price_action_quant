"""
yfinance数据获取器
支持美股、港股、A股（通过ADR）等市场
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from .base import DataFetcher

logger = logging.getLogger(__name__)


class YFinanceFetcher(DataFetcher):
    """yfinance数据获取器"""
    
    def __init__(self, cache_dir: str = "./cache", cache_ttl: int = 3600):
        super().__init__(cache_dir, cache_ttl)
        self.supported_intervals = {
            '1m': '1m', '2m': '2m', '5m': '5m', '15m': '15m', '30m': '30m',
            '60m': '60m', '90m': '90m', '1h': '60m', '1d': '1d', '5d': '5d',
            '1wk': '1wk', '1mo': '1mo', '3mo': '3mo'
        }
    
    def fetch_historical_data(self, symbol: str, start_date: str, end_date: str, 
                             interval: str = "1d") -> pd.DataFrame:
        """
        获取历史数据
        
        Args:
            symbol: 标的代码 (如: AAPL, 000001.SZ, 0700.HK)
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            interval: 时间间隔
            
        Returns:
            DataFrame with price data
        """
        try:
            # 标准化间隔
            interval = self._standardize_interval(interval)
            
            # 创建ticker对象
            ticker = yf.Ticker(symbol)
            
            # 获取历史数据
            logger.info(f"从yfinance获取数据: {symbol} ({start_date} 到 {end_date}, 间隔: {interval})")
            
            # yfinance需要将日期加一天
            end_date_adj = (datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
            
            df = ticker.history(start=start_date, end=end_date_adj, interval=interval)
            
            if df.empty:
                logger.warning(f"yfinance返回空数据: {symbol}")
                return pd.DataFrame()
            
            # 添加symbol列
            df['symbol'] = symbol
            
            # 重命名索引为timestamp
            df.index.name = 'timestamp'
            df = df.reset_index()
            
            logger.info(f"成功获取 {len(df)} 行数据")
            return df
            
        except Exception as e:
            logger.error(f"yfinance数据获取失败: {symbol}, 错误: {e}")
            return pd.DataFrame()
    
    def fetch_realtime_data(self, symbol: str) -> Dict:
        """
        获取实时数据
        
        Args:
            symbol: 标的代码
            
        Returns:
            实时数据字典
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # 提取关键信息
            realtime_data = {
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'current_price': info.get('regularMarketPrice', info.get('currentPrice')),
                'open': info.get('open'),
                'high': info.get('dayHigh'),
                'low': info.get('dayLow'),
                'previous_close': info.get('previousClose'),
                'volume': info.get('volume'),
                'market_cap': info.get('marketCap'),
                'currency': info.get('currency'),
                'exchange': info.get('exchange'),
                'short_name': info.get('shortName'),
                'long_name': info.get('longName')
            }
            
            # 清理None值
            realtime_data = {k: v for k, v in realtime_data.items() if v is not None}
            
            return realtime_data
            
        except Exception as e:
            logger.error(f"实时数据获取失败: {symbol}, 错误: {e}")
            return {'symbol': symbol, 'error': str(e)}
    
    def _standardize_interval(self, interval: str) -> str:
        """标准化时间间隔"""
        interval = interval.lower()
        return self.supported_intervals.get(interval, '1d')
    
    def get_market_status(self, symbol: str) -> Dict:
        """获取市场状态"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # 判断市场是否开放
            market_state = info.get('marketState', 'CLOSED')
            is_market_open = market_state == 'REGULAR'
            
            # 获取交易时间
            exchange_timezone = info.get('exchangeTimezoneName', 'Unknown')
            
            status = {
                'symbol': symbol,
                'is_market_open': is_market_open,
                'market_state': market_state,
                'exchange_timezone': exchange_timezone,
                'currency': info.get('currency'),
                'exchange': info.get('exchange'),
                'quote_type': info.get('quoteType'),
                'timestamp': datetime.now().isoformat()
            }
            
            return status
            
        except Exception as e:
            logger.error(f"市场状态获取失败: {symbol}, 错误: {e}")
            return {'symbol': symbol, 'error': str(e)}
    
    def search_symbols(self, query: str, limit: int = 10) -> List[Dict]:
        """搜索标的"""
        try:
            # yfinance没有直接搜索功能，这里使用简单实现
            # 在实际应用中可能需要结合其他API
            import requests
            
            # 使用雅虎财经搜索建议
            url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query}&quotesCount={limit}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers)
            data = response.json()
            
            symbols = []
            if 'quotes' in data:
                for quote in data['quotes'][:limit]:
                    symbols.append({
                        'symbol': quote.get('symbol'),
                        'name': quote.get('longname') or quote.get('shortname'),
                        'exchange': quote.get('exchange'),
                        'type': quote.get('quoteType'),
                        'score': quote.get('score', 0)
                    })
            
            return symbols
            
        except Exception as e:
            logger.error(f"标的搜索失败: {query}, 错误: {e}")
            return []
    
    def get_dividend_history(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """获取分红历史"""
        try:
            ticker = yf.Ticker(symbol)
            dividends = ticker.dividends
            
            if not dividends.empty:
                dividends_df = dividends.reset_index()
                dividends_df.columns = ['timestamp', 'dividend']
                dividends_df['symbol'] = symbol
                
                # 过滤日期范围
                mask = (dividends_df['timestamp'] >= pd.Timestamp(start_date)) & \
                       (dividends_df['timestamp'] <= pd.Timestamp(end_date))
                dividends_df = dividends_df[mask]
                
                return dividends_df
            
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"分红历史获取失败: {symbol}, 错误: {e}")
            return pd.DataFrame()
    
    def get_splits_history(self, symbol: str) -> pd.DataFrame:
        """获取拆股历史"""
        try:
            ticker = yf.Ticker(symbol)
            splits = ticker.splits
            
            if not splits.empty:
                splits_df = splits.reset_index()
                splits_df.columns = ['timestamp', 'split_ratio']
                splits_df['symbol'] = symbol
                
                return splits_df
            
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"拆股历史获取失败: {symbol}, 错误: {e}")
            return pd.DataFrame()