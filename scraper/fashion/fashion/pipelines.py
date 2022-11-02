# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


import os
from scrapy import Request
from scrapy.pipelines.images import ImagesPipeline
# from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem

class UnimodaPipeline(ImagesPipeline):

    def get_media_requests(self, item, info):
        return Request(
            item["image_urls"],
            meta = {
                "img_name": f"{item.get('id')}",
            }
        )

    def file_path(self, request, response=None, info=None, item=None) -> str:
        return os.path.join(info.spider.name, item["category"], item["subcategory"], f"{request.meta['img_name']}.jpg")

    # def item_completed(self, results, item, info):
    #     file_paths = [x['path'] for ok, x in results if ok]
    #     if not file_paths:
    #         raise DropItem("Item contains no files")
    #     adapter = ItemAdapter(item)
    #     adapter['file_paths'] = file_paths
    #     return item



class DuplicatesPipeline(object):

    def __init__(self):
        self.ids_seen = set()

    def process_item(self, item, spider):
        if item['id'] in self.ids_seen:
            raise DropItem("Duplicate item found: %s" % item)
        else:
            self.ids_seen.add(item['id'])
            return item