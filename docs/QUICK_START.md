# 빠른 시작 가이드

## 3대 라즈베리파이 구성 (Pi4 없이)

### Pi1: 목록 크롤러
```bash
cd pi1
python scripts/run_spider.py
```

### Pi2: 상세 파서
```bash
cd pi2
python scripts/run_consumer.py
```

### Pi3: DB 저장 + HDFS 적재
```bash
cd pi3
# DB 저장 및 자동 HDFS 적재
python scripts/run_db_consumer.py
```

## 수동 실행 (테스트용)

### CSV Export
```bash
cd pi3
python scripts/export_to_csv.py
```

### HDFS 적재
```bash
cd pi3
python scripts/load_to_hdfs.py
```

## 데이터 흐름

```
Pi1 (목록) → Kafka → Pi2 (상세) → Kafka → Pi3 (DB + HDFS)
```

## 설정

각 Pi에서:
```bash
cp config/config.pi1.yaml config/config.yaml  # Pi1
cp config/config.pi2.yaml config/config.yaml  # Pi2
cp config/config.pi3.yaml config/config.yaml  # Pi3
```

그리고 `config/config.yaml`에서 실제 IP 주소와 비밀번호를 수정하세요.

