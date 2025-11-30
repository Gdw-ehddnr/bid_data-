# MariaDB/MySQL 설치 및 설정 가이드

## 라즈베리파이에 MariaDB 설치하기

### 1. MariaDB 설치

```bash
# 패키지 업데이트
sudo apt update

# MariaDB 서버 설치
sudo apt install -y mariadb-server

# MariaDB 클라이언트 설치
sudo apt install -y mariadb-client
```

### 2. 초기 보안 설정

```bash
# 보안 스크립트 실행
sudo mysql_secure_installation
```

설정 항목:
- Root 비밀번호 설정
- 익명 사용자 제거: Y
- 원격 root 로그인 비활성화: Y
- Test 데이터베이스 제거: Y
- 권한 테이블 다시 로드: Y

### 3. 데이터베이스 및 사용자 생성

```bash
# MariaDB 접속
sudo mysql -u root -p
```

```sql
-- 데이터베이스 생성
CREATE DATABASE recall_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 사용자 생성 및 권한 부여
CREATE USER 'recall_user'@'localhost' IDENTIFIED BY 'your_password_here';
GRANT ALL PRIVILEGES ON recall_db.* TO 'recall_user'@'localhost';
FLUSH PRIVILEGES;

-- 확인
SHOW DATABASES;
SELECT user, host FROM mysql.user WHERE user = 'recall_user';

-- 종료
EXIT;
```

### 4. 테이블 생성

```bash
# 프로젝트 디렉토리로 이동
cd /path/to/bid_data-

# 스키마 파일 실행
mysql -u recall_user -p recall_db < pi3/db/schema.sql
```

또는 Python으로:

```bash
python3 -c "
from pi3.db.connection import get_engine
from pi3.db.models import Base

engine = get_engine()
Base.metadata.create_all(engine)
print('테이블 생성 완료')
"
```

### 5. 원격 접속 설정 (선택적)

다른 Pi에서 접속하려면:

```bash
# MariaDB 설정 파일 수정
sudo nano /etc/mysql/mariadb.conf.d/50-server.cnf
```

```ini
# bind-address를 0.0.0.0으로 변경
bind-address = 0.0.0.0
```

```bash
# 원격 접속 사용자 생성
sudo mysql -u root -p
```

```sql
-- 원격 접속 허용 (특정 IP)
CREATE USER 'recall_user'@'192.168.1.%' IDENTIFIED BY 'your_password_here';
GRANT ALL PRIVILEGES ON recall_db.* TO 'recall_user'@'192.168.1.%';
FLUSH PRIVILEGES;
EXIT;
```

```bash
# MariaDB 재시작
sudo systemctl restart mariadb
```

### 6. 방화벽 설정

```bash
# 포트 3306 (MySQL/MariaDB) 열기
sudo ufw allow 3306/tcp
```

### 7. systemd 서비스 관리

```bash
# MariaDB 상태 확인
sudo systemctl status mariadb

# MariaDB 시작
sudo systemctl start mariadb

# MariaDB 중지
sudo systemctl stop mariadb

# MariaDB 재시작
sudo systemctl restart mariadb

# 부팅 시 자동 시작
sudo systemctl enable mariadb
```

## MySQL 사용 시

MySQL을 사용하는 경우:

```bash
# MySQL 설치
sudo apt install -y mysql-server mysql-client

# 나머지 설정은 MariaDB와 동일
```

## 연결 테스트

### 명령줄에서 테스트

```bash
# 로컬 접속
mysql -u recall_user -p recall_db

# 원격 접속
mysql -h 192.168.1.12 -u recall_user -p recall_db
```

### Python에서 테스트

```bash
cd /path/to/bid_data-
python3 -c "
from pi3.db.connection import get_session
from pi3.db.models import Recall

session = get_session()
count = session.query(Recall).count()
print(f'연결 성공! 현재 레코드 수: {count}')
session.close()
"
```

## 백업 및 복원

### 백업

```bash
# 전체 데이터베이스 백업
mysqldump -u recall_user -p recall_db > backup_$(date +%Y%m%d).sql

# 특정 테이블만 백업
mysqldump -u recall_user -p recall_db recall > recall_backup_$(date +%Y%m%d).sql
```

### 복원

```bash
# 데이터베이스 복원
mysql -u recall_user -p recall_db < backup_20251130.sql
```

## 문제 해결

### 연결 거부 오류

```bash
# MariaDB 실행 상태 확인
sudo systemctl status mariadb

# 포트 확인
sudo netstat -tulpn | grep 3306
```

### 권한 오류

```sql
-- 권한 확인
SHOW GRANTS FOR 'recall_user'@'localhost';

-- 권한 다시 부여
GRANT ALL PRIVILEGES ON recall_db.* TO 'recall_user'@'localhost';
FLUSH PRIVILEGES;
```

### 문자 인코딩 문제

```sql
-- 데이터베이스 문자셋 확인
SHOW CREATE DATABASE recall_db;

-- 테이블 문자셋 확인
SHOW CREATE TABLE recall;
```

## 성능 최적화 (선택적)

```bash
# MariaDB 설정 파일 수정
sudo nano /etc/mysql/mariadb.conf.d/50-server.cnf
```

```ini
[mysqld]
# 메모리 설정 (라즈베리파이에 맞게 조정)
innodb_buffer_pool_size = 128M
max_connections = 50
```

```bash
# 재시작
sudo systemctl restart mariadb
```

## 참고

- MariaDB 공식 문서: https://mariadb.com/kb/en/
- 라즈베리파이의 제한된 메모리를 고려하여 설정 조정 필요

