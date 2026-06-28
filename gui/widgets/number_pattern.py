"""당첨번호 패턴 시각화 위젯

1~45 번호를 7열 그리드에 배치하고, 당첨번호 위치에 타원 마커를 표시하며
번호 순서대로 직선으로 연결하는 시각화 위젯입니다.
"""

from PySide6.QtWidgets import QWidget, QSizePolicy
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import (
    QPainter, QColor, QFont, QPen, QBrush, QPainterPath
)


# 그리드 설정: 7열 × 7행 (1~45, 마지막 행은 3칸만 사용)
_COLS = 7
_ROWS = 7  # ceil(45/7) = 7
_TOTAL_NUMBERS = 45


class NumberPatternWidget(QWidget):
    """당첨번호 패턴을 시각적으로 표시하는 위젯.

    1~45 번호를 7열 그리드에 배치하고,
    당첨번호 위치에 타원 마커를 표시하고 순서대로 선으로 연결합니다.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._winning_numbers: list = []  # 당첨번호 (순서 유지)
        self._round_number: int = 0

        self.setMinimumSize(350, 450)
        self.setSizePolicy(QSizePolicy.Policy.Expanding,
                           QSizePolicy.Policy.Expanding)

        # 색상 설정
        self._bg_color = QColor(255, 255, 255)
        self._grid_text_color = QColor(200, 60, 60)  # 빨간 계열 (이미지 참고)
        self._grid_border_color = QColor(200, 60, 60)
        self._marker_color = QColor(60, 60, 60, 200)  # 어두운 타원 마커
        self._line_color = QColor(30, 30, 30)  # 연결선 색상

    def set_numbers(self, numbers: list, round_number: int = 0):
        """당첨번호를 설정합니다.

        Args:
            numbers: 당첨번호 리스트 (6개, 순서 유지)
            round_number: 회차 번호
        """
        self._winning_numbers = list(numbers)
        self._round_number = round_number
        self.update()

    def clear(self):
        """당첨번호를 초기화합니다."""
        self._winning_numbers = []
        self._round_number = 0
        self.update()

    def _get_cell_center(self, number: int) -> QPointF:
        """번호의 그리드 셀 중심 좌표를 반환합니다."""
        idx = number - 1  # 0-based index
        row = idx // _COLS
        col = idx % _COLS

        # 위젯 크기 기반 셀 크기 계산
        margin_x = 30
        margin_y = 60  # 상단 여백 (제목 공간)
        available_w = self.width() - margin_x * 2
        available_h = self.height() - margin_y - 30  # 하단 여백

        cell_w = available_w / _COLS
        cell_h = available_h / _ROWS

        x = margin_x + col * cell_w + cell_w / 2
        y = margin_y + row * cell_h + cell_h / 2

        return QPointF(x, y)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 배경
        painter.fillRect(self.rect(), self._bg_color)

        # 제목
        self._draw_title(painter)

        # 그리드 (모든 번호 표시)
        self._draw_grid(painter)

        # 당첨번호가 있으면 마커와 연결선 그리기
        if self._winning_numbers:
            self._draw_connections(painter)
            self._draw_markers(painter)

        painter.end()

    def _draw_title(self, painter: QPainter):
        """제목을 그립니다."""
        title_font = QFont("맑은 고딕", 14, QFont.Weight.Bold)
        painter.setFont(title_font)
        painter.setPen(QColor(30, 30, 30))

        title_text = "당첨번호 패턴"
        if self._round_number > 0:
            title_text = f"{self._round_number}회 당첨번호 패턴"

        title_rect = QRectF(0, 5, self.width(), 40)
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignCenter, title_text)

    def _draw_grid(self, painter: QPainter):
        """1~45 번호 그리드를 그립니다."""
        margin_x = 30
        margin_y = 60
        available_w = self.width() - margin_x * 2
        available_h = self.height() - margin_y - 30

        cell_w = available_w / _COLS
        cell_h = available_h / _ROWS

        # 번호 텍스트 폰트
        num_font = QFont("맑은 고딕", 11, QFont.Weight.Bold)
        painter.setFont(num_font)

        for number in range(1, _TOTAL_NUMBERS + 1):
            idx = number - 1
            row = idx // _COLS
            col = idx % _COLS

            x = margin_x + col * cell_w
            y = margin_y + row * cell_h

            cell_rect = QRectF(x + 2, y + 2, cell_w - 4, cell_h - 4)

            # 셀 테두리 (빨간 점선 사각형)
            pen = QPen(self._grid_border_color, 1.5, Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(cell_rect)

            # 번호 텍스트 (하단)
            painter.setPen(self._grid_text_color)
            text_rect = QRectF(x, y + cell_h * 0.4, cell_w, cell_h * 0.6)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, str(number))

    def _draw_connections(self, painter: QPainter):
        """당첨번호를 순서대로 직선으로 연결합니다."""
        if len(self._winning_numbers) < 2:
            return

        # 연결선 스타일
        pen = QPen(self._line_color, 2.5, Qt.PenStyle.SolidLine)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)

        # 번호 순서대로 연결
        for i in range(len(self._winning_numbers) - 1):
            from_num = self._winning_numbers[i]
            to_num = self._winning_numbers[i + 1]

            if not (1 <= from_num <= _TOTAL_NUMBERS and 1 <= to_num <= _TOTAL_NUMBERS):
                continue

            p1 = self._get_cell_center(from_num)
            p2 = self._get_cell_center(to_num)
            painter.drawLine(p1, p2)

    def _draw_markers(self, painter: QPainter):
        """당첨번호 위치에 타원 마커를 그립니다."""
        margin_x = 30
        margin_y = 60
        available_w = self.width() - margin_x * 2
        available_h = self.height() - margin_y - 30

        cell_w = available_w / _COLS
        cell_h = available_h / _ROWS

        marker_w = min(cell_w, cell_h) * 0.45
        marker_h = min(cell_w, cell_h) * 0.65

        for number in self._winning_numbers:
            if not (1 <= number <= _TOTAL_NUMBERS):
                continue

            center = self._get_cell_center(number)

            # 타원 마커 (어두운 색 채움)
            painter.setPen(QPen(QColor(20, 20, 20), 1.5))
            painter.setBrush(QBrush(self._marker_color))

            marker_rect = QRectF(
                center.x() - marker_w / 2,
                center.y() - marker_h / 2,
                marker_w,
                marker_h
            )
            painter.drawEllipse(marker_rect)
