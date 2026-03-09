import scrapy
from datetime import datetime


class SinobookSpider(scrapy.Spider):
    name = 'sinobook'
    allowed_domains = ['sinobook.com.cn']
    start_url = 'https://www.sinobook.com.cn/b2c/scrp/bookjczd2.cfm'

    total_pages = 9661
    current_page = 1

    def start_requests(self):
        # 初始请求第一页
        yield scrapy.Request(self.start_url, callback=self.parse)

    def parse(self, response):
        # 1. 解析当前页数据
        # 根据你第一张截图，数据在 table.tblBrow 的 tr 中
        rows = response.css('table.tblBrow tr')

        for row in rows:
            # 排除表头行（包含 th 的行或第一行）
            if row.css('th') or not row.css('td'):
                continue

            tds = row.css('td')
            # 确保列数正确，避免抓到空行
            if len(tds) < 12:
                continue

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
                'page_num': self.current_page  # 传递给 Pipeline 判断
            }
            yield item

        # 2. 翻页逻辑
        if self.current_page < self.total_pages:
            self.current_page += 1
            # 构建 Payload 数据
            payload = {
                'sKeywords': '',
                'sFieldName': 'bname',
                'sTcid': '0',
                'sPno': '',
                'sFj': '0',
                'sSpecial': '0',
                'sYearsB': '',
                'sQuarter': '0',
                'sBrowType': 't',
                'iSortField': '2',
                'sSortOrder': 'asc',
                'sMdId': '',
                'iGoPage': '',
                'iPage': str(self.current_page)  # 关键翻页参数
            }

            yield scrapy.FormRequest(
                url=self.start_url,
                formdata=payload,
                callback=self.parse
            )