import requests
import json
import os
import logging
from datetime import datetime

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('onesignal_service')

# OneSignal 설정
ONESIGNAL_APP_ID = os.environ.get('ONESIGNAL_APP_ID', 'YOUR_ONESIGNAL_APP_ID')
ONESIGNAL_REST_API_KEY = os.environ.get('ONESIGNAL_REST_API_KEY', 'YOUR_ONESIGNAL_REST_API_KEY')
ONESIGNAL_API_URL = "https://onesignal.com/api/v1/notifications"

# 데이터베이스 연결 및 초기화
def get_db_connection():
    """SQLite 데이터베이스 연결을 반환합니다."""
    import sqlite3
    conn = sqlite3.connect('notification.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """데이터베이스 스키마를 초기화합니다."""
    conn = get_db_connection()
    with open('schema.sql') as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()
    logger.info("데이터베이스가 초기화되었습니다.")

def init_notification_system(app):
    """알림 시스템을 초기화합니다."""
    with app.app_context():
        # 데이터베이스 디렉토리 확인
        os.makedirs(os.path.dirname('notification.db'), exist_ok=True)
        
        # 데이터베이스 초기화
        if not os.path.exists('notification.db'):
            init_db()
            logger.info("알림 시스템이 초기화되었습니다.")
        
        # OneSignal 설정 확인
        if ONESIGNAL_APP_ID == 'YOUR_ONESIGNAL_APP_ID' or ONESIGNAL_REST_API_KEY == 'YOUR_ONESIGNAL_REST_API_KEY':
            logger.warning("OneSignal 설정이 완료되지 않았습니다. 환경 변수를 확인하세요.")

def send_push_notification(notice):
    """OneSignal을 통해 푸시 알림을 발송합니다."""
    try:
        # 알림 내용 구성
        notification_content = {
            'app_id': ONESIGNAL_APP_ID,
            'included_segments': ['All'],
            'headings': {'en': '동서대학교 공지사항', 'ko': '동서대학교 공지사항'},
            'contents': {'en': notice['title'], 'ko': notice['title']},
            'url': notice['link'],
            'web_buttons': [
                {
                    'id': 'view',
                    'text': {'en': '공지사항 보기', 'ko': '공지사항 보기'},
                    'url': notice['link']
                }
            ],
            'chrome_web_icon': 'https://www.dongseo.ac.kr/kr/images/common/logo.png',
            'firefox_icon': 'https://www.dongseo.ac.kr/kr/images/common/logo.png'
        }
        
        # OneSignal API 호출
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Basic {ONESIGNAL_REST_API_KEY}'
        }
        
        response = requests.post(
            ONESIGNAL_API_URL,
            headers=headers,
            data=json.dumps(notification_content)
        )
        
        # 응답 확인
        if response.status_code == 200:
            response_data = response.json()
            recipients = response_data.get('recipients', 0)
            logger.info(f"알림 발송 성공: {notice['title']} (수신자: {recipients}명)")
            
            # 알림 히스토리 저장
            conn = get_db_connection()
            conn.execute(
                'INSERT INTO notification_history (notice_id, notice_title, sent_at, recipients) VALUES (?, ?, ?, ?)',
                (int(notice['num']), notice['title'], datetime.now().isoformat(), recipients)
            )
            conn.commit()
            conn.close()
            
            return recipients, 0  # 성공, 실패 카운트
        else:
            logger.error(f"알림 발송 실패: {response.status_code} - {response.text}")
            return 0, 1  # 성공, 실패 카운트
            
    except Exception as e:
        logger.error(f"알림 발송 중 오류 발생: {e}")
        return 0, 1  # 성공, 실패 카운트

def check_and_notify_new_notices(crawler):
    """새로운 공지사항을 확인하고 알림을 발송합니다."""
    try:
        # 마지막으로 확인한 공지사항 ID 가져오기
        conn = get_db_connection()
        last_checked = conn.execute(
            'SELECT value FROM system_settings WHERE key = "last_checked_notice_id"'
        ).fetchone()
        
        last_checked_id = int(last_checked[0]) if last_checked else 0
        logger.info(f"마지막으로 확인한 공지사항 ID: {last_checked_id}")
        
        # 최신 공지사항 크롤링
        notices = crawler.crawl_notices(max_pages=3)
        
        if not notices:
            logger.warning("크롤링된 공지사항이 없습니다.")
            return 0, 0
        
        # 새로운 공지사항 필터링
        new_notices = [notice for notice in notices if int(notice['num']) > last_checked_id]
        new_notices.sort(key=lambda x: int(x['num']))
        
        if not new_notices:
            logger.info("새로운 공지사항이 없습니다.")
            return 0, 0
        
        logger.info(f"새로운 공지사항 {len(new_notices)}건 발견")
        
        # 새로운 공지사항에 대해 알림 발송
        total_success = 0
        total_fail = 0
        
        for notice in new_notices:
            success, fail = send_push_notification(notice)
            total_success += success
            total_fail += fail
        
        # 마지막으로 확인한 공지사항 ID 업데이트
        if new_notices:
            max_id = max([int(notice['num']) for notice in new_notices])
            conn.execute(
                'INSERT OR REPLACE INTO system_settings (key, value) VALUES (?, ?)',
                ('last_checked_notice_id', str(max_id))
            )
            conn.commit()
            logger.info(f"마지막 확인 ID를 {max_id}로 업데이트했습니다.")
        
        conn.close()
        return len(new_notices), total_success
        
    except Exception as e:
        logger.error(f"공지사항 확인 및 알림 발송 중 오류 발생: {e}")
        return 0, 0
