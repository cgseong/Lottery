"""로또 번호 공 위젯"""

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPainter, QColor, QFont, QLinearGradient, QPen


# 번호 구간별 색상 (동행복권 공식 컬러 기준)
BALL_COLORS = {
    (1, 10): QColor(252, 195, 0),      # 노랑
    (11, 20): QColor(105, 175, 255),    # 파랑
    (21, 30): QColor(255, 100, 100),    # 빨강
    (31, 40): QColor(170, 170, 170),    # 회색
    (41, 45): QColor(100, 210, 100),    # 초록
}

BONUS_COLOR = QColor(180, 100, 220)  # 보너스: 보라


def get_ball_color(number: int, is_bonus: bool = False) -> QColor:
    """번호에 해당하는 공 색상을 반환합니다."""
    if is_bonus:
        return BONUS_COLOR
    for (lo, hi), color in BALL_COLORS.items():
        if lo <= number <= hi:
            return color
    return QColor(170, 170, 170)


class NumberBallWidget(QWidget):
    """로또 번호를 공 형태로 표시하는 위젯"""

    def __init__(self, number: int = 0, size: int = 40,
                 is_bonus: bool = False, parent=None):
        super().__init__(parent)
        self._number = number
        self._size = size
        self._is_bonus = is_bonus
        self.setFixedSize(size, size)

    @property
    def number(self) -> int:
        return self._number

    @number.setter
    def number(self, value: int):
        self._number = value
        self.update()

    @property
    def is_bonus(self) -> bool:
        return self._is_bonus

    @is_bonus.setter
    def is_bonus(self, value: bool):
        self._is_bonus = value
        self.update()

    def paintEvent(self, event):
        if self._number <= 0:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 공 색상
        base_color = get_ball_color(self._number, self._is_bonus)

        # 그라디언트 효과 (입체감)
        rect = QRectF(2, 2, self._size - 4, self._size - 4)
        gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        gradient.setColorAt(0.0, base_color.lighter(140))
        gradient.setColorAt(0.5, base_color)
        gradient.setColorAt(1.0, base_color.darker(120))

        # 테두리
        pen = QPen(base_color.darker(150), 1.5)
        painter.setPen(pen)
        painter.setBrush(gradient)
        painter.drawEllipse(rect)

        # 번호 텍스트
        painter.setPen(Qt.GlobalColor.white)
        font = QFont("Arial", int(self._size * 0.35), QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, str(self._number))

        painter.end()
