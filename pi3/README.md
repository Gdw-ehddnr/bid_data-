# Pi #3 - DB Server & HDFS Loader

## 역할
- MariaDB/MySQL 설치 및 운영
- `recall` 테이블 저장
- 중복 처리
- 필드형 검증
- 주간 백업
- **CSV Export 및 HDFS 적재** (Pi4 역할 통합)

## 데이터 흐름
1. **Kafka Topic `recall-parsed`에서 파싱된 데이터 수신** (Pi2로부터)
2. 데이터 검증
3. MariaDB에 저장 (중복 체크)
4. **주기적으로 CSV Export 및 HDFS 적재** (기본: 24시간마다)

## Kafka 사용
- **Consumer**: `recall-parsed` 토픽에서 메시지 수신
- Consumer Group: `pi3-db-server`

## HDFS 적재
- **자동 적재**: `run_db_consumer.py` 실행 시 백그라운드 스레드로 주기적 적재
- **수동 적재**: `python pi3/scripts/load_to_hdfs.py` 실행
- **CSV Export**: `python pi3/scripts/export_to_csv.py` 실행

## 디렉토리 구조
- `db/`: DB 스키마 및 연결 코드
- `scripts/`: 실행 스크립트 및 백업 스크립트
- `backups/`: 백업 파일
- `logs/`: 실행 로그

## 사용 예시

### DB 저장 및 자동 HDFS 적재
```bash
# Kafka에서 데이터 수신하여 DB 저장, 주기적으로 HDFS 적재
python pi3/scripts/run_db_consumer.py
```

### 수동 CSV Export
```bash
# DB 데이터를 CSV로 내보내기
python pi3/scripts/export_to_csv.py

# 최근 100개만 export
python pi3/scripts/export_to_csv.py --limit 100
```

### 수동 HDFS 적재
```bash
# DB 데이터를 HDFS에 적재
python pi3/scripts/load_to_hdfs.py

# 최근 100개만 적재
python pi3/scripts/load_to_hdfs.py --limit 100

# 특정 날짜 이후 데이터만 적재
python pi3/scripts/load_to_hdfs.py --since 2025-01-01
```

