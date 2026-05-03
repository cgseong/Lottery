import hashlib
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.multioutput import MultiOutputClassifier
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from typing import List, Optional, Tuple
import joblib
import os
import warnings

try:
    from utils.logging_config import get_logger
    _log = get_logger(__name__)
except ImportError:
    import logging
    _log = logging.getLogger(__name__)

# sklearn/pandas 버전 호환성 경고만 억제 (오류는 유지)
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning, module='sklearn')

class AIPatternLearner:
    """AI 패턴 학습 및 예측 클래스 (Multi-label & Boosting 기반)

    Args:
        data_file: 로또 당첨번호 CSV 파일 경로
        use_pca: True이면 PCA로 125차원 → pca_components 차원으로 축소하여
                 학습 속도를 높이고 과적합을 줄입니다.
        pca_components: PCA 축소 후 차원 수 (use_pca=True일 때 사용)
    """

    def __init__(self, data_file: str = '로또당첨번호.csv',
                 use_pca: bool = False, pca_components: int = 60):
        self.data_file = data_file
        self.model = None
        self.is_trained = False
        self.window_size = 5
        self.last_seen = None
        self.use_pca = use_pca
        self.pca_components = pca_components
        self._pca: Optional[PCA] = None
        
    def load_data(self) -> Optional[pd.DataFrame]:
        """데이터를 로드하고 시간순(회차 오름차순)으로 정렬합니다."""
        if not os.path.exists(self.data_file):
            print(f"[!] 데이터 파일이 없습니다: {self.data_file}")
            return None
            
        try:
            # 인코딩 호환성을 위한 다양한 시도
            try:
                df = pd.read_csv(self.data_file, encoding='utf-8')
            except UnicodeDecodeError:
                try:
                    df = pd.read_csv(self.data_file, encoding='cp949')
                except UnicodeDecodeError:
                    df = pd.read_csv(self.data_file, encoding='euc-kr')
                    
            # '회차' 기준으로 과거->최신 순서가 되도록 정렬 (데이터의 오름차순 보장)
            if '회차' in df.columns:
                df['회차'] = pd.to_numeric(df['회차'], errors='coerce')
                df = df.dropna(subset=['회차'])
                df = df.sort_values('회차', ascending=True).reset_index(drop=True)
                
            return df
        except Exception as e:
            _log.error("데이터 로드 오류: %s", e)
            return None

    def prepare_dataset(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """시계열 데이터를 Multi-label 학습 데이터셋(X, y)으로 변환합니다.

        파생 피처 (결측기간, 합계 평균, 홀짝 비율) 등을 추가합니다.
        """
        cols = ['번호1', '번호2', '번호3', '번호4', '번호5', '번호6']
        data = df[cols].values
        
        X = []
        y = []
        
        # 1~45번 번호가 가장 마지막으로 나온 회차 인덱스를 추적 (-1은 한 번도 안 나옴을 의미)
        last_seen = np.full(46, -1)
        
        # 순차적으로 데이터를 탐색하며 과거 기록 기반의 피처 X와 정답 y를 만듭니다.
        for i in range(len(data)):
            # window_size(최소 5회차) 이후부터 학습 데이터로 구성 가능
            if i >= self.window_size:
                # [피처 1] 과거 5회차 데이터(30개 번호) 1차원 평탄화
                window_data = data[i - self.window_size : i]
                flat_window = window_data.flatten()
                
                # [피처 2] 최근 5회차 당첨 번호의 합계 평균
                sum_avg = np.mean(np.sum(window_data, axis=1))
                
                # [피처 3] 최근 5회차 내 지정된 홀수 비율
                odd_count = np.sum(window_data % 2 != 0)
                odd_ratio = odd_count / (self.window_size * 6)
                
                # [피처 4] 1~45번 각 번호별 미출현 기간 (Missing Duration) 계산
                missing_duration = []
                for num in range(1, 46):
                    if last_seen[num] == -1:
                        # 한 번도 나온 적 없는 초기 번호는 임의의 큰 페널티 또는 기간 부여
                        missing_duration.append(50)
                    else:
                        missing_duration.append(i - last_seen[num])
                        
                # [피처 5] 공동 출현 피처: 각 번호가 window 내에서 다른 번호와 함께 나온 횟수
                cooccur = np.zeros(45)
                for row in window_data:
                    row_nums = [int(n) - 1 for n in row if 1 <= n <= 45]
                    for a in row_nums:
                        for b in row_nums:
                            if a != b:
                                cooccur[a] += 1
                # 최대값으로 정규화 (window_size * 5가 이론적 최대)
                max_cooccur = self.window_size * 5
                cooccur_norm = cooccur / max_cooccur

                # [피처 6] 구간별 분포 피처: window 내 1-15 / 16-30 / 31-45 출현 비율
                section_counts = np.zeros(3)
                total_nums = self.window_size * 6
                for row in window_data:
                    for n in row:
                        if 1 <= n <= 15:
                            section_counts[0] += 1
                        elif 16 <= n <= 30:
                            section_counts[1] += 1
                        elif 31 <= n <= 45:
                            section_counts[2] += 1
                section_norm = section_counts / max(1, total_nums)

                # X(입력) 결합 (총 피처 수: 30 + 1 + 1 + 45 + 45 + 3 = 125개)
                feature_vector = np.concatenate([
                    flat_window,
                    [sum_avg, odd_ratio],
                    missing_duration,
                    cooccur_norm,
                    section_norm,
                ])
                X.append(feature_vector)
                
                # [제안 1] y(정답) 구성: (Multi-label) 해당 회차(i)에 출현한 번호 자리를 1로 설정
                target_vector = np.zeros(45, dtype=int)
                for num in data[i]:
                    if 1 <= num <= 45:
                        target_vector[num - 1] = 1
                y.append(target_vector)
                
            # 현재 회차 당첨 번호 출현 기록 업데이트 (다음 회차 학습 데이터를 위해)
            for num in data[i]:
                if 1 <= num <= 45:
                    last_seen[num] = i
                    
        return np.array(X), np.array(y), last_seen

    def train_models(self) -> bool:
        """Multi-label 분류 모델(Boosting 기반)을 학습시킵니다."""
        print(" AI 모델 학습 시작 (파생 피처 및 Multi-Label 적용)...")
        
        df = self.load_data()
        if df is None or len(df) <= self.window_size:
            print("[WARN] 데이터 로드 실패 또는 데이터 양이 너무 적습니다.")
            return False
            
        X, y, self.last_seen = self.prepare_dataset(df)
        
        # 모델 검증을 위해 9:1로 데이터 분할
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1, random_state=42)

        # PCA 차원 축소 (선택)
        if self.use_pca:
            n_comp = min(self.pca_components, X_train.shape[1], X_train.shape[0])
            self._pca = PCA(n_components=n_comp, random_state=42)
            X_train = self._pca.fit_transform(X_train)
            print(f"   - PCA 적용: {X.shape[1]}차원 → {n_comp}차원")

        print("   - HistGradientBoostingClassifier (LightGBM 호환) 에 MultiOutput 학습 중...")
        try:
            base_estimator = HistGradientBoostingClassifier(max_iter=100, random_state=42)
            self.model = MultiOutputClassifier(base_estimator)
            self.model.fit(X_train, y_train)
        except Exception as e:
            _log.warning("내장 Boosting 모델 학습 실패, RandomForest로 대체합니다: %s", e)
            self.model = RandomForestClassifier(n_estimators=100, random_state=42)
            self.model.fit(X_train, y_train)
        
        self.is_trained = True
        print(" 모델 학습 완료")
        return True

    def _get_current_features(self, df: pd.DataFrame) -> np.ndarray:
        """현재 시점을 기준으로 다음 회차 예측을 위한 실시간 피처 벡터 생성"""
        cols = ['번호1', '번호2', '번호3', '번호4', '번호5', '번호6']
        data = df[cols].values
        
        window_data = data[-self.window_size:]
        flat_window = window_data.flatten()
        sum_avg = np.mean(np.sum(window_data, axis=1))
        odd_count = np.sum(window_data % 2 != 0)
        odd_ratio = odd_count / (self.window_size * 6)
        
        current_idx = len(data)
        missing_duration = []
        for num in range(1, 46):
            if self.last_seen is not None and self.last_seen[num] != -1:
                missing_duration.append(current_idx - self.last_seen[num])
            else:
                missing_duration.append(50)

        # [피처 5] 공동 출현 피처 (학습 시와 동일한 계산)
        cooccur = np.zeros(45)
        for row in window_data:
            row_nums = [int(n) - 1 for n in row if 1 <= n <= 45]
            for a in row_nums:
                for b in row_nums:
                    if a != b:
                        cooccur[a] += 1
        cooccur_norm = cooccur / (self.window_size * 5)

        # [피처 6] 구간별 분포 피처
        section_counts = np.zeros(3)
        total_nums = self.window_size * 6
        for row in window_data:
            for n in row:
                if 1 <= n <= 15:
                    section_counts[0] += 1
                elif 16 <= n <= 30:
                    section_counts[1] += 1
                elif 31 <= n <= 45:
                    section_counts[2] += 1
        section_norm = section_counts / max(1, total_nums)

        # 모델 차원에 맞게 reshape(1, -1) 적용 (총 125차원)
        return np.concatenate([
            flat_window, [sum_avg, odd_ratio], missing_duration, cooccur_norm, section_norm
        ]).reshape(1, -1)

    def predict_next(self) -> Optional[List[int]]:
        """가장 확률이 높은 6개의 다음 회차 당첨 번호를 예측합니다."""
        if not self.is_trained:
            if not self.train_models():
                return None
                
        df = self.load_data()
        if df is None:
            return None
            
        X_pred = self._get_current_features(df)
        if self.use_pca and self._pca is not None:
            X_pred = self._pca.transform(X_pred)

        try:
            # 예측 확률 리스트 가져오기 (각 번호 1~45에 대해 1이 나올 확률을 추적)
            proba_list = self.model.predict_proba(X_pred)
            
            probabilities = []
            for i in range(45):
                # 타겟 데이터(해당 번호)에 클래스가 (0, 1) 두 개면 shape[1] > 1, 만약 0만 있었으면 shape[1] == 1 임을 방어
                # proba_list는 [array([[P(0), P(1)]]), array([[P(0), P(1)]]), ...] 형식을 띔
                prob = proba_list[i][0, 1] if proba_list[i].shape[1] > 1 else 0.0
                probabilities.append(prob)
                
            # 확률 오름차순 시 가장 마지막 6개의 인덱스 추출
            top_6_indices = np.argsort(probabilities)[-6:]
            # 0번 인덱스가 숫자 1을 의미하므로 + 1
            predicted_numbers = sorted([int(idx) + 1 for idx in top_6_indices])
            return predicted_numbers
            
        except Exception as e:
            _log.warning("예측 계산 중 오류: %s", e)
            return None

    def calculate_combination_probability(self, combinations: List[List[int]]) -> List[float]:
        """각 조합에 포함된 번호별 AI 출현 확률의 기하평균을 점수화하여 반환합니다."""
        if not self.is_trained:
            if not self.train_models():
                return [0.0] * len(combinations)
        
        df = self.load_data()
        if df is None:
            return [0.0] * len(combinations)

        X_pred = self._get_current_features(df)
        if self.use_pca and self._pca is not None:
            X_pred = self._pca.transform(X_pred)

        try:
            proba_list = self.model.predict_proba(X_pred)
            number_probs = {}
            for i in range(45):
                prob = proba_list[i][0, 1] if proba_list[i].shape[1] > 1 else 0.0
                number_probs[i + 1] = prob
                
        except Exception as e:
            _log.warning("확률 계산 오류: %s", e)
            return [0.0] * len(combinations)

        scores = []
        eps = 1e-6
        for combo in combinations:
            probs = [min(1 - eps, max(eps, float(number_probs.get(num, 0.0)))) for num in combo]
            if not probs:
                scores.append(0.0)
                continue

            # 합산 대신 기하평균 기반 합성으로 특정 번호 편중을 완화
            log_joint = float(np.sum(np.log(probs)))
            geometric_mean = float(np.exp(log_joint / len(probs)))
            arithmetic_mean = float(np.mean(probs))

            # 범위 다양성(저/중/고 구간 분산) 보너스
            low = sum(1 for n in combo if 1 <= n <= 15)
            mid = sum(1 for n in combo if 16 <= n <= 30)
            high = sum(1 for n in combo if 31 <= n <= 45)
            spread_penalty = (abs(low - 2) + abs(mid - 2) + abs(high - 2)) / 6.0
            diversity_bonus = max(0.0, 1.0 - spread_penalty)

            score = geometric_mean * 0.75 + arithmetic_mean * 0.20 + diversity_bonus * 0.05
            scores.append(score)
            
        return scores

    @staticmethod
    def _hash_file(path: str) -> str:
        h = hashlib.sha256()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(65536), b''):
                h.update(chunk)
        return h.hexdigest()

    def save_models(self, filename: str = 'ai_models.pkl') -> None:
        """학습된 모델과 파생 피처(last_seen), PCA 상태를 저장하고 SHA256 해시를 기록합니다."""
        if self.is_trained:
            joblib.dump((self.model, getattr(self, 'last_seen', None), self._pca), filename)
            digest = self._hash_file(filename)
            with open(filename + '.sha256', 'w') as f:
                f.write(digest)
            print(f" 모델 저장 완료: {filename}")

    def load_models(self, filename: str = 'ai_models.pkl') -> bool:
        """저장된 모델 상태를 불러옵니다. SHA256 해시로 무결성을 검증합니다."""
        if not os.path.exists(filename):
            return False
        hash_file = filename + '.sha256'
        if os.path.exists(hash_file):
            with open(hash_file, 'r') as f:
                expected = f.read().strip()
            actual = self._hash_file(filename)
            if actual != expected:
                print(f"[WARN] 모델 파일 무결성 검증 실패: {filename}. 재학습이 필요합니다.")
                _log.warning("모델 파일 무결성 검증 실패: %s", filename)
                return False
        data = joblib.load(filename)
        if isinstance(data, tuple) and len(data) == 3:
            self.model, self.last_seen, self._pca = data
        elif isinstance(data, tuple) and len(data) == 2:
            self.model, self.last_seen = data
        else:
            self.model = data
        self.use_pca = self._pca is not None
        self.is_trained = True
        print(f" 모델 로드 완료: {filename}")
        return True
