# 로또 분석 프로그램 실행 방법

## ✅ 문제 해결 완료

가상환경 경로 문제가 해결되었습니다!

## 🚀 실행 방법

### 방법 1: 명령 프롬프트(CMD) - 권장

```cmd
cd D:\Code\Lottery
python lotto_analyzer.py
```

### 방법 2: PowerShell

```powershell
cd D:\Code\Lottery

# 처음 한 번만 실행 (실행 정책 변경)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 프로그램 실행
python lotto_analyzer.py
```

### 방법 3: 가상환경 활성화 후 실행

**명령 프롬프트(CMD):**
```cmd
cd D:\Code\Lottery
.venv\Scripts\activate.bat
python lotto_analyzer.py
```

**PowerShell:**
```powershell
cd D:\Code\Lottery
.\.venv\Scripts\Activate.ps1
python lotto_analyzer.py
```

## 📦 필수 패키지 설치 (선택)

기본 랜덤 번호 생성은 패키지 없이도 작동합니다.

전체 기능을 사용하려면:

```bash
# 기본 분석 기능
pip install numpy pandas scikit-learn

# 웹 크롤링 (데이터 수집)
pip install requests beautifulsoup4

# DNN 기능 (선택)
pip install tensorflow
```

또는 한번에:
```bash
pip install numpy pandas scikit-learn requests beautifulsoup4
```

## 🎯 프로그램 기능

### 1. 랜덤 번호 생성 ✅ (패키지 불필요)
- 1~45 중 6개 무작위 선택
- 제외 번호 설정 가능

### 2. 통계 기반 추천 (scikit-learn 필요)
- 과거 당첨 번호 빈도 분석
- 출현 패턴 기반 추천

### 3. 패턴 분석 (numpy, pandas 필요)
- 연속 번호 분석
- 합계 패턴 분석
- 추세 분석

### 4. 데이터 업데이트 (requests, beautifulsoup4 필요)
- 동행복권 사이트에서 최신 당첨번호 수집

### 5. 제외 번호 관리
- 특정 번호 제외 설정
- 사용 가능 번호 관리

### 6. 시스템 정보
- Python 버전 확인
- 패키지 설치 상태 확인

## 🔧 문제 해결

### "ModuleNotFoundError: No module named 'requests'"

**해결:** requests 패키지 설치
```bash
pip install requests beautifulsoup4
```

또는 해당 기능 없이 기본 기능만 사용

### "did not find executable"

**이미 해결됨!** 가상환경이 Python 3.11.9로 재설정되었습니다.

### PowerShell 실행 정책 오류

**해결:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 프로그램이 멈춤

- Ctrl+C로 중단
- 메뉴에서 0 입력하여 정상 종료

## 📊 사용 예시

### 1단계: 프로그램 실행
```bash
python lotto_analyzer.py
```

### 2단계: 메뉴 선택
```
1. 랜덤 번호 생성    <- 가장 간단
2. 통계 기반 추천
3. 패턴 분석
4. 데이터 업데이트
5. 제외 번호 관리
6. 시스템 정보
0. 종료
```

### 3단계: 번호 생성
```
선택: 1
생성할 번호 세트 개수: 5

생성된 번호:
1. [3, 12, 23, 28, 35, 42]
2. [5, 15, 21, 31, 38, 44]
3. [7, 14, 19, 27, 33, 40]
...
```

## 📁 파일 구조

```
D:\Code\Lottery\
├── lotto_analyzer.py          <- 새 메인 파일 (사용)
├── lotto_analyzer_fixed.py    <- 구 파일 (사용 안함)
│
├── analyzers/                 <- 분석 모듈들
│   ├── exclude_number_manager.py
│   ├── lotto_data_collector.py
│   └── ...
│
├── utils/                     <- 유틸리티
│   ├── system_utils.py
│   └── ...
│
├── .venv/                     <- 가상환경 (재생성됨)
│   └── Scripts/
│       └── python.exe         <- Python 3.11.9
│
└── 문서/
    ├── HOW_TO_RUN.md          <- 이 문서
    ├── MIGRATION_COMPLETE.md
    └── ...
```

## ✨ 팁

1. **빠른 실행**: CMD에서 `python lotto_analyzer.py` (가장 간단)
2. **패키지 없이**: 메뉴 1번(랜덤 생성)만 사용
3. **전체 기능**: 패키지 설치 후 모든 메뉴 사용
4. **제외 번호**: 메뉴 5번에서 싫어하는 번호 제외 설정

## 🎉 완료!

모든 준비가 끝났습니다. 즐거운 로또 번호 생성 되세요!

---

**문제 발생시:**
1. [MIGRATION_COMPLETE.md](MIGRATION_COMPLETE.md) 참고
2. [QUICK_START.md](QUICK_START.md) 참고
3. Python 버전 확인: `python --version`
