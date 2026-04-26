#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
상수 import 테스트 스크립트
"""

import sys
import os

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_constants_import():
    """상수 import 테스트"""
    print(" 상수 import 테스트")
    print("=" * 40)
    
    try:
        # 1. utils.constants에서 직접 import
        print("1. utils.constants에서 직접 import 테스트...")
        from utils.constants import LOTTO_NUMBER_COLUMNS, BONUS_COLUMN, ROUND_COLUMN
        print(f"    LOTTO_NUMBER_COLUMNS: {LOTTO_NUMBER_COLUMNS}")
        print(f"    BONUS_COLUMN: {BONUS_COLUMN}")
        print(f"    ROUND_COLUMN: {ROUND_COLUMN}")
        
        # 2. utils.constants에서 전체 import
        print("\n2. utils.constants에서 전체 import 테스트...")
        import utils.constants as constants
        print(f"    LOTTO_NUMBER_COLUMNS: {constants.LOTTO_NUMBER_COLUMNS}")
        print(f"    MAX_LOTTO_NUMBER: {constants.MAX_LOTTO_NUMBER}")
        print(f"    NUM_LOTTO_NUMBERS_TO_PICK: {constants.NUM_LOTTO_NUMBERS_TO_PICK}")
        
        # 3. lotto_analyzer_fixed에서 import
        print("\n3. lotto_analyzer_fixed에서 import 테스트...")
        from lotto_analyzer_fixed import LOTTO_NUMBER_COLUMNS, BONUS_COLUMN, ROUND_COLUMN
        print(f"    LOTTO_NUMBER_COLUMNS: {LOTTO_NUMBER_COLUMNS}")
        print(f"    BONUS_COLUMN: {BONUS_COLUMN}")
        print(f"    ROUND_COLUMN: {ROUND_COLUMN}")
        
        # 4. analyzers.lotto_pattern_grouping에서 import
        print("\n4. analyzers.lotto_pattern_grouping에서 import 테스트...")
        from analyzers.lotto_pattern_grouping import LottoPatternGrouping
        print("    LottoPatternGrouping 클래스 import 성공")
        
        print("\n 모든 상수 import 테스트가 성공했습니다!")
        return True
        
    except ImportError as e:
        print(f" Import 오류: {e}")
        return False
    except Exception as e:
        print(f" 예상치 못한 오류: {e}")
        return False

if __name__ == "__main__":
    success = test_constants_import()
    if success:
        print("\n 테스트가 성공적으로 완료되었습니다.")
    else:
        print("\n 테스트 중 오류가 발생했습니다.")
        sys.exit(1) 