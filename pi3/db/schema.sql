-- 리콜 데이터베이스 스키마
-- MariaDB/MySQL용

-- 데이터베이스 생성
CREATE DATABASE IF NOT EXISTS recall_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE recall_db;

-- 리콜 테이블 생성
CREATE TABLE IF NOT EXISTS recall (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    url VARCHAR(500) NOT NULL UNIQUE COMMENT '상세링크 (PK 후보)',
    title VARCHAR(500) NOT NULL COMMENT '제목',
    maker VARCHAR(100) NOT NULL COMMENT '제조사',
    model VARCHAR(200) NOT NULL COMMENT '모델/연식',
    model_year INT COMMENT '연식 (파싱된 숫자)',
    defect_part VARCHAR(200) NOT NULL COMMENT '결함부위',
    defect_part_std VARCHAR(100) COMMENT '표준부위 (매핑된 값)',
    symptom TEXT NOT NULL COMMENT '증상',
    action TEXT NOT NULL COMMENT '시정조치',
    start_date DATE COMMENT '시정개시 (YYYY-MM-DD)',
    qty INT COMMENT '대상대수',
    notice_date DATE COMMENT '공지일 (YYYY-MM-DD)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '레코드 생성 시간',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '레코드 수정 시간',
    INDEX idx_url (url),
    INDEX idx_maker (maker),
    INDEX idx_model (model),
    INDEX idx_notice_date (notice_date),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='자동차 리콜 공지 데이터';

-- 사용자 생성 및 권한 부여
CREATE USER IF NOT EXISTS 'recall_user'@'localhost' IDENTIFIED BY 'your_password_here';
GRANT SELECT, INSERT, UPDATE ON recall_db.* TO 'recall_user'@'localhost';
FLUSH PRIVILEGES;

-- 중복 체크를 위한 뷰 (선택사항)
CREATE OR REPLACE VIEW recall_summary AS
SELECT 
    maker,
    COUNT(*) as total_count,
    COUNT(DISTINCT model) as model_count,
    MIN(notice_date) as earliest_notice,
    MAX(notice_date) as latest_notice
FROM recall
GROUP BY maker;

