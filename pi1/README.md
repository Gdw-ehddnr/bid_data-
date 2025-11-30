# Pi #1 - Master / Incremental Controller

## 역할
- 목록 크롤러(ListSpider) 실행
- **증분(신규 공지 식별)만 담당**
- 수동 실행 스크립트 관리
- 전체 플로우 테스트 조율

## 데이터 흐름
1. 자동차리콜센터 목록 페이지 크롤링
2. 신규 URL 추출
3. **Kafka Topic `recall-new-urls`에 발행** (Pi2로 전달)

## Kafka 사용
- **Producer**: `recall-new-urls` 토픽에 메시지 발행
- 메시지 형식:
  ```json
  {
    "url": "https://www.car.go.kr/...",
    "title": "○○차량 리콜",
    "notice_date": "2025-03-01"
  }
  ```

## 디렉토리 구조
- `spiders/`: Scrapy 스파이더 코드
- `scripts/`: 실행 스크립트
- `logs/`: 실행 로그

## 사용 예시
```python
from common.utils import create_producer
import yaml

# 설정 로드
with open('config/config.yaml') as f:
    config = yaml.safe_load(f)

# Kafka Producer 생성
producer = create_producer(
    bootstrap_servers=config['kafka']['bootstrap_servers'],
    topic=config['kafka']['topics']['new_urls']
)

# 신규 URL 발행
producer.send({
    "url": "https://www.car.go.kr/...",
    "title": "리콜 제목",
    "notice_date": "2025-03-01"
})
```

