"""통합 AI 추천 페이지 (마르코프+군집+DL+필터)"""

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


class IntegratedWorker(QThread):
    """통합 AI 추천 실행"""
    finished = Signal(list)
    progress = Signal(str)

    def __init__(self, historical_data):
        super().__init__()
        self.historical_data = historical_data

    def run(self):
        try:
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            if project_root not in sys.path:
                sys.path.insert(0, project_root)

            from analyzers.integrated_recommender import IntegratedRecommender

            self.progress.emit("통합 AI 엔진 초기화 중...")
            recommender = IntegratedRecommender(self.historical_data)
            recommender.initialize()

            self.progress.emit("5개 분석 엔진 앙상블 + 8종 필터 적용 중...")
            results = recommender.generate_recommendations(num_recommendations=5)

            self.progress.emit("완료!")
            self.finished.emit(results or [])
        except Exception as e:
            self.progress.emit(f"오류: {e}")
            self.finished.emit([])


class IntegratedPage(BasePage):
    """통합 AI 추천 페이지"""

    def __init__(self, parent=None):
        super().__init__("통합 AI 추천", parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._create_title_label("🧬 통합 AI 추천 (마르코프+군집+DL+필터)"))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)

        # 설명
        desc_group = QGroupBox("통합 분석 엔진")
        desc_group.setStyleSheet(self._group_style())
        desc_layout = QVBoxLayout(desc_group)
        desc_layout.addWidget(QLabel(
            "• 마르코프 체인: 번호 전이 확률 분석\n"
            "• 군집 패턴: K-means 기반 번호 클러스터링\n"
            "• 딥러닝 예측: LSTM/GBM 기반 확률 모델\n"
            "• 동적 핫/콜드: 시간 가중 빈도 분석\n"
            "• 8종 고급 필터: 역사적 패턴, 합계분포, 연관규칙, 엔트로피 등"
        ))
        content_layout.addWidget(desc_group)

        # 진행 상태
        self.progress_label = QLabel("")
        self.progress_label.setStyleSheet("color: #7f8c8d; font-size: 13px;")
        content_layout.addWidget(self.progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar::chunk { background-color: #e74c3c; border-radius: 4px; }
        """)
        content_layout.addWidget(self.progress_bar)

        # 실행 버튼
        self.run_btn = QPushButton("🧬 통합 AI 추천 실행")
        self.run_btn.setStyleSheet("""
            QPushButton {
                background-color: #c0392b;
                color: white;
                border: none;
                padding: 12px 30px;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #e74c3c; }
        """)
        self.run_btn.clicked.connect(self._run_integrated)
        content_layout.addWidget(self.run_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        # 결과 영역
        self.results_group = QGroupBox("통합 AI 추천 결과")
        self.results_group.setStyleSheet(self._group_style())
        self.results_layout = QVBoxLayout(self.results_group)
        self.results_layout.addWidget(QLabel("통합 AI 추천 실행 버튼을 클릭하세요."))
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

    def _run_integrated(self):
        if not self.historical_data:
            QMessageBox.warning(
                self, "경고",
                "lotto_results.csv 파일을 찾을 수 없습니다.\n"
                "프로그램과 같은 폴더에 파일이 있는지 확인해주세요."
            )
            return

        self.run_btn.setEnabled(False)
        self.progress_bar.setVisible(True)

        self.worker = IntegratedWorker(self.historical_data)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()

    def _on_progress(self, msg: str):
        self.progress_label.setText(msg)

    def _on_finished(self, results: list):
        self.run_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.progress_label.setText("")

        while self.results_layout.count():
            item = self.results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not results:
            self.results_layout.addWidget(QLabel("통합 AI 추천 번호를 생성할 수 없습니다."))
            return

        for i, rec in enumerate(results, 1):
            frame = QFrame()
            frame.setStyleSheet("""
                QFrame {
                    background-color: #fdf2f2;
                    border: 1px solid #f5c6cb;
                    border-radius: 8px;
                    padding: 12px;
                    margin: 3px 0px;
                }
            """)
            f_layout = QVBoxLayout(frame)

            header = QHBoxLayout()
            header.addWidget(QLabel(f"<b>#{i}</b>"))

            # 점수 표시 (rec이 dict인 경우와 list인 경우 모두 처리)
            if isinstance(rec, dict):
                numbers = rec.get('numbers', [])
                score = rec.get('score', 0)
                score_label = QLabel(f"점수: {score:.4f}")
            else:
                numbers = list(rec) if hasattr(rec, '__iter__') else []
                score_label = QLabel("")

            score_label.setStyleSheet("color: #c0392b; font-weight: bold;")
            header.addStretch()
            header.addWidget(score_label)
            f_layout.addLayout(header)

            balls_layout = QHBoxLayout()
            balls_layout.setSpacing(8)
            for num in numbers:
                ball = NumberBallWidget(int(num), size=44)
                balls_layout.addWidget(ball)
            balls_layout.addStretch()
            f_layout.addLayout(balls_layout)

            self.results_layout.addWidget(frame)
