#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
리팩토링된 로또 번호 추천 시스템 v4.0
"""

import csv
import json
import os
import random
import requests
from bs4 import BeautifulSoup
import time
from collections import Counter
from datetime import datetime
from typing import List, Dict, Optional, Set, Tuple, Any

# 유틸리티 import
from utils.constants import *
from utils.helpers import *

# 외부 모듈 import
try:
    from lotto_manager import LottoManager
    from pattern_analyzer import PatternAnalyzer
except ImportError:
    print("[WARN] 일부 모듈을 찾을 수 없습니다.")

# DNN 기능을 선택적으로 import
try:
    import tensorflow as tf
    print(f" TensorFlow {tf.__version__} 감지됨")
    from dnn_lotto_predictor import DNNLottoPredictor
    DNN_AVAILABLE = True
    print(" DNN 기능이 활성화되었습니다.")
except ImportError as e:
    print("[WARN] TensorFlow가 설치되지 않아 DNN 기능을 사용할 수 없습니다.")
    print("   DNN 기능을 사용하려면 다음 명령어로 TensorFlow를 설치하세요:")
    print("   pip install tensorflow")
    DNN_AVAILABLE = False

# AI 패턴 학습을 위한 추가 라이브러리
try:
    import numpy as np
    import pandas as pd
    from sklearn.cluster import KMeans, DBSCAN
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.preprocessing import StandardScaler
    import joblib
    import pickle
    AI_PATTERN_AVAILABLE = True
    print(" AI 패턴 학습 기능이 활성화되었습니다.")
except ImportError as e:
    print("[WARN] AI 패턴 학습에 필요한 라이브러리가 설치되지 않았습니다.")
    print("   다음 명령어로 필요한 라이브러리를 설치하세요:")
    print("   pip install scikit-learn pandas numpy joblib")
    print(f"   상세 오류: {e}")
    AI_PATTERN_AVAILABLE = False

# 선 연결 패턴 분석을 위한 라이브러리
try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    from matplotlib.patches import FancyArrowPatch
    import math
    LINE_PATTERN_AVAILABLE = True
    print(" 선 연결 패턴 분석 기능이 활성화되었습니다.")
except ImportError as e:
    print("[WARN] 선 연결 패턴 분석에 필요한 라이브러리가 설치되지 않았습니다.")
    print("   다음 명령어로 설치하세요:")
    print("   pip install matplotlib")
    print(f"   상세 오류: {e}")
    LINE_PATTERN_AVAILABLE = False


# 공통 로직 함수들
def get_recommendation_params(exclude_manager) -> Dict[str, Any]:
    """추천 파라미터를 가져오는 공통 함수"""
    return {
        'exclude_numbers': exclude_manager.get_exclude_numbers(),
        'num_recommendations': safe_input("추천 번호 개수 (기본 5): ", "5", "int") or 5
    }

def generate_random_recommendation(exclude_numbers: Set[int], method: str, score_range: Tuple[float, float] = (0.1, 0.9)) -> Dict[str, Any]:
    """랜덤 추천 번호를 생성하는 공통 함수"""
    available_numbers = [n for n in range(1, MAX_LOTTO_NUMBER + 1) if n not in exclude_numbers]
    if len(available_numbers) < NUM_LOTTO_NUMBERS_TO_PICK:
        return None
    
    numbers = sorted(random.sample(available_numbers, NUM_LOTTO_NUMBERS_TO_PICK))
    score = random.uniform(score_range[0], score_range[1])
    
    return {
        'numbers': numbers,
        'score': score,
        'method': method,
        'consecutive_count': 0,
        'sum': sum(numbers)
    }

def remove_duplicate_recommendations(recommendations: List[Dict]) -> List[Dict]:
    """중복 추천을 제거하는 공통 함수"""
    unique_recommendations = []
    seen_combinations = set()
    
    for rec in recommendations:
        numbers_tuple = tuple(sorted(rec['numbers']))
        if numbers_tuple not in seen_combinations:
            seen_combinations.add(numbers_tuple)
            unique_recommendations.append(rec)
    
    return unique_recommendations

def process_recommendation_save(recommendations: List[Dict], lotto_manager, title: str):
    """추천 결과 출력 및 저장 처리 공통 함수"""
    if not recommendations:
        print(f" {title}을 생성할 수 없습니다.")
        return
    
    print_recommendations(recommendations, title)
    
    # 저장 여부 확인
    save_choice = safe_input("\n추천번호를 저장하시겠습니까? (y/n): ", "n")
    if save_choice and save_choice.lower() in ['y', 'yes', '예']:
        save_recommendations_to_tickets(recommendations, lotto_manager)

def generate_recommendations_with_retry(exclude_numbers: Set[int], num_recommendations: int, 
                                      method: str, generator_func, max_attempts: int = None) -> List[Dict]:
    """재시도 로직을 포함한 추천 생성 공통 함수"""
    if max_attempts is None:
        max_attempts = num_recommendations * 100
    
    recommendations = []
    attempts = 0
    
    while len(recommendations) < num_recommendations and attempts < max_attempts:
        attempts += 1
        
        try:
            recommendation = generator_func(exclude_numbers)
            if recommendation is None:
                continue
            
            # 중복 검사
            numbers_tuple = tuple(sorted(recommendation['numbers']))
            if any(tuple(sorted(rec['numbers'])) == numbers_tuple for rec in recommendations):
                continue
            
            recommendations.append(recommendation)
            
        except Exception:
            continue
    
    return recommendations

def get_recent_numbers(analyzer, num_rounds: int = 10) -> List[int]:
    """최근 당첨번호를 가져오는 공통 함수"""
    recent_numbers = []
    for row in analyzer.data[-num_rounds:]:
        numbers = extract_numbers_from_data(row)
        if validate_numbers(numbers):
            recent_numbers.extend(numbers)
    return recent_numbers

def create_backup_file(filename: str) -> str:
    """백업 파일 생성 공통 함수"""
    if os.path.exists(filename):
        backup_filename = f"{filename}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.rename(filename, backup_filename)
        print(f" 기존 파일 백업: {backup_filename}")
        return backup_filename
    return None


class ExcludeNumberManager:
    """제외번호 관리 클래스"""
    
    def __init__(self, filename: str = DEFAULT_EXCLUDE_FILE):
        self.filename = filename
        self.exclude_numbers = set()
        self.load_exclude_numbers()
    
    def load_exclude_numbers(self) -> bool:
        """제외번호를 파일에서 로드합니다."""
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.exclude_numbers = set(data.get('exclude_numbers', []))
            return True
        except (FileNotFoundError, json.JSONDecodeError):
            self.exclude_numbers = set()
            return False
    
    def save_exclude_numbers(self) -> bool:
        """제외번호를 파일에 저장합니다."""
        try:
            data = {'exclude_numbers': list(self.exclude_numbers)}
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f" 제외번호 저장 실패: {e}")
            return False
    
    def add_exclude_numbers(self, numbers: List[int]) -> bool:
        """제외번호를 추가합니다."""
        try:
            for num in numbers:
                if 1 <= num <= MAX_LOTTO_NUMBER:
                    self.exclude_numbers.add(num)
            return self.save_exclude_numbers()
        except Exception as e:
            print(f" 제외번호 추가 실패: {e}")
            return False
    
    def remove_exclude_numbers(self, numbers: List[int]) -> bool:
        """제외번호를 제거합니다."""
        try:
            for num in numbers:
                self.exclude_numbers.discard(num)
            return self.save_exclude_numbers()
        except Exception as e:
            print(f" 제외번호 제거 실패: {e}")
            return False
    
    def clear_exclude_numbers(self) -> bool:
        """모든 제외번호를 제거합니다."""
        try:
            self.exclude_numbers.clear()
            return self.save_exclude_numbers()
        except Exception as e:
            print(f" 제외번호 초기화 실패: {e}")
            return False
    
    def get_exclude_numbers(self) -> Set[int]:
        """제외번호를 반환합니다."""
        return self.exclude_numbers.copy()
    
    def show_exclude_numbers(self):
        """제외번호를 표시합니다."""
        if not self.exclude_numbers:
            print(" 제외번호가 설정되지 않았습니다.")
            return
        
        print(f" 현재 제외번호 ({len(self.exclude_numbers)}개): {sorted(self.exclude_numbers)}")
    
    def is_valid_for_lotto(self) -> bool:
        """제외번호가 로또에 적합한지 확인합니다."""
        return len(self.exclude_numbers) < MAX_LOTTO_NUMBER - NUM_LOTTO_NUMBERS_TO_PICK
    
    def get_available_numbers(self) -> List[int]:
        """사용 가능한 번호들을 반환합니다."""
        return [n for n in range(1, MAX_LOTTO_NUMBER + 1) if n not in self.exclude_numbers]


class LottoDataCollector:
    """동행복권 사이트에서 로또 당첨번호를 수집하는 클래스"""
    
    def __init__(self):
        self.base_url = URL_TEMPLATES['BASE_URL']
        self.search_url = URL_TEMPLATES['SEARCH_URL']
        self.round_url_template = URL_TEMPLATES['ROUND_URL']
        self.api_url_template = "https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={}"
        self.headers = DEFAULT_HEADERS

    def _fetch_round_json(self, round_num: int) -> Optional[Dict]:
        try:
            url = self.api_url_template.format(int(round_num))
            response = requests.get(url, headers=self.headers, timeout=3)
            response.raise_for_status()
            payload = response.json()
            return payload if payload.get("returnValue") == "success" else None
        except Exception:
            return None

    def _find_latest_round_via_api(self) -> Optional[int]:
        lo, hi = 1, 2048
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if self._fetch_round_json(mid):
                lo = mid
            else:
                hi = mid - 1
        return lo if lo >= 1 else None
    
    def get_latest_round(self) -> Optional[int]:
        """최신 회차 정보를 가져옵니다."""
        latest_round = self._find_latest_round_via_api()
        if latest_round:
            return latest_round

        try:
            response = requests.get(self.search_url, headers=self.headers, timeout=3)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 최신 회차 정보 찾기 (여러 방법 시도)
            latest_round = None
            
            # 방법 1: win_result 영역에서 찾기
            win_result = soup.find('div', class_='win_result')
            if win_result:
                h4_element = win_result.find('h4')
                if h4_element:
                    round_text = h4_element.get_text().strip()
                    if '회' in round_text:
                        round_number = int(round_text.split('회')[0])
                        latest_round = round_number
            
            # 방법 2: 다른 클래스나 구조에서 찾기
            if not latest_round:
                table = soup.find('table', class_='t_auto')
                if table:
                    rows = table.find_all('tr')
                    for row in rows:
                        cells = row.find_all('td')
                        if len(cells) >= 1:
                            first_cell = cells[0].get_text().strip()
                            if first_cell.isdigit():
                                latest_round = int(first_cell)
                                break
            
            # 방법 3: 페이지 제목에서 찾기
            if not latest_round:
                title = soup.find('title')
                if title:
                    title_text = title.get_text()
                    import re
                    match = re.search(r'(\d+)회', title_text)
                    if match:
                        latest_round = int(match.group(1))
            
            return latest_round
            
        except Exception as e:
            print(f" 최신 회차 HTML 조회 실패: {e}")
            return None
    
    def collect_winning_numbers(self, start_round: Optional[int] = None, 
                              end_round: Optional[int] = None, 
                              max_rounds: int = 100) -> List[Dict]:
        """지정된 범위의 당첨번호를 수집합니다."""
        print(" 동행복권 사이트에서 당첨번호 수집 중...")
        
        # 최신 회차 확인
        latest_round = self.get_latest_round()
        if not latest_round:
            print(" 최신 회차 정보를 가져올 수 없습니다.")
            return []
        
        print(f"[INFO] 최신 회차: {latest_round}회")
        
        # 수집 범위 설정
        if end_round is None:
            end_round = latest_round
        
        if start_round is None:
            start_round = max(1, end_round - max_rounds + 1)
        
        print(f" 수집 범위: {start_round}회 ~ {end_round}회")
        
        collected_data = []
        failed_rounds = []
        
        for round_num in range(start_round, end_round + 1):
            try:
                print(f"    {round_num}회 수집 중...", end=" ")
                
                # 회차별 당첨번호 페이지 URL
                round_url = self.round_url_template.format(round_num)
                
                response = requests.get(round_url, headers=self.headers, timeout=6)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # 당첨번호 추출
                numbers = self._extract_numbers(soup, round_num)
                if not numbers:
                    payload = self._fetch_round_json(round_num)
                    if payload:
                        numbers = [
                            int(payload.get('drwtNo1')),
                            int(payload.get('drwtNo2')),
                            int(payload.get('drwtNo3')),
                            int(payload.get('drwtNo4')),
                            int(payload.get('drwtNo5')),
                            int(payload.get('drwtNo6')),
                        ]
                
                if numbers and len(numbers) == 6:
                    data = {
                        '회차': round_num,
                        '번호1': numbers[0],
                        '번호2': numbers[1],
                        '번호3': numbers[2],
                        '번호4': numbers[3],
                        '번호5': numbers[4],
                        '번호6': numbers[5]
                    }
                    collected_data.append(data)
                    print("")
                else:
                    print("")
                    failed_rounds.append(round_num)
                
                # 서버 부하 방지를 위한 대기
                time.sleep(0.5)
                
            except Exception as e:
                print(f" (오류: {e})")
                failed_rounds.append(round_num)
                continue
        
        print(f"\n 수집 완료: {len(collected_data)}개 성공, {len(failed_rounds)}개 실패")
        
        if failed_rounds:
            print(f" 실패한 회차: {failed_rounds}")
        
        return collected_data
    
    def _extract_numbers(self, soup: BeautifulSoup, round_num: int) -> List[int]:
        """HTML에서 당첨번호를 추출합니다."""
        numbers = []
        
        # 방법 1: 당첨번호 div에서 추출
        win_result = soup.find('div', class_='win_result')
        if win_result:
            spans = win_result.find_all('span', class_='ball_645')
            for span in spans:
                try:
                    numbers.append(int(span.get_text().strip()))
                except (ValueError, TypeError):
                    continue
        
        # 방법 2: 테이블에서 추출
        if len(numbers) != 6:
            numbers = []
            table = soup.find('table', class_='t_auto')
            if table:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 7:  # 회차 + 6개 번호
                        try:
                            round_cell = int(cells[0].get_text().strip())
                            if round_cell == round_num:
                                for i in range(1, 7):
                                    numbers.append(int(cells[i].get_text().strip()))
                                break
                        except (ValueError, TypeError, IndexError):
                            continue
        
        # 방법 3: 다양한 span 클래스에서 추출
        if len(numbers) != 6:
            numbers = []
            span_classes = ['ball_645', 'num', 'number', 'ball']
            for class_name in span_classes:
                spans = soup.find_all('span', class_=class_name)
                for span in spans:
                    try:
                        num = int(span.get_text().strip())
                        if 1 <= num <= 45 and num not in numbers:
                            numbers.append(num)
                        if len(numbers) == 6:
                            break
                    except (ValueError, TypeError):
                        continue
                if len(numbers) == 6:
                    break
        
        return sorted(numbers) if len(numbers) == 6 else []
    
    def save_to_csv(self, data: List[Dict], filename: str = DEFAULT_CSV_FILE) -> bool:
        """수집된 데이터를 CSV 파일로 저장합니다."""
        if not data:
            print(" 저장할 데이터가 없습니다.")
            return False
        
        try:
            # 기존 파일 백업
            create_backup_file(filename)
            
            # 새 데이터 저장
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                fieldnames = ['회차', '번호1', '번호2', '번호3', '번호4', '번호5', '번호6']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
            
            print(f" {len(data)}개 데이터가 {filename}에 저장되었습니다.")
            return True
            
        except Exception as e:
            print(f" CSV 저장 실패: {e}")
            return False
    
    def update_latest_data(self, max_rounds: int = 10) -> bool:
        """최신 데이터만 업데이트합니다."""
        try:
            # 기존 데이터 로드
            existing_data = []
            if os.path.exists(DEFAULT_CSV_FILE):
                with open(DEFAULT_CSV_FILE, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    existing_data = list(reader)
            
            if existing_data:
                # 최신 회차 확인
                latest_existing = max(int(row['회차']) for row in existing_data)
                print(f"[INFO] 기존 데이터 최신 회차: {latest_existing}회")
                
                # 새 데이터 수집
                new_data = self.collect_winning_numbers(
                    start_round=latest_existing + 1,
                    max_rounds=max_rounds
                )
                
                if new_data:
                    # 기존 데이터와 병합
                    all_data = existing_data + new_data
                    
                    # 중복 제거 (회차 기준)
                    seen_rounds = set()
                    unique_data = []
                    for row in all_data:
                        round_num = int(row['회차'])
                        if round_num not in seen_rounds:
                            seen_rounds.add(round_num)
                            unique_data.append(row)
                    
                    # 회차순으로 정렬
                    unique_data.sort(key=lambda x: int(x['회차']))
                    
                    # 저장
                    return self.save_to_csv(unique_data)
                else:
                    print("[INFO] 새로운 데이터가 없습니다.")
                    return True
            else:
                # 기존 데이터가 없으면 전체 수집
                print("[INFO] 기존 데이터가 없어 전체 수집을 진행합니다.")
                new_data = self.collect_winning_numbers(max_rounds=max_rounds)
                return self.save_to_csv(new_data) if new_data else False
                
        except Exception as e:
            print(f" 데이터 업데이트 실패: {e}")
            return False


class LottoAnalyzer:
    """로또 분석 메인 클래스"""
    
    def __init__(self, csv_file: str = DEFAULT_CSV_FILE):
        self.csv_file = csv_file
        self.data = []
        self.winning_numbers = []
        self.frequency_analysis = None
        self.recent_patterns = None
        
        # 분석기들
        self.statistical_analyzer = None
        self.pattern_analyzer = None
        self.ensemble_analyzer = None
        self.mersenne_analyzer = None
        self.trend_analyzer = None
        self.dnn_predictor = None
        self.pattern_grouping = None
        self.line_analyzer = None
        
        # 데이터 로드
        self.load_data()
        
        # 분석기 초기화
        self._initialize_analyzers()
    
    def load_data(self) -> bool:
        """CSV 파일에서 데이터를 로드합니다."""
        try:
            print(f" {self.csv_file} 파일 로드 중...")
            
            # 인코딩 시도
            encodings = ['utf-8', 'cp949', 'euc-kr']
            data = None
            
            for encoding in encodings:
                try:
                    with open(self.csv_file, 'r', encoding=encoding) as f:
                        reader = csv.DictReader(f)
                        data = list(reader)
                    print(f" {encoding} 인코딩으로 성공적으로 읽었습니다!")
                    break
                except UnicodeDecodeError:
                    continue
            
            if data is None:
                print(" 파일을 읽을 수 없습니다.")
                return False
            
            self.data = data
            self.winning_numbers = self.extract_winning_numbers()
            
            print(f"[INFO] 총 {len(self.data)}회의 데이터가 로드되었습니다.")
            return True
            
        except Exception as e:
            print(f" 데이터 로드 실패: {e}")
            return False
    
    def extract_winning_numbers(self) -> List[List[int]]:
        """당첨번호들을 추출합니다."""
        numbers_list = []
        for row in self.data:
            numbers = extract_numbers_from_data(row)
            if validate_numbers(numbers):
                numbers_list.append(numbers)
        return numbers_list
    
    def _initialize_analyzers(self):
        """분석기들을 초기화합니다."""
        if not self.data:
            return
        
        print("\n 분석기 초기화 중...")
        
        # 기본 분석기들
        try:
            from analyzers.statistical_analyzer import StatisticalAnalyzer
            self.statistical_analyzer = StatisticalAnalyzer(self.data)
            print("    통계 분석기 초기화 완료")
        except ImportError:
            print("    통계 분석기 초기화 실패")
        
        # AI 패턴 학습 초기화
        if AI_PATTERN_AVAILABLE:
            try:
                from analyzers.lotto_pattern_grouping import LottoPatternGrouping
                self.pattern_grouping = LottoPatternGrouping(self.data)
                print("    AI 패턴 학습 초기화 완료")
            except ImportError:
                print("    AI 패턴 학습 초기화 실패")
        
        # 선 연결 패턴 분석 초기화
        if LINE_PATTERN_AVAILABLE:
            try:
                from analyzers.line_pattern_analyzer import LinePatternAnalyzer
                self.line_analyzer = LinePatternAnalyzer(self.data)
                print("    선 연결 패턴 분석 초기화 완료")
            except ImportError:
                print("    선 연결 패턴 분석 초기화 실패")
        
        # DNN 예측기 초기화
        if DNN_AVAILABLE:
            try:
                self.dnn_predictor = DNNLottoPredictor()
                print("    DNN 예측기 초기화 완료")
            except Exception as e:
                print(f"    DNN 예측기 초기화 실패: {e}")
        
        print(" 분석기 초기화 완료!")


def main():
    """메인 함수"""
    print(" 로또 번호 추천 시스템 v4.0 (리팩토링 버전)")
    print("=" * 60)
    
    # 패키지 설치 상태 확인
    basic_available, dnn_available, ai_pattern_available, line_pattern_available = check_installation_status()
    
    # 시스템 정보 표시
    show_system_info()
    
    # 관리자 객체들 초기화
    exclude_manager = ExcludeNumberManager()
    lotto_manager = LottoManager()
    
    # 메인 루프
    while True:
        print("\n 메인 메뉴")
        print("=" * 60)
        print("1. [INFO] 번호 추천")
        print("2.  제외번호 관리")
        print("3.  구매 내역 관리")
        print("4.  통계 보기")
        print("5.  제외번호 추천")
        print("6.  당첨번호 수집")
        print("7.  DNN 기반 예측")
        print("8.  앙상블 분석")
        print("9.  AI 패턴 학습")
        print("10.  선 연결 패턴 분석")
        print("11.  패키지 설치 상태 확인")
        print("0. 종료")
        print("=" * 60)
        
        choice = safe_input("\n 메뉴를 선택하세요 (0-11): ", input_type="str")
        
        if choice == MENU_OPTIONS['MAIN_MENU']['EXIT']:
            print(" 프로그램을 종료합니다.")
            break
        
        elif choice == MENU_OPTIONS['MAIN_MENU']['RECOMMEND']:
            # 번호 추천 기능
            handle_recommendation_menu(exclude_manager, lotto_manager)
        
        elif choice == MENU_OPTIONS['MAIN_MENU']['EXCLUDE']:
            # 제외번호 관리
            handle_exclude_menu(exclude_manager)
        
        elif choice == MENU_OPTIONS['MAIN_MENU']['TICKETS']:
            # 구매 내역 관리
            handle_tickets_menu(lotto_manager)
        
        elif choice == MENU_OPTIONS['MAIN_MENU']['STATISTICS']:
            # 통계 보기
            handle_statistics_menu()
        
        elif choice == MENU_OPTIONS['MAIN_MENU']['EXCLUDE_RECOMMEND']:
            # 제외번호 추천
            handle_exclude_recommendation_menu(exclude_manager)
        
        elif choice == MENU_OPTIONS['MAIN_MENU']['DATA_COLLECTION']:
            # 당첨번호 수집
            handle_data_collection_menu()
        
        elif choice == MENU_OPTIONS['MAIN_MENU']['DNN_PREDICT']:
            # DNN 기반 예측
            if DNN_AVAILABLE:
                handle_dnn_menu(exclude_manager, lotto_manager)
            else:
                print(" DNN 기능을 사용할 수 없습니다.")
        
        elif choice == MENU_OPTIONS['MAIN_MENU']['ENSEMBLE']:
            # 앙상블 분석
            handle_ensemble_menu(exclude_manager, lotto_manager)
        
        elif choice == MENU_OPTIONS['MAIN_MENU']['AI_PATTERN']:
            # AI 패턴 학습
            if AI_PATTERN_AVAILABLE:
                handle_ai_pattern_menu(exclude_manager, lotto_manager)
            else:
                print(" AI 패턴 학습 기능을 사용할 수 없습니다.")
        
        elif choice == MENU_OPTIONS['MAIN_MENU']['LINE_PATTERN']:
            # 선 연결 패턴 분석
            if LINE_PATTERN_AVAILABLE:
                handle_line_pattern_menu(exclude_manager, lotto_manager)
            else:
                print(" 선 연결 패턴 분석 기능을 사용할 수 없습니다.")
        
        elif choice == MENU_OPTIONS['MAIN_MENU']['SYSTEM_INFO']:
            # 시스템 정보
            show_system_info()
        
        else:
            print(" 잘못된 선택입니다. 0-11 중에서 선택해주세요.")
        
        # 메뉴 간 구분선
        print("\n" + "=" * 60)


def handle_recommendation_menu(exclude_manager: ExcludeNumberManager, 
                             lotto_manager: LottoManager):
    """번호 추천 메뉴 처리"""
    print("\n[INFO] 번호 추천 메뉴")
    print("=" * 40)
    print("1. 통계 기반 추천")
    print("2. 패턴 매칭 추천")
    print("3. 앙상블 추천")
    print("4. 메르센 트위스터 추천")
    print("5. 최근 추세 추천")
    print("6. 뒤로가기")
    print("=" * 40)
    
    sub_choice = safe_input("선택 (1-6): ", input_type="str")
    
    if sub_choice == '1':
        # 통계 기반 추천
        handle_statistical_recommendation(exclude_manager, lotto_manager)
    elif sub_choice == '2':
        # 패턴 매칭 추천
        handle_pattern_recommendation(exclude_manager, lotto_manager)
    elif sub_choice == '3':
        # 앙상블 추천
        handle_ensemble_recommendation(exclude_manager, lotto_manager)
    elif sub_choice == '4':
        # 메르센 트위스터 추천
        handle_mersenne_recommendation(exclude_manager, lotto_manager)
    elif sub_choice == '5':
        # 최근 추세 추천
        handle_trend_recommendation(exclude_manager, lotto_manager)
    elif sub_choice == '6':
        print(" 메인 메뉴로 돌아갑니다.")
    else:
        print(" 잘못된 선택입니다.")


def handle_statistical_recommendation(exclude_manager: ExcludeNumberManager, 
                                    lotto_manager: LottoManager):
    """통계 기반 추천 처리"""
    try:
        analyzer = LottoAnalyzer()
        if not analyzer.statistical_analyzer:
            print(" 통계 분석기를 초기화할 수 없습니다.")
            return
        
        params = get_recommendation_params(exclude_manager)
        recommendations = analyzer.statistical_analyzer.generate_recommendations(
            params['exclude_numbers'], params['num_recommendations']
        )
        
        process_recommendation_save(recommendations, lotto_manager, "통계 기반 추천 번호")
            
    except Exception as e:
        print(f" 통계 기반 추천 중 오류 발생: {e}")


def save_recommendations_to_tickets(recommendations: List[Dict], 
                                  lotto_manager: LottoManager):
    """추천번호를 구매 내역에 저장합니다."""
    for i, rec in enumerate(recommendations, 1):
        try:
            purchase_date = safe_input(f"{i}번 추천번호 구매일 (예: 2024-01-15): ")
            if not purchase_date or not validate_date_format(purchase_date):
                print(f" {i}번 추천번호 저장을 건너뜁니다.")
                continue
            
            purchase_amount = safe_input(f"{i}번 추천번호 구매 금액 (기본 1000원): ", "1000", "int") or 1000
            
            if lotto_manager.add_ticket(rec['numbers'], purchase_date, purchase_amount):
                print(f" {i}번 추천번호가 저장되었습니다.")
            else:
                print(f" {i}번 추천번호 저장에 실패했습니다.")
        except Exception as e:
            print(f" {i}번 추천번호 저장 중 오류: {e}")
            continue


def handle_exclude_menu(exclude_manager: ExcludeNumberManager):
    """제외번호 관리 메뉴 처리"""
    while True:
        print("\n 제외번호 관리 메뉴")
        print("=" * 40)
        print("1. 제외번호 보기")
        print("2. 제외번호 추가")
        print("3. 제외번호 제거")
        print("4. 제외번호 초기화")
        print("5. 뒤로가기")
        print("=" * 40)
        
        sub_choice = safe_input("선택 (1-5): ", input_type="str")
        
        if sub_choice == '1':
            exclude_manager.show_exclude_numbers()
        elif sub_choice == '2':
            numbers_input = safe_input("추가할 번호들 (예: 1,2,3): ")
            if numbers_input:
                try:
                    numbers = [int(x.strip()) for x in numbers_input.split(',')]
                    if exclude_manager.add_exclude_numbers(numbers):
                        print(" 제외번호가 추가되었습니다.")
                    else:
                        print(" 제외번호 추가에 실패했습니다.")
                except ValueError:
                    print(" 잘못된 번호 형식입니다.")
        elif sub_choice == '3':
            numbers_input = safe_input("제거할 번호들 (예: 1,2,3): ")
            if numbers_input:
                try:
                    numbers = [int(x.strip()) for x in numbers_input.split(',')]
                    if exclude_manager.remove_exclude_numbers(numbers):
                        print(" 제외번호가 제거되었습니다.")
                    else:
                        print(" 제외번호 제거에 실패했습니다.")
                except ValueError:
                    print(" 잘못된 번호 형식입니다.")
        elif sub_choice == '4':
            confirm = safe_input("모든 제외번호를 초기화하시겠습니까? (y/n): ")
            if confirm and confirm.lower() in ['y', 'yes', '예']:
                if exclude_manager.clear_exclude_numbers():
                    print(" 제외번호가 초기화되었습니다.")
                else:
                    print(" 제외번호 초기화에 실패했습니다.")
        elif sub_choice == '5':
            print(" 메인 메뉴로 돌아갑니다.")
            break
        else:
            print(" 잘못된 선택입니다.")


def handle_tickets_menu(lotto_manager: LottoManager):
    """구매 내역 관리 메뉴 처리"""
    while True:
        print("\n 구매 내역 관리 메뉴")
        print("=" * 40)
        print("1. 구매 내역 보기")
        print("2. 구매 내역 추가")
        print("3. 구매 내역 삭제")
        print("4. 뒤로가기")
        print("=" * 40)
        
        sub_choice = safe_input("선택 (1-4): ", input_type="str")
        
        if sub_choice == '1':
            tickets = lotto_manager.get_tickets()
            if tickets:
                print(f"\n 구매 내역 ({len(tickets)}개):")
                for i, ticket in enumerate(tickets, 1):
                    numbers = ticket.get('numbers', [])
                    date = ticket.get('date', '알 수 없음')
                    amount = ticket.get('amount', 0)
                    print(f"{i}. {format_numbers(numbers)} - {date} ({amount:,}원)")
            else:
                print(" 구매 내역이 없습니다.")
        elif sub_choice == '2':
            numbers_input = safe_input("번호들 (예: 1,2,3,4,5,6): ")
            if numbers_input:
                try:
                    numbers = [int(x.strip()) for x in numbers_input.split(',')]
                    if validate_numbers(numbers):
                        date = safe_input("구매일 (예: 2024-01-15): ")
                        amount = safe_input("구매 금액 (기본 1000원): ", "1000", "int") or 1000
                        
                        if lotto_manager.add_ticket(numbers, date, amount):
                            print(" 구매 내역이 추가되었습니다.")
                        else:
                            print(" 구매 내역 추가에 실패했습니다.")
                    else:
                        print(" 잘못된 번호 조합입니다.")
                except ValueError:
                    print(" 잘못된 번호 형식입니다.")
        elif sub_choice == '3':
            tickets = lotto_manager.get_tickets()
            if tickets:
                print(f"\n 구매 내역 ({len(tickets)}개):")
                for i, ticket in enumerate(tickets, 1):
                    numbers = ticket.get('numbers', [])
                    date = ticket.get('date', '알 수 없음')
                    print(f"{i}. {format_numbers(numbers)} - {date}")
                
                delete_index = safe_input("삭제할 내역 번호: ", input_type="int")
                if delete_index and 1 <= delete_index <= len(tickets):
                    if lotto_manager.delete_ticket(delete_index - 1):
                        print(" 구매 내역이 삭제되었습니다.")
                    else:
                        print(" 구매 내역 삭제에 실패했습니다.")
                else:
                    print(" 잘못된 번호입니다.")
            else:
                print(" 삭제할 구매 내역이 없습니다.")
        elif sub_choice == '4':
            print(" 메인 메뉴로 돌아갑니다.")
            break
        else:
            print(" 잘못된 선택입니다.")


def handle_statistics_menu():
    """통계 보기 메뉴 처리"""
    try:
        analyzer = LottoAnalyzer()
        if not analyzer.data:
            print(" 데이터가 없어 통계를 계산할 수 없습니다.")
            return
        
        print("\n 통계 분석")
        print("=" * 40)
        
        # 빈도 분석
        if analyzer.statistical_analyzer:
            frequency_analysis = analyzer.statistical_analyzer.analyze_frequency()
            if frequency_analysis:
                print("\n[INFO] 번호별 출현 빈도 (상위 10개):")
                for num, count in frequency_analysis['most_common']:
                    print(f"   {num}번: {count}회")
        
        # 합계 분석
        if analyzer.statistical_analyzer:
            sum_analysis = analyzer.statistical_analyzer.analyze_sum_range()
            if sum_analysis:
                print(f"\n[INFO] 합계 통계:")
                print(f"   평균: {sum_analysis['avg_sum']:.1f}")
                print(f"   최소: {sum_analysis['min_sum']}")
                print(f"   최대: {sum_analysis['max_sum']}")
                print(f"   범위: {sum_analysis['sum_range'][0]} ~ {sum_analysis['sum_range'][1]}")
        
        print("\n" + "=" * 40)
        
    except Exception as e:
        print(f" 통계 분석 중 오류 발생: {e}")


def handle_exclude_recommendation_menu(exclude_manager: ExcludeNumberManager):
    """제외번호 추천 메뉴 처리"""
    try:
        analyzer = LottoAnalyzer()
        if not analyzer.data:
            print(" 데이터가 없어 제외번호를 추천할 수 없습니다.")
            return
        
        print("\n 제외번호 추천")
        print("=" * 40)
        
        # 최근 당첨번호 분석
        recent_numbers = get_recent_numbers(analyzer, 10)
        
        if recent_numbers:
            from collections import Counter
            frequency = Counter(recent_numbers)
            most_common = frequency.most_common(5)
            
            print("[INFO] 최근 10회에서 자주 나온 번호들:")
            for num, count in most_common:
                print(f"   {num}번: {count}회")
            
            print("\n 제외번호 추천:")
            print("   자주 나온 번호들을 제외번호로 설정하는 것을 고려해보세요.")
        
        print("=" * 40)
        
    except Exception as e:
        print(f" 제외번호 추천 중 오류 발생: {e}")


def handle_data_collection_menu():
    """당첨번호 수집 메뉴 처리"""
    collector = LottoDataCollector()
    
    while True:
        print("\n 당첨번호 수집 메뉴")
        print("=" * 40)
        print("1. 최신 데이터 업데이트")
        print("2. 전체 데이터 수집")
        print("3. 특정 범위 수집")
        print("4. 뒤로가기")
        print("=" * 40)
        
        sub_choice = safe_input("선택 (1-4): ", input_type="str")
        
        if sub_choice == '1':
            max_rounds = safe_input("업데이트할 최대 회차 수 (기본 10): ", "10", "int") or 10
            if collector.update_latest_data(max_rounds):
                print(" 데이터 업데이트가 완료되었습니다.")
            else:
                print(" 데이터 업데이트에 실패했습니다.")
        elif sub_choice == '2':
            max_rounds = safe_input("수집할 최대 회차 수 (기본 100): ", "100", "int") or 100
            data = collector.collect_winning_numbers(max_rounds=max_rounds)
            if data and collector.save_to_csv(data):
                print(" 전체 데이터 수집이 완료되었습니다.")
            else:
                print(" 전체 데이터 수집에 실패했습니다.")
        elif sub_choice == '3':
            start_round = safe_input("시작 회차: ", input_type="int")
            end_round = safe_input("끝 회차: ", input_type="int")
            if start_round and end_round and start_round <= end_round:
                data = collector.collect_winning_numbers(start_round, end_round)
                if data and collector.save_to_csv(data):
                    print(" 특정 범위 데이터 수집이 완료되었습니다.")
                else:
                    print(" 특정 범위 데이터 수집에 실패했습니다.")
            else:
                print(" 잘못된 회차 범위입니다.")
        elif sub_choice == '4':
            print(" 메인 메뉴로 돌아갑니다.")
            break
        else:
            print(" 잘못된 선택입니다.")


def handle_dnn_menu(exclude_manager: ExcludeNumberManager, lotto_manager: LottoManager):
    """DNN 기반 예측 메뉴 처리"""
    try:
        analyzer = LottoAnalyzer()
        if not analyzer.dnn_predictor:
            print(" DNN 예측기를 초기화할 수 없습니다.")
            return
        
        while True:
            print("\n DNN 기반 예측 메뉴")
            print("=" * 40)
            print("1. DNN 모델 훈련")
            print("2. DNN 예측")
            print("3. DNN 모델 평가")
            print("4. 뒤로가기")
            print("=" * 40)
            
            sub_choice = safe_input("선택 (1-4): ", input_type="str")
            
            if sub_choice == '1':
                epochs = safe_input("훈련 에포크 수 (기본 100): ", "100", "int") or 100
                batch_size = safe_input("배치 크기 (기본 32): ", "32", "int") or 32
                
                if analyzer.dnn_predictor.train(csv_file='로또당첨번호.csv', epochs=epochs, batch_size=batch_size, use_improved_features=True):
                    print(" DNN 모델 훈련이 완료되었습니다.")
                else:
                    print(" DNN 모델 훈련에 실패했습니다.")
            
            elif sub_choice == '2':
                num_predictions = safe_input("예측 개수 (기본 5): ", "5", "int") or 5
                exclude_numbers = exclude_manager.get_exclude_numbers()
                
                predictions = analyzer.dnn_predictor.predict_numbers(
                    csv_file='로또당첨번호.csv',
                    num_predictions=num_predictions,
                    use_improved_features=True
                )
                
                if predictions:
                    print(f"\n DNN 예측 결과 ({len(predictions)}개):")
                    for i, pred in enumerate(predictions, 1):
                        print(f"{i}. {format_numbers(pred)}")
                else:
                    print(" DNN 예측에 실패했습니다.")
            
            elif sub_choice == '3':
                evaluation = analyzer.dnn_predictor.evaluate_model(csv_file='로또당첨번호.csv', use_improved_features=True)
                if evaluation:
                    print(f"\n[INFO] DNN 모델 평가 결과:")
                    print(f"   정확도: {evaluation['accuracy']:.3f}")
                    print(f"   MSE: {evaluation['mse']:.3f}")
                    print(f"   MAE: {evaluation['mae']:.3f}")
                else:
                    print(" DNN 모델 평가에 실패했습니다.")
            
            elif sub_choice == '4':
                print(" 메인 메뉴로 돌아갑니다.")
                break
            else:
                print(" 잘못된 선택입니다.")
                
    except Exception as e:
        print(f" DNN 메뉴 처리 중 오류 발생: {e}")


def handle_ensemble_menu(exclude_manager: ExcludeNumberManager, lotto_manager: LottoManager):
    """앙상블 분석 메뉴 처리"""
    try:
        analyzer = LottoAnalyzer()
        if not analyzer.data:
            print(" 데이터가 없어 앙상블 분석을 수행할 수 없습니다.")
            return
        
        exclude_numbers = exclude_manager.get_exclude_numbers()
        num_recommendations = safe_input("추천 번호 개수 (기본 5): ", "5", "int") or 5
        
        # 여러 분석기를 조합한 앙상블 추천
        all_recommendations = []
        
        # 통계 분석기
        if analyzer.statistical_analyzer:
            stat_recs = analyzer.statistical_analyzer.generate_recommendations(
                exclude_numbers, num_recommendations
            )
            all_recommendations.extend(stat_recs)
        
        # DNN 예측기
        if analyzer.dnn_predictor:
            dnn_predictions = analyzer.dnn_predictor.predict_numbers(
                csv_file='로또당첨번호.csv',
                num_predictions=num_recommendations,
                use_improved_features=True
            )
            for pred in dnn_predictions:
                all_recommendations.append({
                    'numbers': pred,
                    'score': 0.5,  # 기본 점수
                    'method': 'DNN 예측',
                    'consecutive_count': 0
                })
        
        if all_recommendations:
            # 점수순으로 정렬하고 중복 제거
            unique_recommendations = []
            seen_combinations = set()
            
            for rec in all_recommendations:
                numbers_tuple = tuple(sorted(rec['numbers']))
                if numbers_tuple not in seen_combinations:
                    seen_combinations.add(numbers_tuple)
                    unique_recommendations.append(rec)
            
            # 상위 추천만 선택
            unique_recommendations.sort(key=lambda x: x['score'], reverse=True)
            final_recommendations = unique_recommendations[:num_recommendations]
            
            print_recommendations(final_recommendations, "앙상블 추천 번호")
            
            # 저장 여부 확인
            save_choice = safe_input("\n추천번호를 저장하시겠습니까? (y/n): ", "n")
            if save_choice and save_choice.lower() in ['y', 'yes', '예']:
                save_recommendations_to_tickets(final_recommendations, lotto_manager)
        else:
            print(" 앙상블 추천을 생성할 수 없습니다.")
            
    except Exception as e:
        print(f" 앙상블 분석 중 오류 발생: {e}")


def handle_ai_pattern_menu(exclude_manager: ExcludeNumberManager, lotto_manager: LottoManager):
    """AI 패턴 학습 메뉴 처리"""
    try:
        analyzer = LottoAnalyzer()
        if not analyzer.pattern_grouping:
            print(" AI 패턴 학습을 초기화할 수 없습니다.")
            return
        
        while True:
            print("\n AI 패턴 학습 메뉴")
            print("=" * 40)
            print("1. 패턴 그룹 생성")
            print("2. AI 모델 훈련")
            print("3. 높은 확률 조합 예측")
            print("4. 분석 보고서 보기")
            print("5. 뒤로가기")
            print("=" * 40)
            
            sub_choice = safe_input("선택 (1-5): ", input_type="str")
            
            if sub_choice == '1':
                group_size = safe_input("그룹 크기 (기본 5): ", "5", "int") or 5
                n_clusters = safe_input("클러스터 수 (기본 5): ", "5", "int") or 5
                
                analyzer.pattern_grouping.create_round_groups(group_size)
                analyzer.pattern_grouping.create_pattern_features()
                analyzer.pattern_grouping.perform_clustering(n_clusters)
                print(" 패턴 그룹 생성이 완료되었습니다.")
            
            elif sub_choice == '2':
                analyzer.pattern_grouping.train_ai_models()
                print(" AI 모델 훈련이 완료되었습니다.")
            
            elif sub_choice == '3':
                exclude_numbers = exclude_manager.get_exclude_numbers()
                num_combinations = safe_input("예측 조합 수 (기본 10): ", "10", "int") or 10
                
                combinations = analyzer.pattern_grouping.predict_high_probability_combinations(
                    exclude_numbers, num_combinations
                )
                
                if combinations:
                    print(f"\n AI 패턴 학습 예측 결과 ({len(combinations)}개):")
                    for i, comb in enumerate(combinations, 1):
                        numbers = comb.get('numbers', [])
                        probability = comb.get('probability', 0)
                        print(f"{i}. {format_numbers(numbers)} (확률: {probability:.3f})")
                    
                    # 공통 번호 분석
                    common_analysis = analyzer.pattern_grouping.find_common_numbers(combinations)
                    
                    if common_analysis['common_numbers']:
                        print(f"\n[CHECK] 공통 번호 분석:")
                        print(f"   [INFO] 모든 조합에 나타나는 번호: {common_analysis['common_numbers']}")
                        print(f"    총 조합 수: {common_analysis['total_combinations']}개")
                    
                    if common_analysis['frequent_numbers']:
                        print(f"\n[INFO] 자주 나타나는 번호들 (50% 이상):")
                        for num, freq in common_analysis['frequent_numbers'][:5]:
                            percentage = freq * 100
                            print(f"   {num}번: {percentage:.1f}% ({int(freq * common_analysis['total_combinations'])}개 조합)")
                    
                    print("=" * 60)
                else:
                    print(" 높은 확률 조합을 생성할 수 없습니다.")
            
            elif sub_choice == '4':
                analyzer.pattern_grouping.print_analysis_report()
            
            elif sub_choice == '5':
                print(" 메인 메뉴로 돌아갑니다.")
                break
            else:
                print(" 잘못된 선택입니다.")
                
    except Exception as e:
        print(f" AI 패턴 학습 중 오류 발생: {e}")


def handle_line_pattern_menu(exclude_manager: ExcludeNumberManager, lotto_manager: LottoManager):
    """선 연결 패턴 분석 메뉴 처리"""
    try:
        analyzer = LottoAnalyzer()
        if not analyzer.line_analyzer:
            print(" 선 연결 패턴 분석을 초기화할 수 없습니다.")
            return
        
        while True:
            print("\n 선 연결 패턴 분석 메뉴")
            print("=" * 40)
            print("1. 패턴 분석")
            print("2. 패턴 시각화")
            print("3. 패턴 기반 추천")
            print("4. 뒤로가기")
            print("=" * 40)
            
            sub_choice = safe_input("선택 (1-4): ", input_type="str")
            
            if sub_choice == '1':
                recent_rounds = safe_input("분석할 최근 회차 수 (기본 20): ", "20", "int") or 20
                patterns = analyzer.line_analyzer.analyze_line_patterns(recent_rounds)
                if patterns:
                    print(" 선 연결 패턴 분석이 완료되었습니다.")
                else:
                    print(" 패턴 분석에 실패했습니다.")
            
            elif sub_choice == '2':
                round_num = safe_input("시각화할 회차 (기본: 최신): ", input_type="int")
                save_path = safe_input("저장 경로 (기본: 화면에 표시): ") or None
                
                analyzer.line_analyzer.visualize_pattern(round_num, save_path)
                print(" 패턴 시각화가 완료되었습니다.")
            
            elif sub_choice == '3':
                exclude_numbers = exclude_manager.get_exclude_numbers()
                num_recommendations = safe_input("추천 번호 개수 (기본 5): ", "5", "int") or 5
                
                # 패턴이 없으면 자동으로 분석 수행
                if not analyzer.line_analyzer.line_patterns:
                    print("[INFO] 패턴 분석이 필요합니다. 자동으로 분석을 수행합니다...")
                    recent_rounds = safe_input("분석할 최근 회차 수 (기본 20): ", "20", "int") or 20
                    patterns = analyzer.line_analyzer.analyze_line_patterns(recent_rounds)
                    if not patterns:
                        print(" 패턴 분석에 실패했습니다.")
                        continue
                
                recommendations = analyzer.line_analyzer.generate_recommendations(
                    exclude_numbers, num_recommendations
                )
                
                if recommendations:
                    print_recommendations(recommendations, "선 연결 패턴 기반 추천 번호")
                    
                    # 저장 여부 확인
                    save_choice = safe_input("\n추천번호를 저장하시겠습니까? (y/n): ", "n")
                    if save_choice and save_choice.lower() in ['y', 'yes', '예']:
                        save_recommendations_to_tickets(recommendations, lotto_manager)
                else:
                    print(" 패턴 기반 추천을 생성할 수 없습니다.")
            
            elif sub_choice == '4':
                print(" 메인 메뉴로 돌아갑니다.")
                break
            else:
                print(" 잘못된 선택입니다.")
                
    except Exception as e:
        print(f" 선 연결 패턴 분석 중 오류 발생: {e}")


def handle_pattern_recommendation(exclude_manager: ExcludeNumberManager, lotto_manager: LottoManager):
    """패턴 매칭 추천 처리"""
    try:
        params = get_recommendation_params(exclude_manager)
        
        def pattern_generator(exclude_numbers):
            return generate_random_recommendation(exclude_numbers, '패턴 매칭', (0.1, 0.9))
        
        recommendations = generate_recommendations_with_retry(
            params['exclude_numbers'], 
            params['num_recommendations'], 
            '패턴 매칭', 
            pattern_generator
        )
        
        process_recommendation_save(recommendations, lotto_manager, "패턴 매칭 추천 번호")
            
    except Exception as e:
        print(f" 패턴 매칭 추천 중 오류 발생: {e}")


def handle_ensemble_recommendation(exclude_manager: ExcludeNumberManager, lotto_manager: LottoManager):
    """앙상블 추천 처리"""
    try:
        analyzer = LottoAnalyzer()
        exclude_numbers = exclude_manager.get_exclude_numbers()
        num_recommendations = safe_input("추천 번호 개수 (기본 5): ", "5", "int") or 5
        
        # 여러 방법을 조합한 앙상블 추천
        all_recommendations = []
        
        # 통계 기반 추천
        if analyzer.statistical_analyzer:
            stat_recs = analyzer.statistical_analyzer.generate_recommendations(
                exclude_numbers, num_recommendations
            )
            all_recommendations.extend(stat_recs)
        
        # 랜덤 추천 추가
        for _ in range(num_recommendations):
            available_numbers = [n for n in range(1, MAX_LOTTO_NUMBER + 1) if n not in exclude_numbers]
            if len(available_numbers) >= NUM_LOTTO_NUMBERS_TO_PICK:
                numbers = sorted(random.sample(available_numbers, NUM_LOTTO_NUMBERS_TO_PICK))
                all_recommendations.append({
                    'numbers': numbers,
                    'score': random.uniform(0.1, 0.5),
                    'method': '앙상블 랜덤',
                    'consecutive_count': 0,
                    'sum': sum(numbers)
                })
        
        if all_recommendations:
            # 중복 제거 및 정렬
            unique_recommendations = []
            seen_combinations = set()
            
            for rec in all_recommendations:
                numbers_tuple = tuple(sorted(rec['numbers']))
                if numbers_tuple not in seen_combinations:
                    seen_combinations.add(numbers_tuple)
                    unique_recommendations.append(rec)
            
            unique_recommendations.sort(key=lambda x: x['score'], reverse=True)
            final_recommendations = unique_recommendations[:num_recommendations]
            
            print_recommendations(final_recommendations, "앙상블 추천 번호")
            
            # 저장 여부 확인
            save_choice = safe_input("\n추천번호를 저장하시겠습니까? (y/n): ", "n")
            if save_choice and save_choice.lower() in ['y', 'yes', '예']:
                save_recommendations_to_tickets(final_recommendations, lotto_manager)
        else:
            print(" 앙상블 추천을 생성할 수 없습니다.")
            
    except Exception as e:
        print(f" 앙상블 추천 중 오류 발생: {e}")


def handle_mersenne_recommendation(exclude_manager: ExcludeNumberManager, lotto_manager: LottoManager):
    """메르센 트위스터 추천 처리"""
    try:
        params = get_recommendation_params(exclude_manager)
        
        def mersenne_generator(exclude_numbers):
            import time
            random.seed(int(time.time() * 1000) % (2**32))
            return generate_random_recommendation(exclude_numbers, '메르센 트위스터', (0.3, 0.8))
        
        recommendations = generate_recommendations_with_retry(
            params['exclude_numbers'], 
            params['num_recommendations'], 
            '메르센 트위스터', 
            mersenne_generator
        )
        
        process_recommendation_save(recommendations, lotto_manager, "메르센 트위스터 추천 번호")
            
    except Exception as e:
        print(f" 메르센 트위스터 추천 중 오류 발생: {e}")


def handle_trend_recommendation(exclude_manager: ExcludeNumberManager, lotto_manager: LottoManager):
    """최근 추세 추천 처리"""
    try:
        analyzer = LottoAnalyzer()
        exclude_numbers = exclude_manager.get_exclude_numbers()
        num_recommendations = safe_input("추천 번호 개수 (기본 5): ", "5", "int") or 5
        
        # 최근 추세 기반 추천
        recommendations = []
        attempts = 0
        max_attempts = num_recommendations * 100
        
        # 최근 당첨번호 분석
        recent_numbers = []
        for row in analyzer.data[-5:]:  # 최근 5회
            numbers = extract_numbers_from_data(row)
            if validate_numbers(numbers):
                recent_numbers.extend(numbers)
        
        while len(recommendations) < num_recommendations and attempts < max_attempts:
            attempts += 1
            
            # 추세를 고려한 번호 생성
            available_numbers = [n for n in range(1, MAX_LOTTO_NUMBER + 1) if n not in exclude_numbers]
            if len(available_numbers) < NUM_LOTTO_NUMBERS_TO_PICK:
                break
            
            # 최근에 나온 번호들은 가중치를 낮춤
            weights = []
            for num in available_numbers:
                if num in recent_numbers:
                    weights.append(0.5)  # 최근 번호는 가중치 낮춤
                else:
                    weights.append(1.0)
            
            try:
                if sum(weights) > 0:
                    numbers = random.choices(available_numbers, weights=weights, k=NUM_LOTTO_NUMBERS_TO_PICK)
                    numbers = sorted(list(set(numbers)))
                    if len(numbers) == NUM_LOTTO_NUMBERS_TO_PICK:
                        # 중복 검사
                        numbers_tuple = tuple(numbers)
                        if any(tuple(sorted(rec['numbers'])) == numbers_tuple for rec in recommendations):
                            continue
                        
                        # 점수 계산
                        score = random.uniform(0.4, 0.9)
                        
                        recommendation = {
                            'numbers': numbers,
                            'score': score,
                            'method': '최근 추세',
                            'consecutive_count': 0,
                            'sum': sum(numbers)
                        }
                        
                        recommendations.append(recommendation)
                else:
                    numbers = sorted(random.sample(available_numbers, NUM_LOTTO_NUMBERS_TO_PICK))
                    # 중복 검사 및 추가 로직...
            except (ValueError, IndexError):
                continue
        
        if recommendations:
            print_recommendations(recommendations, "최근 추세 추천 번호")
            
            # 저장 여부 확인
            save_choice = safe_input("\n추천번호를 저장하시겠습니까? (y/n): ", "n")
            if save_choice and save_choice.lower() in ['y', 'yes', '예']:
                save_recommendations_to_tickets(recommendations, lotto_manager)
        else:
            print(" 최근 추세 추천을 생성할 수 없습니다.")
            
    except Exception as e:
        print(f" 최근 추세 추천 중 오류 발생: {e}")


if __name__ == "__main__":
    main() 