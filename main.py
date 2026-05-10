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
        print(" 9. 전체 패턴 분석 기반 번호 추천")
        print("10. 역(逆) 군중심리 추천 (당첨금 극대화)")
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
            elif choice == '10':
                self.recommend_anti_crowd()
            elif choice == '0':
                print("\n 프로그램을 종료합니다.")
                break
            else:
                print("\n 잘못된 입력입니다.")
            input("\n계속하려면 Enter를 누르세요...")

    # ── 최신 회차 당첨번호 분석 ────────────────────────

    def _analyze_latest_round(self):
        """가장 최신 회차 당첨번호의 상세 분석을 출력합니다."""
        rows = self._load_round_data()   # 최신순 정렬
        if not rows:
            return

        latest = rows[0]
        prev   = rows[1] if len(rows) > 1 else None

        round_no  = latest.get('회차', '?')
        date_str  = latest.get('날짜', '')
        bonus_raw = latest.get('보너스번호', '')

        # 번호 파싱
        nums = []
        for i in range(1, 7):
            try:
                nums.append(int(latest[f'번호{i}']))
            except (ValueError, TypeError):
                pass
        nums.sort()

        try:
            bonus = int(bonus_raw)
        except (ValueError, TypeError):
            bonus = None

        if not nums:
            return

        # ── 전체 통계 (stat_analyzer 사용) ──
        sum_stats    = self.stat_analyzer.analyze_sum_range()   if self.stat_analyzer else {}
        odd_stats    = self.stat_analyzer.analyze_odd_even()    if self.stat_analyzer else {}
        section_hist = (self.stat_analyzer.analyze_section_distribution()
                        if self.stat_analyzer else {})
        all_data     = (self.stat_analyzer.historical_data
                        if self.stat_analyzer else [])

        avg_sum = float(sum_stats.get('avg_sum', 138))
        min_sum = int(sum_stats.get('min_sum', 21))
        max_sum = int(sum_stats.get('max_sum', 279))
        avg_odd = float(odd_stats.get('avg_odd', 3.0))

        # 이번 회차 값
        total_sum   = sum(nums)
        odd_count   = sum(1 for n in nums if n % 2 != 0)
        even_count  = 6 - odd_count
        consec_pairs = sum(1 for a, b in zip(nums, nums[1:]) if b - a == 1)

        s1 = sum(1 for n in nums if 1  <= n <= 15)
        s2 = sum(1 for n in nums if 16 <= n <= 30)
        s3 = sum(1 for n in nums if 31 <= n <= 45)

        # 합계 백분위
        if all_data and max_sum > min_sum:
            lower = sum(
                1 for row in all_data
                if sum(int(row.get(f'번호{i}', 0)) for i in range(1, 7)) < total_sum
            )
            percentile = lower / len(all_data) * 100
        else:
            percentile = 50.0

        # 컬러 그룹 구성
        grp_counts = {}
        for gname, lo, hi, gcol in self._COLOR_GROUPS:
            cnt = sum(1 for n in nums if lo <= n <= hi)
            if cnt:
                grp_counts[gname] = (cnt, gcol)

        # 직전 회차 겹침
        overlap_nums = []
        if prev:
            prev_set = set()
            for i in range(1, 7):
                try:
                    prev_set.add(int(prev[f'번호{i}']))
                except (ValueError, TypeError):
                    pass
            overlap_nums = [n for n in nums if n in prev_set]

        # ── 출력 ──
        reset  = '\033[0m'
        bold   = '\033[1m'
        white  = '\033[97m'
        gray   = '\033[90m'
        green  = '\033[92m'
        red    = '\033[91m'
        yellow = '\033[93m'
        cyan   = '\033[96m'

        title_extra = f"  {gray}{date_str}{reset}" if date_str else ''
        print()
        print("╔" + "═" * 62 + "╗")
        header_text = f"  최신 당첨번호 분석  ({round_no}회{title_extra})"
        print(f"║{bold}{cyan}{header_text}{reset}")
        print("╠" + "═" * 62 + "╣")

        # 컬러 볼 라인
        balls_str = "  ".join(self._ball(n) for n in nums)
        bonus_str = (f"  {gray}+{reset}  {self._ball(bonus, is_bonus=True)}"
                     if bonus else '')
        print(f"║   {balls_str}{bonus_str}")
        print("╠" + "─" * 62 + "╣")

        # 합계
        diff      = total_sum - avg_sum
        diff_sign = f"+{diff:.1f}" if diff >= 0 else f"{diff:.1f}"
        pct_label = f"상위 {100-percentile:.0f}%" if percentile >= 50 else f"하위 {percentile:.0f}%"
        print(f"║  합계       {bold}{total_sum:>4}{reset}  "
              f"(전체 평균 {avg_sum:.1f} 대비 {yellow}{diff_sign}{reset}  ·  {gray}{pct_label}{reset})")

        # 홀짝
        odd_diff = odd_count - round(avg_odd)
        odd_mark = (f"{green}+{odd_diff}{reset}" if odd_diff > 0
                    else (f"{red}{odd_diff}{reset}" if odd_diff < 0 else f"{gray}±0{reset}"))
        print(f"║  홀짝       홀수 {bold}{odd_count}{reset}개 / 짝수 {bold}{even_count}{reset}개"
              f"  (평균 홀수 {avg_odd:.1f}개 대비 {odd_mark})")

        # 구간 분포
        hist_pct = section_hist.get('percentages', {})
        def _bar(cnt):
            return '●' * cnt + '○' * (6 - cnt)
        print(f"║  구간 분포  1-15: {bold}{s1}{reset}개 {gray}{_bar(s1)}{reset}  "
              f"16-30: {bold}{s2}{reset}개 {gray}{_bar(s2)}{reset}  "
              f"31-45: {bold}{s3}{reset}개 {gray}{_bar(s3)}{reset}")

        # 연속 번호
        if consec_pairs == 0:
            consec_label = f"{gray}없음{reset}"
        else:
            pairs = [(a, b) for a, b in zip(nums, nums[1:]) if b - a == 1]
            pairs_str = ', '.join(f"{a}-{b}" for a, b in pairs)
            consec_label = f"{yellow}{consec_pairs}쌍  ({pairs_str}){reset}"
        print(f"║  연속 번호  {consec_label}")

        # 컬러 그룹 구성
        grp_parts = []
        for gname, lo, hi, gcol in self._COLOR_GROUPS:
            if gname in grp_counts:
                cnt, gcol2 = grp_counts[gname]
                grp_parts.append(
                    f"{gcol2}{bold}{white}{gname}{reset} {cnt}개"
                )
        print(f"║  컬러 구성  {'  ·  '.join(grp_parts)}")

        # 직전 회차 대비
        if prev:
            prev_no = prev.get('회차', '?')
            if overlap_nums:
                ov_balls = '  '.join(self._ball(n) for n in sorted(overlap_nums))
                print(f"║  직전 대비  {prev_no}회와 {bold}{len(overlap_nums)}{reset}개 일치: {ov_balls}")
            else:
                print(f"║  직전 대비  {prev_no}회와 {gray}겹치는 번호 없음{reset}")

        print("╚" + "═" * 62 + "╝")

    # ── 최신 회차 분석 끝 ───────────────────────────────

    def analyze_winning_numbers(self):
        """1. 당첨번호 분석"""
        if not self.stat_analyzer or not self.stat_analyzer.historical_data:
            print("\n[WARN] 데이터가 없거나 로드되지 않았습니다. 메뉴 7번(데이터 수집)을 실행하거나 파일을 확인해주세요.")
            return

        # 최신 회차 당첨번호 분석 (신규)
        self._analyze_latest_round()

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

    # (이름, 시작, 끝, ANSI 색상코드)
    _COLOR_GROUPS = [
        ('노랑', 1,  10, '\033[43m'),
        ('파랑', 11, 20, '\033[44m'),
        ('빨강', 21, 30, '\033[41m'),
        ('회색', 31, 40, '\033[100m'),
        ('초록', 41, 45, '\033[42m'),
    ]

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

    # ── 종합 패턴 분석 ──────────────────────────────

    def _analyze_color_patterns(self, rows: list) -> dict:
        """최근 N회 데이터로 컬러 그룹별 패턴을 분석합니다.

        Returns:
            {
              'n_rounds': int,
              'groups': {
                  그룹이름: {
                      'lo', 'hi', 'color',
                      'avg_all': float,   # 전체 평균 출현 수/회
                      'avg_recent': float,# 최근 5회 평균
                      'trend': '↑'|'↓'|'→',
                      'top5': [int, ...], # 가중 빈도 상위 5개 번호
                  }
              },
              'num_weight': {번호: float},   # 번호별 가중 빈도
              'num_count':  {번호: int},     # 번호별 출현 횟수
            }
        """
        from collections import defaultdict

        n_rounds = len(rows)
        if n_rounds == 0:
            return {}

        recent5 = min(5, n_rounds)
        group_counts: dict = {name: [] for name, *_ in self._COLOR_GROUPS}
        num_weight: dict   = defaultdict(float)
        num_count:  dict   = defaultdict(int)

        num_appeared: dict = defaultdict(list)   # {번호: [(회차번호, 몇회전), ...]}

        for rank, row in enumerate(rows):   # rows[0] = 최신 회차
            w = 1.0 / (rank + 1)           # 최신일수록 가중치 ↑
            round_no = row.get('회차', '?')
            nums = []
            for i in range(1, 7):
                try:
                    nums.append(int(row[f'번호{i}']))
                except (ValueError, TypeError):
                    pass

            for name, lo, hi, _ in self._COLOR_GROUPS:
                group_counts[name].append(sum(1 for n in nums if lo <= n <= hi))

            for n in nums:
                num_weight[n] += w
                num_count[n]  += 1
                num_appeared[n].append((round_no, rank + 1))  # rank+1 = 몇 회차 전

        groups = {}
        for name, lo, hi, color in self._COLOR_GROUPS:
            counts      = group_counts[name]
            avg_all     = sum(counts) / n_rounds
            avg_recent  = sum(counts[:recent5]) / recent5

            if avg_recent > avg_all + 0.15:
                trend = '↑'
            elif avg_recent < avg_all - 0.15:
                trend = '↓'
            else:
                trend = '→'

            group_nums = sorted(
                range(lo, hi + 1),
                key=lambda n: num_weight.get(n, 0.0),
                reverse=True,
            )
            groups[name] = {
                'lo': lo, 'hi': hi, 'color': color,
                'avg_all': avg_all, 'avg_recent': avg_recent,
                'trend': trend,
                'top5': group_nums[:5],
                'all_nums': group_nums,  # 가중치 정렬된 전체 목록
            }

        return {
            'n_rounds': n_rounds,
            'groups': groups,
            'num_weight':   dict(num_weight),
            'num_count':    dict(num_count),
            'num_appeared': dict(num_appeared),   # {번호: [(회차, 몇회전), ...]}
        }

    def _recommend_by_color_pattern(self, analysis: dict,
                                    prev_nums: set | None = None) -> tuple:
        """컬러 패턴 분석으로 6개 추천번호와 그룹별 픽 수를 반환합니다.

        알고리즘:
          1. 트렌드를 반영한 기대값(raw_picks)을 그룹별로 계산
          2. Largest Remainder Method로 합=6이 되도록 정수화
          3. 각 그룹에서 가중 빈도 상위 번호를 순서대로 선택
          4. 부족분은 전체 가중 빈도 순으로 보충
          5. 직전 회차 번호 포함을 최대 1개로 제한

        Args:
            analysis:   _analyze_color_patterns() 반환값
            prev_nums:  직전 회차 당첨번호 집합 (None이면 제한 없음)

        Returns:
            (sorted_numbers: list[int], pick_counts: dict[str, int])
        """
        if not analysis or not analysis.get('groups'):
            return [], {}

        groups     = analysis['groups']
        num_weight = analysis['num_weight']

        # 1. 트렌드 반영 기대값
        raw_picks: dict = {}
        for name, info in groups.items():
            avg = info['avg_all']
            rct = info['avg_recent']
            if info['trend'] == '↑':
                raw_picks[name] = avg * 0.4 + rct * 0.6
            elif info['trend'] == '↓':
                raw_picks[name] = avg * 0.6 + rct * 0.4
            else:
                raw_picks[name] = (avg + rct) / 2.0

        # 2. Largest Remainder Method → 합 = 6
        floors = {name: int(v) for name, v in raw_picks.items()}
        remainders = sorted(
            raw_picks.items(),
            key=lambda x: x[1] - int(x[1]),
            reverse=True,
        )
        deficit = 6 - sum(floors.values())
        pick_counts: dict = dict(floors)
        for i in range(max(0, deficit)):
            pick_counts[remainders[i % len(remainders)][0]] += 1

        # 3. 각 그룹에서 상위 번호 선택
        selected: list = []
        for name, info in groups.items():
            cnt = pick_counts.get(name, 0)
            if cnt == 0:
                continue
            pool = [n for n in info['all_nums'] if n not in selected]
            selected.extend(pool[:cnt])

        # 4. 혹시 6개 미만이면 전체 가중치 순으로 보충
        if len(selected) < 6:
            all_sorted = sorted(
                range(1, 46),
                key=lambda n: num_weight.get(n, 0.0),
                reverse=True,
            )
            for n in all_sorted:
                if n not in selected:
                    selected.append(n)
                if len(selected) == 6:
                    break

        # 5. 직전 회차 번호 최대 1개 제한
        if prev_nums:
            selected = self._limit_prev_overlap(selected, analysis, prev_nums)

        return sorted(selected[:6]), pick_counts

    def _limit_prev_overlap(self, selected: list, analysis: dict,
                            prev_nums: set) -> list:
        """직전 회차 번호와의 겹침을 최대 1개로 줄입니다.

        겹치는 번호 중 가중 빈도가 가장 낮은 것부터 같은 컬러 그룹 내
        직전 회차 미포함 번호로 교체합니다.
        """
        num_weight = analysis['num_weight']
        overlap = [n for n in selected if n in prev_nums]

        if len(overlap) <= 1:
            return selected   # 이미 조건 충족

        # 가중치 낮은 순으로 정렬 → 낮은 것부터 교체 (가장 높은 1개는 남김)
        overlap_sorted = sorted(overlap, key=lambda n: num_weight.get(n, 0.0))
        to_replace = overlap_sorted[:-1]   # 마지막(가중치 최고) 1개는 유지

        result = list(selected)
        for num_out in to_replace:
            # 같은 컬러 그룹에서 대체 후보 탐색
            group_info = next(
                (info for name, info in analysis['groups'].items()
                 if info['lo'] <= num_out <= info['hi']),
                None,
            )
            candidate = None
            if group_info:
                for cand in group_info['all_nums']:
                    if cand not in result and cand not in prev_nums:
                        candidate = cand
                        break
            # 같은 그룹 내 대체 불가 → 전체에서 가중치 순 탐색
            if candidate is None:
                for cand in sorted(range(1, 46),
                                   key=lambda n: num_weight.get(n, 0.0),
                                   reverse=True):
                    if cand not in result and cand not in prev_nums:
                        candidate = cand
                        break
            if candidate is not None:
                result.remove(num_out)
                result.append(candidate)

        return result

    def _print_color_analysis(self, analysis: dict, recommended: list,
                              pick_counts: dict):
        """컬러 패턴 분석 결과와 추천번호를 출력합니다."""
        if not analysis:
            return

        reset = '\033[0m'
        bold  = '\033[1m'
        white = '\033[97m'
        gray  = '\033[90m'

        n = analysis['n_rounds']
        print()
        print("╔" + "═" * 62 + "╗")
        print(f"║{bold}  컬러 패턴 분석  (최근 {n}회 기준){reset}" +
              " " * (62 - 19 - len(str(n))) + "║")
        print("╠" + "═" * 62 + "╣")
        header = (f"  {'컬러':<7} {'번호대':<7} {'전체평균':>6} "
                  f"{'최근5회':>7} {'트렌드':>5}  {'픽수':>3}  상위 번호")
        print(f"║{header:<62}║")
        print("╠" + "─" * 62 + "╣")

        for name, lo, hi, color in self._COLOR_GROUPS:
            info = groups = analysis['groups'][name]
            avg_all    = info['avg_all']
            avg_recent = info['avg_recent']
            trend      = info['trend']
            top5       = info['top5']
            cnt        = pick_counts.get(name, 0)

            t_color = ('\033[92m' if trend == '↑' else
                       '\033[91m' if trend == '↓' else '\033[93m')
            label = f"{color}{bold}{white}{name}{reset}"
            top_str = ', '.join(str(n) for n in top5[:4])

            row_str = (f"  {label}  {lo:2d}~{hi:2d}   "
                       f"{avg_all:5.2f}    {avg_recent:5.2f}   "
                       f"{t_color}{trend}{reset}   {cnt:2d}  {top_str}")
            # 박스 너비 보정 (ANSI 코드는 출력 폭에 미포함)
            print(f"║{row_str}")

        print("╠" + "═" * 62 + "╣")

        # 추천번호 출력
        balls_str = "  ".join(self._ball(n) for n in recommended)
        print(f"║  {bold}이번 회차 추천 번호{reset}  ({gray}컬러 패턴 기반{reset})")
        print(f"║")
        print(f"║   {balls_str}")
        print(f"║")
        print("╚" + "═" * 62 + "╝")

    def _print_recommendation_reasons(self, analysis: dict, recommended: list,
                                      pick_counts: dict, prev_nums: set):
        """추천번호별 선택 이유를 출력합니다.

        직전 회차 번호가 포함된 경우 강조하며, 모든 추천번호의
        선택 근거(그룹 순위·출현 이력·트렌드 반영)를 표시합니다.
        """
        if not analysis or not recommended:
            return

        reset  = '\033[0m'
        bold   = '\033[1m'
        white  = '\033[97m'
        gray   = '\033[90m'
        yellow = '\033[93m'
        red    = '\033[91m'
        green  = '\033[92m'

        num_weight   = analysis['num_weight']
        num_count    = analysis['num_count']
        num_appeared = analysis['num_appeared']
        n_rounds     = analysis['n_rounds']

        print()
        print("┌" + "─" * 62 + "┐")
        print(f"│{bold}  추천번호 선택 이유 분석{reset}" + " " * 38 + "│")
        print("├" + "─" * 62 + "┤")

        for num in recommended:
            # 소속 그룹 정보
            group_name = group_color = group_rank = None
            for gname, lo, hi, gcol in self._COLOR_GROUPS:
                if lo <= num <= hi:
                    group_name  = gname
                    group_color = gcol
                    all_in_grp  = analysis['groups'][gname]['all_nums']
                    group_rank  = all_in_grp.index(num) + 1 if num in all_in_grp else '-'
                    break

            ball_str    = self._ball(num)
            count       = num_count.get(num, 0)
            appeared    = num_appeared.get(num, [])  # [(회차, 몇회전), ...]
            w           = num_weight.get(num, 0.0)
            trend       = analysis['groups'][group_name]['trend'] if group_name else '→'
            grp_pick    = pick_counts.get(group_name, 0)

            # 직전 회차 포함 여부
            is_prev = num in prev_nums
            flag    = f" {red}★직전 회차 포함{reset}" if is_prev else ''

            # 출현 회차 요약 (최근 3개)
            appeared_str = ''
            if appeared:
                recent3 = appeared[:3]
                parts   = [f"{r}회({d}회전)" for r, d in recent3]
                if len(appeared) > 3:
                    parts.append(f"외 {len(appeared)-3}회")
                appeared_str = ', '.join(parts)

            # 트렌드 표시
            t_sym   = {'↑': green + '↑ 상승', '↓': red + '↓ 하락', '→': yellow + '→ 안정'}[trend]
            t_label = f"{t_sym}{reset}"

            # 라인 출력
            label = f"{group_color}{bold}{white}{group_name}{reset}" if group_name else ''
            print(f"│  {ball_str}  {label} {group_rank}순위{flag}")
            print(f"│        출현: {count}/{n_rounds}회  가중빈도: {w:.3f}  그룹 트렌드: {t_label} → {grp_pick}개 배정")
            if appeared_str:
                print(f"│        출현 회차: {gray}{appeared_str}{reset}")

            # 직전 회차 포함 이유 상세 설명
            if is_prev:
                rank_in_all = sorted(num_weight.keys(),
                                     key=lambda x: num_weight[x],
                                     reverse=True)
                overall_rank = rank_in_all.index(num) + 1 if num in rank_in_all else '-'
                print(f"│        {yellow}→ 직전 회차 당첨번호이나 전체 가중빈도 {overall_rank}위 · "
                      f"{group_name} 그룹 {group_rank}순위로 선택{reset}")

            print("│")

        print("└" + "─" * 62 + "┘")

    # ── 종합 패턴 분석 ──────────────────────────────

    def _analyze_all_patterns(self, rows: list) -> dict:
        """합계·홀짝·구간분포·연속번호·컬러·직전대비 종합 패턴 분석.

        Returns dict with keys:
          n_rounds, color (기존 _analyze_color_patterns 결과),
          pick_counts (LRM 결정된 그룹별 픽수),
          sum, odd, consec, section, prev_overlap
        """
        from collections import Counter
        import statistics as _stats

        if not rows:
            return {}

        # 기존 컬러 분석 재사용
        color = self._analyze_color_patterns(rows)
        recent5 = min(5, len(rows))

        per_round: list = []
        for rank, row in enumerate(rows):
            nums = []
            for i in range(1, 7):
                try:
                    nums.append(int(row[f'번호{i}']))
                except (ValueError, TypeError):
                    pass
            nums.sort()
            if len(nums) != 6:
                continue

            # 직전 회차 번호
            prev_set: set = set()
            if rank + 1 < len(rows):
                for i in range(1, 7):
                    try:
                        prev_set.add(int(rows[rank + 1][f'번호{i}']))
                    except (ValueError, TypeError):
                        pass

            per_round.append({
                'sum':   sum(nums),
                'odd':   sum(1 for n in nums if n % 2 != 0),
                'consec': sum(1 for a, b in zip(nums, nums[1:]) if b - a == 1),
                's1':    sum(1 for n in nums if  1 <= n <= 15),
                's2':    sum(1 for n in nums if 16 <= n <= 30),
                's3':    sum(1 for n in nums if 31 <= n <= 45),
                'prev_overlap': len([n for n in nums if n in prev_set]),
                'is_recent': rank < recent5,
            })

        n = len(per_round)
        if n == 0:
            return {'color': color, 'n_rounds': 0}

        def _make_stat(key: str, threshold: float = 0.15) -> dict:
            vals_all = [r[key] for r in per_round]
            vals_rec = [r[key] for r in per_round if r['is_recent']]
            avg_a = sum(vals_all) / len(vals_all)
            avg_r = sum(vals_rec) / len(vals_rec) if vals_rec else avg_a
            if avg_r > avg_a + threshold:
                trend = '↑'
            elif avg_r < avg_a - threshold:
                trend = '↓'
            else:
                trend = '→'
            return {'avg_all': avg_a, 'avg_recent': avg_r,
                    'trend': trend, 'vals': vals_all}

        sum_s    = _make_stat('sum',   threshold=5.0)
        odd_s    = _make_stat('odd',   threshold=0.2)
        consec_s = _make_stat('consec', threshold=0.2)
        s1_s     = _make_stat('s1',   threshold=0.2)
        s2_s     = _make_stat('s2',   threshold=0.2)
        s3_s     = _make_stat('s3',   threshold=0.2)
        prev_s   = _make_stat('prev_overlap', threshold=0.3)

        # 합계 목표 범위
        std_sum  = _stats.stdev(sum_s['vals']) if n >= 2 else 25.0
        blend    = sum_s['avg_all'] * 0.5 + sum_s['avg_recent'] * 0.5
        sum_lo   = max(21,  int(blend - std_sum * 0.6))
        sum_hi   = min(279, int(blend + std_sum * 0.6))

        # 홀수 목표
        odd_target = round(odd_s['avg_all'] * 0.5 + odd_s['avg_recent'] * 0.5)

        # 연속 목표: 가장 빈번한 값
        consec_target = Counter(consec_s['vals']).most_common(1)[0][0]

        # 구간 목표: blend 반올림 후 합=6 조정
        raw_ts = [
            s1_s['avg_all'] * 0.5 + s1_s['avg_recent'] * 0.5,
            s2_s['avg_all'] * 0.5 + s2_s['avg_recent'] * 0.5,
            s3_s['avg_all'] * 0.5 + s3_s['avg_recent'] * 0.5,
        ]
        t_floors = [int(v) for v in raw_ts]
        deficit  = 6 - sum(t_floors)
        order    = sorted(range(3), key=lambda i: raw_ts[i] - t_floors[i], reverse=True)
        for i in range(max(0, deficit)):
            t_floors[order[i % 3]] += 1
        t_s1, t_s2, t_s3 = t_floors

        # 컬러 그룹 픽수 (LRM, _recommend_by_color_pattern과 동일 로직)
        groups = color['groups']
        raw_picks: dict = {}
        for name, info in groups.items():
            a, r = info['avg_all'], info['avg_recent']
            if info['trend'] == '↑':
                raw_picks[name] = a * 0.4 + r * 0.6
            elif info['trend'] == '↓':
                raw_picks[name] = a * 0.6 + r * 0.4
            else:
                raw_picks[name] = (a + r) / 2.0

        floors_c   = {name: int(v) for name, v in raw_picks.items()}
        remainders = sorted(raw_picks.items(),
                            key=lambda x: x[1] - int(x[1]), reverse=True)
        deficit_c  = 6 - sum(floors_c.values())
        pick_counts: dict = dict(floors_c)
        for i in range(max(0, deficit_c)):
            pick_counts[remainders[i % len(remainders)][0]] += 1

        return {
            'n_rounds':  n,
            'color':     color,
            'pick_counts': pick_counts,
            'sum':    {**sum_s,    'std': std_sum, 'blend': blend,
                       'target_lo': sum_lo, 'target_hi': sum_hi},
            'odd':    {**odd_s,    'target': odd_target},
            'consec': {**consec_s, 'target': consec_target},
            'section': {
                's1': s1_s, 's2': s2_s, 's3': s3_s,
                'target_s1': t_s1, 'target_s2': t_s2, 'target_s3': t_s3,
            },
            'prev_overlap': prev_s,
        }

    def _recommend_by_all_patterns(self, analysis: dict,
                                   prev_nums: set | None = None) -> tuple:
        """종합 패턴 기반 번호 추천.

        알고리즘:
          1. 컬러 픽수(pick_counts)에 따라 그룹별 후보 조합 생성 (top-6)
          2. itertools.product로 전체 조합 열거
          3. 합계·홀짝·구간·연속번호·가중빈도 5개 지표 점수 합산
          4. 직전 회차 ≤1 제한 적용 후 최고 점수 조합 반환

        Returns:
            (sorted_numbers: list[int], pick_counts: dict[str, int])
        """
        import itertools

        if not analysis or not analysis.get('color'):
            return [], {}

        color       = analysis['color']
        groups      = color['groups']
        num_weight  = color['num_weight']
        pick_counts = analysis['pick_counts']

        blend      = analysis['sum']['blend']
        sum_lo     = analysis['sum']['target_lo']
        sum_hi     = analysis['sum']['target_hi']
        odd_target = analysis['odd']['target']
        c_target   = analysis['consec']['target']
        t_s1       = analysis['section']['target_s1']
        t_s2       = analysis['section']['target_s2']
        t_s3       = analysis['section']['target_s3']

        TOP_K = 6   # 그룹당 후보 번호 수

        # 그룹별 조합 목록
        group_combos: list = []
        for name, _lo, _hi, _ in self._COLOR_GROUPS:
            cnt  = pick_counts.get(name, 0)
            pool = groups[name]['all_nums'][:TOP_K]
            if cnt == 0 or cnt > len(pool):
                group_combos.append([tuple(pool[:cnt]) if cnt <= len(pool) else tuple()])
            else:
                group_combos.append(list(itertools.combinations(pool, cnt)))

        best       = None
        best_score = float('-inf')

        for product_combo in itertools.product(*group_combos):
            nums: list = []
            for grp in product_combo:
                nums.extend(grp)

            if len(set(nums)) != 6:
                continue

            nums_s = sorted(nums)

            # 직전 회차 ≤1 제한
            if prev_nums and sum(1 for n in nums_s if n in prev_nums) > 1:
                continue

            # 5개 지표 채점
            total  = sum(nums_s)
            odd    = sum(1 for n in nums_s if n % 2 != 0)
            consec = sum(1 for a, b in zip(nums_s, nums_s[1:]) if b - a == 1)
            s1     = sum(1 for n in nums_s if  1 <= n <= 15)
            s2     = sum(1 for n in nums_s if 16 <= n <= 30)
            s3     = sum(1 for n in nums_s if 31 <= n <= 45)

            score = 0.0
            score += 3.0 if sum_lo <= total <= sum_hi \
                         else -min(3.0, abs(total - blend) / 20.0)    # 합계
            score -= abs(odd - odd_target) * 1.2                      # 홀짝
            score += 1.0 if consec == c_target \
                         else -abs(consec - c_target) * 0.6           # 연속
            score -= (abs(s1 - t_s1) + abs(s2 - t_s2)
                      + abs(s3 - t_s3)) * 0.4                         # 구간
            score += sum(num_weight.get(n, 0) for n in nums_s) * 0.2  # 가중빈도

            if score > best_score:
                best_score = score
                best       = nums_s

        # 폴백: 모든 조합이 직전 회차 제한에 걸릴 때
        if best is None:
            best, _ = self._recommend_by_color_pattern(color, prev_nums)

        return best, pick_counts

    def _print_all_pattern_analysis(self, analysis: dict,
                                    recommended: list, prev_nums: set):
        """종합 패턴 분석 테이블 + 추천번호를 출력합니다."""
        if not analysis:
            return

        reset  = '\033[0m'
        bold   = '\033[1m'
        white  = '\033[97m'
        gray   = '\033[90m'
        green  = '\033[92m'
        yellow = '\033[93m'

        def tc(t):   # trend color
            return green if t == '↑' else ('\033[91m' if t == '↓' else yellow)

        def chk(ok): # ✓ / △
            return f"{green}✓{reset}" if ok else f"{yellow}△{reset}"

        n = analysis['n_rounds']
        print()
        print("╔" + "═" * 66 + "╗")
        print(f"║{bold}  종합 패턴 분석  (최근 {n}회 기준){reset}")
        print("╠" + "═" * 66 + "╣")
        hdr = (f"  {'패턴':<13} {'전체평균':>8} {'최근5회':>8}"
               f"  {'트렌드':>5}   이번회차 목표")
        print(f"║{hdr}")
        print("╠" + "─" * 66 + "╣")

        # ── 합계
        s = analysis['sum']
        print(f"║  {'합계':<13} {s['avg_all']:>8.1f} {s['avg_recent']:>8.1f}"
              f"  {tc(s['trend'])}{s['trend']}{reset}   "
              f"{s['target_lo']} ~ {s['target_hi']}")

        # ── 홀수 개수
        o = analysis['odd']
        print(f"║  {'홀수 개수':<12} {o['avg_all']:>8.2f} {o['avg_recent']:>8.2f}"
              f"  {tc(o['trend'])}{o['trend']}{reset}   {o['target']}개")

        # ── 구간별
        sec = analysis['section']
        for label, key, tkey in [('1구간(1-15)',  's1', 'target_s1'),
                                  ('2구간(16-30)', 's2', 'target_s2'),
                                  ('3구간(31-45)', 's3', 'target_s3')]:
            st = sec[key]
            print(f"║  {label:<13} {st['avg_all']:>8.2f} {st['avg_recent']:>8.2f}"
                  f"  {tc(st['trend'])}{st['trend']}{reset}   {sec[tkey]}개")

        # ── 연속번호
        c = analysis['consec']
        print(f"║  {'연속번호 쌍':<12} {c['avg_all']:>8.2f} {c['avg_recent']:>8.2f}"
              f"  {tc(c['trend'])}{c['trend']}{reset}   {c['target']}쌍")

        # ── 직전회차 겹침
        p = analysis['prev_overlap']
        print(f"║  {'직전회차 겹침':<11} {p['avg_all']:>8.2f} {p['avg_recent']:>8.2f}"
              f"  {tc(p['trend'])}{p['trend']}{reset}   ≤1개 {gray}(강제 적용){reset}")

        print("╠" + "─" * 66 + "╣")

        # ── 컬러 그룹
        color       = analysis['color']
        pick_counts = analysis['pick_counts']
        hdr2 = (f"  {'컬러 그룹':<13} {'전체평균':>8} {'최근5회':>8}"
                f"  {'트렌드':>5}   픽수")
        print(f"║{hdr2}")
        print("╠" + "─" * 66 + "╣")
        for name, lo, hi, gcol in self._COLOR_GROUPS:
            info  = color['groups'][name]
            label = f"{gcol}{bold}{white}{name}{reset}"
            cnt   = pick_counts.get(name, 0)
            print(f"║  {label}  {lo:2d}~{hi:2d}  "
                  f"{info['avg_all']:>7.2f}  {info['avg_recent']:>7.2f}"
                  f"  {tc(info['trend'])}{info['trend']}{reset}    {cnt}개")

        print("╠" + "═" * 66 + "╣")

        # ── 추천번호
        balls_str = "  ".join(self._ball(n) for n in recommended)
        print(f"║  {bold}이번 회차 추천 번호{reset}  {gray}(종합 패턴 기반){reset}")
        print(f"║")
        print(f"║   {balls_str}")

        # 목표 충족 검증
        if recommended:
            total  = sum(recommended)
            odd    = sum(1 for n in recommended if n % 2 != 0)
            consec = sum(1 for a, b in zip(recommended, recommended[1:]) if b - a == 1)
            s1     = sum(1 for n in recommended if  1 <= n <= 15)
            s2     = sum(1 for n in recommended if 16 <= n <= 30)
            s3     = sum(1 for n in recommended if 31 <= n <= 45)
            ov     = sum(1 for n in recommended if n in prev_nums) if prev_nums else 0

            s_ok = analysis['sum']['target_lo'] <= total <= analysis['sum']['target_hi']
            o_ok = odd    == analysis['odd']['target']
            c_ok = consec <= analysis['consec']['target'] + 1
            p_ok = ov <= 1

            print(f"║")
            print(f"║   합계 {bold}{total}{reset} {chk(s_ok)}"
                  f"   홀수 {bold}{odd}{reset}개 {chk(o_ok)}"
                  f"   구간 {bold}{s1}/{s2}/{s3}{reset}"
                  f"   연속 {bold}{consec}{reset}쌍 {chk(c_ok)}"
                  f"   직전겹침 {bold}{ov}{reset}개 {chk(p_ok)}")

        print(f"║")
        print("╚" + "═" * 66 + "╝")

    # ── 종합 패턴 분석 끝 ────────────────────────────

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
        """9. 전체 패턴 분석 기반 번호 추천"""
        rows = self._load_round_data()
        if not rows:
            print("\n[WARN] 데이터가 없습니다. 메뉴 7번(데이터 수집)을 먼저 실행해주세요.")
            return

        total     = len(rows)
        max_round = int(rows[0].get('회차', 0))
        min_round = int(rows[-1].get('회차', 0))

        print(f"\n 전체 {total}회차 데이터 패턴 분석 중... "
              f"({min_round}회 ~ {max_round}회)")

        # 직전(최신) 회차 번호 추출 및 표시
        prev_nums: set = set()
        latest = rows[0]
        for i in range(1, 7):
            try:
                prev_nums.add(int(latest[f'번호{i}']))
            except (ValueError, TypeError):
                pass

        prev_date = latest.get('날짜', '')
        date_str  = f"  {prev_date}" if prev_date else ''
        balls_str = "  ".join(self._ball(n) for n in sorted(prev_nums))
        try:
            bonus_ball = "  \033[90m+\033[0m  " + self._ball(
                int(latest.get('보너스번호', '')), is_bonus=True)
        except (ValueError, TypeError):
            bonus_ball = ''
        print(f" 직전 당첨번호 ({max_round}회{date_str}): {balls_str}{bonus_ball}")

        # 종합 패턴 분석
        analysis_all = self._analyze_all_patterns(rows)
        rec_nums, pick_counts = self._recommend_by_all_patterns(
            analysis_all, prev_nums=prev_nums
        )

        self._print_all_pattern_analysis(analysis_all, rec_nums, prev_nums)
        self._print_recommendation_reasons(
            analysis_all['color'], rec_nums, pick_counts, prev_nums
        )

        # 저장 여부
        if rec_nums:
            save = input("\n 이 추천 번호를 저장하시겠습니까? (y/n): ").lower()
            if save == 'y':
                self.storage.save_combination(
                    rec_nums, f"전체패턴 분석 추천({total}회차)")
                print("   저장되었습니다.")

    # ──────────────────────────────────────────────
    # 10. 역(逆) 군중심리 추천 — 당첨금 극대화
    # ──────────────────────────────────────────────

    # 사람들이 자주 고르는 "행운의 수" / 패턴 번호
    _CROWD_LUCKY     = {3, 7, 9, 13, 17, 21, 23, 27, 33, 37}
    _CROWD_MONTH     = set(range(1, 13))   # 1~12 (월)
    _CROWD_DAY_MAX   = 31                   # 1~31 (생일)

    def _crowd_popularity(self, n: int) -> float:
        """번호의 군중 선호도(0~1). 높을수록 사람들이 많이 고름.

        근거:
          - Cox·Daniel(1995), Simon(1999) 등 복권 선호 연구에 따르면
            플레이어는 생일·기념일·"행운의 수"를 비대칭적으로 선호함.
          - 한국 6/45도 1~31 범위 편중, 끝자리 7 선호 경향이 보고됨.
        """
        score = 0.40   # baseline

        if 1 <= n <= self._CROWD_DAY_MAX:    # 생일 범위 (일)
            score += 0.18
        if n in self._CROWD_MONTH:           # 월 (1~12)
            score += 0.08
        if n in self._CROWD_LUCKY:           # 행운의 수
            score += 0.13
        if n % 10 == 7:                      # 끝자리 7
            score += 0.05
        if n >= 32:                          # 비-생일 영역
            score -= 0.18

        return min(1.0, max(0.0, score))

    def _anti_crowd_score(self, numbers: list, avg_sum: float = 138.2) -> dict:
        """조합의 비-군중성 점수와 세부 항목을 반환합니다.

        실용성 가드:
          - 32~45 비율이 3~4개일 때 최고점, 5개 이상은 감점 (역사적 분포 반영)
          - 연속 1쌍이 최적, 3쌍 이상은 감점 (통계적 비현실)
        """
        nums  = sorted(numbers)
        total = sum(nums)

        individual = sum(1.0 - self._crowd_popularity(n) for n in nums)

        # 합계 일탈: 평균에서 멀수록 좋음 (max 1.5, deviation 50+ 점에서 만점)
        sum_dev   = abs(total - avg_sum)
        sum_score = min(1.5, sum_dev / 50.0)

        # 32~45 비율: 3~4개일 때 최고, 5+ 감점, 6 큰 감점
        high_count = sum(1 for n in nums if n >= 32)
        high_score_table = {0: -0.5, 1: 0.4, 2: 1.0, 3: 1.5, 4: 1.3,
                            5: -0.5, 6: -1.5}
        high_score = high_score_table.get(high_count, 0.0)

        # 연속 가산: 1쌍이 최적, 0쌍은 무난, 2+ 감점
        consec       = sum(1 for a, b in zip(nums, nums[1:]) if b - a == 1)
        consec_score_table = {0: 0.2, 1: 1.0, 2: 0.4, 3: -0.5, 4: -1.0, 5: -2.0}
        consec_score = consec_score_table.get(consec, -2.0)

        # 끝수 다양성 (4~6 우수)
        last_digits      = {n % 10 for n in nums}
        last_digit_score = min(0.6, len(last_digits) / 10.0)

        # 합계가 너무 평범(평균 ±10)이면 감점
        sum_penalty = -1.0 if abs(total - avg_sum) < 10 else 0.0

        # 홀짝 극단(0:6 또는 6:0)이면 감점
        odd  = sum(1 for n in nums if n % 2 != 0)
        even = 6 - odd
        balance_penalty = -0.5 if (odd == 0 or odd == 6) else 0.0

        total_score = (individual + sum_score + high_score + consec_score
                       + last_digit_score + sum_penalty + balance_penalty)

        return {
            'total':            total_score,
            'individual':       individual,
            'sum_score':        sum_score,
            'high_score':       high_score,
            'consec_score':     consec_score,
            'last_digit_score': last_digit_score,
            'sum_penalty':      sum_penalty,
            'balance_penalty':  balance_penalty,
            'sum':              total,
            'high_count':       high_count,
            'consec':           consec,
            'unique_last_digits': len(last_digits),
            'odd':              odd,
            'even':             even,
        }

    def recommend_anti_crowd(self):
        """10. 역(逆) 군중심리 추천"""
        import itertools

        reset, bold, gray = '\033[0m', '\033[1m', '\033[90m'
        cyan, yellow, red = '\033[96m', '\033[93m', '\033[91m'

        print("\n" + "=" * 66)
        print(f"{bold}{cyan}  역(逆) 군중심리 추천 — 당첨금 극대화 전략{reset}")
        print("=" * 66)
        print(f"  {bold}전략 설명{reset}")
        print(f"  · 1등 당첨 확률은 어떤 조합이든 동일합니다 ({gray}1/8,145,060{reset})")
        print(f"  · 그러나 다른 사람과 겹치지 않는 조합을 고르면")
        print(f"    {yellow}당첨 시 분배 인원이 적어 당첨금이 커집니다.{reset}")
        print(f"")
        print(f"  본 추천은 {red}'사람들이 잘 안 고르는'{reset} 조합을 우선합니다:")
        print(f"    - 32~45 (생일 범위 외) 비율 ↑")
        print(f"    - 합계가 평균(138)에서 벗어남 ↑")
        print(f"    - 연속 번호 허용 (사람들은 회피)")
        print(f"    - '행운의 수'(7,17,27,37 등) 회피")
        print(f"    - 직전 회차 번호 포함 허용")
        print("=" * 66)

        # 평균 합계 계산 (전체 데이터)
        rows = self._load_round_data()
        if not rows:
            print("\n[WARN] 데이터가 없습니다. 메뉴 7번(데이터 수집)을 먼저 실행해주세요.")
            return

        sums = []
        for row in rows:
            try:
                sums.append(sum(int(row[f'번호{i}']) for i in range(1, 7)))
            except (ValueError, TypeError):
                continue
        avg_sum = sum(sums) / len(sums) if sums else 138.0

        # 분할 풀: 1~31 비인기 상위 N개 + 32~45 전체
        low_pool  = sorted(
            [n for n in range(1, 32)],
            key=self._crowd_popularity,
        )[:10]
        high_pool = list(range(32, 46))   # 14개

        print(f"\n  비인기 저번대 풀 (1~31 중 군중 선호도 하위 10개):")
        print("  " + '  '.join(self._ball(n) for n in sorted(low_pool)))
        print(f"\n  고번대 풀 (32~45, 모두 비인기):")
        print("  " + '  '.join(self._ball(n) for n in high_pool))

        # 저번대 2~3개 + 고번대 3~4개 조합만 열거 (현실적 분포)
        candidates = []
        for low_n in (2, 3):
            high_n = 6 - low_n
            for low_c in itertools.combinations(low_pool, low_n):
                for high_c in itertools.combinations(high_pool, high_n):
                    candidates.append(sorted(low_c + high_c))

        print(f"\n  {len(candidates):,}개 조합 점수화 중 "
              f"(저번대 2~3 + 고번대 3~4)...\n")

        best        = None
        best_result = None
        best_score  = float('-inf')

        for nums in candidates:
            result = self._anti_crowd_score(nums, avg_sum)
            if result['total'] > best_score:
                best_score  = result['total']
                best        = nums
                best_result = result

        if not best:
            print("[WARN] 추천 조합을 생성할 수 없습니다.")
            return

        self._print_anti_crowd_result(best, best_result, avg_sum)

        # 저장
        save = input("\n 이 추천 번호를 저장하시겠습니까? (y/n): ").lower()
        if save == 'y':
            self.storage.save_combination(best, "역 군중심리 추천")
            print("   저장되었습니다.")

    def _print_anti_crowd_result(self, numbers: list, result: dict,
                                 avg_sum: float):
        """역 군중심리 추천 결과를 박스 형태로 출력합니다."""
        reset, bold, white, gray = '\033[0m', '\033[1m', '\033[97m', '\033[90m'
        green, yellow, red, cyan = '\033[92m', '\033[93m', '\033[91m', '\033[96m'

        balls_str = "  ".join(self._ball(n) for n in numbers)

        print()
        print("╔" + "═" * 66 + "╗")
        print(f"║  {bold}{cyan}이번 회차 추천 번호{reset}  "
              f"{gray}(역 군중심리 — 비인기 조합){reset}")
        print("║")
        print(f"║   {balls_str}")
        print("║")
        print("╠" + "═" * 66 + "╣")
        print(f"║  {bold}조합 특성{reset}")
        print("╠" + "─" * 66 + "╣")

        # 합계
        sum_dev = abs(result['sum'] - avg_sum)
        sum_label = (f"{green}평균에서 {sum_dev:.0f} 이탈 (좋음){reset}"
                     if sum_dev >= 20 else
                     (f"{red}평균에 가까움 (피하고 싶은 영역){reset}"
                      if sum_dev < 10 else f"{yellow}중간{reset}"))
        print(f"║  합계         {bold}{result['sum']}{reset}  "
              f"(전체 평균 {avg_sum:.1f}) — {sum_label}")

        # 32~45 비율
        high_label = (f"{green}우수 (다수 비-생일 영역){reset}"
                      if result['high_count'] >= 3 else
                      (f"{yellow}보통{reset}" if result['high_count'] >= 2 else
                       f"{red}부족{reset}"))
        print(f"║  32~45 번호   {bold}{result['high_count']}{reset}개  — {high_label}")

        # 홀짝
        print(f"║  홀짝         홀수 {bold}{result['odd']}{reset}개 / "
              f"짝수 {bold}{result['even']}{reset}개")

        # 연속
        consec_label = (f"{green}+ 가산점 (사람들 회피){reset}"
                        if result['consec'] > 0 else f"{gray}없음{reset}")
        print(f"║  연속 번호    {bold}{result['consec']}{reset}쌍  — {consec_label}")

        # 끝수 다양성
        print(f"║  끝수 다양성  {bold}{result['unique_last_digits']}{reset}/6 "
              f"(서로 다른 끝자리)")

        print("╠" + "─" * 66 + "╣")
        print(f"║  {bold}번호별 군중 선호도{reset}  "
              f"{gray}(낮을수록 사람들이 잘 안 고름){reset}")
        print("╠" + "─" * 66 + "╣")
        for n in numbers:
            pop = self._crowd_popularity(n)
            bar_len = int(pop * 20)
            bar = '█' * bar_len + '░' * (20 - bar_len)

            if pop < 0.30:
                pop_color = green
                tag = "비인기"
            elif pop < 0.50:
                pop_color = yellow
                tag = "보통"
            else:
                pop_color = red
                tag = "인기 ★"

            reasons = []
            if 1 <= n <= 31: reasons.append("생일범위")
            if n in self._CROWD_LUCKY: reasons.append("행운수")
            if n % 10 == 7: reasons.append("끝자리7")
            if n >= 32: reasons.append("비생일")
            reason_str = (f" {gray}[{', '.join(reasons)}]{reset}"
                          if reasons else '')

            print(f"║   {self._ball(n)}  {pop_color}{bar}{reset} "
                  f"{pop:.2f}  {pop_color}{tag}{reset}{reason_str}")

        print("╠" + "─" * 66 + "╣")
        print(f"║  {bold}종합 점수: {result['total']:.2f}{reset}  "
              f"{gray}(높을수록 비-군중 조합){reset}")
        print(f"║   · 개별 비인기도:   {result['individual']:>5.2f} / 6.00")
        print(f"║   · 합계 일탈:       {result['sum_score']:>5.2f} / 1.50")
        print(f"║   · 32~45 비율:      {result['high_score']:>5.2f} / 1.50")
        print(f"║   · 연속 가산:       {result['consec_score']:>5.2f} / 1.00")
        print(f"║   · 끝수 다양성:     {result['last_digit_score']:>5.2f} / 0.60")
        if result['sum_penalty'] < 0:
            print(f"║   · 평범 합계 감점: {result['sum_penalty']:>5.2f}")
        if result['balance_penalty'] < 0:
            print(f"║   · 홀짝 극단 감점: {result['balance_penalty']:>5.2f}")
        print("╚" + "═" * 66 + "╝")

        print(f"\n  {yellow}💡 참고{reset}: 본 전략은 1등 확률을 높이지 않습니다.")
        print(f"     단지 {bold}당첨 시 분배 인원을 줄여 기댓값을 높이는{reset} "
              f"통계적 시도입니다.")

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
