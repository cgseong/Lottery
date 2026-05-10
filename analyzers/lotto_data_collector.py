"""로또 데이터 수집 모듈"""

import csv
import time
import os
import requests
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

    def _fetch_round_json(self, round_num, retries: int = 2):
        """JSON API에서 특정 회차 번호를 조회합니다. 실패 시 retries만큼 재시도합니다."""
        url = self.api_url_template.format(int(round_num))
        for attempt in range(retries + 1):
            try:
                response = requests.get(url, headers=self.headers, timeout=3)
                response.raise_for_status()
                payload = response.json()
                if payload.get("returnValue") == "success":
                    return payload
                return None
            except Exception:
                if attempt < retries:
                    time.sleep(0.5 * (attempt + 1))
        return None

    def get_latest_round(self):
        """최신 회차 정보를 가져옵니다."""
        # API 우선: HTML 타임아웃 환경에서도 빠르게 동작
        latest_round = self._find_latest_round_via_api()
        if latest_round:
            return latest_round

        latest_round = None
        response = None
        try:
            response = requests.get(self.search_url, headers=self.headers, timeout=3)
            response.raise_for_status()
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
            if not latest_round and response is not None:
                matches = re.findall(r'drwNo=(\d+)', response.text or "")
                if matches:
                    latest_round = max(int(x) for x in matches)
        except Exception as e:
            _log.warning("최신 회차 HTML 조회 실패, API fallback 사용: %s", e)

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

    def collect_winning_numbers(self, start_round=None, end_round=None, max_rounds=100):
        """지정된 범위의 당첨번호를 수집합니다."""
        print(" 동행복권 사이트에서 당첨번호 수집 중...")

        # 최신 회차 확인
        latest_round = self.get_latest_round()
        if not latest_round:
            print(" 최신 회차 정보를 가져올 수 없습니다.")
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

        for round_num in range(start_round, end_round + 1):
            try:
                print(f"    {round_num}회 수집 중...", end=" ")

                # JSON API 우선 (빠르고 안정적), HTML은 폴백
                payload = self._fetch_round_json(round_num)
                numbers = self._extract_numbers_from_json(payload, round_num)

                if not numbers:
                    round_url = self.round_url_template.format(round_num)
                    response = requests.get(round_url, headers=self.headers, timeout=10)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.content, 'html.parser')
                    numbers = self._extract_numbers(soup, round_num)

                if numbers:
                    collected_data.append(numbers)
                    print("")
                else:
                    failed_rounds.append(round_num)
                    print("")

                time.sleep(0.3)

            except Exception as e:
                failed_rounds.append(round_num)
                _log.warning("%d회 수집 오류: %s", round_num, e)
                print(f"(오류)")
                time.sleep(1)

        print(f"\n 수집 완료: {len(collected_data)}개 성공, {len(failed_rounds)}개 실패")

        if failed_rounds:
            print(f" 실패한 회차: {failed_rounds}")

        return collected_data

    def _extract_numbers(self, soup, round_num):
        """HTML에서 당첨번호를 추출합니다."""
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
                            return {
                                '회차': round_num,
                                '번호1': numbers[0],
                                '번호2': numbers[1],
                                '번호3': numbers[2],
                                '번호4': numbers[3],
                                '번호5': numbers[4],
                                '번호6': numbers[5],
                                '보너스번호': bonus_number
                            }

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
                return {
                    '회차': round_num,
                    '번호1': numbers[0],
                    '번호2': numbers[1],
                    '번호3': numbers[2],
                    '번호4': numbers[3],
                    '번호5': numbers[4],
                    '번호6': numbers[5],
                    '보너스번호': bonus_number
                }

            return None

        except Exception as e:
            _log.debug("번호 추출 오류: %s", e)
            return None

    def _extract_numbers_from_json(self, payload, round_num):
        """JSON payload에서 당첨번호와 부가정보(날짜·당첨자수·당첨금)를 추출합니다."""
        try:
            if not payload or payload.get("returnValue") != "success":
                return None
            record = {
                '회차': int(payload.get('drwNo', round_num)),
                '날짜': payload.get('drwNoDate', ''),
                '번호1': int(payload.get('drwtNo1')),
                '번호2': int(payload.get('drwtNo2')),
                '번호3': int(payload.get('drwtNo3')),
                '번호4': int(payload.get('drwtNo4')),
                '번호5': int(payload.get('drwtNo5')),
                '번호6': int(payload.get('drwtNo6')),
                '보너스번호': int(payload.get('bnusNo')),
                '1등당첨자수': int(payload.get('firstPrzwnerCo', 0)),
                '1등당첨금액': int(payload.get('firstWinamnt', 0)),
            }
            return record
        except Exception:
            return None

    def save_to_csv(self, data, filename='로또당첨번호.csv'):
        """수집된 데이터를 CSV 파일로 저장합니다."""
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
                                if any('회차' in str(k) for k in keys):
                                    existing_data = temp_data
                                    break
                    except Exception:
                        continue

            # 중복 제거 및 병합
            existing_rounds = set()
            valid_existing_data = []
            
            for row in existing_data:
                try:
                    if '회차' in row:
                        existing_rounds.add(int(row['회차']))
                        valid_existing_data.append(row)
                except (ValueError, KeyError):
                    continue
            
            new_data = [row for row in data if int(row['회차']) not in existing_rounds]

            if not new_data:
                print(" 모든 데이터가 이미 존재합니다.")
                return True

            # 새 데이터 추가
            all_data = valid_existing_data + new_data

            # 회차 순으로 정렬
            all_data.sort(key=lambda x: int(x['회차']))

            # CSV 파일로 저장 — 새 데이터에 확장 컬럼이 있으면 포함
            base_fields = ['회차', '날짜', '번호1', '번호2', '번호3', '번호4', '번호5', '번호6', '보너스번호', '1등당첨자수', '1등당첨금액']
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

        except Exception as e:
            _log.error("CSV 파일 저장 실패: %s", e)
            print(f" CSV 파일 저장 실패: {e}")
            return False

    def update_latest_data(self, max_rounds=10):
        """최신 회차 데이터만 업데이트합니다."""
        print(" 최신 당첨번호 업데이트 중...")

        # 기존 데이터 확인
        existing_rounds = set()
        if os.path.exists('로또당첨번호.csv'):
            encodings = ['utf-8', 'cp949', 'euc-kr']
            for enc in encodings:
                try:
                    with open('로또당첨번호.csv', 'r', encoding=enc) as file:
                        reader = csv.DictReader(file)
                        for row in reader:
                            if '회차' in row:
                                try:
                                    existing_rounds.add(int(row['회차']))
                                except ValueError:
                                    continue
                        
                        if existing_rounds:
                            break
                except Exception:
                    continue
        
        if not existing_rounds:
            print(" 기존 데이터가 없거나 읽을 수 없습니다. 전체 데이터를 수집합니다.")
            data = self.collect_winning_numbers(start_round=1)
            if data:
                self.save_to_csv(data)
            return data

        latest_existing = max(existing_rounds)
        latest_available = self.get_latest_round()

        if not latest_available:
            print(" 최신 회차 정보를 가져올 수 없습니다.")
            return []

        if latest_existing >= latest_available:
            print(" 이미 최신 데이터가 있습니다.")
            return []

        print(f" {latest_existing + 1}회 ~ {latest_available}회 업데이트")

        new_data = self.collect_winning_numbers(
            start_round=latest_existing + 1,
            end_round=latest_available
        )

        if new_data:
            self.save_to_csv(new_data)

        return new_data
