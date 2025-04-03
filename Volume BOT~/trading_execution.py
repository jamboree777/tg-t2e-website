"""
거래 실행 모듈
이 모듈은 실제 거래 실행 로직을 담당합니다.
"""
import time
import random
import logging
from datetime import datetime
from typing import Dict, Tuple, List, Any, Optional

import config

logger = logging.getLogger(__name__)

def execute_trade(trading_bot) -> bool:
    """
    단일 자가체결 거래 실행
    
    Args:
        trading_bot: TradingBot 인스턴스
        
    Returns:
        성공 여부
    """
    buy_order_id = None
    sell_order_id = None
    
    try:
        # 1. 잔고 확인
        if not trading_bot._check_balances():
            error_msg = "계정 잔고가 최소 요구치 미만입니다. 거래를 중단합니다."
            logger.error(error_msg)
            if trading_bot.telegram_sender:
                trading_bot.telegram_sender(error_msg)
            trading_bot.running = False
            return False
        
        # 2. 가격 결정
        price = trading_bot._decide_price()
        
        # 3. 매수/매도 주문 동시 제출
        # 매수 주문
        buy_result = trading_bot.api_client.create_order(
            symbol=trading_bot.symbol,
            side='BUY',
            order_type='LIMIT',
            quantity=config.TRADE_AMOUNT,
            price=price
        )
        buy_order_id = buy_result.get('orderId')
        
        # 매도 주문
        sell_result = trading_bot.api_client.create_order(
            symbol=trading_bot.symbol,
            side='SELL',
            order_type='LIMIT',
            quantity=config.TRADE_AMOUNT,
            price=price
        )
        sell_order_id = sell_result.get('orderId')
        
        logger.info(f"주문 제출 완료 - 가격: {price}, 수량: {config.TRADE_AMOUNT}")
        
        # 4. 취소 전 대기 (설정된 시간만큼)
        time.sleep(config.CANCEL_DELAY)
        
        # 5. 주문 상태 확인 및 체결되지 않은 주문 취소
        buy_filled, buy_filled_qty, buy_filled_price = check_and_cancel_order(
            trading_bot.api_client, trading_bot.symbol, buy_order_id
        )
        
        sell_filled, sell_filled_qty, sell_filled_price = check_and_cancel_order(
            trading_bot.api_client, trading_bot.symbol, sell_order_id
        )
        
        # 6. 거래 기록 저장
        now = datetime.now()
        trading_bot.last_trade_time = now
        trading_bot.trade_count += 1
        
        # 체결된 양 계산
        filled_quantity = min(buy_filled_qty, sell_filled_qty)
        
        # DB에 거래 기록 저장
        trade_data = {
            'timestamp': now,
            'price': price,
            'quantity': config.TRADE_AMOUNT,
            'filled_quantity': filled_quantity,
            'filled_percent': (filled_quantity / config.TRADE_AMOUNT) * 100 if config.TRADE_AMOUNT > 0 else 0,
            'buy_order_id': buy_order_id,
            'sell_order_id': sell_order_id,
            'buy_filled': buy_filled,
            'sell_filled': sell_filled
        }
        
        trading_bot.db_manager.save_trade(trade_data)
        
        # 7. 거래 결과 로깅 및 텔레그램 알림
        result_msg = generate_trade_result_message(
            price, config.TRADE_AMOUNT, filled_quantity, buy_filled, sell_filled
        )
        
        logger.info(result_msg)
        if trading_bot.telegram_sender:
            trading_bot.telegram_sender(result_msg)
        
        return True
        
    except Exception as e:
        error_msg = f"거래 실행 중 오류 발생: {str(e)}"
        logger.error(error_msg)
        
        # 오류 발생 시 미체결 주문 취소 시도
        try:
            if buy_order_id:
                trading_bot.api_client.cancel_order(trading_bot.symbol, buy_order_id)
            if sell_order_id:
                trading_bot.api_client.cancel_order(trading_bot.symbol, sell_order_id)
        except Exception as cancel_error:
            logger.error(f"오류 후 주문 취소 중 추가 오류 발생: {str(cancel_error)}")
        
        if trading_bot.telegram_sender:
            trading_bot.telegram_sender(error_msg)
        
        return False

def trading_loop(trading_bot) -> None:
    """
    거래 실행 루프
    
    Args:
        trading_bot: TradingBot 인스턴스
    """
    logger.info("거래 루프 시작")
    
    while trading_bot.running:
        try:
            # 1. 거래 실행
            execute_trade(trading_bot)
            
            # 2. 다음 거래까지 대기 (설정된 범위 내에서 무작위 시간)
            if trading_bot.running:  # 거래 중에 정지되었을 수 있으므로 다시 확인
                wait_time = random.randint(config.MIN_INTERVAL, config.MAX_INTERVAL)
                logger.info(f"다음 거래까지 {wait_time}초 대기")
                
                # 대기 중에도 정지 명령을 확인하기 위해 짧은 간격으로 나누어 대기
                for _ in range(wait_time):
                    if not trading_bot.running:
                        break
                    time.sleep(1)
        
        except Exception as e:
            logger.error(f"거래 루프 중 오류 발생: {str(e)}")
            # 오류 발생 시 짧은 시간 대기 후 재시도
            time.sleep(5)
    
    logger.info("거래 루프 종료")

def check_and_cancel_order(api_client, symbol: str, order_id: str) -> Tuple[bool, float, float]:
    """
    주문 상태를 확인하고 필요시 취소
    
    Args:
        api_client: MEXC API 클라이언트
        symbol: 거래 페어 심볼
        order_id: 주문 ID
        
    Returns:
        (완전 체결 여부, 체결 수량, 체결 가격) 튜플
    """
    try:
        # 주문 상태 조회
        order_status = api_client.get_order_status(symbol, order_id)
        
        # 이미 완전히 체결된 경우
        if order_status.get('status') == 'FILLED':
            filled_qty = float(order_status.get('executedQty', 0))
            avg_price = float(order_status.get('price', 0))
            logger.info(f"주문 {order_id} 완전 체결됨 - 수량: {filled_qty}, 가격: {avg_price}")
            return True, filled_qty, avg_price
        
        # 부분 체결 또는 미체결 상태인 경우
        else:
            # 체결된 수량 확인
            filled_qty = float(order_status.get('executedQty', 0))
            avg_price = float(order_status.get('price', 0))
            
            # 주문 취소
            api_client.cancel_order(symbol, order_id)
            logger.info(f"주문 {order_id} 취소됨 - 체결 수량: {filled_qty}, 가격: {avg_price}")
            
            return False, filled_qty, avg_price
    
    except Exception as e:
        logger.error(f"주문 {order_id} 상태 확인/취소 중 오류: {str(e)}")
        # 오류 발생 시 안전을 위해 주문 취소 시도
        try:
            api_client.cancel_order(symbol, order_id)
        except:
            pass
        return False, 0, 0

def generate_trade_result_message(price: float, total_qty: float, filled_qty: float, 
                                buy_filled: bool, sell_filled: bool) -> str:
    """
    거래 결과 메시지 생성
    
    Args:
        price: 거래 가격
        total_qty: 총 주문 수량
        filled_qty: 체결된 수량
        buy_filled: 매수 주문 완전 체결 여부
        sell_filled: 매도 주문 완전 체결 여부
        
    Returns:
        결과 메시지 문자열
    """
    filled_percent = (filled_qty / total_qty * 100) if total_qty > 0 else 0
    
    status_emoji = "✅" if filled_qty > 0 else "⚠️"
    if filled_qty == 0:
        status_text = "미체결"
    elif filled_qty < total_qty:
        status_text = "부분 체결"
    else:
        status_text = "완전 체결"
    
    buy_status = "완전 체결" if buy_filled else "부분/미체결"
    sell_status = "완전 체결" if sell_filled else "부분/미체결"
    
    # 거래 결과 메시지 생성
    message = (
        f"{status_emoji} 거래 결과: {status_text}\n"
        f"가격: {price:.8f}\n"
        f"수량: {filled_qty}/{total_qty} ({filled_percent:.1f}%)\n"
        f"매수 상태: {buy_status}\n"
        f"매도 상태: {sell_status}\n"
        f"시간: {datetime.now().strftime('%H:%M:%S')}"
    )
    
    return message