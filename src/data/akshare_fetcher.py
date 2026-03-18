"""
akshare数据获取器
专门用于A股市场数据
"""

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from .base import DataFetcher

logger = logging.getLogger(__name__)


class AkshareFetcher(DataFetcher):
    """akshare数据获取器（A股市场）"""
    
    def __init__(self, cache_dir: str = "./cache", cache_ttl: int = 3600):
        super().__init__(cache_dir, cache_ttl)
        
    def fetch_historical_data(self, symbol: str, start_date: str, end_date: str, 
                             interval: str = "1d") -> pd.DataFrame:
        """
        获取A股历史数据
        
        Args:
            symbol: A股代码 (如: 000001, 600519)
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            interval: 时间间隔 (目前主要支持日线)
            
        Returns:
            DataFrame with price data
        """
        try:
            # 标准化A股代码格式
            symbol = self._standardize_symbol(symbol)
            
            logger.info(f"从akshare获取A股数据: {symbol} ({start_date} 到 {end_date})")
            
            # 转换日期格式
            start_date_fmt = start_date.replace('-', '')
            end_date_fmt = end_date.replace('-', '')
            
            # 根据间隔选择不同的函数
            if interval in ['1d', 'daily']:
                df = ak.stock_zh_a_hist(symbol=symbol, period="daily", 
                                       start_date=start_date_fmt, 
                                       end_date=end_date_fmt, 
                                       adjust="qfq")  # 前复权
            elif interval in ['1w', 'weekly']:
                df = ak.stock_zh_a_hist(symbol=symbol, period="weekly",
                                       start_date=start_date_fmt,
                                       end_date=end_date_fmt,
                                       adjust="qfq")
            elif interval in ['1m', 'monthly']:
                df = ak.stock_zh_a_hist(symbol=symbol, period="monthly",
                                       start_date=start_date_fmt,
                                       end_date=end_date_fmt,
                                       adjust="qfq")
            else:
                logger.warning(f"不支持的间隔: {interval}, 使用日线数据")
                df = ak.stock_zh_a_hist(symbol=symbol, period="daily",
                                       start_date=start_date_fmt,
                                       end_date=end_date_fmt,
                                       adjust="qfq")
            
            if df.empty:
                logger.warning(f"akshare返回空数据: {symbol}")
                return pd.DataFrame()
            
            # 重命名列
            column_mapping = {
                '日期': 'timestamp',
                '开盘': 'open',
                '最高': 'high', 
                '最低': 'low',
                '收盘': 'close',
                '成交量': 'volume',
                '成交额': 'amount',
                '振幅': 'amplitude',
                '涨跌幅': 'pct_change',
                '涨跌额': 'change',
                '换手率': 'turnover'
            }
            
            df = df.rename(columns=column_mapping)
            
            # 添加symbol列
            df['symbol'] = symbol
            
            # 转换时间戳
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # 按时间排序
            df = df.sort_values('timestamp')
            
            logger.info(f"成功获取 {len(df)} 行A股数据")
            return df
            
        except Exception as e:
            logger.error(f"akshare数据获取失败: {symbol}, 错误: {e}")
            return pd.DataFrame()
    
    def fetch_realtime_data(self, symbol: str) -> Dict:
        """
        获取A股实时数据
        
        Args:
            symbol: A股代码
            
        Returns:
            实时数据字典
        """
        try:
            symbol = self._standardize_symbol(symbol)
            
            # 获取实时行情
            df = ak.stock_zh_a_spot_em()
            
            # 查找特定标的
            stock_data = df[df['代码'] == symbol]
            
            if stock_data.empty:
                logger.warning(f"未找到实时数据: {symbol}")
                return {'symbol': symbol, 'error': '未找到数据'}
            
            row = stock_data.iloc[0]
            
            realtime_data = {
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'name': row.get('名称', ''),
                'current_price': float(row.get('最新价', 0)),
                'change': float(row.get('涨跌额', 0)),
                'pct_change': float(row.get('涨跌幅', 0)),
                'open': float(row.get('今开', 0)),
                'high': float(row.get('最高', 0)),
                'low': float(row.get('最低', 0)),
                'close': float(row.get('昨收', 0)),
                'volume': float(row.get('成交量', 0)),
                'amount': float(row.get('成交额', 0)),
                'amplitude': float(row.get('振幅', 0)),
                'turnover': float(row.get('换手率', 0)),
                'pe_ratio': float(row.get('市盈率-动态', 0)),
                'market_cap': float(row.get('总市值', 0)),
                'circulating_market_cap': float(row.get('流通市值', 0))
            }
            
            return realtime_data
            
        except Exception as e:
            logger.error(f"A股实时数据获取失败: {symbol}, 错误: {e}")
            return {'symbol': symbol, 'error': str(e)}
    
    def _standardize_symbol(self, symbol: str) -> str:
        """标准化A股代码"""
        # 移除可能的交易所后缀
        symbol = symbol.replace('.SZ', '').replace('.SH', '').replace('.BJ', '')
        
        # 确保是6位代码
        if len(symbol) < 6:
            symbol = symbol.zfill(6)
        
        return symbol
    
    def get_index_data(self, index_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """获取指数数据"""
        try:
            # 转换日期格式
            start_date_fmt = start_date.replace('-', '')
            end_date_fmt = end_date.replace('-', '')
            
            # 常见指数映射
            index_mapping = {
                '000001': 'sh000001',  # 上证指数
                '399001': 'sz399001',  # 深证成指
                '399006': 'sz399006',  # 创业板指
                '000300': 'sh000300',  # 沪深300
                '000905': 'sh000905',  # 中证500
                '000016': 'sh000016',  # 上证50
            }
            
            index_code = index_mapping.get(index_code, index_code)
            
            df = ak.index_zh_a_hist(symbol=index_code, period="daily",
                                   start_date=start_date_fmt,
                                   end_date=end_date_fmt)
            
            if df.empty:
                return pd.DataFrame()
            
            # 重命名列
            column_mapping = {
                '日期': 'timestamp',
                '开盘': 'open',
                '最高': 'high',
                '最低': 'low',
                '收盘': 'close',
                '成交量': 'volume',
                '成交额': 'amount',
                '振幅': 'amplitude',
                '涨跌幅': 'pct_change',
                '涨跌额': 'change'
            }
            
            df = df.rename(columns=column_mapping)
            df['symbol'] = index_code
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            return df
            
        except Exception as e:
            logger.error(f"指数数据获取失败: {index_code}, 错误: {e}")
            return pd.DataFrame()
    
    def get_sector_data(self, sector: str = "全部板块") -> pd.DataFrame:
        """获取板块数据"""
        try:
            df = ak.stock_board_industry_name_em()
            
            if sector != "全部板块":
                df = df[df['板块名称'] == sector]
            
            return df
            
        except Exception as e:
            logger.error(f"板块数据获取失败: {sector}, 错误: {e}")
            return pd.DataFrame()
    
    def get_market_overview(self) -> Dict:
        """获取市场概览"""
        try:
            # 获取市场总体数据
            overview = {
                'timestamp': datetime.now().isoformat(),
                'total_stocks': 0,
                'rising_stocks': 0,
                'falling_stocks': 0,
                'unchanged_stocks': 0,
                'total_market_cap': 0,
                'shanghai_index': 0,
                'shenzhen_index': 0,
                'chi_next_index': 0
            }
            
            # 获取主要指数
            indices = ['sh000001', 'sz399001', 'sz399006']
            for idx in indices:
                try:
                    df = ak.index_zh_a_hist(symbol=idx, period="daily", 
                                           start_date=datetime.now().strftime('%Y%m%d'),
                                           end_date=datetime.now().strftime('%Y%m%d'))
                    if not df.empty:
                        close_price = float(df.iloc[-1]['收盘'])
                        overview[f'{idx}_close'] = close_price
                except:
                    pass
            
            return overview
            
        except Exception as e:
            logger.error(f"市场概览获取失败: {e}")
            return {'error': str(e)}
    
    def get_financial_statements(self, symbol: str, report_type: str = "balance") -> pd.DataFrame:
        """获取财务报表"""
        try:
            symbol = self._standardize_symbol(symbol)
            
            if report_type == "balance":
                df = ak.stock_financial_balance_sheet(symbol)
            elif report_type == "income":
                df = ak.stock_financial_report_sina(symbol, symbol)
            elif report_type == "cashflow":
                df = ak.stock_financial_cash_flow_sina(symbol, symbol)
            else:
                logger.warning(f"不支持的报表类型: {report_type}")
                return pd.DataFrame()
            
            return df
            
        except Exception as e:
            logger.error(f"财务报表获取失败: {symbol}, 类型: {report_type}, 错误: {e}")
            return pd.DataFrame()