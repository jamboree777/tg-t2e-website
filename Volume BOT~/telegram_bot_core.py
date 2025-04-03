"""
텔레그램 봇 모듈 - 핵심 기능
이 모듈은 텔레그램 봇 인터페이스의 핵심 기능을 구현합니다.
"""
import logging
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

import telebot
from telebot import types

import config
from trading_logic import TradingBot
from mexc_api_client import MexcApiClient
from db_manager import DBManager

logger = logging.getLogger(__name__)

class TelegramBotHandler:
    """텔레그램 봇 핸들러 클래스"""
    
    def __init__(self, api_client: MexcApiClient, db_manager: DBManager):
        """텔레그램 봇 핸들러 초기화"""
        self.api_client = api_client
        self.db_manager = db_manager
        self.bot = telebot.TeleBot(config.TELEGRAM_BOT_TOKEN)
        self.trading_bot = TradingBot(api_client, db_manager, self.send_message)
        
        # 접속한 사용자 수 카운트
        self.connected_users = set()
        
        # 봇 명령어 처리 함수 등록
        self._register_handlers()
        
    def _register_handlers(self) -> None:
        """봇 명령어 핸들러 등록"""
        # 숫자 명령어 핸들러
        self.bot.message_handler(func=lambda message: message.text == '000')(self._check_auth(self.handle_000))
        self.bot.message_handler(func=lambda message: message.text == '111')(self._check_auth(self.handle_111))
        self.bot.message_handler(func=lambda message: message.text == '333')(self._check_auth(self.handle_333))
        self.bot.message_handler(func=lambda message: message.text == '555')(self._check_auth(self.handle_555))
        self.bot.message_handler(func=lambda message: message.text == '777')(self._check_auth(self.handle_777))
        self.bot.message_handler(func=lambda message: message.text == '999')(self._check_auth(self.handle_999))
        
        # 키워드 명령어 핸들러 (설정 변경)
        self.bot.message_handler(func=lambda m: m.text.startswith('거래간격'))(self._check_auth(self.handle_interval_setting))
        self.bot.message_handler(func=lambda m: m.text.startswith('가격범위'))(self._check_auth(self.handle_price_setting))
        self.bot.message_handler(func=lambda m: m.text.startswith('거래금액'))(self._check_auth(self.handle_amount_setting))
        self.bot.message_handler(func=lambda m: m.text.startswith('최소USDT'))(self._check_auth(self.handle_min_usdt_setting))
        self.bot.message_handler(func=lambda m: m.text.startswith('최소토큰'))(self._check_auth(self.handle_min_token_setting))
        
        # 기타 메시지 핸들러
        self.bot.message_handler(func=lambda message: True)(self._check_auth(self.handle_unknown))
    
    def _check_auth(self, handler_func):
        """인증 체크 데코레이터"""
        def wrapper(message):
            if not self._is_authorized(message):
                return
            return handler_func(message)
        return wrapper
    
    def start(self) -> None:
        """봇 시작"""
        logger.info("텔레그램 봇 시작")
        self.bot.infinity_polling(timeout=60, long_polling_timeout=30)
    
    def send_message(self, message: str, chat_id: Optional[int] = None) -> None:
        """텔레그램 메시지 전송"""
        if chat_id:
            try:
                self.bot.send_message(chat_id, message)
            except Exception as e:
                logger.error(f"메시지 전송 실패 (ID: {chat_id}): {str(e)}")
        else:
            # 모든 인증된 사용자에게 전송
            for user_id in self.connected_users:
                try:
                    # user_id가 문자열인 경우 (사용자명) 건너뛰기
                    if isinstance(user_id, int):
                        self.bot.send_message(user_id, message)
                except Exception as e:
                    logger.error(f"메시지 전송 실패 (ID: {user_id}): {str(e)}")
    
    def _is_authorized(self, message) -> bool:
        """사용자 인증 확인"""
        try:
            user_id = message.from_user.id
            username = message.from_user.username
            
            logger.info(f"=== 인증 시도 상세 정보 ===")
            logger.info(f"사용자 ID: {user_id} (타입: {type(user_id)})")
            logger.info(f"사용자명: {username} (타입: {type(username)})")
            logger.info(f"인증된 사용자 목록: {config.AUTHORIZED_USERS}")
            logger.info(f"관리자 목록: {config.ADMIN_USERS}")
            
            # 사용자 ID를 정수로 변환
            user_id = int(user_id)
            
            # 관리자 목록 확인
            for admin in config.ADMIN_USERS:
                logger.info(f"관리자 비교: {admin} (타입: {type(admin)})")
                if isinstance(admin, int) and admin == user_id:
                    logger.info(f"ID로 관리자 인증 성공: {user_id}")
                    if len(self.connected_users) < 6 or user_id in self.connected_users:
                        self.connected_users.add(user_id)
                        return True
                    else:
                        logger.warning(f"최대 접속자 수 초과: {len(self.connected_users)}")
                        self.bot.reply_to(message, "최대 접속 인원(6명)을 초과했습니다.")
                        return False
                if isinstance(admin, str) and admin.lower() == username.lower():
                    logger.info(f"사용자명으로 관리자 인증 성공: {username}")
                    if len(self.connected_users) < 6 or user_id in self.connected_users:
                        self.connected_users.add(user_id)
                        return True
                    else:
                        logger.warning(f"최대 접속자 수 초과: {len(self.connected_users)}")
                        self.bot.reply_to(message, "최대 접속 인원(6명)을 초과했습니다.")
                        return False
                    
            # 인증된 사용자 목록 확인
            for auth in config.AUTHORIZED_USERS:
                logger.info(f"인증된 사용자 비교: {auth} (타입: {type(auth)})")
                if isinstance(auth, int) and auth == user_id:
                    logger.info(f"ID로 일반 사용자 인증 성공: {user_id}")
                    if len(self.connected_users) < 6 or user_id in self.connected_users:
                        self.connected_users.add(user_id)
                        return True
                    else:
                        logger.warning(f"최대 접속자 수 초과: {len(self.connected_users)}")
                        self.bot.reply_to(message, "최대 접속 인원(6명)을 초과했습니다.")
                        return False
                if isinstance(auth, str) and auth.lower() == username.lower():
                    logger.info(f"사용자명으로 일반 사용자 인증 성공: {username}")
                    if len(self.connected_users) < 6 or user_id in self.connected_users:
                        self.connected_users.add(user_id)
                        return True
                    else:
                        logger.warning(f"최대 접속자 수 초과: {len(self.connected_users)}")
                        self.bot.reply_to(message, "최대 접속 인원(6명)을 초과했습니다.")
                        return False
                    
            logger.warning(f"인증 실패 - ID: {user_id}, Username: {username}")
            self.bot.reply_to(message, "이 봇을 사용할 권한이 없습니다.")
            return False
            
        except Exception as e:
            logger.error(f"인증 확인 중 오류 발생: {str(e)}")
            self.bot.reply_to(message, "인증 확인 중 오류가 발생했습니다.")
            return False
    
    def _is_admin(self, message) -> bool:
        """관리자 인증 확인"""
        user_id = message.from_user.id
        username = message.from_user.username
        
        logger.info(f"관리자 인증 시도 - ID: {user_id}, Username: {username}")
        logger.info(f"관리자 목록: {config.ADMIN_USERS}")
        
        # ID로 확인 (정수형으로 변환하여 비교)
        user_id_int = int(user_id)
        for auth in config.ADMIN_USERS:
            try:
                if isinstance(auth, (int, str)):
                    auth_id = int(auth) if str(auth).isdigit() else None
                    if auth_id is not None and user_id_int == auth_id:
                        logger.info(f"ID로 관리자 인증 성공: {user_id}")
                        return True
            except (ValueError, TypeError):
                continue
        
        # 사용자명으로 확인 (대소문자 구분 없이 비교)
        if username:
            username_lower = username.lower()
            for auth in config.ADMIN_USERS:
                if isinstance(auth, str) and auth.lower() == username_lower:
                    logger.info(f"사용자명으로 관리자 인증 성공: {username}")
                    return True
        
        logger.warning(f"관리자 인증 실패 - ID: {user_id}, Username: {username}")
        self.bot.reply_to(message, "이 명령어는 관리자만 사용할 수 있습니다.")
        return False
    
    # 명령어 핸들러 함수들 - 각 기능은 다른 모듈에서 구현됨
    def handle_000(self, message):
        """긴급 정지 명령 처리"""
        from telegram_bot_commands import handle_000_impl
        return handle_000_impl(self, message)
    
    def handle_111(self, message):
        """명령어 안내 처리"""
        from telegram_bot_commands import handle_111_impl
        return handle_111_impl(self, message)
    
    def handle_333(self, message):
        """거래 내역 조회 처리"""
        from telegram_bot_commands import handle_333_impl
        return handle_333_impl(self, message)
    
    def handle_555(self, message):
        """상태 확인 처리"""
        from telegram_bot_commands import handle_555_impl
        return handle_555_impl(self, message)
    
    def handle_777(self, message):
        """봇 실행 처리"""
        from telegram_bot_commands import handle_777_impl
        return handle_777_impl(self, message)
    
    def process_start_confirmation(self, message):
        """봇 실행 확인 처리"""
        from telegram_bot_commands import process_start_confirmation_impl
        return process_start_confirmation_impl(self, message)
    
    def handle_999(self, message):
        """설정 변경 안내 처리"""
        from telegram_bot_commands import handle_999_impl
        return handle_999_impl(self, message)
    
    def handle_interval_setting(self, message):
        """거래 간격 설정 처리"""
        from telegram_bot_settings import handle_interval_setting_impl
        return handle_interval_setting_impl(self, message)
    
    def handle_price_setting(self, message):
        """가격 범위 설정 처리"""
        from telegram_bot_settings import handle_price_setting_impl
        return handle_price_setting_impl(self, message)
    
    def handle_amount_setting(self, message):
        """거래 금액 설정 처리"""
        from telegram_bot_settings import handle_amount_setting_impl
        return handle_amount_setting_impl(self, message)
    
    def handle_min_usdt_setting(self, message):
        """최소 USDT 잔고 설정 처리"""
        from telegram_bot_settings import handle_min_usdt_setting_impl
        return handle_min_usdt_setting_impl(self, message)
    
    def handle_min_token_setting(self, message):
        """최소 토큰 잔고 설정 처리"""
        from telegram_bot_settings import handle_min_token_setting_impl
        return handle_min_token_setting_impl(self, message)
    
    def handle_unknown(self, message):
        """알 수 없는 명령어 처리"""
        from telegram_bot_settings import handle_unknown_impl
        return handle_unknown_impl(self, message)