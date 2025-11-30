# Kafka 설치 및 설정 가이드

## 개요

라즈베리파이 환경에서 Apache Kafka를 설치하고 설정하는 방법입니다.

## 사전 요구사항

- Java 8 이상 (OpenJDK 권장)
- 최소 2GB RAM
- 충분한 디스크 공간

## 설치 방법

### 1. Java 설치

```bash
# OpenJDK 설치
sudo apt update
sudo apt install -y openjdk-11-jdk

# Java 버전 확인
java -version
```

### 2. Kafka 다운로드 및 설치

```bash
# 홈 디렉토리로 이동
cd ~

# Kafka 다운로드 (최신 버전 확인: https://kafka.apache.org/downloads)
wget https://downloads.apache.org/kafka/3.6.0/kafka_2.13-3.6.0.tgz

# 압축 해제
tar -xzf kafka_2.13-3.6.0.tgz

# 심볼릭 링크 생성 (버전 관리 용이)
ln -s kafka_2.13-3.6.0 kafka

# 환경 변수 설정
echo 'export KAFKA_HOME=~/kafka' >> ~/.bashrc
echo 'export PATH=$PATH:$KAFKA_HOME/bin' >> ~/.bashrc
source ~/.bashrc
```

### 3. Kafka 설정

#### server.properties 수정

```bash
cd ~/kafka/config

# server.properties 편집
nano server.properties
```

주요 설정 항목:

```properties
# 브로커 ID (각 브로커마다 고유한 ID)
broker.id=0

# 로그 디렉토리
log.dirs=/tmp/kafka-logs

# Zookeeper 연결 정보
zookeeper.connect=localhost:2181

# 리스너 설정 (외부 접근 허용)
listeners=PLAINTEXT://0.0.0.0:9092
advertised.listeners=PLAINTEXT://localhost:9092

# 로그 보관 기간 (일)
log.retention.hours=168

# 로그 세그먼트 크기
log.segment.bytes=1073741824
```

### 4. Zookeeper 설정

Kafka는 Zookeeper가 필요합니다.

```bash
cd ~/kafka/config

# zookeeper.properties 편집
nano zookeeper.properties
```

기본 설정으로도 동작하지만, 필요시 수정:

```properties
dataDir=/tmp/zookeeper
clientPort=2181
```

### 5. 서비스 시작

#### Zookeeper 시작

```bash
cd ~/kafka
bin/zookeeper-server-start.sh config/zookeeper.properties &
```

#### Kafka 시작

```bash
cd ~/kafka
bin/kafka-server-start.sh config/server.properties &
```

### 6. 시스템 서비스로 등록 (선택사항)

더 편리한 관리를 위해 systemd 서비스로 등록:

#### Zookeeper 서비스

```bash
sudo nano /etc/systemd/system/zookeeper.service
```

```ini
[Unit]
Description=Apache Zookeeper
After=network.target

[Service]
Type=simple
User=pi
ExecStart=/home/pi/kafka/bin/zookeeper-server-start.sh /home/pi/kafka/config/zookeeper.properties
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

#### Kafka 서비스

```bash
sudo nano /etc/systemd/system/kafka.service
```

```ini
[Unit]
Description=Apache Kafka
After=network.target zookeeper.service

[Service]
Type=simple
User=pi
ExecStart=/home/pi/kafka/bin/kafka-server-start.sh /home/pi/kafka/config/server.properties
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

#### 서비스 활성화 및 시작

```bash
sudo systemctl daemon-reload
sudo systemctl enable zookeeper
sudo systemctl enable kafka
sudo systemctl start zookeeper
sudo systemctl start kafka
```

## 토픽 생성

프로젝트에 필요한 토픽들을 생성합니다:

```bash
# recall-new-urls 토픽 생성
bin/kafka-topics.sh --create \
  --bootstrap-server localhost:9092 \
  --replication-factor 1 \
  --partitions 3 \
  --topic recall-new-urls

# recall-parsed 토픽 생성
bin/kafka-topics.sh --create \
  --bootstrap-server localhost:9092 \
  --replication-factor 1 \
  --partitions 3 \
  --topic recall-parsed

# recall-db-records 토픽 생성
bin/kafka-topics.sh --create \
  --bootstrap-server localhost:9092 \
  --replication-factor 1 \
  --partitions 3 \
  --topic recall-db-records
```

## 토픽 확인

```bash
# 모든 토픽 목록 확인
bin/kafka-topics.sh --list --bootstrap-server localhost:9092

# 특정 토픽 상세 정보 확인
bin/kafka-topics.sh --describe --bootstrap-server localhost:9092 --topic recall-new-urls
```

## 테스트

### Producer 테스트

```bash
bin/kafka-console-producer.sh \
  --bootstrap-server localhost:9092 \
  --topic recall-new-urls
```

메시지 입력 후 Ctrl+C로 종료

### Consumer 테스트

```bash
bin/kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic recall-new-urls \
  --from-beginning
```

## 네트워크 설정

다른 Pi에서 접근하려면:

1. `server.properties`에서 `advertised.listeners`를 실제 IP로 변경:
   ```properties
   advertised.listeners=PLAINTEXT://192.168.1.10:9092
   ```

2. 방화벽 포트 개방:
   ```bash
   sudo ufw allow 9092/tcp
   ```

3. 다른 Pi의 `config/config.yaml`에서 브로커 주소 설정:
   ```yaml
   kafka:
     bootstrap_servers: "192.168.1.10:9092"
   ```

## 모니터링

### Consumer 그룹 확인

```bash
bin/kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 \
  --list

# 특정 그룹의 lag 확인
bin/kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 \
  --group pi2-detail-parser \
  --describe
```

## 문제 해결

### 포트 충돌

```bash
# 포트 사용 확인
sudo netstat -tulpn | grep 9092
sudo netstat -tulpn | grep 2181
```

### 로그 확인

```bash
# Kafka 로그
tail -f ~/kafka/logs/server.log

# Zookeeper 로그
tail -f ~/kafka/logs/zookeeper.out
```

### 메모리 부족

라즈베리파이의 경우 메모리가 부족할 수 있으므로, `server.properties`에서 힙 메모리 제한:

```properties
# JVM 힙 메모리 설정 (Kafka 시작 스크립트 수정 필요)
KAFKA_HEAP_OPTS="-Xmx512M -Xms512M"
```

## 참고 자료

- [Apache Kafka 공식 문서](https://kafka.apache.org/documentation/)
- [Kafka 설치 가이드](https://kafka.apache.org/quickstart)

