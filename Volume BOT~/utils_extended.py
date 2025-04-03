"""
확장 유틸리티 모듈
이 모듈은 추가적인 유틸리티 함수들을 제공합니다.
"""
import logging
import time
from typing import List, Tuple, Any, Dict, Callable, Generator
from functools import wraps

def retry_on_error(max_retries: int = 3, delay: int = 1, backoff: int = 2):
    """오류 발생 시 재시도 데코레이터
    
    Args:
        max_retries: 최대 재시도 횟수
        delay: 초기 대기 시간(초)
        backoff: 대기 시간 증가 승수
        
    Returns:
        데코레이터 함수
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retry_count = 0
            current_delay = delay
            
            while retry_count < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retry_count += 1
                    if retry_count >= max_retries:
                        raise e
                    
                    logging.warning(f"오류 발생 {func.__name__}: {str(e)}")
                    logging.warning(f"{retry_count}/{max_retries} 재시도 중... {current_delay}초 후")
                    time.sleep(current_delay)
                    current_delay *= backoff
            
            return None
        
        return wrapper
    
    return decorator

def chunks(lst: List[Any], n: int) -> Generator[List[Any], None, None]:
    """리스트를 n 크기의 청크로 분할
    
    Args:
        lst: 분할할 리스트
        n: 청크 크기
        
    Yields:
        분할된 리스트 청크
    """
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def validate_symbol(symbol: str) -> bool:
    """거래 페어 심볼 검증
    
    Args:
        symbol: 검증할 심볼 문자열
        
    Returns:
        유효성 여부
    """
    if not symbol or not isinstance(symbol, str):
        return False
    
    parts = symbol.split('_')
    if len(parts) != 2:
        return False
    
    return all(part.strip() for part in parts)

def parse_symbol(symbol: str) -> Tuple[str, str]:
    """거래 페어 심볼 파싱
    
    Args:
        symbol: 파싱할 심볼 문자열
        
    Returns:
        (기본화폐, 견적화폐) 튜플
        
    Raises:
        ValueError: 심볼 형식이 유효하지 않을 경우
    """
    if not validate_symbol(symbol):
        raise ValueError(f"유효하지 않은 심볼 형식: {symbol}")
    
    parts = symbol.split('_')
    return parts[0], parts[1]

def calculate_profit_percent(buy_price: float, sell_price: float) -> float:
    """매수/매도 가격으로 수익률 계산
    
    Args:
        buy_price: 매수 가격
        sell_price: 매도 가격
        
    Returns:
        수익률(%)
    """
    if buy_price <= 0:
        return 0.0
    
    return ((sell_price - buy_price) / buy_price) * 100.0

def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """긴 문자열 자르기
    
    Args:
        text: 원본 문자열
        max_length: 최대 길이
        suffix: 접미사
        
    Returns:
        잘린 문자열
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """안전한 나눗셈
    
    Args:
        numerator: 분자
        denominator: 분모
        default: 기본값
        
    Returns:
        나눗셈 결과 또는 기본값
    """
    try:
        if denominator == 0:
            return default
        return numerator / denominator
    except (ZeroDivisionError, TypeError):
        return default

def limit_decimal_places(value: float, places: int = 8) -> float:
    """소수점 자릿수 제한
    
    Args:
        value: 원본 값
        places: 소수점 자릿수
        
    Returns:
        제한된 값
    """
    factor = 10 ** places
    return int(value * factor) / factor

def is_valid_price(price: float, min_price: float, max_price: float) -> bool:
    """가격이 유효한 범위 내에 있는지 확인
    
    Args:
        price: 검증할 가격
        min_price: 최소 가격
        max_price: 최대 가격
        
    Returns:
        유효성 여부
    """
    return min_price <= price <= max_price

def timer(func: Callable) -> Callable:
    """함수 실행 시간 측정 데코레이터
    
    Args:
        func: 측정할 함수
        
    Returns:
        래핑된 함수
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        elapsed_time = end_time - start_time
        logging.debug(f"함수 {func.__name__} 실행 시간: {elapsed_time:.6f}초")
        
        return result
    
    return wrapper

def rate_limit(limit_per_second: float) -> Callable:
    """API 요청 속도 제한 데코레이터
    
    Args:
        limit_per_second: 초당 최대 요청 수
        
    Returns:
        데코레이터 함수
    """
    min_interval = 1.0 / limit_per_second
    last_called = [0.0]  # 리스트를 사용하여 클로저에서 수정 가능하게 함
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_time = time.time()
            elapsed = current_time - last_called[0]
            
            # 마지막 호출 이후 충분한 시간이 지나지 않았으면 대기
            if elapsed < min_interval:
                sleep_time = min_interval - elapsed
                time.sleep(sleep_time)
            
            last_called[0] = time.time()
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator