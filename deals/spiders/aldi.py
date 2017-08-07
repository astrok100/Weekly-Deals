import scrapy
import json
from deals.settings import HTML_STORAGE
from deals.lib.file_storage import list_dir


class AldiSpider(scrapy.Spider):
    name = 'Aldi'
    base_domain = 'aldi.ie'
    allowed_domains = ['aldi.ie']
    # TODO: pull from mongo
    start_urls = [
        "https://www.aldi.ie/api/productsearch/category/super-6"
    ]
    replay = False

    def __init__(self, *args, **kwargs):
        super(AldiSpider, self).__init__(*args, **kwargs)
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

    def parse(self, response):
        return json.loads(response.body)
