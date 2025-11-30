# 빠른 설정 가이드 (라즈베리파이)

## 🚀 빠른 시작 (각 Pi에서 실행)

### 공통 작업 (모든 Pi)

```bash
# 1. 시스템 업데이트
sudo apt update && sudo apt upgrade -y

# 2. 프로젝트 복사 (Git 또는 USB)
cd ~
# Git: git clone <repo-url> bid_data-
# 또는 USB/SCP로 복사

# 3. 의존성 설치
cd ~/bid_data-
pip3 install --user -r requirements.txt

# 4. 디렉토리 생성
mkdir -p data/raw data/processed data/export pi1/logs pi2/logs pi3/logs
```

---

## Pi1 설정 (목록 크롤러)

```bash
cd ~/bid_data-

# 1. 설정 파일 생성
cp config/config.pi1.yaml config/config.yaml
nano config/config.yaml  # IP 주소 수정

# 2. Kafka 설치 (Pi1이 Kafka 서버인 경우)
# docs/KAFKA_INSTALL_GUIDE.md 참조

# 3. 설정 검증
python3 scripts/validate_config.py --pi pi1

# 4. 실행
python3 pi1/scripts/run_spider.py
```

**설정 파일에서 수정할 것:**
- `pi.ip`: Pi1의 실제 IP 주소
- `kafka.bootstrap_servers`: Kafka 서버 IP (Pi1이면 자신의 IP)

---

## Pi2 설정 (상세 파서)

```bash
cd ~/bid_data-

# 1. 설정 파일 생성
cp config/config.pi2.yaml config/config.yaml
nano config/config.yaml  # IP 주소 수정

# 2. 설정 검증
python3 scripts/validate_config.py --pi pi2

# 3. 실행
python3 pi2/scripts/run_consumer.py
```

**설정 파일에서 수정할 것:**
- `pi.ip`: Pi2의 실제 IP 주소
- `kafka.bootstrap_servers`: Kafka 서버 IP (Pi1의 IP)

---

## Pi3 설정 (DB 저장)

```bash
cd ~/bid_data-

# 1. MariaDB 설치
sudo apt install -y mariadb-server mariadb-client
sudo mysql_secure_installation

# 2. 데이터베이스 생성
sudo mysql -u root -p
# CREATE DATABASE recall_db;
# CREATE USER 'recall_user'@'localhost' IDENTIFIED BY 'password';
# GRANT ALL PRIVILEGES ON recall_db.* TO 'recall_user'@'localhost';
# FLUSH PRIVILEGES;
# EXIT;

# 3. 테이블 생성
mysql -u recall_user -p recall_db < pi3/db/schema.sql

# 4. 설정 파일 생성
cp config/config.pi3.yaml config/config.yaml
nano config/config.yaml  # IP 주소 및 DB 비밀번호 수정

# 5. 설정 검증
python3 scripts/validate_config.py --pi pi3

# 6. 실행
python3 pi3/scripts/run_db_consumer.py
```

**설정 파일에서 수정할 것:**
- `pi.ip`: Pi3의 실제 IP 주소
- `kafka.bootstrap_servers`: Kafka 서버 IP (Pi1의 IP)
- `database.password`: 실제 DB 비밀번호

---

## 실행 순서

1. **Pi1 시작** (목록 크롤러)
2. **Pi2 시작** (상세 파서)
3. **Pi3 시작** (DB 저장)

---

## 문제 해결

### IP 주소 확인
```bash
hostname -I
```

### Kafka 연결 테스트
```bash
python3 scripts/integration_test.py --skip-db --skip-pipeline
```

### DB 연결 테스트
```bash
python3 scripts/integration_test.py --skip-kafka --skip-pipeline
```

---

**자세한 내용**: `docs/RASPBERRY_PI_SETUP.md` 참조

