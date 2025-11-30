# 설치 체크리스트

## 현재 설치 상태 (이미지 기준)

### 공통 설치 (모든 Pi)
- ✅ Git
- ✅ JDK (Java Development Kit)
- ✅ 하둡 (Hadoop)

### Pi3 추가 설치
- ✅ MySQL
- ✅ Docker

---

## 추가로 필요한 설치

### 1. Python 환경 (모든 Pi) ⚠️ 필수

```bash
# Python 3 확인
python3 --version

# pip 확인
python3 -m pip --version

# 없으면 설치
sudo apt install -y python3 python3-pip
```

### 2. Python 패키지 (모든 Pi) ⚠️ 필수

```bash
cd ~/bid_data-
pip3 install --user -r requirements.txt
```

**필요한 패키지:**
- scrapy
- kafka-python
- pymysql
- sqlalchemy
- pyyaml
- python-dateutil
- pandas
- numpy
- requests
- beautifulsoup4
- lxml

### 3. Kafka (Pi1에만 필요) ⚠️ 필수

JDK는 설치되어 있지만, **Kafka 자체가 설치되어 있지 않습니다.**

```bash
# Pi1에서 실행
cd ~
mkdir kafka && cd kafka
wget https://downloads.apache.org/kafka/3.5.0/kafka_2.13-3.5.0.tgz
tar -xzf kafka_2.13-3.5.0.tgz
cd kafka_2.13-3.5.0

# 설정 파일 수정
nano config/server.properties
# listeners=PLAINTEXT://0.0.0.0:9092
# advertised.listeners=PLAINTEXT://<Pi1의 IP>:9092

# Zookeeper 및 Kafka 시작
bin/zookeeper-server-start.sh config/zookeeper.properties &
bin/kafka-server-start.sh config/server.properties &
```

### 4. MariaDB/MySQL 확인 (Pi3) ⚠️ 필수

MySQL이 설치되어 있지만, **데이터베이스와 사용자가 생성되어 있는지 확인** 필요:

```bash
# Pi3에서 실행
sudo mysql -u root -p

# 데이터베이스 확인
SHOW DATABASES;

# recall_db가 없으면 생성
CREATE DATABASE recall_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# 사용자 확인
SELECT user, host FROM mysql.user WHERE user = 'recall_user';

# 사용자가 없으면 생성
CREATE USER 'recall_user'@'localhost' IDENTIFIED BY 'your_password_here';
GRANT ALL PRIVILEGES ON recall_db.* TO 'recall_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 5. 프로젝트 코드 (모든 Pi) ⚠️ 필수

```bash
# Git으로 클론하거나 USB/SCP로 복사
cd ~
git clone <repo-url> bid_data-
# 또는
# scp -r bid_data- pi@<pi-ip>:/home/pi/
```

### 6. 디렉토리 생성 (모든 Pi) ⚠️ 필수

```bash
cd ~/bid_data-
mkdir -p data/raw data/processed data/export
mkdir -p pi1/logs pi2/logs pi3/logs
```

---

## 설치 확인 스크립트

각 Pi에서 실행하여 설치 상태 확인:

```bash
cd ~/bid_data-
python3 -c "
import sys
import subprocess

print('=' * 60)
print('설치 상태 확인')
print('=' * 60)

# Python 확인
try:
    version = sys.version.split()[0]
    print(f'✓ Python: {version}')
except:
    print('✗ Python: 설치 필요')

# pip 확인
try:
    import pip
    print('✓ pip: 설치됨')
except:
    print('✗ pip: 설치 필요')

# 필수 패키지 확인
packages = ['scrapy', 'kafka', 'pymysql', 'sqlalchemy', 'yaml']
for pkg in packages:
    try:
        if pkg == 'yaml':
            __import__('yaml')
        elif pkg == 'kafka':
            from kafka import KafkaProducer
        else:
            __import__(pkg)
        print(f'✓ {pkg}: 설치됨')
    except:
        print(f'✗ {pkg}: 설치 필요')

# Java 확인
try:
    result = subprocess.run(['java', '-version'], capture_output=True, text=True, stderr=subprocess.STDOUT)
    if result.returncode == 0:
        print('✓ Java: 설치됨')
    else:
        print('✗ Java: 설치 필요')
except:
    print('✗ Java: 설치 필요')

# Git 확인
try:
    result = subprocess.run(['git', '--version'], capture_output=True, text=True)
    if result.returncode == 0:
        print('✓ Git: 설치됨')
    else:
        print('✗ Git: 설치 필요')
except:
    print('✗ Git: 설치 필요')

print('=' * 60)
"
```

---

## Pi별 필수 설치 요약

### Pi1 (목록 크롤러)
- ✅ Git
- ✅ JDK
- ✅ 하둡
- ⚠️ **Python 3 + pip** (필수)
- ⚠️ **Python 패키지들** (필수)
- ⚠️ **Kafka** (필수)
- ⚠️ **프로젝트 코드** (필수)

### Pi2 (상세 파서)
- ✅ Git
- ✅ JDK
- ✅ 하둡
- ⚠️ **Python 3 + pip** (필수)
- ⚠️ **Python 패키지들** (필수)
- ⚠️ **프로젝트 코드** (필수)

### Pi3 (DB 저장)
- ✅ Git
- ✅ JDK
- ✅ MySQL
- ✅ Docker
- ✅ 하둡
- ⚠️ **Python 3 + pip** (필수)
- ⚠️ **Python 패키지들** (필수)
- ⚠️ **데이터베이스 및 사용자 생성** (필수)
- ⚠️ **프로젝트 코드** (필수)

---

## 빠른 설치 명령어

### 모든 Pi에서 공통

```bash
# Python 및 pip 설치
sudo apt install -y python3 python3-pip

# 프로젝트 복사 후
cd ~/bid_data-
pip3 install --user -r requirements.txt
mkdir -p data/raw data/processed data/export pi1/logs pi2/logs pi3/logs
```

### Pi1만

```bash
# Kafka 설치 (docs/KAFKA_INSTALL_GUIDE.md 참조)
cd ~
mkdir kafka && cd kafka
wget https://downloads.apache.org/kafka/3.5.0/kafka_2.13-3.5.0.tgz
tar -xzf kafka_2.13-3.5.0.tgz
cd kafka_2.13-3.5.0
```

### Pi3만

```bash
# 데이터베이스 및 사용자 생성
sudo mysql -u root -p
# CREATE DATABASE recall_db;
# CREATE USER 'recall_user'@'localhost' IDENTIFIED BY 'password';
# GRANT ALL PRIVILEGES ON recall_db.* TO 'recall_user'@'localhost';
# FLUSH PRIVILEGES;
# EXIT;

# 테이블 생성
cd ~/bid_data-
mysql -u recall_user -p recall_db < pi3/db/schema.sql
```

---

## 다음 단계

설치가 완료되면:
1. 설정 파일 생성 및 수정 (`docs/RASPBERRY_PI_SETUP.md` 참조)
2. 설정 파일 검증: `python3 scripts/validate_config.py --pi pi1`
3. 통합 테스트: `python3 scripts/integration_test.py`
4. 실제 실행

