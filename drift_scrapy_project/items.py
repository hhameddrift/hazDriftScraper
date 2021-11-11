# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class DriftScrapyProjectItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

class DriftAccountList(scrapy.Item):
    driftAccountList = scrapy.Field()

class DriftAccountUserList(scrapy.Item):
    driftAccountUserListJSON = scrapy.Field()

class DriftUserActivity(scrapy.Item):
    driftUserActivityJSON = scrapy.Field()

class DriftRawVisitorActivity(scrapy.Item):
    driftRawVisitorJSON = scrapy.Field()
