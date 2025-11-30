FROM python:3.11-slim

WORKDIR /app

# Python 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 프로젝트 파일 복사
COPY . .

# 실행 명령
CMD ["scrapy", "crawl", "list_spider"]

