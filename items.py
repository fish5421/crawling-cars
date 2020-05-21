# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class TeslaPriceItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    year = scrapy.Field()
    model = scrapy.Field()
    configuration = scrapy.Field()
    notes_from_seller = scrapy.Field()
    int_color = scrapy.Field()
    ext_color = scrapy.Field()
    deal = scrapy.Field()
    mileage = scrapy.Field()
    sold_by = scrapy.Field()
    location = scrapy.Field()
    rating = scrapy.Field()
    number_of_reviews = scrapy.Field()
    good_deal_margin = scrapy.Field()
    vin = scrapy.Field()
    hot_car = scrapy.Field()
    price = scrapy.Field()
    original_price = scrapy.Field()
    drive_train = scrapy.Field()
    autopilot = scrapy.Field()
    url = scrapy.Field()


    
