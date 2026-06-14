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
    """로또당첨번호.csv를 로드하고 분석기를 초기화하는 백그라운드 워커

    2단계로 동작합니다:
      1단계: CSV 로드 + 분석기 초기화 → data_ready 시그널 발생 (UI 즉시 업데이트)
      2단계: 가중치 최적화 완료 → finished 시그널 발생
    """
    data_ready = Signal(object, object, object)  # data, stat_analyzer, comp_analyzer
    finished = Signal(object)  # optimized_weights
    progress = Signal(str)

    def __init__(self, csv_path: str):
        super().__init__()
        self.csv_path = csv_path

    def run(self):
        # 프로젝트 루트를 path에 추가
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

        # ── 1단계: CSV 로드 ──
        self.progress.emit("로또당첨번호.csv 로딩 중...")
        data = self._load_csv(self.csv_path)

        if not data:
            self.progress.emit(
                f"⚠️ 로또당첨번호.csv 로드 실패 (경로: {self.csv_path}, "
                f"존재: {os.path.exists(self.csv_path)})"
            )
            self.data_ready.emit(None, None, None)
            self.finished.emit(None)
            return

        # ── 분석기 초기화 ──
        try:
            self.progress.emit(f"{len(data)}회차 로드 완료. 분석기 초기화 중...")
            from analyzers.statistical_analyzer import StatisticalAnalyzer
            from analyzers.comprehensive_analyzer import ComprehensiveAnalyzer

            stat_analyzer = StatisticalAnalyzer(data)
            comp_analyzer = ComprehensiveAnalyzer(data)
        except Exception as e:
            self.progress.emit(f"⚠️ 분석기 초기화 오류: {e}")
            # 분석기 없이 데이터만이라도 전달
            self.data_ready.emit(data, None, None)
            self.finished.emit(None)
            return

        # 1단계 완료 → UI에 즉시 데이터 전달
        self.data_ready.emit(data, stat_analyzer, comp_analyzer)

        # ── 2단계: 가중치 최적화 (시간이 오래 걸릴 수 있음) ──
        try:
            self.progress.emit(f"{len(data)}회차 기반 가중치 최적화 중... (잠시 대기)")
            from features import WeightOptimizer
            optimizer = WeightOptimizer(data)
            best_weights = optimizer.optimize()
            stat_analyzer.score_weights = best_weights
            self.progress.emit("준비 완료")
            self.finished.emit(best_weights)
        except Exception as e:
            self.progress.emit(f"준비 완료 (기본 가중치 사용: {e})")
            self.finished.emit(None)

    def _load_csv(self, filepath: str) -> list:
        """로또당첨번호.csv를 인코딩 자동 감지로 읽어 dict 리스트로 반환합니다."""
        import csv as _csv

        if not os.path.exists(filepath):
            return []

        encodings = ('utf-8-sig', 'utf-8', 'cp949', 'euc-kr')
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
        """백그라운드에서 로또당첨번호.csv 로드 (2단계: 즉시 표시 → 최적화)"""
        # 여러 경로에서 로또당첨번호.csv 탐색
        csv_path = self._find_csv_file()

        if not csv_path:
            self.status_label.setText("⚠️ 로또당첨번호.csv 파일을 찾을 수 없습니다")
            self.data_status_label.setText("프로그램과 같은 폴더에 로또당첨번호.csv가 필요합니다")
            return

        self.worker = DataLoadWorker(csv_path)
        self.worker.progress.connect(self._on_load_progress)
        self.worker.data_ready.connect(self._on_data_ready)
        self.worker.finished.connect(self._on_optimize_finished)
        self.worker.start()

    def _find_csv_file(self) -> str:
        """로또당첨번호.csv 파일을 여러 경로에서 탐색합니다."""
        candidates = [
            # 1. 현재 작업 디렉터리
            os.path.join(os.getcwd(), '로또당첨번호.csv'),
            # 2. app_desktop.py가 있는 디렉터리 (프로젝트 루트)
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '로또당첨번호.csv'),
            # 3. main_window.py 기준 상위 디렉터리
            os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '로또당첨번호.csv'),
            # 4. sys.argv[0] (실행 스크립트) 기준
            os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), '로또당첨번호.csv') if sys.argv else '',
        ]
        for path in candidates:
            if path and os.path.exists(path):
                return os.path.abspath(path)
        return ""

    def _on_load_progress(self, message: str):
        self.status_label.setText(message)

    def _on_data_ready(self, data, stat_analyzer, comp_analyzer):
        """1단계 완료: 데이터 로드됨 → 즉시 페이지에 전달하여 UI 업데이트"""
        self.historical_data = data
        self.stat_analyzer = stat_analyzer
        self.comp_analyzer = comp_analyzer

        if data:
            self.data_status_label.setText(f"📊 로또당첨번호.csv — {len(data)}회차 로드됨")

            # 각 페이지에 데이터 전달 → 분석 결과 즉시 표시
            for page in self.pages.values():
                page.set_data(data, stat_analyzer, comp_analyzer, None)
        else:
            self.status_label.setText("⚠️ 로또당첨번호.csv 로드 실패")
            self.data_status_label.setText(
                "로또당첨번호.csv 파일이 프로그램과 같은 폴더에 있는지 확인해주세요"
            )

    def _on_optimize_finished(self, weights):
        """2단계 완료: 가중치 최적화됨 → stat_analyzer에 반영"""
        self.optimized_weights = weights

        if weights and self.stat_analyzer:
            self.stat_analyzer.score_weights = weights
            self.status_label.setText("준비 완료")
        elif self.historical_data:
            # 최적화 실패해도 데이터는 있으므로 사용 가능
            self.status_label.setText("준비 완료 (기본 가중치 사용)")

    def _on_nav_changed(self, index: int):
        """네비게이션 메뉴 변경 시 페이지 전환"""
        if 0 <= index < self.page_stack.count():
            self.page_stack.setCurrentIndex(index)
