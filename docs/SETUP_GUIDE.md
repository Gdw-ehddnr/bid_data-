# 프로젝트 설정 가이드

## 전체 설정 순서

### 1. 사전 준비

각 라즈베리파이에 다음이 설치되어 있어야 합니다:
- Python 3.8 이상
- pip
- Git

### 2. 프로젝트 클론 및 설정

```bash
# 각 Pi에서 프로젝트 클론
git clone <repository_url>
cd bid_data-

# Python 가상환경 생성 (권장)
python3 -m venv venv
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt
```

### 3. Kafka 설치 및 설정

**Kafka 서버가 될 Pi에서:**

```bash
# Kafka 설치 가이드 참고
# docs/KAFKA_SETUP.md 파일 참조

# 토픽 생성
bin/kafka-topics.sh --create \
  --bootstrap-server localhost:9092 \
  --replication-factor 1 \
  --partitions 3 \
  --topic recall-new-urls

bin/kafka-topics.sh --create \
  --bootstrap-server localhost:9092 \
  --replication-factor 1 \
  --partitions 3 \
  --topic recall-parsed

bin/kafka-topics.sh --create \
  --bootstrap-server localhost:9092 \
  --replication-factor 1 \
  --partitions 3 \
  --topic recall-db-records
```

### 4. 데이터베이스 설정 (Pi3)

```bash
# MariaDB/MySQL 설치
sudo apt install mariadb-server

# 데이터베이스 및 사용자 생성
mysql -u root -p < pi3/db/schema.sql

# 설정 파일에서 비밀번호 수정
# config/config.yaml
```

### 5. 설정 파일 구성

각 Pi에서 `config/config.example.yaml`을 복사하여 수정:

```bash
cp config/config.example.yaml config/config.yaml
nano config/config.yaml
```

주요 설정 항목:
- `kafka.bootstrap_servers`: Kafka 브로커 주소
- `database.*`: DB 연결 정보 (Pi3만)
- `hadoop.*`: HDFS 설정 (Pi4만)

### 6. 실행

#### Pi1: 목록 크롤러

```bash
cd pi1
python scripts/run_spider.py
```

#### Pi2: 상세 크롤러

```bash
cd pi2
python scripts/run_consumer.py
```

#### Pi3: DB 저장

```bash
cd pi3
python scripts/run_db_consumer.py
```

#### Pi4: HDFS 적재

```bash
cd pi4
# Kafka에서 수신
python scripts/load_to_hdfs.py --source kafka

# 또는 DB에서 직접 조회
python scripts/load_to_hdfs.py --source db
```

## 데이터 흐름 확인

### Kafka 토픽 모니터링

```bash
# Consumer 그룹 확인
bin/kafka-consumer-groups.sh --bootstrap-server localhost:9092 --list

# 특정 토픽의 메시지 확인
bin/kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic recall-new-urls \
  --from-beginning
```

### DB 확인

```bash
mysql -u recall_user -p recall_db
SELECT COUNT(*) FROM recall;
SELECT * FROM recall LIMIT 10;
```

## 문제 해결

### Kafka 연결 오류

- Kafka 브로커가 실행 중인지 확인
- 방화벽 포트(9092) 개방 확인
- `config/config.yaml`의 `bootstrap_servers` 주소 확인

### DB 연결 오류

- MariaDB/MySQL 서비스 실행 확인
- 사용자 권한 확인
- `config/config.yaml`의 DB 설정 확인

### 크롤링 오류

- 실제 웹사이트 구조에 맞게 선택자 수정 필요
- `pi1/spiders/list_spider.py`와 `pi2/parsers/recall_parser.py`의 선택자 확인

## 다음 단계

1. 실제 웹사이트 구조에 맞게 크롤러 선택자 수정
2. 파싱 규칙 정확도 향상
3. 에러 처리 및 재시도 로직 추가
4. 모니터링 및 알림 시스템 구축

