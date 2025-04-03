"""
MEXC API 클라이언트 모듈
이 모듈은 MEXC 거래소 API와의 통신을 담당합니다.
"""
import time
import hmac
import hashlib
import requests
import json
import urllib.parse
from typing import Dict, List, Tuple, Optional, Union, Any
import logging

import config

logger = logging.getLogger(__name__)

class MexcApiClient:
    """MEXC API 클라이언트 클래스"""
    
    def __init__(self, api_key: str, api_secret: str):
        """
        MEXC API 클라이언트 초기화
        
        Args:
            api_key: MEXC API 키
            api_secret: MEXC API 시크릿
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = config.API_BASE_URL
        self.retry_count = 0
        self.max_retries = config.MAX_RETRIES
        
    def _get_signature(self, params: Dict[str, Any]) -> str:
        """
        API 요청 서명 생성
        
        Args:
            params: 요청 파라미터 딕셔너리
            
        Returns:
            생성된 HMAC SHA256 서명
        """
        # 파라미터 정렬 및 쿼리 문자열 생성
        query_string = '&'.join([f"{k}={v}" for k, v in sorted(params.items())])
        # HMAC SHA256 서명 생성
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _handle_request(self, method: str, endpoint: str, params: Dict = None, signed: bool = False) -> Dict:
        """
        API 요청 처리 및 응답 반환
        
        Args:
            method: 요청 메소드 ('GET', 'POST', 'DELETE' 등)
            endpoint: API 엔드포인트 경로
            params: 요청 파라미터 딕셔너리
            signed: 서명이 필요한 요청 여부
            
        Returns:
            API 응답 데이터
            
        Raises:
            Exception: API 요청 실패 시
        """
        url = f"{self.base_url}/{config.API_VERSION}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if params is None:
            params = {}
            
        if signed:
            # 타임스탬프 추가
            params['timestamp'] = int(time.time() * 1000)
            # API 키 추가
            params['recvWindow'] = 5000
            # 서명 생성 및 추가
            params['signature'] = self._get_signature(params)
            # API 키 헤더 추가
            headers['X-MEXC-APIKEY'] = self.api_key
        
        try:
            if method == 'GET':
                response = requests.get(url, params=params, headers=headers, timeout=config.API_TIMEOUT)
            elif method == 'POST':
                response = requests.post(url, json=params, headers=headers, timeout=config.API_TIMEOUT)
            elif method == 'DELETE':
                response = requests.delete(url, params=params, headers=headers, timeout=config.API_TIMEOUT)
            else:
                raise ValueError(f"지원되지 않는 HTTP 메소드: {method}")
            
            # 응답 확인
            if response.status_code == 200:
                return response.json()
            else:
                # 오류 정보 로깅
                logger.error(f"API 오류 - 상태 코드: {response.status_code}, 응답: {response.text}")
                error_data = response.json() if response.text else {"error": f"HTTP 오류 {response.status_code}"}
                
                # 재시도 가능한 오류인 경우 재시도
                if response.status_code in [429, 500, 502, 503, 504] and self.retry_count < self.max_retries:
                    self.retry_count += 1
                    retry_delay = 2 ** self.retry_count  # 지수 백오프
                    logger.warning(f"일시적 오류, {retry_delay}초 후 재시도 ({self.retry_count}/{self.max_retries})...")
                    time.sleep(retry_delay)
                    return self._handle_request(method, endpoint, params, signed)
                
                raise Exception(f"MEXC API 오류: {error_data}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"요청 예외 발생: {str(e)}")
            
            # 네트워크 오류 시 재시도
            if self.retry_count < self.max_retries:
                self.retry_count += 1
                retry_delay = 2 ** self.retry_count
                logger.warning(f"네트워크 오류, {retry_delay}초 후 재시도 ({self.retry_count}/{self.max_retries})...")
                time.sleep(retry_delay)
                return self._handle_request(method, endpoint, params, signed)
            
            raise Exception(f"API 요청 실패: {str(e)}")
            
        finally:
            # 성공 시 재시도 카운터 초기화
            if 'response' in locals() and response.status_code == 200:
                self.retry_count = 0
    
    def get_account_info(self) -> Dict:
        """
        계정 정보 조회
        
        Returns:
            계정 정보 딕셔너리
        """
        return self._handle_request('GET', 'account', signed=True)
    
    def get_balances(self) -> Dict[str, float]:
        """
        계정 잔고 조회
        
        Returns:
            통화별 잔고 딕셔너리 (통화 심볼: 잔고)
        """
        account_info = self.get_account_info()
        balances = {}
        
        for asset in account_info.get('balances', []):
            symbol = asset.get('asset', '')
            free = float(asset.get('free', 0))
            locked = float(asset.get('locked', 0))
            balances[symbol] = free + locked  # 총 잔고 (사용 가능 + 락)
            
        return balances
    
    def get_specific_balance(self, symbol: str) -> float:
        """
        특정 통화의 잔고 조회
        
        Args:
            symbol: 통화 심볼 (예: 'BTC', 'USDT')
            
        Returns:
            해당 통화의 총 잔고
        """
        balances = self.get_balances()
        return balances.get(symbol, 0.0)
    
    def get_ticker(self, symbol: str) -> Dict:
        """
        현재 시장 정보(ticker) 조회
        
        Args:
            symbol: 거래 페어 심볼 (예: 'BTC_USDT')
            
        Returns:
            시장 정보 딕셔너리
        """
        params = {'symbol': symbol}
        return self._handle_request('GET', 'ticker', params=params)
    
    def get_orderbook(self, symbol: str, limit: int = 5) -> Dict:
        """
        오더북 조회
        
        Args:
            symbol: 거래 페어 심볼 (예: 'BTC_USDT')
            limit: 조회할 주문 수 (기본값: 5)
            
        Returns:
            오더북 데이터 딕셔너리
        """
        params = {'symbol': symbol, 'limit': limit}
        return self._handle_request('GET', 'depth', params=params)
    
    def get_bid_ask(self, symbol: str) -> Tuple[float, float]:
        """
        최고 매수가(bid1)와 최저 매도가(ask1) 조회
        
        Args:
            symbol: 거래 페어 심볼 (예: 'BTC_USDT')
            
        Returns:
            (bid1, ask1) 튜플
        """
        orderbook = self.get_orderbook(symbol, limit=1)
        
        # 오더북에서 최고 매수가, 최저 매도가 추출
        bid1 = float(orderbook['bids'][0][0]) if orderbook.get('bids') else 0
        ask1 = float(orderbook['asks'][0][0]) if orderbook.get('asks') else 0
        
        return bid1, ask1
    
    def create_order(self, symbol: str, side: str, order_type: str, 
                    quantity: float, price: float = None) -> Dict:
        """
        주문 생성
        
        Args:
            symbol: 거래 페어 심볼 (예: 'BTC_USDT')
            side: 주문 방향 ('BUY' 또는 'SELL')
            order_type: 주문 유형 ('LIMIT', 'MARKET')
            quantity: 주문 수량
            price: 주문 가격 (LIMIT 주문에만 필요)
            
        Returns:
            주문 생성 결과 딕셔너리
        """
        params = {
            'symbol': symbol,
            'side': side,
            'type': order_type,
            'quantity': quantity
        }
        
        # LIMIT 주문인 경우 가격 추가
        if order_type == 'LIMIT' and price is not None:
            params['price'] = price
            params['timeInForce'] = 'GTC'  # Good Till Cancel
        
        return self._handle_request('POST', 'order', params=params, signed=True)
    
    def cancel_order(self, symbol: str, order_id: str) -> Dict:
        """
        주문 취소
        
        Args:
            symbol: 거래 페어 심볼 (예: 'BTC_USDT')
            order_id: 취소할 주문 ID
            
        Returns:
            주문 취소 결과 딕셔너리
        """
        params = {
            'symbol': symbol,
            'orderId': order_id
        }
        
        return self._handle_request('DELETE', 'order', params=params, signed=True)
    
    def cancel_all_orders(self, symbol: str) -> Dict:
        """
        특정 심볼의 모든 주문 취소
        
        Args:
            symbol: 거래 페어 심볼 (예: 'BTC_USDT')
            
        Returns:
            주문 취소 결과 딕셔너리
        """
        params = {'symbol': symbol}
        return self._handle_request('DELETE', 'openOrders', params=params, signed=True)
    
    def get_order_status(self, symbol: str, order_id: str) -> Dict:
        """
        주문 상태 조회
        
        Args:
            symbol: 거래 페어 심볼 (예: 'BTC_USDT')
            order_id: 조회할 주문 ID
            
        Returns:
            주문 상태 정보 딕셔너리
        """
        params = {
            'symbol': symbol,
            'orderId': order_id
        }
        
        return self._handle_request('GET', 'order', params=params, signed=True)
    
    def get_open_orders(self, symbol: str) -> List[Dict]:
        """
        미체결 주문 조회
        
        Args:
            symbol: 거래 페어 심볼 (예: 'BTC_USDT')
            
        Returns:
            미체결 주문 목록
        """
        params = {'symbol': symbol}
        return self._handle_request('GET', 'openOrders', params=params, signed=True)
    
    def get_order_history(self, symbol: str, limit: int = 10) -> List[Dict]:
        """
        주문 내역 조회
        
        Args:
            symbol: 거래 페어 심볼 (예: 'BTC_USDT')
            limit: 조회할 주문 수 (기본값: 10)
            
        Returns:
            주문 내역 목록
        """
        params = {
            'symbol': symbol,
            'limit': limit
        }
        
        return self._handle_request('GET', 'allOrders', params=params, signed=True)