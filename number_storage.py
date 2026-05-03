import json
import os
import tempfile
from datetime import datetime
from typing import List, Dict, Optional

try:
    from utils.logging_config import get_logger
    _log = get_logger(__name__)
except ImportError:
    import logging
    _log = logging.getLogger(__name__)


class NumberStorage:
    """번호 조합 저장 및 관리 클래스"""

    def __init__(self, filename: str = 'saved_numbers.json'):
        self.filename = filename
        self.saved_combinations = self._load_data()

    def _load_data(self) -> List[Dict]:
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                _log.warning("저장 데이터 로드 실패, 초기화: %s", e)
        return []

    def save_combination(self, numbers: List[int], method: str, note: str = "") -> bool:
        if len(numbers) != 6:
            return False

        entry = {
            'id': len(self.saved_combinations) + 1,
            'numbers': [int(n) for n in sorted(numbers)],
            'method': str(method),
            'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'note': str(note),
        }

        self.saved_combinations.append(entry)
        self._save_to_file()
        return True

    def _save_to_file(self) -> None:
        """원자적 쓰기 — 임시 파일에 쓴 뒤 rename으로 교체합니다."""
        dir_name = os.path.dirname(os.path.abspath(self.filename)) or '.'
        try:
            with tempfile.NamedTemporaryFile(
                mode='w', encoding='utf-8', dir=dir_name,
                suffix='.tmp', delete=False
            ) as tmp:
                json.dump(self.saved_combinations, tmp, ensure_ascii=False, indent=2)
                tmp_path = tmp.name
            os.replace(tmp_path, self.filename)
        except OSError as e:
            _log.error("번호 저장 실패: %s", e)
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

    def get_all_combinations(self) -> List[Dict]:
        return self.saved_combinations

    def delete_combination(self, index: int) -> bool:
        if 0 <= index < len(self.saved_combinations):
            del self.saved_combinations[index]
            self._save_to_file()
            return True
        return False

    def clear_all(self) -> None:
        self.saved_combinations = []
        self._save_to_file()
