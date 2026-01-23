import scrapy


class GtSeedSpider(scrapy.Spider):
    name = "gt_seed"
    allowed_domains = ["cc.gatech.edu"]
    start_urls = ["https://cc.gatech.edu"]

    def parse(self, response):
        pass
