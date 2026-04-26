from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List

from analyzers.lotto_data_collector import LottoDataCollector


@dataclass
class AutoUpdateScheduler:
    collector: LottoDataCollector

    def run_once(self) -> Dict:
        started_at = datetime.now().isoformat(timespec="seconds")
        new_rows: List[Dict] = self.collector.update_latest_data() or []
        return {
            "started_at": started_at,
            "updated_count": len(new_rows),
            "updated": len(new_rows) > 0,
        }
