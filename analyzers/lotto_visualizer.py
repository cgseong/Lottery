
import matplotlib.pyplot as plt
import matplotlib.patches as patches

class LottoVisualizer:
    def __init__(self):
        # 한글 폰트 설정 (Windows 기본 폰트 시도)
        plt.rcParams['font.family'] = 'Malgun Gothic'
        plt.rcParams['axes.unicode_minus'] = False

    def visualize_round(self, round_num, numbers):
        """
        특정 회차의 당첨 번호를 시각화합니다.
        :param round_num: 회차 번호
        :param numbers: 당첨 번호 리스트 (보너스 번호 제외 또는 포함, 여기서는 주요 6개 번호 연결)
        """
        # 7x7 그리드 설정 (1~45번을 7열로 배치)
        fig, ax = plt.subplots(figsize=(6, 8))
        
        # 배경색이나 그리드 스타일 설정
        ax.set_xlim(0, 8)
        ax.set_ylim(8, 0) # Y축 반전 (위에서 아래로)
        ax.axis('off') # 축 숨기기
        
        # 제목
        ax.set_title(f"{round_num}회 로또 당첨 번호 패턴", fontsize=15, pad=20)

        # 번호 좌표 계산 함수 (1-based index)
        # 1행: 1, 2, 3, 4, 5, 6, 7
        # 2행: 8, 9, ...
        def get_coord(num):
            row = (num - 1) // 7 + 1
            col = (num - 1) % 7 + 1
            return col, row

        # 모든 번호 (1~45) 그리기 (배경)
        for n in range(1, 46):
            c, r = get_coord(n)
            # 빨간 괄호 스타일: [ n ]
            ax.text(c, r, f"[{n}]", ha='center', va='center', fontsize=10, color='red', alpha=0.3)

        # 당첨 번호 그리기
        sorted_nums = sorted(numbers[:6]) # 보너스 번호 제외하고 앞 6개만 연결 (보통 패턴 분석은 정규 번호로 함)
        
        # 연결 선 그리기
        line_x = []
        line_y = []
        for n in sorted_nums:
            c, r = get_coord(n)
            line_x.append(c)
            line_y.append(r)
            
            # 당첨 번호 강조 (검은 동그라미 배경에 흰 글씨)
            circle = patches.Circle((c, r), 0.3, color='black', zorder=2)
            ax.add_patch(circle)
            ax.text(c, r, str(n), ha='center', va='center', color='white', fontweight='bold', zorder=3)

        # 선 연결 (검은색 실선)
        ax.plot(line_x, line_y, color='black', linewidth=2, zorder=1)

        plt.tight_layout()
        plt.show()

if __name__ == "__main__":
    # 테스트용
    vis = LottoVisualizer()
    vis.visualize_round(1000, [1, 10, 20, 30, 40, 45])
