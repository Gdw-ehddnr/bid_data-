# 라즈베리파이별 설정 가이드

## 📋 준비 사항

### 공통 준비
- [ ] 라즈베리파이 OS 설치 (Raspberry Pi OS)
- [ ] 네트워크 연결 확인 (각 Pi의 IP 주소 확인)
- [ ] SSH 접속 가능한지 확인
- [ ] 프로젝트 파일 준비 (Git 또는 USB로 전송)

---

## 🔧 공통 작업 (모든 Pi에서 실행)

### 1. 시스템 업데이트

```bash
sudo apt update
sudo apt upgrade -y
```

### 2. Python 환경 확인

```bash
# Python 버전 확인 (3.7 이상 필요)
python3 --version

# pip 설치 확인
python3 -m pip --version
```

### 3. 프로젝트 복사

**방법 1: Git 사용 (권장)**
```bash
cd ~
git clone <your-repo-url> bid_data-
cd bid_data-
```

**방법 2: USB 또는 SCP 사용**
```bash
# 호스트 컴퓨터에서
scp -r bid_data- pi@<pi-ip>:/home/pi/

# 라즈베리파이에서
cd ~/bid_data-
```

### 4. 의존성 패키지 설치

```bash
cd ~/bid_data-
pip3 install --user -r requirements.txt
```

### 5. 디렉토리 생성

```bash
cd ~/bid_data-
mkdir -p data/raw data/processed data/export
mkdir -p pi1/logs pi2/logs pi3/logs
```

---

## 🖥️ Pi1 설정 (목록 크롤러)

### 1. 설정 파일 생성

```bash
cd ~/bid_data-
cp config/config.pi1.yaml config/config.yaml
nano config/config.yaml
```

**수정 사항:**
```yaml
pi:
  id: "pi1"
  hostname: "raspberrypi1.local"  # 실제 호스트명
  ip: "192.168.1.10"  # Pi1의 실제 IP 주소

kafka:
  bootstrap_servers: "192.168.1.10:9092"  # Kafka 서버 IP (Pi1이 Kafka 서버인 경우)
```

### 2. Kafka 서버 설치 (Pi1이 Kafka 서버인 경우)

```bash
# Kafka 설치 가이드 참조
# docs/KAFKA_INSTALL_GUIDE.md

# Java 설치
sudo apt install -y openjdk-11-jdk

# Kafka 다운로드 및 설치
cd ~
mkdir kafka && cd kafka
wget https://downloads.apache.org/kafka/3.5.0/kafka_2.13-3.5.0.tgz
tar -xzf kafka_2.13-3.5.0.tgz
cd kafka_2.13-3.5.0

# 설정 파일 수정
nano config/server.properties
# listeners=PLAINTEXT://0.0.0.0:9092
# advertised.listeners=PLAINTEXT://192.168.1.10:9092  # Pi1의 IP

# Zookeeper 및 Kafka 시작
bin/zookeeper-server-start.sh config/zookeeper.properties &
bin/kafka-server-start.sh config/server.properties &

# 토픽 생성
cd ~/bid_data-
python3 scripts/setup_kafka_topics.py
```

### 3. 설정 파일 검증

```bash
cd ~/bid_data-
python3 scripts/validate_config.py --pi pi1
```

### 4. 테스트 실행

```bash
# 목록 크롤링 테스트
cd ~/bid_data-
python3 pi1/scripts/test_spider_simple.py
```

### 5. 실제 실행

```bash
# 목록 크롤러 시작
cd ~/bid_data-
python3 pi1/scripts/run_spider.py
```

---

## 🖥️ Pi2 설정 (상세 파서)

### 1. 설정 파일 생성

```bash
cd ~/bid_data-
cp config/config.pi2.yaml config/config.yaml
nano config/config.yaml
```

**수정 사항:**
```yaml
pi:
  id: "pi2"
  hostname: "raspberrypi2.local"
  ip: "192.168.1.11"  # Pi2의 실제 IP 주소

kafka:
  bootstrap_servers: "192.168.1.10:9092"  # Kafka 서버 IP (Pi1의 IP)
```

### 2. 설정 파일 검증

```bash
cd ~/bid_data-
python3 scripts/validate_config.py --pi pi2
```

### 3. Kafka 연결 테스트

```bash
cd ~/bid_data-
python3 scripts/integration_test.py --skip-db --skip-pipeline
```

### 4. 테스트 실행

```bash
# 상세 파싱 테스트
cd ~/bid_data-
python3 pi2/scripts/test_detail_crawler.py
```

### 5. 실제 실행

```bash
# 상세 파서 시작
cd ~/bid_data-
python3 pi2/scripts/run_consumer.py
```

---

## 🖥️ Pi3 설정 (DB 저장 + HDFS 적재)

### 1. MariaDB 설치 및 설정

```bash
# MariaDB 설치
sudo apt install -y mariadb-server mariadb-client

# 보안 설정
sudo mysql_secure_installation

# 데이터베이스 및 사용자 생성
sudo mysql -u root -p
```

```sql
CREATE DATABASE recall_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'recall_user'@'localhost' IDENTIFIED BY 'your_password_here';
GRANT ALL PRIVILEGES ON recall_db.* TO 'recall_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

```bash
# 테이블 생성
cd ~/bid_data-
mysql -u recall_user -p recall_db < pi3/db/schema.sql

# 또는 Python으로
python3 -c "
from pi3.db.connection import get_engine
from pi3.db.models import Base
Base.metadata.create_all(get_engine())
print('테이블 생성 완료')
"
```

### 2. 설정 파일 생성

```bash
cd ~/bid_data-
cp config/config.pi3.yaml config/config.yaml
nano config/config.yaml
```

**수정 사항:**
```yaml
pi:
  id: "pi3"
  hostname: "raspberrypi3.local"
  ip: "192.168.1.12"  # Pi3의 실제 IP 주소

kafka:
  bootstrap_servers: "192.168.1.10:9092"  # Kafka 서버 IP

database:
  host: "localhost"  # 로컬이면 localhost
  port: 3306
  user: "recall_user"
  password: "your_password_here"  # 실제 비밀번호로 변경
  database: "recall_db"

hadoop:
  hdfs_namenode: "hdfs://localhost:9000"  # HDFS가 있으면 설정
  hdfs_path: "/recall_data"
  hdfs_command: "hdfs"
  export_interval_hours: 24
```

### 3. 설정 파일 검증

```bash
cd ~/bid_data-
python3 scripts/validate_config.py --pi pi3
```

### 4. DB 연결 테스트

```bash
cd ~/bid_data-
python3 scripts/integration_test.py --skip-kafka --skip-pipeline
```

### 5. 테스트 실행

```bash
# DB 저장 테스트 (실제 데이터가 있을 때)
cd ~/bid_data-
python3 -c "
from pi3.db.connection import get_session
from pi3.db.models import Recall
session = get_session()
count = session.query(Recall).count()
print(f'DB 연결 성공! 현재 레코드 수: {count}')
session.close()
"
```

### 6. 실제 실행

```bash
# DB 저장 및 HDFS 적재 시작
cd ~/bid_data-
python3 pi3/scripts/run_db_consumer.py
```

---

## 🔍 전체 시스템 테스트

### 각 Pi에서 순서대로 실행

#### 1. Pi1에서 테스트
```bash
cd ~/bid_data-
python3 scripts/integration_test.py --skip-db --skip-pipeline
```

#### 2. Pi2에서 테스트
```bash
cd ~/bid_data-
python3 scripts/integration_test.py --skip-db --skip-pipeline
```

#### 3. Pi3에서 테스트
```bash
cd ~/bid_data-
python3 scripts/integration_test.py
```

---

## 🚀 실제 운영 시작

### 순서대로 실행

#### 1. Pi1 시작 (목록 크롤러)
```bash
cd ~/bid_data-
python3 pi1/scripts/run_spider.py
```

#### 2. Pi2 시작 (상세 파서)
```bash
cd ~/bid_data-
python3 pi2/scripts/run_consumer.py
```

#### 3. Pi3 시작 (DB 저장)
```bash
cd ~/bid_data-
python3 pi3/scripts/run_db_consumer.py
```

---

## 📊 모니터링

### 로그 확인

```bash
# Pi1 로그
tail -f ~/bid_data-/pi1/logs/spider.log

# Pi2 로그
tail -f ~/bid_data-/pi2/logs/consumer.log

# Pi3 로그
tail -f ~/bid_data-/pi3/logs/db_consumer.log
```

### Kafka 토픽 확인 (Pi1에서)

```bash
cd ~/kafka/kafka_2.13-3.5.0
bin/kafka-topics.sh --list --bootstrap-server localhost:9092
```

### DB 상태 확인 (Pi3에서)

```bash
mysql -u recall_user -p recall_db -e "SELECT COUNT(*) FROM recall;"
```

---

## ⚠️ 문제 해결

### 네트워크 연결 문제
```bash
# 각 Pi의 IP 확인
hostname -I

# 다른 Pi와 통신 테스트
ping <other-pi-ip>
```

### Kafka 연결 실패
- Kafka 서버가 실행 중인지 확인
- 방화벽 설정 확인
- IP 주소가 올바른지 확인

### DB 연결 실패
- MariaDB가 실행 중인지 확인: `sudo systemctl status mariadb`
- 사용자 권한 확인
- 비밀번호 확인

---

## 📝 체크리스트

### Pi1 체크리스트
- [ ] 시스템 업데이트
- [ ] Python 환경 확인
- [ ] 프로젝트 복사
- [ ] 의존성 설치
- [ ] 설정 파일 생성 및 수정
- [ ] Kafka 서버 설치 (Pi1이 Kafka 서버인 경우)
- [ ] Kafka 토픽 생성
- [ ] 설정 파일 검증
- [ ] 테스트 실행
- [ ] 실제 실행

### Pi2 체크리스트
- [ ] 시스템 업데이트
- [ ] Python 환경 확인
- [ ] 프로젝트 복사
- [ ] 의존성 설치
- [ ] 설정 파일 생성 및 수정
- [ ] 설정 파일 검증
- [ ] Kafka 연결 테스트
- [ ] 테스트 실행
- [ ] 실제 실행

### Pi3 체크리스트
- [ ] 시스템 업데이트
- [ ] Python 환경 확인
- [ ] 프로젝트 복사
- [ ] 의존성 설치
- [ ] MariaDB 설치
- [ ] 데이터베이스 및 사용자 생성
- [ ] 테이블 생성
- [ ] 설정 파일 생성 및 수정
- [ ] 설정 파일 검증
- [ ] DB 연결 테스트
- [ ] 테스트 실행
- [ ] 실제 실행

---

**참고**: 각 단계를 순서대로 진행하세요. 문제가 발생하면 해당 단계의 로그를 확인하세요.

