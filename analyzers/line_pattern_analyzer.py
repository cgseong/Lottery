#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
선 연결 패턴 분석기 모듈
"""

import random
import math
from typing import List, Dict, Optional, Tuple, Any

from utils.constants import MAX_LOTTO_NUMBER, NUM_LOTTO_NUMBERS_TO_PICK
from utils.logging_config import get_logger

_log = get_logger(__name__)

# matplotlib 관련 import
try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    from matplotlib.patches import FancyArrowPatch
    LINE_PATTERN_AVAILABLE = True
except ImportError:
    LINE_PATTERN_AVAILABLE = False


class LinePatternAnalyzer:
    """로또 번호를 그리드로 배치하고 선으로 연결한 패턴을 분석하는 클래스"""
    
    def __init__(self, historical_data):
        self.historical_data = historical_data
        self.grid_size = 7  # 그리드 열 수
        self.rows = 7       # 그리드 행 수 (마지막 행은 3개 번호만)
        self.patterns = []
        self.line_patterns = []
        
        # 번호를 그리드 위치로 변환하는 딕셔너리
        self.number_to_grid = self._create_number_grid_mapping()
        self.grid_to_number = self._create_grid_to_number_mapping()
    
    def _create_number_grid_mapping(self):
        """번호를 그리드 위치로 변환하는 딕셔너리를 생성합니다."""
        mapping = {}
        number = 1
        
        for row in range(self.rows):
            if row == 6:  # 마지막 행은 3개 번호만
                cols = 3
            else:
                cols = self.grid_size
            
            for col in range(cols):
                mapping[number] = (row, col)
                number += 1
        
        return mapping
    
    def _create_grid_to_number_mapping(self):
        """그리드 위치를 번호로 변환하는 딕셔너리를 생성합니다."""
        mapping = {}
        number = 1
        
        for row in range(self.rows):
            if row == 6:  # 마지막 행은 3개 번호만
                cols = 3
            else:
                cols = self.grid_size
            
            for col in range(cols):
                mapping[(row, col)] = number
                number += 1
        
        return mapping
    
    def _get_grid_position(self, number):
        """번호의 그리드 위치를 반환합니다."""
        return self.number_to_grid.get(number, None)
    
    def _get_number_from_grid(self, row, col):
        """그리드 위치의 번호를 반환합니다."""
        return self.grid_to_number.get((row, col), None)
    
    def _calculate_distance(self, pos1, pos2):
        """두 그리드 위치 간의 거리를 계산합니다."""
        if not pos1 or not pos2:
            return float('inf')
        
        row1, col1 = pos1
        row2, col2 = pos2
        
        # 유클리드 거리
        return math.sqrt((row2 - row1) ** 2 + (col2 - col1) ** 2)
    
    def _calculate_angle(self, pos1, pos2):
        """두 그리드 위치 간의 각도를 계산합니다."""
        if not pos1 or not pos2:
            return 0
        
        row1, col1 = pos1
        row2, col2 = pos2
        
        # 각도 계산 (라디안)
        angle = math.atan2(row2 - row1, col2 - col1)
        return math.degrees(angle)
    
    def analyze_line_patterns(self, recent_rounds=20):
        """최근 회차들의 선 연결 패턴을 분석합니다."""
        if not LINE_PATTERN_AVAILABLE:
            _log.warning("matplotlib이 설치되지 않아 선 패턴 분석을 사용할 수 없습니다.")
            return

        _log.info("선 연결 패턴 분석 (최근 %d회)", recent_rounds)

        # 데이터 확인
        if not self.historical_data:
            _log.warning("분석할 데이터가 없습니다.")
            return []

        _log.info("총 데이터 수: %d회", len(self.historical_data))
        
        # 최근 회차 데이터 추출
        recent_data = self.historical_data[-recent_rounds:] if len(self.historical_data) >= recent_rounds else self.historical_data
        
        self.line_patterns = []
        
        for i, round_data in enumerate(recent_data):
            try:
                # ROUND_COLUMN 상수 대신 직접 '회차' 사용
                round_num = round_data.get('회차', 0)
                numbers = self._get_main_numbers_from_row(round_data)
                
                _log.debug("회차 %s: %s", round_num, numbers)

                if len(numbers) >= 2:
                    pattern = self._analyze_single_round_pattern(round_num, numbers)
                    self.line_patterns.append(pattern)
                else:
                    _log.warning("회차 %s: 번호가 부족합니다 (%d개)", round_num, len(numbers))

            except Exception as e:
                _log.warning("회차 %d 처리 중 오류: %s", i + 1, e)
                continue
        
        _log.info("성공적으로 분석된 패턴: %d개", len(self.line_patterns))

        # 패턴 통계 분석
        if self.line_patterns:
            self._analyze_pattern_statistics()
        else:
            _log.info("분석할 수 있는 패턴이 없습니다.")
        
        return self.line_patterns
    
    def _get_main_numbers_from_row(self, row_dict):
        """행 데이터에서 메인 번호들을 추출합니다."""
        numbers = []
        # 직접 컬럼명 사용
        for i in range(1, 7):
            col_name = f'번호{i}'
            if col_name in row_dict and row_dict[col_name]:
                try:
                    numbers.append(int(row_dict[col_name]))
                except (ValueError, TypeError):
                    continue
        return sorted(numbers)
    
    def _analyze_single_round_pattern(self, round_num, numbers):
        """단일 회차의 선 연결 패턴을 분석합니다."""
        pattern = {
            'round': round_num,
            'numbers': numbers,
            'grid_positions': [],
            'connections': [],
            'total_distance': 0,
            'angles': [],
            'direction_changes': 0,
            'pattern_type': ''
        }
        
        # 번호들을 그리드 위치로 변환
        positions = []
        for num in numbers:
            pos = self._get_grid_position(num)
            if pos:
                positions.append((num, pos))
        
        pattern['grid_positions'] = positions
        
        if len(positions) < 2:
            return pattern
        
        # 연결선 분석
        connections = []
        total_distance = 0
        angles = []
        
        for i in range(len(positions) - 1):
            num1, pos1 = positions[i]
            num2, pos2 = positions[i + 1]
            
            distance = self._calculate_distance(pos1, pos2)
            angle = self._calculate_angle(pos1, pos2)
            
            connections.append({
                'from': num1,
                'to': num2,
                'from_pos': pos1,
                'to_pos': pos2,
                'distance': distance,
                'angle': angle
            })
            
            total_distance += distance
            angles.append(angle)
        
        pattern['connections'] = connections
        pattern['total_distance'] = total_distance
        pattern['angles'] = angles
        
        # 방향 변화 분석
        direction_changes = 0
        for i in range(1, len(angles)):
            angle_diff = abs(angles[i] - angles[i-1])
            if angle_diff > 45:  # 45도 이상 변화를 방향 변화로 간주
                direction_changes += 1
        
        pattern['direction_changes'] = direction_changes
        
        # 패턴 타입 분류
        pattern['pattern_type'] = self._classify_pattern_type(connections, angles, direction_changes)
        
        return pattern
    
    def _classify_pattern_type(self, connections, angles, direction_changes):
        """선 연결 패턴의 타입을 분류합니다."""
        if not connections:
            return "단일점"
        
        avg_distance = sum(conn['distance'] for conn in connections) / len(connections)
        avg_angle = sum(angles) / len(angles) if angles else 0
        
        if direction_changes == 0:
            if avg_distance < 1.5:
                return "밀집형"
            elif avg_distance > 3:
                return "분산형"
            else:
                return "균형형"
        elif direction_changes == 1:
            return "꺾임형"
        elif direction_changes >= 2:
            return "지그재그형"
        else:
            return "복합형"
    
    def _analyze_pattern_statistics(self):
        """패턴 통계를 분석합니다."""
        if not self.line_patterns:
            return
        
        _log.info("총 분석 회차: %d회", len(self.line_patterns))

        # 패턴 타입별 통계
        pattern_types = {}
        for pattern in self.line_patterns:
            ptype = pattern['pattern_type']
            if ptype not in pattern_types:
                pattern_types[ptype] = 0
            pattern_types[ptype] += 1

        _log.info("패턴 타입별 분포:")
        for ptype, count in sorted(pattern_types.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(self.line_patterns)) * 100
            _log.info("  %s: %d회 (%.1f%%)", ptype, count, percentage)

        # 거리 통계
        distances = [p['total_distance'] for p in self.line_patterns]
        avg_distance = sum(distances) / len(distances)
        _log.info("평균 총 거리: %.2f", avg_distance)

        # 방향 변화 통계
        direction_changes = [p['direction_changes'] for p in self.line_patterns]
        avg_changes = sum(direction_changes) / len(direction_changes)
        _log.info("평균 방향 변화: %.1f회", avg_changes)
    
    def visualize_pattern(self, round_num=None, save_path=None):
        """특정 회차의 선 연결 패턴을 시각화합니다."""
        if not LINE_PATTERN_AVAILABLE:
            _log.warning("matplotlib이 설치되지 않아 시각화를 사용할 수 없습니다.")
            return

        # 특정 회차 또는 가장 최근 회차 선택
        if round_num:
            pattern = next((p for p in self.line_patterns if p['round'] == round_num), None)
        else:
            pattern = self.line_patterns[-1] if self.line_patterns else None

        if not pattern:
            _log.warning("회차 %s의 패턴을 찾을 수 없습니다.", round_num)
            return
        
        self._create_pattern_visualization(pattern, save_path)
    
    def _create_pattern_visualization(self, pattern, save_path=None):
        """패턴 시각화를 생성합니다."""
        fig, ax = plt.subplots(figsize=(12, 10))
        
        # 그리드 그리기
        self._draw_grid(ax)
        
        # 번호들 표시
        self._draw_numbers(ax, pattern['grid_positions'])
        
        # 연결선 그리기
        self._draw_connections(ax, pattern['connections'])
        
        # 제목과 정보
        title = f"회차 {pattern['round']} 선 연결 패턴 - {pattern['pattern_type']}"
        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        
        # 정보 텍스트
        info_text = f"총 거리: {pattern['total_distance']:.2f}\n방향 변화: {pattern['direction_changes']}회"
        ax.text(0.02, 0.98, info_text, transform=ax.transAxes, fontsize=12,
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
        
        ax.set_xlim(-0.5, self.grid_size - 0.5)
        ax.set_ylim(-0.5, self.rows - 0.5)
        ax.invert_yaxis()  # 위쪽이 작은 행 번호가 되도록
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            _log.info("패턴 이미지가 %s에 저장되었습니다.", save_path)
        
        plt.show()
    
    def _draw_grid(self, ax):
        """그리드를 그립니다."""
        # 수직선
        for col in range(self.grid_size + 1):
            ax.axvline(x=col - 0.5, color='gray', alpha=0.3, linewidth=1)
        
        # 수평선
        for row in range(self.rows + 1):
            ax.axhline(y=row - 0.5, color='gray', alpha=0.3, linewidth=1)
    
    def _draw_numbers(self, ax, positions):
        """번호들을 그리드에 표시합니다."""
        for num, (row, col) in positions:
            # 번호 원 그리기
            circle = patches.Circle((col, row), 0.3, facecolor='red', edgecolor='black', linewidth=2)
            ax.add_patch(circle)
            
            # 번호 텍스트
            ax.text(col, row, str(num), ha='center', va='center', fontsize=12, fontweight='bold', color='white')
    
    def _draw_connections(self, ax, connections):
        """연결선들을 그립니다."""
        for i, conn in enumerate(connections):
            from_pos = conn['from_pos']
            to_pos = conn['to_pos']
            
            # 화살표 그리기
            arrow = FancyArrowPatch(
                (from_pos[1], from_pos[0]),  # (col, row)
                (to_pos[1], to_pos[0]),      # (col, row)
                arrowstyle='->',
                mutation_scale=20,
                linewidth=3,
                color='black',
                alpha=0.7
            )
            ax.add_patch(arrow)
            
            # 연결 번호 표시
            mid_col = (from_pos[1] + to_pos[1]) / 2
            mid_row = (from_pos[0] + to_pos[0]) / 2
            ax.text(mid_col, mid_row, f"{i+1}", ha='center', va='center', 
                   fontsize=10, fontweight='bold', color='blue',
                   bbox=dict(boxstyle='round,pad=0.2', facecolor='yellow', alpha=0.8))
    
    def generate_recommendations(self, exclude_numbers=None, num_recommendations=5):
        """선 연결 패턴을 기반으로 번호를 추천합니다."""
        if not self.line_patterns:
            _log.warning("먼저 선 연결 패턴 분석을 수행해주세요.")
            return []

        _log.info("선 연결 패턴 기반 추천 번호 (%d개)", num_recommendations)
        
        recommendations = []
        
        # 패턴 타입별 가중치 설정
        pattern_weights = {
            '밀집형': 0.3,
            '균형형': 0.4,
            '분산형': 0.2,
            '꺾임형': 0.3,
            '지그재그형': 0.2,
            '복합형': 0.25
        }
        
        # 최근 패턴들의 특성 분석
        recent_patterns = self.line_patterns[-10:]  # 최근 10회
        
        # 평균 거리와 방향 변화 계산
        avg_distance = sum(p['total_distance'] for p in recent_patterns) / len(recent_patterns)
        avg_direction_changes = sum(p['direction_changes'] for p in recent_patterns) / len(recent_patterns)
        
        _log.info("최근 패턴 특성: 평균 거리=%.2f, 평균 방향 변화=%.1f회", avg_distance, avg_direction_changes)
        
        for i in range(num_recommendations):
            numbers = self._generate_pattern_based_numbers(
                exclude_numbers, avg_distance, avg_direction_changes, pattern_weights
            )
            
            if numbers:
                score = self._calculate_pattern_score(numbers)
                recommendations.append({
                    'numbers': numbers,
                    'score': score,
                    'pattern_type': self._classify_generated_pattern(numbers)
                })
        
        # 점수순으로 정렬
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        
        # 결과 출력
        for i, rec in enumerate(recommendations, 1):
            pattern_type = rec['pattern_type']
            _log.info("%d. %s (점수: %.2f, 패턴: %s)", i, rec['numbers'], rec['score'], pattern_type)
        
        return recommendations
    
    def _generate_pattern_based_numbers(self, exclude_numbers, target_distance, target_direction_changes, pattern_weights):
        """패턴 기반으로 번호를 생성합니다."""
        exclude_numbers = exclude_numbers or []
        excluded_set = set(exclude_numbers)

        # seen 집합으로 선택된 번호 추적 — O(1) 조회, list.remove() O(n) 루프 제거
        seen: set = set()

        all_candidates = [n for n in range(1, MAX_LOTTO_NUMBER + 1) if n not in excluded_set]
        if len(all_candidates) < 6:
            return []

        # 시작 번호 선택
        start_number = random.choice(all_candidates)
        numbers = [start_number]
        seen.add(start_number)

        # 패턴에 따라 다음 번호들 선택
        for _ in range(5):
            available_numbers = [n for n in all_candidates if n not in seen]
            if not available_numbers:
                break

            # 현재 패턴의 거리와 방향 변화 계산
            current_distance = self._calculate_current_pattern_distance(numbers)
            current_direction_changes = self._calculate_current_direction_changes(numbers)

            # 목표와의 차이에 따라 다음 번호 선택 전략 결정
            if current_distance < target_distance * 0.8:
                # 거리가 너무 짧으면 더 멀리 있는 번호 선택
                next_number = self._select_distant_number(numbers, available_numbers)
            elif current_distance > target_distance * 1.2:
                # 거리가 너무 길면 가까운 번호 선택
                next_number = self._select_nearby_number(numbers, available_numbers)
            else:
                # 균형잡힌 선택
                next_number = self._select_balanced_number(
                    numbers, available_numbers, target_direction_changes, current_direction_changes
                )

            if next_number is None:
                next_number = random.choice(available_numbers)

            numbers.append(next_number)
            seen.add(next_number)

        return sorted(numbers)
    
    def _calculate_current_pattern_distance(self, numbers):
        """현재 번호들의 총 거리를 계산합니다."""
        if len(numbers) < 2:
            return 0
        
        total_distance = 0
        for i in range(len(numbers) - 1):
            pos1 = self._get_grid_position(numbers[i])
            pos2 = self._get_grid_position(numbers[i + 1])
            if pos1 and pos2:
                total_distance += self._calculate_distance(pos1, pos2)
        
        return total_distance
    
    def _calculate_current_direction_changes(self, numbers):
        """현재 번호들의 방향 변화를 계산합니다."""
        if len(numbers) < 3:
            return 0
        
        angles = []
        for i in range(len(numbers) - 1):
            pos1 = self._get_grid_position(numbers[i])
            pos2 = self._get_grid_position(numbers[i + 1])
            if pos1 and pos2:
                angles.append(self._calculate_angle(pos1, pos2))
        
        direction_changes = 0
        for i in range(1, len(angles)):
            angle_diff = abs(angles[i] - angles[i-1])
            if angle_diff > 45:
                direction_changes += 1
        
        return direction_changes
    
    def _select_distant_number(self, current_numbers, available_numbers):
        """현재 번호들과 거리가 먼 번호를 선택합니다."""
        if not current_numbers or not available_numbers:
            return random.choice(available_numbers) if available_numbers else None
        
        # 현재 번호들의 평균 위치 계산
        current_positions = [self._get_grid_position(n) for n in current_numbers]
        current_positions = [pos for pos in current_positions if pos]
        
        if not current_positions:
            return random.choice(available_numbers)
        
        avg_row = sum(pos[0] for pos in current_positions) / len(current_positions)
        avg_col = sum(pos[1] for pos in current_positions) / len(current_positions)
        
        # 가장 먼 번호 선택
        max_distance = 0
        best_number = None
        
        for number in available_numbers:
            pos = self._get_grid_position(number)
            if pos:
                distance = math.sqrt((pos[0] - avg_row) ** 2 + (pos[1] - avg_col) ** 2)
                if distance > max_distance:
                    max_distance = distance
                    best_number = number
        
        return best_number or random.choice(available_numbers)
    
    def _select_nearby_number(self, current_numbers, available_numbers):
        """현재 번호들과 가까운 번호를 선택합니다."""
        if not current_numbers or not available_numbers:
            return random.choice(available_numbers) if available_numbers else None
        
        # 현재 번호들의 평균 위치 계산
        current_positions = [self._get_grid_position(n) for n in current_numbers]
        current_positions = [pos for pos in current_positions if pos]
        
        if not current_positions:
            return random.choice(available_numbers)
        
        avg_row = sum(pos[0] for pos in current_positions) / len(current_positions)
        avg_col = sum(pos[1] for pos in current_positions) / len(current_positions)
        
        # 가장 가까운 번호 선택
        min_distance = float('inf')
        best_number = None
        
        for number in available_numbers:
            pos = self._get_grid_position(number)
            if pos:
                distance = math.sqrt((pos[0] - avg_row) ** 2 + (pos[1] - avg_col) ** 2)
                if distance < min_distance:
                    min_distance = distance
                    best_number = number
        
        return best_number or random.choice(available_numbers)
    
    def _select_balanced_number(self, current_numbers, available_numbers, target_direction_changes, current_direction_changes):
        """균형잡힌 번호를 선택합니다."""
        if not current_numbers or not available_numbers:
            return random.choice(available_numbers) if available_numbers else None
        
        # 방향 변화를 고려한 선택
        if current_direction_changes < target_direction_changes:
            # 방향 변화가 부족하면 꺾임이 있는 번호 선택
            return self._select_direction_change_number(current_numbers, available_numbers)
        else:
            # 방향 변화가 충분하면 직선적인 번호 선택
            return self._select_straight_number(current_numbers, available_numbers)
    
    def _select_direction_change_number(self, current_numbers, available_numbers):
        """방향 변화를 만드는 번호를 선택합니다."""
        if len(current_numbers) < 2:
            return random.choice(available_numbers)
        
        # 마지막 두 번호의 방향
        pos1 = self._get_grid_position(current_numbers[-2])
        pos2 = self._get_grid_position(current_numbers[-1])
        
        if not pos1 or not pos2:
            return random.choice(available_numbers)
        
        current_angle = self._calculate_angle(pos1, pos2)
        
        # 각도가 많이 다른 번호 선택
        best_number = None
        max_angle_diff = 0
        
        for number in available_numbers:
            pos3 = self._get_grid_position(number)
            if pos3:
                new_angle = self._calculate_angle(pos2, pos3)
                angle_diff = abs(new_angle - current_angle)
                if angle_diff > max_angle_diff:
                    max_angle_diff = angle_diff
                    best_number = number
        
        return best_number or random.choice(available_numbers)
    
    def _select_straight_number(self, current_numbers, available_numbers):
        """직선적인 번호를 선택합니다."""
        if len(current_numbers) < 2:
            return random.choice(available_numbers)
        
        # 마지막 두 번호의 방향
        pos1 = self._get_grid_position(current_numbers[-2])
        pos2 = self._get_grid_position(current_numbers[-1])
        
        if not pos1 or not pos2:
            return random.choice(available_numbers)
        
        current_angle = self._calculate_angle(pos1, pos2)
        
        # 각도가 비슷한 번호 선택
        best_number = None
        min_angle_diff = float('inf')
        
        for number in available_numbers:
            pos3 = self._get_grid_position(number)
            if pos3:
                new_angle = self._calculate_angle(pos2, pos3)
                angle_diff = abs(new_angle - current_angle)
                if angle_diff < min_angle_diff:
                    min_angle_diff = angle_diff
                    best_number = number
        
        return best_number or random.choice(available_numbers)
    
    def _calculate_pattern_score(self, numbers):
        """생성된 번호 조합의 패턴 점수를 계산합니다."""
        if len(numbers) < 2:
            return 0
        
        # 거리 점수
        total_distance = self._calculate_current_pattern_distance(numbers)
        distance_score = min(total_distance / 10, 1.0)  # 0-1 범위로 정규화
        
        # 방향 변화 점수
        direction_changes = self._calculate_current_direction_changes(numbers)
        direction_score = min(direction_changes / 3, 1.0)  # 0-1 범위로 정규화
        
        # 균형 점수 (번호 분포)
        balance_score = self._calculate_balance_score(numbers)
        
        # 종합 점수
        total_score = (distance_score * 0.4 + direction_score * 0.3 + balance_score * 0.3)
        
        return total_score
    
    def _calculate_balance_score(self, numbers):
        """번호 분포의 균형 점수를 계산합니다."""
        if not numbers:
            return 0
        
        # 그리드 영역별 분포 계산
        regions = {
            'top_left': 0,      # 1-7
            'top_right': 0,     # 8-14
            'mid_left': 0,      # 15-21
            'mid_right': 0,     # 22-28
            'bottom_left': 0,   # 29-35
            'bottom_right': 0,  # 36-42
            'bottom': 0         # 43-45
        }
        
        for num in numbers:
            if 1 <= num <= 7:
                regions['top_left'] += 1
            elif 8 <= num <= 14:
                regions['top_right'] += 1
            elif 15 <= num <= 21:
                regions['mid_left'] += 1
            elif 22 <= num <= 28:
                regions['mid_right'] += 1
            elif 29 <= num <= 35:
                regions['bottom_left'] += 1
            elif 36 <= num <= 42:
                regions['bottom_right'] += 1
            elif 43 <= num <= 45:
                regions['bottom'] += 1
        
        # 균형 점수 계산 (너무 한쪽에 치우치지 않도록)
        max_count = max(regions.values())
        min_count = min(regions.values())
        
        if max_count == 0:
            return 0
        
        balance_score = 1.0 - (max_count - min_count) / len(numbers)
        return max(0, balance_score)
    
    def _classify_generated_pattern(self, numbers):
        """생성된 번호 조합의 패턴 타입을 분류합니다."""
        if len(numbers) < 2:
            return "단일점"
        
        # 임시 패턴 객체 생성
        temp_pattern = {
            'numbers': numbers,
            'connections': []
        }
        
        # 연결 정보 생성
        for i in range(len(numbers) - 1):
            pos1 = self._get_grid_position(numbers[i])
            pos2 = self._get_grid_position(numbers[i + 1])
            
            if pos1 and pos2:
                distance = self._calculate_distance(pos1, pos2)
                angle = self._calculate_angle(pos1, pos2)
                
                temp_pattern['connections'].append({
                    'distance': distance,
                    'angle': angle
                })
        
        # 패턴 분류
        if temp_pattern['connections']:
            angles = [conn['angle'] for conn in temp_pattern['connections']]
            direction_changes = 0
            
            for i in range(1, len(angles)):
                angle_diff = abs(angles[i] - angles[i-1])
                if angle_diff > 45:
                    direction_changes += 1
            
            return self._classify_pattern_type(temp_pattern['connections'], angles, direction_changes)
        
        return "단일점" 