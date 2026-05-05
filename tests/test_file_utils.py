"""utils/file_utils.py 테스트 — load_csv_data, resolve_data_file"""

import csv
import os
import tempfile

import pytest

from utils.file_utils import load_csv_data, resolve_data_file


class TestLoadCsvData:
    """load_csv_data: 인코딩 자동 감지로 CSV 로드"""

    def test_nonexistent_file_returns_empty(self):
        assert load_csv_data("존재하지않는파일_xyz.csv") == []

    def test_valid_utf8_csv(self):
        """올바른 UTF-8 CSV → 데이터 반환"""
        rows = [
            {'회차': '1', '번호1': '3', '번호2': '14', '번호3': '22',
             '번호4': '31', '번호5': '39', '번호6': '45', '보너스번호': '7'},
            {'회차': '2', '번호1': '5', '번호2': '11', '번호3': '20',
             '번호4': '28', '번호5': '35', '번호6': '42', '보너스번호': '2'},
        ]
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.csv', encoding='utf-8', delete=False, newline=''
        ) as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
            tmp_path = f.name

        try:
            result = load_csv_data(tmp_path)
            assert len(result) == 2
            assert result[0]['번호1'] == '3'
            assert result[1]['회차'] == '2'
        finally:
            os.unlink(tmp_path)

    def test_missing_번호1_column_returns_empty(self):
        """'번호1' 컬럼이 없는 CSV → 빈 리스트 반환"""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.csv', encoding='utf-8', delete=False, newline=''
        ) as f:
            writer = csv.DictWriter(f, fieldnames=['col_a', 'col_b'])
            writer.writeheader()
            writer.writerow({'col_a': '1', 'col_b': '2'})
            tmp_path = f.name

        try:
            result = load_csv_data(tmp_path)
            assert result == []
        finally:
            os.unlink(tmp_path)

    def test_empty_csv_returns_empty(self):
        """헤더만 있는 빈 CSV → 빈 리스트 반환"""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.csv', encoding='utf-8', delete=False, newline=''
        ) as f:
            writer = csv.DictWriter(f, fieldnames=['번호1', '번호2'])
            writer.writeheader()
            tmp_path = f.name

        try:
            result = load_csv_data(tmp_path)
            assert result == []
        finally:
            os.unlink(tmp_path)


class TestResolveDataFile:
    """resolve_data_file: 파일 경로 결정"""

    def test_returns_string(self):
        result = resolve_data_file()
        assert isinstance(result, str)
        assert result.endswith('.csv')

    def test_default_when_no_file(self, tmp_path, monkeypatch):
        """당첨번호 CSV가 없으면 기본 파일명 반환"""
        monkeypatch.chdir(tmp_path)
        result = resolve_data_file()
        assert result == '로또당첨번호.csv'

    def test_finds_existing_file(self, tmp_path, monkeypatch):
        """'로또당첨번호.csv'가 존재하면 그것을 반환"""
        monkeypatch.chdir(tmp_path)
        target = tmp_path / '로또당첨번호.csv'
        target.write_text('test')
        result = resolve_data_file()
        assert result == '로또당첨번호.csv'
