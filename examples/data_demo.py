#!/usr/bin/env python3
"""
数据模块使用示例
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.manager import DataManager
from src.data.yfinance_fetcher import YFinanceFetcher
from src.data.akshare_fetcher import AkshareFetcher
import pandas as pd
from datetime import datetime, timedelta


def demo_basic_usage():
    """基本使用示例"""
    print("=" * 60)
    print("数据模块使用示例")
    print("=" * 60)
    
    # 创建数据管理器
    manager = DataManager(cache_dir="./cache")
    
    # 示例1: 获取美股数据 (AAPL)
    print("\n1. 获取美股数据 (AAPL)")
    print("-" * 40)
    
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    df_aapl = manager.fetch_data("AAPL", start_date, end_date, interval="1d")
    
    if not df_aapl.empty:
        print(f"获取到 {len(df_aapl)} 行数据")
        print(f"时间范围: {df_aapl['timestamp'].min()} 到 {df_aapl['timestamp'].max()}")
        print(f"价格范围: ${df_aapl['close'].min():.2f} - ${df_aapl['close'].max():.2f}")
        print(f"最新收盘价: ${df_aapl['close'].iloc[-1]:.2f}")
        
        # 显示前5行
        print("\n前5行数据:")
        print(df_aapl[['timestamp', 'open', 'high', 'low', 'close', 'volume']].head())
    else:
        print("数据获取失败")
    
    # 示例2: 获取A股数据 (贵州茅台)
    print("\n2. 获取A股数据 (600519 - 贵州茅台)")
    print("-" * 40)
    
    df_600519 = manager.fetch_data("600519", start_date, end_date, interval="1d")
    
    if not df_600519.empty:
        print(f"获取到 {len(df_600519)} 行数据")
        print(f"时间范围: {df_600519['timestamp'].min()} 到 {df_600519['timestamp'].max()}")
        print(f"价格范围: ¥{df_600519['close'].min():.2f} - ¥{df_600519['close'].max():.2f}")
        print(f"最新收盘价: ¥{df_600519['close'].iloc[-1]:.2f}")
    else:
        print("A股数据获取失败（可能需要VPN）")
    
    # 示例3: 获取实时数据
    print("\n3. 获取实时数据")
    print("-" * 40)
    
    realtime_aapl = manager.fetch_realtime("AAPL")
    if 'current_price' in realtime_aapl:
        print(f"AAPL实时价格: ${realtime_aapl['current_price']}")
        print(f"涨跌幅: {realtime_aapl.get('pct_change', 'N/A')}%")
        print(f"成交量: {realtime_aapl.get('volume', 'N/A')}")
    
    # 示例4: 批量获取数据
    print("\n4. 批量获取多个标的")
    print("-" * 40)
    
    symbols = ["AAPL", "MSFT", "GOOGL"]
    all_data = manager.fetch_multiple_symbols(symbols, start_date, end_date)
    
    for symbol, df in all_data.items():
        if not df.empty:
            latest_close = df['close'].iloc[-1]
            print(f"{symbol}: ${latest_close:.2f} ({len(df)} 行数据)")
    
    # 示例5: 数据清洗
    print("\n5. 数据清洗示例")
    print("-" * 40)
    
    if not df_aapl.empty:
        cleaned_data = manager.clean_data(df_aapl)
        print(f"原始数据: {len(df_aapl)} 行")
        print(f"清洗后: {len(cleaned_data)} 行")
        
        # 检查是否有异常值
        outlier_cols = [col for col in cleaned_data.columns if 'is_outlier' in col]
        if outlier_cols:
            for col in outlier_cols:
                outlier_count = cleaned_data[col].sum()
                if outlier_count > 0:
                    print(f"检测到 {outlier_count} 个{col.replace('_is_outlier', '')}异常值")
    
    # 示例6: 数据摘要
    print("\n6. 数据摘要")
    print("-" * 40)
    
    if not df_aapl.empty:
        summary = manager.get_data_summary(df_aapl)
        for key, value in summary.items():
            if isinstance(value, dict):
                print(f"{key}:")
                for k, v in value.items():
                    print(f"  {k}: {v}")
            else:
                print(f"{key}: {value}")


def demo_advanced_features():
    """高级功能示例"""
    print("\n" + "=" * 60)
    print("高级功能示例")
    print("=" * 60)
    
    manager = DataManager()
    
    # 示例: 直接使用特定数据源
    print("\n1. 直接使用yfinance数据源")
    print("-" * 40)
    
    yf_fetcher = YFinanceFetcher()
    
    # 获取分红历史
    dividends = yf_fetcher.get_dividend_history(
        "AAPL", 
        start_date="2023-01-01",
        end_date="2023-12-31"
    )
    
    if not dividends.empty:
        print(f"AAPL 2023年分红记录: {len(dividends)} 次")
        print(dividends[['timestamp', 'dividend']])
    
    # 示例: 使用akshare获取A股指数
    print("\n2. 使用akshare获取A股指数")
    print("-" * 40)
    
    ak_fetcher = AkshareFetcher()
    
    # 获取上证指数
    sh_index = ak_fetcher.get_index_data(
        "000001",
        start_date="2024-01-01",
        end_date="2024-01-31"
    )
    
    if not sh_index.empty:
        print(f"上证指数数据: {len(sh_index)} 行")
        print(f"最新收盘: {sh_index['close'].iloc[-1]:.2f}")
    
    # 示例: 数据重采样
    print("\n3. 数据重采样示例")
    print("-" * 40)
    
    # 先获取日线数据
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
    
    df_daily = manager.fetch_data("AAPL", start_date, end_date, interval="1d")
    
    if not df_daily.empty:
        # 重采样为周线
        df_weekly = manager.resample_data(df_daily, "1w")
        
        print(f"日线数据: {len(df_daily)} 行")
        print(f"周线数据: {len(df_weekly)} 行")
        
        if not df_weekly.empty:
            print("\n周线数据前3行:")
            print(df_weekly[['timestamp', 'open', 'high', 'low', 'close', 'volume']].head(3))


def demo_error_handling():
    """错误处理示例"""
    print("\n" + "=" * 60)
    print("错误处理示例")
    print("=" * 60)
    
    manager = DataManager()
    
    # 示例1: 无效日期
    print("\n1. 无效日期验证")
    print("-" * 40)
    
    is_valid, message = manager.validate_dates("2024-13-01", "2024-01-01")
    print(f"日期 '2024-13-01' 到 '2024-01-01': {is_valid} - {message}")
    
    # 示例2: 不存在的标的
    print("\n2. 获取不存在的标的")
    print("-" * 40)
    
    df_invalid = manager.fetch_data("INVALID_SYMBOL", "2024-01-01", "2024-01-31")
    if df_invalid.empty:
        print("正确处理了无效标的")
    
    # 示例3: 空数据处理
    print("\n3. 空数据处理")
    print("-" * 40)
    
    empty_df = pd.DataFrame()
    summary = manager.get_data_summary(empty_df)
    print(f"空数据摘要: {summary}")


def main():
    """主函数"""
    print("🚀 Price Action Quant - 数据模块演示")
    
    try:
        demo_basic_usage()
        demo_advanced_features()
        demo_error_handling()
        
        print("\n" + "=" * 60)
        print("✅ 演示完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 演示过程中出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()