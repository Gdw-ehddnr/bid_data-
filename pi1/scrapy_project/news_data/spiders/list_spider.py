import scrapy
import re
from scrapy.http import FormRequest
from news_data.items import NewsUrlItem

class ListSpider(scrapy.Spider):
    name = 'list_spider'
    allowed_domains = ['car.go.kr']
    start_urls = ['https://www.car.go.kr/sd/newsDta/list.do']

    # 페이지네이션 설정
    max_pages = 118
    current_page = 1

    custom_settings = {
        'DOWNLOAD_DELAY': 1.0,
        'RANDOMIZE_DOWNLOAD_DELAY': 0.5,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'ROBOTSTXT_OBEY': False,
    }

    def parse(self, response):
        # 총 페이지 수 추출
        page_info = response.xpath('//p[@class="count-result"]/text()').get()
        if page_info:
            match = re.search(r'페이지\s+(\d+)/(\d+)', page_info)
            if match:
                total = int(match.group(2))
                if not hasattr(self, 'max_pages_updated'):
                    self.max_pages = total
                    self.max_pages_updated = True
                    self.logger.info(f"총 페이지 수: {self.max_pages}페이지")

        notice_items = response.xpath('//ul[@class="board-hrznt-list"]/li')

        if not notice_items:
            self.logger.warning("공지 항목을 찾을 수 없습니다.")
            self.logger.debug(f"Response URL: {response.url}")
            return

        self.logger.info(f"페이지 {self.current_page}: {len(notice_items)}개 공지 발견")

        for item in notice_items:
            try:
                # 제목
                title_elem = item.xpath('.//a/strong/text()').get()

                # notice_id: onclick에서 추출
                onclick_attr = item.xpath('.//a/@onclick').get()
                notice_id = None
                if onclick_attr:
                    match = re.search(r"detailView\('(\d+)'\)", onclick_attr)
                    if match:
                        notice_id = match.group(1)

                if not notice_id or not title_elem:
                    continue

                # 날짜 추출
                meta_items = item.xpath('.//ol/li/text()').getall()
                date = meta_items[1].strip() if len(meta_items) >= 2 else ''

                # 상세 페이지 URL
                detail_url = f"https://www.car.go.kr/sd/newsDta/detail.do"

                # 아이템 생성
                news_item = NewsUrlItem()
                news_item['contentsId'] = notice_id
                news_item['title'] = title_elem.strip()
                news_item['date'] = date
                news_item['url'] = detail_url

                yield news_item

            except Exception as e:
                self.logger.error(f"파싱 오류: {e}")
                continue

        # 다음 페이지 처리
        yield from self.follow_next_page(response)

    def follow_next_page(self, response):
        if self.current_page >= self.max_pages:
            return

        next_page_num = self.current_page + 1
        self.current_page = next_page_num

        yield FormRequest(
            url=self.start_urls[0],
            formdata={
                'divisionCode': '0401',
                'currentPageNo': str(next_page_num),
            },
            callback=self.parse,
            dont_filter=False
        )

