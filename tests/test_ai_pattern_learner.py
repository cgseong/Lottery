"""AIPatternLearner 단위 테스트"""

import os
import pytest
from ai_pattern_learner import AIPatternLearner


@pytest.fixture
def learner():
    return AIPatternLearner()


@pytest.fixture
def trained_learner(sample_data, tmp_path, monkeypatch):
    """실제 데이터 파일 없이 prepare_dataset 우회하여 학습된 모델 반환."""
    import pandas as pd

    al = AIPatternLearner()
    df = pd.DataFrame(sample_data)
    df.rename(columns={
        '번호1': '번호1', '번호2': '번호2', '번호3': '번호3',
        '번호4': '번호4', '번호5': '번호5', '번호6': '번호6',
    }, inplace=True)

    X, y, last_seen = al.prepare_dataset(df)
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.multioutput import MultiOutputClassifier
    base = HistGradientBoostingClassifier(max_iter=10, random_state=42)
    al.model = MultiOutputClassifier(base)
    al.model.fit(X, y)
    al.last_seen = last_seen
    al.is_trained = True
    return al, df


def test_initial_state(learner):
    assert not learner.is_trained
    assert learner.model is None
    assert learner.window_size == 5


def test_prepare_dataset(sample_data):
    import pandas as pd
    al = AIPatternLearner()
    df = pd.DataFrame(sample_data)
    X, y, last_seen = al.prepare_dataset(df)
    assert X.shape[1] == 125
    assert y.shape[1] == 45
    assert X.shape[0] == y.shape[0]
    assert len(last_seen) == 46


def test_calculate_probability_returns_list(trained_learner, monkeypatch):
    al, df = trained_learner
    monkeypatch.setattr(al, 'load_data', lambda: df)
    combos = [[1, 7, 14, 21, 33, 42], [2, 8, 15, 22, 34, 43]]
    scores = al.calculate_combination_probability(combos)
    assert len(scores) == 2
    assert all(isinstance(s, float) for s in scores)


def test_save_and_load_with_hash(trained_learner, tmp_path, monkeypatch):
    al, df = trained_learner
    monkeypatch.setattr(al, 'load_data', lambda: df)
    model_path = str(tmp_path / 'model.pkl')
    al.save_models(filename=model_path)
    assert os.path.exists(model_path)
    assert os.path.exists(model_path + '.sha256')

    al2 = AIPatternLearner()
    assert al2.load_models(filename=model_path)
    assert al2.is_trained


def test_tampered_model_rejected(trained_learner, tmp_path):
    al, _ = trained_learner
    model_path = str(tmp_path / 'model.pkl')
    al.save_models(filename=model_path)
    # 파일 변조
    with open(model_path, 'ab') as f:
        f.write(b'\x00')
    al2 = AIPatternLearner()
    result = al2.load_models(filename=model_path)
    assert not result


def test_load_nonexistent_returns_false(learner):
    assert not learner.load_models(filename='/tmp/nonexistent_xyz.pkl')
