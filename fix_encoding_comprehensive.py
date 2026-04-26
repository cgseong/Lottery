#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
인코딩 손상된 줄을 모두 수정하는 스크립트
"""

# 문제가 있는 줄 번호와 올바른 내용
fixes = {
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
}

def fix_file():
    """파일 수정"""
    # 파일 읽기
    with open('lotto_analyzer_fixed.py', 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()

    # 문제 줄 수정
    fixed_count = 0
    for line_no, new_content in fixes.items():
        idx = line_no - 1
        if idx < len(lines):
            lines[idx] = new_content
            fixed_count += 1
            print(f'Line {line_no} fixed')

    # 파일 쓰기
    with open('lotto_analyzer_fixed.py', 'w', encoding='utf-8', newline='\n') as f:
        f.writelines(lines)

    print(f'\\nTotal fixed: {fixed_count} lines')
    return fixed_count

if __name__ == '__main__':
    fix_file()
