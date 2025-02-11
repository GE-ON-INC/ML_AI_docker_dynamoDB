import json
import logging
import random
import time
from datetime import datetime
from typing import Optional, List, Dict, Any
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from fp.fp import FreeProxy
from tqdm import tqdm

from config import (
    ARTICLE_SELECTORS, BROWSER_HEADERS,
    MAX_RETRIES, MIN_DELAY, MAX_DELAY, PAGINATION_PATTERNS,
    REQUEST_TIMEOUT, USE_PROXIES
)
from models.article import Article, ArticleAnalysis
from utils.llm_utils import get_llm

class NewsScraper:
    def __init__(self, llm_provider: str = 'gemini'):
        self.llm = get_llm(llm_provider)
        self.user_agent = UserAgent()
        self.session: Optional[aiohttp.ClientSession] = None
        self.domain_last_access: Dict[str, float] = {}
        self.seen_urls = set()
        self.proxy_list: List[str] = []
        self.current_proxy_idx = 0
        self.proxy_requests_count = 0
        


    def _get_random_headers(self) -> Dict[str, str]:
        """Generate random headers with rotating user agent."""
        headers = BROWSER_HEADERS.copy()
        headers['User-Agent'] = self.user_agent.random
        return headers

    async def _get_proxy(self) -> Optional[str]:
        """Get a proxy from the pool."""
        if not USE_PROXIES:
            return None
            
        try:
            if not self.proxy_list or self.proxy_requests_count >= 10:
                self.proxy_list = [
                    FreeProxy(country_id=['US', 'CA'], timeout=1).get()
                    for _ in range(5)  # Get 5 proxies at once
                ]
                self.current_proxy_idx = 0
                self.proxy_requests_count = 0
                
            proxy = self.proxy_list[self.current_proxy_idx]
            self.proxy_requests_count += 1
            
            if self.proxy_requests_count >= 10:
                self.current_proxy_idx = (self.current_proxy_idx + 1) % len(self.proxy_list)
                
            return proxy
        except Exception as e:
            logging.warning(f"Failed to get proxy: {str(e)}")
            return None

    def _respect_rate_limits(self, domain: str):
        """Ensure we don't overwhelm any domain with requests."""
        now = datetime.now().timestamp()
        if domain in self.domain_last_access:
            time_since_last = now - self.domain_last_access[domain]
            if time_since_last < MIN_DELAY:
                delay = MIN_DELAY - time_since_last + random.uniform(0, MAX_DELAY - MIN_DELAY)
                time.sleep(delay)
        self.domain_last_access[domain] = now

    def fetch_page(self, url: str, retry_count: int = 0) -> Optional[BeautifulSoup]:
        """Fetch and parse a webpage with retries and proxy support."""
        domain = urlparse(url).netloc
        self._respect_rate_limits(domain)
        
        try:
            headers = self._get_random_headers()
            proxy = self._get_proxy()
            
            response = requests.get(
                url,
                headers=headers,
                proxies=proxy,
                timeout=REQUEST_TIMEOUT,
                verify=False
            )
            
            if response.status_code == 200:
                return BeautifulSoup(response.text, 'html.parser')
            elif response.status_code == 403 and retry_count < MAX_RETRIES:
                logging.warning(f"Access forbidden for {url}, retrying with different proxy...")
                time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))
                return self.fetch_page(url, retry_count + 1)
            else:
                logging.warning(f"Failed to fetch {url}: Status {response.status_code}")
                return None
                
        except Exception as e:
            if retry_count < MAX_RETRIES:
                logging.error(f"Error fetching {url} (attempt {retry_count + 1}): {str(e)}")
                time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))
                return self.fetch_page(url, retry_count + 1)
            logging.error(f"Max retries reached for {url}: {str(e)}")
            return None

    def extract_articles(self, soup: BeautifulSoup, base_url: str, category: str) -> List[Article]:
        """Extract article information from a parsed page."""
        articles = []
        if not soup:
            return articles

        # Find article containers
        for container_selector in ARTICLE_SELECTORS['container']:
            article_elements = soup.select(container_selector)
            if article_elements:
                break

        for article_elem in article_elements:
            try:
                # Extract title
                title = None
                for title_selector in ARTICLE_SELECTORS['title']:
                    title_elem = article_elem.select_one(title_selector)
                    if title_elem:
                        title = title_elem.get_text().strip()
                        break

                if not title:
                    continue

                # Extract URL
                url_elem = article_elem.find('a')
                if not url_elem or not url_elem.get('href'):
                    continue

                article_url = urljoin(base_url, url_elem['href'])
                if article_url in self.seen_urls:
                    continue

                self.seen_urls.add(article_url)

                # Extract other optional fields
                author = None
                for author_selector in ARTICLE_SELECTORS['author']:
                    author_elem = article_elem.select_one(author_selector)
                    if author_elem:
                        author = author_elem.get_text().strip()
                        break

                publish_date = None
                for date_selector in ARTICLE_SELECTORS['date']:
                    date_elem = article_elem.select_one(date_selector)
                    if date_elem:
                        date_str = date_elem.get('datetime') or date_elem.get_text().strip()
                        try:
                            publish_date = datetime.fromisoformat(date_str)
                        except (ValueError, TypeError):
                            continue
                        break

                # Extract content if available
                content = None
                for content_selector in ARTICLE_SELECTORS['content']:
                    content_elem = article_elem.select_one(content_selector)
                    if content_elem:
                        content = content_elem.get_text().strip()
                        break
                        
                # Create base Article object
                article = Article(
                    title=title,
                    url=article_url,
                    category=category,
                    source=urlparse(base_url).netloc,
                    author=author,
                    publish_date=publish_date,
                    content=content
                )
                
                # Analyze with LLM if content is available
                if content:
                    try:
                        # Generate summary
                        article.summary = self.llm.generate_summary(content)
                        
                        # Extract topics
                        article.topics = self.llm.extract_topics(content)
                        
                        # Full analysis
                        analysis_dict = json.loads(self.llm.analyze_article(content))
                        article.analysis = ArticleAnalysis(**analysis_dict)
                    except Exception as e:
                        logging.error(f"Error during LLM analysis: {str(e)}")
                        
                articles.append(article)

            except Exception as e:
                logging.error(f"Error extracting article: {str(e)}")
                continue

        return articles

    def get_pagination_url(self, base_url: str, page: int) -> str:
        """Get the URL for a specific page based on site-specific patterns."""
        domain = urlparse(base_url).netloc
        for site, pattern in PAGINATION_PATTERNS.items():
            if site in domain:
                return urljoin(base_url, pattern(page))
        return base_url  # Return original URL if no pattern matches

    async def scrape_source(self, url: str, category: str, max_pages: int = 3) -> List[Article]:
        """Scrape articles from a single source with pagination support."""
        all_articles = []
        
        for page in range(1, max_pages + 1):
            page_url = self.get_pagination_url(url, page)
            soup = await self.fetch_page(page_url)
            
            if soup:
                articles = self.extract_articles(soup, url, category)
                if articles:
                    all_articles.extend(articles)
                    await asyncio.sleep(random.uniform(MIN_DELAY, MAX_DELAY))
                else:
                    break  # No articles found, might be end of pagination
                    
        return all_articles

    def scrape_all_sources(self, sources: Dict[str, List[str]]) -> List[Dict]:
        """Scrape all sources with rate limiting."""
        all_articles = []
        total_urls = sum(len(urls) for urls in sources.values())
        
        with tqdm(total=total_urls, desc="Scraping sources") as pbar:
            for category, urls in sources.items():
                for url in urls:
                    try:
                        articles = self.scrape_source(url, category)
                        all_articles.extend(articles)
                        pbar.update(1)
                    except Exception as e:
                        logging.error(f"Failed to scrape {url}: {str(e)}")
                        pbar.update(1)
                        continue
                        
        return all_articles
