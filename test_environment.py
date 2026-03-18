#!/usr/bin/env python3
"""
测试环境配置和依赖
"""

import sys
import importlib

def test_imports():
    """测试所有关键依赖的导入"""
    dependencies = [
        ('pandas', 'pd'),
        ('numpy', 'np'),
        ('matplotlib', 'mpl'),
        ('plotly', 'plotly'),
        ('yfinance', 'yf'),
        ('ta', 'ta'),
        ('mplfinance', 'mpf'),
        ('seaborn', 'sns'),
        ('scipy', 'sp'),
        ('sklearn', 'sklearn'),
        ('statsmodels', 'sm'),
        ('akshare', 'ak'),
        ('ccxt', 'ccxt'),
    ]
    
    print("🧪 测试依赖导入...")
    print("=" * 50)
    
    for module_name, alias in dependencies:
        try:
            module = importlib.import_module(module_name)
            print(f"✅ {module_name} v{module.__version__ if hasattr(module, '__version__') else 'unknown'}")
        except ImportError as e:
            print(f"❌ {module_name}: {e}")
        except Exception as e:
            print(f"⚠️  {module_name}: {e}")
    
    print("=" * 50)

def test_python_version():
    """测试Python版本"""
    print(f"🐍 Python版本: {sys.version}")
    print(f"📁 虚拟环境: {'venv' if sys.prefix != sys.base_prefix else '系统环境'}")

def test_yfinance():
    """测试yfinance数据获取"""
    try:
        import yfinance as yf
        print("\n📊 测试yfinance数据获取...")
        ticker = yf.Ticker("AAPL")
        hist = ticker.history(period="1d")
        if not hist.empty:
            print(f"✅ AAPL数据获取成功: {len(hist)}行数据")
            print(f"   最新价格: ${hist['Close'].iloc[-1]:.2f}")
        else:
            print("⚠️  数据为空，可能是网络问题")
    except Exception as e:
        print(f"❌ yfinance测试失败: {e}")

def main():
    """主测试函数"""
    print("🚀 Price Action Quant 环境测试")
    print("=" * 50)
    
    test_python_version()
    test_imports()
    test_yfinance()
    
    print("\n🎉 环境测试完成！")

if __name__ == "__main__":
    main()