# 아키텍처 변경 사항

## 변경 이유

Pi4가 작동하지 않아 **Pi4의 역할(HDFS 적재)을 Pi3에 통합**했습니다.

## 변경 전 아키텍처

```
Pi1 → Kafka → Pi2 → Kafka → Pi3 → DB
                                    ↓
                                  Kafka → Pi4 → HDFS
```

## 변경 후 아키텍처

```
Pi1 → Kafka → Pi2 → Kafka → Pi3 → DB → CSV → HDFS
```

## 역할 변경

### Pi3 (변경 후)
- ✅ DB 저장 (기존)
- ✅ CSV Export (기존)
- ✅ **HDFS 적재 (Pi4에서 통합)** ← 새로 추가

### Pi4 (선택적)
- HDFS 분석만 수행 (HDFS 적재는 Pi3에서 처리)
- 또는 사용하지 않음

## 데이터 흐름

1. **Pi1**: 목록 크롤링 → Kafka (`recall-new-urls`)
2. **Pi2**: 상세 파싱 → Kafka (`recall-parsed`)
3. **Pi3**: 
   - Kafka에서 데이터 수신
   - DB 저장
   - 주기적으로 CSV Export 및 HDFS 적재

## 장점

1. **단순화**: Pi4 없이도 전체 파이프라인 작동
2. **효율성**: DB 저장과 HDFS 적재를 같은 서버에서 처리
3. **유연성**: HDFS가 없어도 DB 저장은 정상 작동

## 설정 변경

`config/config.yaml`에 Hadoop 설정 추가:

```yaml
hadoop:
  hdfs_namenode: "hdfs://localhost:9000"
  hdfs_path: "/recall_data"
  hdfs_command: "hdfs"
  export_interval_hours: 24
```

## 실행 방법

### 자동 HDFS 적재 (권장)
```bash
# DB 저장과 함께 자동으로 주기적 HDFS 적재
python pi3/scripts/run_db_consumer.py
```

### 수동 HDFS 적재
```bash
# 수동으로 HDFS 적재
python pi3/scripts/load_to_hdfs.py
```

## 참고

- HDFS가 설치되어 있지 않아도 DB 저장은 정상 작동합니다
- HDFS 적재는 선택적 기능입니다
- 주기적 적재는 백그라운드 스레드로 실행됩니다

