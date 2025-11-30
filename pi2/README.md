# Pi #2 - Detail Parsing Worker

## 역할
- 상세 페이지 크롤링
- 필드 파싱 및 정규화
- JSON 결과 반환
- 파싱 규칙 업데이트

## 데이터 흐름
1. **Kafka Topic `recall-new-urls`에서 URL 수신** (Pi1로부터)
2. 각 URL의 상세 페이지 크롤링
3. 필드 파싱 및 정규화
4. **Kafka Topic `recall-parsed`에 파싱 결과 발행** (Pi3로 전달)

## Kafka 사용
- **Consumer**: `recall-new-urls` 토픽에서 메시지 수신
- **Producer**: `recall-parsed` 토픽에 파싱된 데이터 발행
- Consumer Group: `pi2-detail-parser`

## 디렉토리 구조
- `spiders/`: 상세 페이지 크롤링 스파이더
- `parsers/`: 파싱 및 정규화 로직
- `scripts/`: 실행 스크립트
- `logs/`: 실행 로그

## 사용 예시
```python
from common.utils import create_consumer, create_producer
import yaml

# 설정 로드
with open('config/config.yaml') as f:
    config = yaml.safe_load(f)

# Kafka Consumer 생성
consumer = create_consumer(
    bootstrap_servers=config['kafka']['bootstrap_servers'],
    topic=config['kafka']['topics']['new_urls'],
    group_id=config['kafka']['consumer_groups']['pi2']
)

# Kafka Producer 생성
producer = create_producer(
    bootstrap_servers=config['kafka']['bootstrap_servers'],
    topic=config['kafka']['topics']['parsed_recalls']
)

# URL 수신 및 처리
def process_url(message):
    url = message['url']
    # 크롤링 및 파싱
    parsed_data = crawl_and_parse(url)
    # 파싱 결과 발행
    producer.send(parsed_data)

consumer.consume(process_url)
```

