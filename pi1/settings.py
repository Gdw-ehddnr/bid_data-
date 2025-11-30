"""
Scrapy 설정 파일
"""
BOT_NAME = 'recall_pipeline'

SPIDER_MODULES = ['pi1.spiders']
NEWSPIDER_MODULE = 'pi1.spiders'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# 다운로드 지연
DOWNLOAD_DELAY = 1
RANDOMIZE_DOWNLOAD_DELAY = True

# 동시 요청 수
CONCURRENT_REQUESTS = 1

# User-Agent
USER_AGENT = 'Mozilla/5.0 (compatible; RecallBot/1.0)'

# 로깅
LOG_LEVEL = 'INFO'

# HTTP 캐시 (선택사항)
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 3600

