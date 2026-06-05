"""통계 기반 번호 추천 페이지"""

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QGroupBox, QSpinBox, QFrame,
    QMessageBox
)
from PySide6.QtCore import Qt, QThread, Signal

from gui.pages.base_page import BasePage
from gui.widgets.number_ball import NumberBallWidget


class RecommendWorker(QThread):
    """추천 번호 생성을 백그라운드에서 수행"""
    finished = Signal(list)

    def __init__(self, stat_analyzer, count):
        super().__init__()
        self.stat_analyzer = stat_analyzer
        self.count = count

    def run(self):
        try:
            results = self.stat_analyzer.generate_recommendations(
                num_recommendations=self.count
            )
            self.finished.emit(results or [])
        except Exception as e:
            self.finished.emit([])


class RecommendPage(BasePage):
    """통계 기반 번호 추천 페이지"""

    def __init__(self, parent=None):
        super().__init__("통계 기반 추천", parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._create_title_label("🎯 통계 기반 번호 추천"))

        # 스크롤 영역
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)

        # 설정 섹션
        settings_group = QGroupBox("추천 설정")
        settings_group.setStyleSheet(self._group_style())
        settings_layout = QHBoxLayout(settings_group)

        settings_layout.addWidget(QLabel("추천 조합 수:"))
        self.count_spin = QSpinBox()
        self.count_spin.setRange(1, 20)
        self.count_spin.setValue(5)
        self.count_spin.setStyleSheet("padding: 5px; font-size: 13px;")
        settings_layout.addWidget(self.count_spin)
        settings_layout.addStretch()

        self.recommend_btn = QPushButton("🎯 추천 번호 생성")
        self.recommend_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 10px 25px;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #229954; }
            QPushButton:pressed { background-color: #1e8449; }
        """)
        self.recommend_btn.clicked.connect(self._generate_recommendations)
        settings_layout.addWidget(self.recommend_btn)

        content_layout.addWidget(settings_group)

        # 결과 섹션
        self.results_group = QGroupBox("추천 결과")
        self.results_group.setStyleSheet(self._group_style())
        self.results_layout = QVBoxLayout(self.results_group)
        self.results_layout.addWidget(
            QLabel("추천 번호 생성 버튼을 클릭하세요.")
        )
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

    def _generate_recommendations(self):
        if not self.stat_analyzer:
            QMessageBox.warning(
                self, "경고",
                "분석기가 초기화되지 않았습니다.\n\n"
                "터미널에서 아래 명령어를 실행해주세요:\n"
                "pip install --upgrade matplotlib numpy"
            )
            return

        self.recommend_btn.setEnabled(False)
        self.recommend_btn.setText("생성 중...")

        count = self.count_spin.value()
        self.worker = RecommendWorker(self.stat_analyzer, count)
        self.worker.finished.connect(self._on_results)
        self.worker.start()

    def _on_results(self, results: list):
        self.recommend_btn.setEnabled(True)
        self.recommend_btn.setText("🎯 추천 번호 생성")

        # 기존 결과 제거
        while self.results_layout.count():
            item = self.results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not results:
            self.results_layout.addWidget(QLabel("추천 번호를 생성할 수 없습니다."))
            return

        for i, rec in enumerate(results, 1):
            card = self._create_result_card(i, rec)
            self.results_layout.addWidget(card)

    def _create_result_card(self, index: int, rec: dict) -> QFrame:
        """추천 결과 카드 위젯"""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        layout = QVBoxLayout(frame)

        # 헤더
        header = QHBoxLayout()
        header.addWidget(QLabel(f"<b>조합 #{index}</b>"))
        score_label = QLabel(f"점수: {rec.get('score', 0):.4f}")
        score_label.setStyleSheet("color: #27ae60; font-weight: bold;")
        header.addStretch()
        header.addWidget(score_label)
        layout.addLayout(header)

        # 번호 공
        balls_layout = QHBoxLayout()
        balls_layout.setSpacing(8)
        for num in rec.get('numbers', []):
            ball = NumberBallWidget(num, size=42)
            balls_layout.addWidget(ball)
        balls_layout.addStretch()

        # 저장 버튼
        save_btn = QPushButton("💾 저장")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 6px 15px;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover { background-color: #2980b9; }
        """)
        save_btn.clicked.connect(lambda: self._save_combination(rec.get('numbers', [])))
        balls_layout.addWidget(save_btn)

        layout.addLayout(balls_layout)
        return frame

    def _save_combination(self, numbers: list):
        """조합을 저장"""
        try:
            import sys, os
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            from number_storage import NumberStorage
            storage = NumberStorage()
            if storage.save_combination(numbers, "통계 추천 (GUI)"):
                QMessageBox.information(self, "저장 완료", f"번호 {numbers}가 저장되었습니다.")
            else:
                QMessageBox.warning(self, "저장 실패", "저장에 실패했습니다.")
        except Exception as e:
            QMessageBox.warning(self, "오류", f"저장 중 오류: {e}")
