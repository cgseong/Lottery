# 로또 분석 프로그램 리팩토링 가이드

## 📋 문제점

**lotto_analyzer_fixed.py** 파일이 약 260KB (4,700줄)로 매우 크고 관리가 어렵습니다.

### 문제점 요약
- ✗ 파일 크기 260KB - Git에서 diff 확인 어려움
- ✗ 4,700줄 - 코드 탐색 및 유지보수 어려움
- ✗ 11개 클래스가 한 파일에 혼재
- ✗ 코드 재사용성 낮음
- ✗ 테스트 작성 어려움

## ✅ 해결 방법

### 1단계: 모듈화 구조 (완료 ✓)

```
Lottery/
├── analyzers/              # 분석기 모듈들
│   ├── __init__.py
│   ├── exclude_number_manager.py      ✓ 새로 생성
│   ├── lotto_data_collector.py        ✓ 새로 생성
│   ├── statistical_analyzer.py        ✓ 기존
│   ├── pattern_matching_analyzer.py   ✓ 기존
│   ├── ensemble_analyzer.py           ✓ 기존
│   ├── mersenne_twister_analyzer.py   ✓ 기존
│   ├── trend_analyzer.py              ✓ 기존
│   ├── sum_pattern_analyzer.py        □ 필요
│   ├── lotto_pattern_grouping.py      ✓ 기존
│   └── line_pattern_analyzer.py       ✓ 기존
│
├── utils/                  # 유틸리티 함수들
│   ├── __init__.py
│   ├── constants.py                   ✓ 기존
│   ├── helpers.py                     ✓ 기존
│   ├── system_utils.py                ✓ 새로 생성
│   └── file_utils.py                  ✓ 새로 생성
│
├── lotto_analyzer_fixed.py    # 메인 파일 (리팩토링 필요)
└── lotto_analyzer.py          # 새 메인 파일 (생성 필요)
```

### 2단계: 메인 파일 간소화 (TODO)

**기존 lotto_analyzer_fixed.py** (4,700줄)를 다음과 같이 축소:

```python
# lotto_analyzer.py (새로 생성)

import os
from utils.constants import *
from utils.file_utils import resolve_data_file
from utils.system_utils import check_installation_status, show_system_info
from analyzers.exclude_number_manager import ExcludeNumberManager
from analyzers.lotto_data_collector import LottoDataCollector
from lotto_manager import LottoManager

# 전역 설정
DATA_FILE_PATH = resolve_data_file()
DEFAULT_RECENT_COUNT = 51
DEFAULT_MAX_CONSECUTIVE = 3
DEFAULT_MAX_RECENT_OVERLAP = 4

def main():
    """메인 함수"""
    # 패키지 상태 확인
    check_installation_status()

    # 시스템 정보 표시
    show_system_info()

    # LottoManager 초기화
    manager = LottoManager()
    manager.run()

if __name__ == "__main__":
    main()
```

예상 결과: **150줄 이하**

### 3단계: LottoAnalyzer 클래스 분리 (TODO)

**lotto_analyzer_fixed.py**의 `LottoAnalyzer` 클래스(690~1614줄)를
`analyzers/lotto_analyzer.py`로 분리

### 4단계: SumPatternAnalyzer 분리 (TODO)

**lotto_analyzer_fixed.py**의 `SumPatternAnalyzer` 클래스(2895~3160줄)를
`analyzers/sum_pattern_analyzer.py`로 분리

## 📊 기대 효과

| 항목 | 변경 전 | 변경 후 |
|------|---------|---------|
| 메인 파일 크기 | 260KB | ~10KB |
| 메인 파일 줄 수 | 4,700줄 | ~150줄 |
| 클래스 파일 분리 | 1개 | 11개 |
| 코드 재사용성 | 낮음 | 높음 |
| 유지보수성 | 어려움 | 쉬움 |
| 테스트 작성 | 어려움 | 쉬움 |

## 🔧 다음 단계

### 즉시 실행 가능한 작업

1. **analyzers/__init__.py 업데이트**
   ```python
   from .exclude_number_manager import ExcludeNumberManager
   from .lotto_data_collector import LottoDataCollector
   from .sum_pattern_analyzer import SumPatternAnalyzer  # TODO
   from .lotto_analyzer import LottoAnalyzer  # TODO
   # ... 기존 import들
   ```

2. **SumPatternAnalyzer 분리**
   - lotto_analyzer_fixed.py에서 2895~3160줄 추출
   - analyzers/sum_pattern_analyzer.py 생성
   - 필요한 import 추가

3. **LottoAnalyzer 분리**
   - lotto_analyzer_fixed.py에서 690~1614줄 추출
   - analyzers/lotto_analyzer.py 생성
   - 필요한 import 추가

4. **새 메인 파일 생성**
   - lotto_analyzer.py 생성 (간소화된 버전)
   - 기존 lotto_analyzer_fixed.py는 백업으로 유지

5. **테스트**
   ```bash
   python lotto_analyzer.py
   ```

## ⚠️ 주의사항

- **lotto_analyzer_fixed.py는 삭제하지 말 것** (백업으로 유지)
- 각 분리 작업 후 기능 테스트 필수
- import 경로 충돌 주의
- 순환 import 방지

## 📝 추가 개선 사항

### 성능 최적화
- Lazy loading: 필요할 때만 모듈 import
- 캐싱: 반복 계산 결과 저장
- 병렬 처리: 다중 분석기 동시 실행

### 코드 품질
- Type hints 추가
- Docstring 표준화
- Linter 적용 (pylint, flake8)
- 단위 테스트 작성

### 사용성
- CLI 인터페이스 개선
- 설정 파일 지원 (config.yaml)
- 로깅 시스템 개선
- 에러 핸들링 강화

## 🎯 완료 체크리스트

- [x] analyzers/exclude_number_manager.py 생성
- [x] analyzers/lotto_data_collector.py 생성
- [x] utils/system_utils.py 생성
- [x] utils/file_utils.py 생성
- [ ] analyzers/sum_pattern_analyzer.py 생성
- [ ] analyzers/lotto_analyzer.py 생성
- [ ] lotto_analyzer.py (새 메인) 생성
- [ ] analyzers/__init__.py 업데이트
- [ ] 통합 테스트
- [ ] 문서 업데이트

## 💡 팁

### 빠른 클래스 추출 방법

```bash
# 특정 클래스만 추출 (예: SumPatternAnalyzer)
sed -n '2895,3160p' lotto_analyzer_fixed.py > temp_class.py

# 필요한 import 확인
grep -n "^import\|^from" temp_class.py
```

### Import 경로 일괄 변경

```python
# 기존
from lotto_analyzer_fixed import ExcludeNumberManager

# 변경
from analyzers.exclude_number_manager import ExcludeNumberManager
```

## 📚 참고 자료

- [Python 모듈화 베스트 프랙티스](https://docs.python.org/3/tutorial/modules.html)
- [프로젝트 구조 가이드](https://docs.python-guide.org/writing/structure/)
- [리팩토링 원칙](https://refactoring.guru/refactoring)
