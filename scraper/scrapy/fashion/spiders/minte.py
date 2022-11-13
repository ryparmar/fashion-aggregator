import scrapy
from typing import List
from fashion.items import MinteItem
from scrapy import Request


class MinteSpider(scrapy.Spider):
    name = "minte"
    valid_categories = ("damske-obleceni",)
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:98.0) Gecko/20100101 Firefox/98.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
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
        super(MinteSpider, self).__init__(*args, **kwargs)

        # Validate given arguments
        if category not in self.valid_categories:
            raise ValueError(
                f"Given invalid argument for category - {category}.",
                f"Expected argument is one of the: {self.valid_categories}",
            )
        if not isinstance(starting_page, int):
            raise ValueError(f"Unexpected data type for starting_page {type(starting_page)}. Use integer.")

        if category:
            self.start_urls = [f"https://www.minte.cz/damske-obleceni/strana-{starting_page}/"]
        else:
            self.start_urls = [f"https://www.minte.cz/damske-obleceni/strana-{starting_page}/"]

    def _get_last_page_num(self, nums: List[str]) -> int:
        for num in nums[::-1]:
            if num.isnumeric():
                return int(num)

    def start_requests(self):
        for url in self.url_list:
            return Request(url=url, callback=self.parse, headers=self.HEADERS)

    def parse_item(self, response) -> MinteItem:
        """Function that parses each item separatedly

        Benefit: if there is data missing, I can map it to the exact item!
        """
        item = MinteItem()
        item["id"] = response.css("div.product[id]::attr(id)").get().replace("product-", "")
        # item["description"] = response.css('a.cat-product-name::text').get()
        # item["link"] = response.css('a.cat-product-name::attr(href)').get()
        # item["category"] = item["link"].replace("https://unimoda.cz/", "").split("/")[0]
        # item["subcategory"] = item["link"].replace("https://unimoda.cz/", "").split("/")[1]
        # item["price"] = response.css('span.small-current-price::text').get()
        # item["sizes"] = " ".join(response.css('span.size-attribute').css('span::text').getall()).replace(" | ", " ").split()
        # item["brand"] = response.css('div.name').css('a::text').get()
        # item["condition"] = " ".join([cond.strip() for cond in response.css('div.name').css('span::text').getall()])
        # item["image_urls"] = response.css('div.image').css('img::attr(src)').extract_first()
        return item

    def parse(self, response):
        """Main crawler function

        Iterate all the items in the given category and then crawl to next page.
        """
        curr_page_num = int(response.url.split("page=")[-1])
        self.logger.info(f"Parsing page {curr_page_num} from {response.url}")
        number_of_pages = self._get_last_page_num(response.css("div.links").css("a::text").getall())  # 3
        if not isinstance(number_of_pages, int):
            raise ValueError("Wrongly scraped pagination!")
        self.logger.info(f"Last page is {number_of_pages}")

        # Parse items on the page
        for item in response.css("div.product"):
            yield self.parse_item(item)

        # Go to next page
        next_page_num = curr_page_num + 1
        self.logger.info(f"Parsed page {curr_page_num}/{number_of_pages}")
        if next_page_num < number_of_pages:
            next_page_url = response.url.replace(
                f"page={curr_page_num}", f"page={next_page_num}"
            )  # f'{"".join(response.url.split("page=")[:-1])}page={next_page_num+1}'
            self.logger.info(f"URL of next page {next_page_url}")
            yield scrapy.Request(response.urljoin(next_page_url), self.parse)
