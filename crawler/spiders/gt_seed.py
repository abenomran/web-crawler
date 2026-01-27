import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
import re
from collections import Counter
import time
import csv


STOPWORDS = {
    "the","and","for","that","with","this","from","are","was","were","have","has",
    "will","been","they","their","about","into","more","also","than","when","where",
    "what","which","your","you","our","its","can","may","not","use","using"
}

DENY = (
        "/cas/login",
        "/login",
        "\\?service=",
        "mailto:",
        "tel:",
        "jupiter.cc.gatech.edu",
        "www-static.cc.gatech.edu",
        "konom.cc.gatech.edu",
        "saopaulo.cc.gatech.edu",
        "ftp.cc.gatech.edu",
        "www-int.cc.gatech.edu",
        "www2-int.cc.gatech.edu",
        "eclass.cc.gatech.edu",
        "c2000.cc.gatech.edu",
        "swiki.cc.gatech.edu",
        "guzdial.cc.gatech.edu",
        "claws.cc.gatech.edu",
        "ubicomp.cc.gatech.edu",
        "rs2023.cc.gatech.edu",
        "cc-sox.cc.gatech.edu",
        "staff-feedback.cc.gatech.edu",
        "grad.cc.gatech.edu",
        "repository.gatech.edu",
        "sso.gatech.edu",
        "ehsa.gatech.edu",
        "slash.gatech.edu",
        "gcatt.gatech.edu"
    )
DENY_EXTENSIONS = [
        "pdf", "doc", "docx", "ppt", "pptx", "xls", "xlsx",
        "zip", "rar", "7z", "jpg", "jpeg", "png", "gif", 
        "svg", "webp", "mp3", "mp4", "mov", "avi", "exe",
        "ps", "gz", "eps", "tar", "tgz", "mid", "class",
        "mpg", "mpeg", "tar", "ps", "z"
    ]


def extract_keywords_from_text(text, limit=10):
    words = re.findall(r"[a-zA-Z]{4,}", text.lower())
    words = [w for w in words if w not in STOPWORDS]
    return [w for w, _ in Counter(words).most_common(limit)]

class Page(scrapy.Item):
    title = scrapy.Field()
    url = scrapy.Field()
    keywords = scrapy.Field()   
    out_links = scrapy.Field()

class GTCCSpider(CrawlSpider):
    name = "gt_cc_crawler"
    start_urls = ["https://cc.gatech.edu"]

    allowed_domains = ["cc.gatech.edu"]
    # allowed_domains = ["gatech.edu"]
    

    """
    rules control which links the crawler follows:
    we keep normal HTML pages on the site and ignore login pages,
    dead sites, files (pdfs, images, etc.), and other non-page 
    links like email links (these cause problems with Scrapy parsing)

    some sites also fail to fetch robots.txt so I am avoiding those as well

    as a side note, by adding this I noticed a speed performance increase
    """
    rules = (
        Rule(
            LinkExtractor(
                allow="/",
                deny=DENY,
                deny_extensions=DENY_EXTENSIONS,
            ),
            callback="parse",
            follow=True
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # making adjustments to our spider class to enable time/stats tracking
        self.start_time = time.time()
        self.page_count = 0
        self.total_urls = 0
        self.total_keywords = 0
        self.discovered_urls = set()
        self.crawled_urls = set()

        # metrics sets
        self.encountered_urls_total = 0
        self.encountered_urls_unique = set()
        self.able_urls_unique = set() # passes rules
        self.crawled_urls_unique = set()

        self.metrics_extractor = LinkExtractor(
            allow="/",
            deny=DENY,
            deny_extensions=DENY_EXTENSIONS
        )

        # subsequently, I will be logging the following information in a csv file to use for plots later
        self.log_file = open("crawl_log.csv", "w", newline="", encoding="utf-8")
        self.logger_csv = csv.writer(self.log_file)
        self.logger_csv.writerow([
            "page_number",
            "elapsed_seconds",
            "elapsed_minutes",
            "total_urls_extracted",
            "total_keywords_extracted",
            "page_urls",
            "page_keywords",
            "urls_able_to_crawl",
            "urls_crawled",
            "urls_remaining",
            "encountered_urls_total",
            "encountered_urls_unique",
            "able_urls_unique",
            "crawled_urls_unique",
        ])

    # need to override this method so Scrapy properly saves the log file when it is done crawling
    def closed(self, reason):
        self.log_file.close()

    def parse(self, response):
        self.logger.info(f"Crawled: {response.url}")

        # update crawl frontier
        self.crawled_urls.add(response.url)
        self.discovered_urls.add(response.url)

        # get title
        title_node = response.css("title::text").get()
        title = title_node.strip() if title_node else ""

        description = response.css(
            'meta[name="description"]::attr(content)'
        ).get()

        if not description:
            description = response.css(
                'meta[property="og:description"]::attr(content)'
            ).get()

        if not description:
            description = response.css(
                'meta[name="twitter:description"]::attr(content)'
            ).get()

        description = description.strip() if description else ""

        # keywords
        text_nodes = response.css(
            "main ::text, article ::text, section ::text, p ::text, h1 ::text, h2 ::text"
        ).getall()

        text = " ".join(t.strip() for t in text_nodes)
        text = " ".join(text.split())

        keywords = extract_keywords_from_text(text)

        # outgoing links
        raw_links = response.css("a::attr(href)").getall()
        out_links = []

        for href in raw_links:
            if not href:
                continue

            absolute_url = response.urljoin(href)
            out_links.append(absolute_url)
            # update crawl frontier to add more urls
            self.discovered_urls.add(absolute_url)
            self.encountered_urls_total += 1
            self.encountered_urls_unique.add(absolute_url)
        
        # urls that pass rules
        able_links = self.metrics_extractor.extract_links(response)
        able_urls = {link.url for link in able_links}
        self.able_urls_unique.update(able_urls)


        # save data in page item
        page = Page()
        page['title'] = title
        page['url'] = response.url
        page['keywords'] = keywords
        page['out_links'] = out_links

        # time/stat tracking and logging
        self.page_count += 1
        page_urls = len(out_links)
        page_keywords = len(keywords)
        self.total_urls += page_urls
        self.total_keywords += page_keywords
        elapsed_seconds = time.time() - self.start_time
        elapsed_minutes = elapsed_seconds / 60.0
        urls_able_to_crawl = len(self.discovered_urls)
        urls_crawled = len(self.crawled_urls)
        urls_remaining = urls_able_to_crawl - urls_crawled
        encountered_total = self.encountered_urls_total
        encountered_unique = len(self.encountered_urls_unique)
        able_unique = len(self.able_urls_unique)
        crawled_unique = len(self.crawled_urls)

        self.logger_csv.writerow([
            self.page_count,
            round(elapsed_seconds, 2),
            round(elapsed_minutes, 4),
            self.total_urls,
            self.total_keywords,
            page_urls,
            page_keywords,
            urls_able_to_crawl,
            urls_crawled,
            urls_remaining,
            encountered_total,
            encountered_unique,
            able_unique,
            crawled_unique
        ])
        self.log_file.flush()

        # save this page in json
        yield page
