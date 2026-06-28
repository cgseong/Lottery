"""패턴 구조 분석기 모듈

7열 그리드 좌표 기반으로 당첨번호의 구조적 특성을 수치화하고,
패턴 유형을 분류하며, 무게중심 이동 추세를 분석합니다.

분석 항목:
    1. 구조적 특성 수치화: 무게중심, 분산도, 행/열 엔트로피, 밀집도 등
    2. 패턴 유형 분류: 밀집/분산/대각선/수평/수직/ㄱ자/지그재그형
    3. 무게중심 이동 추세: 연속 회차 간 무게중심 변위 벡터 및 예측
"""
from __future__ import annotations

import math
import numpy as np
from collections import Counter, defaultdict
from typing import Dict, List, Optional, Tuple

from utils.constants import MAX_LOTTO_NUMBER, LOTTO_NUMBER_COLUMNS

try:
    from utils.logging_config import get_logger
    _log = get_logger(__name__)
except ImportError:
    import logging
    _log = logging.getLogger(__name__)

# 그리드 설정: 7열 × 7행
_COLS = 7
_ROWS = 7



# ═══════════════════════════════════════════════════════════════════════
# 패턴 유형 정의
# ═══════════════════════════════════════════════════════════════════════

PATTERN_TYPES = {
    'dense': '밀집형',        # 번호가 좁은 영역에 집중
    'dispersed': '분산형',    # 번호가 넓게 퍼짐
    'diagonal': '대각선형',   # 대각선 방향 배치
    'horizontal': '수평형',   # 같은 행에 집중
    'vertical': '수직형',     # 같은 열에 집중
    'L_shape': 'ㄱ자형',     # L자 또는 ㄱ자 배치
    'zigzag': '지그재그형',   # 행 간 좌우 교차
    'balanced': '균형형',     # 고르게 분포
}


def number_to_grid(number: int) -> Tuple[int, int]:
    """번호(1~45)를 7열 그리드 좌표 (row, col)로 변환합니다.
    
    Args:
        number: 1~45 번호
    Returns:
        (row, col) — 0-indexed
    """
    idx = number - 1
    return (idx // _COLS, idx % _COLS)


def grid_to_number(row: int, col: int) -> int:
    """그리드 좌표를 번호로 변환합니다."""
    return row * _COLS + col + 1



# ═══════════════════════════════════════════════════════════════════════
# 1. 구조적 특성 수치화
# ═══════════════════════════════════════════════════════════════════════

def compute_structural_features(numbers: List[int]) -> Dict[str, float]:
    """당첨번호 조합의 구조적 특성을 수치화합니다.

    Args:
        numbers: 6개 당첨번호 리스트

    Returns:
        {
            'centroid_row': 무게중심 행,
            'centroid_col': 무게중심 열,
            'spread': 분산도 (표준편차),
            'row_entropy': 행 분포 엔트로피,
            'col_entropy': 열 분포 엔트로피,
            'density': 밀집도 (볼록 껍질 면적 역수),
            'aspect_ratio': 종횡비 (행 범위 / 열 범위),
            'diagonal_score': 대각선 정렬도,
            'path_length': 번호 순서 연결 총 경로 길이,
            'direction_changes': 경로 방향 변화 횟수,
        }
    """
    if not numbers or len(numbers) < 2:
        return _empty_features()

    coords = [number_to_grid(n) for n in numbers]
    rows = [c[0] for c in coords]
    cols = [c[1] for c in coords]

    # 무게중심
    centroid_row = np.mean(rows)
    centroid_col = np.mean(cols)

    # 분산도 (유클리드 거리 표준편차)
    distances = [math.sqrt((r - centroid_row)**2 + (c - centroid_col)**2)
                 for r, c in coords]
    spread = float(np.std(distances))

    # 행/열 엔트로피
    row_entropy = _entropy(rows, _ROWS)
    col_entropy = _entropy(cols, _COLS)

    # 밀집도: 바운딩 박스 면적 대비 점 수
    row_range = max(rows) - min(rows) + 1
    col_range = max(cols) - min(cols) + 1
    bbox_area = row_range * col_range
    density = len(numbers) / max(1, bbox_area)

    # 종횡비
    aspect_ratio = row_range / max(1, col_range)

    # 대각선 정렬도 (상관계수)
    if len(set(rows)) > 1 and len(set(cols)) > 1:
        corr = abs(float(np.corrcoef(rows, cols)[0, 1]))
        diagonal_score = corr if not np.isnan(corr) else 0.0
    else:
        diagonal_score = 0.0

    # 경로 길이 (번호 순서대로 연결)
    path_length = 0.0
    for i in range(len(coords) - 1):
        dr = coords[i+1][0] - coords[i][0]
        dc = coords[i+1][1] - coords[i][1]
        path_length += math.sqrt(dr**2 + dc**2)

    # 방향 변화 횟수
    direction_changes = _count_direction_changes(coords)

    return {
        'centroid_row': round(centroid_row, 3),
        'centroid_col': round(centroid_col, 3),
        'spread': round(spread, 3),
        'row_entropy': round(row_entropy, 3),
        'col_entropy': round(col_entropy, 3),
        'density': round(density, 3),
        'aspect_ratio': round(aspect_ratio, 3),
        'diagonal_score': round(diagonal_score, 3),
        'path_length': round(path_length, 3),
        'direction_changes': direction_changes,
    }



def _entropy(values: List[int], max_val: int) -> float:
    """분포 엔트로피를 계산합니다 (0~1 정규화)."""
    counter = Counter(values)
    total = len(values)
    if total == 0:
        return 0.0
    probs = [count / total for count in counter.values()]
    ent = -sum(p * math.log2(p) for p in probs if p > 0)
    max_ent = math.log2(min(total, max_val))
    return ent / max_ent if max_ent > 0 else 0.0


def _count_direction_changes(coords: List[Tuple[int, int]]) -> int:
    """경로에서 방향 변화(꺾임) 횟수를 계산합니다."""
    if len(coords) < 3:
        return 0
    changes = 0
    for i in range(1, len(coords) - 1):
        dr1 = coords[i][0] - coords[i-1][0]
        dc1 = coords[i][1] - coords[i-1][1]
        dr2 = coords[i+1][0] - coords[i][0]
        dc2 = coords[i+1][1] - coords[i][1]
        # 방향 벡터가 다르면 꺾임
        if (dr1, dc1) != (dr2, dc2):
            changes += 1
    return changes


def _detect_l_shape(coords: List[Tuple[int, int]]) -> float:
    """L자/ㄱ자 형태를 탐지합니다.

    경로에서 뚜렷한 수평→수직 또는 수직→수평 전환이 있는지 확인.
    """
    if len(coords) < 4:
        return 0.1

    # 연속 구간에서 수평 이동(행 변화 없음)과 수직 이동(열 변화 없음)을 검출
    segments = []
    for i in range(len(coords) - 1):
        dr = abs(coords[i+1][0] - coords[i][0])
        dc = abs(coords[i+1][1] - coords[i][1])
        if dr == 0 and dc > 0:
            segments.append('H')
        elif dc == 0 and dr > 0:
            segments.append('V')
        else:
            segments.append('D')  # 대각

    # H→V 또는 V→H 전환이 있으면 L자
    transitions = 0
    for i in range(len(segments) - 1):
        if ((segments[i] == 'H' and segments[i+1] == 'V') or
                (segments[i] == 'V' and segments[i+1] == 'H')):
            transitions += 1

    if transitions >= 2:
        return 0.8
    elif transitions == 1:
        return 0.55
    return 0.15


def _detect_zigzag(coords: List[Tuple[int, int]]) -> float:
    """지그재그 형태를 탐지합니다.

    열 방향이 번갈아 바뀌는 패턴 (좌→우→좌 또는 우→좌→우).
    """
    if len(coords) < 3:
        return 0.1

    col_diffs = [coords[i+1][1] - coords[i][1] for i in range(len(coords) - 1)]

    # 부호 변화 횟수 계산
    sign_changes = 0
    for i in range(len(col_diffs) - 1):
        if col_diffs[i] * col_diffs[i+1] < 0:  # 부호 반전
            sign_changes += 1

    max_possible = len(col_diffs) - 1
    if max_possible == 0:
        return 0.1

    ratio = sign_changes / max_possible
    if ratio >= 0.75:
        return 0.85
    elif ratio >= 0.5:
        return 0.6
    elif ratio >= 0.25:
        return 0.35
    return 0.15


def _empty_features() -> Dict[str, float]:
    return {
        'centroid_row': 0.0, 'centroid_col': 0.0,
        'spread': 0.0, 'row_entropy': 0.0, 'col_entropy': 0.0,
        'density': 0.0, 'aspect_ratio': 0.0, 'diagonal_score': 0.0,
        'path_length': 0.0, 'direction_changes': 0,
    }



# ═══════════════════════════════════════════════════════════════════════
# 2. 패턴 유형 분류
# ═══════════════════════════════════════════════════════════════════════

def classify_pattern(numbers: List[int]) -> Dict[str, any]:
    """당첨번호 조합의 패턴 유형을 분류합니다.

    Returns:
        {
            'type': 유형 키 (예: 'dense'),
            'type_name': 유형 한글명 (예: '밀집형'),
            'confidence': 분류 신뢰도 (0~1),
            'sub_scores': 각 유형별 점수,
        }
    """
    if not numbers or len(numbers) < 6:
        return {'type': 'balanced', 'type_name': '균형형',
                'confidence': 0.0, 'sub_scores': {}}

    features = compute_structural_features(numbers)
    coords = [number_to_grid(n) for n in numbers]
    rows = [c[0] for c in coords]
    cols = [c[1] for c in coords]

    scores = {}

    # 밀집형: 분산 낮고 밀집도 높음 (바운딩 박스 작음)
    row_range = max(rows) - min(rows)
    col_range = max(cols) - min(cols)
    compact = 1.0 - min(1.0, (row_range + col_range) / 10.0)
    scores['dense'] = compact * 0.7 + features['density'] * 0.3

    # 분산형: 행/열 범위 모두 넓고 밀집도 낮음
    spread_score = min(1.0, (row_range + col_range) / 10.0)
    scores['dispersed'] = spread_score * (1.0 - features['density'])

    # 수평형: 행 범위 좁고 열 범위 넓음 (같은 행 근처에 집중)
    if row_range <= 2 and col_range >= 4:
        scores['horizontal'] = 0.8 + (1.0 - row_range / 6.0) * 0.2
    elif max(Counter(rows).values()) >= 3:
        scores['horizontal'] = 0.5
    else:
        scores['horizontal'] = 0.1

    # 수직형: 열 범위 좁고 행 범위 넓음 (같은 열 근처에 집중)
    if col_range <= 2 and row_range >= 4:
        scores['vertical'] = 0.8 + (1.0 - col_range / 6.0) * 0.2
    elif max(Counter(cols).values()) >= 3:
        scores['vertical'] = 0.5
    else:
        scores['vertical'] = 0.1

    # 대각선형: 행/열 상관관계 높음
    scores['diagonal'] = features['diagonal_score'] * 0.95

    # ㄱ자형: 경로에서 뚜렷한 직각 꺾임 (수평→수직 또는 수직→수평)
    l_score = _detect_l_shape(coords)
    scores['L_shape'] = l_score

    # 지그재그형: 열 방향이 번갈아 변함 (좌→우→좌 반복)
    zigzag_score = _detect_zigzag(coords)
    scores['zigzag'] = zigzag_score

    # 균형형: 행/열 엔트로피 모두 높고 특별한 패턴 없음
    balance = (features['row_entropy'] + features['col_entropy']) / 2.0
    other_max = max(scores.get('dense', 0), scores.get('horizontal', 0),
                    scores.get('vertical', 0), scores.get('diagonal', 0))
    scores['balanced'] = balance * (1.0 - other_max * 0.5)

    # 최고 점수 유형 선택
    best_type = max(scores, key=scores.get)
    best_score = scores[best_type]

    # 신뢰도: 최고 점수와 2번째 점수의 차이
    sorted_scores = sorted(scores.values(), reverse=True)
    gap = sorted_scores[0] - sorted_scores[1] if len(sorted_scores) > 1 else sorted_scores[0]
    confidence = min(1.0, best_score * 0.6 + gap * 0.4)

    return {
        'type': best_type,
        'type_name': PATTERN_TYPES.get(best_type, best_type),
        'confidence': round(confidence, 3),
        'sub_scores': {k: round(v, 3) for k, v in scores.items()},
    }



# ═══════════════════════════════════════════════════════════════════════
# 3. 무게중심 이동 추세 분석
# ═══════════════════════════════════════════════════════════════════════

class PatternStructureAnalyzer:
    """역대 당첨번호의 구조적 패턴을 분석하고 추세를 예측합니다.

    Args:
        historical_data: CSV에서 로드한 당첨번호 dict 리스트
    """

    def __init__(self, historical_data: List[Dict]):
        self.historical_data = historical_data
        self._draws: List[List[int]] = []
        self._features_cache: List[Dict] = []
        self._centroids: List[Tuple[float, float]] = []
        self._pattern_types: List[str] = []
        self._is_analyzed = False
        self._prepare_data()

    def _prepare_data(self):
        """데이터를 정렬하고 회차별 번호를 추출합니다."""
        rows = sorted(self.historical_data,
                      key=lambda x: int(x.get('round', 0) or 0))
        for row in rows:
            nums = []
            for col in LOTTO_NUMBER_COLUMNS:
                try:
                    n = int(row.get(col, 0))
                    if 1 <= n <= MAX_LOTTO_NUMBER:
                        nums.append(n)
                except (ValueError, TypeError):
                    continue
            if len(nums) == 6:
                self._draws.append(nums)

    def analyze(self) -> None:
        """전체 회차의 구조적 특성을 분석합니다."""
        if self._is_analyzed:
            return

        for draw in self._draws:
            features = compute_structural_features(draw)
            self._features_cache.append(features)
            self._centroids.append((features['centroid_row'],
                                    features['centroid_col']))
            ptype = classify_pattern(draw)
            self._pattern_types.append(ptype['type'])

        self._is_analyzed = True
        _log.info("패턴 구조 분석 완료: %d회차", len(self._draws))


    def get_centroid_trend(self, window: int = 10) -> Dict:
        """최근 N회차의 무게중심 이동 추세를 분석합니다.

        Returns:
            {
                'recent_centroids': 최근 N개 무게중심 좌표,
                'velocity_row': 행 방향 이동 속도 (양수=아래, 음수=위),
                'velocity_col': 열 방향 이동 속도 (양수=오른쪽, 음수=왼쪽),
                'predicted_centroid': 다음 회차 예상 무게중심,
                'predicted_region': 예상 구역 (상/중/하 × 좌/중/우),
                'trend_strength': 추세 강도 (0~1),
            }
        """
        self.analyze()

        if len(self._centroids) < 3:
            return {'recent_centroids': [], 'velocity_row': 0,
                    'velocity_col': 0, 'predicted_centroid': (3.0, 3.0),
                    'predicted_region': '중앙', 'trend_strength': 0.0}

        recent = self._centroids[-window:]
        n = len(recent)

        # 선형 회귀로 이동 속도 계산
        x = np.arange(n)
        rows_arr = np.array([c[0] for c in recent])
        cols_arr = np.array([c[1] for c in recent])

        # 행 방향 속도
        if n > 1:
            row_slope = float(np.polyfit(x, rows_arr, 1)[0])
            col_slope = float(np.polyfit(x, cols_arr, 1)[0])
        else:
            row_slope = 0.0
            col_slope = 0.0

        # 다음 무게중심 예측 (선형 외삽)
        pred_row = float(rows_arr[-1] + row_slope)
        pred_col = float(cols_arr[-1] + col_slope)
        # 그리드 범위로 클리핑
        pred_row = max(0.0, min(6.0, pred_row))
        pred_col = max(0.0, min(6.0, pred_col))

        # 예상 구역 결정
        region = self._get_region_name(pred_row, pred_col)

        # 추세 강도: R² 값으로 측정
        if n > 2:
            row_residuals = rows_arr - np.polyval(np.polyfit(x, rows_arr, 1), x)
            col_residuals = cols_arr - np.polyval(np.polyfit(x, cols_arr, 1), x)
            row_r2 = 1.0 - (np.var(row_residuals) / max(0.001, np.var(rows_arr)))
            col_r2 = 1.0 - (np.var(col_residuals) / max(0.001, np.var(cols_arr)))
            strength = max(0.0, (row_r2 + col_r2) / 2.0)
        else:
            strength = 0.0

        return {
            'recent_centroids': [(round(r, 2), round(c, 2)) for r, c in recent],
            'velocity_row': round(row_slope, 4),
            'velocity_col': round(col_slope, 4),
            'predicted_centroid': (round(pred_row, 2), round(pred_col, 2)),
            'predicted_region': region,
            'trend_strength': round(min(1.0, strength), 3),
        }

    @staticmethod
    def _get_region_name(row: float, col: float) -> str:
        """무게중심 좌표를 구역명으로 변환합니다."""
        # 행: 상(0~2) / 중(2~4) / 하(4~6)
        if row < 2.0:
            v = '상단'
        elif row < 4.5:
            v = '중단'
        else:
            v = '하단'
        # 열: 좌(0~2) / 중(2~5) / 우(5~7)
        if col < 2.0:
            h = '좌측'
        elif col < 5.0:
            h = '중앙'
        else:
            h = '우측'
        return f'{v} {h}'


    def get_pattern_type_statistics(self) -> Dict:
        """역사적 패턴 유형별 출현 빈도 통계를 반환합니다.

        Returns:
            {
                'type_counts': {유형: 횟수},
                'type_percentages': {유형: 비율},
                'recent_types': 최근 10회 유형 리스트,
                'next_likely_type': 다음 회차 예상 유형,
                'transition_probs': 유형 간 전이 확률,
            }
        """
        self.analyze()

        if not self._pattern_types:
            return {}

        # 전체 빈도
        counter = Counter(self._pattern_types)
        total = len(self._pattern_types)
        type_counts = dict(counter.most_common())
        type_percentages = {k: round(v / total * 100, 1)
                           for k, v in type_counts.items()}

        # 최근 10회 유형
        recent = self._pattern_types[-10:]

        # 유형 간 전이 확률 (마르코프 1차)
        transitions = defaultdict(Counter)
        for i in range(len(self._pattern_types) - 1):
            curr = self._pattern_types[i]
            nxt = self._pattern_types[i + 1]
            transitions[curr][nxt] += 1

        # 전이 확률 정규화
        transition_probs = {}
        for curr_type, next_counts in transitions.items():
            total_from = sum(next_counts.values())
            transition_probs[curr_type] = {
                nxt: round(cnt / total_from, 3)
                for nxt, cnt in next_counts.most_common(5)
            }

        # 다음 예상 유형: 마지막 유형에서 전이 확률 기반
        last_type = self._pattern_types[-1] if self._pattern_types else 'balanced'
        if last_type in transition_probs:
            next_likely = max(transition_probs[last_type],
                             key=transition_probs[last_type].get)
        else:
            next_likely = counter.most_common(1)[0][0]

        return {
            'type_counts': type_counts,
            'type_percentages': type_percentages,
            'recent_types': [(PATTERN_TYPES.get(t, t)) for t in recent],
            'last_type': PATTERN_TYPES.get(last_type, last_type),
            'next_likely_type': PATTERN_TYPES.get(next_likely, next_likely),
            'next_likely_key': next_likely,
            'transition_probs': transition_probs,
        }


    def get_region_preference_scores(self, window: int = 30) -> np.ndarray:
        """다음 회차에 유리한 그리드 구역별 선호도 점수를 반환합니다.

        무게중심 추세 + 패턴 유형 전이를 결합하여
        1~45 각 번호의 구조적 선호도 점수를 계산합니다.

        Returns:
            shape=(45,) 정규화된 선호도 점수 벡터
        """
        self.analyze()

        scores = np.ones(MAX_LOTTO_NUMBER, dtype=np.float64)

        # 1. 무게중심 추세 기반 구역 선호도
        trend = self.get_centroid_trend(window)
        pred_row, pred_col = trend['predicted_centroid']
        strength = trend['trend_strength']

        for num in range(1, MAX_LOTTO_NUMBER + 1):
            row, col = number_to_grid(num)
            # 예상 무게중심과의 거리 기반 점수
            dist = math.sqrt((row - pred_row)**2 + (col - pred_col)**2)
            # 가까울수록 높은 점수 (가우시안 형태)
            proximity_score = math.exp(-dist**2 / 8.0)
            # 추세 강도에 비례하여 적용
            scores[num - 1] *= (1.0 + proximity_score * strength * 0.5)

        # 2. 패턴 유형 전이 기반 구조 선호도
        stats = self.get_pattern_type_statistics()
        next_type = stats.get('next_likely_key', 'balanced')

        # 유형별 구조 특성에 맞는 번호 부스트
        if next_type == 'dense':
            # 밀집형: 중앙 구역 번호 선호
            for num in range(1, MAX_LOTTO_NUMBER + 1):
                r, c = number_to_grid(num)
                if 2 <= r <= 4 and 2 <= c <= 4:
                    scores[num - 1] *= 1.2
        elif next_type == 'dispersed':
            # 분산형: 모서리/가장자리 번호 선호
            for num in range(1, MAX_LOTTO_NUMBER + 1):
                r, c = number_to_grid(num)
                if r in (0, 6) or c in (0, 6):
                    scores[num - 1] *= 1.15
        elif next_type == 'horizontal':
            # 수평형: 예상 무게중심 행 근처 번호 선호
            target_row = int(round(pred_row))
            for num in range(1, MAX_LOTTO_NUMBER + 1):
                r, _ = number_to_grid(num)
                if abs(r - target_row) <= 1:
                    scores[num - 1] *= 1.2
        elif next_type == 'vertical':
            # 수직형: 예상 무게중심 열 근처 번호 선호
            target_col = int(round(pred_col))
            for num in range(1, MAX_LOTTO_NUMBER + 1):
                _, c = number_to_grid(num)
                if abs(c - target_col) <= 1:
                    scores[num - 1] *= 1.2

        # 정규화
        total = scores.sum()
        if total > 0:
            scores /= total

        return scores

    def get_draw_analysis(self, round_idx: int = -1) -> Dict:
        """특정 회차의 상세 구조 분석을 반환합니다."""
        self.analyze()

        if not self._draws:
            return {}

        idx = round_idx if round_idx >= 0 else len(self._draws) + round_idx
        if idx < 0 or idx >= len(self._draws):
            return {}

        draw = self._draws[idx]
        features = self._features_cache[idx]
        pattern = classify_pattern(draw)

        return {
            'numbers': draw,
            'features': features,
            'pattern': pattern,
            'centroid': self._centroids[idx],
        }

    def get_summary_report(self) -> Dict:
        """전체 분석 요약 리포트를 반환합니다."""
        self.analyze()

        return {
            'total_draws': len(self._draws),
            'latest_draw': self.get_draw_analysis(-1),
            'centroid_trend': self.get_centroid_trend(10),
            'pattern_statistics': self.get_pattern_type_statistics(),
        }

    def predict_next_numbers(self, num_sets: int = 5,
                             exclude_numbers: Optional[set] = None
                             ) -> List[Dict]:
        """다음 예상 유형에 맞춰 번호를 추천하고 구조 분석 결과를 포함합니다.

        구역 선호도 점수 기반으로 번호를 샘플링하되,
        생성된 조합이 예상 패턴 유형에 부합하는지 검증합니다.

        Returns:
            [{'numbers': [...], 'pattern_type': str, 'score': float,
              'features': {...}, 'confidence': float}, ...]
        """
        self.analyze()

        if not self._draws:
            return []

        exclude = exclude_numbers or set()
        scores = self.get_region_preference_scores(30)

        # 제외 번호 처리
        for n in exclude:
            if 1 <= n <= MAX_LOTTO_NUMBER:
                scores[n - 1] = 0.0

        # 직전 회차 번호 2개 이상 겹침 제외를 위해
        last_draw = set(self._draws[-1]) if self._draws else set()

        # 예상 유형
        stats = self.get_pattern_type_statistics()
        target_type = stats.get('next_likely_key', 'balanced')
        target_type_name = PATTERN_TYPES.get(target_type, target_type)

        # 정규화
        total = scores.sum()
        if total <= 0:
            return []
        probs = scores / total

        rng = np.random.default_rng()
        results = []
        seen = set()
        max_attempts = num_sets * 3000

        for _ in range(max_attempts):
            if len(results) >= num_sets:
                break

            chosen = rng.choice(MAX_LOTTO_NUMBER, size=6, replace=False, p=probs)
            nums = sorted((chosen + 1).tolist())
            key = tuple(nums)

            if key in seen:
                continue
            seen.add(key)

            # 직전 회차와 2개 이상 겹침 제외
            if len(set(nums) & last_draw) >= 2:
                continue

            # 합계 범위 필터
            total_sum = sum(nums)
            if not (100 <= total_sum <= 180):
                continue

            # 패턴 유형 분류
            pattern = classify_pattern(nums)
            features = compute_structural_features(nums)

            # 예상 유형과 일치하거나 점수가 높은 조합 우선
            type_match = 1.0 if pattern['type'] == target_type else 0.3
            region_score = sum(scores[n - 1] for n in nums)
            combo_score = type_match * 0.6 + region_score * 0.4

            results.append({
                'numbers': nums,
                'pattern_type': pattern['type_name'],
                'pattern_key': pattern['type'],
                'score': round(float(combo_score), 4),
                'confidence': pattern['confidence'],
                'features': features,
                'type_match': pattern['type'] == target_type,
            })

        # 점수 내림차순 정렬 (유형 일치 우선)
        results.sort(key=lambda x: (x['type_match'], x['score']), reverse=True)

        # 다양성 필터: 너무 비슷한 조합 제거
        filtered = []
        for r in results:
            if len(filtered) >= num_sets:
                break
            ns = set(r['numbers'])
            if all(len(ns & set(f['numbers'])) <= 3 for f in filtered):
                filtered.append(r)

        _log.info("패턴 기반 추천 완료: %d개 조합 (예상 유형: %s)",
                  len(filtered), target_type_name)
        return filtered
