# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

"""
Big Refactoring needed but it works for now.
"""

import re
from decimal import Decimal
from datetime import datetime
from pymongo import MongoClient
from dateparser import parse
from lxml import etree, html


class BasePipline(object):

    collection_name = 'offers'
    pipline_name = None
    mongo_map = [
        "product_code",
        "picture",
        "description",
        "price",
        "date_to",
        "was_price",
        "alt_was_price",
        "product_url",
        "date_from",
        "price_per_unit",
        "name",
        "promo",
        "promo_year"
    ]

    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DATABASE', 'items')
        )

    def open_spider(self, spider):
        self.client = MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]

    def close_spider(self, spider):
        self.client.close()

    def scrub_dict(self, dict_item):
        return {
            k: self.scrub_whitelines(v)
            for k, v in dict_item.items()
        }

    def scrub_whitelines(self, value):
        if isinstance(value, (str, unicode)):
            value.strip()
            for line in ('\n', '\t'):
                value = value.replace(line, '')

            value = " ".join(value.split())
        return value

    def none_to_string(self, value):
        return '' if value is None else str(value)

    def decimal_to_float(self, value):
        return float(value) if isinstance(value, Decimal) else value

    def str_to_float(self, value):
        try:
            return float(value)
        except Exception:
            return value

    def set_date_to_max(self, value):
        if isinstance(value, datetime):
            value = datetime.combine(value.date(), value.time().max)
        return value

    def set_date_to_min(self, value):
        if isinstance(value, datetime):
            value = datetime.combine(value.date(), value.time().min)
        return value


class AldiPipeline(BasePipline):

    pipline_name = "Aldi"

    def process_item(self, items, spider):

        if spider.name != self.pipline_name:
            return items

        for item in items.get('results'):
            item = self.scrub_dict(item)
            date_from, date_to = self.insert_dates(item.get('description'))
            item['date_from'] = date_from
            item['date_to'] = date_to
            item['product_code'] = "{}-{}".format(
                self.pipline_name, item.pop('code')
            )
            item['promo_year'] = datetime.now().date().year
            item['product_url'] = spider.base_domain + item.pop('productUrl')
            item['price_per_unit'] = item.pop('pricePerUnit')
            item['alt_was_price'] = item.get('wasPrice')
            item['was_price'] = self.str_to_float(
                item.pop('wasPrice').replace(u"€", ''))
            item['price'] = self.str_to_float(item['price'].replace(u"€", ''))
            item['picture'] = self.lazy_load_img(item['picture'])
            item['promo'] = "super-6"
            offer = {info: item.get(info) or None for info in self.mongo_map}
            offer.update({
                "updated": datetime.now(),
                "retailer": self.pipline_name
            })

            self.db[self.collection_name].update(
                {
                    "product_code": offer['product_code'],
                    "description": offer['description'],
                    "promo_year": offer['promo_year']
                },
                offer,
                True
            )
        return items

    def lazy_load_img(self, img):
        image = html.fromstring(img)
        image.attrib['class'] = "{} lazyload".format(
            image.attrib.pop('class'))
        sources = image.xpath("//source")
        for source in sources:
            source.attrib['data-srcset'] = source.attrib.pop("srcset")
        return etree.tostring(image)

    # TODO: make this better
    def insert_dates(self, desc):
        date_from = None
        date_to = None
        if desc:
            search = re.search(r'(\s-\s|\sto\s)', desc, re.I)
            if search and search.group(0):
                date_range = desc.split(search.group(0))
                if len(date_range) == 2:
                    dates = [
                        re.search(r'(\d+\w\w\s\w+)', d_r, re.I).group(0)
                        for d_r in date_range
                    ]
                    date_from, date_to = [parse(d) for d in dates]

        return self.set_date_to_min(date_from), self.set_date_to_max(date_to)


class LidlPipeline(BasePipline):

    pipline_name = 'Lidl'

    def process_item(self, items, spider):
        if spider.name != self.pipline_name:
            return items

        for item in items.get('results'):
            item = self.scrub_dict(item)
            item['was_price'] = self.string_to_decimal(
                item['alt_was_price'])

            item['promo_year'] = datetime.now().date().year
            date_from, date_to = self.insert_dates(item.get('description'))
            item['date_from'] = date_from
            if not date_to:
                date_to = self.set_date_to_max(datetime.now())
            item['date_to'] = date_to
            item['price'] = self.str_to_float(item['price'])
            item['product_url'] = "{}{}".format(
                spider.base_domain, item.pop('product_url'))
            item['product_code'] = "{}-{}".format(
                self.pipline_name, item['product_code'])

            offer = {info: item.get(info) or None for info in self.mongo_map}
            offer.update({
                "updated": datetime.now(),
                "retailer": self.pipline_name
            })

            self.db[self.collection_name].update(
                {
                    "product_code": offer['product_code'],
                    "description": offer['description'],
                    "promo_year": offer['promo_year']
                },
                offer,
                upsert=True
            )

        return items

    def string_to_decimal(self, price):
        was_price = None
        if price:
            was_price = (
                re.search(r"Was\s.?(\d+\.\d*)", price, re.I) or
                re.search(r"Was\s(\d+c)", price, re.I) or
                re.search(ur"Was\s€(\d+)", price, re.I)
            )

            if was_price:
                try:
                    was_price = Decimal(was_price.group(1))

                except Exception:
                    # cents e.g 90c
                    was_price = re.search(r"Was\s(\d+)c", price, re.I)
                    if was_price:
                        was_price = "0.{}".format(was_price.group(1))
                        was_price = Decimal(was_price)

        return self.decimal_to_float(was_price)

    # TODO: make this better
    def insert_dates(self, desc):
        date_from = None
        date_to = None

        if desc:
            date_range = desc.split(' - ')
            # 22.08.
            dates = [
                re.search(r'(\d\d\.\d\d\.)', d_r, re.I).group(0)
                for d_r in date_range
            ]
            if dates:
                dates = [
                    # 22.08.2017
                    parse(
                        "{}{}".format(date, datetime.now().year),
                        settings={'DATE_ORDER': 'DMY'}
                    )
                    for date in dates
                ]
            if len(dates) == 2:
                date_from, date_to = dates
            elif len(dates) == 1:
                date_from = dates.pop()
        return self.set_date_to_min(date_from), self.set_date_to_max(date_to)
