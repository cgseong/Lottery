#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
로또 분석 시스템 유틸리티 함수들
"""

import os
import sys
from typing import List, Dict, Optional, Set, Tuple, Any
from datetime import datetime

# 상수 import
from .constants import *


def check_installation_status() -> Tuple[bool, bool]:
    """필요한 패키지들의 설치 상태를 확인합니다."""
    print("[CHECK] 패키지 설치 상태 확인 중...")
    print("=" * 50)

    # 표준 라이브러리
    basic_packages = {
        'csv': 'CSV 파일 처리',
        'random': '랜덤 번호 생성',
        'collections': '데이터 구조',
        'datetime': '날짜/시간 처리',
    }
    print(" 기본 패키지:")
    basic_available = True
    for package, description in basic_packages.items():
        try:
            __import__(package)
            print(f"    {package}: {description}")
        except ImportError:
            print(f"    {package}: {description} (설치 필요)")
            basic_available = False

    # 외부 의존성
    ext_packages = {
        'sklearn': '머신러닝 라이브러리',
        'numpy': '수치 계산 라이브러리',
        'joblib': '병렬 처리 라이브러리',
        'requests': 'HTTP 요청 라이브러리',
        'bs4': 'HTML 파싱 라이브러리',
        'matplotlib': '그래프 시각화 라이브러리',
    }
    print("\n 외부 패키지:")
    ext_available = True
    for package, description in ext_packages.items():
        try:
            __import__(package)
            print(f"    {package}: {description}")
        except ImportError:
            print(f"    {package}: {description} (설치 필요)")
            ext_available = False

    if not basic_available or not ext_available:
        print("\n 설치 가이드: pip install -r requirements.txt")
    else:
        print("\n    모든 패키지가 설치되어 있습니다!")

    print("=" * 50)
    return basic_available, ext_available


def show_system_info():
    """시스템 정보를 표시합니다."""
    print("\n 시스템 정보")
    print("=" * 50)

    import platform
    print(f" Python 버전: {sys.version}")
    print(f" 운영체제: {platform.system()} {platform.release()}")
    print(f" 작업 디렉토리: {os.getcwd()}")

    files_to_check = [
        DEFAULT_CSV_FILE,
        DEFAULT_EXCLUDE_FILE,
        DEFAULT_SAVED_FILE,
        DEFAULT_AI_MODELS_PATH,
    ]
    print("\n 파일 상태:")
    for file_path in files_to_check:
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            print(f"    {file_path} ({file_size:,} bytes)")
        else:
            print(f"    {file_path} (없음)")

    print("=" * 50)



def validate_numbers(numbers: List[int]) -> bool:
    """번호 조합의 유효성을 검사합니다."""
    if not numbers or len(numbers) != NUM_LOTTO_NUMBERS_TO_PICK:
        return False
    
    # 중복 검사
    if len(set(numbers)) != NUM_LOTTO_NUMBERS_TO_PICK:
        return False
    
    # 범위 검사
    for num in numbers:
        if not (1 <= num <= MAX_LOTTO_NUMBER):
            return False
    
    return True


def format_numbers(numbers: List[int]) -> str:
    """번호 리스트를 포맷팅합니다."""
    if not numbers:
        return "[]"
    return f"[{', '.join(map(str, sorted(numbers)))}]"


def calculate_summary_stats(numbers_list: List[List[int]]) -> Dict[str, Any]:
    """번호 조합들의 통계를 계산합니다."""
    if not numbers_list:
        return {}
    
    all_numbers = []
    sums = []
    
    for numbers in numbers_list:
        all_numbers.extend(numbers)
        sums.append(sum(numbers))
    
    # 빈도 분석
    from collections import Counter
    frequency = Counter(all_numbers)
    
    return {
        'total_combinations': len(numbers_list),
        'most_common_numbers': frequency.most_common(5),
        'least_common_numbers': frequency.most_common()[:-6:-1],
        'avg_sum': sum(sums) / len(sums),
        'min_sum': min(sums),
        'max_sum': max(sums),
        'sum_range': (min(sums), max(sums))
    }


def print_recommendations(recommendations: List[Dict], title: str = "추천 번호"):
    """추천 번호들을 출력합니다."""
    if not recommendations:
        print(f" {title}이 없습니다.")
        return
    
    print(f"\n {title} ({len(recommendations)}개):")
    print("=" * 60)
    
    for i, rec in enumerate(recommendations, 1):
        numbers = rec.get('numbers', [])
        score = rec.get('score', 0)
        method = rec.get('method', '알 수 없음')
        consecutive_count = rec.get('consecutive_count', 0)
        
        print(f"{i}. {format_numbers(numbers)}")
        print(f"   점수: {score:.3f}")
        print(f"   방법: {method}")
        print(f"   연속번호: {consecutive_count}개")
        
        # 추가 정보가 있으면 출력
        if 'sum' in rec:
            print(f"   합계: {rec['sum']}")
        if 'probability' in rec:
            print(f"   확률: {rec['probability']:.3f}")
        if 'cluster_info' in rec and rec['cluster_info']:
            cluster_info = rec['cluster_info']
            print(f"   클러스터: {cluster_info['best_cluster']+1} (유사도: {cluster_info['similarity']:.3f})")
        
        print()
    
    print("=" * 60)


def safe_input(prompt: str, default: str = "", input_type: str = "str") -> Any:
    """안전한 입력을 받습니다."""
    try:
        user_input = input(prompt).strip()
        if not user_input and default:
            user_input = default
        
        if input_type == "int":
            return int(user_input)
        elif input_type == "float":
            return float(user_input)
        else:
            return user_input
    except (ValueError, KeyboardInterrupt):
        return None


def create_directory_if_not_exists(directory: str) -> bool:
    """디렉토리가 없으면 생성합니다."""
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f" 디렉토리 생성: {directory}")
        return True
    except Exception as e:
        print(f" 디렉토리 생성 실패: {e}")
        return False


def get_file_size_mb(file_path: str) -> float:
    """파일 크기를 MB 단위로 반환합니다."""
    try:
        if os.path.exists(file_path):
            return os.path.getsize(file_path) / (1024 * 1024)
        return 0.0
    except Exception:
        return 0.0


def format_file_size(size_bytes: int) -> str:
    """파일 크기를 읽기 쉬운 형태로 포맷팅합니다."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def validate_date_format(date_str: str) -> bool:
    """날짜 형식의 유효성을 검사합니다."""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def extract_numbers_from_data(data: Dict) -> List[int]:
    """데이터에서 번호를 추출합니다."""
    numbers = []
    for i in range(1, 7):
        key = f'num{i}'
        if key in data and data[key]:
            try:
                numbers.append(int(data[key]))
            except (ValueError, TypeError):
                continue
    return sorted(numbers)


def check_consecutive_count(numbers: List[int]) -> int:
    """번호 목록에서 연속 쌍(인접 번호 쌍)의 총 개수를 반환합니다.

    예: [1, 2, 5, 6, 7] → 3쌍  ((1,2), (5,6), (6,7))
    예: [3, 7, 12, 33, 40, 45] → 0쌍

    이 함수는 프로젝트 전반에서 공유되는 단일 구현입니다.
    각 분석기 클래스의 check_consecutive_numbers()는 이 함수에 위임합니다.
    """
    if len(numbers) < 2:
        return 0
    sorted_nums = sorted(numbers)
    return sum(1 for a, b in zip(sorted_nums, sorted_nums[1:]) if b - a == 1)


def normalize_exclude_numbers(exclude_numbers) -> Set[int]:
    """제외번호를 set[int]로 정규화합니다.

    dict, list, set, None 등 다양한 입력 형식을 일관된 집합으로 변환합니다.
    dict인 경우 키만 추출합니다 (키가 번호 번호라고 가정).

    Examples:
        >>> normalize_exclude_numbers(None)
        set()
        >>> normalize_exclude_numbers({1, 2, 3})
        {1, 2, 3}
        >>> normalize_exclude_numbers({1: 'a', 5: 'b'})
        {1, 5}
        >>> normalize_exclude_numbers([3, 7, 12])
        {3, 7, 12}
    """
    if not exclude_numbers:
        return set()
    if isinstance(exclude_numbers, dict):
        return set(exclude_numbers.keys())
    return set(exclude_numbers)



# ──────────────────────────────────────────────────────────────────────
# 조합 필터링 함수 — 역사적으로 당첨 가능성이 낮은 패턴을 제거합니다.
# ──────────────────────────────────────────────────────────────────────

def calc_ac_value(numbers: List[int]) -> int:
    """AC값 (Arithmetic Complexity) 계산.

    6개 번호에서 만들 수 있는 모든 쌍의 차이 고유값 수.
    이론적 최대: C(6,2) = 15, 최소: 5 (등차수열)
    역대 당첨번호 AC값은 대부분 7~10 범위.

    Examples:
        >>> calc_ac_value([1, 2, 3, 4, 5, 6])  # 등차
        5
        >>> calc_ac_value([2, 13, 19, 27, 38, 45])
        15
    """
    sorted_nums = sorted(numbers)
    diffs = set()
    for i in range(len(sorted_nums)):
        for j in range(i + 1, len(sorted_nums)):
            diffs.add(sorted_nums[j] - sorted_nums[i])
    return len(diffs)


def check_same_decade_limit(numbers: List[int], max_same: int = 3) -> bool:
    """동일 십의자리(decade) 번호가 max_same개 이하인지 확인합니다.

    로또 번호를 십의자리 기준으로 그룹핑(1~9, 10~19, 20~29, 30~39, 40~45)하여
    한 그룹에 max_same개 초과 번호가 있으면 False.

    Examples:
        >>> check_same_decade_limit([11, 12, 13, 14, 25, 36])  # 10대 4개
        False
        >>> check_same_decade_limit([3, 12, 23, 34, 41, 45])
        True
    """
    from collections import Counter
    decades = Counter((n - 1) // 10 for n in numbers)
    return all(cnt <= max_same for cnt in decades.values())


def calc_last_digit_sum(numbers: List[int]) -> int:
    """끝수(일의 자리) 합계를 계산합니다.

    역대 당첨번호의 끝수합은 대체로 13~33 범위에 약 80% 분포.

    Examples:
        >>> calc_last_digit_sum([3, 12, 25, 31, 40, 44])
        15
    """
    return sum(n % 10 for n in numbers)


def check_last_digit_sum_range(numbers: List[int], low: int = 13, high: int = 33) -> bool:
    """끝수합이 지정 범위 내인지 확인합니다.

    Args:
        low: 하한 (포함)
        high: 상한 (포함)
    """
    s = calc_last_digit_sum(numbers)
    return low <= s <= high


def check_low_high_ratio(numbers: List[int], max_imbalance: int = 4) -> bool:
    """저번호(1-22) / 고번호(23-45) 비율이 max_imbalance 이하인지 확인합니다.

    max_imbalance=4 → 허용 비율: 2:4, 3:3, 4:2 (즉, 한쪽이 5개 이상이면 False)

    Examples:
        >>> check_low_high_ratio([1, 2, 3, 4, 5, 44])  # 저5:고1
        False
        >>> check_low_high_ratio([3, 12, 22, 30, 38, 44])  # 저3:고3
        True
    """
    low_count = sum(1 for n in numbers if n <= 22)
    high_count = 6 - low_count
    return low_count <= max_imbalance and high_count <= max_imbalance


def get_last_draw_numbers(historical_data: List[Dict]) -> Set[int]:
    """역사 데이터에서 직전(최신) 회차의 당첨번호를 반환합니다.

    Args:
        historical_data: CSV에서 로드한 당첨번호 dict 리스트

    Returns:
        직전 회차 당첨번호 집합 (6개) 또는 빈 집합
    """
    if not historical_data:
        return set()

    # round 기준으로 최신 회차 찾기
    latest = max(historical_data, key=lambda x: int(x.get('round', 0) or 0))
    nums = set()
    for i in range(1, 7):
        try:
            n = int(latest.get(f'num{i}', 0))
            if 1 <= n <= MAX_LOTTO_NUMBER:
                nums.add(n)
        except (ValueError, TypeError):
            continue
    return nums


def exceeds_prev_draw_overlap(numbers: List[int], prev_numbers: Set[int],
                               max_overlap: int = 1) -> bool:
    """조합이 직전 회차 당첨번호와 max_overlap개 초과로 겹치는지 확인합니다.

    직전 회차 번호가 2개 이상 포함된 조합을 제외하려면 max_overlap=1로 호출합니다.

    Args:
        numbers: 검사할 번호 조합
        prev_numbers: 직전 회차 당첨번호 집합
        max_overlap: 허용 최대 겹침 수 (기본 1 → 2개 이상이면 True 반환)

    Returns:
        True: 겹침 초과 (제외 대상)
        False: 허용 범위 (통과)
    """
    if not prev_numbers:
        return False
    overlap = len(set(numbers) & prev_numbers)
    return overlap > max_overlap


def passes_advanced_filters(
    numbers: List[int],
    min_ac: int = 7,
    max_same_decade: int = 3,
    last_digit_sum_range: Tuple[int, int] = (13, 33),
    max_low_high_imbalance: int = 4,
) -> bool:
    """복합 고급 필터를 한 번에 적용합니다.

    Args:
        numbers: 6개 번호 조합
        min_ac: 최소 AC값 (기본 7, 역사적으로 AC<7인 당첨은 극히 드묾)
        max_same_decade: 동일 십의자리 최대 허용 수
        last_digit_sum_range: (최소, 최대) 끝수합 범위
        max_low_high_imbalance: 저/고 한쪽 최대 허용 수

    Returns:
        True: 모든 필터 통과 (양호한 조합)
        False: 하나라도 실패 (제거 대상)
    """
    # 1. AC값 필터
    if calc_ac_value(numbers) < min_ac:
        return False

    # 2. 동일 십의자리 제한
    if not check_same_decade_limit(numbers, max_same_decade):
        return False

    # 3. 끝수합 범위
    if not check_last_digit_sum_range(numbers, *last_digit_sum_range):
        return False

    # 4. 저고비율
    if not check_low_high_ratio(numbers, max_low_high_imbalance):
        return False

    return True
