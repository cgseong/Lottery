"""로또 분석 시스템 로깅 설정"""

import logging
import os
from logging.handlers import RotatingFileHandler

_LOG_FILE = 'lotto_system.log'
_MAX_BYTES = 1 * 1024 * 1024  # 1 MB
_BACKUP_COUNT = 3


def get_logger(name: str) -> logging.Logger:
    """모듈별 로거를 반환합니다. 최초 호출 시 핸들러를 설정합니다."""
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    fmt = logging.Formatter(
        '[%(levelname)s] %(name)s — %(message)s'
    )

    # 콘솔: WARNING 이상만 출력
    ch = logging.StreamHandler()
    ch.setLevel(logging.WARNING)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    # 파일: DEBUG 이상 모두 기록 (회전 로그)
    try:
        fh = RotatingFileHandler(
            _LOG_FILE, maxBytes=_MAX_BYTES, backupCount=_BACKUP_COUNT,
            encoding='utf-8'
        )
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    except OSError:
        pass  # 파일 쓰기 불가 환경에서도 콘솔 로그는 동작

    logger.propagate = False
    return logger
