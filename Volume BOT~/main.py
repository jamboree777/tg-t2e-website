"""
메인 애플리케이션 모듈
이 모듈은 애플리케이션의 진입점입니다.
"""
import sys
import signal
import logging
import traceback
from typing import Any

import config
from mexc_api_client import MexcApiClient
from trading_logic import TradingBot
from db_manager import DBManager
from telegram_bot_core import TelegramBotHandler
from utils import setup_logging

# 전역 변수
api_client = None
db_manager = None
trading_bot = None
telegram_bot = None

def signal_handler(sig: int, frame: Any) -> None:
    """시그널 핸들러"""
    logging.info(f"시그널 {sig}을(를) 받았습니다. 프로그램을 종료합니다.")
    
    # 봇 정지
    if trading_bot is not None and trading_bot.running:
        logging.info("거래 봇을 정지합니다...")
        trading_bot.stop()
    
    # 알림 전송
    if telegram_bot is not None:
        telegram_bot.send_message("프로그램이 종료되었습니다.")
    
    sys.exit(0)

def setup_signal_handlers() -> None:
    """시그널 핸들러 설정"""
    signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # 종료 시그널

def initialize() -> bool:
    """애플리케이션 초기화"""
    global api_client, db_manager, trading_bot, telegram_bot
    
    try:
        # 로깅 설정
        setup_logging()
        logging.info("애플리케이션 시작 중...")
        
        # API 클라이언트 초기화
        api_client = MexcApiClient(config.MEXC_API_KEY, config.MEXC_API_SECRET)
        logging.info("MEXC API 클라이언트가 초기화되었습니다.")
        
        # 데이터베이스 매니저 초기화
        db_manager = DBManager()
        logging.info("데이터베이스 매니저가 초기화되었습니다.")
        
        # 거래 봇 초기화
        trading_bot = TradingBot(api_client, db_manager)
        logging.info("거래 봇이 초기화되었습니다.")
        
        # 텔레그램 봇 초기화
        telegram_bot = TelegramBotHandler(api_client, db_manager)
        logging.info("텔레그램 봇이 초기화되었습니다.")
        
        # 시그널 핸들러 설정
        setup_signal_handlers()
        
        return True
    
    except Exception as e:
        logging.error(f"초기화 중 오류 발생: {str(e)}")
        logging.error(traceback.format_exc())
        return False

def run() -> None:
    """애플리케이션 실행"""
    try:
        if not initialize():
            logging.error("초기화 실패. 프로그램을 종료합니다.")
            return
        
        # 시작 메시지 전송
        if telegram_bot is not None:
            telegram_bot.send_message("MEXC 자가체결 거래량 생성 봇이 시작되었습니다. 명령어 목록은 111을 입력하세요.")
        
        # 텔레그램 봇 실행
        if telegram_bot is not None:
            logging.info("텔레그램 봇 실행 중...")
            telegram_bot.start()
        
        logging.info("애플리케이션 종료.")
    
    except Exception as e:
        logging.error(f"실행 중 오류 발생: {str(e)}")
        logging.error(traceback.format_exc())
        
        # 오류 알림 전송
        if telegram_bot is not None:
            telegram_bot.send_message(f"오류로 인해 프로그램이 종료됩니다: {str(e)}")

if __name__ == "__main__":
    run()