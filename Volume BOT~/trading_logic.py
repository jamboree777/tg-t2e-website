"""
거래 로직 모듈
이 모듈은 자가체결 거래 로직을 구현합니다.
"""
import time
import random
import logging
import threading
from typing import Dict, List, Tuple, Optional, Union, Any
from datetime import datetime

import config
from mexc_api_client import MexcApiClient
from db_manager import DBManager

logger = logging.getLogger(__name__)

class TradingBot:
    """자가체결 거래량 생성 봇 클래스"""
    
    def __init__(self, api_client: MexcApiClient, db_manager: DBManager, telegram_sender=None):
        """
        거래 봇 초기화
        
        Args:
            api_client: MEXC API 클라이언트 인스턴스
            db_manager: 데이터베이스 매니저 인스턴스
            telegram_sender: 텔레그램 메시지 전송 콜백 함수
        """
        self.api_client = api_client
        self.db_manager = db_manager
        self.telegram_sender = telegram_sender
        self.running = False
        self.trading_thread = None
        self.lock = threading.Lock()
        self.last_trade_time = None
        self.trade_count = 0
        self.symbol = config.SYMBOL
        self.token_name = config.TOKEN_NAME
        self.quote_currency = config.QUOTE_CURRENCY
        
    def start(self) -> bool:
        """
        거래 봇 시작
        
        Returns:
            성공 여부
        """
        with self.lock:
            if self.running:
                logger.warning("봇이 이미 실행 중입니다.")
                return False
            
            # 계정 잔고 확인
            if not self._check_balances():
                error_msg = "계정 잔고가 최소 요구치 미만입니다. 봇을 시작할 수 없습니다."
                logger.error(error_msg)
                if self.telegram_sender:
                    self.telegram_sender(error_msg)
                return False
            
            # 거래 스레드 시작
            self.running = True
            self.trading_thread = threading.Thread(target=self._trading_loop)
            self.trading_thread.daemon = True
            self.trading_thread.start()
            
            start_msg = f"거래 봇이 시작되었습니다. 심볼: {self.symbol}, 간격: {config.MIN_INTERVAL}-{config.MAX_INTERVAL}초"
            logger.info(start_msg)
            if self.telegram_sender:
                self.telegram_sender(start_msg)
            
            return True
    
    def stop(self) -> bool:
        """
        거래 봇 정지
        
        Returns:
            성공 여부
        """
        with self.lock:
            if not self.running:
                logger.warning("봇이 실행 중이 아닙니다.")
                return False
            
            # 플래그를 통해 거래 스레드 중지
            self.running = False
            
            # 모든 미체결 주문 취소
            try:
                self.api_client.cancel_all_orders(self.symbol)
                logger.info("모든 미체결 주문이 취소되었습니다.")
            except Exception as e:
                logger.error(f"미체결 주문 취소 중 오류 발생: {str(e)}")
            
            stop_msg = "거래 봇이 중지되었습니다."
            logger.info(stop_msg)
            if self.telegram_sender:
                self.telegram_sender(stop_msg)
            
            return True
    
    def get_status(self) -> Dict:
        """
        현재 봇 상태 조회
        
        Returns:
            상태 정보 딕셔너리
        """
        # 실행 시간 계산
        running_time = ""
        if self.running and self.last_trade_time:
            running_seconds = int((datetime.now() - self.last_trade_time).total_seconds())
            hours, remainder = divmod(running_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            running_time = f"{hours}시간 {minutes}분 {seconds}초"
        
        # 잔고 조회
        usdt_balance = 0
        token_balance = 0
        try:
            usdt_balance = self.api_client.get_specific_balance(self.quote_currency)
            token_balance = self.api_client.get_specific_balance(self.token_name)
        except Exception as e:
            logger.error(f"잔고 조회 중 오류 발생: {str(e)}")
        
        # 누적 거래량 조회
        total_volume = self.db_manager.get_total_volume()
        
        # 상태 딕셔너리 생성
        status = {
            "running": self.running,
            "trade_count": self.trade_count,
            "last_trade_time": self.last_trade_time,
            "running_time": running_time,
            "usdt_balance": usdt_balance,
            "token_balance": token_balance,
            "symbol": self.symbol,
            "total_volume": total_volume,
            "settings": {
                "min_interval": config.MIN_INTERVAL,
                "max_interval": config.MAX_INTERVAL,
                "min_price": config.MIN_PRICE,
                "max_price": config.MAX_PRICE,
                "trade_amount": config.TRADE_AMOUNT,
                "min_usdt_balance": config.MIN_USDT_BALANCE,
                "min_token_balance": config.MIN_TOKEN_BALANCE
            }
        }
        
        return status
    
    def get_trade_history(self, count: int = 10) -> List[Dict]:
        """
        거래 내역 조회
        
        Args:
            count: 조회할 거래 수
            
        Returns:
            거래 내역 목록
        """
        return self.db_manager.get_recent_trades(count)
    
    def _check_balances(self) -> bool:
        """
        최소 잔고 요구사항을 충족하는지 확인
        
        Returns:
            충족 여부
        """
        try:
            # USDT 잔고 확인
            usdt_balance = self.api_client.get_specific_balance(self.quote_currency)
            if usdt_balance < config.MIN_USDT_BALANCE:
                logger.warning(f"{self.quote_currency} 잔고가 최소 요구치 미만입니다. "
                            f"현재: {usdt_balance}, 최소: {config.MIN_USDT_BALANCE}")
                return False
            
            # 토큰 잔고 확인
            token_balance = self.api_client.get_specific_balance(self.token_name)
            if token_balance < config.MIN_TOKEN_BALANCE:
                logger.warning(f"{self.token_name} 잔고가 최소 요구치 미만입니다. "
                            f"현재: {token_balance}, 최소: {config.MIN_TOKEN_BALANCE}")
                return False
            
            return True
        
        except Exception as e:
            logger.error(f"잔고 확인 중 오류 발생: {str(e)}")
            return False
    
    def _decide_price(self) -> float:
        """
        거래 가격 결정
        
        Returns:
            결정된 거래 가격
        """
        try:
            # 최고 매수가(bid1)와 최저 매도가(ask1) 조회
            bid1, ask1 = self.api_client.get_bid_ask(self.symbol)
            
            # 호가창 스프레드 계산
            spread = ask1 - bid1
            
            # 가격 결정 방식 1: 직접 범위 내 가격 선택
            if config.MIN_PRICE <= bid1 <= config.MAX_PRICE and config.MIN_PRICE <= ask1 <= config.MAX_PRICE:
                # 범위 내에서 무작위 가격 선택
                price = random.uniform(bid1, ask1)
            
            # 가격 결정 방식 2: bid1과 ask1 사이에서 결정
            else:
                # bid1과 ask1 사이의 임의 지점 선택 (예: 30~70% 사이)
                percent = random.uniform(0.3, 0.7)
                price = bid1 + (spread * percent)
                
                # 설정된 최소/최대 가격 범위 내로 조정
                price = max(config.MIN_PRICE, min(config.MAX_PRICE, price))
            
            # 소수점 조정 (거래소의 최소 단위에 맞춤)
            # 대부분의 MEXC 거래쌍은 소수점 8자리를 지원
            price = round(price, 8)
            
            logger.info(f"가격 결정 - Bid1: {bid1}, Ask1: {ask1}, 선택된 가격: {price}")
            return price
        
        except Exception as e:
            logger.error(f"가격 결정 중 오류 발생: {str(e)}")
            # 오류 발생 시 기본값으로 중간 가격 반환
            return (config.MIN_PRICE + config.MAX_PRICE) / 2
    
    # trading_execution.py로 이동한 나머지 메서드들
    def _execute_trade(self):
        """_trading_execution.py로 구현이 이동됨"""
        from trading_execution import execute_trade
        return execute_trade(self)
    
    def _trading_loop(self):
        """_trading_execution.py로 구현이 이동됨"""
        from trading_execution import trading_loop
        return trading_loop(self)