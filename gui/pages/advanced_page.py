"""고급 추천 페이지 - 고정번호/제외번호 설정"""

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QGroupBox, QSpinBox, QFrame,
    QMessageBox
)
from PySide6.QtCore import Qt, QThread, Signal

from gui.pages.base_page import BasePage
from gui.widgets.number_ball import NumberBallWidget
from gui.widgets.number_selector import NumberSelectorWidget


class AdvancedRecommendWorker(QThread):
    """고급 추천 생성"""
    finished = Signal(list)

    def __init__(self, stat_analyzer, fixed_numbers, exclude_numbers, count):
        super().__init__()
        self.stat_analyzer = stat_analyzer
        self.fixed_numbers = fixed_numbers
        self.exclude_numbers = exclude_numbers
        self.count = count

    def run(self):
        try:
            results = self.stat_analyzer.generate_recommendations(
                fixed_numbers=set(self.fixed_numbers),
                exclude_numbers=set(self.exclude_numbers),
                num_recommendations=self.count,
            )
            self.finished.emit(results or [])
        except Exception as e:
            self.finished.emit([])


class AdvancedPage(BasePage):
    """고급 추천 페이지 - 고정번호/제외번호 지정"""

    def __init__(self, parent=None):
        super().__init__("고급 추천", parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._create_title_label("🔧 고급 추천 (고정/제외 번호)"))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)

        # 고정번호 선택
        fixed_group = QGroupBox("고정번호 선택 (반드시 포함할 번호)")
        fixed_group.setStyleSheet(self._group_style())
        fixed_layout = QVBoxLayout(fixed_group)
        self.fixed_selector = NumberSelectorWidget(max_selection=5)
        fixed_layout.addWidget(self.fixed_selector)
        content_layout.addWidget(fixed_group)

        # 제외번호 선택
        exclude_group = QGroupBox("제외번호 선택 (포함하지 않을 번호)")
        exclude_group.setStyleSheet(self._group_style())
        exclude_layout = QVBoxLayout(exclude_group)
        self.exclude_selector = NumberSelectorWidget(max_selection=20)
        exclude_layout.addWidget(self.exclude_selector)
        content_layout.addWidget(exclude_group)

        # 추천 설정
        settings_layout = QHBoxLayout()
        settings_layout.addWidget(QLabel("추천 조합 수:"))
        self.count_spin = QSpinBox()
        self.count_spin.setRange(1, 20)
        self.count_spin.setValue(5)
        self.count_spin.setStyleSheet("padding: 5px;")
        settings_layout.addWidget(self.count_spin)
        settings_layout.addStretch()

        self.recommend_btn = QPushButton("🔧 고급 추천 생성")
        self.recommend_btn.setStyleSheet("""
            QPushButton {
                background-color: #e67e22;
                color: white;
                border: none;
                padding: 10px 25px;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #d35400; }
        """)
        self.recommend_btn.clicked.connect(self._generate)
        settings_layout.addWidget(self.recommend_btn)
        content_layout.addLayout(settings_layout)

        # 결과 영역
        self.results_group = QGroupBox("추천 결과")
        self.results_group.setStyleSheet(self._group_style())
        self.results_layout = QVBoxLayout(self.results_group)
        self.results_layout.addWidget(QLabel("고정/제외 번호를 선택한 후 추천 생성을 클릭하세요."))
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

    def _generate(self):
        if not self.stat_analyzer:
            QMessageBox.warning(
                self, "경고",
                "분석기가 초기화되지 않았습니다.\n\n"
                "터미널에서 아래 명령어를 실행해주세요:\n"
                "pip install --upgrade matplotlib numpy"
            )
            return

        fixed = self.fixed_selector.get_selected()
        exclude = self.exclude_selector.get_selected()

        # 고정과 제외 겹침 체크
        overlap = set(fixed) & set(exclude)
        if overlap:
            QMessageBox.warning(self, "경고", f"고정번호와 제외번호가 겹칩니다: {sorted(overlap)}")
            return

        self.recommend_btn.setEnabled(False)
        self.recommend_btn.setText("생성 중...")

        self.worker = AdvancedRecommendWorker(
            self.stat_analyzer, fixed, exclude, self.count_spin.value()
        )
        self.worker.finished.connect(self._on_results)
        self.worker.start()

    def _on_results(self, results: list):
        self.recommend_btn.setEnabled(True)
        self.recommend_btn.setText("🔧 고급 추천 생성")

        while self.results_layout.count():
            item = self.results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not results:
            self.results_layout.addWidget(QLabel("추천 번호를 생성할 수 없습니다."))
            return

        for i, rec in enumerate(results, 1):
            frame = QFrame()
            frame.setStyleSheet("""
                QFrame {
                    background-color: #f8f9fa;
                    border: 1px solid #e9ecef;
                    border-radius: 8px;
                    padding: 10px;
                }
            """)
            f_layout = QHBoxLayout(frame)
            f_layout.addWidget(QLabel(f"<b>#{i}</b>"))

            for num in rec.get('numbers', []):
                ball = NumberBallWidget(num, size=40)
                f_layout.addWidget(ball)

            f_layout.addStretch()
            score_label = QLabel(f"점수: {rec.get('score', 0):.4f}")
            score_label.setStyleSheet("color: #e67e22; font-weight: bold;")
            f_layout.addWidget(score_label)

            self.results_layout.addWidget(frame)
