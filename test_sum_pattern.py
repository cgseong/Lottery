#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
합계 패턴 분석 기능 테스트 스크립트
"""

import sys
import os

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_sum_pattern_analyzer():
    """합계 패턴 분석기를 테스트합니다."""
    print(" 합계 패턴 분석기 테스트")
    print("=" * 50)
    
    try:
        # 1. LottoAnalyzer 객체 생성
        print("1. LottoAnalyzer 객체 생성 중...")
        from lotto_analyzer_fixed import LottoAnalyzer
        
        analyzer = LottoAnalyzer('로또당첨번호.csv')
        print(" LottoAnalyzer 객체 생성 완료")
        
        # 2. 합계 패턴 분석기 상태 확인
        print("\n2. 합계 패턴 분석기 상태 확인...")
        if analyzer.sum_pattern_analyzer:
            print(" 합계 패턴 분석기가 초기화되었습니다")
            
            # 3. 합계 패턴 분석 리포트 출력
            print("\n3. 합계 패턴 분석 리포트:")
            analyzer.sum_pattern_analyzer.print_sum_analysis_report()
            
            # 4. 합계 기반 추천 번호 생성 테스트
            print("\n4. 합계 기반 추천 번호 생성 테스트...")
            recommendations = analyzer.sum_pattern_analyzer.generate_sum_based_recommendations(
                exclude_numbers=None, 
                num_recommendations=3
            )
            
            if recommendations:
                print(f" {len(recommendations)}개의 추천 번호가 생성되었습니다!")
            else:
                print(" 추천 번호를 생성할 수 없습니다")
            
            # 5. 특정 합계 범위로 추천 생성 테스트
            print("\n5. 특정 합계 범위로 추천 생성 테스트...")
            specific_recommendations = analyzer.sum_pattern_analyzer.generate_sum_based_recommendations(
                exclude_numbers=None, 
                num_recommendations=2,
                target_sum_range='보통 (121-150)'
            )
            
            if specific_recommendations:
                print(f" {len(specific_recommendations)}개의 특정 범위 추천이 생성되었습니다!")
            else:
                print(" 특정 범위 추천을 생성할 수 없습니다")
                
        else:
            print(" 합계 패턴 분석기가 초기화되지 않았습니다")
        
        print("\n 테스트 완료!")
        return True
        
    except ImportError as e:
        print(f" 모듈 import 실패: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f" 테스트 중 오류 발생: {e}")
        print("\n 상세 오류 정보:")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_sum_pattern_analyzer()
    if success:
        print("\n 테스트가 성공적으로 완료되었습니다.")
    else:
        print("\n 테스트 중 오류가 발생했습니다.")
        sys.exit(1)
