#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
로또 번호 분석 및 추천 시스템 v3.0
인코딩 문제 해결 및 모듈화 적용 버전
"""

import csv
import random
import os
from collections import Counter
from datetime import datetime

# 모듈화된 분석기 import (선택적)
try:
    from analyzers import (
        ExcludeNumberManager,
        LottoDataCollector,
        StatisticalAnalyzer,
        PatternMatchingAnalyzer,
        EnsembleAnalyzer,
        MersenneTwisterAnalyzer,
        TrendAnalyzer,
        LottoPatternGrouping,
        LinePatternAnalyzer
    )
    ANALYZERS_AVAILABLE = True
except ImportError as e:
    print(f"WARNING: 분석기 모듈 로드 실패: {e}")
    print("   기본 기능만 사용 가능합니다.")
    ANALYZERS_AVAILABLE = False
    ExcludeNumberManager = None
    LottoDataCollector = None
    StatisticalAnalyzer = None

# 유틸리티 import (선택적)
try:
    from utils import (
        check_installation_status,
        show_system_info,
        resolve_data_file,
        LOTTO_NUMBER_COLUMNS,
        BONUS_COLUMN,
        ROUND_COLUMN,
        MAX_LOTTO_NUMBER,
        NUM_LOTTO_NUMBERS_TO_PICK
    )
    UTILS_AVAILABLE = True
except ImportError:
    UTILS_AVAILABLE = False
    # 기본값 설정
    MAX_LOTTO_NUMBER = 45
    NUM_LOTTO_NUMBERS_TO_PICK = 6
    def resolve_data_file():
        return '로또당첨번호.csv'
    def check_installation_status():
        print("[!] utils 모듈을 찾을 수 없습니다.")
    def show_system_info():
        import sys, platform
        print(f"Python: {sys.version}")
        print(f"OS: {platform.system()}")

# DNN 기능 선택적 import
try:
    import tensorflow as tf
    from dnn_lotto_predictor import DNNLottoPredictor
    DNN_AVAILABLE = True
    print(f"[OK] TensorFlow {tf.__version__} 감지됨")
except ImportError:
    DNN_AVAILABLE = False
    print("[!] DNN 기능 비활성화 (TensorFlow 미설치)")

# AI 패턴 학습 라이브러리
try:
    import numpy as np
    import pandas as pd
    from sklearn.cluster import KMeans, DBSCAN
    from sklearn.ensemble import RandomForestClassifier
    AI_PATTERN_AVAILABLE = True
except ImportError:
    AI_PATTERN_AVAILABLE = False

# 전역 설정
DATA_FILE_PATH = resolve_data_file()
DEFAULT_RECENT_COUNT = 51
DEFAULT_MAX_CONSECUTIVE = 3
DEFAULT_MAX_RECENT_OVERLAP = 4


def load_historical_data(filename=None):
    """과거 당첨 번호 데이터를 로드합니다."""
    if filename is None:
        filename = DATA_FILE_PATH

    historical_data = []
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                historical_data.append(row)
        print(f"[OK] {len(historical_data)}개 회차 데이터 로드 완료")
        return historical_data
    except FileNotFoundError:
        print(f"[X] 파일을 찾을 수 없습니다: {filename}")
        return []
    except Exception as e:
        print(f"[X] 데이터 로드 중 오류: {e}")
        return []


def generate_random_numbers(exclude_manager=None, count=1):
    """랜덤 번호를 생성합니다."""
    results = []

    for i in range(count):
        if exclude_manager and exclude_manager.is_valid_for_lotto():
            available = exclude_manager.get_available_numbers()
        else:
            available = list(range(1, MAX_LOTTO_NUMBER + 1))

        if len(available) < NUM_LOTTO_NUMBERS_TO_PICK:
            print("[X] 사용 가능한 번호가 부족합니다.")
            break

        numbers = sorted(random.sample(available, NUM_LOTTO_NUMBERS_TO_PICK))
        results.append(numbers)

    return results


def analyze_patterns(historical_data):
    """패턴 분석을 수행합니다."""
    if not historical_data:
        print("[X] 분석할 데이터가 없습니다.")
        return

    print("\n 패턴 분석 중...")

    # 통계 분석
    stat_analyzer = StatisticalAnalyzer(historical_data)
    frequencies = stat_analyzer.get_number_frequencies()

    print("\n상위 10개 번호:")
    for num, freq in sorted(frequencies.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {num}번: {freq}회")

    # 추세 분석
    if AI_PATTERN_AVAILABLE:
        trend_analyzer = TrendAnalyzer(historical_data)
        hot_numbers = trend_analyzer.get_hot_numbers(top_n=10)
        print(f"\n[HOT] 핫 넘버: {hot_numbers}")

    return frequencies


def main_menu():
    """메인 메뉴를 표시합니다."""
    print("\n" + "="*60)
    print(" 로또 번호 분석 및 추천 시스템 v3.0")
    print("="*60)

    # 분석기 초기화 (있는 경우만)
    exclude_manager = ExcludeNumberManager() if ANALYZERS_AVAILABLE and ExcludeNumberManager else None
    data_collector = LottoDataCollector() if ANALYZERS_AVAILABLE and LottoDataCollector else None

    while True:
        print("\n 메뉴:")
        print("1. 랜덤 번호 생성")
        print("2. 통계 기반 번호 추천")
        print("3. 패턴 분석")
        print("4. 데이터 업데이트")
        print("5. 제외 번호 관리")
        print("6. 시스템 정보")
        print("0. 종료")

        choice = input("\n선택: ").strip()

        if choice == '1':
            count = int(input("생성할 번호 세트 개수 (1-10): ") or "1")
            count = min(max(1, count), 10)

            numbers = generate_random_numbers(exclude_manager, count)
            print(f"\n 생성된 번호 ({len(numbers)}개):")
            for i, nums in enumerate(numbers, 1):
                print(f"  {i}. {nums}")

        elif choice == '2':
            if not ANALYZERS_AVAILABLE or not StatisticalAnalyzer:
                print("[X] 통계 분석기를 사용할 수 없습니다. (패키지 설치 필요)")
                continue

            historical_data = load_historical_data()
            if historical_data:
                stat_analyzer = StatisticalAnalyzer(historical_data)
                exclude_nums = exclude_manager.get_exclude_numbers() if exclude_manager else []
                recommendations = stat_analyzer.get_recommended_numbers(
                    count=5,
                    exclude_numbers=exclude_nums
                )
                print(f"\n 통계 기반 추천 번호 ({len(recommendations)}개):")
                for i, nums in enumerate(recommendations, 1):
                    print(f"  {i}. {nums}")

        elif choice == '3':
            historical_data = load_historical_data()
            analyze_patterns(historical_data)

        elif choice == '4':
            if not data_collector:
                print("[X] 데이터 수집기를 사용할 수 없습니다. (패키지 설치 필요)")
                continue

            print("\n 데이터 업데이트 중...")
            latest = data_collector.get_latest_round()
            if latest:
                print(f"최신 회차: {latest}회")
                data = data_collector.update_latest_data(max_rounds=10)
                if data:
                    data_collector.save_to_csv(data)

        elif choice == '5':
            if not exclude_manager:
                print("[X] 제외 번호 관리를 사용할 수 없습니다. (패키지 설치 필요)")
                continue

            print("\n 제외 번호 관리")
            print("1. 제외 번호 추가")
            print("2. 제외 번호 제거")
            print("3. 제외 번호 보기")
            print("4. 전체 초기화")

            sub_choice = input("선택: ").strip()

            if sub_choice == '1':
                nums = input("추가할 번호 (쉼표로 구분): ").strip()
                numbers = [int(n.strip()) for n in nums.split(',') if n.strip().isdigit()]
                exclude_manager.add_exclude_numbers(numbers)

            elif sub_choice == '2':
                nums = input("제거할 번호 (쉼표로 구분): ").strip()
                numbers = [int(n.strip()) for n in nums.split(',') if n.strip().isdigit()]
                exclude_manager.remove_exclude_numbers(numbers)

            elif sub_choice == '3':
                exclude_manager.show_exclude_numbers()

            elif sub_choice == '4':
                confirm = input("정말 초기화하시겠습니까? (y/N): ").strip().lower()
                if confirm == 'y':
                    exclude_manager.clear_exclude_numbers()

        elif choice == '6':
            show_system_info()
            check_installation_status()

        elif choice == '0':
            print("\n 프로그램을 종료합니다.")
            break

        else:
            print("[X] 잘못된 선택입니다.")


def main():
    """메인 함수"""
    print(" 동행복권 로또 번호 추천 시스템 v3.0")

    if DNN_AVAILABLE:
        print("   [OK] DNN 기능: 활성화됨")
    else:
        print("   [!] DNN 기능: 비활성화 (TensorFlow 미설치)")

    if AI_PATTERN_AVAILABLE:
        print("   [OK] AI 패턴 학습: 활성화됨")
    else:
        print("   [!] AI 패턴 학습: 비활성화")

    print(f"\n 데이터 파일: {DATA_FILE_PATH}")

    # 데이터 파일 확인
    if not os.path.exists(DATA_FILE_PATH):
        print(f"\n[!] 데이터 파일이 없습니다: {DATA_FILE_PATH}")

        if ANALYZERS_AVAILABLE and LottoDataCollector:
            create = input("새로 다운로드하시겠습니까? (y/N): ").strip().lower()

            if create == 'y':
                collector = LottoDataCollector()
                data = collector.collect_winning_numbers(max_rounds=100)
                if data:
                    collector.save_to_csv(data, DATA_FILE_PATH)
        else:
            print("   데이터 수집 기능을 사용할 수 없습니다. (패키지 설치 필요)")

    # 메인 메뉴 실행
    main_menu()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[!] 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n[X] 오류 발생: {e}")
        import traceback
        traceback.print_exc()
