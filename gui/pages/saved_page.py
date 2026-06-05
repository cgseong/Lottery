"""저장된 조합 관리 페이지"""

import os
import sys
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QGroupBox, QFrame,
    QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt

from gui.pages.base_page import BasePage
from gui.widgets.number_ball import NumberBallWidget


class SavedPage(BasePage):
    """저장된 번호 조합 관리 페이지"""

    def __init__(self, parent=None):
        super().__init__("저장된 조합", parent)
        self._storage = None
        self._setup_ui()

    def _get_storage(self):
        if self._storage is None:
            try:
                project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                if project_root not in sys.path:
                    sys.path.insert(0, project_root)
                from number_storage import NumberStorage
                self._storage = NumberStorage()
            except ImportError:
                pass
        return self._storage

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._create_title_label("💾 저장된 조합 관리"))

        # 버튼 바
        btn_bar = QHBoxLayout()
        btn_bar.setContentsMargins(20, 10, 20, 10)

        self.refresh_btn = QPushButton("🔄 새로고침")
        self.refresh_btn.clicked.connect(self._load_combinations)
        self.refresh_btn.setStyleSheet(self._btn_style("#3498db"))
        btn_bar.addWidget(self.refresh_btn)

        self.delete_btn = QPushButton("🗑️ 선택 삭제")
        self.delete_btn.clicked.connect(self._delete_selected)
        self.delete_btn.setStyleSheet(self._btn_style("#e74c3c"))
        btn_bar.addWidget(self.delete_btn)

        self.clear_btn = QPushButton("⚠️ 전체 삭제")
        self.clear_btn.clicked.connect(self._clear_all)
        self.clear_btn.setStyleSheet(self._btn_style("#95a5a6"))
        btn_bar.addWidget(self.clear_btn)

        btn_bar.addStretch()
        layout.addLayout(btn_bar)

        # 테이블
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["번호", "번호 조합", "방법", "날짜"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ddd;
                gridline-color: #ecf0f1;
                font-size: 13px;
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

        # 카운트 레이블
        self.count_label = QLabel("저장된 조합: 0개")
        self.count_label.setStyleSheet("padding: 10px 20px; color: #7f8c8d;")
        layout.addWidget(self.count_label)

    def _btn_style(self, color: str) -> str:
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {color};
                opacity: 0.9;
            }}
        """

    def on_data_loaded(self):
        self._load_combinations()

    def _load_combinations(self):
        storage = self._get_storage()
        if not storage:
            return

        combos = storage.get_all_combinations()
        self.table.setRowCount(len(combos))

        for row, combo in enumerate(combos):
            # 번호
            self.table.setItem(row, 0, QTableWidgetItem(str(row + 1)))

            # 번호 조합
            nums = combo.get('numbers', [])
            nums_str = ", ".join(str(n) for n in nums)
            self.table.setItem(row, 1, QTableWidgetItem(nums_str))

            # 방법
            self.table.setItem(row, 2, QTableWidgetItem(combo.get('method', '')))

            # 날짜
            self.table.setItem(row, 3, QTableWidgetItem(combo.get('date', '')))

        self.count_label.setText(f"저장된 조합: {len(combos)}개")

    def _delete_selected(self):
        rows = set()
        for item in self.table.selectedItems():
            rows.add(item.row())

        if not rows:
            QMessageBox.information(self, "알림", "삭제할 항목을 선택하세요.")
            return

        reply = QMessageBox.question(
            self, "확인", f"{len(rows)}개 항목을 삭제하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            storage = self._get_storage()
            if storage:
                for idx in sorted(rows, reverse=True):
                    storage.delete_combination(idx)
                self._load_combinations()

    def _clear_all(self):
        reply = QMessageBox.question(
            self, "경고", "정말 모든 조합을 삭제하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            storage = self._get_storage()
            if storage:
                storage.clear_all()
                self._load_combinations()
