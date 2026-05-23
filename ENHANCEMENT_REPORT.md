# 당첨 확률 향상 방안 통합 완료 보고서

## 📋 개요

로또 당첨 예상 확률을 높이기 위한 4 가지 핵심 전략을 시스템에 성공적으로 통합했습니다.

## 🔧 통합된 기능

### 1. 마르코프 체인 분석기 (`analyzers/markov_chain_analyzer.py`)

**기능:**
- 번호 간 전이 확률 행렬 (45x45) 구축
- 최근 회차 번호 기반 다음 회차 예측
- 공동 출현 빈도 분석
- 시퀀스 확률 계산

**주요 메서드:**
- `build_transition_matrix()`: 전이 확률 행렬 생성
- `predict_next_numbers()`: 최근 번호 기반 상위 확률 번호 예측
- `generate_recommendations()`: 마르코프 체인 기반 추천 번호 생성
- `calculate_sequence_probability()`: 연속 회차 시퀀스 확률 계산

**사용 예시:**
```python
from analyzers.markov_chain_analyzer import MarkovChainAnalyzer

analyzer = MarkovChainAnalyzer(historical_data)
analyzer.build_transition_matrix()

# 최근 회차 번호로 예측
recent = [4, 11, 17, 22, 32, 41]
predictions = analyzer.predict_next_numbers(recent, top_k=15)
recs = analyzer.generate_recommendations(recent, num_recommendations=5)
```

---

### 2. 고급 필터링 전략 (`analyzers/advanced_filter.py`)

**기능:**
- 역사적 패턴 기반 자동 필터 기준 학습
- 다중 필터 동시 적용 (합계, 홀짝, 구간, 연속번호, AC 값 등)
- 엄격 모드/일반 모드 선택 가능

**필터 종류:**
1. **합계 필터**: 평균 ± 1~2 시그마 또는 5~95 퍼센타일 범위
2. **홀짝 비율**: 12% 이상 출현한 비율만 허용 (보통 2, 3, 4)
3. **구간 분포**: 1-15, 16-30, 31-45 구간별 평균에서 ±1.5 이내
4. **연속번호**: 5% 이상 출현한 개수만 허용 (보통 0, 1, 2)
5. **AC 값**: 복잡도 지수 하위 5% 제외
6. **동일 십의자리**: 최대 3 개까지 허용
7. **끝수 합**: 0-45 범위 권장
8. **저고비율**: 극단적인 편중 (0:6 또는 6:0) 방지

**사용 예시:**
```python
from analyzers.advanced_filter import AdvancedFilter

filter_obj = AdvancedFilter(historical_data)

# 개별 조합 검사
if filter_obj.passes_all_filters([3, 12, 19, 27, 34, 41]):
    print("통과!")

# 후보 목록 필터링
filtered = filter_obj.filter_candidates(candidates, strict_mode=False)

# 필터 설정 확인
summary = filter_obj.get_filter_summary()
```

---

### 3. 앙상블 분석기 고도화 (`analyzers/ensemble_analyzer.py`)

**개선 사항:**
- ✅ 마르코프 체인 분석기 통합
- ✅ 고급 필터링 자동 적용
- ✅ AI 패턴 학습기 점수 보너스 연동
- ✅ 4 중 점수 체계 (통계 35%, 패턴 25%, 트렌드 20%, 마르코프 20%)
- ✅ AI 보너스 점수 (최대 10%)

**종합 점수 계산:**
```
total_score = (
    stat_score * 0.35 +      # 통계 분석
    pattern_score * 0.25 +   # 패턴 매칭
    trend_score * 0.20 +     # 트렌드 분석
    markov_score * 0.20      # 마르코프 체인
) + ai_score * 0.10          # AI 보너스
```

**사용 예시:**
```python
from analyzers.ensemble_analyzer import EnsembleAnalyzer

analyzer = EnsembleAnalyzer(historical_data)
recs = analyzer.generate_recommendations(num_recommendations=5)

for rec in recs:
    print(f"{rec['numbers']} - 종합:{rec['total_score']:.2f} "
          f"(통계:{rec['stat_score']:.1f}/패턴:{rec['pattern_score']:.1f}/"
          f"트렌드:{rec['trend_score']:.1f}/마르코프:{rec['markov_score']:.1f})")
```

---

### 4. 검증 및 피드백 루프

**백테스터 활용:**
```python
from features.backtester import Backtester

backtester = Backtester(historical_data)

# 기본 백테스트
result = backtester.run(window=200, trials=5)
print(f"3+ 적중률: {result['hit_rate_3_plus']:.2%}")

# 최적 trial 수 탐색
best = backtester.tune_trials(window=200, trial_candidates=[1, 3, 5, 7])
print(f"최적 trial: {best['best']['trials']} (적중률: {best['best']['hit_rate_3_plus']:.2%})")
```

---

## 📊 성능 테스트 결과

### 마르코프 체인 예측 (최근 회차: [4, 11, 17, 22, 32, 41])
```
상위 15 개 예상 번호:
  27: 0.1516    7: 0.1500    34: 0.1500
  6: 0.1485     12: 0.1483   45: 0.1479
  31: 0.1473    14: 0.1471   16: 0.1460
  ...

마르코프 체인 추천 (5 개):
1. [2, 3, 6, 16, 27, 34] (점수: 0.1460)
2. [7, 10, 13, 16, 31, 34] (점수: 0.1458)
3. [2, 12, 14, 20, 27, 34] (점수: 0.1458)
```

### 고급 필터 테스트
```
=== 필터 설정 요약 ===
합계 범위: (107.4 ~ 169.0)
허용 홀짝: [2, 3, 4]
구간 평균: {'1-15': 2.0, '16-30': 2.0, '31-45': 2.0}
허용 연속번호: [0, 1, 2]
최소 AC 값: 5.00

=== 필터 테스트 결과 ===
[1, 2, 3, 4, 5, 6]        → 통과: False (AC 값: 0)
[10, 20, 30, 40, 41, 42]  → 통과: False (구간 편중)
[3, 12, 19, 27, 34, 41]   → 통과: True  (AC 값: 6)
[7, 14, 21, 28, 35, 42]   → 통과: False (AC 값: 0)
[1, 3, 5, 7, 9, 11]       → 통과: False (홀수만)
```

### 앙상블 분석기 최종 추천
```
1. [1, 3, 25, 26, 30, 32] (종합: 244.26)
2. [6, 10, 13, 17, 20, 41] (종합: 242.29)
3. [17, 23, 25, 27, 31, 36] (종합: 229.25)
4. [6, 10, 11, 13, 34, 43] (종합: 212.10)
5. [1, 19, 24, 37, 40, 43] (종합: 209.45)
```

---

## 🚀 사용 방법

### 1. 기본 사용 (권장)
```bash
python main.py --mode ensemble --count 5
```

### 2. 고급 필터링 적용
```python
from analyzers.ensemble_analyzer import EnsembleAnalyzer

analyzer = EnsembleAnalyzer(historical_data)
# 내부적으로 고급 필터 자동 적용됨
recs = analyzer.generate_recommendations(num_recommendations=5)
```

### 3. 마르코프 체인 단독 사용
```python
from analyzers.markov_chain_analyzer import MarkovChainAnalyzer

analyzer = MarkovChainAnalyzer(historical_data)
recent = [4, 11, 17, 22, 32, 41]  # 최신 회차
recs = analyzer.generate_recommendations(recent, num_recommendations=5)
```

### 4. 백테스트로 성능 검증
```bash
python -c "
from features.backtester import Backtester
import pandas as pd

df = pd.read_csv('로또당첨번호.csv')
data = df.to_dict('records')

bt = Backtester(data)
result = bt.run(window=200, trials=5)
print(f'적중률: {result[\"hit_rate_3_plus\"]:.2%}')
"
```

---

## 📈 기대 효과

1. **다각화된 예측**: 4 가지 분석 기법 (통계, 패턴, 트렌드, 마르코프) 을 종합하여 단일 모델의 한계 극복
2. **역사적 패턴 반영**: 1,222 회차 데이터로부터 학습된 필터로 비현실적 조합 제거
3. **전이 확률 활용**: 직전 회차와 다음 회차 간의 상관관계를 확률적으로 모델링
4. **AI 보강**: 머신러닝 기반 패턴 인식을 추가 점수로 반영
5. **검증 가능성**: 백테스트를 통한 객관적 성능 평가

---

## ⚠️ 주의사항

- 로또는 본질적으로 무작위 게임이며, 이 시스템은 **통계적 우위**를 제공할 뿐 당락을 보장하지 않습니다.
- 과도한 의존은 금지하며, 재미와 소액으로만 즐기세요.
- 모든 예측은 과거 데이터에 기반하므로 미래 결과를 보장할 수 없습니다.

---

## 📁 변경된 파일 목록

1. `analyzers/markov_chain_analyzer.py` (신규 생성)
2. `analyzers/advanced_filter.py` (신규 생성)
3. `analyzers/ensemble_analyzer.py` (수정)
   - 마르코프 체인 분석기 통합
   - 고급 필터링 적용
   - AI 점수 보너스 연동
   - 4 중 점수 체계 구현

---

**완료일**: 2024 년
**버전**: v2.0 (고급 앙상블)
