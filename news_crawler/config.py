from typing import Dict, List, Any

# Crawler Configuration
CRAWLER_CONFIG: Dict[str, Any] = {
    # Timing and Intervals
    'default_interval_minutes': 30,      # Time between crawl cycles
    'domain_timeout_minutes': 60,        # Time before recrawling same domain
    'error_backoff_multiplier': 2,       # Multiply timeout by this for each error
    'max_backoff_minutes': 240,          # Maximum backoff time for problematic domains
    
    # Article Limits
    'min_title_words': 3,               # Minimum words in article title
    'articles_per_source': 100,          # Articles to get per source (reduced to get fresher content)
    'sites_per_category': 50,            # Sites to crawl per category (increased coverage)
    
    # Retry Logic
    'max_retries': 3,                   # Maximum retry attempts per request
    'retry_delay_seconds': 60,           # Delay between retries
    'max_errors_per_domain': 5,          # Max errors before longer backoff
    
    # Cache Settings
    'cache_db_path': 'cache/article_cache.db',  # SQLite cache location
    'cache_cleanup_days': 30,            # Remove entries older than this
    
    # Concurrency Settings
    'max_concurrent_requests': 10,       # Concurrent requests (up from 5)
    'max_concurrent_domains': 3,         # Max concurrent requests per domain
    'request_timeout_seconds': 30        # Timeout for each request
}

# File Configuration
FILE_CONFIG: Dict[str, str] = {
    'csv_file': 'articles_simple_latest.csv',
    'log_dir': 'output',
    'csv_delimiter': '|',
    'cache_dir': 'cache',
    'error_log': 'output/crawler_errors.log',
    'stats_file': 'output/crawler_stats.json'
}

# News Sources Configuration
NEWS_SOURCES: Dict[str, List[str]] = {
    'general': [
        # Major News Sites
        'https://www.nytimes.com',         # #1 news site
        'https://www.cnn.com',             # #2
        'https://www.bbc.com/news',        # #3
        'https://www.reuters.com',         # #4
        'https://apnews.com',              # #5 Associated Press
        'https://www.nbcnews.com',         # #6
        'https://abcnews.go.com',          # #7
        'https://www.cbsnews.com',         # #8
        'https://www.washingtonpost.com',  # #9
        'https://www.foxnews.com',         # #10
        'https://www.npr.org',             # #11
        'https://www.yahoo.com/news',      # #12
        'https://www.msn.com/news',        # #13
        'https://www.usnews.com',          # #14
        'https://www.theatlantic.com',     # #15
        'https://www.nationalreview.com',  # #16
        'https://fivethirtyeight.com',     # #17
        'https://www.vice.com/en/section/news',  # #18
        'https://theintercept.com',        # #19
        'https://medium.com/tag/news',     # #20
    ],
    'sports': [
        # Major Sports Sites
        'https://www.espn.com',           
        'https://www.cbssports.com',      
        'https://bleacherreport.com',     
        'https://www.si.com',             
        'https://www.theathletic.com',    
        'https://www.skysports.com',      
        'https://www.nbcsports.com',      
        'https://www.foxsports.com',      
        'https://www.sbnation.com',       
        'https://sports.yahoo.com',       
        'https://www.nba.com/news',       
        'https://www.nfl.com',            
        'https://www.mlb.com/news',       
        'https://www.goal.com'            
    ],
    'business': [
        # Major Financial News
        'https://www.bloomberg.com',                
        'https://www.cnbc.com',                     
        'https://www.reuters.com/business',         
        'https://www.forbes.com',                   
        'https://www.businessinsider.com',          
        'https://www.ft.com',                       
        'https://www.wsj.com',                      
        'https://www.economist.com',                
        'https://www.marketwatch.com',              
        'https://www.investopedia.com',             
        
        # Investment News
        'https://seekingalpha.com/market-news',
        'https://www.marketwatch.com/',
        'https://www.investing.com/news/',
        'https://finance.yahoo.com/',
        'https://www.barrons.com/topics/markets',
        
        # Business News
        'https://www.businessinsider.com/markets',
        'https://fortune.com/section/finance/',
        'https://www.economist.com/finance-and-economics',
        'https://hbr.org/topic/finance',
        'https://www.forbes.com/money-and-markets/',
        
        # Tech Business
        'https://siliconangle.com/category/cloud/',
        'https://www.geekwire.com/tag/artificial-intelligence/',
        'https://www.fastcompany.com/technology',
        'https://www.businessinsider.com/tech',
        'https://www.axios.com/technology',
        
        # Crypto & Fintech
        'https://www.coindesk.com/',
        'https://cointelegraph.com/',
        'https://decrypt.co/news',
        'https://www.theblockcrypto.com/',
        'https://www.pymnts.com/news/',
        
        # Economic News
        'https://www.project-syndicate.org/economics',
        'https://www.brookings.edu/topics/economics/',
        'https://voxeu.org/',
        'https://www.worldbank.org/en/news',
        'https://www.imf.org/en/news'
    ],
    'technology': [
        # Major Tech News Sites
        'https://www.theverge.com/tech',           
        'https://techcrunch.com',                  
        'https://www.wired.com',                   
        'https://www.cnet.com/tech/',              
        'https://www.gizmodo.com',                 
        'https://arstechnica.com',                 
        'https://www.engadget.com/tech/',          
        'https://www.zdnet.com',                   
        'https://news.ycombinator.com',            
        'https://www.technologyreview.com',        
        
        # Tech Industry News
        'https://www.computerworld.com/category/emerging-technology/',
        'https://www.infoworld.com/category/artificial-intelligence/',
        'https://www.technewsworld.com/section/tech-blog',
        'https://www.tomshardware.com/news',
        'https://www.anandtech.com/show/news',
        
        # AI/ML Focused
        'https://www.artificialintelligence-news.com/',
        'https://www.unite.ai/news/',
        'https://www.datanami.com/category/machine-learning/',
        'https://www.kdnuggets.com/news/',
        'https://www.analyticsinsight.net/category/latest-news/',
        
        # Research & Development
        'https://blog.google/technology/ai/',
        'https://ai.facebook.com/blog/',
        'https://aws.amazon.com/blogs/machine-learning/',
        'https://blogs.microsoft.com/ai/',
        'https://research.ibm.com/blog/categories/artificial-intelligence',
        'https://www.deepmind.com/blog',
        'https://futurism.com',
        
        # Developer News
        'https://dev.to/t/ai',
        'https://thenewstack.io/category/ai/',
        'https://www.infoq.com/ai-ml-data-eng/',
        'https://www.developertech.com/categories/ai',
        'https://www.i-programmer.info/news/105-artificial-intelligence.html',
        
        # Security Tech
        'https://www.darkreading.com/artificial-intelligence',
        'https://www.infosecurity-magazine.com/ai-cybersecurity/',
        'https://www.scmagazine.com/topic/artificial-intelligence',
        'https://www.helpnetsecurity.com/tag/artificial-intelligence/',
        'https://www.csoonline.com/category/artificial-intelligence/'
    ],
    'entertainment': [
        # Movies & TV
        'https://variety.com/news',
        'https://deadline.com/news',
        'https://www.hollywoodreporter.com/news',
        'https://www.indiewire.com/news',
        'https://www.empireonline.com/movies/news',
        'https://www.nbc.com/news',           # #2
        'https://www.cbs.com/news',           # #3
        
        # Celebrity News
        'https://people.com/news',
        'https://www.eonline.com/news',
        'https://www.tmz.com',
        'https://pagesix.com',
        'https://www.usmagazine.com/celebrity-news',
        
        # Music
        'https://www.billboard.com/news',
        'https://pitchfork.com/news',
        'https://www.rollingstone.com/music/music-news',
        'https://www.nme.com/news/music',
        'https://www.spin.com/news',
        
        # Gaming
        'https://www.ign.com/news',
        'https://www.gamespot.com/news',
        'https://www.polygon.com/news',
        'https://kotaku.com',
        'https://www.eurogamer.net/news',
        
        # Streaming & Digital
        'https://www.whats-on-netflix.com/news',
        'https://www.digitalspy.com/tv',
        'https://www.tvguide.com/news',
        'https://www.radiotimes.com/news',
        'https://www.vulture.com/news',
        
        # Pop Culture
        'https://www.buzzfeed.com/entertainment',
        'https://www.avclub.com/news',
        'https://www.cinemablend.com/news',
        'https://screenrant.com/movie-news',
        'https://collider.com/news'
    ],
    'science': [
        'https://www.nature.com/news',              
        'https://www.sciencedaily.com',             
        'https://www.livescience.com',              
        'https://www.scientificamerican.com',       
        'https://www.space.com',                    
        'https://www.nature.com/news'
    ]
}

# Scraping Configuration
CONCURRENT_REQUESTS = CRAWLER_CONFIG['max_concurrent_requests']  # Use value from CRAWLER_CONFIG
REQUEST_TIMEOUT = CRAWLER_CONFIG['request_timeout_seconds']     # Use value from CRAWLER_CONFIG

# Cache Configuration
CACHE_CONFIG: Dict[str, Any] = {
    'db_path': CRAWLER_CONFIG['cache_db_path'],
    'cleanup_days': CRAWLER_CONFIG['cache_cleanup_days'],
    'max_errors': CRAWLER_CONFIG['max_errors_per_domain'],
    'backoff_multiplier': CRAWLER_CONFIG['error_backoff_multiplier']
}
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
