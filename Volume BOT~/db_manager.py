"""
데이터베이스 관리 모듈
이 모듈은 거래 데이터 저장 및 조회를 담당합니다.
"""
import sqlite3
import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

import config

logger = logging.getLogger(__name__)

class DBManager:
    """데이터베이스 관리 클래스"""
    
    def __init__(self, db_file: str = None):
        """
        데이터베이스 매니저 초기화
        
        Args:
            db_file: 데이터베이스 파일 경로
        """
        self.db_file = db_file or config.DB_FILE
        self._initialize_db()
    
    def _initialize_db(self) -> None:
        """데이터베이스 초기화 및 테이블 생성"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # 거래 테이블 생성
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                price REAL NOT NULL,
                quantity REAL NOT NULL,
                filled_quantity REAL NOT NULL,
                filled_percent REAL NOT NULL,
                buy_order_id TEXT,
                sell_order_id TEXT,
                buy_filled INTEGER,
                sell_filled INTEGER,
                data TEXT
            )
            ''')
            
            # 설정 테이블 생성
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TEXT
            )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("데이터베이스가 초기화되었습니다.")
        
        except Exception as e:
            logger.error(f"데이터베이스 초기화 중 오류 발생: {str(e)}")
    
    def save_trade(self, trade_data: Dict) -> bool:
        """
        거래 데이터 저장
        
        Args:
            trade_data: 거래 데이터 딕셔너리
            
        Returns:
            저장 성공 여부
        """
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # 기본 필드 추출
            timestamp = trade_data.get('timestamp', datetime.now())
            price = trade_data.get('price', 0.0)
            quantity = trade_data.get('quantity', 0.0)
            filled_quantity = trade_data.get('filled_quantity', 0.0)
            filled_percent = trade_data.get('filled_percent', 0.0)
            buy_order_id = trade_data.get('buy_order_id', '')
            sell_order_id = trade_data.get('sell_order_id', '')
            buy_filled = 1 if trade_data.get('buy_filled', False) else 0
            sell_filled = 1 if trade_data.get('sell_filled', False) else 0
            
            # 추가 데이터를 JSON으로 직렬화
            data_json = json.dumps(trade_data)
            
            # 타임스탬프 형식 변환
            if isinstance(timestamp, datetime):
                timestamp = timestamp.isoformat()
            
            # SQL 쿼리 실행
            cursor.execute('''
            INSERT INTO trades (
                timestamp, price, quantity, filled_quantity, filled_percent,
                buy_order_id, sell_order_id, buy_filled, sell_filled, data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                timestamp, price, quantity, filled_quantity, filled_percent,
                buy_order_id, sell_order_id, buy_filled, sell_filled, data_json
            ))
            
            conn.commit()
            conn.close()
            
            logger.debug(f"거래 데이터가 저장되었습니다. ID: {cursor.lastrowid}")
            return True
        
        except Exception as e:
            logger.error(f"거래 데이터 저장 중 오류 발생: {str(e)}")
            return False
    
    def get_recent_trades(self, count: int = 10) -> List[Dict]:
        """
        최근 거래 내역 조회
        
        Args:
            count: 조회할 거래 수
            
        Returns:
            거래 내역 리스트
        """
        try:
            conn = sqlite3.connect(self.db_file)
            conn.row_factory = sqlite3.Row  # 결과를 딕셔너리 형태로 반환
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT * FROM trades
            ORDER BY id DESC
            LIMIT ?
            ''', (count,))
            
            rows = cursor.fetchall()
            trades = []
            
            for row in rows:
                trade = dict(row)
                # JSON 데이터 파싱
                if 'data' in trade and trade['data']:
                    try:
                        additional_data = json.loads(trade['data'])
                        # 기본 필드에 추가 데이터 병합
                        for key, value in additional_data.items():
                            if key not in trade:
                                trade[key] = value
                    except:
                        pass
                
                trades.append(trade)
            
            conn.close()
            return trades
        
        except Exception as e:
            logger.error(f"거래 내역 조회 중 오류 발생: {str(e)}")
            return []
    
    def get_total_volume(self) -> float:
        """
        총 거래량 조회
        
        Returns:
            총 체결 거래량
        """
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT SUM(filled_quantity) FROM trades
            ''')
            
            result = cursor.fetchone()
            conn.close()
            
            total_volume = result[0] if result[0] is not None else 0
            return float(total_volume)
        
        except Exception as e:
            logger.error(f"총 거래량 조회 중 오류 발생: {str(e)}")
            return 0.0
    
    # db_manager_extended.py로 나머지 메서드 이동
    def load_settings(self):
        """db_manager_extended.py로 구현 이동됨"""
        from db_manager_extended import load_settings
        return load_settings(self)