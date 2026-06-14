from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from analyzers.statistical_analyzer import StatisticalAnalyzer


@dataclass
class Backtester:
    historical_data: List[Dict]

    def run(self, window: int = 200, trials: int = 1) -> Dict:
        if len(self.historical_data) < window + 2:
            return {"ok": False, "reason": "not_enough_data"}

        hit_dist = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}
        total = 0

        for idx in range(window, len(self.historical_data) - 1):
            train_data = self.historical_data[:idx]
            next_row = self.historical_data[idx]
            actual = {int(next_row[f"num{i}"]) for i in range(1, 7)}
            analyzer = StatisticalAnalyzer(train_data)

            recs = analyzer.generate_recommendations(num_recommendations=max(1, trials))
            for rec in recs:
                picked = set(rec["numbers"])
                hit = len(picked & actual)
                hit_dist[hit] += 1
                total += 1

        return {
            "ok": True,
            "samples": total,
            "hit_distribution": hit_dist,
            "hit_rate_3_plus": (sum(v for k, v in hit_dist.items() if k >= 3) / total) if total else 0.0,
        }

    def tune_trials(self, window: int = 200, trial_candidates: List[int] = None) -> Dict:
        if trial_candidates is None:
            trial_candidates = [1, 3, 5, 7]

        best = {"ok": False, "reason": "no_result"}
        all_results = []
        for trials in trial_candidates:
            result = self.run(window=window, trials=max(1, int(trials)))
            if not result.get("ok"):
                continue
            result["trials"] = max(1, int(trials))
            all_results.append(result)
            if (not best.get("ok")) or (result["hit_rate_3_plus"] > best["hit_rate_3_plus"]):
                best = result

        return {
            "ok": bool(all_results),
            "best": best if all_results else {"ok": False, "reason": "not_enough_data"},
            "results": all_results,
        }
