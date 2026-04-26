#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSV 파일에 보너스번호 컬럼을 추가하는 스크립트
"""

import csv
import os
import shutil
from datetime import datetime

def fix_csv_columns():
    """CSV 파일에 보너스번호 컬럼을 추가합니다."""
    
    input_file = '로또당첨번호.csv'
    backup_file = f'로또당첨번호.csv.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    
    print(" CSV 파일 컬럼 수정 중...")
    print(f"입력 파일: {input_file}")
    
    # 1. 백업 파일 생성
    if os.path.exists(input_file):
        shutil.copy2(input_file, backup_file)
        print(f" 백업 파일 생성: {backup_file}")
    else:
        print(f" 입력 파일을 찾을 수 없습니다: {input_file}")
        return False
    
    # 2. CSV 파일 읽기 및 수정
    fixed_data = []
    
    try:
        with open(input_file, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            
            # 헤더 처리
            header = next(reader)
            if '보너스번호' not in header:
                header.append('보너스번호')
                fixed_data.append(header)
                print(" 헤더에 '보너스번호' 컬럼 추가")
            else:
                print(" '보너스번호' 컬럼이 이미 존재합니다")
                return True
            
            # 데이터 행 처리
            for row_num, row in enumerate(reader, 1):
                if len(row) == 6:  # 보너스번호가 없는 경우
                    row.append('0')  # 기본값 0으로 설정
                elif len(row) == 7:  # 보너스번호가 이미 있는 경우
                    pass  # 그대로 유지
                else:
                    print(f"[WARN] {row_num}번째 행의 컬럼 수가 예상과 다릅니다: {len(row)}개")
                    continue
                
                fixed_data.append(row)
            
            print(f" 총 {len(fixed_data)-1}개의 데이터 행을 처리했습니다")
    
    except Exception as e:
        print(f" CSV 파일 읽기 실패: {e}")
        return False
    
    # 3. 수정된 데이터를 새 파일에 저장
    try:
        with open(input_file, 'w', encoding='utf-8', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(fixed_data)
        
        print(" 수정된 CSV 파일 저장 완료")
        print(f"[INFO] 컬럼 수: {len(fixed_data[0])}개")
        print(f"[INFO] 데이터 행 수: {len(fixed_data)-1}개")
        
        return True
        
    except Exception as e:
        print(f" CSV 파일 저장 실패: {e}")
        return False

def check_csv_structure():
    """CSV 파일의 구조를 확인합니다."""
    
    input_file = '로또당첨번호.csv'
    
    if not os.path.exists(input_file):
        print(f" 파일이 존재하지 않습니다: {input_file}")
        return False
    
    try:
        with open(input_file, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            
            # 헤더 확인
            header = next(reader)
            print(f" 헤더: {header}")
            print(f"[INFO] 컬럼 수: {len(header)}개")
            
            # 첫 몇 행 확인
            print("\n[INFO] 첫 5개 데이터 행:")
            for i, row in enumerate(reader, 1):
                if i <= 5:
                    print(f"  {i}: {row}")
                else:
                    break
            
            return True
            
    except Exception as e:
        print(f" CSV 파일 확인 실패: {e}")
        return False

if __name__ == "__main__":
    print(" CSV 파일 컬럼 수정 도구")
    print("=" * 50)
    
    # 현재 상태 확인
    print("\n1. 현재 CSV 파일 구조 확인:")
    check_csv_structure()
    
    # 컬럼 수정
    print("\n2. CSV 파일 컬럼 수정:")
    if fix_csv_columns():
        print("\n3. 수정 후 CSV 파일 구조 확인:")
        check_csv_structure()
        print("\n CSV 파일 수정이 완료되었습니다!")
    else:
        print("\n CSV 파일 수정에 실패했습니다.")
