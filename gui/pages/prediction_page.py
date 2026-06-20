"""다음 회차 패턴 예측 페이지

역대 당첨번호의 번호별 발생 패턴(주기/갭/스트릭/페어링/모멘텀)을
분석하여 다음 회차 예상 번호를 추천합니다.
"""

import os
import sys
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QGroupBox, QFrame,
    QMessageBox, QProgressBar, QGridLayout
)
from PySide6.QtCore import Qt, QThread, Signal

from gui.pages.base_page import BasePage
from gui.widgets.number_ball import NumberBallWidget



class PredictionWorker(QThread):
    """패턴 분석 및 예측을 백그라운드에서 수행"""
    finished = Signal(dict)
    progress = Signal(str)

    def __init__(self, historical_data):
        super().__init__()
        self.historical_data = historical_data

    def run(self):
        try:
            project_root = os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            if project_root not in sys.path:
                sys.path.insert(0, project_root)

            from analyzers.next_draw_predictor import NextDrawPredictor

            self.progress.emit("패턴 분석 엔진 초기화 중...")
            predictor = NextDrawPredictor(self.historical_data)

            self.progress.emit("5개 지표 분석 중 (주기/갭/스트릭/페어링/모멘텀)...")
            predictor.analyze()

            self.progress.emit("다음 회차 예측 번호 생성 중...")
            predictions = predictor.predict_next_draw(num_sets=5)
            report = predictor.get_analysis_report()
            indicator_scores = predictor.get_indicator_scores()

            self.progress.emit("완료!")
            self.finished.emit({
                'predictions': predictions,
                'report': report,
                'indicators': indicator_scores,
            })
        except Exception as e:
            self.progress.emit(f"오류: {e}")
            self.finished.emit({})



class PredictionPage(BasePage):
    """다음 회차 패턴 예측 페이지"""

    def __init__(self, parent=None):
        super().__init__("패턴 예측", parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._create_title_label(
            "🔮 다음 회차 패턴 예측 (주기+갭+스트릭+페어링+모멘텀)"))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)

        # 설명 그룹
        desc_group = QGroupBox("분석 알고리즘")
        desc_group.setStyleSheet(self._group_style())
        desc_layout = QVBoxLayout(desc_group)
        desc_layout.addWidget(QLabel(
            "역대 당첨번호의 번호별 발생 패턴을 5개 지표로 분석합니다:\n\n"
            "  1. 주기(Cycle) 분석: 자기상관(ACF) 기반 번호별 출현 주기 탐지\n"
            "  2. 갭(Gap) 예측: 미출현 기간 vs 평균 간격 비교로 출현 예정 번호 판단\n"
            "  3. 스트릭(Streak) 분석: 연속 출현/미출현 길이 기반 추세 예측\n"
            "  4. 조건부 페어링: 최근 번호 기반 동반 출현 확률 계산\n"
            "  5. 모멘텀 웨이브: 단기/중기/장기 이동평균 크로스오버 분석\n\n"
            "5개 지표를 가중 앙상블(20/25/15/20/20%)로 합산하여 최종 예측합니다."
        ))
        content_layout.addWidget(desc_group)

        # 진행 상태
        self.progress_label = QLabel("")
        self.progress_label.setStyleSheet(
            "color: #7f8c8d; font-size: 13px; padding: 5px;")
        content_layout.addWidget(self.progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar { border: 1px solid #bdc3c7; border-radius: 5px;
                           text-align: center; height: 20px; }
            QProgressBar::chunk { background-color: #e67e22; border-radius: 4px; }
        """)
        content_layout.addWidget(self.progress_bar)

        # 실행 버튼
        self.run_btn = QPushButton("🔮 패턴 예측 실행")
        self.run_btn.setStyleSheet("""
            QPushButton {
                background-color: #e67e22;
                color: white; border: none;
                padding: 12px 30px; border-radius: 5px;
                font-size: 14px; font-weight: bold;
            }
            QPushButton:hover { background-color: #d35400; }
            QPushButton:pressed { background-color: #ba4a00; }
        """)
        self.run_btn.clicked.connect(self._run_prediction)
        content_layout.addWidget(self.run_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        # 지표별 분석 결과 영역
        self.indicators_group = QGroupBox("지표별 상위 번호")
        self.indicators_group.setStyleSheet(self._group_style())
        self.indicators_layout = QVBoxLayout(self.indicators_group)
        self.indicators_layout.addWidget(QLabel("예측 실행 후 지표별 분석 결과가 표시됩니다."))
        content_layout.addWidget(self.indicators_group)

        # 예측 결과 영역
        self.results_group = QGroupBox("다음 회차 예측 번호")
        self.results_group.setStyleSheet(self._group_style())
        self.results_layout = QVBoxLayout(self.results_group)
        self.results_layout.addWidget(QLabel("패턴 예측 실행 버튼을 클릭하세요."))
        content_layout.addWidget(self.results_group)

        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)


    def _group_style(self) -> str:
        return """
            QGroupBox {
                font-size: 14px; font-weight: bold; color: #2c3e50;
                border: 1px solid #ddd; border-radius: 8px;
                margin-top: 10px; padding-top: 15px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin; left: 15px; padding: 0 8px;
            }
        """

    def _run_prediction(self):
        if not self.historical_data:
            QMessageBox.warning(
                self, "경고",
                "lotto_results.csv 파일을 찾을 수 없습니다.\n"
                "프로그램과 같은 폴더에 파일이 있는지 확인해주세요."
            )
            return

        self.run_btn.setEnabled(False)
        self.progress_bar.setVisible(True)

        self.worker = PredictionWorker(self.historical_data)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()

    def _on_progress(self, msg: str):
        self.progress_label.setText(msg)

    def _on_finished(self, result: dict):
        self.run_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.progress_label.setText("")

        if not result:
            self._clear_layout(self.results_layout)
            self.results_layout.addWidget(QLabel("예측 번호를 생성할 수 없습니다."))
            return

        # 지표별 분석 결과 표시
        self._display_indicators(result.get('indicators', {}),
                                 result.get('report', {}))

        # 예측 결과 표시
        self._display_predictions(result.get('predictions', []),
                                  result.get('report', {}))


    def _display_indicators(self, indicators: dict, report: dict):
        """지표별 상위 번호를 표시합니다."""
        self._clear_layout(self.indicators_layout)

        # 최근 회차 정보
        if report.get('latest_draw'):
            info_label = QLabel(
                f"분석 기준: {report.get('total_draws', 0)}회차 | "
                f"최신 회차: {report.get('latest_round', '?')}회 "
                f"{report.get('latest_draw', [])}"
            )
            info_label.setStyleSheet(
                "color: #2c3e50; font-size: 12px; padding: 5px; font-weight: normal;")
            self.indicators_layout.addWidget(info_label)

        # 지표별 색상
        indicator_colors = {
            'cycle': ('#3498db', '주기 분석 (ACF)'),
            'gap': ('#e74c3c', '갭 예측 (미출현)'),
            'streak': ('#27ae60', '스트릭 분석'),
            'pairing': ('#9b59b6', '페어링 분석'),
            'momentum': ('#f39c12', '모멘텀 웨이브'),
        }

        grid_frame = QFrame()
        grid_frame.setStyleSheet("QFrame { background: transparent; }")
        grid_layout = QGridLayout(grid_frame)
        grid_layout.setSpacing(8)

        for col, (key, info) in enumerate(indicators.items()):
            color, display_name = indicator_colors.get(key, ('#7f8c8d', key))
            name = info.get('name', display_name)
            top_numbers = info.get('top_numbers', [])

            # 지표 헤더
            header = QLabel(f"<b>{name}</b>")
            header.setStyleSheet(f"color: {color}; font-size: 12px;")
            header.setAlignment(Qt.AlignmentFlag.AlignCenter)
            grid_layout.addWidget(header, 0, col)

            # 상위 5개 번호 표시
            nums_widget = QWidget()
            nums_layout = QVBoxLayout(nums_widget)
            nums_layout.setContentsMargins(2, 2, 2, 2)
            nums_layout.setSpacing(2)

            for num, score in top_numbers[:5]:
                row_w = QWidget()
                row_l = QHBoxLayout(row_w)
                row_l.setContentsMargins(0, 0, 0, 0)
                row_l.setSpacing(4)

                ball = NumberBallWidget(num, size=28)
                row_l.addWidget(ball)

                score_lbl = QLabel(f"{score:.3f}")
                score_lbl.setStyleSheet(
                    "color: #555; font-size: 11px; font-weight: normal;")
                row_l.addWidget(score_lbl)
                row_l.addStretch()

                nums_layout.addWidget(row_w)

            grid_layout.addWidget(nums_widget, 1, col)

        self.indicators_layout.addWidget(grid_frame)


    def _display_predictions(self, predictions: list, report: dict):
        """예측 결과를 표시합니다."""
        self._clear_layout(self.results_layout)

        if not predictions:
            self.results_layout.addWidget(QLabel("예측 번호를 생성할 수 없습니다."))
            return

        # 다음 회차 번호 표시
        next_round = report.get('latest_round', 0) + 1
        header_label = QLabel(f"<b>{next_round}회 예측 번호 (상위 5조합)</b>")
        header_label.setStyleSheet("font-size: 14px; color: #2c3e50; padding: 5px;")
        self.results_layout.addWidget(header_label)

        for i, pred in enumerate(predictions, 1):
            frame = QFrame()
            frame.setStyleSheet("""
                QFrame {
                    background-color: #fef9f0;
                    border: 1px solid #f5d7a8;
                    border-radius: 8px;
                    padding: 12px;
                    margin: 3px 0px;
                }
            """)
            f_layout = QVBoxLayout(frame)

            # 헤더: 순위 + 점수
            header = QHBoxLayout()
            rank_label = QLabel(f"<b>#{i}</b>")
            header.addWidget(rank_label)

            score = pred.get('score', 0)
            score_label = QLabel(f"종합 점수: {score:.4f}")
            score_label.setStyleSheet("color: #e67e22; font-weight: bold;")
            header.addStretch()
            header.addWidget(score_label)
            f_layout.addLayout(header)

            # 번호 공
            balls_layout = QHBoxLayout()
            balls_layout.setSpacing(8)
            for num in pred.get('numbers', []):
                ball = NumberBallWidget(int(num), size=44)
                balls_layout.addWidget(ball)
            balls_layout.addStretch()

            # 저장 버튼
            save_btn = QPushButton("💾 저장")
            save_btn.setStyleSheet("""
                QPushButton {
                    background-color: #3498db; color: white;
                    border: none; padding: 6px 15px;
                    border-radius: 4px; font-size: 12px;
                }
                QPushButton:hover { background-color: #2980b9; }
            """)
            numbers = pred.get('numbers', [])
            save_btn.clicked.connect(
                lambda checked, nums=numbers: self._save_combination(nums))
            balls_layout.addWidget(save_btn)
            f_layout.addLayout(balls_layout)

            # 지표별 점수 분해
            breakdown = pred.get('indicator_breakdown', {})
            if breakdown:
                detail_parts = []
                labels = {'cycle': '주기', 'gap': '갭', 'streak': '스트릭',
                          'pairing': '페어링', 'momentum': '모멘텀'}
                for key, label in labels.items():
                    if key in breakdown:
                        detail_parts.append(f"{label}:{breakdown[key]:.3f}")
                detail_text = " | ".join(detail_parts)
                detail_label = QLabel(detail_text)
                detail_label.setStyleSheet(
                    "color: #7f8c8d; font-size: 11px; font-weight: normal;")
                f_layout.addWidget(detail_label)

            self.results_layout.addWidget(frame)


    def _save_combination(self, numbers: list):
        """조합을 저장합니다."""
        try:
            project_root = os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            from number_storage import NumberStorage
            storage = NumberStorage()
            if storage.save_combination(numbers, "패턴 예측 (GUI)"):
                QMessageBox.information(
                    self, "저장 완료", f"번호 {numbers}가 저장되었습니다.")
            else:
                QMessageBox.warning(self, "저장 실패", "저장에 실패했습니다.")
        except Exception as e:
            QMessageBox.warning(self, "오류", f"저장 중 오류: {e}")

    def _clear_layout(self, layout):
        """레이아웃의 모든 위젯을 제거합니다."""
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
