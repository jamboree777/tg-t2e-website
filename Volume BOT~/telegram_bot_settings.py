"""
텔레그램 봇 모듈 - 설정 변경 기능
이 모듈은 텔레그램 봇의 설정 변경 기능을 구현합니다.
"""
import logging

import config

logger = logging.getLogger(__name__)

def handle_interval_setting_impl(handler, message) -> None:
    """거래 간격 설정 처리 - 관리자만 가능"""
    if not handler._is_authorized(message):
        return
    
    if not handler._is_admin(message):
        return
    
    try:
        parts = message.text.split()
        
        if len(parts) != 3:
            handler.bot.reply_to(message, "❌ 형식이 올바르지 않습니다. 예) 거래간격 30 50")
            return
        
        min_val = int(parts[1])
        max_val = int(parts[2])
        
        # 자동으로 작은 값을 최소값으로 설정
        min_val, max_val = min(min_val, max_val), max(min_val, max_val)
        
        # 유효성 검사
        if min_val < 5:
            handler.bot.reply_to(message, "⚠️ 최소 간격은 5초 이상이어야 합니다.")
            return
        
        # 설정 변경
        config.MIN_INTERVAL = min_val
        config.MAX_INTERVAL = max_val
        
        # 모든 사용자에게 알림
        success_msg = f"✅ 거래 간격이 {min_val}-{max_val}초로 설정되었습니다."
        handler.bot.reply_to(message, success_msg)
        
        # 다른 접속 사용자에게도 알림
        for user_id in handler.connected_users:
            if user_id != message.from_user.id and isinstance(user_id, int):
                try:
                    handler.bot.send_message(user_id, f"🔄 관리자가 거래 간격을 {min_val}-{max_val}초로 변경했습니다.")
                except:
                    pass
    
    except ValueError:
        handler.bot.reply_to(message, "❌ 숫자 형식이 올바르지 않습니다. 예) 거래간격 30 50")
    except Exception as e:
        handler.bot.reply_to(message, f"❌ 오류 발생: {str(e)}")

def handle_price_setting_impl(handler, message) -> None:
    """가격 범위 설정 처리 - 관리자만 가능"""
    if not handler._is_authorized(message):
        return
    
    if not handler._is_admin(message):
        return
    
    try:
        parts = message.text.split()
        
        if len(parts) != 3:
            handler.bot.reply_to(message, "❌ 형식이 올바르지 않습니다. 예) 가격범위 10 12")
            return
        
        min_price = float(parts[1])
        max_price = float(parts[2])
        
        # 자동으로 작은 값을 최소값으로 설정
        min_price, max_price = min(min_price, max_price), max(min_price, max_price)
        
        # 유효성 검사
        if min_price <= 0:
            handler.bot.reply_to(message, "⚠️ 가격은 0보다 커야 합니다.")
            return
        
        # 설정 변경
        config.MIN_PRICE = min_price
        config.MAX_PRICE = max_price
        
        # 사용자에게 알림
        success_msg = f"✅ 가격 범위가 {min_price}-{max_price}$로 설정되었습니다."
        handler.bot.reply_to(message, success_msg)
        
        # 다른 접속 사용자에게도 알림
        for user_id in handler.connected_users:
            if user_id != message.from_user.id and isinstance(user_id, int):
                try:
                    handler.bot.send_message(user_id, f"🔄 관리자가 가격 범위를 {min_price}-{max_price}$로 변경했습니다.")
                except:
                    pass
    
    except ValueError:
        handler.bot.reply_to(message, "❌ 숫자 형식이 올바르지 않습니다. 예) 가격범위 10 12")
    except Exception as e:
        handler.bot.reply_to(message, f"❌ 오류 발생: {str(e)}")

def handle_amount_setting_impl(handler, message) -> None:
    """거래 금액 설정 처리 - 관리자만 가능"""
    if not handler._is_authorized(message):
        return
    
    if not handler._is_admin(message):
        return
    
    try:
        parts = message.text.split()
        
        if len(parts) != 2:
            handler.bot.reply_to(message, "❌ 형식이 올바르지 않습니다. 예) 거래금액 10.5")
            return
        
        amount = float(parts[1])
        
        # 유효성 검사
        if amount <= 0:
            handler.bot.reply_to(message, "⚠️ 금액은 0보다 커야 합니다.")
            return
        
        # 설정 변경
        config.TRADE_AMOUNT_USDT = amount
        
        # 사용자에게 알림
        success_msg = f"✅ 거래 금액이 {amount} {config.QUOTE_CURRENCY}로 설정되었습니다."
        handler.bot.reply_to(message, success_msg)
        
        # 다른 접속 사용자에게도 알림
        for user_id in handler.connected_users:
            if user_id != message.from_user.id and isinstance(user_id, int):
                try:
                    handler.bot.send_message(user_id, f"🔄 관리자가 거래 금액을 {amount} {config.QUOTE_CURRENCY}로 변경했습니다.")
                except:
                    pass
    
    except ValueError:
        handler.bot.reply_to(message, "❌ 숫자 형식이 올바르지 않습니다. 예) 거래금액 10.5")
    except Exception as e:
        handler.bot.reply_to(message, f"❌ 오류 발생: {str(e)}")



        """
텔레그램 봇 모듈 - 설정 변경 기능 추가 부분
이 모듈은 telegram_bot_settings.py의 계속 부분입니다.
"""
import logging

import config

logger = logging.getLogger(__name__)

def handle_min_usdt_setting_impl(handler, message) -> None:
    """최소 USDT 잔고 설정 처리 - 관리자만 가능"""
    if not handler._is_authorized(message):
        return
    
    if not handler._is_admin(message):
        return
    
    try:
        parts = message.text.split()
        
        if len(parts) != 2:
            handler.bot.reply_to(message, "❌ 형식이 올바르지 않습니다. 예) 최소USDT 100")
            return
        
        min_usdt = float(parts[1])
        
        # 유효성 검사
        if min_usdt < 0:
            handler.bot.reply_to(message, "⚠️ 최소 잔고는 0 이상이어야 합니다.")
            return
        
        # 설정 변경
        config.MIN_USDT_BALANCE = min_usdt
        
        # 사용자에게 알림
        success_msg = f"✅ 최소 {config.QUOTE_CURRENCY} 잔고가 {min_usdt}로 설정되었습니다."
        handler.bot.reply_to(message, success_msg)
        
        # 다른 접속 사용자에게도 알림
        for user_id in handler.connected_users:
            if user_id != message.from_user.id and isinstance(user_id, int):
                try:
                    handler.bot.send_message(user_id, f"🔄 관리자가 최소 {config.QUOTE_CURRENCY} 잔고를 {min_usdt}로 변경했습니다.")
                except:
                    pass
    
    except ValueError:
        handler.bot.reply_to(message, "❌ 숫자 형식이 올바르지 않습니다. 예) 최소USDT 100")
    except Exception as e:
        handler.bot.reply_to(message, f"❌ 오류 발생: {str(e)}")

def handle_min_token_setting_impl(handler, message) -> None:
    """최소 토큰 잔고 설정 처리 - 관리자만 가능"""
    if not handler._is_authorized(message):
        return
    
    if not handler._is_admin(message):
        return
    
    try:
        parts = message.text.split()
        
        if len(parts) != 2:
            handler.bot.reply_to(message, "❌ 형식이 올바르지 않습니다. 예) 최소토큰 500")
            return
        
        min_token = float(parts[1])
        
        # 유효성 검사
        if min_token < 0:
            handler.bot.reply_to(message, "⚠️ 최소 잔고는 0 이상이어야 합니다.")
            return
        
        # 설정 변경
        config.MIN_TOKEN_BALANCE = min_token
        
        # 사용자에게 알림
        success_msg = f"✅ 최소 {config.TOKEN_NAME} 잔고가 {min_token}로 설정되었습니다."
        handler.bot.reply_to(message, success_msg)
        
        # 다른 접속 사용자에게도 알림
        for user_id in handler.connected_users:
            if user_id != message.from_user.id and isinstance(user_id, int):
                try:
                    handler.bot.send_message(user_id, f"🔄 관리자가 최소 {config.TOKEN_NAME} 잔고를 {min_token}로 변경했습니다.")
                except:
                    pass
    
    except ValueError:
        handler.bot.reply_to(message, "❌ 숫자 형식이 올바르지 않습니다. 예) 최소토큰 500")
    except Exception as e:
        handler.bot.reply_to(message, f"❌ 오류 발생: {str(e)}")

def handle_unknown_impl(handler, message) -> None:
    """알 수 없는 명령어 처리"""
    if not handler._is_authorized(message):
        return
    
    help_suggestion = "지원되지 않는 명령어입니다. 도움말은 111을 입력하세요."
    handler.bot.reply_to(message, help_suggestion)