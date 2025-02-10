from typing import Dict, List

# News Sources Configuration
NEWS_SOURCES: Dict[str, List[str]] = {
    'general': [
        'https://www.yahoo.com/news',  # #1 most popular
        'https://www.nbcnews.com',     # #5
        'https://www.cnn.com',         # #4
        'https://www.forbes.com',      # #7
        'https://www.nytimes.com',     # #8
        'https://www.reuters.com',     # #11
        'https://www.foxnews.com',     # #12
        'https://www.npr.org',         # #13
        'https://www.bloomberg.com',   # #14
        'https://www.today.com',       # #15
        'https://www.msn.com/news',    # #16
        'https://www.businessinsider.com', # #17
        'https://www.washingtonpost.com',  # #18
        'https://www.usnews.com',      # #19
        'https://www.buzzfeed.com/news' # #20
    ],
    'sports': [
        'https://www.espn.com',       # #6
        'https://www.nfl.com',         # #9
        'https://sports.yahoo.com',
        'https://www.cbssports.com',
        'https://www.nba.com/news',
        'https://www.mlb.com/news'
    ],
    'business': [
        'https://www.cnbc.com',       # #10
        'https://www.bloomberg.com/business',
        'https://www.forbes.com/business',
        'https://www.reuters.com/business',
        'https://www.businessinsider.com/finance'
    ],
    'technology': [
        'https://www.cnet.com/tech',
        'https://www.theverge.com',
        'https://www.wired.com',
        'https://techcrunch.com',
        'https://arstechnica.com'
    ],
    'entertainment': [
        'https://www.nbc.com/news',    # #2
        'https://www.cbs.com/news',    # #3
        'https://www.buzzfeed.com/entertainment',
        'https://www.today.com/entertainment'
    ],
    'science': [
        'https://www.sciencedaily.com',
        'https://www.livescience.com',
        'https://www.scientificamerican.com',
        'https://www.space.com',
        'https://www.nature.com/news'
    ]
}

# Scraping Configuration
CONCURRENT_REQUESTS = 5  # Number of concurrent requests
REQUEST_TIMEOUT = 30  # Timeout in seconds
MAX_RETRIES = 3  # Maximum number of retries per URL
MIN_DELAY = 2  # Minimum delay between requests to same domain
MAX_DELAY = 5  # Maximum delay between requests to same domain
ARTICLES_PER_PAGE = 30  # Maximum number of articles to extract per page
PAGES_PER_SOURCE = 3  # Number of pages to crawl per source

# Article Selectors
ARTICLE_SELECTORS = {
    'container': [
        'article',
        'div[class*="article"]',
        'div[class*="story"]',
        'div[class*="post"]',
        'div[class*="news"]',
        'div[class*="content"]',
        'section[class*="article"]',
        'li[class*="article"]'
    ],
    'title': [
        'h1',
        'h2',
        'h3',
        'a[class*="title"]',
        'a[class*="headline"]',
        '.title',
        '.headline'
    ],
    'content': [
        'div[class*="content"]',
        'div[class*="body"]',
        'div[class*="text"]',
        'article',
        '.content',
        '.body',
        '.text'
    ],
    'author': [
        'a[class*="author"]',
        'span[class*="author"]',
        'div[class*="author"]',
        '.author',
        '.byline'
    ],
    'date': [
        'time',
        'span[class*="date"]',
        'div[class*="date"]',
        'div[class*="time"]',
        '.date',
        '.time',
        '.published'
    ]
}

# Output Configuration
OUTPUT_FILE = 'news_articles.csv'
LOG_FILE = 'scraper.log'
ERROR_FILE = 'errors.log'

# Proxy Configuration
USE_PROXIES = True
PROXY_ROTATION_FREQUENCY = 10  # Rotate proxy every N requests

# Browser Headers
BROWSER_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Cache-Control': 'max-age=0'
}

# Site-specific Pagination Patterns
PAGINATION_PATTERNS = {
    'techcrunch.com': lambda page: f"/page/{page}",
    'marketwatch.com': lambda page: f"?page={page}",
    'yahoo.com': lambda page: f"?offset={(page-1)*30}",
    'sciencedaily.com': lambda page: f"/page/{page}",
    'livescience.com': lambda page: f"/page/{page}",
    'space.com': lambda page: f"/page/{page}"
}
