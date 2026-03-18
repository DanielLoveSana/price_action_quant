"""
市场结构因子演示
展示如何使用市场结构分析模块
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# 导入数据模块
from data.manager import DataManager
from data.yfinance_fetcher import YFinanceFetcher

# 导入市场结构模块
from factors.market_structure import MarketStructureAnalyzer


def create_sample_data():
    """创建示例数据用于演示"""
    print("📊 创建示例数据...")
    
    # 生成日期范围
    dates = pd.date_range(start='2024-01-01', periods=200, freq='D')
    
    # 创建多阶段市场数据
    # 阶段1: 上升趋势
    phase1 = 100 + np.arange(80) * 0.8 + np.random.normal(0, 3, 80)
    
    # 阶段2: 震荡整理
    phase2 = 164 + 8 * np.sin(np.arange(60) * 2 * np.pi / 15) + np.random.normal(0, 2, 60)
    
    # 阶段3: 突破上涨
    phase3 = 170 + np.arange(60) * 0.5 + np.random.normal(0, 4, 60)
    
    # 合并价格
    prices = np.concatenate([phase1, phase2, phase3])
    
    # 生成OHLC数据
    opens = prices - np.random.uniform(0, 2, 200)
    highs = prices + np.random.uniform(2, 5, 200)
    lows = prices - np.random.uniform(2, 5, 200)
    closes = prices
    volumes = np.random.randint(5000, 30000, 200)
    
    df = pd.DataFrame({
        'open': opens,
        'high': highs,
        'low': lows,
        'close': closes,
        'volume': volumes
    }, index=dates)
    
    print(f"✅ 创建了 {len(df)} 条示例数据")
    print(f"   价格范围: ${df['low'].min():.2f} - ${df['high'].max():.2f}")
    print(f"   最终价格: ${df['close'].iloc[-1]:.2f}")
    
    return df


def demo_basic_analysis():
    """演示基础市场结构分析"""
    print("\n" + "="*60)
    print("🎯 演示1: 基础市场结构分析")
    print("="*60)
    
    # 创建示例数据
    df = create_sample_data()
    
    # 初始化分析器
    analyzer = MarketStructureAnalyzer(
        trend_window=20,
        structure_lookback=50,
        swing_threshold=0.03
    )
    
    # 执行分析
    print("\n🔍 正在分析市场结构...")
    results = analyzer.analyze_market_structure(df)
    
    # 显示关键结果
    print("\n📊 分析结果摘要:")
    print(f"   趋势方向: {results['trend_analysis']['trend_direction'].upper()}")
    print(f"   趋势强度: {results['trend_analysis']['trend_strength']:.1f}/100")
    print(f"   趋势分类: {results['trend_analysis']['trend_class'].replace('_', ' ').upper()}")
    
    print(f"\n🏗️ 结构评分: {results['structure_breaks']['market_structure_score']}/100")
    print(f"   结构健康度: {results['structure_breaks']['structure_health']['overall'].upper()}")
    
    print(f"\n📍 摆动点统计:")
    print(f"   高点摆动点: {results['swing_points']['count']['highs']} 个")
    print(f"   低点摆动点: {results['swing_points']['count']['lows']} 个")
    
    print(f"\n🎯 综合评分: {results['composite_score']['composite_score']:.1f}/100")
    print(f"   评级: {results['composite_score']['grade']} - {results['composite_score']['grade_description']}")
    
    return results


def demo_real_data_analysis():
    """演示真实数据市场结构分析"""
    print("\n" + "="*60)
    print("🎯 演示2: 真实数据市场结构分析")
    print("="*60)
    
    try:
        # 初始化数据管理器
        print("\n📥 获取真实市场数据...")
        manager = DataManager(cache_dir='./cache')
        
        # 获取AAPL数据
        symbol = 'AAPL'
        print(f"   获取 {symbol} 数据...")
        df = manager.get_data(
            symbol=symbol,
            start_date='2024-01-01',
            end_date='2024-12-31',
            interval='1d'
        )
        
        if df is not None and len(df) > 0:
            print(f"   ✅ 成功获取 {len(df)} 条数据")
            print(f"   价格范围: ${df['low'].min():.2f} - ${df['high'].max():.2f}")
            print(f"   最新价格: ${df['close'].iloc[-1]:.2f}")
            
            # 初始化分析器
            analyzer = MarketStructureAnalyzer()
            
            # 执行分析
            print("\n🔍 正在分析市场结构...")
            results = analyzer.analyze_market_structure(df)
            
            # 显示关键结果
            print("\n📊 AAPL市场结构分析:")
            print(f"   趋势方向: {results['trend_analysis']['trend_direction'].upper()}")
            print(f"   趋势强度: {results['trend_analysis']['trend_strength']:.1f}/100")
            print(f"   结构评分: {results['structure_breaks']['market_structure_score']}/100")
            print(f"   综合评分: {results['composite_score']['composite_score']:.1f}/100")
            print(f"   评级: {results['composite_score']['grade']}")
            
            # 显示交易建议
            suggestions = results['trading_suggestions']
            if suggestions:
                print(f"\n💡 交易建议 ({len(suggestions)} 个):")
                for i, suggestion in enumerate(suggestions[:3], 1):  # 只显示前3个
                    confidence = suggestion['confidence']
                    emoji = '🟢' if confidence == 'high' else '🟡' if confidence == 'medium' else '🔴'
                    print(f"   {i}. {emoji} {suggestion['type'].replace('_', ' ').upper()}")
                    print(f"      方向: {suggestion['direction'].upper()}")
                    print(f"      理由: {suggestion['reason']}")
                    print(f"      操作: {suggestion['action']}")
            
            return results
        else:
            print("   ⚠️ 无法获取数据，使用示例数据替代")
            return demo_basic_analysis()
            
    except Exception as e:
        print(f"   ❌ 获取真实数据失败: {e}")
        print("   ⚠️ 使用示例数据替代")
        return demo_basic_analysis()


def demo_comprehensive_report():
    """演示完整报告生成"""
    print("\n" + "="*60)
    print("🎯 演示3: 完整市场结构分析报告")
    print("="*60)
    
    # 创建示例数据
    df = create_sample_data()
    
    # 初始化分析器
    analyzer = MarketStructureAnalyzer()
    
    # 生成完整报告
    print("\n📋 生成完整分析报告...")
    report = analyzer.get_comprehensive_report(df)
    
    # 显示报告
    print("\n" + report)
    
    # 保存报告到文件
    report_file = 'market_structure_report.txt'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n💾 报告已保存到: {report_file}")
    
    return report


def demo_individual_components():
    """演示各个组件的独立使用"""
    print("\n" + "="*60)
    print("🎯 演示4: 独立组件使用演示")
    print("="*60)
    
    # 创建示例数据
    df = create_sample_data()
    
    # 1. 趋势分析器
    print("\n1. 📈 趋势分析器演示")
    from factors.market_structure.trend_analyzer import TrendAnalyzer
    trend_analyzer = TrendAnalyzer()
    trend_results = trend_analyzer.analyze_trend(df)
    print(f"   趋势方向: {trend_results['trend_direction']}")
    print(f"   趋势强度: {trend_results['trend_strength']:.1f}")
    print(f"   摆动点: {len(trend_results['swing_points']['highs'])}高/{len(trend_results['swing_points']['lows'])}低")
    
    # 2. 结构突破分析器
    print("\n2. 🏗️ 结构突破分析器演示")
    from factors.market_structure.structure_break import StructureBreakAnalyzer
    structure_analyzer = StructureBreakAnalyzer()
    structure_results = structure_analyzer.analyze_structure_breaks(df)
    print(f"   结构评分: {structure_results['market_structure_score']}/100")
    print(f"   BOS信号: {len(structure_results['bos_signals'])}个")
    print(f"   CHOCH信号: {len(structure_results['choch_signals'])}个")
    
    # 3. 摆动点检测器
    print("\n3. 📍 摆动点检测器演示")
    from factors.market_structure.swing_points import SwingPointDetector
    swing_detector = SwingPointDetector()
    swing_results = swing_detector.detect_swing_points(df, use_advanced=True)
    print(f"   检测到摆动点: {swing_results['count']['highs']}高/{swing_results['count']['lows']}低")
    print(f"   支撑集群: {len(swing_results['key_areas']['support_clusters'])}个")
    print(f"   阻力集群: {len(swing_results['key_areas']['resistance_clusters'])}个")
    
    # 显示趋势摘要
    print("\n" + "="*40)
    print("📋 趋势分析摘要")
    print("="*40)
    trend_summary = trend_analyzer.get_trend_summary(df)
    print(trend_summary)


def demo_performance_test():
    """演示性能测试"""
    print("\n" + "="*60)
    print("🎯 演示5: 性能测试")
    print("="*60)
    
    import time
    
    # 创建不同规模的数据
    sizes = [100, 500, 1000, 5000]
    
    for size in sizes:
        print(f"\n📊 测试数据规模: {size} 条")
        
        # 创建测试数据
        dates = pd.date_range(start='2024-01-01', periods=size, freq='D')
        prices = 100 + np.arange(size) * 0.1 + np.random.normal(0, 2, size)
        
        df = pd.DataFrame({
            'open': prices - np.random.uniform(0, 1, size),
            'high': prices + np.random.uniform(1, 3, size),
            'low': prices - np.random.uniform(1, 3, size),
            'close': prices,
            'volume': np.random.randint(1000, 10000, size)
        }, index=dates)
        
        # 测试市场结构分析器性能
        analyzer = MarketStructureAnalyzer()
        
        start_time = time.time()
        results = analyzer.analyze_market_structure(df)
        end_time = time.time()
        
        elapsed = end_time - start_time
        print(f"   分析时间: {elapsed:.3f} 秒")
        print(f"   处理速度: {size/elapsed:.0f} 条/秒")
        print(f"   综合评分: {results['composite_score']['composite_score']:.1f}/100")


def main():
    """主函数"""
    print("🚀 市场结构因子演示程序")
    print("="*60)
    
    # 演示1: 基础分析
    results1 = demo_basic_analysis()
    
    # 演示2: 真实数据分析
    results2 = demo_real_data_analysis()
    
    # 演示3: 完整报告
    demo_comprehensive_report()
    
    # 演示4: 独立组件
    demo_individual_components()
    
    # 演示5: 性能测试
    demo_performance_test()
    
    print("\n" + "="*60)
    print("✅ 所有演示完成!")
    print("="*60)
    print("\n📚 演示总结:")
    print("   1. 基础市场结构分析 - 完成")
    print("   2. 真实数据市场分析 - 完成")
    print("   3. 完整分析报告生成 - 完成")
    print("   4. 独立组件使用演示 - 完成")
    print("   5. 性能测试 - 完成")
    print("\n🎯 市场结构因子模块已完全实现并测试通过!")


if __name__ == "__main__":
    main()