"""회차 정보 페이지"""

import csv
import os
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QWidget, QGroupBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QSpinBox, QLineEdit
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from gui.pages.base_page import BasePage
from gui.widgets.number_ball import get_ball_color


class HistoryPage(BasePage):
    """회차 정보 페이지 - 모든 당첨번호 조회"""

    def __init__(self, parent=None):
        super().__init__("회차 정보", parent)
        self._all_rows = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._create_title_label("📋 회차별 당첨번호"))

        # 검색/필터 바
        filter_bar = QHBoxLayout()
        filter_bar.setContentsMargins(20, 10, 20, 10)

        filter_bar.addWidget(QLabel("회차 검색:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("회차 번호 입력...")
        self.search_input.setStyleSheet("padding: 6px; border: 1px solid #ccc; border-radius: 4px; width: 100px;")
        self.search_input.returnPressed.connect(self._search_round)
        filter_bar.addWidget(self.search_input)

        search_btn = QPushButton("검색")
        search_btn.clicked.connect(self._search_round)
        search_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 7px 15px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #2980b9; }
        """)
        filter_bar.addWidget(search_btn)

        filter_bar.addStretch()

        self.info_label = QLabel("")
        self.info_label.setStyleSheet("color: #7f8c8d;")
        filter_bar.addWidget(self.info_label)

        layout.addLayout(filter_bar)

        # 테이블
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "회차", "날짜", "번호1", "번호2", "번호3",
            "번호4", "번호5", "번호6", "보너스"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ddd;
                gridline-color: #ecf0f1;
                font-size: 13px;
                alternate-background-color: #f8f9fa;
            }
            QTableWidget::item:selected {
                background-color: #d5e8f7;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.table)

    def on_data_loaded(self):
        self._load_all_rounds()

    def _load_all_rounds(self):
        if not self.historical_data:
            return

        self._all_rows = sorted(
            self.historical_data,
            key=lambda x: int(x.get('회차', 0)),
            reverse=True
        )
        self._populate_table(self._all_rows)
        self.info_label.setText(f"총 {len(self._all_rows)}회차")

    def _populate_table(self, rows: list):
        self.table.setRowCount(len(rows))

        for row_idx, row_data in enumerate(rows):
            # 회차
            round_item = QTableWidgetItem(str(row_data.get('회차', '')))
            round_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row_idx, 0, round_item)

            # 날짜
            date_item = QTableWidgetItem(row_data.get('날짜', ''))
            date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row_idx, 1, date_item)

            # 번호 1~6
            for i in range(1, 7):
                num_str = row_data.get(f'번호{i}', '')
                item = QTableWidgetItem(num_str)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                # 번호별 색상
                try:
                    num = int(num_str)
                    color = get_ball_color(num)
                    item.setForeground(color.darker(130))
                    item.setFont(item.font())
                except (ValueError, TypeError):
                    pass

                self.table.setItem(row_idx, i + 1, item)

            # 보너스
            bonus_str = row_data.get('보너스번호', '')
            bonus_item = QTableWidgetItem(bonus_str)
            bonus_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            try:
                bonus_color = get_ball_color(int(bonus_str), is_bonus=True)
                bonus_item.setForeground(bonus_color)
            except (ValueError, TypeError):
                pass
            self.table.setItem(row_idx, 8, bonus_item)

    def _search_round(self):
        query = self.search_input.text().strip()
        if not query:
            self._populate_table(self._all_rows)
            self.info_label.setText(f"총 {len(self._all_rows)}회차")
            return

        try:
            round_no = int(query)
            filtered = [r for r in self._all_rows if int(r.get('회차', 0)) == round_no]
            if filtered:
                self._populate_table(filtered)
                self.info_label.setText(f"{round_no}회차 검색 결과")
            else:
                self.info_label.setText(f"{round_no}회차를 찾을 수 없습니다")
        except ValueError:
            self.info_label.setText("유효한 회차 번호를 입력하세요")
