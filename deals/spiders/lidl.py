import scrapy


class LidlSpider(scrapy.Spider):
    name = 'Lidl'
    base_domain = 'lidl.ie'

    allowed_domains = ['lidl.ie']
    start_urls = [
        "https://www.lidl.ie/en/super-savers.htm?id=61&week=1",
        "https://www.lidl.ie/en/super-savers.htm?id=63&week=1",
        "https://www.lidl.ie/en/super-savers.htm?id=62&week=1"
    ]
    # TODO: pull xpath from mongo
    def parse(self, response):
        items = response.xpath('//ul[@class="productgrid__list"]/li')
        products = {"results": []}
        for item in items:
            products['results'].append({
                "product_url": item.xpath(".//div/a/@href").extract_first(),
                "picture": item.xpath(".//div/a/div/div/img").extract_first(),
                "description": item.xpath(
                    ".//div/div/ul/li/div/text()").extract_first(),
                "price": item.xpath("@data-price").extract_first(),
                "product_code": item.xpath("@data-id").extract_first(),
                "name": item.xpath(
                    ".//div/a/span[1]/h2/text()").extract_first(),
                "alt_was_price": item.xpath(
                    ".//div/a/span[2]/span/span[1]/span[1]/text()"
                ).extract_first(),
                "price_per_unit": item.xpath(
                    ".//div/a/span[2]/span/span[2]/text()").extract_first(),
                "promo": item.xpath("@data-list").extract_first()
            })
        return products
