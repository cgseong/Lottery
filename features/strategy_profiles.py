from __future__ import annotations

from typing import Dict, List, Set

from analyzers.statistical_analyzer import StatisticalAnalyzer

STRATEGY_PROFILES: Dict[str, Dict] = {
    "보수형": {"sum_min": 100, "sum_max": 165, "max_consecutive": 2},
    "균형형": {"sum_min": 90, "sum_max": 180, "max_consecutive": 3},
    "고변동형": {"sum_min": 70, "sum_max": 210, "max_consecutive": 5},
}


class StrategyProfileEngine:
    def __init__(self, analyzer: StatisticalAnalyzer):
        self.analyzer = analyzer

    def generate(self, profile_name: str, exclude_numbers: Set[int], count: int = 5) -> List[Dict]:
        profile = STRATEGY_PROFILES.get(profile_name, STRATEGY_PROFILES["균형형"])
        results: List[Dict] = []
        attempts = 0
        max_attempts = count * 300

        while len(results) < count and attempts < max_attempts:
            attempts += 1
            recs = self.analyzer.generate_recommendations(
                exclude_numbers=set(exclude_numbers),
                num_recommendations=1,
            )
            if not recs:
                continue
            rec = recs[0]
            rec_sum = sum(rec["numbers"])
            if not (profile["sum_min"] <= rec_sum <= profile["sum_max"]):
                continue
            if int(rec.get("consecutive_count", 0)) > int(profile["max_consecutive"]):
                continue
            if any(tuple(r["numbers"]) == tuple(rec["numbers"]) for r in results):
                continue
            rec["profile"] = profile_name
            results.append(rec)

        return results
