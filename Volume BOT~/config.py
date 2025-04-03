"""
MEXC 자가체결 거래량 생성 봇 설정 파일
이 파일에는 API 키, 시크릿 키, 봇 설정값들이 저장됩니다.
"""
import os

# API 키 설정 (환경 변수에서 불러오거나 직접 입력)
MEXC_API_KEY = os.environ.get("MEXC_API_KEY", "mx0vglWj4l2LZ8p9nK")
MEXC_API_SECRET = os.environ.get("MEXC_API_SECRET", "21714eb2d36f42d888e5f28a695daa61")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN","7899477609:AAGApju5LAJc8Cc2C1Cmpfcl88kF3Ussq9g")  # 환경 변수에서만 가져옴

# 텔레그램 인증 설정
# 최대 6명까지 접속 가능 (사용자 ID 또는 사용자명으로 입력)
AUTHORIZED_USERS = [
    # 사용자 ID (숫자)
    7739042399,  # 관리자 ID
    
    # 사용자명 (문자열)
    "JustinCrepe",  # 일반 사용자
    "Doori8003",    # 일반 사용자
    "danielhhchoi", # 일반 사용자
    "onchain_federation"  # 일반 사용자
]

# 관리자 목록 - 중요 명령어를 실행할 수 있는 사용자
ADMIN_USERS = [
    # 사용자 ID (숫자)
    165706381,  # 관리자 ID
    
    # 사용자명 (문자열)
    "purple_in_the_zone"  # 관리자 사용자명
]

# 거래 설정
SYMBOL = "CREPE_USDT"  # 거래 페어 심볼
TOKEN_NAME = SYMBOL.split('_')[0]  # 토큰 이름 (예: BTC)
QUOTE_CURRENCY = SYMBOL.split('_')[1]  # 쿼팅 통화 (예: USDT)

# 주문 설정
TRADE_AMOUNT_USDT = 10.0  # 주문당 거래 금액 (USDT 단위)
MIN_PRICE = 10.0  # 최소 가격 범위 (USDT 단위)
MAX_PRICE = 12.0  # 최대 가격 범위 (USDT 단위)
MIN_INTERVAL = 30  # 주문 간 최소 간격 (초)
MAX_INTERVAL = 50  # 주문 간 최대 간격 (초)
CANCEL_DELAY = 1   # 주문 취소 지연 시간 (초)

# 잔고 안전장치
MIN_USDT_BALANCE = 100.0  # 최소 USDT 잔고
MIN_TOKEN_BALANCE = 500.0  # 최소 토큰 잔고

# 로깅 설정
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE = "trading_bot.log"
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
LOG_BACKUP_COUNT = 5  # 로그 백업 파일 수

# 데이터베이스 설정 (거래 기록 저장용)
DB_FILE = "trading_data.db"

# 거래소 API 설정
API_BASE_URL = "https://api.mexc.com"
API_VERSION = "v3"
API_TIMEOUT = 10  # API 요청 타임아웃 (초)
MAX_RETRIES = 3   # API 요청 재시도 횟수

# 오류 메시지
ERROR_MESSAGES = {
    "api_error": "MEXC API 오류가 발생했습니다: {}",
    "balance_low": "잔고가 최소 허용치 아래로 떨어졌습니다. 거래가 중지됩니다.",
    "not_authorized": "이 봇을 사용할 권한이 없습니다.",
    "invalid_input": "잘못된 입력입니다. 다시 시도하세요.",
    "bot_running": "봇이 이미 실행 중입니다.",
    "bot_not_running": "봇이 실행 중이 아닙니다."
}

# 성공 메시지
SUCCESS_MESSAGES = {
    "bot_started": "봇이 성공적으로 시작되었습니다.",
    "bot_stopped": "봇이 중지되었습니다.",
    "settings_updated": "설정이 업데이트되었습니다."
}

# 명령어 도움말
HELP_TEXT = """
📋 명령어 안내:
000 - 긴급 시스템 정지
111 - 명령어 안내 (현재 메뉴)
333 - 최근 10개 거래내역 조회
555 - 현재 상태 및 잔고 확인
777 - 봇 실행 (현재 설정값 사용)
999 - 설정값 변경 안내
"""