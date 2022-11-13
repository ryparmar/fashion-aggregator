import scrapy
import urllib.parse
from typing import List
from fashion.items import VintedItem
from scrapy.http import Request

class VintedSpider(scrapy.Spider):
    name = "vinted"
    home_url = "https://www.vinted.cz"
    valid_categories = (
        "zeny",
        # "muzi"
    )
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:98.0) Gecko/20100101 Firefox/98.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en,cs;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }

    def __init__(self, category: str = None, starting_page: int = 1, *args, **kwargs):
        super(VintedSpider, self).__init__(*args, **kwargs)

        # Validate given arguments
        if category and category not in self.valid_categories:
            raise ValueError(
                f"Given invalid argument for category - {category}.", 
                f"Expected argument is one of the: {self.valid_categories}"
            )
        if not isinstance(starting_page, int):
            raise ValueError(
                f"Unexpected data type for starting_page {type(starting_page)}. Use integer.")

        if category:
            self.url_list = [
                f'https://www.vinted.cz/vetements?catalog[]=4&page={starting_page}',
            ]
        else:
            self.url_list = [
                f'https://www.vinted.cz/vetements?catalog[]=4&page={starting_page}',
            ]

    # def _get_last_page_num(self, nums: List[str]) -> int:
    #     for num in nums[::-1]:
    #         if num.rstrip("/").isnumeric():
    #             return int(num.rstrip("/"))

    def start_requests(self):
        for url in self.url_list:
            self.logger.info(f"Requesting {url}")
            yield Request(url=url, callback=self.parse, headers=self.HEADERS)

    def parse_item(self, response) -> VintedItem:
        """Function that parses each item separatedly

        Benefit: if there is data missing, I can map it to the exact item!
        """
        item = VintedItem()
        item["id"] = response.css('div.name::text').get()  #.css('div.product[id]::attr(id)').get().replace("product-", "")
        item["description"] = response.css('div.u-text-wrap').css('span::text').get()
        item["link"] = response.url
        # item["category"] = item["link"].replace("https://unimoda.cz/", "").split("/")[0]
        # item["subcategory"] = item["link"].replace("https://unimoda.cz/", "").split("/")[1]
        # item["price"] = response.css('div.prices').css('div.price price-final').get()
        # item["sizes"] = " ".join(response.css('span.size-attribute').css('span::text').getall()).replace(" | ", " ").split()
        # item["brand"] = response.css('div.name').css('a::text').get()
        # item["condition"] = " ".join([cond.strip() for cond in response.css('div.name').css('span::text').getall()])
        item["image_urls"] = response.css('div.item-photos').css('img').extract_first()
        return item

    def parse(self, response):
        """Main crawler function
        
        Iterate all the items in the given category and then crawl to next page.
        """
        # curr_page_num = int(response.url.split("strana-")[-1].rstrip("/"))
        # self.logger.info(f"Parsing page {curr_page_num} from {response.url}")
        # number_of_pages = self._get_last_page_num(response.css('div.pagination').css('a::text').getall())  # 3
        # if not isinstance(number_of_pages, int):
        #     raise ValueError("Wrongly scraped pagination!")
        # self.logger.info(f"Last page is {number_of_pages}")

        # Parse items on the page
        self.logger.info(f"{response.css('img').getall()}")
        for item in response.css('div.feed-grid__item'):
            item_url = urllib.parse.urljoin(self.home_url, item.css('a::attr(href)').get())
            self.logger.info(f"Item url: {item_url}")
            yield Request(url=item_url, callback=self.parse_item, headers=self.HEADERS)
        
        # Go to next page
        # next_page_num = curr_page_num + 1
        # self.logger.info(f"Parsed page {curr_page_num}/{number_of_pages}")
        # if next_page_num < number_of_pages:
        #     next_page_url = response.url.replace(f"strana-{curr_page_num}", f"strana-{next_page_num}")  #f'{"".join(response.url.split("page=")[:-1])}page={next_page_num+1}'
        #     self.logger.info(f"URL of next page {next_page_url}")
        #     yield scrapy.Request(response.urljoin(next_page_url), self.parse)