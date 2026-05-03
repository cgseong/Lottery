"""NumberStorage 단위 테스트"""

import json
import os
import pytest
from number_storage import NumberStorage


@pytest.fixture
def tmp_storage(tmp_path):
    return NumberStorage(filename=str(tmp_path / 'test_saved.json'))


def test_save_and_retrieve(tmp_storage):
    assert tmp_storage.save_combination([1, 7, 14, 21, 33, 42], '테스트')
    combos = tmp_storage.get_all_combinations()
    assert len(combos) == 1
    assert combos[0]['numbers'] == [1, 7, 14, 21, 33, 42]


def test_numbers_are_sorted_on_save(tmp_storage):
    tmp_storage.save_combination([42, 1, 21, 7, 33, 14], '순서테스트')
    saved = tmp_storage.get_all_combinations()[0]['numbers']
    assert saved == sorted(saved)


def test_invalid_length_rejected(tmp_storage):
    assert not tmp_storage.save_combination([1, 2, 3], '짧음')
    assert not tmp_storage.save_combination([1, 2, 3, 4, 5, 6, 7], '긺')


def test_delete_combination(tmp_storage):
    tmp_storage.save_combination([1, 7, 14, 21, 33, 42], 'A')
    tmp_storage.save_combination([2, 8, 15, 22, 34, 43], 'B')
    assert tmp_storage.delete_combination(0)
    assert len(tmp_storage.get_all_combinations()) == 1


def test_delete_out_of_range(tmp_storage):
    assert not tmp_storage.delete_combination(0)
    assert not tmp_storage.delete_combination(-1)


def test_clear_all(tmp_storage):
    tmp_storage.save_combination([1, 7, 14, 21, 33, 42], 'X')
    tmp_storage.clear_all()
    assert tmp_storage.get_all_combinations() == []


def test_persistence(tmp_path):
    path = str(tmp_path / 'persist.json')
    s1 = NumberStorage(filename=path)
    s1.save_combination([3, 9, 16, 23, 35, 44], '영속성')
    s2 = NumberStorage(filename=path)
    assert len(s2.get_all_combinations()) == 1
    assert s2.get_all_combinations()[0]['numbers'] == [3, 9, 16, 23, 35, 44]


def test_atomic_write_creates_file(tmp_path):
    path = str(tmp_path / 'atomic.json')
    s = NumberStorage(filename=path)
    s.save_combination([1, 2, 3, 4, 5, 6], '원자성')
    assert os.path.exists(path)
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    assert len(data) == 1
