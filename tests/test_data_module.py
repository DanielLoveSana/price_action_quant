"""
数据模块测试
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import pandas as pd
from datetime import datetime, timedelta
from src.data.manager import DataManager
from src.data.yfinance_fetcher import YFinanceFetcher
from src.data.akshare_fetcher import AkshareFetcher


class TestDataManager:
    """数据管理器测试"""
    
    def setup_method(self):
        """测试前准备"""
        self.manager = DataManager(cache_dir="./test_cache")
        self.end_date = datetime.now().strftime('%Y-%m-%d')
        self.start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    def teardown_method(self):
        """测试后清理"""
        import shutil
        if os.path.exists("./test_cache"):
            shutil.rmtree("./test_cache")
    
    def test_detect_symbol_type(self):
        """测试标的类型检测"""
        # 测试美股
        assert self.manager.detect_symbol_type("AAPL") == "yfinance"
        assert self.manager.detect_symbol_type("TSLA") == "yfinance"
        
        # 测试港股
        assert self.manager.detect_symbol_type("0700.HK") == "yfinance"
        
        # 测试A股
        assert self.manager.detect_symbol_type("000001") == "akshare"
        assert self.manager.detect_symbol_type("600519") == "akshare"
        
        # 测试未知类型（默认yfinance）
        assert self.manager.detect_symbol_type("UNKNOWN") == "yfinance"
    
    def test_validate_dates(self):
        """测试日期验证"""
        # 有效日期
        is_valid, message = self.manager.validate_dates("2024-01-01", "2024-01-31")
        assert is_valid
        assert message == ""
        
        # 开始日期晚于结束日期
        is_valid, message = self.manager.validate_dates("2024-01-31", "2024-01-01")
        assert not is_valid
        assert "不能晚于" in message
        
        # 无效日期格式
        is_valid, message = self.manager.validate_dates("2024/01/01", "2024-01-31")
        assert not is_valid
        assert "格式错误" in message
    
    def test_get_fetcher(self):
        """测试获取数据获取器"""
        # 自动检测
        fetcher = self.manager.get_fetcher("AAPL")
        assert isinstance(fetcher, YFinanceFetcher)
        
        fetcher = self.manager.get_fetcher("000001")
        assert isinstance(fetcher, AkshareFetcher)
        
        # 指定数据源
        fetcher = self.manager.get_fetcher(source="yfinance")
        assert isinstance(fetcher, YFinanceFetcher)
        
        fetcher = self.manager.get_fetcher(source="akshare")
        assert isinstance(fetcher, AkshareFetcher)
    
    @pytest.mark.skipif(os.getenv('SKIP_NETWORK_TESTS') == '1', 
                       reason="跳过网络依赖测试")
    def test_fetch_data_basic(self):
        """测试基本数据获取（需要网络）"""
        # 测试美股数据获取
        df = self.manager.fetch_data("AAPL", self.start_date, self.end_date)
        
        # 检查返回类型
        assert isinstance(df, pd.DataFrame)
        
        if not df.empty:
            # 检查必要的列
            required_cols = ['open', 'high', 'low', 'close', 'volume', 'timestamp']
            for col in required_cols:
                assert col in df.columns
            
            # 检查数据类型
            assert pd.api.types.is_numeric_dtype(df['close'])
            assert pd.api.types.is_datetime64_any_dtype(df['timestamp'])
            
            # 检查数据范围
            assert len(df) > 0
            assert df['timestamp'].min() >= pd.Timestamp(self.start_date)
            assert df['timestamp'].max() <= pd.Timestamp(self.end_date)
    
    def test_clean_data(self):
        """测试数据清洗"""
        # 创建测试数据
        test_data = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=10, freq='D'),
            'open': [100, 101, None, 103, 104, 105, 106, 107, 108, 109],
            'high': [102, 103, 104, 105, 106, 107, 108, 109, 110, 111],
            'low': [98, 99, 100, 101, 102, 103, 104, 105, 106, 107],
            'close': [101, 102, 103, 104, 105, 106, 107, 108, 109, 110],
            'volume': [1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000]
        })
        
        # 添加一个异常值
        test_data.loc[5, 'close'] = 1000
        
        # 清洗数据
        cleaned = self.manager.clean_data(test_data)
        
        # 检查结果
        assert isinstance(cleaned, pd.DataFrame)
        assert len(cleaned) == len(test_data)
        
        # 检查缺失值处理
        assert cleaned['open'].isna().sum() == 0
        
        # 检查异常值标记
        assert 'close_is_outlier' in cleaned.columns
        assert cleaned['close_is_outlier'].sum() > 0
        
        # 检查衍生指标
        assert 'range' in cleaned.columns
        assert 'body' in cleaned.columns
        assert 'upper_shadow' in cleaned.columns
        assert 'lower_shadow' in cleaned.columns
    
    def test_resample_data(self):
        """测试数据重采样"""
        # 创建日线数据
        daily_data = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=30, freq='D'),
            'open': range(100, 130),
            'high': range(102, 132),
            'low': range(98, 128),
            'close': range(101, 131),
            'volume': range(1000, 1030)
        })
        
        # 重采样为周线
        weekly_data = self.manager.resample_data(daily_data, "1w")
        
        # 检查结果
        assert isinstance(weekly_data, pd.DataFrame)
        assert len(weekly_data) > 0
        assert len(weekly_data) < len(daily_data)  # 周线应该更少
        
        # 检查必要的列
        required_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        for col in required_cols:
            assert col in weekly_data.columns
    
    def test_get_data_summary(self):
        """测试数据摘要"""
        # 创建测试数据
        test_data = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=5, freq='D'),
            'open': [100, 101, 102, 103, 104],
            'high': [102, 103, 104, 105, 106],
            'low': [98, 99, 100, 101, 102],
            'close': [101, 102, 103, 104, 105],
            'volume': [1000, 2000, 3000, 4000, 5000],
            'symbol': ['TEST'] * 5
        })
        
        # 获取摘要
        summary = self.manager.get_data_summary(test_data)
        
        # 检查摘要内容
        assert isinstance(summary, dict)
        assert 'start_date' in summary
        assert 'end_date' in summary
        assert 'data_points' in summary
        assert summary['data_points'] == 5
        assert 'price_range' in summary
        assert 'volume_stats' in summary


class TestYFinanceFetcher:
    """yfinance数据获取器测试"""
    
    def setup_method(self):
        self.fetcher = YFinanceFetcher(cache_dir="./test_cache")
    
    def test_standardize_interval(self):
        """测试时间间隔标准化"""
        assert self.fetcher._standardize_interval("1d") == "1d"
        assert self.fetcher._standardize_interval("1h") == "60m"
        assert self.fetcher._standardize_interval("1w") == "1wk"
        assert self.fetcher._standardize_interval("unknown") == "1d"
    
    def test_cache_operations(self):
        """测试缓存操作"""
        # 测试缓存键生成
        cache_key = self.fetcher.get_cache_key("AAPL", "2024-01-01", "2024-01-31", "1d")
        assert cache_key == "AAPL_2024-01-01_2024-01-31_1d"
        
        # 测试缓存路径
        cache_path = self.fetcher.get_cache_path(cache_key)
        assert cache_path.endswith(".parquet")
        assert "AAPL_2024-01-01_2024-01-31_1d" in cache_path


class TestAkshareFetcher:
    """akshare数据获取器测试"""
    
    def setup_method(self):
        self.fetcher = AkshareFetcher(cache_dir="./test_cache")
    
    def test_standardize_symbol(self):
        """测试A股代码标准化"""
        assert self.fetcher._standardize_symbol("000001") == "000001"
        assert self.fetcher._standardize_symbol("600519") == "600519"
        assert self.fetcher._standardize_symbol("000001.SZ") == "000001"
        assert self.fetcher._standardize_symbol("1") == "000001"
        assert self.fetcher._standardize_symbol("123") == "000123"


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])