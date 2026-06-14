"""당첨번호 분석 페이지"""

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QGroupBox, QGridLayout, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from gui.pages.base_page import BasePage
from gui.widgets.number_ball import NumberBallWidget


class AnalysisPage(BasePage):
    """당첨번호 분석 페이지 - 빈도, 합계, 홀짝, 구간, 연속 통계"""

    def __init__(self, parent=None):
        super().__init__("당첨번호 분석", parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 타이틀
        layout.addWidget(self._create_title_label("📊 당첨번호 분석"))

        # 스크롤 영역
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        content = QWidget()
        self.content_layout = QVBoxLayout(content)
        self.content_layout.setContentsMargins(20, 20, 20, 20)
        self.content_layout.setSpacing(15)

        # 최신 당첨번호 섹션
        self.latest_group = self._create_latest_section()
        self.content_layout.addWidget(self.latest_group)

        # Hot/Cold 분석 섹션
        self.hotcold_group = self._create_hotcold_section()
        self.content_layout.addWidget(self.hotcold_group)

        # 빈도 분석 섹션
        self.freq_group = self._create_frequency_section()
        self.content_layout.addWidget(self.freq_group)

        # 합계/홀짝/구간 통계
        self.stats_group = self._create_stats_section()
        self.content_layout.addWidget(self.stats_group)

        # 연속번호 패턴
        self.consec_group = self._create_consecutive_section()
        self.content_layout.addWidget(self.consec_group)

        self.content_layout.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll)

        # 분석 실행 버튼
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(20, 10, 20, 10)
        self.analyze_btn = QPushButton("🔄 분석 새로고침")
        self.analyze_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px 25px;
                border-radius: 5px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #2980b9; }
            QPushButton:pressed { background-color: #21618c; }
        """)
        self.analyze_btn.clicked.connect(self._run_analysis)
        btn_layout.addStretch()
        btn_layout.addWidget(self.analyze_btn)
        layout.addLayout(btn_layout)

    def _create_latest_section(self) -> QGroupBox:
        group = QGroupBox("최신 당첨번호")
        group.setStyleSheet(self._group_style())
        layout = QVBoxLayout(group)

        self.latest_round_label = QLabel("데이터 로딩 중...")
        self.latest_round_label.setStyleSheet("font-size: 13px; color: #7f8c8d;")
        layout.addWidget(self.latest_round_label)

        self.balls_layout = QHBoxLayout()
        self.balls_layout.setSpacing(8)
        self.balls_layout.addStretch()
        layout.addLayout(self.balls_layout)

        return group

    def _create_hotcold_section(self) -> QGroupBox:
        group = QGroupBox("Hot & Cold 번호 (최근 20회)")
        group.setStyleSheet(self._group_style())
        layout = QVBoxLayout(group)

        self.hot_label = QLabel("")
        self.hot_label.setWordWrap(True)
        self.hot_label.setStyleSheet("font-size: 13px;")
        layout.addWidget(self.hot_label)

        self.cold_label = QLabel("")
        self.cold_label.setWordWrap(True)
        self.cold_label.setStyleSheet("font-size: 13px;")
        layout.addWidget(self.cold_label)

        return group

    def _create_frequency_section(self) -> QGroupBox:
        group = QGroupBox("출현 빈도 분석")
        group.setStyleSheet(self._group_style())
        layout = QVBoxLayout(group)

        self.most_common_label = QLabel("")
        self.most_common_label.setWordWrap(True)
        layout.addWidget(self.most_common_label)

        self.least_common_label = QLabel("")
        self.least_common_label.setWordWrap(True)
        layout.addWidget(self.least_common_label)

        return group

    def _create_stats_section(self) -> QGroupBox:
        group = QGroupBox("합계 / 홀짝 / 구간 통계")
        group.setStyleSheet(self._group_style())
        grid = QGridLayout(group)

        self.sum_label = QLabel("")
        self.odd_even_label = QLabel("")
        self.section_label = QLabel("")

        grid.addWidget(QLabel("<b>합계:</b>"), 0, 0)
        grid.addWidget(self.sum_label, 0, 1)
        grid.addWidget(QLabel("<b>홀짝:</b>"), 1, 0)
        grid.addWidget(self.odd_even_label, 1, 1)
        grid.addWidget(QLabel("<b>구간분포:</b>"), 2, 0)
        grid.addWidget(self.section_label, 2, 1)

        return group

    def _create_consecutive_section(self) -> QGroupBox:
        group = QGroupBox("연속번호 패턴")
        group.setStyleSheet(self._group_style())
        layout = QVBoxLayout(group)

        self.consec_label = QLabel("")
        self.consec_label.setWordWrap(True)
        layout.addWidget(self.consec_label)

        return group

    def _group_style(self) -> str:
        return """
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                color: #2c3e50;
                border: 1px solid #ddd;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px;
            }
        """

    def on_data_loaded(self):
        self._run_analysis()

    def _run_analysis(self):
        if not self.historical_data:
            self.latest_round_label.setText("lotto_results.csv 파일을 확인해주세요.")
            return

        # ── 최신 당첨번호 (CSV 데이터에서 직접 읽기) ──
        sorted_data = sorted(
            self.historical_data,
            key=lambda x: int(x.get('round', 0)),
            reverse=True
        )

        self._display_latest_numbers(sorted_data)
        self._display_basic_stats(sorted_data)

        # stat_analyzer가 있으면 고급 분석도 표시
        if self.stat_analyzer:
            self._display_advanced_analysis()

    def _display_latest_numbers(self, sorted_data: list):
        """CSV에서 최신 당첨번호를 읽어 공 위젯으로 표시"""
        if not sorted_data:
            return

        latest = sorted_data[0]
        round_no = latest.get('round', '?')
        date_str = latest.get('date', '')
        self.latest_round_label.setText(f"{round_no}회 ({date_str})")

        # 기존 공 위젯 제거 (마지막 stretch 제외)
        while self.balls_layout.count() > 1:
            item = self.balls_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 번호 공 삽입
        for i in range(1, 7):
            try:
                num = int(latest[f'num{i}'])
                ball = NumberBallWidget(num, size=48)
                self.balls_layout.insertWidget(
                    self.balls_layout.count() - 1, ball
                )
            except (ValueError, TypeError, KeyError):
                pass

        # 보너스 번호
        try:
            bonus = int(latest.get('bonus', ''))
            plus_label = QLabel("+")
            plus_label.setStyleSheet("font-size: 18px; color: #7f8c8d; padding: 0 5px;")
            self.balls_layout.insertWidget(self.balls_layout.count() - 1, plus_label)

            bonus_ball = NumberBallWidget(bonus, size=48, is_bonus=True)
            self.balls_layout.insertWidget(self.balls_layout.count() - 1, bonus_ball)
        except (ValueError, TypeError):
            pass

    def _display_basic_stats(self, sorted_data: list):
        """CSV 데이터에서 직접 기본 통계를 계산하여 표시 (stat_analyzer 불필요)"""
        from collections import Counter

        if not sorted_data:
            return

        # 모든 번호 추출
        all_numbers = []
        for row in sorted_data:
            for i in range(1, 7):
                try:
                    all_numbers.append(int(row[f'num{i}']))
                except (ValueError, TypeError, KeyError):
                    pass

        if not all_numbers:
            return

        # 빈도 분석
        counter = Counter(all_numbers)
        most_common = counter.most_common(5)
        least_common = counter.most_common()[:-6:-1]  # 하위 5개

        most_str = ", ".join([f"<b>{n}번</b>({c}회)" for n, c in most_common])
        least_str = ", ".join([f"{n}번({c}회)" for n, c in least_common])
        self.most_common_label.setText(f"📈 <b>최다 출현:</b> {most_str}")
        self.least_common_label.setText(f"📉 <b>최소 출현:</b> {least_str}")

        # Hot/Cold (최근 20회)
        recent_20 = sorted_data[:20]
        recent_numbers = []
        for row in recent_20:
            for i in range(1, 7):
                try:
                    recent_numbers.append(int(row[f'번호{i}']))
                except (ValueError, TypeError, KeyError):
                    pass

        recent_counter = Counter(recent_numbers)
        hot_nums = recent_counter.most_common(5)
        all_nums_set = set(range(1, 46))
        appeared_set = set(recent_numbers)
        cold_nums = sorted(all_nums_set - appeared_set)[:10]

        hot_str = ", ".join([f"<b>{n}번</b>({c}회)" for n, c in hot_nums])
        cold_str = ", ".join([f"{n}번" for n in cold_nums])
        self.hot_label.setText(f"🔥 <b>Hot:</b> {hot_str}")
        self.cold_label.setText(f"❄️ <b>Cold:</b> {cold_str}")

        # 합계 통계
        sums = []
        for row in sorted_data:
            try:
                s = sum(int(row[f'번호{i}']) for i in range(1, 7))
                sums.append(s)
            except (ValueError, TypeError, KeyError):
                pass

        if sums:
            avg_sum = sum(sums) / len(sums)
            self.sum_label.setText(
                f"평균 {avg_sum:.1f} | 최소 {min(sums)} | 최대 {max(sums)}"
            )

        # 홀짝 통계
        odd_counts = []
        for row in sorted_data:
            try:
                nums = [int(row[f'번호{i}']) for i in range(1, 7)]
                odd_counts.append(sum(1 for n in nums if n % 2 != 0))
            except (ValueError, TypeError, KeyError):
                pass

        if odd_counts:
            avg_odd = sum(odd_counts) / len(odd_counts)
            avg_even = 6 - avg_odd
            self.odd_even_label.setText(
                f"평균 홀수 {avg_odd:.1f}개 / 짝수 {avg_even:.1f}개"
            )

        # 구간분포
        section_counts = {'1-15': 0, '16-30': 0, '31-45': 0}
        total_nums = 0
        for row in sorted_data:
            for i in range(1, 7):
                try:
                    n = int(row[f'번호{i}'])
                    if 1 <= n <= 15:
                        section_counts['1-15'] += 1
                    elif 16 <= n <= 30:
                        section_counts['16-30'] += 1
                    elif 31 <= n <= 45:
                        section_counts['31-45'] += 1
                    total_nums += 1
                except (ValueError, TypeError, KeyError):
                    pass

        if total_nums > 0:
            self.section_label.setText(
                f"1-15: {section_counts['1-15']/total_nums*100:.1f}% | "
                f"16-30: {section_counts['16-30']/total_nums*100:.1f}% | "
                f"31-45: {section_counts['31-45']/total_nums*100:.1f}%"
            )

        # 연속번호 패턴
        consec_counts = Counter()
        for row in sorted_data:
            try:
                nums = sorted(int(row[f'번호{i}']) for i in range(1, 7))
                pairs = sum(1 for a, b in zip(nums, nums[1:]) if b - a == 1)
                consec_counts[pairs] += 1
            except (ValueError, TypeError, KeyError):
                pass

        total_rounds = sum(consec_counts.values())
        if total_rounds > 0:
            parts = []
            for k in [0, 1, 2, 3]:
                if k in consec_counts:
                    pct = consec_counts[k] / total_rounds * 100
                    parts.append(f"{k}쌍: {pct:.1f}%")
            self.consec_label.setText(" | ".join(parts))

    def _display_advanced_analysis(self):
        """stat_analyzer가 있을 때 고급 분석 결과로 덮어쓰기"""
        # Hot/Cold 분석
        trends = self.stat_analyzer.analyze_recent_trends(recent_count=20)
        if trends:
            hot_nums = trends.get('hot_numbers', [])
            cold_nums = trends.get('cold_numbers', [])
            hot_str = ", ".join([f"<b>{num}번</b>({cnt}회)" for num, cnt in hot_nums[:5]])
            cold_str = ", ".join([f"{n}번" for n in cold_nums[:10]])
            self.hot_label.setText(f"🔥 <b>Hot:</b> {hot_str}")
            self.cold_label.setText(f"❄️ <b>Cold:</b> {cold_str}")

        # 빈도 분석
        freq = self.stat_analyzer.analyze_frequency()
        if freq:
            most = freq.get('most_common', [])[:5]
            least = freq.get('least_common', [])[:5]
            most_str = ", ".join([f"<b>{n}번</b>({c}회)" for n, c in most])
            least_str = ", ".join([f"{n}번({c}회)" for n, c in least])
            self.most_common_label.setText(f"📈 <b>최다 출현:</b> {most_str}")
            self.least_common_label.setText(f"📉 <b>최소 출현:</b> {least_str}")

        # 합계 통계
        sum_stats = self.stat_analyzer.analyze_sum_range()
        if sum_stats:
            self.sum_label.setText(
                f"평균 {sum_stats.get('avg_sum', 0):.1f} | "
                f"최소 {sum_stats.get('min_sum', 0)} | 최대 {sum_stats.get('max_sum', 0)}"
            )

        # 홀짝 통계
        odd_even = self.stat_analyzer.analyze_odd_even()
        if odd_even:
            self.odd_even_label.setText(
                f"평균 홀수 {odd_even.get('avg_odd', 0):.1f}개 / "
                f"짝수 {odd_even.get('avg_even', 0):.1f}개"
            )

        # 구간분포
        section = self.stat_analyzer.analyze_section_distribution()
        if section and 'percentages' in section:
            pct = section['percentages']
            self.section_label.setText(
                f"1-15: {pct.get('1-15', 0):.1f}% | "
                f"16-30: {pct.get('16-30', 0):.1f}% | "
                f"31-45: {pct.get('31-45', 0):.1f}%"
            )

        # 연속번호 패턴
        consec = self.stat_analyzer.analyze_consecutive_patterns()
        if consec and 'percentages' in consec:
            pct = consec['percentages']
            parts = []
            for k in [0, 1, 2, 3]:
                if k in pct:
                    parts.append(f"{k}쌍: {pct[k]:.1f}%")
            self.consec_label.setText(" | ".join(parts))
