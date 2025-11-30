# 테스트 가이드

## 사전 준비

1. **설정 파일 생성**
   ```bash
   # 각 Pi에서 해당하는 설정 파일 복사
   # Pi1
   cp config/config.pi1.yaml config/config.yaml
   
   # Pi2
   cp config/config.pi2.yaml config/config.yaml
   
   # Pi3
   cp config/config.pi3.yaml config/config.yaml
   
   # Pi4
   cp config/config.pi4.yaml config/config.yaml
   ```

2. **설정 파일 수정**
   - Kafka 브로커 주소 (실제 IP로 수정)
   - DB 비밀번호 (Pi3만)
   - 기타 필요한 설정

## 단계별 테스트

### 1. 연결 테스트

각 Pi에서 기본 연결을 테스트합니다:

```bash
python scripts/test_pipeline.py
```

이 스크립트는 다음을 확인합니다:
- 설정 파일 존재 여부
- 웹사이트 접근 가능 여부
- Kafka 연결
- DB 연결 (Pi3만)

### 2. Pi1 테스트 (목록 크롤러)

```bash
cd pi1
python scripts/run_spider.py
```

**확인 사항:**
- 목록 페이지 크롤링 성공
- URL 추출 성공
- Kafka에 메시지 발행 성공

**Kafka 메시지 확인:**
```bash
# Kafka 서버에서
bin/kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic recall-new-urls \
  --from-beginning
```

### 3. Pi2 테스트 (상세 크롤러)

```bash
cd pi2
python scripts/run_consumer.py
```

**확인 사항:**
- Kafka에서 URL 수신
- 상세 페이지 크롤링 성공
- 데이터 파싱 성공
- Kafka에 파싱된 데이터 발행

**Kafka 메시지 확인:**
```bash
bin/kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic recall-parsed \
  --from-beginning
```

### 4. Pi3 테스트 (DB 저장)

```bash
cd pi3
python scripts/run_db_consumer.py
```

**확인 사항:**
- Kafka에서 파싱된 데이터 수신
- 데이터 검증 성공
- DB 저장 성공
- 중복 처리 동작

**DB 확인:**
```bash
mysql -u recall_user -p recall_db
SELECT COUNT(*) FROM recall;
SELECT * FROM recall LIMIT 5;
```

### 5. Pi4 테스트 (HDFS 적재)

```bash
cd pi4
# DB에서 직접 조회하여 HDFS 적재
python scripts/load_to_hdfs.py --source db
```

**확인 사항:**
- DB에서 데이터 조회
- CSV 파일 생성
- HDFS 적재 성공

## 전체 파이프라인 테스트

1. **순서대로 실행:**
   ```bash
   # 터미널 1: Pi1
   cd pi1 && python scripts/run_spider.py
   
   # 터미널 2: Pi2
   cd pi2 && python scripts/run_consumer.py
   
   # 터미널 3: Pi3
   cd pi3 && python scripts/run_db_consumer.py
   
   # 터미널 4: Pi4 (선택적)
   cd pi4 && python scripts/load_to_hdfs.py --source db
   ```

2. **데이터 흐름 확인:**
   - Pi1 → Kafka → Pi2 → Kafka → Pi3 → DB
   - 각 단계에서 로그 확인
   - Kafka 토픽 모니터링
   - DB 레코드 확인

## 문제 해결

### 웹사이트 구조 확인

실제 웹사이트 구조를 확인하려면:

```bash
python scripts/inspect_website.py
```

이 스크립트는:
- 목록 페이지 HTML 구조 분석
- 상세 페이지 HTML 구조 분석
- HTML 샘플 저장 (`data/raw/`)

### 선택자 수정

웹사이트 구조가 다르면 다음 파일 수정:

1. **목록 페이지 선택자**: `pi1/spiders/list_spider.py`
   - `parse_list()` 메서드의 선택자 수정

2. **상세 페이지 선택자**: `pi2/parsers/recall_parser.py`
   - `parse()` 메서드의 선택자 수정
   - `_extract_from_table()` 메서드의 테이블 구조 확인

### 디버깅

1. **HTML 저장 확인**
   - 크롤링 실패 시 `data/raw/list_page_debug.html` 확인
   - 실제 HTML 구조에 맞게 선택자 수정

2. **로그 확인**
   - 각 Pi의 `logs/` 디렉토리에서 로그 확인
   - 로그 레벨을 DEBUG로 변경하여 상세 정보 확인

3. **Kafka 메시지 확인**
   - 각 토픽의 메시지 내용 확인
   - Consumer 그룹의 lag 확인

## 성능 테스트

### 부하 테스트

```bash
# 여러 URL을 Kafka에 발행하여 테스트
python scripts/test_kafka_load.py
```

### 모니터링

- Kafka Consumer 그룹 lag 모니터링
- DB 쿼리 성능 확인
- 크롤링 속도 확인

## 다음 단계

테스트가 성공하면:
1. 실제 운영 환경 설정
2. 스케줄링 설정 (cron 등)
3. 모니터링 및 알림 설정
4. 백업 및 복구 계획 수립

