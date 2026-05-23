"""머신러닝/AI 모델 고도화 모듈

LSTM, Transformer, GAN, 딥 앙상블을 활용한 로또 번호 예측기.
PyTorch 기반으로 구현하며, 미설치 시 sklearn 폴백을 제공합니다.
"""
from __future__ import annotations

import numpy as np
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

from utils.constants import MAX_LOTTO_NUMBER, NUM_LOTTO_NUMBERS_TO_PICK

try:
    from utils.logging_config import get_logger
    _log = get_logger(__name__)
except ImportError:
    import logging
    _log = logging.getLogger(__name__)

# PyTorch 선택적 의존성
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import DataLoader, TensorDataset
    _HAS_TORCH = True
except ImportError:
    _HAS_TORCH = False
    _log.info("PyTorch 미설치 — sklearn 폴백 모드로 동작합니다.")



# ═══════════════════════════════════════════════════════════════════════
# 공통 데이터 전처리
# ═══════════════════════════════════════════════════════════════════════

def _prepare_sequences(historical_data: List[Dict], window_size: int = 10
                       ) -> Tuple[np.ndarray, np.ndarray]:
    """시계열 시퀀스 데이터를 생성합니다.

    Args:
        historical_data: 회차순 정렬된 데이터
        window_size: 입력 시퀀스 길이

    Returns:
        X: shape=(N, window_size, 45) 이진 시퀀스
        y: shape=(N, 45) 다음 회차 이진 벡터
    """
    rows = sorted(historical_data, key=lambda x: int(x.get('회차', 0) or 0))

    # 각 회차를 45차원 이진 벡터로 변환
    vectors = []
    for row in rows:
        vec = np.zeros(MAX_LOTTO_NUMBER, dtype=np.float32)
        for i in range(1, 7):
            try:
                n = int(row.get(f'번호{i}', 0))
                if 1 <= n <= MAX_LOTTO_NUMBER:
                    vec[n - 1] = 1.0
            except (ValueError, TypeError):
                continue
        vectors.append(vec)

    if len(vectors) <= window_size:
        return np.empty((0, window_size, MAX_LOTTO_NUMBER)), np.empty((0, MAX_LOTTO_NUMBER))

    vectors = np.array(vectors)
    X, y = [], []
    for i in range(window_size, len(vectors)):
        X.append(vectors[i - window_size:i])
        y.append(vectors[i])

    return np.array(X, dtype=np.float32), np.array(y, dtype=np.float32)



# ═══════════════════════════════════════════════════════════════════════
# 1. LSTM 예측기
# ═══════════════════════════════════════════════════════════════════════

if _HAS_TORCH:
    class _LSTMNet(nn.Module):
        """Bidirectional LSTM + Attention for multi-label prediction."""

        def __init__(self, input_dim: int = 45, hidden_dim: int = 128,
                     num_layers: int = 2, dropout: float = 0.3):
            super().__init__()
            self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers,
                                batch_first=True, bidirectional=True, dropout=dropout)
            self.attention = nn.Sequential(
                nn.Linear(hidden_dim * 2, hidden_dim),
                nn.Tanh(),
                nn.Linear(hidden_dim, 1)
            )
            self.fc = nn.Sequential(
                nn.Linear(hidden_dim * 2, hidden_dim),
                nn.ReLU(),
                nn.Dropout(dropout),
                nn.Linear(hidden_dim, input_dim),
                nn.Sigmoid()
            )

        def forward(self, x):
            # x: (batch, seq_len, 45)
            lstm_out, _ = self.lstm(x)  # (batch, seq, hidden*2)
            # Attention mechanism
            attn_weights = self.attention(lstm_out)  # (batch, seq, 1)
            attn_weights = torch.softmax(attn_weights, dim=1)
            context = (lstm_out * attn_weights).sum(dim=1)  # (batch, hidden*2)
            return self.fc(context)  # (batch, 45)



    class _TransformerNet(nn.Module):
        """Transformer Encoder for sequence-to-label prediction."""

        def __init__(self, input_dim: int = 45, d_model: int = 128,
                     nhead: int = 4, num_layers: int = 3, dropout: float = 0.2):
            super().__init__()
            self.input_proj = nn.Linear(input_dim, d_model)
            self.pos_encoding = nn.Parameter(torch.randn(1, 100, d_model) * 0.02)
            encoder_layer = nn.TransformerEncoderLayer(
                d_model=d_model, nhead=nhead, dim_feedforward=d_model * 4,
                dropout=dropout, batch_first=True
            )
            self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
            self.fc = nn.Sequential(
                nn.Linear(d_model, d_model),
                nn.GELU(),
                nn.Dropout(dropout),
                nn.Linear(d_model, input_dim),
                nn.Sigmoid()
            )

        def forward(self, x):
            # x: (batch, seq_len, 45)
            seq_len = x.size(1)
            x = self.input_proj(x)  # (batch, seq, d_model)
            x = x + self.pos_encoding[:, :seq_len, :]
            x = self.encoder(x)  # (batch, seq, d_model)
            x = x.mean(dim=1)  # global average pooling
            return self.fc(x)



    class _GANGenerator(nn.Module):
        """GAN Generator — 잠재 벡터로부터 로또 번호 조합을 생성합니다."""

        def __init__(self, latent_dim: int = 32, hidden_dim: int = 128,
                     output_dim: int = 45):
            super().__init__()
            self.net = nn.Sequential(
                nn.Linear(latent_dim, hidden_dim),
                nn.LeakyReLU(0.2),
                nn.BatchNorm1d(hidden_dim),
                nn.Linear(hidden_dim, hidden_dim * 2),
                nn.LeakyReLU(0.2),
                nn.BatchNorm1d(hidden_dim * 2),
                nn.Linear(hidden_dim * 2, output_dim),
                nn.Sigmoid()
            )

        def forward(self, z):
            return self.net(z)

    class _GANDiscriminator(nn.Module):
        """GAN Discriminator — 조합이 '실제 당첨' 패턴인지 판별합니다."""

        def __init__(self, input_dim: int = 45, hidden_dim: int = 128):
            super().__init__()
            self.net = nn.Sequential(
                nn.Linear(input_dim, hidden_dim),
                nn.LeakyReLU(0.2),
                nn.Dropout(0.3),
                nn.Linear(hidden_dim, hidden_dim // 2),
                nn.LeakyReLU(0.2),
                nn.Dropout(0.3),
                nn.Linear(hidden_dim // 2, 1),
                nn.Sigmoid()
            )

        def forward(self, x):
            return self.net(x)



# ═══════════════════════════════════════════════════════════════════════
# 2. 통합 딥러닝 예측기 클래스
# ═══════════════════════════════════════════════════════════════════════

class DeepLearningPredictor:
    """LSTM, Transformer, GAN 앙상블 기반 로또 번호 예측기.

    PyTorch가 설치되어 있으면 딥러닝 모델을 학습하고,
    미설치 시 sklearn 기반 폴백(HistGradientBoosting)으로 동작합니다.

    앙상블 전략:
        - LSTM: 시계열 순서 패턴 학습
        - Transformer: 장거리 의존성 + 셀프 어텐션
        - GAN: 실제 당첨 패턴 분포 학습 → 새로운 조합 생성
        - 소프트 보팅으로 최종 확률 합산
    """

    def __init__(self, historical_data: List[Dict],
                 window_size: int = 10,
                 epochs: int = 100,
                 batch_size: int = 32,
                 lr: float = 0.001):
        self.historical_data = historical_data
        self.window_size = window_size
        self.epochs = epochs
        self.batch_size = batch_size
        self.lr = lr
        self._is_trained = False
        self._models: Dict[str, object] = {}
        self._device = 'cpu'

        if _HAS_TORCH and torch.cuda.is_available():
            self._device = 'cuda'


    def train(self) -> bool:
        """모든 모델을 학습합니다."""
        X, y = _prepare_sequences(self.historical_data, self.window_size)
        if len(X) < 20:
            _log.warning("학습 데이터 부족 (최소 20개 시퀀스 필요)")
            return False

        if _HAS_TORCH:
            return self._train_torch(X, y)
        else:
            return self._train_sklearn_fallback(X, y)

    def _train_torch(self, X: np.ndarray, y: np.ndarray) -> bool:
        """PyTorch 기반 LSTM + Transformer + GAN 학습."""
        device = self._device

        # Train/Val split
        split_idx = int(len(X) * 0.9)
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]

        train_dataset = TensorDataset(
            torch.FloatTensor(X_train), torch.FloatTensor(y_train))
        train_loader = DataLoader(train_dataset, batch_size=self.batch_size, shuffle=True)

        # --- LSTM ---
        lstm_model = _LSTMNet().to(device)
        self._train_model(lstm_model, train_loader, 'LSTM')
        self._models['lstm'] = lstm_model

        # --- Transformer ---
        transformer_model = _TransformerNet().to(device)
        self._train_model(transformer_model, train_loader, 'Transformer')
        self._models['transformer'] = transformer_model

        # --- GAN ---
        self._train_gan(torch.FloatTensor(y_train).to(device))

        self._is_trained = True
        _log.info("딥러닝 앙상블 학습 완료 (LSTM + Transformer + GAN)")
        return True

    def _train_model(self, model: 'nn.Module', loader: 'DataLoader', name: str):
        """공통 학습 루프."""
        device = self._device
        optimizer = optim.Adam(model.parameters(), lr=self.lr)
        criterion = nn.BCELoss()
        scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=self.epochs)

        model.train()
        for epoch in range(self.epochs):
            total_loss = 0
            for xb, yb in loader:
                xb, yb = xb.to(device), yb.to(device)
                optimizer.zero_grad()
                pred = model(xb)
                loss = criterion(pred, yb)
                loss.backward()
                nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step()
                total_loss += loss.item()
            scheduler.step()

            if (epoch + 1) % 25 == 0:
                avg_loss = total_loss / len(loader)
                _log.debug("[%s] Epoch %d/%d — Loss: %.4f", name, epoch+1, self.epochs, avg_loss)


    def _train_gan(self, real_data: 'torch.Tensor'):
        """GAN 학습 — Generator + Discriminator."""
        device = self._device
        latent_dim = 32

        generator = _GANGenerator(latent_dim=latent_dim).to(device)
        discriminator = _GANDiscriminator().to(device)

        opt_g = optim.Adam(generator.parameters(), lr=self.lr * 0.5, betas=(0.5, 0.999))
        opt_d = optim.Adam(discriminator.parameters(), lr=self.lr * 0.5, betas=(0.5, 0.999))
        criterion = nn.BCELoss()

        n_samples = real_data.size(0)
        gan_epochs = min(self.epochs, 80)

        for epoch in range(gan_epochs):
            # --- Train Discriminator ---
            idx = torch.randint(0, n_samples, (min(self.batch_size, n_samples),))
            real_batch = real_data[idx]
            real_labels = torch.ones(real_batch.size(0), 1).to(device)
            fake_labels = torch.zeros(real_batch.size(0), 1).to(device)

            z = torch.randn(real_batch.size(0), latent_dim).to(device)
            fake_batch = generator(z)

            opt_d.zero_grad()
            d_real = discriminator(real_batch)
            d_fake = discriminator(fake_batch.detach())
            d_loss = criterion(d_real, real_labels) + criterion(d_fake, fake_labels)
            d_loss.backward()
            opt_d.step()

            # --- Train Generator ---
            opt_g.zero_grad()
            z = torch.randn(real_batch.size(0), latent_dim).to(device)
            fake_batch = generator(z)
            g_loss = criterion(discriminator(fake_batch), real_labels)
            g_loss.backward()
            opt_g.step()

        self._models['gan_generator'] = generator
        self._models['gan_discriminator'] = discriminator
        _log.info("GAN 학습 완료 (%d epochs)", gan_epochs)


    def _train_sklearn_fallback(self, X: np.ndarray, y: np.ndarray) -> bool:
        """sklearn 폴백 학습 (PyTorch 미설치 시)."""
        from sklearn.ensemble import HistGradientBoostingClassifier
        from sklearn.multioutput import MultiOutputClassifier

        # X를 2D로 변환: (N, window*45)
        X_flat = X.reshape(X.shape[0], -1)

        model = MultiOutputClassifier(
            HistGradientBoostingClassifier(max_iter=150, random_state=42)
        )
        model.fit(X_flat, y.astype(int))
        self._models['sklearn_fallback'] = model
        self._is_trained = True
        _log.info("sklearn 폴백 모델 학습 완료")
        return True

    def predict_probabilities(self) -> np.ndarray:
        """다음 회차 각 번호(1~45)의 출현 확률을 예측합니다.

        Returns:
            shape=(45,) 확률 벡터
        """
        if not self._is_trained:
            if not self.train():
                return np.ones(MAX_LOTTO_NUMBER) / MAX_LOTTO_NUMBER

        X, _ = _prepare_sequences(self.historical_data, self.window_size)
        if len(X) == 0:
            return np.ones(MAX_LOTTO_NUMBER) / MAX_LOTTO_NUMBER

        # 최근 시퀀스
        latest_seq = X[-1:].copy()

        if _HAS_TORCH and 'lstm' in self._models:
            return self._predict_torch_ensemble(latest_seq)
        elif 'sklearn_fallback' in self._models:
            return self._predict_sklearn(latest_seq)
        return np.ones(MAX_LOTTO_NUMBER) / MAX_LOTTO_NUMBER


    def _predict_torch_ensemble(self, latest_seq: np.ndarray) -> np.ndarray:
        """LSTM + Transformer + GAN 앙상블 예측."""
        device = self._device
        x_tensor = torch.FloatTensor(latest_seq).to(device)

        probs_sum = np.zeros(MAX_LOTTO_NUMBER, dtype=np.float64)
        n_models = 0

        # LSTM prediction
        if 'lstm' in self._models:
            self._models['lstm'].eval()
            with torch.no_grad():
                pred = self._models['lstm'](x_tensor).cpu().numpy().flatten()
            probs_sum += pred
            n_models += 1

        # Transformer prediction
        if 'transformer' in self._models:
            self._models['transformer'].eval()
            with torch.no_grad():
                pred = self._models['transformer'](x_tensor).cpu().numpy().flatten()
            probs_sum += pred
            n_models += 1

        # GAN: 여러 샘플 생성 후 빈도 기반 확률
        if 'gan_generator' in self._models:
            gen = self._models['gan_generator']
            gen.eval()
            with torch.no_grad():
                z = torch.randn(100, 32).to(device)
                fake_samples = gen(z).cpu().numpy()
            # 각 번호가 상위 6에 포함되는 빈도
            gan_freq = np.zeros(MAX_LOTTO_NUMBER)
            for sample in fake_samples:
                top6 = np.argsort(sample)[-6:]
                for idx in top6:
                    gan_freq[idx] += 1
            gan_freq /= max(gan_freq.sum(), 1)
            probs_sum += gan_freq
            n_models += 1

        if n_models > 0:
            probs_sum /= n_models

        # 정규화
        total = probs_sum.sum()
        if total > 0:
            probs_sum /= total
        return probs_sum

    def _predict_sklearn(self, latest_seq: np.ndarray) -> np.ndarray:
        """sklearn 폴백 예측."""
        model = self._models['sklearn_fallback']
        X_flat = latest_seq.reshape(1, -1)
        try:
            proba_list = model.predict_proba(X_flat)
            probs = np.array([
                p[0, 1] if p.shape[1] > 1 else 0.0 for p in proba_list
            ])
        except Exception:
            probs = np.ones(MAX_LOTTO_NUMBER) / MAX_LOTTO_NUMBER

        total = probs.sum()
        if total > 0:
            probs /= total
        return probs


    def generate_combinations(self, n_combinations: int = 10,
                              exclude: Optional[set] = None) -> List[Dict]:
        """예측 확률 기반으로 번호 조합을 생성합니다.

        Args:
            n_combinations: 생성할 조합 수
            exclude: 제외할 번호 집합

        Returns:
            [{'numbers': [...], 'score': float, 'method': str}, ...]
        """
        exclude = exclude or set()
        probs = self.predict_probabilities()

        # 제외 번호 확률 제거
        for n in exclude:
            if 1 <= n <= MAX_LOTTO_NUMBER:
                probs[n - 1] = 0.0

        total = probs.sum()
        if total <= 0:
            probs = np.ones(MAX_LOTTO_NUMBER) / MAX_LOTTO_NUMBER
        else:
            probs /= total

        rng = np.random.default_rng(seed=None)
        results = []
        seen = set()

        for _ in range(n_combinations * 50):
            if len(results) >= n_combinations:
                break

            # 확률 가중 샘플링
            chosen = rng.choice(MAX_LOTTO_NUMBER, size=6, replace=False, p=probs)
            nums = sorted((chosen + 1).tolist())
            key = tuple(nums)

            if key in seen:
                continue
            seen.add(key)

            # 점수: 선택된 번호의 확률 합 (기하평균)
            num_probs = [probs[n - 1] for n in nums]
            geo_mean = float(np.exp(np.mean(np.log(np.clip(num_probs, 1e-10, 1)))))

            results.append({
                'numbers': nums,
                'score': geo_mean,
                'method': 'Deep Learning Ensemble',
            })

        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:n_combinations]

    def score_combination(self, numbers: List[int]) -> float:
        """조합의 딥러닝 기반 점수를 반환합니다 (0~1)."""
        probs = self.predict_probabilities()
        num_probs = [probs[n - 1] for n in numbers if 1 <= n <= MAX_LOTTO_NUMBER]
        if not num_probs:
            return 0.0
        # 기하평균 정규화
        geo_mean = float(np.exp(np.mean(np.log(np.clip(num_probs, 1e-10, 1)))))
        # 이론적 최대 (상위 6개 확률의 기하평균)로 정규화
        top6_probs = np.sort(probs)[-6:]
        max_geo = float(np.exp(np.mean(np.log(np.clip(top6_probs, 1e-10, 1)))))
        if max_geo > 0:
            return float(min(1.0, geo_mean / max_geo))
        return 0.5
