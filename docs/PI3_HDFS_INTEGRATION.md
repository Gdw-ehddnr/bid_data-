# Pi3 HDFS 적재 통합 가이드

## 변경 사항

Pi4가 작동하지 않아 **Pi4의 역할(HDFS 적재)을 Pi3에 통합**했습니다.

## 새로운 Pi3 역할

### 기존 역할
- Kafka에서 파싱된 데이터 수신
- DB 저장 및 중복 처리
- 데이터 검증

### 추가된 역할 (Pi4에서 통합)
- CSV Export
- HDFS 적재
- 주기적 자동 적재

## 데이터 흐름

```
Pi1: 목록 크롤링 → Kafka
  ↓
Pi2: 상세 파싱 → Kafka
  ↓
Pi3: DB 저장 → CSV Export → HDFS 적재
```

## 사용 방법

### 1. 자동 HDFS 적재 (권장)

`run_db_consumer.py`를 실행하면 백그라운드 스레드가 주기적으로 HDFS에 데이터를 적재합니다.

```bash
python pi3/scripts/run_db_consumer.py
```

- 기본 적재 간격: 24시간
- 설정 파일에서 `hadoop.export_interval_hours`로 변경 가능
- 마지막 적재 이후의 신규 데이터만 적재

### 2. 수동 CSV Export

```bash
# 전체 데이터 export
python pi3/scripts/export_to_csv.py

# 최근 100개만 export
python pi3/scripts/export_to_csv.py --limit 100

# 특정 파일로 export
python pi3/scripts/export_to_csv.py --output data/export/my_export.csv
```

### 3. 수동 HDFS 적재

```bash
# 전체 데이터 HDFS 적재
python pi3/scripts/load_to_hdfs.py

# 최근 100개만 적재
python pi3/scripts/load_to_hdfs.py --limit 100

# 특정 날짜 이후 데이터만 적재
python pi3/scripts/load_to_hdfs.py --since 2025-01-01
```

## 설정

`config/config.yaml`에 Hadoop 설정 추가:

```yaml
hadoop:
  hdfs_namenode: "hdfs://localhost:9000"
  hdfs_path: "/recall_data"
  hdfs_command: "hdfs"  # 또는 "hadoop"
  export_interval_hours: 24  # 주기적 적재 간격 (시간)
```

## HDFS 명령이 없는 경우

HDFS 명령이 설치되어 있지 않아도 DB 저장은 정상 작동합니다.
HDFS 적재만 건너뛰고 경고 메시지를 출력합니다.

## 주의사항

1. **HDFS 적재는 선택사항**: HDFS가 없어도 DB 저장은 정상 작동
2. **주기적 적재**: 백그라운드 스레드로 실행되므로 메인 프로세스 종료 시 함께 종료됨
3. **CSV 파일**: `/tmp/` 디렉토리에 임시 생성 후 HDFS 적재 후 삭제

## 문제 해결

### HDFS 명령을 찾을 수 없음
- HDFS가 설치되어 있는지 확인
- `hdfs_command` 설정 확인
- PATH에 HDFS 명령이 있는지 확인

### HDFS 적재 실패
- HDFS 서버가 실행 중인지 확인
- 네트워크 연결 확인
- 권한 확인

### 주기적 적재가 작동하지 않음
- 로그 확인: `pi3/logs/db_consumer.log`
- 백그라운드 스레드가 실행 중인지 확인

