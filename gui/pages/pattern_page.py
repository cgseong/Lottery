"""당첨번호 패턴 시각화 페이지

회차를 선택하면 해당 회차의 당첨번호를 7열 그리드에 표시하고,
번호 순서대로 선으로 연결하여 패턴을 시각적으로 보여줍니다.
"""

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QWidget, QGroupBox, QSpinBox, QScrollArea, QFrame
)
from PySide6.QtCore import Qt

from gui.pages.base_page import BasePage
from gui.widgets.number_pattern import NumberPatternWidget
from gui.widgets.number_ball import NumberBallWidget


class PatternPage(BasePage):
    """당첨번호 패턴 시각화 페이지"""

    def __init__(self, parent=None):
        super().__init__("패턴 시각화", parent)
        self._all_rows = []
        self._max_round = 0
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._create_title_label("🔗 당첨번호 패턴 시각화"))

        # 스크롤 영역
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20, 15, 20, 15)
        content_layout.setSpacing(12)

        # ─── 회차 선택 컨트롤 ───
        control_group = QGroupBox("회차 선택")
        control_group.setStyleSheet(self._group_style())
        ctrl_layout = QHBoxLayout(control_group)

        # 이전 버튼
        self.prev_btn = QPushButton("◀ 이전")
        self.prev_btn.setStyleSheet(self._nav_btn_style())
        self.prev_btn.clicked.connect(self._go_prev)
        ctrl_layout.addWidget(self.prev_btn)

        # 회차 스핀박스
        ctrl_layout.addWidget(QLabel("회차:"))
        self.round_spin = QSpinBox()
        self.round_spin.setRange(1, 9999)
        self.round_spin.setValue(1)
        self.round_spin.setStyleSheet(
            "padding: 6px 12px; font-size: 14px; font-weight: bold; min-width: 80px;")
        self.round_spin.valueChanged.connect(self._on_round_changed)
        ctrl_layout.addWidget(self.round_spin)

        # 다음 버튼
        self.next_btn = QPushButton("다음 ▶")
        self.next_btn.setStyleSheet(self._nav_btn_style())
        self.next_btn.clicked.connect(self._go_next)
        ctrl_layout.addWidget(self.next_btn)

        ctrl_layout.addSpacing(20)

        # 최신 회차 버튼
        self.latest_btn = QPushButton("최신 회차")
        self.latest_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c; color: white;
                border: none; padding: 8px 16px;
                border-radius: 4px; font-size: 12px; font-weight: bold;
            }
            QPushButton:hover { background-color: #c0392b; }
        """)
        self.latest_btn.clicked.connect(self._go_latest)
        ctrl_layout.addWidget(self.latest_btn)

        ctrl_layout.addStretch()

        # 당첨번호 표시 레이블
        self.numbers_label = QLabel("")
        self.numbers_label.setStyleSheet(
            "font-size: 13px; color: #2c3e50; font-weight: bold;")
        ctrl_layout.addWidget(self.numbers_label)

        content_layout.addWidget(control_group)

        # ─── 패턴 시각화 영역 ───
        pattern_frame = QFrame()
        pattern_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 8px;
            }
        """)
        pattern_layout = QVBoxLayout(pattern_frame)
        pattern_layout.setContentsMargins(10, 10, 10, 10)

        self.pattern_widget = NumberPatternWidget()
        self.pattern_widget.setMinimumSize(400, 500)
        pattern_layout.addWidget(self.pattern_widget)

        content_layout.addWidget(pattern_frame)

        # ─── 번호 공 표시 ───
        self.balls_group = QGroupBox("당첨번호")
        self.balls_group.setStyleSheet(self._group_style())
        self.balls_layout = QHBoxLayout(self.balls_group)
        self.balls_layout.setSpacing(8)
        self.balls_layout.addStretch()
        content_layout.addWidget(self.balls_group)

        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)

    def on_data_loaded(self):
        """데이터 로드 후 초기화"""
        if not self.historical_data:
            return

        self._all_rows = sorted(
            self.historical_data,
            key=lambda x: int(x.get('round', 0) or 0)
        )

        if self._all_rows:
            self._max_round = int(self._all_rows[-1].get('round', 0))
            self.round_spin.setRange(
                int(self._all_rows[0].get('round', 1)),
                self._max_round
            )
            # 최신 회차로 이동
            self.round_spin.setValue(self._max_round)

    def _on_round_changed(self, round_no: int):
        """회차 변경 시 패턴 업데이트"""
        row = self._find_round(round_no)
        if row is None:
            self.pattern_widget.clear()
            self.numbers_label.setText(f"{round_no}회 — 데이터 없음")
            self._clear_balls()
            return

        # 번호 추출
        numbers = []
        for i in range(1, 7):
            try:
                n = int(row.get(f'num{i}', 0))
                if 1 <= n <= 45:
                    numbers.append(n)
            except (ValueError, TypeError):
                continue

        # 패턴 위젯 업데이트
        self.pattern_widget.set_numbers(numbers, round_no)

        # 번호 텍스트 표시
        nums_str = ", ".join(str(n) for n in numbers)
        bonus = row.get('bonus', '')
        self.numbers_label.setText(f"{round_no}회: [{nums_str}] + 보너스 {bonus}")

        # 번호 공 위젯 업데이트
        self._update_balls(numbers, bonus)

    def _find_round(self, round_no: int):
        """해당 회차 데이터를 찾습니다."""
        for row in self._all_rows:
            try:
                if int(row.get('round', 0)) == round_no:
                    return row
            except (ValueError, TypeError):
                continue
        return None

    def _go_prev(self):
        """이전 회차로 이동"""
        current = self.round_spin.value()
        if current > self.round_spin.minimum():
            self.round_spin.setValue(current - 1)

    def _go_next(self):
        """다음 회차로 이동"""
        current = self.round_spin.value()
        if current < self.round_spin.maximum():
            self.round_spin.setValue(current + 1)

    def _go_latest(self):
        """최신 회차로 이동"""
        if self._max_round > 0:
            self.round_spin.setValue(self._max_round)

    def _update_balls(self, numbers: list, bonus: str):
        """번호 공 위젯을 업데이트합니다."""
        self._clear_balls()

        for num in numbers:
            ball = NumberBallWidget(num, size=42)
            self.balls_layout.insertWidget(self.balls_layout.count() - 1, ball)

        # 보너스 번호
        try:
            bonus_num = int(bonus)
            if 1 <= bonus_num <= 45:
                # + 레이블
                plus_label = QLabel("+")
                plus_label.setStyleSheet(
                    "font-size: 16px; font-weight: bold; color: #7f8c8d;")
                self.balls_layout.insertWidget(
                    self.balls_layout.count() - 1, plus_label)
                # 보너스 공
                bonus_ball = NumberBallWidget(bonus_num, size=42, is_bonus=True)
                self.balls_layout.insertWidget(
                    self.balls_layout.count() - 1, bonus_ball)
        except (ValueError, TypeError):
            pass

    def _clear_balls(self):
        """번호 공 위젯을 모두 제거합니다."""
        while self.balls_layout.count() > 1:  # stretch 유지
            item = self.balls_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

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

    def _nav_btn_style(self) -> str:
        return """
            QPushButton {
                background-color: #3498db; color: white;
                border: none; padding: 8px 16px;
                border-radius: 4px; font-size: 12px; font-weight: bold;
            }
            QPushButton:hover { background-color: #2980b9; }
            QPushButton:pressed { background-color: #1a6da3; }
        """
