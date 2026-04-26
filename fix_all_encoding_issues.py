#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
모든 인코딩 문제 수정
"""

# 모든 문제 줄과 올바른 내용
all_fixes = {
    # 기존 수정 내용
    3636: '            print(f"   연속번호: {combo[\'consecutive_count\']}개")\n',
    3937: '        print(f"패턴 그룹 수: {len(self.grouped_patterns)}개")\n',
    3942: '            print(f"클러스터 {cluster_id}: {len(cluster_info[\'analysis\'])}개 분석")\n',
    3946: '                print(f"   그룹 크기: {analysis[\'size\']}개")\n',
    3953: '            print(f"\\n학습된 AI 모델 수: {len(self.ai_models)}개")\n',
    4053: '            print(f"클러스터 {cluster_id}: {len(cluster_info[\'rounds\'])}개 회차")\n',
    4078: '        print(f"\\n예측된 번호 조합 ({len(recommendations)}개):")\n',
    4195: '        print(f"\\n학습 완료: 정확도 {accuracy:.2%}")\n',
    4218: '        print(f"  예측 확률: {prob:.2%}")\n',
    4347: '            print(f"  최적 클러스터: {best_cluster_id} (점수: {best_score:.4f})")\n',
    4704: '        print(f"\\n선 연결 패턴 분석 결과 ({len(self.line_patterns)}개 패턴):")\n',
    4900: '        print(f"  패턴 개수: {len(common_patterns)}개")\n',
    4967: '        print(f"\\n패턴별 추천 번호 ({len(recommendations)}개):")\n',
    4984: '        print(f"  패턴: {pattern}")\n',
    4985: '        print(f"  추천 번호: {numbers}")\n',
    4986: '        print(f"  점수: {score:.4f}")\n',
    4987: '        print(f"  선 개수: {line_count}개")\n',
    5518: '        print(f"\\n최적 번호 조합 ({len(best_combinations)}개):")\n',
    5529: '            print(f"  점수: {combo[\'score\']:.4f}")\n',
    5772: '    print(f"\\n로또 번호 생성 완료! ({len(generated_numbers)}개)")\n',

    # 새로 발견된 문제들
    3933: '        print("\\n[INFO] AI 패턴 분석 리포트")\n',
    4726: '        print("2. 번호 생성")\n',
    4730: '        print("6. 제외 번호 관리")\n',
    5007: '        print("5. 제외번호 전체 초기화")\n',
    5008: '        print("6. 돌아가기")\n',
    5115: '        print("\\n 제외번호 전체 초기화")\n',
    5144: '        print("5. 선택 히스토리 그래프")\n',
    5145: '        print("6. 돌아가기")\n',
    5234: '        print("\\n 선택 히스토리 그래프")\n',
    5259: '        print("2. 전체 데이터 재수집")\n',
    5260: '        print("3. 돌아가기")\n',
    5291: '        print("\\n 전체 데이터 재수집")\n',
    5361: '        print("3. 패턴 클러스터링")\n',
    5365: '        print("7. AI 분석 리포트")\n',
    5367: '        print("9. 돌아가기")\n',
    5409: '        print("\\n 패턴 클러스터링")\n',
    5549: '        print("1. 모델 훈련")\n',
    5551: '        print("3. 돌아가기")\n',
    5582: '        print("\\n[INFO] AI 분석 리포트")\n',
    5634: '        print("2. 특정 회차 패턴 제거")\n',
    5637: '        print("5. 돌아가기")\n',
}

def fix_all():
    """모든 문제 수정"""
    # 파일 읽기
    with open('lotto_analyzer_fixed.py', 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()

    # 수정
    fixed_count = 0
    for line_no, new_content in all_fixes.items():
        idx = line_no - 1
        if idx < len(lines):
            old_content = lines[idx]
            lines[idx] = new_content
            if old_content != new_content:
                fixed_count += 1
                print(f'Fixed line {line_no}')

    # 파일 쓰기
    with open('lotto_analyzer_fixed.py', 'w', encoding='utf-8', newline='\n') as f:
        f.writelines(lines)

    print(f'\\n Total fixed: {fixed_count} lines')
    return fixed_count

if __name__ == '__main__':
    fix_all()
