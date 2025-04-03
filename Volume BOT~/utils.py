"""
유틸리티 모듈
이 모듈은 기본 유틸리티 함수들을 제공합니다.
"""
import logging
import logging.handlers
import time
import random
import os
from typing import Optional, Tuple, Any, Dict
from datetime import datetime, timedelta

import config

def setup_logging() -> None:
    """로깅 설정"""
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, config.LOG_LEVEL))
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, config.LOG_LEVEL))
    console_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_format)
    
    # 파일 핸들러
    file_handler = logging.handlers.RotatingFileHandler(
        config.LOG_FILE,
        maxBytes=config.MAX_LOG_SIZE,
        backupCount=config.LOG_BACKUP_COUNT
    )
    file_handler.setLevel(getattr(logging, config.LOG_LEVEL))
    file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_format)
    
    # 핸들러 등록
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    logging.info("로깅 설정이 완료되었습니다.")

def get_random_delay(min_seconds: int, max_seconds: int) -> int:
    """무작위 대기 시간 생성"""
    return random.randint(min_seconds, max_seconds)

def format_time(seconds: int) -> str:
    """초를 시:분:초 형식으로 변환"""
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}시간 {minutes}분 {seconds}초"

def format_decimal(value: float, precision: int = 8) -> str:
    """소수점 형식 변환"""
    format_str = f"{{:.{precision}f}}"
    return format_str.format(value)

def safe_float(value: Any, default: float = 0.0) -> float:
    """안전한 float 변환"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def safe_int(value: Any, default: int = 0) -> int:
    """안전한 int 변환"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def timestamp_to_datetime(timestamp: Any) -> Optional[datetime]:
    """타임스탬프를 datetime으로 변환"""
    try:
        if isinstance(timestamp, str):
            if timestamp.isdigit():
                # Unix 타임스탬프 (초)
                return datetime.fromtimestamp(int(timestamp))
            else:
                # ISO 형식 문자열
                return datetime.fromisoformat(timestamp)
        elif isinstance(timestamp, (int, float)):
            return datetime.fromtimestamp(timestamp)
        return None
    except Exception:
        return None

def datetime_to_str(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """datetime을 문자열로 변환"""
    if dt is None:
        return "N/A"
    return dt.strftime(format_str)

def create_directory_if_not_exists(directory: str) -> None:
    """디렉토리가 없으면 생성"""
    if not os.path.exists(directory):
        os.makedirs(directory)

# 추가 유틸리티는 utils_extended.py에 있습니다.