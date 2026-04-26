"""
시스템 정보 및 패키지 상태 확인 유틸리티
"""

import sys
import platform


def check_installation_status():
    """필요한 패키지들의 설치 상태를 확인합니다."""
    print("\n 패키지 설치 상태 확인")
    print("=" * 50)

    # 기본 패키지들
    basic_packages = {
        'numpy': '수치 계산',
        'pandas': '데이터 처리',
        'requests': '웹 요청',
        'beautifulsoup4': '웹 스크래핑',
        'matplotlib': '그래프 생성',
        'scikit-learn': '머신러닝'
    }

    # DNN 관련 패키지들
    dnn_packages = {
        'tensorflow': '딥러닝 프레임워크',
        'keras': '딥러닝 라이브러리'
    }

    # AI 패턴 학습 관련 패키지들
    ai_pattern_packages = {
        'numpy': '수치 계산 라이브러리',
        'pandas': '데이터 처리 라이브러리',
        'scikit-learn': '머신러닝 라이브러리',
        'joblib': '모델 저장/로드 라이브러리'
    }

    print(" 기본 패키지:")
    basic_available = True
    for package, description in basic_packages.items():
        try:
            __import__(package)
            print(f"    {package}: {description}")
        except ImportError:
            print(f"    {package}: {description} (설치 필요)")
            basic_available = False

    print("\n DNN 패키지:")
    dnn_available = True
    for package, description in dnn_packages.items():
        try:
            __import__(package)
            print(f"    {package}: {description}")
        except ImportError:
            print(f"    {package}: {description} (설치 필요)")
            dnn_available = False

    print("\n AI 패턴 학습 패키지:")
    ai_pattern_available = True
    for package, description in ai_pattern_packages.items():
        try:
            __import__(package)
            print(f"    {package}: {description}")
        except ImportError:
            print(f"    {package}: {description} (설치 필요)")
            ai_pattern_available = False

    # 선 연결 패턴 분석 관련 패키지들
    line_pattern_packages = {
        'matplotlib': '그래프 및 시각화 라이브러리'
    }

    print("\n 선 연결 패턴 분석 패키지:")
    line_pattern_available = True
    for package, description in line_pattern_packages.items():
        try:
            __import__(package)
            print(f"    {package}: {description}")
        except ImportError:
            print(f"    {package}: {description} (설치 필요)")
            line_pattern_available = False

    print("\n 설치 가이드:")
    if not basic_available or not dnn_available or not ai_pattern_available or not line_pattern_available:
        print("   모든 패키지 설치:")
        print("   pip install -r requirements.txt")
        print("\n   또는 개별 설치:")
        if not basic_available:
            print("   기본 패키지: pip install numpy pandas requests beautifulsoup4 matplotlib scikit-learn")
        if not dnn_available:
            print("   DNN 패키지: pip install tensorflow")
        if not ai_pattern_available:
            print("   AI 패턴 학습 패키지: pip install scikit-learn pandas numpy joblib")
        if not line_pattern_available:
            print("   선 연결 패턴 분석 패키지: pip install matplotlib")
    else:
        print("    모든 패키지가 설치되어 있습니다!")

    print("=" * 50)
    return basic_available, dnn_available, ai_pattern_available, line_pattern_available


def show_system_info():
    """시스템 정보를 표시합니다."""
    print("\n 시스템 정보")
    print("=" * 50)

    print(f" Python 버전: {sys.version}")
    print(f" 운영체제: {platform.system()} {platform.release()}")
    print(f" 아키텍처: {platform.machine()}")

    # 메모리 정보 (가능한 경우)
    try:
        import psutil
        memory = psutil.virtual_memory()
        print(f" 메모리: {memory.total // (1024**3):.1f}GB (사용 가능: {memory.available // (1024**3):.1f}GB)")
    except ImportError:
        print(" 메모리: psutil 패키지가 설치되지 않아 확인이 불가능합니다.")

    # CPU 정보 (가능한 경우)
    try:
        import psutil
        cpu_count = psutil.cpu_count()
        print(f" CPU 코어: {cpu_count}개")
    except ImportError:
        print(" CPU: psutil 패키지가 설치되지 않아 확인이 불가능합니다.")

    print("=" * 50)
