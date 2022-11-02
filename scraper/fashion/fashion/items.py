# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

class UnimodaItem(scrapy.Item):
    id = scrapy.Field()
    category = scrapy.Field()
    subcategory = scrapy.Field()
    description = scrapy.Field()
    link = scrapy.Field()
    price = scrapy.Field()
    sizes = scrapy.Field()
    brand = scrapy.Field()
    condition = scrapy.Field()
    image_urls = scrapy.Field()
    images = scrapy.Field()
