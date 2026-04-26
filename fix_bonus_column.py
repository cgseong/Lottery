#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def fix_bonus_column():
    """BONUS_COLUMN을 '보너스'에서 '보너스번호'로 수정"""
    try:
        # 파일 읽기
        with open('lotto_analyzer_fixed.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 수정
        content = content.replace("BONUS_COLUMN = '보너스'", "BONUS_COLUMN = '보너스번호'")
        
        # 파일 쓰기
        with open('lotto_analyzer_fixed.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(" BONUS_COLUMN이 성공적으로 수정되었습니다!")
        return True
    except Exception as e:
        print(f" 오류 발생: {e}")
        return False

if __name__ == "__main__":
    fix_bonus_column() 