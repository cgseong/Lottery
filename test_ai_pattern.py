#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 패턴 학습 기능 테스트 스크립트
"""

import sys
import os
import csv
import random
from datetime import datetime

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_test_data():
    """테스트용 로또 데이터를 생성합니다."""
    print(" 테스트용 로또 데이터 생성 중...")
    
    test_data = []
    for round_num in range(1, 101):  # 100회차 테스트 데이터
        # 랜덤한 6개 번호 생성 (중복 없이)
        numbers = sorted(random.sample(range(1, 46), 6))
        bonus = random.randint(1, 45)
        
        test_data.append({
            '회차': round_num,
            '번호1': numbers[0],
            '번호2': numbers[1],
            '번호3': numbers[2],
            '번호4': numbers[3],
            '번호5': numbers[4],
            '번호6': numbers[5],
            '보너스번호': bonus
        })
    
    # CSV 파일로 저장
    with open('test_lotto_data.csv', 'w', newline='', encoding='utf-8') as file:
        fieldnames = ['회차', '번호1', '번호2', '번호3', '번호4', '번호5', '번호6', '보너스번호']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(test_data)
    
    print(f" {len(test_data)}회차의 테스트 데이터가 'test_lotto_data.csv'에 저장되었습니다.")
    return test_data

def test_ai_pattern_learning():
    """AI 패턴 학습 기능을 테스트합니다."""
    print("\n AI 패턴 학습 기능 테스트")
    print("=" * 60)
    
    try:
        # AI 패턴 학습 기능 import 확인
        from lotto_analyzer_fixed import LottoPatternGrouping, AI_PATTERN_AVAILABLE
        
        if not AI_PATTERN_AVAILABLE:
            print(" AI 패턴 학습 기능을 사용할 수 없습니다.")
            print("   다음 명령어로 필요한 라이브러리를 설치하세요:")
            print("   pip install scikit-learn pandas numpy joblib")
            return False
        
        # 테스트 데이터 생성
        test_data = create_test_data()
        
        # AI 패턴 학습 객체 생성
        print("\n AI 패턴 학습 객체 초기화...")
        pattern_grouping = LottoPatternGrouping(test_data)
        
        # 1. 회차 그룹핑 테스트
        print("\n 1. 회차 그룹핑 테스트")
        print("-" * 40)
        groups = pattern_grouping.create_round_groups(group_size=5)
        print(f" {len(groups)}개의 그룹이 생성되었습니다.")
        
        # 2. AI 특성 생성 테스트
        print("\n 2. AI 특성 생성 테스트")
        print("-" * 40)
        features = pattern_grouping.create_pattern_features()
        if features:
            print(f" {len(features['features'])}개의 특성 벡터가 생성되었습니다.")
            print(f"   특성 차원: {len(features['features'][0])}개")
        else:
            print(" 특성 생성에 실패했습니다.")
            return False
        
        # 3. 패턴 클러스터링 테스트
        print("\n 3. 패턴 클러스터링 테스트")
        print("-" * 40)
        clusters = pattern_grouping.perform_clustering(n_clusters=3)
        if clusters:
            print(f" {len(clusters['analysis'])}개의 클러스터가 생성되었습니다.")
        else:
            print(" 클러스터링에 실패했습니다.")
            return False
        
        # 4. AI 모델 훈련 테스트
        print("\n 4. AI 모델 훈련 테스트")
        print("-" * 40)
        models = pattern_grouping.train_ai_models()
        if models:
            print(f" {len(models)}개의 AI 모델이 훈련되었습니다.")
            for name, model_info in models.items():
                print(f"   {name}: 정확도 {model_info['accuracy']:.3f}")
        else:
            print(" AI 모델 훈련에 실패했습니다.")
            return False
        
        # 5. 높은 확률 조합 예측 테스트
        print("\n 5. 높은 확률 조합 예측 테스트")
        print("-" * 40)
        combinations = pattern_grouping.predict_high_probability_combinations(
            exclude_numbers=[1, 2, 3], num_combinations=5
        )
        if combinations:
            print(f" {len(combinations)}개의 높은 확률 조합이 생성되었습니다.")
            for i, comb in enumerate(combinations, 1):
                print(f"   {i}번째: {comb['numbers']} (확률: {comb['probability']:.3f})")
        else:
            print(" 높은 확률 조합 생성에 실패했습니다.")
            return False
        
        # 6. 모델 저장/로드 테스트
        print("\n 6. 모델 저장/로드 테스트")
        print("-" * 40)
        save_success = pattern_grouping.save_models('test_ai_models.pkl')
        if save_success:
            print(" 모델 저장 성공")
            
            # 새로운 객체로 모델 로드 테스트
            new_pattern_grouping = LottoPatternGrouping(test_data)
            load_success = new_pattern_grouping.load_models('test_ai_models.pkl')
            if load_success:
                print(" 모델 로드 성공")
            else:
                print(" 모델 로드 실패")
                return False
        else:
            print(" 모델 저장 실패")
            return False
        
        # 7. AI 분석 리포트 테스트
        print("\n 7. AI 분석 리포트 테스트")
        print("-" * 40)
        pattern_grouping.print_analysis_report()
        
        # 테스트 파일 정리
        try:
            os.remove('test_lotto_data.csv')
            os.remove('test_ai_models.pkl')
            print("\n 테스트 파일이 정리되었습니다.")
        except:
            pass
        
        print("\n 모든 AI 패턴 학습 기능 테스트가 성공적으로 완료되었습니다!")
        return True
        
    except ImportError as e:
        print(f" 필요한 모듈을 import할 수 없습니다: {e}")
        return False
    except Exception as e:
        print(f" 테스트 중 오류 발생: {e}")
        return False

def main():
    """메인 함수"""
    print(" AI 패턴 학습 기능 테스트 스크립트")
    print("=" * 60)
    
    # AI 패턴 학습 기능 테스트
    success = test_ai_pattern_learning()
    
    if success:
        print("\n 모든 테스트가 성공적으로 완료되었습니다!")
        print("   이제 메인 프로그램에서 AI 패턴 학습 기능을 사용할 수 있습니다.")
    else:
        print("\n 일부 테스트가 실패했습니다.")
        print("   패키지 설치 상태를 확인하고 다시 시도해주세요.")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main() 