#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""랜덤 기반 + 약한 필터 번호 추천 엔진

설계 원칙:
  1. 로또는 완전한 무작위 추첨이므로 번호 생성도 무작위가 기본
  2. 극단적으로 비현실적인 조합(전부 홀수, 전부 한 구간 등)만 제거
  3. 여러 조합 생성 시 번호 겹침을 최소화하여 커버리지 극대화
  4. 과거 빈도/패턴에 대한 가중치를 의도적으로 배제
"""

import random
from typing import List, Dict, Optional, Set

from utils.helpers import check_consecutive_count


# 상수
_MAX_NUM = 45
_PICK = 6

# ─── 약한 필터 기준 (극단 패턴만 제거, 전체 조합의 약 10%만 걸러냄) ───
_MIN_ODD = 1      # 최소 홀수 개수 (전부 짝수 방지)
_MAX_ODD = 5      # 최대 홀수 개수 (전부 홀수 방지)
_MIN_SUM = 80     # 최소 합계 (역대 최저 근처)
_MAX_SUM = 210    # 최대 합계 (역대 최고 근처)
_MAX_CONSEC = 3   # 최대 연속 쌍 수 (4쌍 이상은 극히 드묾)
_MIN_SECTIONS = 2  # 최소 구간 수 (3구간 중 최소 2개는 사용)


def _passes_soft_filter(numbers: List[int]) -> bool:
    """약한 필터: 극단적으로 비현실적인 조합만 제거.

    역대 당첨번호 1226회차 기준으로 한 번도 나온 적 없거나
    극히 드문(1% 미만) 패턴만 제거합니다.
    """
    # 홀짝 비율 (전부 홀수 또는 전부 짝수 방지)
    odd_count = sum(1 for n in numbers if n % 2 != 0)
    if odd_count < _MIN_ODD or odd_count > _MAX_ODD:
        return False

    # 합계 범위 (극단값 제거)
    total = sum(numbers)
    if total < _MIN_SUM or total > _MAX_SUM:
        return False

    # 연속번호 과다 (4쌍 이상 = 5개 이상 연속)
    if check_consecutive_count(numbers) > _MAX_CONSEC:
        return False

    # 구간 분포 (1-15, 16-30, 31-45 중 최소 2개 구간 사용)
    sections_used = set()
    for n in numbers:
        if n <= 15:
            sections_used.add(0)
        elif n <= 30:
            sections_used.add(1)
        else:
            sections_used.add(2)
    if len(sections_used) < _MIN_SECTIONS:
        return False

    return True


def _compute_diversity_score(new_combo: List[int], existing_combos: List[List[int]]) -> float:
    """기존 조합들과의 다양성 점수 (높을수록 겹침이 적음).

    각 기존 조합과 겹치는 번호 수의 평균을 계산하고,
    겹침이 적을수록 높은 점수를 반환합니다.
    """
    if not existing_combos:
        return 1.0

    new_set = set(new_combo)
    overlaps = [len(new_set & set(combo)) for combo in existing_combos]
    avg_overlap = sum(overlaps) / len(overlaps)
    # 6개 중 평균 겹침이 0이면 1.0, 6이면 0.0
    return max(0.0, 1.0 - avg_overlap / _PICK)


def generate_diverse_recommendations(
    num_recommendations: int = 5,
    exclude_numbers: Optional[Set[int]] = None,
    fixed_numbers: Optional[Set[int]] = None,
    max_overlap: int = 2,
    seed: Optional[int] = None,
) -> List[Dict]:
    """랜덤 기반 + 약한 필터 + 다양성 확보 번호 추천.

    Args:
        num_recommendations: 생성할 조합 수 (1~20)
        exclude_numbers: 제외할 번호 집합
        fixed_numbers: 반드시 포함할 번호 집합 (최대 5개)
        max_overlap: 조합 간 허용 최대 겹침 번호 수 (기본 2)
        seed: 난수 시드 (None이면 매번 다른 결과)

    Returns:
        [{'numbers': [...], 'diversity_score': float}, ...]
    """
    if seed is not None:
        random.seed(seed)

    exclude = exclude_numbers or set()
    fixed = sorted(fixed_numbers or set())

    # 고정번호 유효성 검증
    if len(fixed) >= _PICK:
        return [{'numbers': fixed[:_PICK], 'diversity_score': 1.0}]

    # 사용 가능한 번호 풀
    available = [n for n in range(1, _MAX_NUM + 1) if n not in exclude and n not in fixed]
    needed = _PICK - len(fixed)

    if len(available) < needed:
        return []

    results: List[List[int]] = []
    max_attempts = num_recommendations * 500  # 충분한 시도 횟수
    attempts = 0

    while len(results) < num_recommendations and attempts < max_attempts:
        attempts += 1

        # 순수 무작위 생성
        picked = random.sample(available, needed)
        combo = sorted(fixed + picked)

        # 약한 필터 적용
        if not _passes_soft_filter(combo):
            continue

        # 다양성 검증: 기존 조합과 최대 max_overlap개까지만 겹침 허용
        combo_set = set(combo)
        is_diverse = True
        for existing in results:
            if len(combo_set & set(existing)) > max_overlap:
                is_diverse = False
                break

        if not is_diverse:
            # 조합이 많아지면 다양성 제약을 점진적으로 완화
            if len(results) >= num_recommendations * 0.7:
                # 70% 이상 채웠으면 겹침 +1 허용
                is_diverse = all(
                    len(combo_set & set(ex)) <= max_overlap + 1
                    for ex in results
                )
            if not is_diverse:
                continue

        results.append(combo)

    # 다양성 점수 계산 및 반환
    recommendations = []
    for i, combo in enumerate(results):
        others = results[:i] + results[i+1:]
        diversity = _compute_diversity_score(combo, others)
        recommendations.append({
            'numbers': combo,
            'diversity_score': round(diversity, 4),
        })

    return recommendations


def generate_coverage_sets(
    num_sets: int = 5,
    exclude_numbers: Optional[Set[int]] = None,
    seed: Optional[int] = None,
) -> List[Dict]:
    """번호 커버리지를 극대화하는 조합 세트 생성.

    N개 조합이 1~45 번호를 최대한 많이 커버하도록 합니다.
    5조합 × 6번호 = 30번호, 이론적으로 45개 중 30개 커버 가능.

    Args:
        num_sets: 생성할 조합 수
        exclude_numbers: 제외할 번호
        seed: 난수 시드

    Returns:
        [{'numbers': [...], 'coverage': float, 'new_numbers': int}, ...]
    """
    if seed is not None:
        random.seed(seed)

    exclude = exclude_numbers or set()
    all_available = [n for n in range(1, _MAX_NUM + 1) if n not in exclude]

    if len(all_available) < _PICK:
        return []

    results: List[List[int]] = []
    covered: Set[int] = set()
    max_attempts_per_set = 200

    for set_idx in range(num_sets):
        best_combo: Optional[List[int]] = None
        best_new_count = -1

        for _ in range(max_attempts_per_set):
            # 아직 커버되지 않은 번호를 우선 선택
            uncovered = [n for n in all_available if n not in covered]
            combo: List[int]

            if len(uncovered) >= _PICK:
                # 미커버 번호에서 우선 선택 (약간의 무작위성 유지)
                combo = sorted(random.sample(uncovered, _PICK))
            elif uncovered:
                # 미커버 번호 전부 + 나머지는 랜덤
                rest_pool = [n for n in all_available if n not in set(uncovered)]
                rest_needed = _PICK - len(uncovered)
                if rest_needed > len(rest_pool):
                    continue
                combo = sorted(uncovered + random.sample(rest_pool, rest_needed))
            else:
                # 모든 번호가 커버됨 → 순수 랜덤
                combo = sorted(random.sample(all_available, _PICK))

            if not _passes_soft_filter(combo):
                continue

            # 새로 커버하는 번호 수
            new_count = len(set(combo) - covered)
            if new_count > best_new_count:
                best_new_count = new_count
                best_combo = combo

        if best_combo is None:
            # 필터 통과 실패 시 필터 없이 생성
            best_combo = sorted(random.sample(all_available, _PICK))
            best_new_count = len(set(best_combo) - covered)

        results.append(best_combo)
        covered.update(best_combo)

    # 결과 포맷팅
    total_available = len(all_available)
    recommendations = []
    running_covered: Set[int] = set()

    for combo in results:
        new_nums = len(set(combo) - running_covered)
        running_covered.update(combo)
        coverage = len(running_covered) / total_available if total_available else 0
        recommendations.append({
            'numbers': combo,
            'coverage': round(coverage, 4),
            'new_numbers': new_nums,
        })

    return recommendations
