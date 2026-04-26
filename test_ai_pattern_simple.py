#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 패턴 분석 테스트 스크립트
모델 파일이 없어도 작동하는지 확인
"""

import sys
import os

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from lotto_analyzer_fixed import LottoPatternGrouping, LottoDataCollector
    print(" 모듈 import 성공")
    
    # CSV 파일에서 데이터 로드
    print("\n 로또 데이터 로드 중...")
    collector = LottoDataCollector()
    data = collector.load_data()
    
    if not data:
        print(" 데이터를 로드할 수 없습니다.")
        sys.exit(1)
    
    print(f" {len(data)}개의 로또 데이터를 로드했습니다.")
    
    # AI 패턴 그룹핑 테스트
    print("\n AI 패턴 그룹핑 테스트 중...")
    pattern_grouping = LottoPatternGrouping(data)
    
    # 추천 번호 생성 (모델 파일이 없어도 작동해야 함)
    print("\n AI 기반 추천 번호 생성 중...")
    recommendations = pattern_grouping.predict_high_probability_combinations(
        exclude_numbers=None, 
        num_combinations=3
    )
    
    if recommendations:
        print(f"\n {len(recommendations)}개의 추천 번호가 생성되었습니다!")
        for i, rec in enumerate(recommendations, 1):
            print(f"\n{i}번째 추천:")
            print(f"   번호: {rec['numbers']}")
            print(f"   방법: {rec.get('method', '알 수 없음')}")
            print(f"   점수: {rec.get('score', 0)}")
    else:
        print(" 추천 번호를 생성할 수 없습니다.")
    
except ImportError as e:
    print(f" 모듈 import 실패: {e}")
    sys.exit(1)
except Exception as e:
    print(f" 오류 발생: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n 테스트 완료!") 