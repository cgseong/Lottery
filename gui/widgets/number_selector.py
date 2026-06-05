"""1~45 번호 선택 그리드 위젯"""

from PySide6.QtWidgets import (
    QWidget, QGridLayout, QPushButton, QHBoxLayout, QLabel, QVBoxLayout
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QColor

from .number_ball import get_ball_color


class NumberSelectorWidget(QWidget):
    """1~45 번호를 그리드로 표시하고 선택할 수 있는 위젯

    Signals:
        selection_changed(list): 선택된 번호 리스트가 변경될 때 발생
    """

    selection_changed = Signal(list)

    def __init__(self, max_selection: int = 6, parent=None):
        super().__init__(parent)
        self._max_selection = max_selection
        self._selected: set = set()
        self._buttons: dict = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 선택 상태 표시
        self._status_label = QLabel(f"선택: 0/{self._max_selection}")
        self._status_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout.addWidget(self._status_label)

        # 번호 그리드 (9열 x 5행)
        grid = QGridLayout()
        grid.setSpacing(4)

        for num in range(1, 46):
            row = (num - 1) // 9
            col = (num - 1) % 9
            btn = QPushButton(str(num))
            btn.setFixedSize(38, 38)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, n=num: self._on_click(n, checked))
            self._buttons[num] = btn
            self._update_button_style(btn, num, False)
            grid.addWidget(btn, row, col)

        layout.addLayout(grid)

        # 초기화 버튼
        btn_layout = QHBoxLayout()
        clear_btn = QPushButton("전체 해제")
        clear_btn.clicked.connect(self.clear_selection)
        clear_btn.setStyleSheet("padding: 5px 15px;")
        btn_layout.addStretch()
        btn_layout.addWidget(clear_btn)
        layout.addLayout(btn_layout)

    def _on_click(self, number: int, checked: bool):
        if checked:
            if len(self._selected) >= self._max_selection:
                # 최대 선택 수 초과 시 체크 해제
                self._buttons[number].setChecked(False)
                return
            self._selected.add(number)
        else:
            self._selected.discard(number)

        self._update_button_style(self._buttons[number], number, number in self._selected)
        self._status_label.setText(f"선택: {len(self._selected)}/{self._max_selection}")
        self.selection_changed.emit(sorted(self._selected))

    def _update_button_style(self, btn: QPushButton, number: int, selected: bool):
        color = get_ball_color(number)
        if selected:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color.name()};
                    color: white;
                    border: 2px solid {color.darker(130).name()};
                    border-radius: 19px;
                    font-weight: bold;
                    font-size: 12px;
                }}
            """)
        else:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: #f0f0f0;
                    color: #333;
                    border: 1px solid #ccc;
                    border-radius: 19px;
                    font-size: 12px;
                }}
                QPushButton:hover {{
                    background-color: {color.lighter(160).name()};
                    border: 1px solid {color.name()};
                }}
            """)

    def get_selected(self) -> list:
        """현재 선택된 번호 리스트를 반환합니다."""
        return sorted(self._selected)

    def set_selected(self, numbers: list):
        """번호를 프로그래밍적으로 선택합니다."""
        self.clear_selection()
        for num in numbers[:self._max_selection]:
            if 1 <= num <= 45:
                self._selected.add(num)
                self._buttons[num].setChecked(True)
                self._update_button_style(self._buttons[num], num, True)
        self._status_label.setText(f"선택: {len(self._selected)}/{self._max_selection}")
        self.selection_changed.emit(sorted(self._selected))

    def clear_selection(self):
        """모든 선택을 해제합니다."""
        for num in list(self._selected):
            self._buttons[num].setChecked(False)
            self._update_button_style(self._buttons[num], num, False)
        self._selected.clear()
        self._status_label.setText(f"선택: 0/{self._max_selection}")
        self.selection_changed.emit([])

    def set_max_selection(self, max_sel: int):
        """최대 선택 수를 변경합니다."""
        self._max_selection = max_sel
        self._status_label.setText(f"선택: {len(self._selected)}/{self._max_selection}")
