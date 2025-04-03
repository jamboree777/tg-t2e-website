"""
데이터베이스 관리 확장 모듈
이 모듈은 데이터베이스 관리 추가 기능을 제공합니다.
"""
import sqlite3
import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

import config

logger = logging.getLogger(__name__)

def get_trade_count(db_manager) -> int:
    """
    총 거래 건수 조회
    
    Args:
        db_manager: DBManager 인스턴스
        
    Returns:
        총 거래 건수
    """
    try:
        conn = sqlite3.connect(db_manager.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT COUNT(*) FROM trades
        ''')
        
        result = cursor.fetchone()
        conn.close()
        
        count = result[0] if result[0] is not None else 0
        return int(count)
    
    except Exception as e:
        logger.error(f"거래 건수 조회 중 오류 발생: {str(e)}")
        return 0

def save_setting(db_manager, key: str, value: Any) -> bool:
    """
    설정 저장
    
    Args:
        db_manager: DBManager 인스턴스
        key: 설정 키
        value: 설정 값
        
    Returns:
        저장 성공 여부
    """
    try:
        conn = sqlite3.connect(db_manager.db_file)
        cursor = conn.cursor()
        
        # 값을 JSON으로 직렬화
        value_json = json.dumps(value)
        now = datetime.now().isoformat()
        
        # 저장 또는 업데이트
        cursor.execute('''
        INSERT OR REPLACE INTO settings (key, value, updated_at)
        VALUES (?, ?, ?)
        ''', (key, value_json, now))
        
        conn.commit()
        conn.close()
        
        logger.debug(f"설정이 저장되었습니다. 키: {key}")
        return True
    
    except Exception as e:
        logger.error(f"설정 저장 중 오류 발생: {str(e)}")
        return False

def load_settings(db_manager) -> Dict:
    """
    모든 설정 로드
    
    Args:
        db_manager: DBManager 인스턴스
        
    Returns:
        설정 딕셔너리
    """
    try:
        conn = sqlite3.connect(db_manager.db_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT key, value FROM settings
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        settings = {}
        for row in rows:
            key = row['key']
            try:
                value = json.loads(row['value'])
                settings[key] = value
            except:
                settings[key] = row['value']
        
        return settings
    
    except Exception as e:
        logger.error(f"설정 로드 중 오류 발생: {str(e)}")
        return {}

def get_setting(db_manager, key: str, default=None) -> Any:
    """
    특정 설정 로드
    
    Args:
        db_manager: DBManager 인스턴스
        key: 설정 키
        default: 기본값
        
    Returns:
        설정 값 또는 기본값
    """
    try:
        conn = sqlite3.connect(db_manager.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT value FROM settings
        WHERE key = ?
        ''', (key,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            try:
                return json.loads(result[0])
            except:
                return result[0]
        else:
            return default
    
    except Exception as e:
        logger.error(f"설정 조회 중 오류 발생: {str(e)}")
        return default

def delete_setting(db_manager, key: str) -> bool:
    """
    설정 삭제
    
    Args:
        db_manager: DBManager 인스턴스
        key: 삭제할 설정 키
        
    Returns:
        삭제 성공 여부
    """
    try:
        conn = sqlite3.connect(db_manager.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
        DELETE FROM settings
        WHERE key = ?
        ''', (key,))
        
        conn.commit()
        conn.close()
        
        logger.debug(f"설정이 삭제되었습니다. 키: {key}")
        return True
    
    except Exception as e:
        logger.error(f"설정 삭제 중 오류 발생: {str(e)}")
        return False

def save_bot_state(db_manager, state: Dict) -> bool:
    """
    봇 상태 저장
    
    Args:
        db_manager: DBManager 인스턴스
        state: 상태 딕셔너리
        
    Returns:
        저장 성공 여부
    """
    return save_setting(db_manager, 'bot_state', state)

def load_bot_state(db_manager) -> Dict:
    """
    봇 상태 로드
    
    Args:
        db_manager: DBManager 인스턴스
        
    Returns:
        상태 딕셔너리
    """
    return get_setting(db_manager, 'bot_state', {})

def get_recent_filled_trades(db_manager, count: int = 10) -> List[Dict]:
    """
    최근 체결된 거래 조회
    
    Args:
        db_manager: DBManager 인스턴스
        count: 조회할 거래 수
        
    Returns:
        체결된 거래 목록
    """
    try:
        conn = sqlite3.connect(db_manager.db_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT * FROM trades
        WHERE filled_quantity > 0
        ORDER BY id DESC
        LIMIT ?
        ''', (count,))
        
        rows = cursor.fetchall()
        trades = []
        
        for row in rows:
            trade = dict(row)
            if 'data' in trade and trade['data']:
                try:
                    additional_data = json.loads(trade['data'])
                    for key, value in additional_data.items():
                        if key not in trade:
                            trade[key] = value
                except:
                    pass
            
            trades.append(trade)
        
        conn.close()
        return trades
    
    except Exception as e:
        logger.error(f"체결 거래 조회 중 오류 발생: {str(e)}")
        return []

def get_trade_stats(db_manager) -> Dict:
    """
    거래 통계 조회
    
    Args:
        db_manager: DBManager 인스턴스
        
    Returns:
        통계 정보 딕셔너리
    """
    try:
        conn = sqlite3.connect(db_manager.db_file)
        cursor = conn.cursor()
        
        # 총 거래 수
        cursor.execute('SELECT COUNT(*) FROM trades')
        total_count = cursor.fetchone()[0] or 0
        
        # 체결된 거래 수
        cursor.execute('SELECT COUNT(*) FROM trades WHERE filled_quantity > 0')
        filled_count = cursor.fetchone()[0] or 0
        
        # 총 거래량
        cursor.execute('SELECT SUM(filled_quantity) FROM trades')
        total_volume = cursor.fetchone()[0] or 0
        
        # 평균 체결률
        cursor.execute('SELECT AVG(filled_percent) FROM trades')
        avg_fill_percent = cursor.fetchone()[0] or 0
        
        # 최근 거래 시간
        cursor.execute('SELECT timestamp FROM trades ORDER BY id DESC LIMIT 1')
        result = cursor.fetchone()
        last_trade_time = result[0] if result else None
        
        conn.close()
        
        return {
            'total_count': total_count,
            'filled_count': filled_count,
            'total_volume': float(total_volume),
            'avg_fill_percent': float(avg_fill_percent),
            'last_trade_time': last_trade_time
        }
    
    except Exception as e:
        logger.error(f"거래 통계 조회 중 오류 발생: {str(e)}")
        return {
            'total_count': 0,
            'filled_count': 0,
            'total_volume': 0.0,
            'avg_fill_percent': 0.0,
            'last_trade_time': None
        }

def clear_old_trades(db_manager, days: int = 30) -> bool:
    """
    오래된 거래 내역 삭제
    
    Args:
        db_manager: DBManager 인스턴스
        days: 보관할 일수
        
    Returns:
        삭제 성공 여부
    """
    try:
        conn = sqlite3.connect(db_manager.db_file)
        cursor = conn.cursor()
        
        # 특정 일수보다 오래된 거래 삭제
        cursor.execute('''
        DELETE FROM trades
        WHERE datetime(timestamp) < datetime('now', '-? days')
        ''', (days,))
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        logger.info(f"{deleted_count}개의 오래된 거래 내역이 삭제되었습니다.")
        return True
    
    except Exception as e:
        logger.error(f"오래된 거래 내역 삭제 중 오류 발생: {str(e)}")
        return False