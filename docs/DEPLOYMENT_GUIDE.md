# 배포 가이드

## 단계별 배포 절차

### 1단계: Kafka 서버 설치 및 설정

**Pi1 (또는 전용 Kafka 서버)에서 실행:**

```bash
# Kafka 설치 가이드 참조
# docs/KAFKA_INSTALL_GUIDE.md

# 1. Java 설치
sudo apt update
sudo apt install -y openjdk-11-jdk

# 2. Kafka 다운로드 및 설치
cd ~
mkdir kafka && cd kafka
wget https://downloads.apache.org/kafka/3.5.0/kafka_2.13-3.5.0.tgz
tar -xzf kafka_2.13-3.5.0.tgz
cd kafka_2.13-3.5.0

# 3. 설정 파일 수정
nano config/server.properties
# listeners=PLAINTEXT://0.0.0.0:9092
# advertised.listeners=PLAINTEXT://YOUR_PI_IP:9092

# 4. Zookeeper 및 Kafka 시작
bin/zookeeper-server-start.sh config/zookeeper.properties &
bin/kafka-server-start.sh config/server.properties &

# 5. 토픽 생성
cd /path/to/bid_data-
python3 scripts/setup_kafka_topics.py
```

### 2단계: MariaDB/MySQL 설치 및 설정

**Pi3에서 실행:**

```bash
# MariaDB 설치 가이드 참조
# docs/MARIADB_INSTALL_GUIDE.md

# 1. MariaDB 설치
sudo apt update
sudo apt install -y mariadb-server mariadb-client

# 2. 보안 설정
sudo mysql_secure_installation

# 3. 데이터베이스 및 사용자 생성
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
# 4. 테이블 생성
cd /path/to/bid_data-
mysql -u recall_user -p recall_db < pi3/db/schema.sql

# 또는 Python으로
python3 -c "
from pi3.db.connection import get_engine
from pi3.db.models import Base
Base.metadata.create_all(get_engine())
print('테이블 생성 완료')
"
```

### 3단계: 각 Pi에서 설정 파일 수정

#### Pi1 설정

```bash
cd /path/to/bid_data-
cp config/config.pi1.yaml config/config.yaml
nano config/config.yaml
```

**수정 사항:**
- `kafka.bootstrap_servers`: Kafka 서버 IP 주소
- `pi.ip`: Pi1의 IP 주소

#### Pi2 설정

```bash
cd /path/to/bid_data-
cp config/config.pi2.yaml config/config.yaml
nano config/config.yaml
```

**수정 사항:**
- `kafka.bootstrap_servers`: Kafka 서버 IP 주소
- `pi.ip`: Pi2의 IP 주소

#### Pi3 설정

```bash
cd /path/to/bid_data-
cp config/config.pi3.yaml config/config.yaml
nano config/config.yaml
```

**수정 사항:**
- `kafka.bootstrap_servers`: Kafka 서버 IP 주소
- `database.host`: DB 서버 IP (로컬이면 localhost)
- `database.password`: 실제 비밀번호
- `hadoop.hdfs_namenode`: HDFS NameNode 주소 (선택적)
- `pi.ip`: Pi3의 IP 주소

### 4단계: 설정 파일 검증

각 Pi에서:

```bash
# Pi1
python3 scripts/validate_config.py --pi pi1

# Pi2
python3 scripts/validate_config.py --pi pi2

# Pi3
python3 scripts/validate_config.py --pi pi3
```

### 5단계: 통합 테스트

각 Pi에서:

```bash
# Kafka 연결 테스트
python3 scripts/integration_test.py --skip-db --skip-pipeline

# DB 연결 테스트 (Pi3만)
python3 scripts/integration_test.py --skip-kafka --skip-pipeline

# 전체 파이프라인 테스트
python3 scripts/integration_test.py
```

### 6단계: 실제 실행

#### Pi1: 목록 크롤러 시작

```bash
cd /path/to/bid_data-
python3 pi1/scripts/run_spider.py
```

#### Pi2: 상세 파서 시작

```bash
cd /path/to/bid_data-
python3 pi2/scripts/run_consumer.py
```

#### Pi3: DB 저장 및 HDFS 적재 시작

```bash
cd /path/to/bid_data-
python3 pi3/scripts/run_db_consumer.py
```

## 자동 실행 설정 (선택적)

### systemd 서비스 등록

각 Pi에서:

```bash
# Pi1 서비스 파일 생성
sudo nano /etc/systemd/system/recall-pi1.service
```

```ini
[Unit]
Description=Recall Pi1 List Crawler
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/bid_data-
ExecStart=/usr/bin/python3 /home/pi/bid_data-/pi1/scripts/run_spider.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable recall-pi1
sudo systemctl start recall-pi1
```

Pi2, Pi3도 동일하게 설정합니다.

## 모니터링

### 로그 확인

```bash
# Pi1 로그
tail -f pi1/logs/spider.log

# Pi2 로그
tail -f pi2/logs/consumer.log

# Pi3 로그
tail -f pi3/logs/db_consumer.log
```

### Kafka 토픽 모니터링

```bash
# 메시지 수 확인
bin/kafka-run-class.sh kafka.tools.GetOffsetShell \
  --broker-list localhost:9092 \
  --topic recall-new-urls

# Consumer 그룹 상태 확인
bin/kafka-consumer-groups.sh --bootstrap-server localhost:9092 --list
```

### DB 상태 확인

```bash
# 레코드 수 확인
mysql -u recall_user -p recall_db -e "SELECT COUNT(*) FROM recall;"

# 최근 데이터 확인
mysql -u recall_user -p recall_db -e "SELECT * FROM recall ORDER BY created_at DESC LIMIT 10;"
```

## 문제 해결

### Kafka 연결 실패
- Kafka 서버가 실행 중인지 확인
- 방화벽 설정 확인
- IP 주소가 올바른지 확인

### DB 연결 실패
- MariaDB가 실행 중인지 확인
- 사용자 권한 확인
- 방화벽 설정 확인

### 데이터가 수집되지 않음
- 각 Pi의 로그 확인
- Kafka 토픽에 메시지가 있는지 확인
- 웹사이트 접근 가능한지 확인

## 참고 문서

- [Kafka 설치 가이드](KAFKA_INSTALL_GUIDE.md)
- [MariaDB 설치 가이드](MARIADB_INSTALL_GUIDE.md)
- [빠른 시작 가이드](QUICK_START.md)
- [테스트 요약](TEST_SUMMARY.md)

