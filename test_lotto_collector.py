#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
동행복권 당첨번호 수집 테스트 스크립트
"""

import sys
import os

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from lotto_analyzer_fixed import LottoDataCollector

def test_lotto_collector():
    """당첨번호 수집 기능을 테스트합니다."""
    print(" 동행복권 당첨번호 수집 테스트")
    print("=" * 50)
    
    # 수집기 초기화
    collector = LottoDataCollector()
    
    # 1. 최신 회차 확인
    print("\n1 최신 회차 확인 중...")
    latest_round = collector.get_latest_round()
    if latest_round:
        print(f" 최신 회차: {latest_round}회")
    else:
        print(" 최신 회차 정보를 가져올 수 없습니다.")
        return
    
    # 2. 최근 5회차 수집 테스트
    print(f"\n2 최근 5회차 수집 테스트 ({latest_round-4}회 ~ {latest_round}회)")
    test_data = collector.collect_winning_numbers(
        start_round=latest_round-4,
        end_round=latest_round
    )
    
    if test_data:
        print(f" {len(test_data)}개 회차 수집 성공!")
        for data in test_data:
            numbers = [data[f'번호{i}'] for i in range(1, 7)]
            print(f"   {data['회차']}회: {numbers} + 보너스({data['보너스번호']})")
        
        # 3. CSV 저장 테스트
        print(f"\n3 CSV 저장 테스트")
        if collector.save_to_csv(test_data, 'test_로또당첨번호.csv'):
            print(" CSV 저장 성공!")
        else:
            print(" CSV 저장 실패!")
    else:
        print(" 데이터 수집에 실패했습니다.")
    
    print("\n 테스트 완료!")

if __name__ == "__main__":
    test_lotto_collector() 