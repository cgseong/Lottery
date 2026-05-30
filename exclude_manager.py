#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""제외번호 관리 모듈"""

import json
import os
import tempfile
from typing import List, Set

try:
    from utils.logging_config import get_logger
    from utils.constants import DEFAULT_EXCLUDE_FILE
    _log = get_logger(__name__)
except ImportError:
    import logging
    _log = logging.getLogger(__name__)
    DEFAULT_EXCLUDE_FILE = 'exclude_numbers.json'


class ExcludeNumberManager:
    """제외번호 저장 및 관리 클래스"""

    def __init__(self, filename: str = DEFAULT_EXCLUDE_FILE):
        self.filename = filename
        self.exclude_numbers: List[int] = self._load_data()

    def _load_data(self) -> List[int]:
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return [int(n) for n in data if 1 <= int(n) <= 45]
                    return []
            except (json.JSONDecodeError, OSError, ValueError) as e:
                _log.warning("제외번호 로드 실패, 초기화: %s", e)
        return []

    def _save_to_file(self) -> None:
        """원자적 쓰기 — 임시 파일에 쓴 뒤 rename으로 교체합니다."""
        dir_name = os.path.dirname(os.path.abspath(self.filename)) or '.'
        try:
            with tempfile.NamedTemporaryFile(
                mode='w', encoding='utf-8', dir=dir_name,
                suffix='.tmp', delete=False
            ) as tmp:
                json.dump(sorted(self.exclude_numbers), tmp, ensure_ascii=False, indent=2)
                tmp_path = tmp.name
            os.replace(tmp_path, self.filename)
        except OSError as e:
            _log.error("제외번호 저장 실패: %s", e)
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

    def get_exclude_numbers(self) -> List[int]:
        """현재 제외번호 목록을 반환합니다."""
        return list(self.exclude_numbers)

    def add_numbers(self, numbers: List[int]) -> None:
        """제외번호를 추가합니다."""
        for n in numbers:
            if 1 <= n <= 45 and n not in self.exclude_numbers:
                self.exclude_numbers.append(n)
        self.exclude_numbers.sort()
        self._save_to_file()

    def remove_numbers(self, numbers: List[int]) -> None:
        """제외번호를 제거합니다."""
        self.exclude_numbers = [n for n in self.exclude_numbers if n not in numbers]
        self._save_to_file()

    def clear_all(self) -> None:
        """제외번호를 모두 초기화합니다."""
        self.exclude_numbers = []
        self._save_to_file()
