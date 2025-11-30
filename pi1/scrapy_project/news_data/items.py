import scrapy

class NewsUrlItem(scrapy.Item):
    contentsId = scrapy.Field() # 공지 ID (POST 요청 시 사용할 키값)
    title = scrapy.Field()      # 공지 제목
    date = scrapy.Field()       # 공지 날짜
    url = scrapy.Field()        # 상세 페이지 URL (detail.do)