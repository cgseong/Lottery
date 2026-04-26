#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 패턴 학습 모델 자동 훈련 및 저장 스크립트
"""

import sys
import os

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from lotto_analyzer_fixed import LottoAnalyzer, AI_PATTERN_AVAILABLE
    print(" lotto_analyzer_fixed 모듈을 성공적으로 가져왔습니다.")
except ImportError as e:
    print(f" lotto_analyzer_fixed 모듈을 가져올 수 없습니다: {e}")
    sys.exit(1)

def create_ai_models():
    """AI 패턴 학습 모델을 훈련하고 저장합니다."""
    
    print(" AI 패턴 학습 모델 자동 훈련 및 저장")
    print("=" * 50)
    
    # AI 패턴 학습 사용 가능 여부 확인
    if not AI_PATTERN_AVAILABLE:
        print(" AI 패턴 학습 기능을 사용할 수 없습니다.")
        print("   다음 명령어로 필요한 라이브러리를 설치하세요:")
        print("   pip install scikit-learn pandas numpy joblib")
        return False
    
    try:
        # LottoAnalyzer 객체 생성
        print("[INFO] 로또 데이터 로드 중...")
        analyzer = LottoAnalyzer('로또당첨번호.csv')
        
        if not analyzer.pattern_grouping:
            print(" AI 패턴 학습 기능이 초기화되지 않았습니다.")
            return False
        
        print(" 로또 데이터 로드 완료")
        
        # 1. 회차 그룹핑 분석
        print("\n[INFO] 1단계: 회차 그룹핑 분석")
        print("-" * 30)
        group_size = 5  # 기본값
        groups = analyzer.pattern_grouping.create_round_groups(group_size)
        if not groups:
            print(" 회차 그룹핑에 실패했습니다.")
            return False
        print(f" {len(groups)}개의 그룹이 생성되었습니다.")
        
        # 2. AI 특성 생성
        print("\n 2단계: AI 특성 생성")
        print("-" * 30)
        features = analyzer.pattern_grouping.create_pattern_features()
        if not features:
            print(" AI 특성 생성에 실패했습니다.")
            return False
        print(f" {len(features['features'])}개의 특성 벡터가 생성되었습니다.")
        
        # 3. 패턴 클러스터링
        print("\n 3단계: 패턴 클러스터링")
        print("-" * 30)
        clusters = analyzer.pattern_grouping.perform_clustering()
        if not clusters:
            print(" 패턴 클러스터링에 실패했습니다.")
            return False
        print(f" 클러스터링이 완료되었습니다.")
        
        # 4. AI 모델 훈련
        print("\n 4단계: AI 모델 훈련")
        print("-" * 30)
        models = analyzer.pattern_grouping.train_ai_models()
        if not models:
            print(" AI 모델 훈련에 실패했습니다.")
            return False
        print(f" {len(models)}개의 AI 모델이 훈련되었습니다.")
        
        # 5. 모델 저장
        print("\n 5단계: AI 모델 저장")
        print("-" * 30)
        success = analyzer.pattern_grouping.save_models()
        if not success:
            print(" AI 모델 저장에 실패했습니다.")
            return False
        print(" AI 모델이 'ai_pattern_models.pkl'에 저장되었습니다.")
        
        # 6. 분석 리포트 출력
        print("\n[INFO] 6단계: AI 분석 리포트")
        print("-" * 30)
        analyzer.pattern_grouping.print_analysis_report()
        
        print("\n AI 패턴 학습 모델 훈련 및 저장이 완료되었습니다!")
        print("이제 메인 프로그램에서 AI 패턴 학습 기능을 사용할 수 있습니다.")
        
        return True
        
    except Exception as e:
        print(f" AI 모델 생성 중 오류 발생: {e}")
        return False

if __name__ == "__main__":
    success = create_ai_models()
    if success:
        print("\n 스크립트가 성공적으로 완료되었습니다.")
    else:
        print("\n 스크립트 실행 중 오류가 발생했습니다.")
        sys.exit(1) 