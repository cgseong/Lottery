#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
전체 파일의 인코딩 문제를 수정하는 스크립트
"""

import re

def fix_all_encoding_issues(filename):
    """파일의 모든 인코딩 문제를 수정합니다."""

    # 파일 읽기
    with open(filename, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    # 손상된 문자를 포함한 f-string 찾기 및 수정
    # 패턴: f"..." 내부에 가 있거나 마지막 따옴표가 없는 경우

    # 특정 줄들을 개별적으로 수정
    replacements = {
        # 라인 3318
        r'print\(f"[^"]*\{len\(features\)\}[^"]*"\)':
            'print(f"총 {len(features)}개의 특성 벡터가 생성되었습니다.")',

        # 라인 3319
        r'print\(f"\s+[^"]*차원[^"]*\{len\(features\[0\]\)\}[^")]*\)':
            'print(f"   특성 차원: {len(features[0])}개")',

        # 라인 3636
        r'print\(f"\s+[^"]*속번호[^"]*\{combo\[\'consecutive_count\'\]\}[^")]*\)':
            'print(f"   연속번호: {combo[\'consecutive_count\']}개")',
    }

    original_content = content
    fixed_count = 0

    for pattern, replacement in replacements.items():
        new_content = re.sub(pattern, replacement, content)
        if new_content != content:
            fixed_count += 1
            content = new_content

    # 추가: 잘못된 print 문 전체 찾기
    # f"..."에서 닫는 따옴표가 없는 경우
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'print(f"' in line and line.count('"') % 2 != 0:
            # 따옴표가 홀수 개 - 닫히지 않은 문자열
            if '' in line or '?' in line:
                # 다음 줄과 합쳐서 확인
                print(f"라인 {i+1}에 문제 발견: {line[:60]}...")

    # 파일 쓰기
    if content != original_content:
        with open(filename, 'w', encoding='utf-8', newline='\n') as f:
            f.write(content)
        print(f"수정 완료: {fixed_count}개 패턴")
        return True
    else:
        print("수정할 내용이 없습니다.")
        return False

if __name__ == "__main__":
    fix_all_encoding_issues("lotto_analyzer_fixed.py")
