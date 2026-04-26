import json
import os
from datetime import datetime
from typing import List, Dict, Optional

class NumberStorage:
    """번호 조합 저장 및 관리 클래스"""
    
    def __init__(self, filename: str = 'saved_numbers.json'):
        self.filename = filename
        self.saved_combinations = self._load_data()

    def _load_data(self) -> List[Dict]:
        """저장된 데이터를 로드합니다."""
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return []
        return []

    def save_combination(self, numbers: List[int], method: str, note: str = "") -> bool:
        """번호 조합을 저장합니다."""
        if len(numbers) != 6:
            return False
            
        entry = {
            'id': len(self.saved_combinations) + 1,
            'numbers': [int(n) for n in sorted(numbers)],
            'method': method,
            'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'note': note
        }
        
        self.saved_combinations.append(entry)
        self._save_to_file()
        return True

    def _save_to_file(self):
        """데이터를 파일에 저장합니다."""
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(self.saved_combinations, f, ensure_ascii=False, indent=2)

    def get_all_combinations(self) -> List[Dict]:
        """모든 저장된 조합을 반환합니다."""
        return self.saved_combinations

    def delete_combination(self, index: int) -> bool:
        """특정 인덱스의 조합을 삭제합니다."""
        if 0 <= index < len(self.saved_combinations):
            del self.saved_combinations[index]
            self._save_to_file()
            return True
        return False

    def clear_all(self):
        """모든 데이터를 삭제합니다."""
        self.saved_combinations = []
        self._save_to_file()
