from __future__ import annotations

from typing import Dict, List

from analyzers.statistical_analyzer import StatisticalAnalyzer


class RecommendationExplainer:
    def __init__(self, analyzer: StatisticalAnalyzer):
        self.analyzer = analyzer

    def build(self, numbers: List[int]) -> Dict:
        sorted_nums = sorted(numbers)
        sum_stats = self.analyzer.analyze_sum_range() or {}
        odd_even = self.analyzer.analyze_odd_even() or {}
        sections = self.analyzer.analyze_section_distribution() or {}
        consecutive = self.analyzer.check_consecutive_numbers(sorted_nums)

        odd_count = sum(1 for n in sorted_nums if n % 2 == 1)
        section_counts = {
            "1-15": sum(1 for n in sorted_nums if 1 <= n <= 15),
            "16-30": sum(1 for n in sorted_nums if 16 <= n <= 30),
            "31-45": sum(1 for n in sorted_nums if 31 <= n <= 45),
        }

        return {
            "numbers": sorted_nums,
            "sum": sum(sorted_nums),
            "sum_vs_avg": (sum(sorted_nums) - float(sum_stats.get("avg_sum", 0.0))),
            "odd_even": {
                "odd": odd_count,
                "even": 6 - odd_count,
                "avg_odd": float(odd_even.get("avg_odd", 0.0)),
                "avg_even": float(odd_even.get("avg_even", 0.0)),
            },
            "sections": {
                "counts": section_counts,
                "historical_pct": sections.get("percentages", {}),
            },
            "consecutive_pairs": consecutive,
            "score": self.analyzer.calculate_score(sorted_nums),
        }
