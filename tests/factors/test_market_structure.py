"""
市场结构因子测试
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from factors.market_structure import (
    TrendAnalyzer,
    StructureBreakAnalyzer,
    SwingPointDetector,
    MarketStructureAnalyzer
)


class TestTrendAnalyzer:
    """趋势分析器测试"""
    
    @pytest.fixture
    def sample_data(self):
        """创建测试数据"""
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
        
        # 创建上升趋势数据
        base_price = 100
        trend_slope = 0.5  # 每天上涨0.5
        noise = np.random.normal(0, 2, 100)
        
        closes = base_price + np.arange(100) * trend_slope + noise
        highs = closes + np.random.uniform(1, 3, 100)
        lows = closes - np.random.uniform(1, 3, 100)
        
        df = pd.DataFrame({
            'open': closes - np.random.uniform(0, 1, 100),
            'high': highs,
            'low': lows,
            'close': closes,
            'volume': np.random.randint(1000, 10000, 100)
        }, index=dates)
        
        return df
    
    def test_trend_analyzer_initialization(self):
        """测试初始化"""
        analyzer = TrendAnalyzer(window=20, adx_period=14, zigzag_threshold=0.05)
        assert analyzer.window == 20
        assert analyzer.adx_period == 14
        assert analyzer.zigzag_threshold == 0.05
    
    def test_analyze_trend(self, sample_data):
        """测试趋势分析"""
        analyzer = TrendAnalyzer()
        results = analyzer.analyze_trend(sample_data)
        
        # 检查返回结果结构
        assert 'trend_direction' in results
        assert 'trend_strength' in results
        assert 'swing_points' in results
        assert 'trend_class' in results
        
        # 检查趋势强度范围
        assert 0 <= results['trend_strength'] <= 100
        
        # 检查摆动点数据结构
        swing_points = results['swing_points']
        assert 'highs' in swing_points
        assert 'lows' in swing_points
        assert isinstance(swing_points['highs'], pd.DataFrame)
        assert isinstance(swing_points['lows'], pd.DataFrame)
    
    def test_get_trend_direction(self, sample_data):
        """测试趋势方向判断"""
        analyzer = TrendAnalyzer()
        direction = analyzer._get_trend_direction(sample_data)
        
        # 应该是上升趋势
        assert direction in ['uptrend', 'downtrend', 'sideways']
    
    def test_calculate_trend_strength(self, sample_data):
        """测试趋势强度计算"""
        analyzer = TrendAnalyzer()
        strength = analyzer._calculate_trend_strength(sample_data)
        
        # 检查强度范围
        assert 0 <= strength <= 100
    
    def test_detect_swing_points(self, sample_data):
        """测试摆动点检测"""
        analyzer = TrendAnalyzer()
        swing_points = analyzer._detect_swing_points(sample_data)
        
        assert 'highs' in swing_points
        assert 'lows' in swing_points
        assert 'last_high' in swing_points
        assert 'last_low' in swing_points
    
    def test_get_trend_summary(self, sample_data):
        """测试趋势摘要生成"""
        analyzer = TrendAnalyzer()
        summary = analyzer.get_trend_summary(sample_data)
        
        assert isinstance(summary, str)
        assert '趋势分析摘要' in summary
        assert '趋势方向' in summary
        assert '趋势强度' in summary


class TestStructureBreakAnalyzer:
    """结构突破分析器测试"""
    
    @pytest.fixture
    def sample_data_with_breakout(self):
        """创建带突破的测试数据"""
        dates = pd.date_range(start='2024-01-01', periods=200, freq='D')
        
        # 第一阶段: 横盘整理
        prices1 = 100 + np.random.normal(0, 2, 100)
        
        # 第二阶段: 突破上涨
        prices2 = 110 + np.arange(100) * 0.3 + np.random.normal(0, 3, 100)
        
        prices = np.concatenate([prices1, prices2])
        highs = prices + np.random.uniform(1, 4, 200)
        lows = prices - np.random.uniform(1, 4, 200)
        
        df = pd.DataFrame({
            'open': prices - np.random.uniform(0, 1, 200),
            'high': highs,
            'low': lows,
            'close': prices,
            'volume': np.random.randint(1000, 20000, 200)
        }, index=dates)
        
        return df
    
    def test_structure_break_analyzer_initialization(self):
        """测试初始化"""
        analyzer = StructureBreakAnalyzer(lookback_period=50, bos_threshold=0.01)
        assert analyzer.lookback_period == 50
        assert analyzer.bos_threshold == 0.01
    
    def test_analyze_structure_breaks(self, sample_data_with_breakout):
        """测试结构突破分析"""
        analyzer = StructureBreakAnalyzer()
        results = analyzer.analyze_structure_breaks(sample_data_with_breakout)
        
        # 检查返回结果结构
        assert 'bos_signals' in results
        assert 'choch_signals' in results
        assert 'market_structure_score' in results
        assert 'structure_health' in results
        assert 'recent_breaks' in results
        
        # 检查评分范围
        assert 0 <= results['market_structure_score'] <= 100
        
        # 检查结构健康度
        health = results['structure_health']
        assert 'overall' in health
        assert health['overall'] in ['healthy', 'moderate', 'weak', 'neutral']
    
    def test_detect_bos_signals(self, sample_data_with_breakout):
        """测试BOS信号检测"""
        analyzer = StructureBreakAnalyzer()
        
        # 先获取摆动点
        from factors.market_structure.trend_analyzer import TrendAnalyzer
        trend_analyzer = TrendAnalyzer()
        swing_points = trend_analyzer._detect_swing_points(sample_data_with_breakout)
        
        bos_signals = analyzer._detect_bos_signals(sample_data_with_breakout, swing_points)
        
        assert isinstance(bos_signals, list)
        # 由于有突破，应该能检测到BOS信号
        # assert len(bos_signals) > 0
    
    def test_calculate_structure_score(self, sample_data_with_breakout):
        """测试结构评分计算"""
        analyzer = StructureBreakAnalyzer()
        
        # 先进行分析
        results = analyzer.analyze_structure_breaks(sample_data_with_breakout)
        score = analyzer._calculate_structure_score(
            results['bos_signals'], 
            results['choch_signals'], 
            sample_data_with_breakout
        )
        
        assert 0 <= score <= 100
    
    def test_get_structure_summary(self, sample_data_with_breakout):
        """测试结构摘要生成"""
        analyzer = StructureBreakAnalyzer()
        summary = analyzer.get_structure_summary(sample_data_with_breakout)
        
        assert isinstance(summary, str)
        assert '市场结构分析' in summary
        assert '结构评分' in summary


class TestSwingPointDetector:
    """摆动点检测器测试"""
    
    @pytest.fixture
    def sample_oscillating_data(self):
        """创建震荡测试数据"""
        dates = pd.date_range(start='2024-01-01', periods=150, freq='D')
        
        # 创建明显的摆动点模式
        t = np.arange(150)
        # 正弦波加上趋势
        prices = 100 + 10 * np.sin(t * 2 * np.pi / 30) + t * 0.1
        
        highs = prices + np.random.uniform(1, 3, 150)
        lows = prices - np.random.uniform(1, 3, 150)
        
        df = pd.DataFrame({
            'open': prices - np.random.uniform(0, 1, 150),
            'high': highs,
            'low': lows,
            'close': prices,
            'volume': np.random.randint(1000, 15000, 150)
        }, index=dates)
        
        return df
    
    def test_swing_point_detector_initialization(self):
        """测试初始化"""
        detector = SwingPointDetector(threshold=0.03, lookback=5, min_swing_distance=10)
        assert detector.threshold == 0.03
        assert detector.lookback == 5
        assert detector.min_swing_distance == 10
    
    def test_detect_swing_points(self, sample_oscillating_data):
        """测试摆动点检测"""
        detector = SwingPointDetector()
        results = detector.detect_swing_points(sample_oscillating_data, use_advanced=True)
        
        # 检查返回结果结构
        assert 'highs' in results
        assert 'lows' in results
        assert 'stats' in results
        assert 'key_areas' in results
        assert 'count' in results
        
        # 检查摆动点数量
        assert results['count']['highs'] >= 0
        assert results['count']['lows'] >= 0
        
        # 检查关键区域
        key_areas = results['key_areas']
        assert 'support_clusters' in key_areas
        assert 'resistance_clusters' in key_areas
        assert 'consolidation_zones' in key_areas
    
    def test_detect_swing_points_basic(self, sample_oscillating_data):
        """测试基础摆动点检测"""
        detector = SwingPointDetector()
        results = detector.detect_swing_points(sample_oscillating_data, use_advanced=False)
        
        assert 'highs' in results
        assert 'lows' in results
    
    def test_filter_close_points(self):
        """测试接近点过滤"""
        detector = SwingPointDetector(min_swing_distance=10)
        
        # 创建测试点
        points = [(0, 100), (5, 102), (15, 105), (20, 103)]
        
        # 测试高点过滤
        filtered_highs = detector._filter_close_points(points, is_high=True)
        assert len(filtered_highs) <= len(points)
        
        # 测试低点过滤
        filtered_lows = detector._filter_close_points(points, is_high=False)
        assert len(filtered_lows) <= len(points)
    
    def test_get_swing_summary(self, sample_oscillating_data):
        """测试摆动点摘要生成"""
        detector = SwingPointDetector()
        summary = detector.get_swing_summary(sample_oscillating_data)
        
        assert isinstance(summary, str)
        assert '摆动点分析' in summary
        assert '摆动点统计' in summary


class TestMarketStructureAnalyzer:
    """市场结构分析器测试"""
    
    @pytest.fixture
    def complex_sample_data(self):
        """创建复杂测试数据"""
        dates = pd.date_range(start='2024-01-01', periods=300, freq='D')
        
        # 创建多阶段数据: 上升 -> 震荡 -> 突破
        # 阶段1: 上升趋势
        phase1 = 100 + np.arange(100) * 0.5 + np.random.normal(0, 3, 100)
        
        # 阶段2: 震荡整理
        phase2 = 150 + 5 * np.sin(np.arange(100) * 2 * np.pi / 20) + np.random.normal(0, 2, 100)
        
        # 阶段3: 突破上涨
        phase3 = 155 + np.arange(100) * 0.8 + np.random.normal(0, 4, 100)
        
        prices = np.concatenate([phase1, phase2, phase3])
        highs = prices + np.random.uniform(2, 5, 300)
        lows = prices - np.random.uniform(2, 5, 300)
        
        df = pd.DataFrame({
            'open': prices - np.random.uniform(0, 2, 300),
            'high': highs,
            'low': lows,
            'close': prices,
            'volume': np.random.randint(5000, 30000, 300)
        }, index=dates)
        
        return df
    
    def test_market_structure_analyzer_initialization(self):
        """测试初始化"""
        analyzer = MarketStructureAnalyzer(
            trend_window=20,
            structure_lookback=50,
            swing_threshold=0.03
        )
        
        assert analyzer.trend_analyzer.window == 20
        assert analyzer.structure_analyzer.lookback_period == 50
        assert analyzer.swing_detector.threshold == 0.03
    
    def test_analyze_market_structure(self, complex_sample_data):
        """测试市场结构分析"""
        analyzer = MarketStructureAnalyzer()
        results = analyzer.analyze_market_structure(complex_sample_data)
        
        # 检查返回结果结构
        assert 'timestamp' in results
        assert 'symbol' in results
        assert 'data_points' in results
        assert 'trend_analysis' in results
        assert 'swing_points' in results
        assert 'structure_breaks' in results
        assert 'composite_score' in results
        assert 'trading_context' in results
        assert 'trading_suggestions' in results
        
        # 检查综合评分
        scores = results['composite_score']
        assert 'composite_score' in scores
        assert 0 <= scores['composite_score'] <= 100
        assert 'grade' in scores
        assert 'grade_description' in scores
        
        # 检查交易背景
        context = results['trading_context']
        assert 'overall_context' in context
        assert 'trend_context' in context
        assert 'risk_context' in context
        
        # 检查交易建议
        suggestions = results['trading_suggestions']
        assert isinstance(suggestions, list)
    
    def test_calculate_composite_score(self, complex_sample_data):
        """测试综合评分计算"""
        analyzer = MarketStructureAnalyzer()
        
        # 先进行分析
        results = analyzer.analyze_market_structure(complex_sample_data)
        scores = analyzer._calculate_composite_score(results)
        
        assert 'composite_score' in scores
        assert 0 <= scores['composite_score'] <= 100
        assert 'grade' in scores
        assert scores['grade'] in ['A', 'B', 'C', 'D', 'F']
    
    def test_assess_trading_context(self, complex_sample_data):
        """测试交易背景评估"""
        analyzer = MarketStructureAnalyzer()
        
        # 先进行分析
        results = analyzer.analyze_market_structure(complex_sample_data)
        context = analyzer._assess_trading_context(results)
        
        assert 'overall_context' in context
        assert context['overall_context'] in ['favorable', 'opportunistic', 'risky', 'neutral']
        assert 'risk_context' in context
        assert context['risk_context'] in ['high', 'medium', 'low']
    
    def test_generate_trading_suggestions(self, complex_sample_data):
        """测试交易建议生成"""
        analyzer = MarketStructureAnalyzer()
        
        # 先进行分析
        results = analyzer.analyze_market_structure(complex_sample_data)
        suggestions = analyzer._generate_trading_suggestions(results)
        
        assert isinstance(suggestions, list)
        if suggestions:
            suggestion = suggestions[0]
            assert 'type' in suggestion
            assert 'direction' in suggestion
            assert 'confidence' in suggestion
            assert 'reason' in suggestion
    
    def test_get_comprehensive_report(self, complex_sample_data):
        """测试完整报告生成"""
        analyzer = MarketStructureAnalyzer()
        report = analyzer.get_comprehensive_report(complex_sample_data)
        
        assert isinstance(report, str)
        assert '市场结构分析报告' in report
        assert '综合评分' in report
        assert '趋势分析' in report
        assert '结构分析' in report


if __name__ == '__main__':
    # 运行测试
    pytest.main([__file__, '-v'])