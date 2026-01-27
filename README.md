# Web Crawler

This project implements a web crawler using Scrapy to crawl pages from the Georgia Tech College of Computing website (`cc.gatech.edu`) or general Georgia Tech website (`gatech.edu`).  
The crawler extracts page metadata, keywords, outgoing links, and crawl statistics, which are then analyzed and visualized using a Jupyter notebook.

---

## Project Overview

The crawler:
- Starts from seed URL (`https://cc.gatech.edu`)
- Follows links within the allowed domain
- Filters out non-parsable content (PDFs, images, videos, executables, etc.) for our purposes
- Extracts keywords from page text
- Logs crawl statistics over time for performance analysis

The project also includes a Jupyter notebook that:
- Plots crawl speed vs time
- Plots pages crawled, URLs discovered, and keywords extracted
- Estimates time required to crawl 10 million and 1 billion pages

---

## Requirements

### Python Version
- Tested with Python 3.11

### Python Packages
It's recommended to create a virtual environment, from there install dependencies:

```bash
pip install -r requirements.txt
```

This installs all packages required to run the crawler and the analysis notebook.

## Running


From the project root, run:

```bash
scrapy crawl gt_cc_crawler -s CLOSESPIDER_PAGECOUNT=1500
```

You may adjust the `CLOSESPIDER_PAGECOUNT` argument to the max number of pages you wish to crawl.

Sometimes Scrapy will automatically end the session when it hits this limit, other times it remains hanging in the terminal. You can `Ctrl+C` to force an exit. 

Please note that if you perform multiple runs, it will overwrite the `crawl_log.csv` and `web_archive.json` of the previous run you perform. I suggest renaming those files if you want to keep them. You may edit the path in the plotting notebook to run plots on different data.

## Data Storage Design

The crawler stores its output in two main components:

1. A **crawl statistics log** (`crawl_log.csv`)
2. A **web archive** of crawled pages (JSON output) (`web_archive.json`)

I separate the two to allow analysis of crawl performance to be separate from analysis of page content.

---

### Crawl Statistics (`crawl_log.csv`)

The file `crawl_log.csv` stores time-series statistics collected during the crawl.  
Each row corresponds to the crawler’s state after processing a single page.

#### Stored Fields

| Column | Description |
|------|------------|
| page_number | Total number of pages crawled so far |
| elapsed_seconds | Elapsed crawl time in seconds |
| elapsed_minutes | Elapsed crawl time in minutes |
| total_urls_extracted | Total URLs extracted across all pages |
| total_keywords_extracted | Total keywords extracted across all pages |
| page_urls | Number of URLs extracted from the current page |
| page_keywords | Number of keywords extracted from the current page |
| urls_able_to_crawl | URLs remaining in the crawl frontier |
| urls_crawled | URLs successfully crawled so far |
| urls_remaining | Difference between discovered and crawled URLs |
| encountered_urls_total | Total URLs encountered (including duplicates) |
| encountered_urls_unique | Unique URLs encountered |
| able_urls_unique | Unique URLs allowed by crawler rules |
| crawled_urls_unique | Unique URLs actually crawled |

This file is primarily used for:
- Measuring crawl speed
- Tracking URL discovery vs crawling
- Producing plots and extrapolations

You may reference `crawler_plots.ipynb` to create plots on the data.

---

### Web Archive (Crawled Pages)

Crawled web pages are stored as structured JSON records, forming a simple web archive.

Each page is stored independently and contains:
- Page title
- Page URL
- Extracted keywords (topics/subjects)
- Outgoing links

#### Page Record Structure

```json
{
  "title": "College of Computing",
  "url": "https://cc.gatech.edu",
  "keywords": ["research", "programs", "computing", "world", "education", "college", "curriculum", "undergraduate", "program"],
  "out_links": [
    "https://cc.gatech.edu/research",
    "https://cc.gatech.edu/academics",
    ..., 
    "https://www.cc.gatech.edu/cas"
  ]
}
```
*Note: shortened out_links for brevity with ...*