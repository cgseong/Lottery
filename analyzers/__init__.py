"""
로또 분석기 모듈

핵심 분석기는 항상 로드되고, 시각화/선택적 모듈은
matplotlib·numpy 버전 충돌 시에도 앱이 정상 동작하도록
안전하게 import합니다.
"""

# ── 핵심 분석기 (matplotlib 의존 없음) ──
from .lotto_data_collector import LottoDataCollector
from .statistical_analyzer import StatisticalAnalyzer
from .pattern_matching_analyzer import PatternMatchingAnalyzer
from .ensemble_analyzer import EnsembleAnalyzer
from .mersenne_twister_analyzer import MersenneTwisterAnalyzer
from .trend_analyzer import TrendAnalyzer
from .lotto_pattern_grouping import LottoPatternGrouping
from .comprehensive_analyzer import ComprehensiveAnalyzer
from .advanced_statistics import (
    MarkovChainAnalyzer, ClusterPatternAnalyzer, DynamicHotColdWeighter
)
from .advanced_filters import (
    HistoricalPatternFilter, SumDistributionFilter,
    AssociationRuleFilter, EntropyFilter, AdvancedFilterPipeline
)
from .integrated_recommender import IntegratedRecommender

# ── 선택적 모듈 (matplotlib 또는 torch 의존 — 실패해도 앱 동작에 지장 없음) ──
try:
    from .line_pattern_analyzer import LinePatternAnalyzer
except (ImportError, AttributeError, Exception):
    LinePatternAnalyzer = None

try:
    from .deep_learning_predictor import DeepLearningPredictor
except (ImportError, AttributeError, Exception):
    DeepLearningPredictor = None

__all__ = [
    'LottoDataCollector',
    'StatisticalAnalyzer',
    'PatternMatchingAnalyzer',
    'EnsembleAnalyzer',
    'MersenneTwisterAnalyzer',
    'TrendAnalyzer',
    'LinePatternAnalyzer',
    'LottoPatternGrouping',
    'ComprehensiveAnalyzer',
    'MarkovChainAnalyzer',
    'ClusterPatternAnalyzer',
    'DynamicHotColdWeighter',
    'DeepLearningPredictor',
    'HistoricalPatternFilter',
    'SumDistributionFilter',
    'AssociationRuleFilter',
    'EntropyFilter',
    'AdvancedFilterPipeline',
    'IntegratedRecommender',
]
