-- 구독 테이블 생성
CREATE TABLE IF NOT EXISTS subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    endpoint TEXT NOT NULL,
    p256dh TEXT NOT NULL,
    auth TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 알림 히스토리 테이블 생성
CREATE TABLE IF NOT EXISTS notification_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    notice_id INTEGER NOT NULL,
    notice_title TEXT NOT NULL,
    sent_at TIMESTAMP NOT NULL,
    recipients INTEGER DEFAULT 0
);

-- 시스템 설정 테이블 생성
CREATE TABLE IF NOT EXISTS system_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- 초기 설정 삽입
INSERT OR IGNORE INTO system_settings (key, value) VALUES ('last_checked_notice_id', '0');
