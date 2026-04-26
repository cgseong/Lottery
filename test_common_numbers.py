#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
공통 번호 분석 기능 테스트 스크립트
"""

import sys
import os

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from lotto_analyzer_fixed import LottoPatternGrouping, LottoAnalyzer
    print(" 모듈 import 성공")
except ImportError as e:
    print(f" 모듈 import 실패: {e}")
    sys.exit(1)

def test_common_numbers_analysis():
    """공통 번호 분석 기능을 테스트합니다."""
    print("\n 공통 번호 분석 기능 테스트")
    print("=" * 50)
    
    # 테스트용 조합 데이터 생성
    test_combinations = [
        {'numbers': [1, 7, 15, 23, 35, 42], 'probability': 0.8, 'consecutive_count': 0},
        {'numbers': [1, 8, 16, 24, 36, 43], 'probability': 0.75, 'consecutive_count': 0},
        {'numbers': [1, 9, 17, 25, 37, 44], 'probability': 0.7, 'consecutive_count': 0},
        {'numbers': [2, 10, 18, 26, 38, 45], 'probability': 0.65, 'consecutive_count': 0},
        {'numbers': [1, 11, 19, 27, 39, 41], 'probability': 0.6, 'consecutive_count': 0},
        {'numbers': [3, 12, 20, 28, 40, 42], 'probability': 0.55, 'consecutive_count': 0},
        {'numbers': [1, 13, 21, 29, 35, 43], 'probability': 0.5, 'consecutive_count': 0},
        {'numbers': [4, 14, 22, 30, 36, 44], 'probability': 0.45, 'consecutive_count': 0},
        {'numbers': [1, 15, 23, 31, 37, 45], 'probability': 0.4, 'consecutive_count': 0},
        {'numbers': [5, 16, 24, 32, 38, 41], 'probability': 0.35, 'consecutive_count': 0}
    ]
    
    print(f" 테스트 조합 수: {len(test_combinations)}개")
    
    # LottoPatternGrouping 객체 생성 (테스트용)
    try:
        # 간단한 테스트 데이터로 초기화
        test_data = [{'회차': i, '번호1': 1, '번호2': 2, '번호3': 3, '번호4': 4, '번호5': 5, '번호6': 6} 
                    for i in range(1, 11)]
        
        pattern_grouping = LottoPatternGrouping(test_data)
        
        # 공통 번호 분석 실행
        common_analysis = pattern_grouping.find_common_numbers(test_combinations)
        
        print(f"\n 공통 번호 분석 결과:")
        print(f"    총 조합 수: {common_analysis['total_combinations']}개")
        
        if common_analysis['common_numbers']:
            print(f"    모든 조합에 나타나는 번호: {common_analysis['common_numbers']}")
        else:
            print("    모든 조합에 나타나는 번호: 없음")
        
        if common_analysis['frequent_numbers']:
            print(f"\n 자주 나타나는 번호들 (50% 이상):")
            for num, freq in common_analysis['frequent_numbers']:
                percentage = freq * 100
                count = int(freq * common_analysis['total_combinations'])
                print(f"   {num}번: {percentage:.1f}% ({count}개 조합)")
        else:
            print("\n 자주 나타나는 번호들: 없음")
        
        # 번호별 출현 횟수 상세 정보
        print(f"\n 번호별 출현 횟수:")
        for num in sorted(common_analysis['number_counts'].keys()):
            count = common_analysis['number_counts'][num]
            percentage = (count / common_analysis['total_combinations']) * 100
            print(f"   {num}번: {count}회 ({percentage:.1f}%)")
        
        print("\n 공통 번호 분석 기능 테스트 완료!")
        
    except Exception as e:
        print(f" 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()

def test_with_real_data():
    """실제 데이터로 공통 번호 분석을 테스트합니다."""
    print("\n 실제 데이터로 공통 번호 분석 테스트")
    print("=" * 50)
    
    try:
        # LottoAnalyzer 객체 생성
        analyzer = LottoAnalyzer('로또당첨번호.csv')
        
        if not analyzer.pattern_grouping:
            print(" AI 패턴 학습 기능이 초기화되지 않았습니다.")
            return
        
        # AI 패턴 학습 초기화
        print(" AI 패턴 학습 초기화 중...")
        
        # 회차 그룹핑
        groups = analyzer.pattern_grouping.create_round_groups(5)
        if not groups:
            print(" 회차 그룹핑에 실패했습니다.")
            return
        
        # AI 특성 생성
        features = analyzer.pattern_grouping.create_pattern_features()
        if not features:
            print(" AI 특성 생성에 실패했습니다.")
            return
        
        # 클러스터링
        clusters = analyzer.pattern_grouping.perform_clustering(5)
        if not clusters:
            print(" 클러스터링에 실패했습니다.")
            return
        
        # AI 모델 훈련
        models = analyzer.pattern_grouping.train_ai_models()
        if not models:
            print(" AI 모델 훈련에 실패했습니다.")
            return
        
        print(" AI 패턴 학습 초기화 완료!")
        
        # 높은 확률 조합 예측
        print("\n 높은 확률 조합 예측 중...")
        combinations = analyzer.pattern_grouping.predict_high_probability_combinations(
            exclude_numbers=None, num_combinations=10
        )
        
        if combinations:
            print(f"\n AI 예측 결과 ({len(combinations)}개):")
            print("=" * 60)
            for i, comb in enumerate(combinations, 1):
                print(f"{i}번째: {comb['numbers']}")
                print(f"   확률: {comb['probability']:.3f}")
                print(f"   연속번호: {comb['consecutive_count']}개")
                if comb['cluster_info']:
                    print(f"   클러스터: {comb['cluster_info']['best_cluster']+1} (유사도: {comb['cluster_info']['similarity']:.3f})")
                print()
            
            # 공통 번호 분석
            common_analysis = analyzer.pattern_grouping.find_common_numbers(combinations)
            
            if common_analysis['common_numbers']:
                print(f"\n 공통 번호 분석:")
                print(f"    모든 조합에 나타나는 번호: {common_analysis['common_numbers']}")
                print(f"    총 조합 수: {common_analysis['total_combinations']}개")
            
            if common_analysis['frequent_numbers']:
                print(f"\n 자주 나타나는 번호들 (50% 이상):")
                for num, freq in common_analysis['frequent_numbers'][:5]:  # 상위 5개만 표시
                    percentage = freq * 100
                    print(f"   {num}번: {percentage:.1f}% ({int(freq * common_analysis['total_combinations'])}개 조합)")
            
            print("=" * 60)
            print("\n 실제 데이터로 공통 번호 분석 테스트 완료!")
        else:
            print(" 높은 확률 조합을 생성할 수 없습니다.")
        
    except Exception as e:
        print(f" 실제 데이터 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print(" 공통 번호 분석 기능 테스트 스크립트")
    print("=" * 50)
    
    # 기본 테스트
    test_common_numbers_analysis()
    
    # 실제 데이터 테스트 (선택적)
    try:
        test_with_real_data()
    except Exception as e:
        print(f" 실제 데이터 테스트를 건너뜁니다: {e}")
    
    print("\n 모든 테스트가 완료되었습니다!") 