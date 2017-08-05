import scrapy
import json


class AldiSpider(scrapy.Spider):
    name = 'Aldi'
    base_domain = 'aldi.ie'
    allowed_domains = ['aldi.ie']
    start_urls = [
        "https://www.aldi.ie/api/productsearch/category/super-6"
    ]

    def parse(self, response):
        return json.loads(response.body)
