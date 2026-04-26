#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 모델 자동 생성 테스트 스크립트
"""

import sys
import os

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_auto_model_creation():
    """AI 모델 자동 생성을 테스트합니다."""
    print(" AI 모델 자동 생성 테스트")
    print("=" * 50)
    
    try:
        # 1. LottoAnalyzer 객체 생성 (자동으로 모델 생성 시도)
        print("1. LottoAnalyzer 객체 생성 중...")
        from lotto_analyzer_fixed import LottoAnalyzer
        
        analyzer = LottoAnalyzer('로또당첨번호.csv')
        print(" LottoAnalyzer 객체 생성 완료")
        
        # 2. AI 패턴 그룹핑 상태 확인
        print("\n2. AI 패턴 그룹핑 상태 확인...")
        if analyzer.pattern_grouping:
            print(" AI 패턴 그룹핑이 초기화되었습니다")
            
            # 3. AI 모델 상태 확인
            print("\n3. AI 모델 상태 확인...")
            if analyzer.pattern_grouping.ai_models:
                print(f" {len(analyzer.pattern_grouping.ai_models)}개의 AI 모델이 로드되었습니다")
                
                # 4. 추천 번호 생성 테스트
                print("\n4. AI 기반 추천 번호 생성 테스트...")
                recommendations = analyzer.pattern_grouping.predict_high_probability_combinations(
                    exclude_numbers=None, 
                    num_combinations=2
                )
                
                if recommendations:
                    print(f" {len(recommendations)}개의 추천 번호가 생성되었습니다!")
                    for i, rec in enumerate(recommendations, 1):
                        print(f"\n{i}번째 추천:")
                        print(f"   번호: {rec['numbers']}")
                        print(f"   방법: {rec.get('method', '알 수 없음')}")
                        print(f"   점수: {rec.get('score', 0)}")
                else:
                    print(" 추천 번호를 생성할 수 없습니다")
            else:
                print(" AI 모델이 로드되지 않았습니다")
        else:
            print(" AI 패턴 그룹핑이 초기화되지 않았습니다")
        
        # 5. 통합 추천 테스트
        print("\n5. 통합 추천 테스트...")
        try:
            recommendations = analyzer.generate_recommendations_ensemble(
                exclude_numbers=None, 
                num_recommendations=2
            )
            if recommendations:
                print(f" {len(recommendations)}개의 통합 추천이 생성되었습니다!")
            else:
                print(" 통합 추천을 생성할 수 없습니다")
        except Exception as e:
            print(f" 통합 추천 생성 중 오류: {e}")
        
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
    success = test_auto_model_creation()
    if success:
        print("\n 테스트가 성공적으로 완료되었습니다.")
    else:
        print("\n 테스트 중 오류가 발생했습니다.")
        sys.exit(1)
