import scrapy
from deals.settings import HTML_STORAGE
from deals.lib.file_storage import list_dir


class LidlSpider(scrapy.Spider):
    name = 'Lidl'
    base_domain = 'lidl.ie'

    allowed_domains = ['lidl.ie']
    # TODO: pull from mongo
    start_urls = [
        "https://www.lidl.ie/en/super-savers.htm?id=61&week=1",
        "https://www.lidl.ie/en/super-savers.htm?id=63&week=1",
        "https://www.lidl.ie/en/super-savers.htm?id=62&week=1"
    ]
    replay = False

    def __init__(self, *args, **kwargs):
        super(LidlSpider, self).__init__(*args, **kwargs)
        replay = kwargs.get('replay')
        date = kwargs.get("date")
        if replay and date:
            self.logger.info("Replaying old scrap {}".format(date))
            file_path = "{}/{}/{}".format(
                HTML_STORAGE.get('PATH'),
                self.name,
                date
            )
            self.start_urls = [
                "file://{}/{}".format(file_path, f)
                for f in list_dir(file_path)
            ]
            self.replay = replay

    # TODO: pull xpath from a db
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
                "name": item.xpath("@data-name").extract_first(),
                "alt_was_price": item.xpath(
                    ".//div/a/span[2]/span/span[1]/span[1]/text()"
                ).extract_first(),
                "old_price": item.css(
                    ".pricefield__old-price"
                ).xpath("text()").extract_first() if item.css(
                    ".pricefield__old-price"
                ).extract_first() else None,
                "price_per_unit": item.xpath(
                    ".//div/a/span[2]/span/span[2]/text()").extract_first(),
                "promo": item.xpath("@data-list").extract_first()
            })
        return products
