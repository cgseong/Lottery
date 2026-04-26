#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
로또 분석 시스템 유틸리티 함수들
"""

import os
import sys
from typing import List, Dict, Optional, Set, Tuple, Any
from datetime import datetime

# 상수 import
from .constants import *


def check_installation_status() -> Tuple[bool, bool, bool, bool]:
    """필요한 패키지들의 설치 상태를 확인합니다."""
    print("[CHECK] 패키지 설치 상태 확인 중...")
    print("=" * 50)
    
    # 기본 패키지들
    basic_packages = {
        'csv': 'CSV 파일 처리',
        'random': '랜덤 번호 생성',
        'collections': '데이터 구조',
        'datetime': '날짜/시간 처리'
    }
    
    print(" 기본 패키지:")
    basic_available = True
    for package, description in basic_packages.items():
        try:
            __import__(package)
            print(f"    {package}: {description}")
        except ImportError:
            print(f"    {package}: {description} (설치 필요)")
            basic_available = False
    
    # DNN 관련 패키지들
    dnn_packages = {
        'tensorflow': '딥러닝 프레임워크',
        'numpy': '수치 계산 라이브러리',
        'sklearn': '머신러닝 라이브러리'
    }
    
    print("\n DNN 패키지:")
    dnn_available = True
    for package, description in dnn_packages.items():
        try:
            __import__(package)
            print(f"    {package}: {description}")
        except ImportError:
            print(f"    {package}: {description} (설치 필요)")
            dnn_available = False
    
    # AI 패턴 학습 관련 패키지들
    ai_pattern_packages = {
        'sklearn': '머신러닝 라이브러리',
        'pandas': '데이터 분석 라이브러리',
        'numpy': '수치 계산 라이브러리',
        'joblib': '병렬 처리 라이브러리'
    }
    
    print("\n AI 패턴 학습 패키지:")
    ai_pattern_available = True
    for package, description in ai_pattern_packages.items():
        try:
            __import__(package)
            print(f"    {package}: {description}")
        except ImportError:
            print(f"    {package}: {description} (설치 필요)")
            ai_pattern_available = False
    
    # 선 연결 패턴 분석 관련 패키지들
    line_pattern_packages = {
        'matplotlib': '그래프 및 시각화 라이브러리'
    }
    
    print("\n 선 연결 패턴 분석 패키지:")
    line_pattern_available = True
    for package, description in line_pattern_packages.items():
        try:
            __import__(package)
            print(f"    {package}: {description}")
        except ImportError:
            print(f"    {package}: {description} (설치 필요)")
            line_pattern_available = False
    
    print("\n 설치 가이드:")
    if not basic_available or not dnn_available or not ai_pattern_available or not line_pattern_available:
        print("   모든 패키지 설치:")
        print("   pip install -r requirements.txt")
        if not dnn_available:
            print("   DNN 패키지: pip install tensorflow numpy scikit-learn")
        if not ai_pattern_available:
            print("   AI 패턴 학습 패키지: pip install scikit-learn pandas numpy joblib")
        if not line_pattern_available:
            print("   선 연결 패턴 분석 패키지: pip install matplotlib")
    else:
        print("    모든 패키지가 설치되어 있습니다!")
    
    print("=" * 50)
    return basic_available, dnn_available, ai_pattern_available, line_pattern_available


def show_system_info():
    """시스템 정보를 표시합니다."""
    print("\n 시스템 정보")
    print("=" * 50)
    
    # Python 버전
    print(f" Python 버전: {sys.version}")
    
    # 운영체제 정보
    import platform
    print(f" 운영체제: {platform.system()} {platform.release()}")
    
    # 현재 작업 디렉토리
    print(f" 작업 디렉토리: {os.getcwd()}")
    
    # 파일 존재 여부 확인
    files_to_check = [
        DEFAULT_CSV_FILE,
        DEFAULT_EXCLUDE_FILE,
        DEFAULT_TICKETS_FILE,
        DEFAULT_DNN_MODEL_PATH,
        DEFAULT_AI_MODELS_PATH
    ]
    
    print("\n 파일 상태:")
    for file_path in files_to_check:
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            print(f"    {file_path} ({file_size:,} bytes)")
        else:
            print(f"    {file_path} (없음)")
    
    print("=" * 50)


def validate_numbers(numbers: List[int]) -> bool:
    """번호 조합의 유효성을 검사합니다."""
    if not numbers or len(numbers) != NUM_LOTTO_NUMBERS_TO_PICK:
        return False
    
    # 중복 검사
    if len(set(numbers)) != NUM_LOTTO_NUMBERS_TO_PICK:
        return False
    
    # 범위 검사
    for num in numbers:
        if not (1 <= num <= MAX_LOTTO_NUMBER):
            return False
    
    return True


def format_numbers(numbers: List[int]) -> str:
    """번호 리스트를 포맷팅합니다."""
    if not numbers:
        return "[]"
    return f"[{', '.join(map(str, sorted(numbers)))}]"


def calculate_summary_stats(numbers_list: List[List[int]]) -> Dict[str, Any]:
    """번호 조합들의 통계를 계산합니다."""
    if not numbers_list:
        return {}
    
    all_numbers = []
    sums = []
    
    for numbers in numbers_list:
        all_numbers.extend(numbers)
        sums.append(sum(numbers))
    
    # 빈도 분석
    from collections import Counter
    frequency = Counter(all_numbers)
    
    return {
        'total_combinations': len(numbers_list),
        'most_common_numbers': frequency.most_common(5),
        'least_common_numbers': frequency.most_common()[:-6:-1],
        'avg_sum': sum(sums) / len(sums),
        'min_sum': min(sums),
        'max_sum': max(sums),
        'sum_range': (min(sums), max(sums))
    }


def print_recommendations(recommendations: List[Dict], title: str = "추천 번호"):
    """추천 번호들을 출력합니다."""
    if not recommendations:
        print(f" {title}이 없습니다.")
        return
    
    print(f"\n {title} ({len(recommendations)}개):")
    print("=" * 60)
    
    for i, rec in enumerate(recommendations, 1):
        numbers = rec.get('numbers', [])
        score = rec.get('score', 0)
        method = rec.get('method', '알 수 없음')
        consecutive_count = rec.get('consecutive_count', 0)
        
        print(f"{i}. {format_numbers(numbers)}")
        print(f"   점수: {score:.3f}")
        print(f"   방법: {method}")
        print(f"   연속번호: {consecutive_count}개")
        
        # 추가 정보가 있으면 출력
        if 'sum' in rec:
            print(f"   합계: {rec['sum']}")
        if 'probability' in rec:
            print(f"   확률: {rec['probability']:.3f}")
        if 'cluster_info' in rec and rec['cluster_info']:
            cluster_info = rec['cluster_info']
            print(f"   클러스터: {cluster_info['best_cluster']+1} (유사도: {cluster_info['similarity']:.3f})")
        
        print()
    
    print("=" * 60)


def safe_input(prompt: str, default: str = "", input_type: str = "str") -> Any:
    """안전한 입력을 받습니다."""
    try:
        user_input = input(prompt).strip()
        if not user_input and default:
            user_input = default
        
        if input_type == "int":
            return int(user_input)
        elif input_type == "float":
            return float(user_input)
        else:
            return user_input
    except (ValueError, KeyboardInterrupt):
        return None


def create_directory_if_not_exists(directory: str) -> bool:
    """디렉토리가 없으면 생성합니다."""
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f" 디렉토리 생성: {directory}")
        return True
    except Exception as e:
        print(f" 디렉토리 생성 실패: {e}")
        return False


def get_file_size_mb(file_path: str) -> float:
    """파일 크기를 MB 단위로 반환합니다."""
    try:
        if os.path.exists(file_path):
            return os.path.getsize(file_path) / (1024 * 1024)
        return 0.0
    except Exception:
        return 0.0


def format_file_size(size_bytes: int) -> str:
    """파일 크기를 읽기 쉬운 형태로 포맷팅합니다."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def validate_date_format(date_str: str) -> bool:
    """날짜 형식의 유효성을 검사합니다."""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def extract_numbers_from_data(data: Dict) -> List[int]:
    """데이터에서 번호를 추출합니다."""
    numbers = []
    for i in range(1, 7):
        key = f'번호{i}'
        if key in data and data[key]:
            try:
                numbers.append(int(data[key]))
            except (ValueError, TypeError):
                continue
    return sorted(numbers) 