"""AI 패턴 추천 페이지"""

import os
import sys
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QGroupBox, QFrame,
    QMessageBox, QProgressBar
)
from PySide6.QtCore import Qt, QThread, Signal

from gui.pages.base_page import BasePage
from gui.widgets.number_ball import NumberBallWidget


class AITrainWorker(QThread):
    """AI 모델 학습 및 추천 생성"""
    finished = Signal(dict)
    progress = Signal(str)

    def __init__(self, historical_data, stat_analyzer):
        super().__init__()
        self.historical_data = historical_data
        self.stat_analyzer = stat_analyzer

    def run(self):
        try:
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            if project_root not in sys.path:
                sys.path.insert(0, project_root)

            from ai_pattern_learner import AIPatternLearner

            self.progress.emit("AI 모델 학습 중...")
            learner = AIPatternLearner()

            if not learner.is_trained:
                learner.train_models()

            self.progress.emit("후보 조합 생성 중...")
            candidates = self.stat_analyzer.generate_unique_recommendations(
                num_recommendations=1000,
            )

            if not candidates:
                self.finished.emit({})
                return

            self.progress.emit("AI 확률 계산 중...")
            candidate_numbers = [c['numbers'] for c in candidates]
            ai_scores = learner.calculate_combination_probability(candidate_numbers)

            # AI 점수 부착 및 최적 조합 선정
            scored = []
            for cand, ai_score in zip(candidates, ai_scores):
                if ai_score is not None:
                    cand['ai_score'] = ai_score
                    scored.append(cand)

            if not scored:
                self.finished.emit({})
                return

            # 정규화 후 종합 점수
            ai_vals = [c['ai_score'] for c in scored]
            stat_vals = [c['score'] for c in scored]
            ai_min, ai_max = min(ai_vals), max(ai_vals)
            st_min, st_max = min(stat_vals), max(stat_vals)

            def norm(v, lo, hi):
                return (v - lo) / (hi - lo) if hi > lo else 0.0

            for cand in scored:
                cand['combined_score'] = (
                    norm(cand['ai_score'], ai_min, ai_max) * 0.5
                    + norm(cand['score'], st_min, st_max) * 0.5
                )

            # 상위 5개
            scored.sort(key=lambda c: c['combined_score'], reverse=True)
            top5 = scored[:5]

            self.progress.emit("완료!")
            self.finished.emit({'results': top5})

        except Exception as e:
            err_msg = str(e)
            # numpy/scikit-learn 바이너리 비호환 감지
            if 'dtype size changed' in err_msg or 'binary incompatibility' in err_msg:
                self.progress.emit(
                    "⚠️ numpy/scikit-learn 버전 호환 오류. "
                    "터미널에서 실행: pip install --upgrade numpy scikit-learn"
                )
            else:
                self.progress.emit(f"오류: {e}")
            self.finished.emit({})


class AIPage(BasePage):
    """AI 패턴 추천 페이지"""

    def __init__(self, parent=None):
        super().__init__("AI 패턴 추천", parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._create_title_label("🤖 AI 패턴 추천 (미출현 조합 + AI 확률)"))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)

        # 설명
        desc_group = QGroupBox("알고리즘 설명")
        desc_group.setStyleSheet(self._group_style())
        desc_layout = QVBoxLayout(desc_group)
        desc_layout.addWidget(QLabel(
            "• 과거 1등 당첨번호와 겹치지 않는 새로운 조합 생성\n"
            "• AI 모델 (HistGradientBoosting 앙상블)로 출현 확률 계산\n"
            "• 통계 점수 + AI 확률을 종합하여 최적 조합 추천"
        ))
        content_layout.addWidget(desc_group)

        # 진행 상태
        self.progress_label = QLabel("")
        self.progress_label.setStyleSheet("color: #7f8c8d; font-size: 13px; padding: 5px;")
        content_layout.addWidget(self.progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # indeterminate
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                text-align: center;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #9b59b6;
                border-radius: 4px;
            }
        """)
        content_layout.addWidget(self.progress_bar)

        # 실행 버튼
        self.run_btn = QPushButton("🤖 AI 추천 실행")
        self.run_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border: none;
                padding: 12px 30px;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #8e44ad; }
            QPushButton:pressed { background-color: #7d3c98; }
        """)
        self.run_btn.clicked.connect(self._run_ai)
        content_layout.addWidget(self.run_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        # 결과 영역
        self.results_group = QGroupBox("AI 추천 결과")
        self.results_group.setStyleSheet(self._group_style())
        self.results_layout = QVBoxLayout(self.results_group)
        self.results_layout.addWidget(QLabel("AI 추천 실행 버튼을 클릭하세요."))
        content_layout.addWidget(self.results_group)

        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)

    def _group_style(self) -> str:
        return """
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                color: #2c3e50;
                border: 1px solid #ddd;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px;
            }
        """

    def _run_ai(self):
        if not self.historical_data:
            QMessageBox.warning(self, "경고", "로또당첨번호.csv 파일을 찾을 수 없습니다.")
            return
        if not self.stat_analyzer:
            QMessageBox.warning(
                self, "경고",
                "분석기가 초기화되지 않았습니다.\n\n"
                "터미널에서 아래 명령어를 실행해주세요:\n"
                "pip install --upgrade matplotlib numpy"
            )
            return

        self.run_btn.setEnabled(False)
        self.progress_bar.setVisible(True)

        self.worker = AITrainWorker(self.historical_data, self.stat_analyzer)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()

    def _on_progress(self, msg: str):
        self.progress_label.setText(msg)

    def _on_finished(self, result: dict):
        self.run_btn.setEnabled(True)
        self.progress_bar.setVisible(False)

        while self.results_layout.count():
            item = self.results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        results = result.get('results', [])
        if not results:
            self.results_layout.addWidget(QLabel("AI 추천 번호를 생성할 수 없습니다."))
            return

        for i, rec in enumerate(results, 1):
            frame = QFrame()
            frame.setStyleSheet("""
                QFrame {
                    background-color: #f5f0ff;
                    border: 1px solid #d4c5f9;
                    border-radius: 8px;
                    padding: 12px;
                    margin: 3px 0px;
                }
            """)
            f_layout = QVBoxLayout(frame)

            # 헤더
            header = QHBoxLayout()
            header.addWidget(QLabel(f"<b>#{i}</b>"))
            scores_text = (
                f"종합: {rec.get('combined_score', 0):.4f} | "
                f"AI: {rec.get('ai_score', 0):.4f} | "
                f"통계: {rec.get('score', 0):.4f}"
            )
            scores_label = QLabel(scores_text)
            scores_label.setStyleSheet("color: #8e44ad; font-size: 12px;")
            header.addStretch()
            header.addWidget(scores_label)
            f_layout.addLayout(header)

            # 번호 공
            balls_layout = QHBoxLayout()
            balls_layout.setSpacing(8)
            for num in rec.get('numbers', []):
                ball = NumberBallWidget(num, size=44)
                balls_layout.addWidget(ball)
            balls_layout.addStretch()
            f_layout.addLayout(balls_layout)

            self.results_layout.addWidget(frame)
