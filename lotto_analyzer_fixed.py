#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Compatibility wrapper for legacy imports.
"""

from __future__ import annotations

import csv
import os
from typing import Dict, List, Optional, Set

from analyzers.lotto_data_collector import LottoDataCollector as _BaseLottoDataCollector
from analyzers.lotto_pattern_grouping import LottoPatternGrouping
from analyzers.statistical_analyzer import StatisticalAnalyzer
from ai_pattern_learner import AIPatternLearner
from utils.constants import (
    BONUS_COLUMN,
    LOTTO_NUMBER_COLUMNS,
    ROUND_COLUMN,
)

try:
    from analyzers.lotto_pattern_grouping import AI_PATTERN_AVAILABLE
except Exception:
    AI_PATTERN_AVAILABLE = False


class LottoDataCollector(_BaseLottoDataCollector):
    """Backwards-compatible collector with local CSV load helper."""

    def load_data(self, filename: str = "로또당첨번호.csv") -> List[Dict]:
        if not os.path.exists(filename):
            return []

        for enc in ("utf-8", "cp949", "euc-kr"):
            try:
                with open(filename, "r", encoding=enc) as f:
                    rows = list(csv.DictReader(f))
                if rows:
                    return rows
            except Exception:
                continue
        return []


class SumPatternAnalyzer:
    """Simple sum-range analyzer and recommender."""

    RANGES = {
        "낮음 (70-120)": (70, 120),
        "보통 (121-150)": (121, 150),
        "높음 (151-180)": (151, 180),
        "매우높음 (181-210)": (181, 210),
    }

    def __init__(self, historical_data: List[Dict], stat_analyzer: StatisticalAnalyzer):
        self.historical_data = historical_data
        self.stat_analyzer = stat_analyzer
        self.analysis = self.analyze_sum_patterns()

    def _extract_numbers(self, row: Dict) -> List[int]:
        nums: List[int] = []
        for i in range(1, 7):
            key = f"번호{i}"
            if key in row:
                try:
                    nums.append(int(row[key]))
                except (TypeError, ValueError):
                    pass
        return nums

    def analyze_sum_patterns(self) -> Dict:
        sums: List[int] = []
        for row in self.historical_data:
            nums = self._extract_numbers(row)
            if len(nums) == 6:
                sums.append(sum(nums))

        if not sums:
            return {"count": 0, "avg": 0.0, "min": 0, "max": 0, "ranges": {}}

        range_counts = {name: 0 for name in self.RANGES}
        for s in sums:
            for name, (lo, hi) in self.RANGES.items():
                if lo <= s <= hi:
                    range_counts[name] += 1
                    break

        return {
            "count": len(sums),
            "avg": sum(sums) / len(sums),
            "min": min(sums),
            "max": max(sums),
            "ranges": range_counts,
        }

    def print_sum_analysis_report(self) -> None:
        info = self.analysis
        print("\n[합계 패턴 분석]")
        print(f"- 데이터 수: {info['count']}")
        print(f"- 평균/최소/최대: {info['avg']:.1f} / {info['min']} / {info['max']}")
        if info["count"] > 0:
            for name, cnt in info["ranges"].items():
                ratio = (cnt / info["count"]) * 100
                print(f"- {name}: {cnt}회 ({ratio:.1f}%)")

    def generate_sum_based_recommendations(
        self,
        exclude_numbers: Optional[Set[int]] = None,
        num_recommendations: int = 5,
        target_sum_range: Optional[str] = None,
    ) -> List[Dict]:
        exclude_numbers = exclude_numbers or set()
        lo_hi = self.RANGES.get(target_sum_range) if target_sum_range else None

        results: List[Dict] = []
        attempts = 0
        max_attempts = max(500, num_recommendations * 300)
        while len(results) < num_recommendations and attempts < max_attempts:
            attempts += 1
            base = self.stat_analyzer.generate_recommendations(
                exclude_numbers=set(exclude_numbers),
                num_recommendations=1,
            )
            if not base:
                continue
            rec = base[0]
            s = sum(rec["numbers"])
            if lo_hi and not (lo_hi[0] <= s <= lo_hi[1]):
                continue
            if any(tuple(r["numbers"]) == tuple(rec["numbers"]) for r in results):
                continue
            rec["sum_range"] = target_sum_range or "자동"
            results.append(rec)
        return results


class LottoAnalyzer:
    """Compatibility facade used by existing tests/scripts."""

    def __init__(self, data_file: str = "로또당첨번호.csv"):
        self.data_file = data_file
        self.historical_data = self._load_data()
        self.stat_analyzer = StatisticalAnalyzer(self.historical_data) if self.historical_data else None
        self.sum_pattern_analyzer = (
            SumPatternAnalyzer(self.historical_data, self.stat_analyzer)
            if self.stat_analyzer else None
        )
        self.pattern_grouping = LottoPatternGrouping(self.historical_data) if self.historical_data else None
        self.ai_learner = AIPatternLearner(data_file=self.data_file)

        if self.pattern_grouping and AI_PATTERN_AVAILABLE:
            self._ensure_ai_models()

    def _load_data(self) -> List[Dict]:
        collector = LottoDataCollector()
        return collector.load_data(self.data_file)

    def _ensure_ai_models(self) -> None:
        model_file = "ai_pattern_models.pkl"
        try:
            if self.pattern_grouping.load_models(model_file):
                return
        except Exception:
            # Ignore legacy model load/encoding errors and fallback to retraining.
            pass
        try:
            groups = self.pattern_grouping.create_round_groups(5)
            if not groups:
                return
            features = self.pattern_grouping.create_pattern_features()
            if not features:
                return
            self.pattern_grouping.perform_clustering(5)
            self.pattern_grouping.train_ai_models()
            self.pattern_grouping.save_models(model_file)
        except Exception:
            # Keep compatibility behavior: initialization should not fail hard.
            return

    def generate_recommendations_ensemble(
        self,
        exclude_numbers: Optional[Set[int]] = None,
        num_recommendations: int = 5,
    ) -> List[Dict]:
        if not self.stat_analyzer:
            return []

        exclude_numbers = exclude_numbers or set()
        candidates: List[Dict] = []
        candidates.extend(
            self.stat_analyzer.generate_recommendations(
                exclude_numbers=set(exclude_numbers),
                num_recommendations=max(3, num_recommendations),
            )
        )

        if self.sum_pattern_analyzer:
            candidates.extend(
                self.sum_pattern_analyzer.generate_sum_based_recommendations(
                    exclude_numbers=set(exclude_numbers),
                    num_recommendations=max(3, num_recommendations),
                )
            )

        if self.pattern_grouping and self.pattern_grouping.ai_models:
            try:
                ai_recs = self.pattern_grouping.predict_high_probability_combinations(
                    exclude_numbers=set(exclude_numbers),
                    num_combinations=max(3, num_recommendations),
                )
                for rec in ai_recs:
                    candidates.append(
                        {
                            "numbers": sorted(rec["numbers"]),
                            "score": float(rec.get("probability", 0.0)),
                            "method": "AI 패턴",
                            "consecutive_count": int(rec.get("consecutive_count", 0)),
                            "sum": sum(rec["numbers"]),
                        }
                    )
            except Exception:
                pass

        # Deduplicate and rank
        dedup: Dict[tuple, Dict] = {}
        for rec in candidates:
            key = tuple(sorted(rec["numbers"]))
            if key not in dedup or rec.get("score", 0.0) > dedup[key].get("score", 0.0):
                dedup[key] = rec

        ranked = sorted(dedup.values(), key=lambda x: x.get("score", 0.0), reverse=True)
        return ranked[:num_recommendations]
