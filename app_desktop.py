#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""로또 번호 추천 시스템 - PySide6 데스크톱 GUI 진입점"""

import sys
import os

# 프로젝트 루트를 Python path에 추가
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from gui.main_window import MainWindow


def load_stylesheet() -> str:
    """QSS 스타일시트를 로드합니다."""
    qss_path = os.path.join(PROJECT_ROOT, 'gui', 'styles', 'theme.qss')
    if os.path.exists(qss_path):
        with open(qss_path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""


def main():
    # High DPI 지원
    os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")

    app = QApplication(sys.argv)

    # 기본 폰트 설정
    font = QFont("Malgun Gothic", 10)  # Windows 한글 폰트
    # macOS/Linux 대응
    if sys.platform == 'darwin':
        font = QFont("Apple SD Gothic Neo", 12)
    elif sys.platform.startswith('linux'):
        font = QFont("Noto Sans KR", 10)
    app.setFont(font)

    # 스타일시트 적용
    stylesheet = load_stylesheet()
    if stylesheet:
        app.setStyleSheet(stylesheet)

    # 메인 윈도우 생성 및 표시
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
