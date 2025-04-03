"""
텔레그램 봇 모듈 - 명령어 처리 기능
이 모듈은 텔레그램 봇의 명령어 처리 기능을 구현합니다.
"""
import logging
from datetime import datetime

import config

logger = logging.getLogger(__name__)

def handle_000_impl(handler, message) -> None:
    """긴급 정지 명령 처리 - 관리자만 가능"""
    if not handler._is_admin(message):
        return
    
    try:
        # 거래 봇 정지
        was_running = handler.trading_bot.running
        result = handler.trading_bot.stop()
        
        if result:
            # 상태 메시지 생성
            timestamp = datetime.now().strftime("%m/%d %H:%M:%S")
            status_text = f"🛑 {timestamp} 긴급 정지 명령 실행\n"
            
            if was_running:
                status_text += "모든 매수 작업이 중지되었습니다."
            else:
                status_text += "봇이 이미 정지 상태였습니다."
            
            # 메시지 전송
            handler.bot.reply_to(message, status_text)
            handler.bot.send_message(
                message.chat.id, 
                "⚠️ 주의: 이미 제출된 주문은 취소되지 않을 수 있습니다."
            )
        else:
            handler.bot.reply_to(message, "❌ 봇 정지 중 오류가 발생했습니다.")
    
    except Exception as e:
        handler.bot.reply_to(message, f"❌ 오류 발생: {str(e)}")

def handle_111_impl(handler, message) -> None:
    """명령어 안내 처리"""
    # 관리자 여부 확인
    is_admin = handler._is_admin(message)
    
    help_text = """
📋 명령어 안내:
000 - 긴급 시스템 정지 (관리자 전용)
111 - 명령어 안내 (현재 메뉴)
333 - 최근 10개 거래내역 조회
555 - 현재 상태 및 잔고 확인
777 - 봇 실행 (관리자 전용)
999 - 설정값 변경 안내 (관리자 전용)

"""
    
    # 관리자인 경우에만 설정 변경 명령어 표시
    if is_admin:
        help_text += """
📝 설정 변경 명령어 (관리자 전용):
거래간격 [최소] [최대] - 예) 거래간격 30 50
가격범위 [최소] [최대] - 예) 가격범위 10 12
거래금액 [USDT금액] - 예) 거래금액 10.5
최소USDT [금액] - 예) 최소USDT 100
최소토큰 [수량] - 예) 최소토큰 500
"""
    
    handler.bot.reply_to(message, help_text)

def handle_333_impl(handler, message) -> None:
    """거래 내역 조회 처리"""
    if not handler._is_authorized(message):
        return
    
    try:
        # 최근 거래 내역 조회
        trades = handler.trading_bot.get_trade_history(10)
        
        if not trades:
            handler.bot.reply_to(message, "📊 아직 거래 내역이 없습니다.")
            return
        
        # 거래 내역 포맷팅
        history_text = "📊 최근 10개 거래내역:\n"
        
        for i, trade in enumerate(trades, 1):
            # 거래 시간 파싱
            try:
                timestamp = datetime.fromisoformat(trade.get('timestamp', '')).strftime("%m/%d %H:%M:%S")
            except:
                timestamp = trade.get('timestamp', 'N/A')
            
            price = trade.get('price', 0)
            usdt_amount = trade.get('usdt_amount', 0)
            filled_usdt = trade.get('filled_usdt_amount', 0)
            filled_percent = trade.get('filled_percent', 0)
            
            trade_line = (
                f"#{i} - {timestamp} | "
                f"금액: {filled_usdt:.2f}/{usdt_amount:.2f} USDT ({filled_percent:.1f}%) | "
                f"가격: {price:.4f}\n"
            )
            
            history_text += trade_line
        
        # 메시지 전송
        handler.bot.reply_to(message, history_text)
    
    except Exception as e:
        handler.bot.reply_to(message, f"❌ 거래 내역 조회 중 오류 발생: {str(e)}")

def handle_555_impl(handler, message) -> None:
    """상태 확인 처리"""
    if not handler._is_authorized(message):
        return
    
    try:
        # 봇 상태 조회
        status = handler.trading_bot.get_status()
        
        # 상태 메시지 생성
        running_status = "✅ 실행 중" if status['running'] else "⛔ 정지됨"
        running_time = status.get('running_time', '')
        if running_time:
            running_status += f" ({running_time})"
        
        settings = status.get('settings', {})
        
        status_text = (
            f"📈 현재 상태:\n"
            f"실행 상태: {running_status}\n"
            f"{status['quote_currency']} 잔고: {status['usdt_balance']:.2f}\n"
            f"{status['token_name']} 잔고: {status['token_balance']:.6f}\n\n"
            
            f"⚙️ 현재 설정:\n"
            f"- 주문 간격: {settings['min_interval']}-{settings['max_interval']}초\n"
            f"- 가격 범위: {settings['min_price']}-{settings['max_price']}$\n"
            f"- 거래 금액: {settings['trade_amount_usdt']} {status['quote_currency']}/주문\n"
            f"- 최소 잔고: {settings['min_usdt_balance']} {status['quote_currency']}, "
            f"{settings['min_token_balance']} {status['token_name']}\n\n"
            
            f"📊 거래 정보:\n"
            f"- 누적 거래: {status['trade_count']}건 (총 {status['total_volume']:.6f} {status['token_name']})\n"
            f"- 접속 중인 사용자: {len(handler.connected_users)}명\n"
        )
        
        if status['last_trade_time']:
            last_trade = status['last_trade_time'].strftime("%H:%M:%S") if isinstance(status['last_trade_time'], datetime) else status['last_trade_time']
            status_text += f"- 마지막 거래: {last_trade}\n"
        
        # 메시지 전송
        handler.bot.reply_to(message, status_text)
    
    except Exception as e:
        handler.bot.reply_to(message, f"❌ 상태 확인 중 오류 발생: {str(e)}")

def handle_777_impl(handler, message) -> None:
    """봇 실행 처리 - 관리자만 가능"""
    if not handler._is_authorized(message):
        return
    
    if not handler._is_admin(message):
        return
    
    try:
        # 이미 실행 중인지 확인
        if handler.trading_bot.running:
            handler.bot.reply_to(message, "이미 자동 매매가 실행 중입니다. 중지하려면 000을 입력하세요.")
            return
        
        # 현재 설정 출력
        settings = handler.trading_bot.get_status().get('settings', {})
        symbol = config.SYMBOL
        
        status_text = (
            f"🚀 거래 봇 실행 준비 중...\n\n"
            f"현재 설정:\n"
            f"- 심볼: {symbol}\n"
            f"- 주문 간격: {settings['min_interval']}-{settings['max_interval']}초\n"
            f"- 가격 범위: {settings['min_price']}-{settings['max_price']}$\n"
            f"- 거래 금액: {settings['trade_amount_usdt']} {config.QUOTE_CURRENCY}/주문\n"
            f"- 최소 잔고: {settings['min_usdt_balance']} {config.QUOTE_CURRENCY}, "
            f"{settings['min_token_balance']} {config.TOKEN_NAME}\n\n"
            f"위 설정으로 실행하시겠습니까? (1=실행, 0=취소)"
        )
        
        handler.bot.reply_to(message, status_text)
        handler.bot.register_next_step_handler(message, handler.process_start_confirmation)
    
    except Exception as e:
        handler.bot.reply_to(message, f"❌ 오류 발생: {str(e)}")

def process_start_confirmation_impl(handler, message) -> None:
    """봇 실행 확인 처리"""
    if not handler._is_authorized(message):
        return
    
    if not handler._is_admin(message):
        return
    
    try:
        answer = message.text.strip()
        
        if answer == '1':
            # 봇 시작
            result = handler.trading_bot.start()
            
            if result:
                # 모든 접속 사용자에게 알림
                start_msg = "✅ 봇이 성공적으로 시작되었습니다!"
                handler.bot.reply_to(message, start_msg)
                
                # 다른 접속 사용자에게도 알림
                for user_id in handler.connected_users:
                    if user_id != message.from_user.id and isinstance(user_id, int):
                        try:
                            handler.bot.send_message(user_id, f"🚀 관리자에 의해 봇이 시작되었습니다!")
                        except:
                            pass
                
                # 시장 상태 조회
                try:
                    bid1, ask1 = handler.api_client.get_bid_ask(config.SYMBOL)
                    market_info = f"시장 상태: Bid1={bid1:.8f}$, Ask1={ask1:.8f}$"
                    handler.bot.send_message(message.chat.id, market_info)
                except:
                    pass
            else:
                handler.bot.reply_to(message, "❌ 봇 시작에 실패했습니다. 설정과 잔고를 확인하세요.")
        
        else:
            handler.bot.reply_to(message, "❌ 봇 실행이 취소되었습니다.")
    
    except Exception as e:
        handler.bot.reply_to(message, f"❌ 오류 발생: {str(e)}")

def handle_999_impl(handler, message) -> None:
    """설정 변경 안내 처리 - 관리자만 가능"""
    if not handler._is_authorized(message):
        return
    
    if not handler._is_admin(message):
        return
    
    settings_text = """
⚙️ 설정 변경 명령어:

1️⃣ 거래간격 [최소] [최대]
   예) 거래간격 30 50
   설명: 거래 사이의 대기 시간(초)

2️⃣ 가격범위 [최소] [최대]
   예) 가격범위 10 12
   설명: 거래 가격 범위(USDT)

3️⃣ 거래금액 [USDT금액]
   예) 거래금액 10.5
   설명: 매 거래당 주문 금액(USDT)

4️⃣ 최소USDT [금액]
   예) 최소USDT 100
   설명: 최소 USDT 잔고 설정

5️⃣ 최소토큰 [수량]
   예) 최소토큰 500
   설명: 최소 토큰 잔고 설정

✅ 설정 완료 후 777을 입력하여 봇을 시작하세요.
"""
    handler.bot.reply_to(message, settings_text)