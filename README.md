# 로또 번호 추천 시스템

통계 분석, 10개 지표 종합 평가, AI 패턴 학습을 결합한 로또 번호 추천 CLI 도구입니다.

## 기능 요약

| 메뉴 | 기능 |
|------|------|
| 1 | 당첨번호 분석 — 빈도·합계·홀짝·구간·연속 통계 |
| 2 | 통계 기반 번호 추천 |
| 3 | 제외번호 관리 |
| 4 | 고급 추천 (제외/고정 번호 지정) |
| 5 | 저장된 조합 관리 및 품질 검토 |
| 6 | AI + 미출현 패턴 기반 고유 추천 |
| 7 | 동행복권 최신 데이터 자동 수집 |
| 8 | 10개 지표 종합 패턴 분석 추천 |

## 설치 및 실행

```bash
# 의존성 설치
pip install -r requirements.txt

# 실행
python main.py

# 대시보드 (선택)
streamlit run dashboard_app.py
```

## 프로젝트 구조

```
Lottery/
├── main.py                  # 진입점 (메뉴 시스템)
├── ai_pattern_learner.py    # ML 기반 번호 확률 예측
├── number_storage.py        # 번호 조합 저장/관리
├── dashboard_app.py         # Streamlit 대시보드
│
├── analyzers/
│   ├── comprehensive_analyzer.py    # 10개 지표 종합 분석
│   ├── statistical_analyzer.py      # 통계 기반 분석/추천
│   ├── lotto_data_collector.py      # 동행복권 데이터 수집
│   └── exclude_number_manager.py   # 제외번호 관리
│
├── features/
│   ├── auto_update_scheduler.py    # 데이터 자동 업데이트
│   ├── backtester.py               # 전략 백테스트
│   ├── weight_optimizer.py         # 점수 가중치 최적화
│   ├── recommendation_report.py    # 추천 상세 리포트
│   └── strategy_profiles.py        # 전략 프로파일 (보수/균형/고변동)
│
├── utils/
│   ├── constants.py         # 공통 상수 정의
│   ├── logging_config.py    # 구조화된 로깅 설정
│   ├── helpers.py
│   ├── file_utils.py
│   └── system_utils.py
│
└── tests/                   # pytest 테스트 스위트
    ├── conftest.py
    ├── test_constants.py
    ├── test_statistical_analyzer.py
    ├── test_comprehensive_analyzer.py
    ├── test_number_storage.py
    ├── test_ai_pattern_learner.py
    └── test_backtester.py
```

## AI 모델 상세

`AIPatternLearner`는 sklearn의 `HistGradientBoostingClassifier` + `MultiOutputClassifier`를 사용합니다.

- **입력**: 최근 5회차 데이터 기반 125차원 특성 벡터
  - 과거 5회차 번호 (30), 합계 평균·홀수 비율 (2), 미출현 기간 (45), 공동출현 (45), 구간분포 (3)
- **출력**: 1~45번 각 번호의 출현 확률
- **PCA 옵션**: `AIPatternLearner(use_pca=True)` — 125차원을 60차원으로 축소하여 학습 속도 향상
- **모델 저장**: SHA256 해시로 무결성 검증 (`ai_models.pkl` + `ai_models.pkl.sha256`)

## 테스트

```bash
pytest
```

## 데이터 파일

| 파일 | 설명 |
|------|------|
| `로또당첨번호.csv` | 당첨번호 (메뉴 7번으로 자동 수집) |
| `saved_numbers.json` | 저장된 번호 조합 |
| `exclude_numbers.json` | 제외번호 목록 |
| `ai_models.pkl` | 학습된 AI 모델 |
| `lotto_system.log` | 시스템 로그 (자동 생성) |
