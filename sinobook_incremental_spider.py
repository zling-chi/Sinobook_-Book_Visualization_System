import scrapy
from datetime import datetime

class SinobookIncrSpider(scrapy.Spider):
    name = 'sinobook_incr'
    start_url = 'https://www.sinobook.com.cn/b2c/scrp/bookjczd2.cfm'
    # 增量爬取设定：只爬取前 10 页
    max_incr_pages = 5
    current_page = 1

    def start_requests(self):
        yield scrapy.Request(self.start_url, callback=self.parse)

    def parse(self, response):
        rows = response.css('table.tblBrow tr')
        for row in rows:
            if row.css('th') or len(row.css('td')) < 12:
                continue

            tds = row.css('td')
            item = {
                'link': response.urljoin(tds[1].css('a::attr(href)').get('')),
                'name': tds[1].css('a::text').get('').strip(),
                'author' :tds[2].css('::text').get('').strip(),
                'publisher': tds[3].css('a::text').get('').strip(),
                'ISBN': tds[4].css('::text').get('').strip(),
                'grade_level': tds[5].css('::text').get('').strip(),
                'applicable_major': tds[6].css('::text').get('').strip(),
                'order_number': tds[7].css('::text').get('').strip(),
                'price': tds[8].css('::text').get('').strip(),
                'year' :tds[9].css('::text').get('').strip(),
                'quarter' :tds[10].css('::text').get('').strip(),
                'category' :tds[11].css('::text').get('').strip(),
                'cellection_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'page_num': self.current_page
            }
            yield item

        # 翻页逻辑：达到设定页数即停止
        if self.current_page < self.max_incr_pages:
            self.current_page += 1
            payload = {
                'sKeywords': '', 'sFieldName': 'bname', 'sTcid': '0', 'sPno': '',
                'sFj': '0', 'sSpecial': '0', 'sYearsB': '', 'sQuarter': '0',
                'sBrowType': 't', 'iSortField': '2', 'sSortOrder': 'asc',
                'sMdId': '', 'iGoPage': '', 'iPage': str(self.current_page)
            }
            yield scrapy.FormRequest(self.start_url, formdata=payload, callback=self.parse)