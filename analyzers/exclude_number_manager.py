"""제외번호 관리 모듈"""

import json
import os
import tempfile
from datetime import datetime

try:
    from utils.logging_config import get_logger
    _log = get_logger(__name__)
except ImportError:
    import logging
    _log = logging.getLogger(__name__)


class ExcludeNumberManager:
    """제외번호를 관리하는 클래스"""

    def __init__(self, filename='exclude_numbers.json'):
        self.filename = filename
        self.exclude_numbers = set()
        self.load_exclude_numbers()

    def load_exclude_numbers(self):
        """파일에서 제외번호를 불러옵니다."""
        try:
            with open(self.filename, 'r', encoding='utf-8') as file:
                data = json.load(file)
                self.exclude_numbers = set(data.get('exclude_numbers', []))
                print(f" 제외번호 {len(self.exclude_numbers)}개를 불러왔습니다.")
        except FileNotFoundError:
            print(" 제외번호 파일이 없습니다. 새로 생성합니다.")
            self.exclude_numbers = set()
        except Exception as e:
            print(f" 제외번호 불러오기 실패: {e}")
            self.exclude_numbers = set()

    def save_exclude_numbers(self) -> bool:
        """제외번호를 원자적으로 저장합니다 (임시 파일 → rename)."""
        data = {
            'exclude_numbers': sorted(list(self.exclude_numbers)),
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
        dir_name = os.path.dirname(os.path.abspath(self.filename)) or '.'
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode='w', encoding='utf-8', dir=dir_name,
                suffix='.tmp', delete=False
            ) as tmp:
                json.dump(data, tmp, ensure_ascii=False, indent=2)
                tmp_path = tmp.name
            os.replace(tmp_path, self.filename)
            print(f" 제외번호 {len(self.exclude_numbers)}개가 저장되었습니다.")
            return True
        except OSError as e:
            _log.error("제외번호 저장 실패: %s", e)
            print(f" 제외번호 저장 실패: {e}")
            if tmp_path:
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass
            return False

    def add_exclude_numbers(self, numbers):
        """제외번호를 추가합니다."""
        if isinstance(numbers, int):
            numbers = [numbers]

        added_count = 0
        for num in numbers:
            if 1 <= num <= 45 and num not in self.exclude_numbers:
                self.exclude_numbers.add(num)
                added_count += 1

        if added_count > 0:
            self.save_exclude_numbers()
            print(f" 제외번호 {added_count}개가 추가되었습니다.")
        else:
            print("[WARN] 추가할 제외번호가 없습니다.")

        return added_count

    def remove_exclude_numbers(self, numbers):
        """제외번호를 제거합니다."""
        if isinstance(numbers, int):
            numbers = [numbers]

        removed_count = 0
        for num in numbers:
            if num in self.exclude_numbers:
                self.exclude_numbers.remove(num)
                removed_count += 1

        if removed_count > 0:
            self.save_exclude_numbers()
            print(f" 제외번호 {removed_count}개가 제거되었습니다.")
        else:
            print("[WARN] 제거할 제외번호가 없습니다.")

        return removed_count

    def clear_exclude_numbers(self):
        """모든 제외번호를 제거합니다."""
        count = len(self.exclude_numbers)
        self.exclude_numbers.clear()
        self.save_exclude_numbers()
        print(f" 제외번호 {count}개가 모두 제거되었습니다.")
        return count

    def get_exclude_numbers(self):
        """현재 제외번호 목록을 반환합니다."""
        return sorted(list(self.exclude_numbers))

    def show_exclude_numbers(self):
        """제외번호 목록을 출력합니다."""
        if not self.exclude_numbers:
            print(" 등록된 제외번호가 없습니다.")
            return

        numbers = sorted(list(self.exclude_numbers))
        print(f" 등록된 제외번호 ({len(numbers)}개):")
        print(f"   {numbers}")

        # 사용 가능한 번호 개수 표시
        available_count = 45 - len(numbers)
        print(f"[INFO] 사용 가능한 번호: {available_count}개")

        if available_count < 6:
            print("[WARN] 경고: 사용 가능한 번호가 6개 미만입니다.")

    def is_valid_for_lotto(self):
        """로또 번호 생성이 가능한지 확인합니다."""
        available_count = 45 - len(self.exclude_numbers)
        return available_count >= 6

    def get_available_numbers(self):
        """사용 가능한 번호 목록을 반환합니다."""
        return [n for n in range(1, 46) if n not in self.exclude_numbers]
