"""
市场结构分析器 - 整合所有市场结构因子
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import warnings
warnings.filterwarnings('ignore')

from .trend_analyzer import TrendAnalyzer
from .structure_break import StructureBreakAnalyzer
from .swing_points import SwingPointDetector


class MarketStructureAnalyzer:
    """
    市场结构分析器 - 整合所有市场结构分析功能
    
    功能整合:
    1. 趋势分析 (TrendAnalyzer)
    2. 结构突破分析 (StructureBreakAnalyzer)
    3. 摆动点分析 (SwingPointDetector)
    4. 综合市场结构评分
    """
    
    def __init__(self, 
                 trend_window: int = 20,
                 structure_lookback: int = 50,
                 swing_threshold: float = 0.03):
        """
        初始化市场结构分析器
        
        Args:
            trend_window: 趋势分析窗口
            structure_lookback: 结构分析回看周期
            swing_threshold: 摆动点检测阈值
        """
        self.trend_analyzer = TrendAnalyzer(window=trend_window)
        self.structure_analyzer = StructureBreakAnalyzer(lookback_period=structure_lookback)
        self.swing_detector = SwingPointDetector(threshold=swing_threshold)
        
    def analyze_market_structure(self, df: pd.DataFrame) -> Dict:
        """
        综合分析市场结构
        
        Args:
            df: 包含OHLCV数据的DataFrame
            
        Returns:
            Dict: 完整的市场结构分析结果
        """
        if not {'high', 'low', 'close'}.issubset(df.columns):
            raise ValueError("DataFrame必须包含'high', 'low', 'close'列")
            
        results = {
            'timestamp': pd.Timestamp.now(),
            'symbol': df.index.name if df.index.name else 'unknown',
            'data_points': len(df)
        }
        
        # 1. 趋势分析
        print("🔍 进行趋势分析...")
        results['trend_analysis'] = self.trend_analyzer.analyze_trend(df)
        
        # 2. 摆动点检测
        print("📍 检测摆动点...")
        results['swing_points'] = self.swing_detector.detect_swing_points(df, use_advanced=True)
        
        # 3. 结构突破分析
        print("🚨 分析结构突破...")
        results['structure_breaks'] = self.structure_analyzer.analyze_structure_breaks(
            df, results['swing_points']
        )
        
        # 4. 综合评分
        print("📊 计算综合评分...")
        results['composite_score'] = self._calculate_composite_score(results)
        
        # 5. 交易背景评估
        print("🎯 评估交易背景...")
        results['trading_context'] = self._assess_trading_context(results)
        
        # 6. 生成交易建议
        print("💡 生成交易建议...")
        results['trading_suggestions'] = self._generate_trading_suggestions(results)
        
        print("✅ 市场结构分析完成!")
        return results
    
    def _calculate_composite_score(self, analysis_results: Dict) -> Dict:
        """
        计算综合市场结构评分
        """
        scores = {}
        
        # 趋势评分 (0-100)
        trend_strength = analysis_results['trend_analysis']['trend_strength']
        trend_direction = analysis_results['trend_analysis']['trend_direction']
        
        if trend_direction == 'uptrend':
            scores['trend_score'] = trend_strength
        elif trend_direction == 'downtrend':
            scores['trend_score'] = trend_strength
        else:  # sideways
            scores['trend_score'] = max(0, 50 - trend_strength)  # 横盘时趋势强度低是好的
        
        # 结构评分 (0-100)
        structure_score = analysis_results['structure_breaks']['market_structure_score']
        scores['structure_score'] = structure_score
        
        # 摆动点质量评分
        swing_stats = analysis_results['swing_points']['stats']
        if 'overall' in swing_stats:
            swing_density = swing_stats['overall']['swing_density']
            # 适中的摆动点密度最好 (0.1-0.3)
            if 0.1 <= swing_density <= 0.3:
                scores['swing_quality'] = 80
            elif swing_density < 0.05:
                scores['swing_quality'] = 40  # 太稀疏
            elif swing_density > 0.5:
                scores['swing_quality'] = 30  # 太密集
            else:
                scores['swing_quality'] = 60
        else:
            scores['swing_quality'] = 50
        
        # 结构健康度评分
        health = analysis_results['structure_breaks']['structure_health']['overall']
        health_scores = {
            'healthy': 80,
            'moderate': 60,
            'weak': 30,
            'neutral': 50
        }
        scores['health_score'] = health_scores.get(health, 50)
        
        # 综合评分 (加权平均)
        weights = {
            'trend_score': 0.3,
            'structure_score': 0.3,
            'swing_quality': 0.2,
            'health_score': 0.2
        }
        
        total_score = 0
        total_weight = 0
        
        for score_name, weight in weights.items():
            if score_name in scores:
                total_score += scores[score_name] * weight
                total_weight += weight
        
        scores['composite_score'] = total_score / total_weight if total_weight > 0 else 50
        
        # 评分等级
        composite = scores['composite_score']
        if composite >= 80:
            scores['grade'] = 'A'
            scores['grade_description'] = '优秀 - 清晰的市场结构'
        elif composite >= 70:
            scores['grade'] = 'B'
            scores['grade_description'] = '良好 - 明确的市场结构'
        elif composite >= 60:
            scores['grade'] = 'C'
            scores['grade_description'] = '一般 - 可交易的市场结构'
        elif composite >= 50:
            scores['grade'] = 'D'
            scores['grade_description'] = '较差 - 模糊的市场结构'
        else:
            scores['grade'] = 'F'
            scores['grade_description'] = '糟糕 - 混乱的市场结构'
        
        return scores
    
    def _assess_trading_context(self, analysis_results: Dict) -> Dict:
        """
        评估交易背景
        """
        context = {
            'overall_context': 'neutral',
            'trend_context': 'neutral',
            'structure_context': 'neutral',
            'risk_context': 'medium',
            'opportunity_level': 'medium'
        }
        
        # 趋势背景
        trend_direction = analysis_results['trend_analysis']['trend_direction']
        trend_strength = analysis_results['trend_analysis']['trend_strength']
        
        if trend_direction == 'uptrend' and trend_strength > 60:
            context['trend_context'] = 'strong_bullish'
        elif trend_direction == 'uptrend' and trend_strength > 30:
            context['trend_context'] = 'moderate_bullish'
        elif trend_direction == 'downtrend' and trend_strength > 60:
            context['trend_context'] = 'strong_bearish'
        elif trend_direction == 'downtrend' and trend_strength > 30:
            context['trend_context'] = 'moderate_bearish'
        else:
            context['trend_context'] = 'ranging'
        
        # 结构背景
        structure_score = analysis_results['structure_breaks']['market_structure_score']
        bos_signals = analysis_results['structure_breaks']['bos_signals']
        choch_signals = analysis_results['structure_breaks']['choch_signals']
        
        if structure_score >= 70 and not choch_signals:
            context['structure_context'] = 'stable'
        elif structure_score >= 70 and bos_signals:
            context['structure_context'] = 'breaking_out'
        elif structure_score < 50 or choch_signals:
            context['structure_context'] = 'changing'
        else:
            context['structure_context'] = 'consolidating'
        
        # 风险背景
        recent_breaks = analysis_results['structure_breaks']['recent_breaks']
        volatility = analysis_results['trend_analysis'].get('volatility', 0)
        
        if recent_breaks or volatility > 5:
            context['risk_context'] = 'high'
        elif volatility < 1:
            context['risk_context'] = 'low'
        else:
            context['risk_context'] = 'medium'
        
        # 机会水平
        composite_score = analysis_results['composite_score']['composite_score']
        if composite_score >= 70:
            context['opportunity_level'] = 'high'
        elif composite_score >= 60:
            context['opportunity_level'] = 'medium'
        else:
            context['opportunity_level'] = 'low'
        
        # 整体背景
        if context['trend_context'] in ['strong_bullish', 'strong_bearish'] and context['structure_context'] == 'stable':
            context['overall_context'] = 'favorable'
        elif context['structure_context'] == 'breaking_out':
            context['overall_context'] = 'opportunistic'
        elif context['risk_context'] == 'high':
            context['overall_context'] = 'risky'
        else:
            context['overall_context'] = 'neutral'
        
        return context
    
    def _generate_trading_suggestions(self, analysis_results: Dict) -> List[Dict]:
        """
        生成交易建议
        """
        suggestions = []
        
        trend_direction = analysis_results['trend_analysis']['trend_direction']
        trend_strength = analysis_results['trend_analysis']['trend_strength']
        structure_score = analysis_results['structure_breaks']['market_structure_score']
        bos_signals = analysis_results['structure_breaks']['bos_signals']
        choch_signals = analysis_results['structure_breaks']['choch_signals']
        swing_points = analysis_results['swing_points']
        
        # 建议1: 趋势跟踪
        if trend_strength > 60 and structure_score > 70:
            if trend_direction == 'uptrend':
                suggestions.append({
                    'type': 'trend_following',
                    'direction': 'long',
                    'confidence': 'high',
                    'reason': f'强势上升趋势 (强度: {trend_strength:.1f})，结构稳定',
                    'action': '考虑逢低做多',
                    'risk': '中等'
                })
            elif trend_direction == 'downtrend':
                suggestions.append({
                    'type': 'trend_following',
                    'direction': 'short',
                    'confidence': 'high',
                    'reason': f'强势下降趋势 (强度: {trend_strength:.1f})，结构稳定',
                    'action': '考虑逢高做空',
                    'risk': '中等'
                })
        
        # 建议2: 突破交易
        if bos_signals:
            recent_bos = bos_signals[-1] if bos_signals else None
            if recent_bos and recent_bos.get('confirmed', False):
                if recent_bos['type'] == 'bos_bullish':
                    suggestions.append({
                        'type': 'breakout',
                        'direction': 'long',
                        'confidence': 'medium',
                        'reason': f'确认突破前高 {recent_bos["break_level"]:.2f}',
                        'action': '考虑突破后做多',
                        'risk': '较高',
                        'entry': f'突破 {recent_bos["break_level"]:.2f} 后',
                        'stop_loss': f'低于 {recent_bos["break_level"] * 0.99:.2f}'
                    })
                elif recent_bos['type'] == 'bos_bearish':
                    suggestions.append({
                        'type': 'breakout',
                        'direction': 'short',
                        'confidence': 'medium',
                        'reason': f'确认突破前低 {recent_bos["break_level"]:.2f}',
                        'action': '考虑突破后做空',
                        'risk': '较高',
                        'entry': f'突破 {recent_bos["break_level"]:.2f} 后',
                        'stop_loss': f'高于 {recent_bos["break_level"] * 1.01:.2f}'
                    })
        
        # 建议3: 反转交易 (CHOCH信号)
        if choch_signals:
            for choch in choch_signals:
                if choch['type'] == 'choch_bullish':
                    suggestions.append({
                        'type': 'reversal',
                        'direction': 'long',
                        'confidence': 'low',
                        'reason': f'下降趋势中出现更高的低点 (CHOCH信号)',
                        'action': '谨慎考虑反转做多',
                        'risk': '高',
                        'note': '需要进一步确认'
                    })
                elif choch['type'] == 'choch_bearish':
                    suggestions.append({
                        'type': 'reversal',
                        'direction': 'short',
                        'confidence': 'low',
                        'reason': f'上升趋势中出现更低的高点 (CHOCH信号)',
                        'action': '谨慎考虑反转做空',
                        'risk': '高',
                        'note': '需要进一步确认'
                    })
        
        # 建议4: 区间交易
        key_areas = swing_points['key_areas']
        if key_areas['consolidation_zones']:
            consolidation = key_areas['consolidation_zones'][0]  # 取第一个震荡区间
            suggestions.append({
                'type': 'range_trading',
                'direction': 'both',
                'confidence': 'medium',
                'reason': f'识别到震荡区间 {consolidation["support_level"]:.2f}-{consolidation["resistance_level"]:.2f}',
                'action': '考虑区间上下沿交易',
                'risk': '中等',
                'buy_zone': f'接近 {consolidation["support_level"]:.2f}',
                'sell_zone': f'接近 {consolidation["resistance_level"]:.2f}'
            })
        
        # 建议5: 观望建议
        if trend_strength < 30 and structure_score < 50:
            suggestions.append({
                'type': 'wait',
                'direction': 'none',
                'confidence': 'high',
                'reason': '趋势不明确，市场结构混乱',
                'action': '建议观望，等待更清晰信号',
                'risk': '低'
            })
        
        return suggestions
    
    def get_comprehensive_report(self, df: pd.DataFrame) -> str:
        """
        获取完整的市场结构分析报告
        """
        analysis = self.analyze_market_structure(df)
        
        report = f"""
        📊 市场结构分析报告
        {'='*60}
        分析时间: {analysis['timestamp']}
        标的: {analysis['symbol']}
        数据点数: {analysis['data_points']}
        
        🎯 综合评分: {analysis['composite_score']['composite_score']:.1f}/100
        评级: {analysis['composite_score']['grade']} - {analysis['composite_score']['grade_description']}
        
        📈 趋势分析
        {'─'*40}
        方向: {analysis['trend_analysis']['trend_direction'].upper()}
        强度: {analysis['trend_analysis']['trend_strength']:.1f}/100
        分类: {analysis['trend_analysis']['trend_class'].replace('_', ' ').upper()}
        
        🏗️ 结构分析
        {'─'*40}
        结构评分: {analysis['structure_breaks']['market_structure_score']}/100
        健康度: {analysis['structure_breaks']['structure_health']['overall'].upper()}
        BOS信号: {len(analysis['structure_breaks']['bos_signals'])} 个
        CHOCH信号: {len(analysis['structure_breaks']['choch_signals'])} 个
        
        📍 摆动点分析
        {'─'*40}
        高点: {analysis['swing_points']['count']['highs']} 个
        低点: {analysis['swing_points']['count']['lows']} 个
        支撑集群: {len(analysis['swing_points']['key_areas']['support_clusters'])} 个
        阻力集群: {len(analysis['swing_points']['key_areas']['resistance_clusters'])} 个
        
        🎭 交易背景
        {'─'*40}
        整体背景: {analysis['trading_context']['overall_context'].upper()}
        趋势背景: {analysis['trading_context']['trend_context'].replace('_', ' ').upper()}
        结构背景: {analysis['trading_context']['structure_context'].upper()}
        风险水平: {analysis['trading_context']['risk_context'].upper()}
        机会等级: {analysis['trading_context']['opportunity_level'].upper()}
        
        💡 交易建议
        {'─'*40}
        """
        
        if analysis['trading_suggestions']:
            for i, suggestion in enumerate(analysis['trading_suggestions'], 1):
                confidence_emoji = '🟢' if suggestion['confidence'] == 'high' else '🟡' if suggestion['confidence'] == 'medium' else '🔴'
                report += f"\n{i}. {confidence_emoji} {suggestion['type'].replace('_', ' ').upper()}"
                report += f"\n   方向: {suggestion['direction'].upper()}"
                report += f"\n   理由: {suggestion['reason']}"
                report += f"\n   操作: {suggestion['action']}"
                report += f"\n   风险: {suggestion['risk']}"
                
                if 'entry' in suggestion:
                    report += f"\n   入场: {suggestion['entry']}"
                if 'stop_loss' in suggestion:
                    report += f"\n   止损: {suggestion['stop_loss']}"
                if 'note' in suggestion:
                    report += f"\n   备注: {suggestion['note']}"
                
                report += "\n"
        
        report += "\n" + "="*60
        report += "\n📝 报告结束"
        
        return report