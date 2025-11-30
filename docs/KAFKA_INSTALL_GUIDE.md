# Kafka 설치 및 설정 가이드

## 라즈베리파이에 Kafka 설치하기

### 1. Java 설치 (필수)

Kafka는 Java가 필요합니다.

```bash
# Java 11 설치 (OpenJDK)
sudo apt update
sudo apt install -y openjdk-11-jdk

# Java 버전 확인
java -version
```

### 2. Kafka 다운로드

```bash
# 작업 디렉토리 생성
cd ~
mkdir kafka
cd kafka

# Kafka 다운로드 (2.13-3.5.0 버전, ARM64용)
# 라즈베리파이 4 (64-bit)의 경우
wget https://downloads.apache.org/kafka/3.5.0/kafka_2.13-3.5.0.tgz

# 압축 해제
tar -xzf kafka_2.13-3.5.0.tgz
cd kafka_2.13-3.5.0
```

**참고**: 라즈베리파이 3 (32-bit)의 경우 다른 버전이 필요할 수 있습니다.

### 3. Zookeeper 설정

Kafka는 Zookeeper를 사용합니다 (Kafka 3.5.0은 KRaft 모드도 지원하지만, 여기서는 Zookeeper 사용).

```bash
# Zookeeper 설정 파일 수정
nano config/zookeeper.properties

# 주요 설정:
# dataDir=/tmp/zookeeper
# clientPort=2181
```

### 4. Kafka 설정

```bash
# Kafka 설정 파일 수정
nano config/server.properties

# 주요 설정:
# broker.id=0
# listeners=PLAINTEXT://0.0.0.0:9092
# advertised.listeners=PLAINTEXT://YOUR_PI_IP:9092
# log.dirs=/tmp/kafka-logs
# zookeeper.connect=localhost:2181
```

**중요**: `YOUR_PI_IP`를 실제 라즈베리파이 IP 주소로 변경하세요.

### 5. systemd 서비스 등록 (선택적)

```bash
# Zookeeper 서비스 파일 생성
sudo nano /etc/systemd/system/zookeeper.service
```

```ini
[Unit]
Description=Apache Zookeeper
After=network.target

[Service]
Type=simple
User=pi
ExecStart=/home/pi/kafka/kafka_2.13-3.5.0/bin/zookeeper-server-start.sh /home/pi/kafka/kafka_2.13-3.5.0/config/zookeeper.properties
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

```bash
# Kafka 서비스 파일 생성
sudo nano /etc/systemd/system/kafka.service
```

```ini
[Unit]
Description=Apache Kafka
After=network.target zookeeper.service

[Service]
Type=simple
User=pi
ExecStart=/home/pi/kafka/kafka_2.13-3.5.0/bin/kafka-server-start.sh /home/pi/kafka/kafka_2.13-3.5.0/config/server.properties
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

```bash
# 서비스 활성화
sudo systemctl daemon-reload
sudo systemctl enable zookeeper
sudo systemctl enable kafka
sudo systemctl start zookeeper
sudo systemctl start kafka
```

### 6. 수동 실행 (테스트용)

```bash
# 터미널 1: Zookeeper 시작
bin/zookeeper-server-start.sh config/zookeeper.properties

# 터미널 2: Kafka 시작
bin/kafka-server-start.sh config/server.properties
```

### 7. 토픽 생성

```bash
# 토픽 생성 스크립트 실행
cd /path/to/bid_data-
python scripts/kafka_setup_example.py

# 또는 수동으로 토픽 생성
bin/kafka-topics.sh --create \
  --bootstrap-server localhost:9092 \
  --replication-factor 1 \
  --partitions 1 \
  --topic recall-new-urls

bin/kafka-topics.sh --create \
  --bootstrap-server localhost:9092 \
  --replication-factor 1 \
  --partitions 1 \
  --topic recall-parsed

bin/kafka-topics.sh --create \
  --bootstrap-server localhost:9092 \
  --replication-factor 1 \
  --partitions 1 \
  --topic recall-db-records
```

### 8. 토픽 확인

```bash
# 모든 토픽 목록 확인
bin/kafka-topics.sh --list --bootstrap-server localhost:9092

# 특정 토픽 상세 정보
bin/kafka-topics.sh --describe --bootstrap-server localhost:9092 --topic recall-new-urls
```

## 네트워크 설정

### 방화벽 설정

```bash
# 포트 9092 (Kafka) 열기
sudo ufw allow 9092/tcp
sudo ufw allow 2181/tcp  # Zookeeper
```

### IP 주소 확인

```bash
# 라즈베리파이 IP 주소 확인
hostname -I
```

이 IP 주소를 다른 Pi의 `config/config.yaml`에서 `bootstrap_servers`에 사용하세요.

## 테스트

### Producer 테스트

```bash
# Producer 시작
bin/kafka-console-producer.sh --bootstrap-server localhost:9092 --topic recall-new-urls

# 메시지 입력 (예: {"url": "test", "title": "test"})
```

### Consumer 테스트

```bash
# Consumer 시작
bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic recall-new-urls --from-beginning
```

## 문제 해결

### Java 메모리 부족
```bash
# Kafka 시작 스크립트 수정
export KAFKA_HEAP_OPTS="-Xmx256M -Xms256M"
```

### 포트 충돌
```bash
# 포트 사용 확인
sudo netstat -tulpn | grep 9092
sudo netstat -tulpn | grep 2181
```

### 로그 확인
```bash
# Kafka 로그
tail -f logs/server.log

# Zookeeper 로그
tail -f logs/zookeeper.out
```

## 참고

- Kafka 공식 문서: https://kafka.apache.org/documentation/
- 라즈베리파이용 최적화된 설정이 필요할 수 있습니다
- 메모리 부족 시 JVM 힙 크기 조정 필요

