#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 로또 번호 추천 시스템
import os
import sys
from typing import List, Dict

try:
    from analyzers.lotto_data_collector import LottoDataCollector
    from analyzers.statistical_analyzer import StatisticalAnalyzer
    from analyzers.exclude_number_manager import ExcludeNumberManager
    from analyzers.comprehensive_analyzer import ComprehensiveAnalyzer
    from number_storage import NumberStorage
    from ai_pattern_learner import AIPatternLearner
    from features import (
        AutoUpdateScheduler,
        WeightOptimizer,
    )
except ImportError as e:
    print(f" 필수 모듈 로드 실패: {e}")
    print("requirements.txt를 확인하고 패키지를 설치해주세요.")
    sys.exit(1)


class LottoSystem:
    def __init__(self):
        self.data_file = '로또당첨번호.csv'
        self.collector = LottoDataCollector()
        self.storage = NumberStorage()
        self.exclude_manager = ExcludeNumberManager()
        self.ai_learner = AIPatternLearner()

        self.historical_data = self._load_data()
        self.optimized_weights = None
        self.stat_analyzer = StatisticalAnalyzer(self.historical_data) if self.historical_data else None
        self.comp_analyzer = ComprehensiveAnalyzer(self.historical_data) if self.historical_data else None
        self.scheduler = AutoUpdateScheduler(self.collector)

        # 시작 시 가중치 자동 최적화
        if self.historical_data:
            print(" 가중치 최적화 중...")
            self._optimize_weights(silent=True)

    def _load_data(self) -> List[Dict]:
        from utils.file_utils import load_csv_data
        data = load_csv_data(self.data_file)
        if not data and os.path.exists(self.data_file):
            print(" 데이터를 읽을 수 없습니다. 파일 인코딩이나 형식을 확인해주세요.")
        return data

    def _optimize_weights(self, silent: bool = False):
        """백테스트 기반 점수 가중치를 최적화하고 stat_analyzer에 즉시 적용합니다."""
        if not self.historical_data or not self.stat_analyzer:
            return
        optimizer = WeightOptimizer(self.historical_data)
        best_weights = optimizer.optimize()
        self.optimized_weights = best_weights
        self.stat_analyzer.score_weights = best_weights
        if not silent:
            print(" 가중치 최적화 완료 — 추천 메뉴(1·2·4·6)에 즉시 반영됩니다.")

    def _refresh_data(self):
        self.historical_data = self._load_data()
        if self.historical_data:
            self.stat_analyzer = StatisticalAnalyzer(
                self.historical_data,
                score_weights=self.optimized_weights,
            )
            self.comp_analyzer = ComprehensiveAnalyzer(self.historical_data)
            # 새 데이터에 맞춰 가중치 재최적화
            self._optimize_weights(silent=True)
        else:
            self.stat_analyzer = None
            self.comp_analyzer = None

    def print_menu(self):
        print("\n" + "=" * 60)
        print(" 로또 번호 추천 시스템")
        print("=" * 60)
        print(" 1. 당첨 번호 분석")
        print(" 2. 통계 기반 번호 추천")
        print(" 3. 제외 번호 관리")
        print(" 4. 고급 추천 (제외/고정)")
        print(" 5. 저장된 조합")
        print(" 6. 고유 패턴 추천 (AI + 미출현)")
        print(" 7. 데이터 수집 / 자동 업데이트")
        print(" 8. 종합 패턴 분석 추천 (10개 지표)")
        print(" 9. 회차별 당첨번호 조회")
        print(" 0. 종료")
        print("=" * 60)

    def run(self):
        while True:
            self.print_menu()
            choice = input("\n 메뉴를 선택하세요: ").strip()
            if choice == '1':
                self.analyze_winning_numbers()
            elif choice == '2':
                self.recommend_numbers()
            elif choice == '3':
                self.manage_exclude_numbers()
            elif choice == '4':
                self.recommend_with_exclusion()
            elif choice == '5':
                self.manage_saved_combinations()
            elif choice == '6':
                self.recommend_unique_patterns()
            elif choice == '7':
                self.run_auto_update()
            elif choice == '8':
                self.comprehensive_recommend()
            elif choice == '9':
                self.show_round_info()
            elif choice == '0':
                print("\n 프로그램을 종료합니다.")
                break
            else:
                print("\n 잘못된 입력입니다.")
            input("\n계속하려면 Enter를 누르세요...")

    def analyze_winning_numbers(self):
        """1. 당첨번호 분석"""
        if not self.stat_analyzer or not self.stat_analyzer.historical_data:
            print("\n[WARN] 데이터가 없거나 로드되지 않았습니다. 메뉴 7번(데이터 수집)을 실행하거나 파일을 확인해주세요.")
            return
        print("\n[INFO] 당첨번호 분석 결과")

        trends = self.stat_analyzer.analyze_recent_trends(recent_count=20)
        if trends:
            print(f"\n 최근 {trends['recent_count']}회 Hot & Cold 분석")
            print("   [Hot Numbers] 최근 자주 나온 번호:")
            for num, count in trends['hot_numbers']:
                print(f"    - {num}번: {count}회")
            print("\n   [Cold Numbers] 최근 미출현 (장기 미출현 등):")
            cold_str = ", ".join([f"{n}번" for n in trends['cold_numbers']])
            print(f"    - {cold_str}")
            print("")

        freq = self.stat_analyzer.analyze_frequency()
        if not freq or not freq.get('most_common'):
            print("\n[WARN] 분석할 데이터가 충분하지 않습니다.")
            return

        print(" 가장 많이 나온 번호 (Top 5):")
        for num, count in freq['most_common'][:5]:
            print(f"   {num}번: {count}회")

        print(f"\n 가장 적게 나온 번호 (Top 5):")
        for num, count in freq['least_common'][:5]:
            print(f"   {num}번: {count}회")

        sum_stats = self.stat_analyzer.analyze_sum_range()
        print(f"\n 합계 통계:")
        print(f"   평균 합계: {sum_stats.get('avg_sum', 0):.1f}")
        print(f"   최소/최대 합계: {sum_stats.get('min_sum', 0)} / {sum_stats.get('max_sum', 0)}")

        odd_even_stats = self.stat_analyzer.analyze_odd_even()
        print(f"\n 홀짝 통계:")
        print(f"   평균 홀수 개수: {odd_even_stats.get('avg_odd', 0):.1f}개")
        print(f"   평균 짝수 개수: {odd_even_stats.get('avg_even', 0):.1f}개")

        section_stats = self.stat_analyzer.analyze_section_distribution()
        print(f"\n 구간별 분포:")
        if 'percentages' in section_stats:
            print(f"   1-15구간: {section_stats['percentages'].get('1-15', 0):.1f}%")
            print(f"   16-30구간: {section_stats['percentages'].get('16-30', 0):.1f}%")
            print(f"   31-45구간: {section_stats['percentages'].get('31-45', 0):.1f}%")
        else:
            print("   데이터 부족으로 분석 불가")

        consecutive_stats = self.stat_analyzer.analyze_consecutive_patterns()
        print(f"\n 연속번호 패턴:")
        if 'percentages' in consecutive_stats:
            print(f"   연속번호 없음: {consecutive_stats['percentages'].get(0, 0):.1f}%")
            print(f"   1쌍 연속: {consecutive_stats['percentages'].get(1, 0):.1f}%")
            print(f"   2쌍 연속: {consecutive_stats['percentages'].get(2, 0):.1f}%")
        else:
            print("   데이터 부족으로 분석 불가")

        print(f"\n{'─' * 60}")
        print(" 분석 결과 기반 추천번호")
        recs = self.stat_analyzer.generate_recommendations(num_recommendations=1)
        if recs:
            nums = recs[0]['numbers']
            score = recs[0]['score']
            print(f"   추천번호: {nums}  (점수: {score:.4f})")
            save = input("   이 조합을 저장하시겠습니까? (y/n): ").lower()
            if save == 'y':
                self.storage.save_combination(nums, "분석 기반 추천")
                print("    저장되었습니다.")

    def recommend_numbers(self):
        """2. 번호 추천"""
        if not self.stat_analyzer:
            print("\n[WARN] 데이터가 없습니다.")
            return
        print("\n 통계 기반 번호 추천")
        recommendations = self.stat_analyzer.generate_recommendations(num_recommendations=1)
        if not recommendations:
            print("\n[WARN] 추천 번호를 생성할 수 없습니다.")
            return
        rec = recommendations[0]
        print(f"\n 추천번호: {rec['numbers']}  (점수: {rec['score']:.4f})")
        save = input("   이 조합을 저장하시겠습니까? (y/n): ").lower()
        if save == 'y':
            self.storage.save_combination(rec['numbers'], "통계 추천")
            print("    저장되었습니다.")

    def manage_exclude_numbers(self):
        """3. 제외번호 관리"""
        while True:
            print("\n 제외번호 관리")
            print("1. 제외번호 목록 보기")
            print("2. 제외번호 추가")
            print("3. 제외번호 삭제")
            print("4. 초기화")
            print("0. 뒤로가기")
            sub_choice = input("선택: ").strip()
            if sub_choice == '1':
                self.exclude_manager.show_exclude_numbers()
            elif sub_choice == '2':
                nums = input("추가할 번호 (쉼표 구분): ")
                try:
                    raw_list = [int(n.strip()) for n in nums.split(',') if n.strip()]
                    if not raw_list:
                        print("번호를 입력해주세요.")
                        continue
                    invalid = [n for n in raw_list if not (1 <= n <= 45)]
                    if invalid:
                        print(f"유효하지 않은 번호: {invalid}  (1~45 사이만 허용)")
                        continue
                    self.exclude_manager.add_exclude_numbers(raw_list)
                except ValueError:
                    print("숫자만 입력해주세요. (예: 3, 7, 15)")
            elif sub_choice == '3':
                nums = input("삭제할 번호 (쉼표 구분): ")
                try:
                    raw_list = [int(n.strip()) for n in nums.split(',') if n.strip()]
                    if not raw_list:
                        print("번호를 입력해주세요.")
                        continue
                    invalid = [n for n in raw_list if not (1 <= n <= 45)]
                    if invalid:
                        print(f"유효하지 않은 번호: {invalid}  (1~45 사이만 허용)")
                        continue
                    self.exclude_manager.remove_exclude_numbers(raw_list)
                except ValueError:
                    print("숫자만 입력해주세요. (예: 3, 7, 15)")
            elif sub_choice == '4':
                if input("제외번호를 모두 초기화하시겠습니까? (y/n): ").lower() == 'y':
                    self.exclude_manager.clear_exclude_numbers()
            elif sub_choice == '0':
                break

    def recommend_with_exclusion(self):
        """4. 고급 추천 (제외/고정)"""
        if not self.stat_analyzer:
            print("\n[WARN] 데이터가 없습니다.")
            return
        print("\n 고급 번호 추천 (제외수 / 고정수 설정)")

        exclude_nums = self.exclude_manager.get_exclude_numbers()
        print(f"\n1 제외번호 설정")
        if exclude_nums:
            print(f"   현재 등록된 제외번호: {exclude_nums}")
            if input("   제외번호를 수정하시겠습니까? (y/n): ").lower() == 'y':
                self.manage_exclude_numbers()
                exclude_nums = self.exclude_manager.get_exclude_numbers()
        else:
            print("   등록된 제외번호가 없습니다.")
            if input("   제외번호를 추가하시겠습니까? (y/n): ").lower() == 'y':
                self.manage_exclude_numbers()
                exclude_nums = self.exclude_manager.get_exclude_numbers()

        fixed_nums = set()
        print(f"\n2 고정번호 설정")
        if input("   고정수(반드시 포함할 번호)를 설정하시겠습니까? (y/n): ").lower() == 'y':
            while True:
                user_input = input("   고정할 번호 입력 (쉼표 구분, Enter로 건너뜀): ").strip()
                if not user_input:
                    break
                try:
                    input_list = [int(n.strip()) for n in user_input.split(',')]
                    valid_list = [n for n in input_list if 1 <= n <= 45]
                    if len(valid_list) != len(input_list):
                        print("유효하지 않은 번호가 포함되어 있습니다. (1~45 사이)")
                        continue
                    if len(valid_list) > 6:
                        print("   [WARN] 고정수는 최대 6개까지만 가능합니다.")
                        continue
                    fixed_nums = set(valid_list)
                    print(f"    고정번호 설정됨: {fixed_nums}")
                    break
                except ValueError:
                    print("숫자를 입력해주세요.")

        print(f"\n    고정번호: {len(fixed_nums)}개 {list(fixed_nums)}")
        try:
            count = int(input("\n추천받을 조합 개수 (1~20): ").strip() or "5")
            count = max(1, min(20, count))
        except ValueError:
            count = 5
        recommendations = self.stat_analyzer.generate_recommendations(
            exclude_numbers=set(exclude_nums),
            fixed_numbers=fixed_nums,
            num_recommendations=count,
        )
        for i, rec in enumerate(recommendations, 1):
            print(f"\n[{i}] {rec['numbers']} (점수: {rec['score']:.2f})")
            save = input("   저장하시겠습니까? (y/n): ").lower()
            if save == 'y':
                method_str = "제외/고정 추천"
                if fixed_nums:
                    method_str += f"(고정:{list(fixed_nums)})"
                self.storage.save_combination(rec['numbers'], method_str)
                print("    저장되었습니다.")

    def manage_saved_combinations(self):
        """5. 저장된 번호 관리"""
        while True:
            print("\n 저장된 번호 관리")
            combos = self.storage.get_all_combinations()
            if not combos:
                print("   (저장된 조합이 없습니다)")
            else:
                for i, combo in enumerate(combos):
                    print(f"   {i+1}. {combo['numbers']} [{combo['method']}] ({combo['date']})")
            print("\n1. 조합 삭제")
            print("2. 전체 삭제")
            print("3. 번호 직접 입력 저장")
            print("4. 저장된 조합 품질 검토")
            print("0. 뒤로가기")
            sub_choice = input("선택: ").strip()
            if sub_choice == '1':
                try:
                    idx = int(input("삭제할 번호(인덱스): ").strip()) - 1
                    if self.storage.delete_combination(idx):
                        print(" 삭제되었습니다.")
                    else:
                        print(" 해당 인덱스의 조합을 찾을 수 없습니다.")
                except ValueError:
                    print(" 올바른 숫자를 입력해주세요.")
            elif sub_choice == '2':
                if input("정말 모두 삭제합니까? (y/n): ").lower() == 'y':
                    self.storage.clear_all()
                    print(" 초기화되었습니다.")
            elif sub_choice == '3':
                self._input_and_save_combination()
            elif sub_choice == '4':
                self._review_saved_combinations()
            elif sub_choice == '0':
                break

    def _input_and_save_combination(self):
        """번호 직접 입력 후 저장"""
        print("\n 번호 직접 입력 저장")
        print("   1~45 사이의 번호 6개를 쉼표로 구분하여 입력하세요.")
        raw = input("   번호 입력: ").strip()
        try:
            nums = [int(n.strip()) for n in raw.split(',')]
            if len(nums) != 6:
                print(" 번호는 정확히 6개여야 합니다.")
                return
            if any(n < 1 or n > 45 for n in nums):
                print(" 모든 번호는 1~45 사이여야 합니다.")
                return
            if len(set(nums)) != 6:
                print(" 중복된 번호가 있습니다.")
                return
            nums.sort()
            self.storage.save_combination(nums, "직접 입력")
            print(f"    저장되었습니다: {nums}")
        except ValueError:
            print(" 올바른 숫자를 입력해주세요.")

    def _review_saved_combinations(self):
        """저장된 조합 품질 검토"""
        if not self.stat_analyzer:
            print("\n[WARN] 분석 데이터가 없습니다. 메뉴 7번(데이터 수집)을 먼저 실행해주세요.")
            return
        combos = self.storage.get_all_combinations()
        if not combos:
            print("\n   저장된 조합이 없습니다.")
            return

        print("\n" + "=" * 60)
        print(" 저장된 조합 품질 검토")
        print("=" * 60)

        for i, combo in enumerate(combos, 1):
            nums = combo['numbers']
            method = combo['method']
            result = self._evaluate_combination(nums)

            print(f"\n[{i}] {nums}  ({method})")
            print(f"   ┌ 빈도 점수:   {result['freq_score']:.4f}  — {result['freq_comment']}")
            print(f"   ├ 합계 점수:   {result['sum_score']:.4f}  — 합계 {result['total_sum']} (평균 {result['avg_sum']:.1f})")
            print(f"   ├ 홀짝 점수:   {result['odd_even_score']:.4f}  — 홀수 {result['odd_count']}개 / 짝수 {result['even_count']}개")
            print(f"   ├ 구간 점수:   {result['section_score']:.4f}  — {result['section_comment']}")
            print(f"   ├ 연속번호:    {result['consec_score']:.4f}  — {result['consec_count']}쌍")
            print(f"   └ 종합 점수:   {result['total_score']:.4f}  [{result['grade']}]")

        print("\n" + "=" * 60)

    def _evaluate_combination(self, numbers: list) -> dict:
        """조합의 품질을 5개 지표로 평가하여 종합 점수와 등급을 반환합니다."""
        nums = sorted(int(n) for n in numbers)

        freq_data = self.stat_analyzer.analyze_frequency()
        sum_data = self.stat_analyzer.analyze_sum_range()
        odd_even_data = self.stat_analyzer.analyze_odd_even()
        section_data = self.stat_analyzer.analyze_section_distribution()

        # 1. 빈도 점수: 6개 번호의 평균 빈도를 전체 번호 중 상위 몇 %인지로 환산
        # sorted(set(...))으로 중복값 제거 후 percentile 계산 — index() 첫번째 값 반환 오류 방지
        freq_map = freq_data.get('frequency', {})
        num_freqs = [freq_map.get(n, 0) for n in nums]
        sorted_unique = sorted(set(freq_map.values()))
        n_unique = len(sorted_unique)
        if sorted_unique and sorted_unique[-1] > 0:
            ranks = [sorted_unique.index(f) / max(n_unique - 1, 1) for f in num_freqs]
            freq_score = sum(ranks) / 6
        else:
            freq_score = 0.5
        freq_comment = "고빈도 번호 위주" if freq_score >= 0.6 else ("저빈도 번호 위주" if freq_score < 0.4 else "균형")

        # 2. 합계 점수: 역사적 평균 합계와의 근접도
        avg_sum = float(sum_data.get('avg_sum', 138))
        total_sum = sum(nums)
        deviation_ratio = abs(total_sum - avg_sum) / avg_sum
        sum_score = max(0.0, 1.0 - deviation_ratio * 3)

        # 3. 홀짝 점수: 역사적 평균 홀수 개수와의 근접도
        avg_odd = float(odd_even_data.get('avg_odd', 3.0))
        odd_count = sum(1 for n in nums if n % 2 != 0)
        even_count = 6 - odd_count
        odd_even_score = max(0.0, 1.0 - abs(odd_count - round(avg_odd)) / 3)

        # 4. 구간 점수: 역사적 구간 분포와의 근접도
        hist_pct = section_data.get('percentages', {'1-15': 33.3, '16-30': 33.3, '31-45': 33.3})
        actual_pct = {
            '1-15':  sum(1 for n in nums if 1  <= n <= 15) / 6 * 100,
            '16-30': sum(1 for n in nums if 16 <= n <= 30) / 6 * 100,
            '31-45': sum(1 for n in nums if 31 <= n <= 45) / 6 * 100,
        }
        mae = sum(abs(actual_pct[k] - hist_pct.get(k, 33.3)) for k in actual_pct) / 3
        section_score = max(0.0, 1.0 - mae / 50)
        section_comment = f"1구간 {actual_pct['1-15']:.0f}% / 2구간 {actual_pct['16-30']:.0f}% / 3구간 {actual_pct['31-45']:.0f}%"

        # 5. 연속번호 점수: 연속 쌍이 적을수록 유리
        consec_count = sum(1 for a, b in zip(nums, nums[1:]) if b - a == 1)
        consec_score = max(0.0, 1.0 - consec_count * 0.25)

        total_score = (freq_score + sum_score + odd_even_score + section_score + consec_score) / 5

        if total_score >= 0.75:
            grade = "우수 ★★★"
        elif total_score >= 0.55:
            grade = "양호 ★★"
        elif total_score >= 0.40:
            grade = "보통 ★"
        else:
            grade = "미흡"

        return {
            'freq_score': freq_score, 'freq_comment': freq_comment,
            'sum_score': sum_score, 'total_sum': total_sum, 'avg_sum': avg_sum,
            'odd_even_score': odd_even_score, 'odd_count': odd_count, 'even_count': even_count,
            'section_score': section_score, 'section_comment': section_comment,
            'consec_score': consec_score, 'consec_count': consec_count,
            'total_score': total_score, 'grade': grade,
        }

    def recommend_unique_patterns(self):
        """6. 고유 패턴 추천 (AI + 미출현)"""
        if not self.stat_analyzer:
            print("\n[WARN] 데이터가 없습니다.")
            return
        print("\n 패턴 기반 추천 (미출현 조합 + AI 확률)")
        print("   - 과거 1등 당첨번호와 겹치지 않는 새로운 조합을 생성합니다.")
        print("   - AI 모델을 통해 각 조합의 출현 확률을 계산하여 가장 높은 확률의 조합을 추천합니다.")

        if not self.ai_learner.is_trained:
            print("\n AI 예측 모델을 학습합니다...")
            self.ai_learner.train_models()

        exclude_nums = self.exclude_manager.get_exclude_numbers()
        if exclude_nums:
            print(f"    제외번호: {exclude_nums}")

        candidate_count = 2000
        print(f"\n[CHECK] 후보 조합 {candidate_count}개 생성 및 AI 분석 중...")

        candidates = self.stat_analyzer.generate_unique_recommendations(
            exclude_numbers=set(exclude_nums),
            num_recommendations=candidate_count,
        )
        if not candidates:
            print("\n[WARN] 추천할 수 있는 조합을 찾지 못했습니다.")
            return

        candidate_numbers = [c['numbers'] for c in candidates]
        ai_scores = self.ai_learner.calculate_combination_probability(candidate_numbers)

        # AI 점수 부착
        scored = []
        for cand, ai_score in zip(candidates, ai_scores):
            if ai_score is not None:
                cand['ai_score'] = ai_score
                scored.append(cand)

        if not scored:
            print("\n[WARN] AI 점수를 계산할 수 없습니다.")
            return

        # AI 점수·통계 점수 각각 0~1 정규화 후 동일 가중치로 종합 점수 산출
        ai_vals = [c['ai_score'] for c in scored]
        stat_vals = [c['score'] for c in scored]

        ai_min, ai_max = min(ai_vals), max(ai_vals)
        st_min, st_max = min(stat_vals), max(stat_vals)

        def norm(v, lo, hi):
            return (v - lo) / (hi - lo) if hi > lo else 0.0

        for cand in scored:
            cand['combined_score'] = (
                norm(cand['ai_score'], ai_min, ai_max) * 0.5
                + norm(cand['score'], st_min, st_max) * 0.5
            )

        best = max(scored, key=lambda c: c['combined_score'])

        print(f"\n{'─' * 60}")
        print(f" 최적 추천번호: {best['numbers']}")
        print(f"    - 종합 점수:  {best['combined_score']:.4f}")
        print(f"    - AI 확률:    {best['ai_score']:.4f}")
        print(f"    - 통계 점수:  {best['score']:.4f}")
        print(f"    - 연속 번호:  {best['consecutive_count']}쌍")
        save = input("\n   저장하시겠습니까? (y/n): ").lower()
        if save == 'y':
            self.storage.save_combination(best['numbers'], "AI 미출현 패턴")
            print("    저장되었습니다.")

    # ──────────────────────────────────────────────
    # 9. 회차별 당첨번호 조회
    # ──────────────────────────────────────────────

    _BALL_COLORS = {
        (1, 10):  '\033[43m',   # 노랑 (1~10)
        (11, 20): '\033[44m',   # 파랑 (11~20)
        (21, 30): '\033[41m',   # 빨강 (21~30)
        (31, 40): '\033[100m',  # 회색 (31~40)
        (41, 45): '\033[42m',   # 초록 (41~45)
    }

    def _ball(self, number: int, is_bonus: bool = False) -> str:
        """번호를 ANSI 컬러 볼 문자열로 반환합니다."""
        reset = '\033[0m'
        bold  = '\033[1m'
        white = '\033[97m'
        if is_bonus:
            color = '\033[45m'  # 보너스: 마젠타
        else:
            color = '\033[100m'
            for (lo, hi), c in self._BALL_COLORS.items():
                if lo <= number <= hi:
                    color = c
                    break
        return f"{color}{bold}{white} {number:2d} {reset}"

    def _format_prize(self, amount_won: str) -> str:
        """당첨금액을 억 단위 문자열로 변환합니다. (예: '1860000000' → '18.6억')"""
        try:
            won = int(amount_won)
            eok = won / 1_0000_0000
            return f"{eok:.1f}억"
        except (ValueError, TypeError):
            return '-'

    def _load_round_data(self) -> list:
        """CSV에서 전체 회차 데이터를 읽어 정렬된 리스트로 반환합니다."""
        import csv as _csv
        path = self.data_file
        if not os.path.exists(path):
            return []
        encodings = ['utf-8', 'cp949', 'euc-kr']
        for enc in encodings:
            try:
                with open(path, 'r', encoding=enc) as f:
                    rows = list(_csv.DictReader(f))
                if rows:
                    rows.sort(key=lambda r: int(r.get('회차', 0)), reverse=True)
                    return rows
            except Exception:
                continue
        return []

    def _print_round_row(self, row: dict):
        """회차 1개를 이미지와 유사한 형식으로 출력합니다."""
        round_no  = row.get('회차', '?')
        date_str  = row.get('날짜', '')
        bonus     = row.get('보너스번호', '')
        winners   = row.get('1등당첨자수', '')
        prize_raw = row.get('1등당첨금액', '')

        # 번호 6개
        balls = []
        for i in range(1, 7):
            val = row.get(f'번호{i}', '')
            try:
                balls.append(self._ball(int(val)))
            except (ValueError, TypeError):
                balls.append(f" {val:>2} ")

        # 보너스 볼
        try:
            bonus_ball = self._ball(int(bonus), is_bonus=True)
        except (ValueError, TypeError):
            bonus_ball = f" {bonus} "

        # 헤더 라인: 회차 번호 (빨간색)
        red   = '\033[91m'
        reset = '\033[0m'
        bold  = '\033[1m'
        gray  = '\033[90m'

        balls_str = '  '.join(balls)
        prize_str = self._format_prize(prize_raw) if prize_raw else ''
        winner_str = f"{winners}명" if winners else ''

        line1 = f"  {red}{bold}{round_no:>4}회{reset}  {balls_str}  {gray}+{reset}  {bonus_ball}"
        if winner_str or prize_str:
            line1 += f"   {gray}{winner_str}  {prize_str}{reset}"
        print(line1)

        if date_str:
            print(f"         {gray}{date_str}{reset}")
        print()

    def show_round_info(self):
        """9. 회차별 당첨번호 조회"""
        rows = self._load_round_data()
        if not rows:
            print("\n[WARN] 데이터가 없습니다. 메뉴 7번(데이터 수집)을 먼저 실행해주세요.")
            return

        total = len(rows)
        max_round = int(rows[0].get('회차', 0))
        min_round = int(rows[-1].get('회차', 0))

        while True:
            print("\n" + "=" * 60)
            print(f" 회차별 당첨번호 조회  [{min_round}회 ~ {max_round}회, 총 {total}회차]")
            print("=" * 60)
            print(" 1. 최근 N회 보기")
            print(" 2. 특정 회차 검색")
            print(" 3. 특정 번호 포함 회차 검색")
            print(" 0. 뒤로가기")
            sub = input("\n 선택: ").strip()

            if sub == '0':
                break

            elif sub == '1':
                try:
                    n = int(input(" 최근 몇 회차를 볼까요? (기본 10): ").strip() or '10')
                    n = max(1, min(n, total))
                except ValueError:
                    n = 10
                print()
                for row in rows[:n]:
                    self._print_round_row(row)

            elif sub == '2':
                raw = input(" 조회할 회차 번호 (쉼표로 여러 개, 예: 1223 또는 1220,1221,1222): ").strip()
                try:
                    targets = {int(r.strip()) for r in raw.split(',') if r.strip()}
                except ValueError:
                    print(" 숫자만 입력해주세요.")
                    continue
                matched = [r for r in rows if int(r.get('회차', 0)) in targets]
                matched.sort(key=lambda r: int(r.get('회차', 0)), reverse=True)
                if matched:
                    print()
                    for row in matched:
                        self._print_round_row(row)
                else:
                    print(f"\n[WARN] {targets} 회차를 찾을 수 없습니다.")

            elif sub == '3':
                raw = input(" 포함할 번호 (쉼표로 여러 개, 예: 7,13,42): ").strip()
                try:
                    search_nums = {int(r.strip()) for r in raw.split(',') if r.strip()}
                    invalid = [n for n in search_nums if not (1 <= n <= 45)]
                    if invalid:
                        print(f" 유효하지 않은 번호: {invalid}  (1~45 사이)")
                        continue
                except ValueError:
                    print(" 숫자만 입력해주세요.")
                    continue

                matched = []
                for row in rows:
                    nums_in_row = set()
                    for i in range(1, 7):
                        try:
                            nums_in_row.add(int(row.get(f'번호{i}', 0)))
                        except (ValueError, TypeError):
                            pass
                    if search_nums.issubset(nums_in_row):
                        matched.append(row)

                if matched:
                    print(f"\n {search_nums} 포함 회차: {len(matched)}건\n")
                    for row in matched:
                        self._print_round_row(row)
                else:
                    print(f"\n[INFO] {search_nums} 번호를 모두 포함하는 회차가 없습니다.")
            else:
                print(" 잘못된 입력입니다.")

    def run_auto_update(self):
        """7. 데이터 수집 / 자동 업데이트"""
        print("\n[Auto Update] 최신 당첨번호를 가져오는 중...")
        result = self.scheduler.run_once()
        print(f"- 시작 시각: {result['started_at']}")
        print(f"- 업데이트 건수: {result['updated_count']}")
        if result['updated']:
            self._refresh_data()  # 내부에서 가중치 재최적화 포함
            print(" 데이터 및 가중치가 갱신되었습니다.")
        else:
            print(" 이미 최신 데이터입니다.")

    def comprehensive_recommend(self):
        """8. 종합 패턴 분석 추천 (10개 지표)"""
        if not self.comp_analyzer:
            print("\n[WARN] 데이터가 없습니다.")
            return

        print("\n" + "=" * 60)
        print(" 종합 패턴 분석 추천 (10개 지표)")
        print("=" * 60)

        stats = self.comp_analyzer.summary_stats()
        if stats:
            print(f"\n 분석 회차: {stats['total_rounds']}회")
            print(f" 합계 평균: {stats['sum_mean']}  표준편차: {stats['sum_std']}")
            print(f" 최다 출현: {stats['top5_freq']}")
            print(f" 장기 미출현 (회차 경과): {stats['coldest5']}")

        exclude_nums = set(self.exclude_manager.get_exclude_numbers())
        if exclude_nums:
            print(f"\n 제외번호 적용: {sorted(exclude_nums)}")

        print(f"\n 30,000개 후보 조합 분석 중... (잠시 대기)")
        results = self.comp_analyzer.generate_recommendations(
            num_recommendations=1,
            exclude_numbers=exclude_nums,
        )
        if not results:
            print("\n[WARN] 추천 조합을 생성할 수 없습니다.")
            return

        rec = results[0]
        nums = rec['numbers']
        score = rec['score']
        print(f"\n{'─' * 60}")
        print(f" 최고 점수 추천번호: {nums}  (종합점수: {score:.4f})")
        for label, val in self.comp_analyzer.indicator_report(nums).items():
            bar = '█' * int(val * 20)
            print(f"   {label}: {val:.4f}  {bar}")
        save = input("\n   저장하시겠습니까? (y/n): ").lower()
        if save == 'y':
            self.storage.save_combination(nums, "10지표 종합 추천")
            print("    저장되었습니다.")


if __name__ == "__main__":
    app = LottoSystem()
    app.run()
