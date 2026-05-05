#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
로또 패턴 그룹핑 분석기 모듈
"""

import random
import pickle
from collections import Counter
from typing import List, Dict, Optional, Set, Tuple, Any

# 상수 import
from utils.constants import *
from utils.helpers import normalize_exclude_numbers
from utils.logging_config import get_logger

_log = get_logger(__name__)

# AI 패턴 학습을 위한 추가 라이브러리
try:
    import numpy as np
    from sklearn.cluster import KMeans
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import accuracy_score
    AI_PATTERN_AVAILABLE = True
except ImportError:
    AI_PATTERN_AVAILABLE = False


class LottoPatternGrouping:
    """로또 당첨번호 그룹핑 및 패턴 분석 클래스"""
    
    def __init__(self, historical_data):
        self.historical_data = historical_data
        self.grouped_patterns = {}
        self.pattern_features = {}
        self.cluster_models = {}
        self.ai_models = {}
        self.scalers = {}
        
    def create_round_groups(self, group_size=5):
        """회차를 그룹으로 나누어 패턴을 분석합니다."""
        _log.info("회차 그룹핑 분석 (그룹 크기: %d)", group_size)
        
        groups = []
        for i in range(0, len(self.historical_data), group_size):
            group_data = self.historical_data[i:i+group_size]
            if len(group_data) >= 3:  # 최소 3회차 이상
                try:
                    start_round = group_data[0].get('회차', '알 수 없음')
                    end_round = group_data[-1].get('회차', '알 수 없음')
                    
                    groups.append({
                        'start_round': start_round,
                        'end_round': end_round,
                        'data': group_data,
                        'patterns': self._extract_group_patterns(group_data)
                    })
                except Exception as e:
                    _log.warning("그룹 %d 처리 중 오류: %s", i//group_size + 1, e)
                    continue

        if not groups:
            _log.warning("유효한 그룹을 생성할 수 없습니다.")
            return None

        _log.info("총 %d개의 그룹이 생성되었습니다.", len(groups))

        # 각 그룹의 패턴 분석
        for i, group in enumerate(groups):
            try:
                patterns = group['patterns']
                if patterns:
                    _log.debug("그룹 %d: %s회 ~ %s회 | 번호 빈도 TOP 5: %s | 홀짝 비율: %s | 평균 합계: %.1f | 연속번호 패턴: %s",
                               i+1, group['start_round'], group['end_round'],
                               patterns.get('top_frequency', [])[:5],
                               patterns.get('odd_even_ratio', 'N/A'),
                               patterns.get('avg_sum', 0),
                               patterns.get('consecutive_patterns', []))
            except Exception as e:
                _log.warning("그룹 %d 패턴 출력 중 오류: %s", i+1, e)
                continue
        
        self.grouped_patterns = groups
        return groups
    
    def _extract_group_patterns(self, group_data):
        """그룹 데이터에서 패턴을 추출합니다."""
        try:
            all_numbers = []
            odd_even_counts = {'odd': 0, 'even': 0}
            sums = []
            consecutive_patterns = []
            
            for row in group_data:
                try:
                    numbers = []
                    for col in LOTTO_NUMBER_COLUMNS:
                        if col in row and row[col]:
                            try:
                                numbers.append(int(row[col]))
                            except (ValueError, TypeError):
                                continue
                    
                    if len(numbers) != 6:  # 유효한 번호가 6개가 아니면 건너뛰기
                        continue
                        
                    all_numbers.extend(numbers)
                    
                    # 홀짝 카운트
                    odd_count = sum(1 for n in numbers if n % 2 == 1)
                    even_count = len(numbers) - odd_count
                    odd_even_counts['odd'] += odd_count
                    odd_even_counts['even'] += even_count
                    
                    # 합계
                    sums.append(sum(numbers))
                    
                    # 연속번호 패턴
                    sorted_numbers = sorted(numbers)
                    consecutive_count = 0
                    max_consecutive = 0
                    for j in range(len(sorted_numbers) - 1):
                        if sorted_numbers[j+1] - sorted_numbers[j] == 1:
                            consecutive_count += 1
                            max_consecutive = max(max_consecutive, consecutive_count)
                        else:
                            consecutive_count = 0
                    consecutive_patterns.append(max_consecutive)
                    
                except Exception as e:
                    _log.warning("행 처리 중 오류: %s", e)
                    continue

            if not all_numbers:
                _log.warning("유효한 번호를 추출할 수 없습니다.")
                return None
                
            # 번호별 빈도
            frequency = Counter(all_numbers)
            top_frequency = frequency.most_common(10)
            
            return {
                'top_frequency': top_frequency,
                'odd_even_ratio': f"{odd_even_counts['odd']}:{odd_even_counts['even']}",
                'avg_sum': sum(sums) / len(sums) if sums else 0,
                'consecutive_patterns': consecutive_patterns,
                'frequency_distribution': dict(frequency),
                'sum_range': {'min': min(sums) if sums else 0, 'max': max(sums) if sums else 0, 'avg': sum(sums) / len(sums) if sums else 0}
            }
            
        except Exception as e:
            _log.warning("패턴 추출 중 오류: %s", e)
            return None
    
    def create_pattern_features(self):
        """그룹 패턴을 AI 학습용 특성으로 변환합니다."""
        if not self.grouped_patterns:
            _log.warning("먼저 회차 그룹핑을 수행해주세요.")
            return None

        if not AI_PATTERN_AVAILABLE:
            _log.warning("AI 패턴 학습에 필요한 라이브러리가 설치되지 않았습니다.")
            return None

        _log.info("AI 학습용 특성 생성 중... (그룹 수: %d)", len(self.grouped_patterns))
        
        features = []
        labels = []
        
        for i, group in enumerate(self.grouped_patterns):
            try:
                patterns = group['patterns']
                
                # 특성 벡터 생성
                feature_vector = []
                
                # 1. 번호별 빈도 특성 (45개)
                freq_dist = patterns['frequency_distribution']
                for num in range(1, MAX_LOTTO_NUMBER + 1):
                    feature_vector.append(freq_dist.get(num, 0))
                
                # 2. 홀짝 비율 특성 (2개)
                odd_even = patterns['odd_even_ratio'].split(':')
                feature_vector.append(int(odd_even[0]))
                feature_vector.append(int(odd_even[1]))
            except Exception as e:
                _log.warning("그룹 %d 처리 중 오류: %s | 패턴 데이터: %s", i+1, e, patterns)
                continue
            
            try:
                # 3. 합계 통계 특성 (3개)
                sum_range = patterns['sum_range']
                feature_vector.extend([sum_range['min'], sum_range['max'], sum_range['avg']])
                
                # 4. 연속번호 패턴 특성 (5개)
                consecutive = patterns['consecutive_patterns']
                feature_vector.extend([
                    sum(consecutive) / len(consecutive),  # 평균
                    max(consecutive),  # 최대
                    min(consecutive),  # 최소
                    len([c for c in consecutive if c > 0]),  # 연속번호 있는 회차 수
                    len([c for c in consecutive if c >= 2])   # 2개 이상 연속인 회차 수
                ])
                
                # 5. 구간별 분포 특성 (5개)
                section_dist = [0] * 5
                for num, freq in freq_dist.items():
                    section = (num - 1) // 10
                    if section < 5:
                        section_dist[section] += freq
                feature_vector.extend(section_dist)
                
                features.append(feature_vector)

                # 레이블: 현재 그룹 상위 빈도 번호가 다음 그룹에서 출현하는 비율로 결정
                # (무작위 레이블 대신 실제 데이터 기반 레이블 사용)
                if i + 1 < len(self.grouped_patterns):
                    next_nums: set = set()
                    for _row in self.grouped_patterns[i + 1]['data']:
                        for _col in [f'번호{_j}' for _j in range(1, 7)]:
                            if _col in _row and _row[_col]:
                                try:
                                    next_nums.add(int(_row[_col]))
                                except (ValueError, TypeError):
                                    pass
                    top_nums = set(num for num, _ in patterns['top_frequency'][:10])
                    overlap = len(top_nums & next_nums)
                    # 기댓값: 상위 10개 번호 중 약 6~7개가 다음 그룹에 출현 (무작위 기준)
                    # 겹침 수가 기댓값 이상이면 패턴 지속 → 레이블 1
                    expected_overlap = round(len(top_nums) * len(next_nums) / 45)
                    labels.append(1 if overlap >= max(expected_overlap, 4) else 0)
                else:
                    # 마지막 그룹은 비교 대상 없음 → 기본값 0
                    labels.append(0)
            except Exception as e:
                _log.warning("그룹 %d 특성 생성 중 오류: %s", i+1, e)
                continue

        if not features:
            _log.warning("생성된 특성 벡터가 없습니다.")
            return None

        self.pattern_features = {
            'features': np.array(features),
            'labels': np.array(labels),
            'feature_names': self._get_feature_names()
        }

        _log.info("%d개의 특성 벡터가 생성되었습니다. (특성 차원: %d개)", len(features), len(features[0]))
        
        return self.pattern_features
    
    def _get_feature_names(self):
        """특성 이름 목록을 반환합니다."""
        names = []
        
        # 번호별 빈도
        for i in range(1, MAX_LOTTO_NUMBER + 1):
            names.append(f"freq_{i}")
        
        # 홀짝 비율
        names.extend(['odd_count', 'even_count'])
        
        # 합계 통계
        names.extend(['sum_min', 'sum_max', 'sum_avg'])
        
        # 연속번호 패턴
        names.extend(['consec_avg', 'consec_max', 'consec_min', 'consec_count', 'consec_count_2plus'])
        
        # 구간별 분포
        names.extend(['section_1_10', 'section_11_20', 'section_21_30', 'section_31_40', 'section_41_45'])
        
        return names
    
    def perform_clustering(self, n_clusters=5):
        """그룹 패턴을 클러스터링합니다."""
        if not self.pattern_features:
            _log.warning("먼저 특성을 생성해주세요.")
            return None

        if not AI_PATTERN_AVAILABLE:
            _log.warning("AI 패턴 학습에 필요한 라이브러리가 설치되지 않았습니다.")
            return None

        _log.info("패턴 클러스터링 (클러스터 수: %d)", n_clusters)
        
        features = self.pattern_features['features']
        
        # 특성 정규화
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features)
        
        # K-means 클러스터링
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(features_scaled)
        
        # 클러스터별 특성 분석
        cluster_analysis = {}
        for i in range(n_clusters):
            cluster_indices = np.where(cluster_labels == i)[0]
            cluster_groups = [self.grouped_patterns[idx] for idx in cluster_indices]
            
            cluster_analysis[i] = {
                'size': len(cluster_indices),
                'groups': cluster_groups,
                'patterns': self._analyze_cluster_patterns(cluster_groups)
            }
        
        self.cluster_models['kmeans'] = {
            'model': kmeans,
            'scaler': scaler,
            'labels': cluster_labels,
            'analysis': cluster_analysis
        }
        
        # 클러스터 분석 결과 출력
        _log.info("%d개의 클러스터가 생성되었습니다.", n_clusters)
        for i in range(n_clusters):
            analysis = cluster_analysis[i]
            patterns = analysis['patterns']
            _log.info("클러스터 %d (%d개 그룹): 평균 홀짝 비율=%s, 평균 합계=%.1f, 주요 번호=%s",
                      i+1, analysis['size'], patterns['avg_odd_even'],
                      patterns['avg_sum'], patterns['top_numbers'][:5])
        
        return self.cluster_models['kmeans']
    
    def _analyze_cluster_patterns(self, cluster_groups):
        """클러스터의 패턴을 분석합니다."""
        all_numbers = []
        odd_counts = []
        even_counts = []
        sums = []
        
        for group in cluster_groups:
            patterns = group['patterns']
            freq_dist = patterns['frequency_distribution']
            all_numbers.extend([num for num, freq in freq_dist.items() for _ in range(freq)])
            
            odd_even = patterns['odd_even_ratio'].split(':')
            odd_counts.append(int(odd_even[0]))
            even_counts.append(int(odd_even[1]))
            
            sums.append(patterns['sum_range']['avg'])
        
        # 번호별 빈도
        frequency = Counter(all_numbers)
        top_numbers = frequency.most_common(10)
        
        return {
            'avg_odd_even': f"{sum(odd_counts)/len(odd_counts):.1f}:{sum(even_counts)/len(even_counts):.1f}",
            'avg_sum': sum(sums) / len(sums),
            'top_numbers': [num for num, _ in top_numbers]
        }
    
    def train_ai_models(self):
        """AI 모델들을 훈련합니다."""
        if not self.pattern_features:
            _log.warning("먼저 특성을 생성해주세요.")
            return None

        if not AI_PATTERN_AVAILABLE:
            _log.warning("AI 패턴 학습에 필요한 라이브러리가 설치되지 않았습니다.")
            return None

        _log.info("AI 모델 훈련 중...")
        
        features = self.pattern_features['features']
        labels = self.pattern_features['labels']
        
        # 데이터 분할
        X_train, X_test, y_train, y_test = train_test_split(
            features, labels, test_size=0.2, random_state=42
        )
        
        # 특성 정규화
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # 모델들 정의
        models = {
            'RandomForest': RandomForestClassifier(n_estimators=100, random_state=42),
            'GradientBoosting': GradientBoostingClassifier(n_estimators=100, random_state=42)
        }
        
        # 모델 훈련 및 평가
        for name, model in models.items():
            _log.info("%s 모델 훈련 중...", name)

            # 훈련
            model.fit(X_train_scaled, y_train)

            # 예측
            y_pred = model.predict(X_test_scaled)
            accuracy = accuracy_score(y_test, y_pred)

            # 교차 검증
            cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=5)

            _log.info("%s: 테스트 정확도=%.3f, 교차 검증 정확도=%.3f (+/- %.3f)",
                      name, accuracy, cv_scores.mean(), cv_scores.std() * 2)
            
            # 모델 저장
            self.ai_models[name] = {
                'model': model,
                'scaler': scaler,
                'accuracy': accuracy,
                'cv_scores': cv_scores
            }
        
        _log.info("%d개의 AI 모델이 훈련되었습니다.", len(models))
        return self.ai_models
    
    def predict_high_probability_combinations(self, exclude_numbers=None, num_combinations=10):
        """AI 모델을 사용하여 높은 확률의 조합을 예측합니다."""
        if not self.ai_models:
            _log.warning("먼저 AI 모델을 훈련해주세요.")
            return []
        
        exclude_numbers = normalize_exclude_numbers(exclude_numbers)
        _log.info("AI 기반 높은 확률 조합 예측 (예측 개수: %d)", num_combinations)
        
        # 최근 패턴을 기반으로 특성 벡터 생성
        recent_groups = self.grouped_patterns[-3:]  # 최근 3개 그룹
        recent_patterns = self._extract_group_patterns([row for group in recent_groups for row in group['data']])
        
        # 특성 벡터 생성
        feature_vector = self._create_feature_vector(recent_patterns)
        
        # AI 모델들의 예측 확률 계산
        predictions = {}
        for name, model_info in self.ai_models.items():
            model = model_info['model']
            scaler = model_info['scaler']
            
            # 특성 정규화
            feature_scaled = scaler.transform([feature_vector])
            
            # 예측 확률
            if hasattr(model, 'predict_proba'):
                proba = model.predict_proba(feature_scaled)[0]
                predictions[name] = proba[1]  # 성공 확률
            else:
                predictions[name] = model.predict(feature_scaled)[0]
        
        # 평균 확률 계산
        avg_probability = sum(predictions.values()) / len(predictions)
        
        _log.info("AI 모델 예측 확률: 평균=%.3f", avg_probability)
        for name, prob in predictions.items():
            _log.debug("  %s: %.3f", name, prob)
        
        # 높은 확률을 기반으로 번호 조합 생성
        high_prob_combinations = self._generate_high_probability_combinations(
            avg_probability, exclude_numbers, num_combinations
        )
        
        return high_prob_combinations
    
    def _create_feature_vector(self, patterns):
        """패턴에서 특성 벡터를 생성합니다."""
        feature_vector = []
        
        # 번호별 빈도 특성 (45개)
        freq_dist = patterns['frequency_distribution']
        for num in range(1, MAX_LOTTO_NUMBER + 1):
            feature_vector.append(freq_dist.get(num, 0))
        
        # 홀짝 비율 특성 (2개)
        odd_even = patterns['odd_even_ratio'].split(':')
        feature_vector.append(int(odd_even[0]))
        feature_vector.append(int(odd_even[1]))
        
        # 합계 통계 특성 (3개)
        sum_range = patterns['sum_range']
        feature_vector.extend([sum_range['min'], sum_range['max'], sum_range['avg']])
        
        # 연속번호 패턴 특성 (5개)
        consecutive = patterns['consecutive_patterns']
        feature_vector.extend([
            sum(consecutive) / len(consecutive),
            max(consecutive),
            min(consecutive),
            len([c for c in consecutive if c > 0]),
            len([c for c in consecutive if c >= 2])
        ])
        
        # 구간별 분포 특성 (5개)
        section_dist = [0] * 5
        for num, freq in freq_dist.items():
            section = (num - 1) // 10
            if section < 5:
                section_dist[section] += freq
        feature_vector.extend(section_dist)
        
        return feature_vector
    
    def _generate_high_probability_combinations(self, probability, exclude_numbers, num_combinations):
        """높은 확률을 기반으로 번호 조합을 생성합니다."""
        combinations = []
        attempts = 0
        max_attempts = num_combinations * 1000
        
        # 확률에 따른 가중치 조정
        if probability > 0.7:
            # 높은 확률: 보수적인 패턴
            weight_factor = 0.8
            max_consecutive = 2
        elif probability > 0.5:
            # 중간 확률: 균형잡힌 패턴
            weight_factor = 1.0
            max_consecutive = 3
        else:
            # 낮은 확률: 공격적인 패턴
            weight_factor = 1.2
            max_consecutive = 4
        
        _log.info("확률 기반 생성 파라미터: 가중치 계수=%.1f, 최대 연속번호=%d", weight_factor, max_consecutive)
        
        while len(combinations) < num_combinations and attempts < max_attempts:
            attempts += 1
            
            # 클러스터 기반 번호 선택
            if self.cluster_models and 'kmeans' in self.cluster_models:
                numbers = self._select_numbers_from_clusters(exclude_numbers, weight_factor)
            else:
                numbers = self._select_numbers_random(exclude_numbers, weight_factor)
            
            if not numbers:
                continue
            
            # 연속번호 검사
            consecutive_count = self._check_consecutive_numbers(numbers)
            if consecutive_count > max_consecutive:
                continue
            
            # 중복 검사
            numbers_tuple = tuple(sorted(numbers))
            if any(tuple(sorted(comb['numbers'])) == numbers_tuple for comb in combinations):
                continue
            
            # 조합 정보 생성
            combination_info = {
                'numbers': sorted(numbers),
                'probability': probability,
                'consecutive_count': consecutive_count,
                'method': 'AI 패턴 학습',
                'cluster_info': self._get_cluster_info(numbers) if self.cluster_models else None
            }
            
            combinations.append(combination_info)
            _log.debug("  %d번째 조합 생성: %s", len(combinations), combination_info['numbers'])

        _log.info("%d개의 높은 확률 조합이 생성되었습니다.", len(combinations))
        return combinations
    
    def _select_numbers_from_clusters(self, exclude_numbers, weight_factor):
        """클러스터 정보를 기반으로 번호를 선택합니다."""
        exclude_numbers = normalize_exclude_numbers(exclude_numbers)
        available_numbers = [n for n in range(1, MAX_LOTTO_NUMBER + 1) if n not in exclude_numbers]
        if len(available_numbers) < 6:
            return None
        
        # 클러스터별 번호 가중치 계산
        cluster_weights = {}
        for cluster_id, cluster_info in self.cluster_models['kmeans']['analysis'].items():
            patterns = cluster_info['patterns']
            for num in patterns['top_numbers']:
                if num in available_numbers:
                    cluster_weights[num] = cluster_weights.get(num, 0) + 1
        
        # 가중치 기반 선택
        weights = []
        for num in available_numbers:
            weight = cluster_weights.get(num, 1) * weight_factor
            weights.append(max(0.1, weight))
        
        try:
            # available_numbers가 시퀀스인지 확인하고 변환
            if isinstance(available_numbers, dict):
                available_numbers = sorted(available_numbers)
            elif isinstance(available_numbers, set):
                available_numbers = list(available_numbers)
            
            # available_numbers와 weights의 길이가 일치하는지 확인
            if len(available_numbers) != len(weights):
                weights = weights[:len(available_numbers)]
            
            selected = random.choices(available_numbers, weights=weights, k=6)
            return list(set(selected)) if len(set(selected)) == 6 else None
        except (ValueError, IndexError):
            return None
    
    def _select_numbers_random(self, exclude_numbers, weight_factor):
        """랜덤하게 번호를 선택합니다."""
        exclude_numbers = normalize_exclude_numbers(exclude_numbers)
        available_numbers = [n for n in range(1, MAX_LOTTO_NUMBER + 1) if n not in exclude_numbers]
        if len(available_numbers) < 6:
            return None
        
        try:
            # available_numbers가 시퀀스인지 확인하고 변환
            if isinstance(available_numbers, dict):
                available_numbers = sorted(available_numbers)
            elif isinstance(available_numbers, set):
                available_numbers = list(available_numbers)
            
            selected = random.sample(available_numbers, 6)
            return sorted(selected)
        except (ValueError, IndexError):
            return None
    
    def _check_consecutive_numbers(self, numbers):
        """연속 번호 개수를 확인합니다."""
        numbers = sorted(numbers)
        consecutive_count = 0
        max_consecutive = 0
        
        for i in range(len(numbers) - 1):
            if numbers[i+1] - numbers[i] == 1:
                consecutive_count += 1
                max_consecutive = max(max_consecutive, consecutive_count)
            else:
                consecutive_count = 0
        
        return max_consecutive
    
    def _get_cluster_info(self, numbers):
        """번호 조합의 클러스터 정보를 반환합니다."""
        if not self.cluster_models or 'kmeans' not in self.cluster_models:
            return None
        
        # 각 클러스터와의 유사도 계산
        cluster_similarities = {}
        for cluster_id, cluster_info in self.cluster_models['kmeans']['analysis'].items():
            patterns = cluster_info['patterns']
            top_numbers = set(patterns['top_numbers'])
            overlap = len(set(numbers) & top_numbers)
            cluster_similarities[cluster_id] = overlap / len(numbers)
        
        # 가장 유사한 클러스터 찾기
        best_cluster = max(cluster_similarities.items(), key=lambda x: x[1])
        
        return {
            'best_cluster': best_cluster[0],
            'similarity': best_cluster[1],
            'all_similarities': cluster_similarities
        }
    
    def find_common_numbers(self, combinations):
        """여러 조합에서 공통으로 나타나는 번호들을 찾습니다."""
        if not combinations or len(combinations) < 2:
            return []
        
        # 모든 조합의 번호들을 수집
        all_numbers = []
        for comb in combinations:
            if 'numbers' in comb:
                all_numbers.extend(comb['numbers'])
        
        # 번호별 출현 횟수 계산
        number_counts = {}
        for num in all_numbers:
            number_counts[num] = number_counts.get(num, 0) + 1
        
        # 전체 조합 수
        total_combinations = len(combinations)
        
        # 공통 번호 찾기 (모든 조합에 나타나는 번호)
        common_numbers = []
        for num, count in number_counts.items():
            if count == total_combinations:
                common_numbers.append(num)
        
        # 자주 나타나는 번호들 (50% 이상의 조합에 나타나는 번호)
        frequent_numbers = []
        for num, count in number_counts.items():
            frequency = count / total_combinations
            if frequency >= 0.5 and num not in common_numbers:
                frequent_numbers.append((num, frequency))
        
        # 빈도순으로 정렬
        frequent_numbers.sort(key=lambda x: x[1], reverse=True)
        
        return {
            'common_numbers': sorted(common_numbers),  # 모든 조합에 나타나는 번호
            'frequent_numbers': frequent_numbers,      # 자주 나타나는 번호들
            'total_combinations': total_combinations,
            'number_counts': number_counts
        }
    
    def save_models(self, filepath='ai_pattern_models.pkl'):
        """훈련된 모델들을 파일로 저장합니다."""
        if not self.ai_models:
            _log.warning("저장할 모델이 없습니다.")
            return False

        try:
            model_data = {
                'ai_models': self.ai_models,
                'cluster_models': self.cluster_models,
                'pattern_features': self.pattern_features,
                'grouped_patterns': self.grouped_patterns
            }

            with open(filepath, 'wb') as f:
                pickle.dump(model_data, f)

            _log.info("AI 모델들이 %s에 저장되었습니다.", filepath)
            return True
        except Exception as e:
            _log.error("모델 저장 실패: %s", e)
            return False
    
    def load_models(self, filepath='ai_pattern_models.pkl'):
        """저장된 모델들을 파일에서 로드합니다."""
        try:
            with open(filepath, 'rb') as f:
                model_data = pickle.load(f)
            
            self.ai_models = model_data.get('ai_models', {})
            self.cluster_models = model_data.get('cluster_models', {})
            self.pattern_features = model_data.get('pattern_features', {})
            self.grouped_patterns = model_data.get('grouped_patterns', [])
            
            _log.info("AI 모델들이 %s에서 로드되었습니다.", filepath)
            return True
        except FileNotFoundError:
            _log.warning("모델 파일 %s을 찾을 수 없습니다.", filepath)
            return False
        except Exception as e:
            _log.error("모델 로드 실패: %s", e)
            return False
    
    def print_analysis_report(self):
        """AI 패턴 분석 리포트를 출력합니다."""
        if not self.grouped_patterns:
            _log.warning("먼저 회차 그룹핑을 수행해주세요.")
            return

        _log.info("AI 패턴 분석 리포트 - 총 그룹 수: %d개", len(self.grouped_patterns))

        # 클러스터 정보
        if self.cluster_models and 'kmeans' in self.cluster_models:
            cluster_info = self.cluster_models['kmeans']
            _log.info("클러스터 수: %d개", len(cluster_info['analysis']))

            for cluster_id, analysis in cluster_info['analysis'].items():
                patterns = analysis['patterns']
                _log.info("클러스터 %d: 그룹 수=%d개, 주요 번호=%s, 평균 합계=%.1f",
                          cluster_id + 1, analysis['size'],
                          patterns['top_numbers'][:5], patterns['avg_sum'])

        # AI 모델 정보
        if self.ai_models:
            _log.info("AI 모델 수: %d개", len(self.ai_models))
            for name, model_info in self.ai_models.items():
                _log.info("  %s: 정확도 %.3f", name, model_info['accuracy']) 