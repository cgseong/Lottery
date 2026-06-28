"""당첨번호 패턴 시각화 페이지

회차를 선택하면 해당 회차의 당첨번호를 7열 그리드에 표시하고,
번호 순서대로 선으로 연결하여 패턴을 시각적으로 보여줍니다.
구조적 특성 수치화 및 패턴 유형 분류 결과도 함께 표시합니다.
"""

import os
import sys
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QWidget, QGroupBox, QSpinBox, QScrollArea, QFrame,
    QGridLayout
)
from PySide6.QtCore import Qt

from gui.pages.base_page import BasePage
from gui.widgets.number_pattern import NumberPatternWidget
from gui.widgets.number_ball import NumberBallWidget


class PatternPage(BasePage):
    """당첨번호 패턴 시각화 페이지"""

    def __init__(self, parent=None):
        super().__init__("패턴 시각화", parent)
        self._all_rows = []
        self._max_round = 0
        self._analyzer = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._create_title_label(
            "🔗 당첨번호 패턴 시각화 + 구조 분석"))

        # 스크롤 영역
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20, 15, 20, 15)
        content_layout.setSpacing(12)


        # ─── 회차 선택 컨트롤 ───
        control_group = QGroupBox("회차 선택")
        control_group.setStyleSheet(self._group_style())
        ctrl_layout = QHBoxLayout(control_group)

        self.prev_btn = QPushButton("◀ 이전")
        self.prev_btn.setStyleSheet(self._nav_btn_style())
        self.prev_btn.clicked.connect(self._go_prev)
        ctrl_layout.addWidget(self.prev_btn)

        ctrl_layout.addWidget(QLabel("회차:"))
        self.round_spin = QSpinBox()
        self.round_spin.setRange(1, 9999)
        self.round_spin.setValue(1)
        self.round_spin.setStyleSheet(
            "padding: 6px 12px; font-size: 14px; font-weight: bold;"
            " min-width: 80px;")
        self.round_spin.valueChanged.connect(self._on_round_changed)
        ctrl_layout.addWidget(self.round_spin)

        self.next_btn = QPushButton("다음 ▶")
        self.next_btn.setStyleSheet(self._nav_btn_style())
        self.next_btn.clicked.connect(self._go_next)
        ctrl_layout.addWidget(self.next_btn)

        ctrl_layout.addSpacing(20)

        self.latest_btn = QPushButton("최신 회차")
        self.latest_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c; color: white;
                border: none; padding: 8px 16px;
                border-radius: 4px; font-size: 12px; font-weight: bold;
            }
            QPushButton:hover { background-color: #c0392b; }
        """)
        self.latest_btn.clicked.connect(self._go_latest)
        ctrl_layout.addWidget(self.latest_btn)

        ctrl_layout.addStretch()

        self.numbers_label = QLabel("")
        self.numbers_label.setStyleSheet(
            "font-size: 13px; color: #2c3e50; font-weight: bold;")
        ctrl_layout.addWidget(self.numbers_label)

        content_layout.addWidget(control_group)


        # ─── 메인 콘텐츠: 좌=패턴 시각화, 우=구조 분석 ───
        main_h_layout = QHBoxLayout()
        main_h_layout.setSpacing(12)

        # 좌측: 패턴 시각화
        pattern_frame = QFrame()
        pattern_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 8px;
            }
        """)
        pattern_layout = QVBoxLayout(pattern_frame)
        pattern_layout.setContentsMargins(10, 10, 10, 10)

        self.pattern_widget = NumberPatternWidget()
        self.pattern_widget.setMinimumSize(380, 480)
        pattern_layout.addWidget(self.pattern_widget)

        main_h_layout.addWidget(pattern_frame, stretch=3)

        # 우측: 구조 분석 결과
        analysis_frame = QFrame()
        analysis_frame.setStyleSheet("""
            QFrame {
                background-color: #fafafa;
                border: 1px solid #ddd;
                border-radius: 8px;
            }
        """)
        analysis_layout = QVBoxLayout(analysis_frame)
        analysis_layout.setContentsMargins(12, 12, 12, 12)
        analysis_layout.setSpacing(10)

        # 패턴 유형 표시
        self.type_label = QLabel("패턴 유형: —")
        self.type_label.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #2c3e50;"
            " padding: 8px; background: white; border-radius: 6px;")
        analysis_layout.addWidget(self.type_label)

        # 구조적 특성 그리드
        features_group = QGroupBox("구조적 특성")
        features_group.setStyleSheet(self._inner_group_style())
        self.features_grid = QGridLayout(features_group)
        self.features_grid.setSpacing(4)
        # 초기 플레이스홀더
        self._feature_labels = {}
        feature_names = [
            ('centroid', '무게중심'),
            ('spread', '분산도'),
            ('density', '밀집도'),
            ('row_entropy', '행 엔트로피'),
            ('col_entropy', '열 엔트로피'),
            ('diagonal_score', '대각선 정렬'),
            ('path_length', '경로 길이'),
            ('direction_changes', '방향 변화'),
            ('aspect_ratio', '종횡비'),
        ]
        for i, (key, name) in enumerate(feature_names):
            name_lbl = QLabel(f"{name}:")
            name_lbl.setStyleSheet(
                "font-size: 11px; color: #555; font-weight: bold;")
            val_lbl = QLabel("—")
            val_lbl.setStyleSheet("font-size: 11px; color: #2c3e50;")
            self.features_grid.addWidget(name_lbl, i, 0)
            self.features_grid.addWidget(val_lbl, i, 1)
            self._feature_labels[key] = val_lbl
        analysis_layout.addWidget(features_group)


        # 무게중심 추세
        trend_group = QGroupBox("무게중심 이동 추세")
        trend_group.setStyleSheet(self._inner_group_style())
        trend_layout = QVBoxLayout(trend_group)
        self.trend_velocity_label = QLabel("이동 속도: —")
        self.trend_velocity_label.setStyleSheet("font-size: 11px;")
        trend_layout.addWidget(self.trend_velocity_label)
        self.trend_predict_label = QLabel("예상 구역: —")
        self.trend_predict_label.setStyleSheet(
            "font-size: 12px; font-weight: bold; color: #e74c3c;")
        trend_layout.addWidget(self.trend_predict_label)
        self.trend_strength_label = QLabel("추세 강도: —")
        self.trend_strength_label.setStyleSheet("font-size: 11px;")
        trend_layout.addWidget(self.trend_strength_label)
        analysis_layout.addWidget(trend_group)

        # 패턴 유형 통계
        stats_group = QGroupBox("패턴 유형 통계")
        stats_group.setStyleSheet(self._inner_group_style())
        stats_layout = QVBoxLayout(stats_group)
        self.stats_current_label = QLabel("현재 유형: —")
        self.stats_current_label.setStyleSheet("font-size: 11px;")
        stats_layout.addWidget(self.stats_current_label)
        self.stats_next_label = QLabel("다음 예상: —")
        self.stats_next_label.setStyleSheet(
            "font-size: 12px; font-weight: bold; color: #8e44ad;")
        stats_layout.addWidget(self.stats_next_label)
        self.stats_recent_label = QLabel("최근 10회: —")
        self.stats_recent_label.setStyleSheet(
            "font-size: 10px; color: #555; word-wrap: break-word;")
        self.stats_recent_label.setWordWrap(True)
        stats_layout.addWidget(self.stats_recent_label)
        analysis_layout.addWidget(stats_group)

        analysis_layout.addStretch()
        main_h_layout.addWidget(analysis_frame, stretch=2)

        content_layout.addLayout(main_h_layout)


        # ─── 번호 공 표시 ───
        self.balls_group = QGroupBox("당첨번호")
        self.balls_group.setStyleSheet(self._group_style())
        self.balls_layout = QHBoxLayout(self.balls_group)
        self.balls_layout.setSpacing(8)
        self.balls_layout.addStretch()
        content_layout.addWidget(self.balls_group)

        # ─── 다음 회차 예상 번호 + 패턴 시각화 ───
        predict_group = QGroupBox("🔮 다음 회차 예상 (패턴 유형 기반 추천)")
        predict_group.setStyleSheet(self._group_style())
        predict_layout = QVBoxLayout(predict_group)

        # 예상 실행 버튼
        btn_row = QHBoxLayout()
        self.predict_btn = QPushButton("🔮 예상 번호 생성")
        self.predict_btn.setStyleSheet("""
            QPushButton {
                background-color: #8e44ad; color: white;
                border: none; padding: 10px 24px;
                border-radius: 5px; font-size: 13px; font-weight: bold;
            }
            QPushButton:hover { background-color: #9b59b6; }
            QPushButton:pressed { background-color: #7d3c98; }
        """)
        self.predict_btn.clicked.connect(self._generate_prediction)
        btn_row.addWidget(self.predict_btn)
        btn_row.addStretch()
        self.predict_info_label = QLabel("")
        self.predict_info_label.setStyleSheet(
            "font-size: 12px; color: #8e44ad; font-weight: bold;")
        btn_row.addWidget(self.predict_info_label)
        predict_layout.addLayout(btn_row)

        # 예상 결과: 좌=패턴 그리드, 우=번호 목록
        self.predict_content_layout = QHBoxLayout()
        self.predict_content_layout.setSpacing(12)

        # 예상 패턴 시각화 위젯
        pred_pattern_frame = QFrame()
        pred_pattern_frame.setStyleSheet("""
            QFrame {
                background-color: #faf5ff;
                border: 1px solid #d4c5f9;
                border-radius: 8px;
            }
        """)
        pred_pattern_inner = QVBoxLayout(pred_pattern_frame)
        pred_pattern_inner.setContentsMargins(8, 8, 8, 8)
        self.predict_pattern_widget = NumberPatternWidget()
        self.predict_pattern_widget.setMinimumSize(350, 440)
        pred_pattern_inner.addWidget(self.predict_pattern_widget)
        self.predict_content_layout.addWidget(pred_pattern_frame, stretch=3)

        # 우측: 예상 번호 리스트
        self.predict_list_frame = QFrame()
        self.predict_list_frame.setStyleSheet("""
            QFrame {
                background-color: #faf5ff;
                border: 1px solid #d4c5f9;
                border-radius: 8px;
            }
        """)
        self.predict_list_layout = QVBoxLayout(self.predict_list_frame)
        self.predict_list_layout.setContentsMargins(10, 10, 10, 10)
        self.predict_list_layout.setSpacing(8)
        self.predict_list_layout.addWidget(
            QLabel("예상 번호 생성 버튼을 클릭하세요."))
        self.predict_list_layout.addStretch()
        self.predict_content_layout.addWidget(
            self.predict_list_frame, stretch=2)

        predict_layout.addLayout(self.predict_content_layout)
        content_layout.addWidget(predict_group)

        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)

    # ─── 데이터 로드 ─────────────────────────────────────────────

    def on_data_loaded(self):
        """데이터 로드 후 초기화"""
        if not self.historical_data:
            return

        self._all_rows = sorted(
            self.historical_data,
            key=lambda x: int(x.get('round', 0) or 0)
        )

        if self._all_rows:
            self._max_round = int(self._all_rows[-1].get('round', 0))
            self.round_spin.setRange(
                int(self._all_rows[0].get('round', 1)),
                self._max_round
            )

        # 구조 분석기 초기화
        try:
            project_root = os.path.dirname(
                os.path.dirname(os.path.dirname(
                    os.path.abspath(__file__))))
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            from analyzers.pattern_structure_analyzer import (
                PatternStructureAnalyzer
            )
            self._analyzer = PatternStructureAnalyzer(self.historical_data)
            self._analyzer.analyze()
        except Exception:
            self._analyzer = None

        # 최신 회차로 이동
        if self._max_round > 0:
            self.round_spin.setValue(self._max_round)

        # 전체 추세/통계 업데이트
        self._update_trend_panel()
        self._update_stats_panel()


    # ─── 회차 변경 이벤트 ─────────────────────────────────────────

    def _on_round_changed(self, round_no: int):
        """회차 변경 시 패턴 및 분석 업데이트"""
        row = self._find_round(round_no)
        if row is None:
            self.pattern_widget.clear()
            self.numbers_label.setText(f"{round_no}회 — 데이터 없음")
            self._clear_balls()
            self._reset_features_panel()
            return

        # 번호 추출
        numbers = []
        for i in range(1, 7):
            try:
                n = int(row.get(f'num{i}', 0))
                if 1 <= n <= 45:
                    numbers.append(n)
            except (ValueError, TypeError):
                continue

        # 패턴 위젯 업데이트
        self.pattern_widget.set_numbers(numbers, round_no)

        # 번호 텍스트 표시
        nums_str = ", ".join(str(n) for n in numbers)
        bonus = row.get('bonus', '')
        self.numbers_label.setText(
            f"{round_no}회: [{nums_str}] + 보너스 {bonus}")

        # 번호 공 업데이트
        self._update_balls(numbers, bonus)

        # 구조 분석 업데이트
        self._update_features_panel(numbers)

    # ─── 구조 분석 UI 업데이트 ────────────────────────────────────

    def _update_features_panel(self, numbers: list):
        """구조적 특성 패널을 업데이트합니다."""
        try:
            from analyzers.pattern_structure_analyzer import (
                compute_structural_features, classify_pattern
            )
        except ImportError:
            return

        if len(numbers) < 6:
            self._reset_features_panel()
            return

        features = compute_structural_features(numbers)
        pattern = classify_pattern(numbers)

        # 패턴 유형 표시
        type_name = pattern.get('type_name', '—')
        confidence = pattern.get('confidence', 0)
        self.type_label.setText(
            f"패턴 유형: {type_name}  (신뢰도 {confidence:.0%})")

        # 구조적 특성 값 업데이트
        self._feature_labels['centroid'].setText(
            f"({features['centroid_row']:.1f}, {features['centroid_col']:.1f})")
        self._feature_labels['spread'].setText(
            f"{features['spread']:.2f}")
        self._feature_labels['density'].setText(
            f"{features['density']:.2f}")
        self._feature_labels['row_entropy'].setText(
            f"{features['row_entropy']:.3f}")
        self._feature_labels['col_entropy'].setText(
            f"{features['col_entropy']:.3f}")
        self._feature_labels['diagonal_score'].setText(
            f"{features['diagonal_score']:.3f}")
        self._feature_labels['path_length'].setText(
            f"{features['path_length']:.1f}")
        self._feature_labels['direction_changes'].setText(
            f"{features['direction_changes']}회")
        self._feature_labels['aspect_ratio'].setText(
            f"{features['aspect_ratio']:.2f}")

    def _reset_features_panel(self):
        """구조적 특성 패널을 초기화합니다."""
        self.type_label.setText("패턴 유형: —")
        for lbl in self._feature_labels.values():
            lbl.setText("—")


    def _update_trend_panel(self):
        """무게중심 이동 추세 패널을 업데이트합니다."""
        if not self._analyzer:
            return

        try:
            trend = self._analyzer.get_centroid_trend(10)
        except Exception:
            return

        vel_r = trend.get('velocity_row', 0)
        vel_c = trend.get('velocity_col', 0)
        dir_r = '↓' if vel_r > 0.05 else ('↑' if vel_r < -0.05 else '→')
        dir_c = '→' if vel_c > 0.05 else ('←' if vel_c < -0.05 else '·')
        self.trend_velocity_label.setText(
            f"이동 속도: 행 {vel_r:+.3f}{dir_r}  열 {vel_c:+.3f}{dir_c}")

        region = trend.get('predicted_region', '—')
        pred = trend.get('predicted_centroid', (0, 0))
        self.trend_predict_label.setText(
            f"다음 예상 구역: {region} ({pred[0]:.1f}, {pred[1]:.1f})")

        strength = trend.get('trend_strength', 0)
        bar = '█' * int(strength * 10) + '░' * (10 - int(strength * 10))
        self.trend_strength_label.setText(
            f"추세 강도: {bar} {strength:.0%}")

    def _update_stats_panel(self):
        """패턴 유형 통계 패널을 업데이트합니다."""
        if not self._analyzer:
            return

        try:
            stats = self._analyzer.get_pattern_type_statistics()
        except Exception:
            return

        last_type = stats.get('last_type', '—')
        self.stats_current_label.setText(f"최신 회차 유형: {last_type}")

        next_type = stats.get('next_likely_type', '—')
        self.stats_next_label.setText(f"다음 예상 유형: {next_type}")

        recent = stats.get('recent_types', [])
        if recent:
            recent_str = " → ".join(recent[-7:])
            self.stats_recent_label.setText(f"최근 흐름: {recent_str}")


    # ─── 네비게이션 ───────────────────────────────────────────────

    def _find_round(self, round_no: int):

        for row in self._all_rows:
            try:
                if int(row.get('round', 0)) == round_no:
                    return row
            except (ValueError, TypeError):
                continue
        return None

    def _go_prev(self):
        current = self.round_spin.value()
        if current > self.round_spin.minimum():
            self.round_spin.setValue(current - 1)

    def _go_next(self):
        current = self.round_spin.value()
        if current < self.round_spin.maximum():
            self.round_spin.setValue(current + 1)

    def _go_latest(self):
        if self._max_round > 0:
            self.round_spin.setValue(self._max_round)

    # ─── 번호 공 ─────────────────────────────────────────────────

    def _update_balls(self, numbers: list, bonus: str):
        self._clear_balls()
        for num in numbers:
            ball = NumberBallWidget(num, size=42)
            self.balls_layout.insertWidget(
                self.balls_layout.count() - 1, ball)
        try:
            bonus_num = int(bonus)
            if 1 <= bonus_num <= 45:
                plus_label = QLabel("+")
                plus_label.setStyleSheet(
                    "font-size: 16px; font-weight: bold; color: #7f8c8d;")
                self.balls_layout.insertWidget(
                    self.balls_layout.count() - 1, plus_label)
                bonus_ball = NumberBallWidget(
                    bonus_num, size=42, is_bonus=True)
                self.balls_layout.insertWidget(
                    self.balls_layout.count() - 1, bonus_ball)
        except (ValueError, TypeError):
            pass

    def _clear_balls(self):
        while self.balls_layout.count() > 1:
            item = self.balls_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    # ─── 스타일 ──────────────────────────────────────────────────

    def _group_style(self) -> str:
        return """
            QGroupBox {
                font-size: 14px; font-weight: bold; color: #2c3e50;
                border: 1px solid #ddd; border-radius: 8px;
                margin-top: 10px; padding-top: 15px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin; left: 15px; padding: 0 8px;
            }
        """

    def _inner_group_style(self) -> str:
        return """
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #34495e;
                border: 1px solid #e0e0e0; border-radius: 6px;
                margin-top: 8px; padding-top: 12px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin; left: 10px; padding: 0 5px;
            }
        """

    def _nav_btn_style(self) -> str:
        return """
            QPushButton {
                background-color: #3498db; color: white;
                border: none; padding: 8px 16px;
                border-radius: 4px; font-size: 12px; font-weight: bold;
            }
            QPushButton:hover { background-color: #2980b9; }
            QPushButton:pressed { background-color: #1a6da3; }
        """
