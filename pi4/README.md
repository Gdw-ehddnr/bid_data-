# Pi #4 - Hadoop / 분석

## 역할
- 하둡 설치(NameNode or DataNode)
- Kafka에서 데이터 수신 후 HDFS 적재
- 데이터 분석

## 데이터 흐름
1. **Kafka Topic `recall-db-records`에서 데이터 수신** (Pi3로부터, 선택적)
   또는 **DB를 직접 조회**하여 데이터 수집
2. HDFS에 적재
3. 분석 작업 수행

## Kafka 사용
- **Consumer**: `recall-db-records` 토픽에서 메시지 수신 (선택적)
- Consumer Group: `pi4-hadoop-loader`
- 또는 DB를 직접 조회하여 배치로 데이터 수집

## 디렉토리 구조
- `hadoop/`: 하둡 설정 및 스크립트
- `scripts/`: 실행 스크립트
- `analytics/`: 분석 코드
- `logs/`: 실행 로그

## 사용 예시

### 방법 1: Kafka에서 수신
```python
from common.utils import create_consumer
import yaml

# 설정 로드
with open('config/config.yaml') as f:
    config = yaml.safe_load(f)

# Kafka Consumer 생성
consumer = create_consumer(
    bootstrap_servers=config['kafka']['bootstrap_servers'],
    topic=config['kafka']['topics']['db_records'],
    group_id=config['kafka']['consumer_groups']['pi4']
)

# 데이터 수신 및 HDFS 적재
def load_to_hdfs(message):
    # HDFS에 적재
    load_data_to_hdfs(message)

consumer.consume(load_to_hdfs)
```

### 방법 2: DB 직접 조회
```python
# DB에서 배치로 데이터 조회 후 HDFS 적재
# 주기적으로 실행하는 스크립트
```

