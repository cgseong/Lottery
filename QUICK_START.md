# 로또 분석 프로그램 빠른 시작 가이드

## 🚨 현재 상황

**lotto_analyzer_fixed.py** 파일에 인코딩 문제가 있어 실행이 안 됩니다.

## ✅ 해결 방법

### 옵션 1: PowerShell에서 직접 실행

```powershell
# 1. 실행 정책 변경 (한 번만 실행)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 2. 가상환경 활성화
.\.venv\Scripts\Activate.ps1

# 3. 프로그램 실행
python lotto_analyzer_fixed.py
```

### 옵션 2: 명령 프롬프트 사용 (권장)

```cmd
# CMD 창 열기
cmd

# 가상환경 활성화
.venv\Scripts\activate.bat

# 프로그램 실행
python lotto_analyzer_fixed.py
```

### 옵션 3: 가상환경 없이 실행

```bash
python lotto_analyzer_fixed.py
```

## 🔧 인코딩 문제 해결

### Git에서 복원 (가장 빠름)
```bash
git checkout lotto_analyzer_fixed.py
```

### 수동 수정
VSCode나 다른 에디터로 다음 파일을 열고 수정:

**d:\Code\Lottery\lotto_analyzer_fixed.py**

손상된 줄들:
- 3318번: `print(f"총 {len(features)}개의 특성 벡터가 생성되었습니다.")`
- 3319번: `print(f"   특성 차원: {len(features[0])}개")`
- 3636번: `print(f"   연속번호: {combo['consecutive_count']}개")`

## 📦 필요한 패키지 설치

```bash
pip install -r requirements.txt
```

또는 개별 설치:
```bash
pip install numpy pandas scikit-learn requests beautifulsoup4 matplotlib
pip install tensorflow  # DNN 기능 사용시
```

## 🎯 리팩토링된 모듈 사용

새로 분리된 모듈들을 직접 사용할 수도 있습니다:

```python
from analyzers import ExcludeNumberManager, LottoDataCollector
from utils import check_installation_status, show_system_info

# 시스템 정보 확인
show_system_info()

# 패키지 설치 상태 확인
check_installation_status()

# 제외 번호 관리
manager = ExcludeNumberManager()
manager.add_exclude_numbers([1, 2, 3])

# 데이터 수집
collector = LottoDataCollector()
latest = collector.get_latest_round()
print(f"최신 회차: {latest}")
```

## 📚 문서

- [REFACTORING_GUIDE.md](REFACTORING_GUIDE.md) - 전체 리팩토링 가이드
- [REFACTORING_SUMMARY.md](REFACTORING_SUMMARY.md) - 완료 요약

## ⚡ 빠른 테스트

모듈이 정상 작동하는지 확인:

```bash
python -c "from analyzers import ExcludeNumberManager; print('OK')"
python -c "from analyzers import LottoDataCollector; print('OK')"
python -c "from utils import check_installation_status; print('OK')"
```

## 🐛 문제 해결

### Python 실행 오류
```
did not find executable at 'C:\Python313\python.exe'
```

해결: 가상환경의 Python 경로 재설정
```bash
python -m venv .venv --clear
```

### PowerShell 실행 정책 오류
```
이 시스템에서 스크립트를 실행할 수 없으므로...
```

해결: 관리자 권한으로 PowerShell 열고
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Import 오류
```
ModuleNotFoundError: No module named 'analyzers'
```

해결: 프로젝트 루트 디렉토리에서 실행
```bash
cd d:\Code\Lottery
python your_script.py
```

## 💡 팁

1. **CMD 사용 권장**: PowerShell 대신 명령 프롬프트(CMD) 사용
2. **절대 경로 사용**: 스크립트에서 상대 경로 문제시 절대 경로 사용
3. **UTF-8 인코딩**: 파일 저장시 항상 UTF-8 사용
