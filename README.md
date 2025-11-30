# 자동차 리콜센터 데이터 파이프라인 프로젝트

자동차리콜센터(https://www.car.go.kr)의 공지 데이터를 **Scrapy → 정제 → DB 저장 → Hadoop(HDFS) 분석**까지 구축하는 분산형 데이터 파이프라인 프로젝트입니다.

4대의 라즈베리파이를 분업하여 분산형 데이터 파이프라인을 구현합니다.

## 📋 프로젝트 구조

```
bid_data-/
├── common/                 # 공통 모듈
│   ├── schemas/           # 데이터 스키마 정의
│   ├── utils/             # 유틸리티 함수
│   └── validators/        # 데이터 검증 모듈
│
├── pi1/                   # Pi #1 - Master / Incremental Controller
│   ├── spiders/          # 목록 크롤러 스파이더
│   ├── scripts/          # 실행 스크립트
│   └── logs/             # 실행 로그
│
├── pi2/                   # Pi #2 - Detail Parsing Worker
│   ├── spiders/          # 상세 페이지 크롤링 스파이더
│   ├── parsers/          # 파싱 및 정규화 로직
│   ├── scripts/          # 실행 스크립트
│   └── logs/             # 실행 로그
│
├── pi3/                   # Pi #3 - DB Server
│   ├── db/               # DB 스키마 및 연결 코드
│   ├── scripts/          # 실행 및 백업 스크립트
│   ├── backups/          # 백업 파일
│   └── logs/             # 실행 로그
│
├── pi4/                   # Pi #4 - Hadoop / 분석 (선택적)
│   ├── hadoop/           # 하둡 설정 및 스크립트
│   ├── scripts/          # 실행 스크립트
│   ├── analytics/        # 분석 코드
│   └── logs/             # 실행 로그
│   # 참고: Pi4가 작동하지 않는 경우, Pi3에서 HDFS 적재까지 처리합니다
│
├── data/                  # 데이터 디렉토리
│   ├── raw/              # 원본 데이터
│   ├── processed/        # 처리된 데이터
│   └── export/           # 내보내기 데이터 (CSV 등)
│
├── config/                # 설정 파일
│   └── config.example.yaml
│
└── scripts/               # 공통 스크립트
```

## 🔄 라즈베리파이 역할 분담

### **Pi #1 — Master / Incremental Controller**
- 목록 크롤러(ListSpider) 실행
- **증분(신규 공지 식별)만 담당**
- 수동 실행 스크립트 관리
- 전체 플로우 테스트 조율

**데이터 출력**: Kafka Topic `recall-new-urls`

### **Pi #2 — Detail Parsing Worker**
- 상세 페이지 크롤링
- 필드 파싱 및 정규화
- JSON 결과 반환
- 파싱 규칙 업데이트

**데이터 입력**: Kafka Topic `recall-new-urls`  
**데이터 출력**: Kafka Topic `recall-parsed`

### **Pi #3 — DB Server & HDFS Loader**
- MariaDB/MySQL 설치 및 운영
- `recall` 테이블 저장
- 중복 처리
- 필드형 검증
- 주간 백업
- **CSV Export 및 HDFS 적재** (Pi4 역할 통합)

**데이터 입력**: Kafka Topic `recall-parsed`  
**데이터 출력**: 
- CSV 파일 (`data/export/`)
- HDFS 적재 (주기적 또는 수동)

### **Pi #4 — Hadoop / 분석** (선택적)
- 하둡 설치(NameNode or DataNode)
- HDFS에서 데이터 분석
- 데이터 분석

**참고**: Pi4가 작동하지 않는 경우, Pi3에서 HDFS 적재까지 처리합니다.

## 📊 전체 데이터 흐름

```
Pi1: 목록 크롤링 → 신규 URL 추출
      |
      V (Kafka: recall-new-urls)
Pi2: 상세 크롤링 → 정제 → 파싱
      |
      V (Kafka: recall-parsed)
Pi3: DB 저장 → 중복 처리 → CSV Export → HDFS 적재
      |
      V (HDFS: /recall_data/)
Pi4: HDFS 분석 (선택적, Pi3에서 HDFS 적재 처리 가능)
```

## 📝 필드 스키마

| 필드 | 설명 | 예시 | 처리 규칙 |
| --- | --- | --- | --- |
| maker | 제조사 | 현대자동차 | 원본 |
| model | 모델/연식 | 아반떼(2020) | 연식 분리 가능 |
| model_year | 연식 | 2020 | 숫자 파싱 |
| defect_part | 결함부위 | 제동장치 | 원본 |
| defect_part_std | 표준부위 | brake | 매핑 |
| symptom | 증상 | 제동거리 증가 | trim |
| action | 시정조치 | 실린더 교환 | 키워드 태그 가능 |
| start_date | 시정개시 | 2025-03-12 | YYYY-MM-DD |
| qty | 대상대수 | 1234 | 숫자만 추출 |
| notice_date | 공지일 | 2025-03-01 | YYYY-MM-DD |
| url | 상세링크 | https://… | PK 후보 |
| title | 제목 | ○○차량 리콜 | 목록 데이터 |

## 🔧 설정

1. `config/config.example.yaml`을 `config/config.yaml`로 복사
2. 각 Pi의 설정에 맞게 수정
3. 데이터베이스 및 하둡 설정 입력

## 📦 데이터 전달 방식

Pi 간 데이터 전달은 **Apache Kafka**를 사용합니다:

### Kafka Topics

- **`recall-new-urls`**: Pi1 → Pi2
  - 신규 URL 목록 전달
  - 메시지 형식: `{"url": "...", "title": "...", "notice_date": "..."}`

- **`recall-parsed`**: Pi2 → Pi3
  - 파싱된 리콜 데이터 전달
  - 메시지 형식: `RecallSchema` JSON

- **`recall-db-records`**: Pi3 → Pi4 (선택적)
  - DB 저장 완료된 레코드 전달
  - 또는 Pi4에서 DB를 직접 조회하여 HDFS 적재

### Kafka 설정

각 Pi의 `config/config.yaml`에서 Kafka 브로커 주소와 토픽을 설정합니다.

```yaml
kafka:
  bootstrap_servers: "kafka-broker:9092"  # Kafka 브로커 주소
  topics:
    new_urls: "recall-new-urls"
    parsed_recalls: "recall-parsed"
    db_records: "recall-db-records"
```

> **참고**: Kafka는 별도 서버에 설치하거나, Pi 중 하나에 설치하여 사용할 수 있습니다.

## 🚀 시작하기

### 빠른 시작

1. **Kafka 설치 및 설정**: [Kafka 설치 가이드](docs/KAFKA_SETUP.md) 참고
2. **전체 설정 가이드**: [설정 가이드](docs/SETUP_GUIDE.md) 참고
3. **각 Pi별 실행**:
   - Pi1: `python pi1/scripts/run_spider.py`
   - Pi2: `python pi2/scripts/run_consumer.py`
   - Pi3: `python pi3/scripts/run_db_consumer.py`
   - Pi4: `python pi4/scripts/load_to_hdfs.py --source db`

### 상세 문서

- [Kafka 설치 가이드](docs/KAFKA_SETUP.md)
- [전체 설정 가이드](docs/SETUP_GUIDE.md)
- [Pi1 README](pi1/README.md) - 목록 크롤러
- [Pi2 README](pi2/README.md) - 상세 크롤러
- [Pi3 README](pi3/README.md) - DB 저장
- [Pi4 README](pi4/README.md) - HDFS 적재

## 📁 주요 파일 구조

### 공통 모듈
- `common/schemas/recall_schema.py`: 데이터 스키마 정의
- `common/utils/kafka_producer.py`: Kafka Producer 유틸리티
- `common/utils/kafka_consumer.py`: Kafka Consumer 유틸리티
- `common/validators/recall_validator.py`: 데이터 검증

### Pi별 구현
- **Pi1**: `pi1/spiders/list_spider.py` - 목록 크롤러
- **Pi2**: `pi2/parsers/recall_parser.py` - 파서, `pi2/scripts/run_consumer.py` - 실행 스크립트
- **Pi3**: `pi3/db/schema.sql` - DB 스키마, `pi3/db/repository.py` - 저장소
- **Pi4**: `pi4/scripts/load_to_hdfs.py` - HDFS 적재 스크립트

## ⚠️ 주의사항

1. **웹사이트 구조 확인**: 실제 자동차리콜센터 사이트 구조에 맞게 크롤러 선택자를 수정해야 합니다.
   - `pi1/spiders/list_spider.py`의 목록 페이지 선택자
   - `pi2/parsers/recall_parser.py`의 상세 페이지 선택자

2. **설정 파일**: 각 Pi에서 `config/config.yaml`을 생성하고 올바른 설정을 입력해야 합니다.

3. **Kafka 브로커**: Kafka 서버가 실행 중이어야 하며, 토픽이 생성되어 있어야 합니다.
