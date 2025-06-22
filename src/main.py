import os
import json
import time
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from apscheduler.schedulers.background import BackgroundScheduler
from src.crawler import DongseoNoticeCrawler
from src.notification_service import init_notification_system, check_and_notify_new_notices

# Flask 앱 초기화
app = Flask(__name__)

# 크롤러 초기화
crawler = DongseoNoticeCrawler()

# 마지막 업데이트 시간
last_updated = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# 스케줄러 초기화
scheduler = BackgroundScheduler()

@app.route('/')
def index():
    """메인 페이지를 렌더링합니다."""
    return render_template('index.html', last_updated=last_updated)

@app.route('/api/notices')
def get_notices():
    """공지사항 목록을 JSON 형태로 반환합니다."""
    # 저장된 공지사항 로드
    notices = crawler.load_notices()
    
    # 공지사항이 없으면 크롤링
    if not notices:
        notices = crawler.crawl_notices()
        global last_updated
        last_updated = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 검색어 필터링
    search_query = request.args.get('search', '').lower()
    if search_query:
        notices = [notice for notice in notices if search_query in notice['title'].lower() or search_query in notice['author'].lower()]
    
    # 필터 적용
    filter_type = request.args.get('filter', 'all')
    if filter_type == 'notice':
        notices = [notice for notice in notices if notice['is_notice']]
    elif filter_type == 'new':
        notices = [notice for notice in notices if notice['is_new']]
    elif filter_type == 'attachment':
        notices = [notice for notice in notices if notice['has_attachment']]
    
    # 페이지네이션
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    
    paginated_notices = notices[start_idx:end_idx]
    
    return jsonify({
        'notices': paginated_notices,
        'total': len(notices),
        'page': page,
        'per_page': per_page,
        'last_updated': last_updated
    })

@app.route('/api/notices/refresh')
def refresh_notices():
    """공지사항을 새로 크롤링합니다."""
    notices = crawler.crawl_notices()
    
    global last_updated
    last_updated = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    return jsonify({
        'success': True,
        'count': len(notices),
        'last_updated': last_updated
    })

@app.route('/api/notice/<notice_id>')
def get_notice_detail(notice_id):
    """공지사항 상세 정보를 반환합니다."""
    notices = crawler.load_notices()
    
    # 해당 ID의 공지사항 찾기
    notice = next((n for n in notices if n['num'] == notice_id), None)
    
    if not notice:
        return jsonify({'error': '공지사항을 찾을 수 없습니다.'}), 404
    
    # 상세 내용 크롤링
    detail = crawler.crawl_notice_detail(notice['link'])
    
    # 공지사항 정보와 상세 내용 병합
    notice_with_detail = {**notice, **detail}
    
    return jsonify(notice_with_detail)

def scheduled_crawling():
    """정기적으로 공지사항을 크롤링하고 알림을 발송합니다."""
    print(f"[{datetime.now()}] 정기 크롤링 및 알림 발송 시작...")
    
    try:
        # 새 공지사항 확인 및 알림 발송
        new_count, sent_count = check_and_notify_new_notices(crawler)
        
        print(f"[{datetime.now()}] 정기 크롤링 완료: 새 공지사항 {new_count}건, 알림 발송 {sent_count}건")
        
        # 마지막 업데이트 시간 갱신
        global last_updated
        last_updated = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
    except Exception as e:
        print(f"[{datetime.now()}] 정기 크롤링 중 오류 발생: {e}")

def start_scheduler():
    """스케줄러를 시작합니다."""
    if not scheduler.running:
        # 30분마다 크롤링 및 알림 발송
        scheduler.add_job(scheduled_crawling, 'interval', minutes=30, id='crawling_job')
        scheduler.start()
        print("스케줄러가 시작되었습니다.")

@app.before_first_request
def before_first_request():
    """첫 요청 전에 실행되는 함수입니다."""
    # 알림 시스템 초기화
    init_notification_system(app)
    
    # 스케줄러 시작
    start_scheduler()
    
    # 초기 크롤링
    crawler.crawl_notices()

if __name__ == '__main__':
    # 개발 환경에서 실행 시
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
