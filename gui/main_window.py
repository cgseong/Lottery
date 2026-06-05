"""메인 윈도우 - 네비게이션 + 페이지 스택"""

import os
import sys
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QListWidget, QListWidgetItem, QStackedWidget,
    QStatusBar, QLabel, QMessageBox, QSplitter
)
from PySide6.QtCore import Qt, QSize, QThread, Signal
from PySide6.QtGui import QFont, QIcon

# 페이지 임포트
from gui.pages.analysis_page import AnalysisPage
from gui.pages.recommend_page import RecommendPage
from gui.pages.advanced_page import AdvancedPage
from gui.pages.saved_page import SavedPage
from gui.pages.ai_page import AIPage
from gui.pages.comprehensive_page import ComprehensivePage
from gui.pages.integrated_page import IntegratedPage
from gui.pages.history_page import HistoryPage


class DataLoadWorker(QThread):
    """로또당첨번호.csv를 로드하고 분석기를 초기화하는 백그라운드 워커"""
    finished = Signal(object, object, object, object)
    progress = Signal(str)

    def __init__(self, csv_path: str):
        super().__init__()
        self.csv_path = csv_path

    def run(self):
        try:
            # 프로젝트 루트를 path에 추가
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if project_root not in sys.path:
                sys.path.insert(0, project_root)

            import csv
            from analyzers.statistical_analyzer import StatisticalAnalyzer
            from analyzers.comprehensive_analyzer import ComprehensiveAnalyzer
            from features import WeightOptimizer

            self.progress.emit("로또당첨번호.csv 로딩 중...")

            # 로또당첨번호.csv 직접 읽기 (인코딩 자동 감지)
            data = self._load_csv(self.csv_path)

            if not data:
                self.progress.emit("⚠️ 로또당첨번호.csv 파일을 찾을 수 없거나 비어있습니다.")
                self.finished.emit(None, None, None, None)
                return

            self.progress.emit(f"로또당첨번호.csv 로드 완료 ({len(data)}회차). 가중치 최적화 중...")

            stat_analyzer = StatisticalAnalyzer(data)
            comp_analyzer = ComprehensiveAnalyzer(data)

            # 가중치 최적화
            optimizer = WeightOptimizer(data)
            best_weights = optimizer.optimize()
            stat_analyzer.score_weights = best_weights

            self.progress.emit("초기화 완료!")
            self.finished.emit(data, stat_analyzer, comp_analyzer, best_weights)

        except Exception as e:
            self.progress.emit(f"오류: {e}")
            self.finished.emit(None, None, None, None)

    def _load_csv(self, filepath: str) -> list:
        """로또당첨번호.csv를 인코딩 자동 감지로 읽어 리스트로 반환합니다."""
        import csv as _csv

        if not os.path.exists(filepath):
            return []

        encodings = ('utf-8', 'cp949', 'euc-kr')
        for enc in encodings:
            try:
                with open(filepath, 'r', encoding=enc, newline='') as f:
                    reader = _csv.DictReader(f)
                    data = list(reader)
                    if data and any('번호1' in str(k) for k in data[0].keys()):
                        return data
            except (UnicodeDecodeError, Exception):
                continue
        return []


class MainWindow(QMainWindow):
    """로또 번호 추천 시스템 메인 윈도우"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("로또 번호 추천 시스템")
        self.setMinimumSize(1100, 750)
        self.resize(1200, 800)

        # 데이터 상태
        self.historical_data = None
        self.stat_analyzer = None
        self.comp_analyzer = None
        self.optimized_weights = None

        self._setup_ui()
        self._setup_statusbar()
        self._load_data()

    def _setup_ui(self):
        """UI 구성"""
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.page_stack = QStackedWidget()
        self.page_stack.setStyleSheet("background-color: #fafafa;")

        # 페이지들 생성
        self.pages = {}
        page_classes = [
            ("analysis", AnalysisPage),
            ("recommend", RecommendPage),
            ("advanced", AdvancedPage),
            ("saved", SavedPage),
            ("ai", AIPage),
            ("comprehensive", ComprehensivePage),
            ("integrated", IntegratedPage),
            ("history", HistoryPage),
        ]
        for name, PageClass in page_classes:
            page = PageClass()
            self.pages[name] = page
            self.page_stack.addWidget(page)

        # 좌측 네비게이션 (page_stack 생성 후에 생성)
        nav_widget = self._create_navigation()

        # 스플리터로 분리
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(nav_widget)
        splitter.addWidget(self.page_stack)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([220, 980])

        main_layout.addWidget(splitter)

    def _create_navigation(self) -> QWidget:
        """좌측 네비게이션 패널 생성"""
        nav_widget = QWidget()
        nav_widget.setFixedWidth(220)
        nav_widget.setStyleSheet("""
            QWidget {
                background-color: #2c3e50;
            }
        """)

        layout = QVBoxLayout(nav_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 타이틀
        title_label = QLabel("🎰 로또 추천 시스템")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 20px 10px;
                background-color: #1a252f;
            }
        """)
        layout.addWidget(title_label)

        # 메뉴 리스트
        self.nav_list = QListWidget()
        self.nav_list.setStyleSheet("""
            QListWidget {
                background-color: #2c3e50;
                border: none;
                outline: none;
                padding: 5px;
            }
            QListWidget::item {
                color: #ecf0f1;
                padding: 12px 15px;
                border-radius: 6px;
                margin: 2px 5px;
                font-size: 13px;
            }
            QListWidget::item:selected {
                background-color: #3498db;
                color: white;
                font-weight: bold;
            }
            QListWidget::item:hover:!selected {
                background-color: #34495e;
            }
        """)

        menu_items = [
            "📊 당첨번호 분석",
            "🎯 통계 기반 추천",
            "🔧 고급 추천",
            "💾 저장된 조합",
            "🤖 AI 패턴 추천",
            "📈 종합 분석 (10지표)",
            "🧬 통합 AI 추천",
            "📋 회차 정보",
        ]

        for text in menu_items:
            item = QListWidgetItem(text)
            item.setSizeHint(QSize(200, 42))
            self.nav_list.addItem(item)

        self.nav_list.currentRowChanged.connect(self._on_nav_changed)
        self.nav_list.setCurrentRow(0)

        layout.addWidget(self.nav_list)
        layout.addStretch()

        # 하단 정보
        info_label = QLabel("v2.0 Desktop")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                font-size: 11px;
                padding: 10px;
            }
        """)
        layout.addWidget(info_label)

        return nav_widget

    def _setup_statusbar(self):
        """상태바 구성"""
        self.statusBar().setStyleSheet("""
            QStatusBar {
                background-color: #ecf0f1;
                border-top: 1px solid #bdc3c7;
                padding: 3px;
            }
        """)
        self.status_label = QLabel("초기화 중...")
        self.statusBar().addWidget(self.status_label)

        self.data_status_label = QLabel("")
        self.statusBar().addPermanentWidget(self.data_status_label)

    def _load_data(self):
        """백그라운드에서 로또당첨번호.csv 로드"""
        # app_desktop.py가 있는 프로젝트 루트에서 로또당첨번호.csv를 찾음
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        csv_path = os.path.join(project_root, '로또당첨번호.csv')

        # 프로젝트 루트에 없으면 현재 작업 디렉터리에서도 탐색
        if not os.path.exists(csv_path):
            csv_path = os.path.join(os.getcwd(), '로또당첨번호.csv')

        self.worker = DataLoadWorker(csv_path)
        self.worker.progress.connect(self._on_load_progress)
        self.worker.finished.connect(self._on_load_finished)
        self.worker.start()

    def _on_load_progress(self, message: str):
        self.status_label.setText(message)

    def _on_load_finished(self, data, stat_analyzer, comp_analyzer, weights):
        self.historical_data = data
        self.stat_analyzer = stat_analyzer
        self.comp_analyzer = comp_analyzer
        self.optimized_weights = weights

        if data:
            self.status_label.setText("준비 완료")
            self.data_status_label.setText(f"📊 로또당첨번호.csv — {len(data)}회차 로드됨")

            # 각 페이지에 데이터 전달
            for page in self.pages.values():
                page.set_data(data, stat_analyzer, comp_analyzer, weights)
        else:
            self.status_label.setText("⚠️ 로또당첨번호.csv 로드 실패")
            self.data_status_label.setText("로또당첨번호.csv 파일을 확인해주세요")

    def _on_nav_changed(self, index: int):
        """네비게이션 메뉴 변경 시 페이지 전환"""
        if 0 <= index < self.page_stack.count():
            self.page_stack.setCurrentIndex(index)
