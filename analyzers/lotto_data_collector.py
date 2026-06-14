"""로또 데이터 수집 모듈"""

import csv
import time
import os
import requests
from requests.exceptions import ConnectionError, Timeout, HTTPError
from bs4 import BeautifulSoup
import re

try:
    from utils.logging_config import get_logger
    _log = get_logger(__name__)
except ImportError:
    import logging
    _log = logging.getLogger(__name__)

try:
    from utils.constants import DEFAULT_HEADERS as _DEFAULT_HEADERS
except ImportError:
    _DEFAULT_HEADERS = None

# 네트워크 설정 상수
_DEFAULT_TIMEOUT = 10          # 기본 요청 타임아웃 (초)
_API_TIMEOUT = 5               # API 요청 타임아웃 (초)
_MAX_CONSECUTIVE_FAILURES = 5  # 연속 실패 허용 횟수 (초과 시 수집 중단)
_RETRY_DELAY_BASE = 0.5        # 재시도 기본 대기 시간 (초)
_REQUEST_DELAY = 0.3           # 요청 간 대기 시간 (초)


class DataCollectionError(Exception):
    """데이터 수집 관련 커스텀 예외"""
    pass


class NetworkError(DataCollectionError):
    """네트워크 연결 실패"""
    pass


class ParseError(DataCollectionError):
    """페이지 파싱 실패 (사이트 구조 변경 가능성)"""
    pass


class LottoDataCollector:
    """동행복권 사이트에서 로또 당첨번호를 수집하는 클래스"""

    def __init__(self):
        self.base_url = "https://dhlottery.co.kr"
        self.search_url = "https://dhlottery.co.kr/gameResult.do?method=byWin"
        self.round_url_template = "https://dhlottery.co.kr/gameResult.do?method=byWin&drwNo={}"
        self.api_url_template = "https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={}"
        # constants.DEFAULT_HEADERS 공유 — 중복 정의 방지
        self.headers = dict(_DEFAULT_HEADERS) if _DEFAULT_HEADERS else {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

    # ------------------------------------------------------------------
    # 네트워크 요청 헬퍼
    # ------------------------------------------------------------------

    def _request_get(self, url: str, timeout: int = _DEFAULT_TIMEOUT) -> requests.Response:
        """공통 GET 요청 — 네트워크 오류를 NetworkError로 통합 변환합니다."""
        try:
            response = requests.get(url, headers=self.headers, timeout=timeout)
            response.raise_for_status()
            return response
        except Timeout as e:
            raise NetworkError(
                f"요청 시간 초과 ({timeout}초). 인터넷 연결 상태를 확인해주세요."
            ) from e
        except ConnectionError as e:
            raise NetworkError(
                "서버에 연결할 수 없습니다. 인터넷 연결 또는 동행복권 사이트 상태를 확인해주세요."
            ) from e
        except HTTPError as e:
            status = e.response.status_code if e.response is not None else "unknown"
            if status == 403:
                raise NetworkError(
                    "접근이 차단되었습니다 (403). 잠시 후 다시 시도해주세요."
                ) from e
            elif status == 404:
                raise NetworkError(
                    f"페이지를 찾을 수 없습니다 (404). URL: {url}"
                ) from e
            elif status >= 500:
                raise NetworkError(
                    f"동행복권 서버 오류 ({status}). 잠시 후 다시 시도해주세요."
                ) from e
            else:
                raise NetworkError(
                    f"HTTP 오류 발생 ({status}). URL: {url}"
                ) from e

    def _fetch_round_json(self, round_num, retries: int = 2):
        """JSON API에서 특정 회차 번호를 조회합니다. 실패 시 retries만큼 재시도합니다."""
        url = self.api_url_template.format(int(round_num))
        last_error = None
        for attempt in range(retries + 1):
            try:
                response = self._request_get(url, timeout=_API_TIMEOUT)
                payload = response.json()
                if payload.get("returnValue") == "success":
                    return payload
                return None
            except NetworkError as e:
                last_error = e
                if attempt < retries:
                    time.sleep(_RETRY_DELAY_BASE * (attempt + 1))
            except (ValueError, KeyError) as e:
                # JSON 파싱 실패
                _log.debug("JSON 파싱 실패 (회차 %d): %s", round_num, e)
                return None

        if last_error:
            _log.debug("API 조회 최종 실패 (회차 %d): %s", round_num, last_error)
        return None

    # ------------------------------------------------------------------
    # 최신 회차 조회
    # ------------------------------------------------------------------

    def get_latest_round(self):
        """최신 회차 정보를 가져옵니다.

        Returns:
            int: 최신 회차 번호, 실패 시 None
        """
        # API 우선: HTML 타임아웃 환경에서도 빠르게 동작
        latest_round = self._find_latest_round_via_api()
        if latest_round:
            return latest_round

        latest_round = None
        try:
            response = self._request_get(self.search_url)
            soup = BeautifulSoup(response.content, 'html.parser')

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
                    match = re.search(r'(\d+)회', title_text)
                    if match:
                        latest_round = int(match.group(1))

            # 방법 4: 페이지 내 drwNo 파라미터에서 추출
            if not latest_round:
                matches = re.findall(r'drwNo=(\d+)', response.text or "")
                if matches:
                    latest_round = max(int(x) for x in matches)

        except NetworkError as e:
            _log.warning("최신 회차 HTML 조회 실패: %s", e)
            print(f"\n[WARN] {e}")
        except (ValueError, AttributeError) as e:
            _log.warning("최신 회차 HTML 파싱 실패 (사이트 구조 변경 가능): %s", e)
            print("\n[WARN] 동행복권 사이트 구조가 변경되었을 수 있습니다. API로 시도합니다.")

        # 방법 5: JSON API fallback (HTML 실패/파싱 실패 포함)
        if not latest_round:
            latest_round = self._find_latest_round_via_api()

        return latest_round

    def _find_latest_round_via_api(self):
        """API 기반으로 최신 회차를 빠르게 찾습니다."""
        # 현재 연도(2025 기준) 최신 회차는 1100 이상 — 비현실적인 결과(lo=1) 차단
        _MIN_PLAUSIBLE_ROUND = 1000
        lo, hi = 1, 2048
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if self._fetch_round_json(mid):
                lo = mid
            else:
                hi = mid - 1
        # API 전체 다운 시 lo=1 오반환 방지: 실제 유효 여부 + 최솟값 검증
        if lo < _MIN_PLAUSIBLE_ROUND:
            _log.warning("이진탐색 결과(%d)가 현실적 최솟값(%d) 미만 — API 다운으로 판단", lo, _MIN_PLAUSIBLE_ROUND)
            return None
        return lo if self._fetch_round_json(lo) else None

    # ------------------------------------------------------------------
    # 데이터 수집
    # ------------------------------------------------------------------

    def collect_winning_numbers(self, start_round=None, end_round=None, max_rounds=100):
        """지정된 범위의 당첨번호를 수집합니다.

        연속 실패가 _MAX_CONSECUTIVE_FAILURES를 초과하면 수집을 조기 중단합니다.

        Returns:
            list[dict]: 수집된 당첨번호 목록
        """
        print(" 동행복권 사이트에서 당첨번호 수집 중...")

        # 최신 회차 확인
        try:
            latest_round = self.get_latest_round()
        except Exception as e:
            print(f"\n[ERROR] 최신 회차 조회 실패: {e}")
            print("  → 인터넷 연결 상태를 확인해주세요.")
            return []

        if not latest_round:
            print("\n[ERROR] 최신 회차 정보를 가져올 수 없습니다.")
            print("  → 동행복권 사이트(dhlottery.co.kr) 접속 가능 여부를 확인해주세요.")
            print("  → VPN 또는 방화벽이 차단하고 있을 수 있습니다.")
            return []

        _log.info("최신 회차: %d회", latest_round)

        # 수집 범위 설정
        if end_round is None:
            end_round = latest_round

        if start_round is None:
            start_round = max(1, end_round - max_rounds + 1)

        print(f" 수집 범위: {start_round}회 ~ {end_round}회")

        collected_data = []
        failed_rounds = []
        consecutive_failures = 0

        for round_num in range(start_round, end_round + 1):
            # 연속 실패 체크 — 네트워크 장애 시 조기 중단
            if consecutive_failures >= _MAX_CONSECUTIVE_FAILURES:
                print(f"\n[WARN] 연속 {_MAX_CONSECUTIVE_FAILURES}회 실패로 수집을 중단합니다.")
                print("  → 네트워크 상태를 확인하고 나중에 다시 시도해주세요.")
                remaining = list(range(round_num, end_round + 1))
                failed_rounds.extend(remaining)
                break

            try:
                print(f"    {round_num}회 수집 중...", end=" ")

                # JSON API 우선 (빠르고 안정적), HTML은 폴백
                payload = self._fetch_round_json(round_num)
                numbers = self._extract_numbers_from_json(payload, round_num)

                if not numbers:
                    try:
                        round_url = self.round_url_template.format(round_num)
                        response = self._request_get(round_url)
                        soup = BeautifulSoup(response.content, 'html.parser')
                        numbers = self._extract_numbers(soup, round_num)
                    except NetworkError as e:
                        _log.warning("%d회 HTML 폴백 실패: %s", round_num, e)
                        numbers = None

                if numbers:
                    collected_data.append(numbers)
                    consecutive_failures = 0  # 성공 시 연속 실패 카운터 초기화
                    print("")
                else:
                    failed_rounds.append(round_num)
                    consecutive_failures += 1
                    print("(파싱 실패)")

                time.sleep(_REQUEST_DELAY)

            except NetworkError as e:
                failed_rounds.append(round_num)
                consecutive_failures += 1
                _log.warning("%d회 네트워크 오류: %s", round_num, e)
                print(f"(네트워크 오류)")
                time.sleep(_RETRY_DELAY_BASE * 2)

            except Exception as e:
                failed_rounds.append(round_num)
                consecutive_failures += 1
                _log.error("%d회 예상치 못한 오류: %s", round_num, e)
                print(f"(오류: {type(e).__name__})")
                time.sleep(_RETRY_DELAY_BASE * 2)

        # 결과 요약
        print(f"\n 수집 완료: {len(collected_data)}개 성공, {len(failed_rounds)}개 실패")

        if failed_rounds:
            if len(failed_rounds) <= 10:
                print(f" 실패한 회차: {failed_rounds}")
            else:
                print(f" 실패한 회차: {failed_rounds[:10]} ... 외 {len(failed_rounds)-10}개")

            # 실패 원인 안내
            if consecutive_failures >= _MAX_CONSECUTIVE_FAILURES:
                print("\n[TIP] 네트워크 문제로 중단되었습니다. 나중에 메뉴 7번을 다시 실행하면")
                print("      누락된 회차만 자동으로 보충됩니다.")

        return collected_data

    # ------------------------------------------------------------------
    # HTML 파싱
    # ------------------------------------------------------------------

    def _extract_numbers(self, soup, round_num):
        """HTML에서 당첨번호를 추출합니다.

        Returns:
            dict: 당첨번호 딕셔너리, 파싱 실패 시 None
        """
        try:
            numbers = []
            bonus_number = None

            # 방법 1: win_result 영역에서 찾기
            win_result = soup.find('div', class_='win_result')
            if win_result:
                number_elements = win_result.find_all('span', class_='ball_645')
                if len(number_elements) >= 7:
                    for i, element in enumerate(number_elements[:6]):
                        numbers.append(int(element.get_text().strip()))
                    bonus_number = int(number_elements[6].get_text().strip())

                    h4_element = win_result.find('h4')
                    if h4_element:
                        round_text = h4_element.get_text().strip()
                        if str(round_num) in round_text:
                            return self._build_record(round_num, numbers, bonus_number)

            # 방법 2: 테이블에서 찾기
            if not numbers:
                table = soup.find('table', class_='t_auto')
                if table:
                    rows = table.find_all('tr')
                    for row in rows:
                        cells = row.find_all('td')
                        if len(cells) >= 8:
                            try:
                                row_round = int(cells[0].get_text().strip())
                                if row_round == round_num:
                                    for i in range(1, 7):
                                        numbers.append(int(cells[i].get_text().strip()))
                                    bonus_number = int(cells[7].get_text().strip())
                                    break
                            except (ValueError, IndexError):
                                continue

            # 방법 3: 다른 클래스명으로 찾기
            if not numbers:
                class_names = ['ball_645', 'ball', 'num', 'number']
                for class_name in class_names:
                    number_elements = soup.find_all('span', class_=class_name)
                    if len(number_elements) >= 7:
                        for i, element in enumerate(number_elements[:6]):
                            try:
                                numbers.append(int(element.get_text().strip()))
                            except ValueError:
                                continue
                        try:
                            bonus_number = int(number_elements[6].get_text().strip())
                        except (ValueError, IndexError):
                            continue
                        break

            # 결과 반환
            if len(numbers) == 6 and bonus_number is not None:
                # 번호 유효성 검증
                if all(1 <= n <= 45 for n in numbers) and 1 <= bonus_number <= 45:
                    return self._build_record(round_num, numbers, bonus_number)
                else:
                    _log.warning("%d회: 유효하지 않은 번호 감지 %s + %d", round_num, numbers, bonus_number)
                    return None

            _log.debug("%d회: HTML에서 번호 추출 실패 (사이트 구조 변경 가능)", round_num)
            return None

        except (ValueError, AttributeError, TypeError) as e:
            _log.debug("%d회 번호 추출 오류: %s", round_num, e)
            return None

    def _extract_numbers_from_json(self, payload, round_num):
        """JSON payload에서 당첨번호와 부가정보(날짜·당첨자수·당첨금)를 추출합니다."""
        try:
            if not payload or payload.get("returnValue") != "success":
                return None

            numbers = [
                int(payload.get(f'drwtNo{i}'))
                for i in range(1, 7)
            ]
            bonus = int(payload.get('bnusNo'))

            # 번호 유효성 검증
            if not all(1 <= n <= 45 for n in numbers) or not (1 <= bonus <= 45):
                _log.warning("%d회 API: 유효하지 않은 번호 %s + %d", round_num, numbers, bonus)
                return None

            record = {
                'round': int(payload.get('drwNo', round_num)),
                'date': payload.get('drwNoDate', ''),
                'num1': numbers[0],
                'num2': numbers[1],
                'num3': numbers[2],
                'num4': numbers[3],
                'num5': numbers[4],
                'num6': numbers[5],
                'bonus': bonus,
                'winners': int(payload.get('firstPrzwnerCo', 0)),
                'prize': int(payload.get('firstWinamnt', 0)),
            }
            return record
        except (TypeError, ValueError, KeyError) as e:
            _log.debug("%d회 JSON 파싱 오류: %s", round_num, e)
            return None

    @staticmethod
    def _build_record(round_num, numbers, bonus_number):
        """번호 리스트로부터 표준 레코드 딕셔너리를 생성합니다."""
        return {
            'round': round_num,
            'num1': numbers[0],
            'num2': numbers[1],
            'num3': numbers[2],
            'num4': numbers[3],
            'num5': numbers[4],
            'num6': numbers[5],
            'bonus': bonus_number,
        }

    # ------------------------------------------------------------------
    # CSV 저장
    # ------------------------------------------------------------------

    def save_to_csv(self, data, filename='lotto_results.csv'):
        """수집된 데이터를 CSV 파일로 저장합니다.

        Returns:
            bool: 저장 성공 여부
        """
        if not data:
            print(" 저장할 데이터가 없습니다.")
            return False

        try:
            # 기존 파일이 있는지 확인
            existing_data = []
            if os.path.exists(filename):
                encodings = ['utf-8', 'cp949', 'euc-kr']
                for enc in encodings:
                    try:
                        with open(filename, 'r', encoding=enc) as file:
                            reader = csv.DictReader(file)
                            temp_data = list(reader)
                            if temp_data:
                                keys = list(temp_data[0].keys())
                                if any('num1' in str(k) or 'round' in str(k) for k in keys):
                                    existing_data = temp_data
                                    break
                    except (UnicodeDecodeError, csv.Error):
                        continue
                    except OSError as e:
                        _log.warning("기존 CSV 읽기 실패: %s", e)
                        break

            # 중복 제거 및 병합
            existing_rounds = set()
            valid_existing_data = []

            for row in existing_data:
                try:
                    if 'round' in row:
                        existing_rounds.add(int(row['round']))
                        valid_existing_data.append(row)
                except (ValueError, KeyError):
                    continue

            new_data = [row for row in data if int(row['round']) not in existing_rounds]

            if not new_data:
                print(" 모든 데이터가 이미 존재합니다.")
                return True

            # 새 데이터 추가
            all_data = valid_existing_data + new_data

            # 회차 순으로 정렬
            all_data.sort(key=lambda x: int(x['round']))

            # CSV 파일로 저장 — 새 데이터에 확장 컬럼이 있으면 포함
            base_fields = ['round', 'date', 'num1', 'num2', 'num3', 'num4', 'num5', 'num6', 'bonus', 'winners', 'prize']
            # 기존 데이터에 없는 컬럼은 빈 값으로 채움
            for row in all_data:
                for field in base_fields:
                    row.setdefault(field, '')

            with open(filename, 'w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=base_fields, extrasaction='ignore')
                writer.writeheader()
                writer.writerows(all_data)

            print(f" {len(new_data)}개 회차 데이터가 {filename}에 저장되었습니다.")
            _log.info("총 %d개 회차 데이터가 있습니다.", len(all_data))
            return True

        except OSError as e:
            print(f"\n[ERROR] 파일 저장 실패: {e}")
            if "No space" in str(e) or "ENOSPC" in str(e):
                print("  → 디스크 공간이 부족합니다. 공간을 확보 후 다시 시도해주세요.")
            else:
                print(f"  → 파일 쓰기 권한 또는 경로를 확인해주세요: {filename}")
            return False
        except Exception as e:
            _log.error("CSV 파일 저장 중 예상치 못한 오류: %s", e)
            print(f"\n[ERROR] CSV 파일 저장 실패: {e}")
            return False

    # ------------------------------------------------------------------
    # 업데이트
    # ------------------------------------------------------------------

    def update_latest_data(self, max_rounds=10):
        """최신 회차 데이터만 업데이트합니다.

        Returns:
            list[dict]: 새로 수집된 데이터 목록
        """
        print(" 최신 당첨번호 업데이트 중...")

        # 기존 데이터 확인
        existing_rounds = set()
        if os.path.exists('lotto_results.csv'):
            encodings = ['utf-8', 'cp949', 'euc-kr']
            for enc in encodings:
                try:
                    with open('lotto_results.csv', 'r', encoding=enc) as file:
                        reader = csv.DictReader(file)
                        for row in reader:
                            if 'round' in row:
                                try:
                                    existing_rounds.add(int(row['round']))
                                except ValueError:
                                    continue

                        if existing_rounds:
                            break
                except (UnicodeDecodeError, csv.Error):
                    continue
                except OSError as e:
                    _log.warning("기존 CSV 읽기 실패: %s", e)
                    break

        if not existing_rounds:
            print(" 기존 데이터가 없거나 읽을 수 없습니다. 전체 데이터를 수집합니다.")
            data = self.collect_winning_numbers(start_round=1)
            if data:
                self.save_to_csv(data)
            return data

        latest_existing = max(existing_rounds)
        latest_available = self.get_latest_round()

        if not latest_available:
            print("\n[WARN] 최신 회차 정보를 가져올 수 없습니다.")
            print("  → 인터넷 연결 상태를 확인해주세요.")
            return []

        if latest_existing >= latest_available:
            print(f" 이미 최신 데이터가 있습니다. (현재: {latest_existing}회)")
            return []

        gap = latest_available - latest_existing
        print(f" {latest_existing + 1}회 ~ {latest_available}회 업데이트 ({gap}회차)")

        new_data = self.collect_winning_numbers(
            start_round=latest_existing + 1,
            end_round=latest_available
        )

        if new_data:
            self.save_to_csv(new_data)

        return new_data
