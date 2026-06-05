"""페이지 기본 클래스"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt


class BasePage(QWidget):
    """모든 페이지의 기본 클래스"""

    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self._title = title
        self.historical_data = None
        self.stat_analyzer = None
        self.comp_analyzer = None
        self.optimized_weights = None
        self._data_loaded = False

    def set_data(self, historical_data, stat_analyzer, comp_analyzer, weights):
        """메인 윈도우에서 데이터를 전달받습니다."""
        self.historical_data = historical_data
        self.stat_analyzer = stat_analyzer
        self.comp_analyzer = comp_analyzer
        self.optimized_weights = weights
        self._data_loaded = True
        self.on_data_loaded()

    def on_data_loaded(self):
        """데이터 로드 후 호출됩니다. 서브클래스에서 오버라이드하세요."""
        pass

    def _create_title_label(self, text: str) -> QLabel:
        """페이지 타이틀 레이블을 생성합니다."""
        label = QLabel(text)
        label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #2c3e50;
                padding: 15px 20px;
                background-color: white;
                border-bottom: 2px solid #3498db;
            }
        """)
        return label

    def _create_section_label(self, text: str) -> QLabel:
        """섹션 제목 레이블을 생성합니다."""
        label = QLabel(text)
        label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #34495e;
                padding: 8px 0px;
            }
        """)
        return label
