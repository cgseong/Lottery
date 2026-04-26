#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
인코딩 문제 수정 스크립트
"""

import re
import sys

def fix_encoding_issues(filename):
    """파일의 인코딩 문제를 수정합니다."""

    # 파일 읽기
    try:
        with open(filename, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"파일 읽기 오류: {e}")
        return False

    # 문제가 있는 줄 수정
    fixed_count = 0

    for i, line in enumerate(lines):
        original = line

        # 3318번 줄 수정
        if i == 3317:  # 0-based index
            line = '        print(f"총 {len(features)}개의 특성 벡터가 생성되었습니다.")\n'
            if line != original:
                fixed_count += 1
                print(f"라인 {i+1} 수정됨")

        # 3319번 줄 수정
        elif i == 3318:  # 0-based index
            line = '        print(f"   특성 차원: {len(features[0])}개")\n'
            if line != original:
                fixed_count += 1
                print(f"라인 {i+1} 수정됨")

        lines[i] = line

    # 파일 쓰기
    try:
        with open(filename, 'w', encoding='utf-8', newline='\n') as f:
            f.writelines(lines)
        print(f"\n수정 완료: {fixed_count}개 라인")
        return True
    except Exception as e:
        print(f"파일 쓰기 오류: {e}")
        return False

if __name__ == "__main__":
    filename = "lotto_analyzer_fixed.py"
    success = fix_encoding_issues(filename)
    sys.exit(0 if success else 1)
