"""종합 분석 추천 페이지 (10개 지표)"""

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QGroupBox, QFrame,
    QMessageBox, QProgressBar
)
from PySide6.QtCore import Qt, QThread, Signal

from gui.pages.base_page import BasePage
from gui.widgets.number_ball import NumberBallWidget


class ComprehensiveWorker(QThread):
    """10개 지표 종합 추천 생성"""
    finished = Signal(list)
    progress = Signal(str)

    def __init__(self, comp_analyzer, exclude_numbers=None):
        super().__init__()
        self.comp_analyzer = comp_analyzer
        self.exclude_numbers = exclude_numbers or set()

    def run(self):
        try:
            self.progress.emit("30,000개 후보 조합 분석 중...")
            results = self.comp_analyzer.generate_recommendations(
                num_recommendations=5,
                exclude_numbers=self.exclude_numbers,
            )
            self.finished.emit(results or [])
        except Exception as e:
            self.progress.emit(f"오류: {e}")
            self.finished.emit([])


class ComprehensivePage(BasePage):
    """종합 분석 추천 (10개 지표) 페이지"""

    def __init__(self, parent=None):
        super().__init__("종합 분석", parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._create_title_label("📈 종합 패턴 분석 추천 (10개 지표)"))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)

        # 10개 지표 설명
        desc_group = QGroupBox("10개 분석 지표")
        desc_group.setStyleSheet(self._group_style())
        desc_layout = QVBoxLayout(desc_group)
        indicators = [
            "1. 전체 출현 빈도", "2. 최근 트렌드", "3. 냉각(미출현) 번호",
            "4. 합계 범위 적합도", "5. 홀짝 균형", "6. 구간 분산",
            "7. 연속번호 패턴", "8. 번호 쌍 공동출현",
            "9. 끝수 다양성", "10. 상금 배분 최적화"
        ]
        desc_text = " | ".join(indicators)
        desc_label = QLabel(desc_text)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("font-size: 12px; color: #555;")
        desc_layout.addWidget(desc_label)
        content_layout.addWidget(desc_group)

        # 통계 요약
        self.stats_group = QGroupBox("데이터 요약")
        self.stats_group.setStyleSheet(self._group_style())
        self.stats_layout = QVBoxLayout(self.stats_group)
        self.stats_label = QLabel("데이터 로딩 중...")
        self.stats_layout.addWidget(self.stats_label)
        content_layout.addWidget(self.stats_group)

        # 진행 상태
        self.progress_label = QLabel("")
        self.progress_label.setStyleSheet("color: #7f8c8d;")
        content_layout.addWidget(self.progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        content_layout.addWidget(self.progress_bar)

        # 실행 버튼
        self.run_btn = QPushButton("📈 종합 분석 추천 실행")
        self.run_btn.setStyleSheet("""
            QPushButton {
                background-color: #16a085;
                color: white;
                border: none;
                padding: 12px 30px;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #1abc9c; }
        """)
        self.run_btn.clicked.connect(self._run_analysis)
        content_layout.addWidget(self.run_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        # 결과 영역
        self.results_group = QGroupBox("종합 추천 결과")
        self.results_group.setStyleSheet(self._group_style())
        self.results_layout = QVBoxLayout(self.results_group)
        self.results_layout.addWidget(QLabel("분석 실행 버튼을 클릭하세요."))
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

    def on_data_loaded(self):
        if self.comp_analyzer:
            try:
                stats = self.comp_analyzer.summary_stats()
                if stats:
                    self.stats_label.setText(
                        f"분석 회차: {stats['total_rounds']}회 | "
                        f"합계 평균: {stats['sum_mean']} | "
                        f"표준편차: {stats['sum_std']}\n"
                        f"최다 출현: {stats['top5_freq']} | "
                        f"장기 미출현: {stats['coldest5']}"
                    )
                else:
                    self.stats_label.setText("통계 요약을 생성할 수 없습니다.")
            except Exception:
                self.stats_label.setText("데이터 로드됨")

    def _run_analysis(self):
        if not self.comp_analyzer:
            QMessageBox.warning(self, "경고", "데이터가 로드되지 않았습니다.")
            return

        self.run_btn.setEnabled(False)
        self.progress_bar.setVisible(True)

        self.worker = ComprehensiveWorker(self.comp_analyzer)
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
            self.results_layout.addWidget(QLabel("추천 조합을 생성할 수 없습니다."))
            return

        for i, rec in enumerate(results, 1):
            frame = QFrame()
            frame.setStyleSheet("""
                QFrame {
                    background-color: #f0faf7;
                    border: 1px solid #b2dfdb;
                    border-radius: 8px;
                    padding: 12px;
                    margin: 3px 0px;
                }
            """)
            f_layout = QVBoxLayout(frame)

            # 헤더
            header = QHBoxLayout()
            header.addWidget(QLabel(f"<b>#{i}</b>"))
            score_label = QLabel(f"종합 점수: {rec.get('score', 0):.4f}")
            score_label.setStyleSheet("color: #16a085; font-weight: bold;")
            header.addStretch()
            header.addWidget(score_label)
            f_layout.addLayout(header)

            # 번호 공
            balls_layout = QHBoxLayout()
            balls_layout.setSpacing(8)
            for num in rec.get('numbers', []):
                ball = NumberBallWidget(num, size=44)
                balls_layout.addWidget(ball)
            balls_layout.addStretch()
            f_layout.addLayout(balls_layout)

            # 지표별 상세 (있는 경우)
            if self.comp_analyzer and rec.get('numbers'):
                try:
                    report = self.comp_analyzer.indicator_report(rec['numbers'])
                    if report:
                        indicators_layout = QHBoxLayout()
                        for label, val in list(report.items())[:5]:
                            ind_label = QLabel(f"{label}: {val:.2f}")
                            ind_label.setStyleSheet("font-size: 11px; color: #555; padding: 2px 6px; background: #e8f5e9; border-radius: 3px;")
                            indicators_layout.addWidget(ind_label)
                        indicators_layout.addStretch()
                        f_layout.addLayout(indicators_layout)
                except Exception:
                    pass

            self.results_layout.addWidget(frame)
