import json
import os
import re
import csv
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from loguru import logger

from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CacheMode,
    CrawlerRunConfig,
    LLMExtractionStrategy,
)
from dotenv import load_dotenv
from tqdm import tqdm

import sys
from pathlib import Path

# Add parent directory to path for imports
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from new_crawler.config import ARTICLE_SELECTORS
from models.article import Article, ArticleAnalysis
from utils.date_utils import parse_date
from utils.persistent_cache import PersistentArticleCache

# Load environment variables
load_dotenv()

class NewsCrawler:
    """AI-powered news crawler using DeepSeek and Crawl4AI."""
    
    def __init__(self, storage=None, cache_path: str = "cache/article_cache.db"):
        self.browser_config = self._get_browser_config()
        self.crawler = None
        self.cache = PersistentArticleCache(cache_path)  # Initialize persistent cache
        self.storage = storage  # ArticleStorage instance for immediate saving
        
    async def initialize(self):
        """Initialize the crawler with browser."""
        # Initialize the crawler with browser
        self.crawler = AsyncWebCrawler(browser_config=self.browser_config)
        await self.crawler.start()
        
    def _get_browser_config(self) -> BrowserConfig:
        """Get browser configuration for the crawler."""
        return BrowserConfig(
            browser_type="chromium",
            headless=True,
            verbose=True,
            text_mode=True,  # Only load text content
            ignore_https_errors=True,  # Handle SSL issues
            use_managed_browser=True  # Use the managed browser
        )
        
    def _get_llm_strategy(self) -> LLMExtractionStrategy:
        """Get LLM extraction strategy configuration."""
        return LLMExtractionStrategy(
            provider="google",
            api_token=os.getenv("GOOGLE_API_KEY"),
            model="gemini-pro",
            schema=Article.model_json_schema(),
            extraction_type="schema",
            instruction=(
                "Extract article information with 'title', 'content', 'author', "
                "'publish_date', and analyze the content to provide: main_topic, "
                "subtopics (list), key_points (list), sentiment, and bias."
            ),
            input_format="markdown",
            verbose=True
        )
        
    async def _check_no_results(self, url: str, session_id: str) -> bool:
        """Check if page has no results."""
        config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            session_id=session_id
        )
        config.browser_config = self.browser_config
        result = await self.crawler.arun(
            url=url,
            config=config
        )
        
        if result.success:
            return "No Results Found" in result.cleaned_html
        return False
                
    async def _crawl_source_with_semaphore(self, semaphore: asyncio.Semaphore, base_url: str, category: str, max_articles: int, max_pages: int) -> List[Article]:
        """Crawl a single source with semaphore control for concurrency."""
        async with semaphore:
            try:
                # First get the homepage
                result = await self.crawler.arun(
                    url=base_url,
                    bypass_cache=True,
                    verbose=True
                )
                
                if not result.success:
                    logger.error(f"Failed to crawl {base_url}: {result.error_message}")
                    return []
                
                # Extract article links
                article_links = self._extract_article_links(result.html, base_url)
                if not article_links:
                    logger.info(f"No article links found on {base_url}")
                    return []
                
                # Get pagination links
                soup = BeautifulSoup(result.html, 'html.parser')
                pagination_links = self._get_pagination_links(soup, base_url)
                logger.info(f"Found {len(pagination_links)} pagination links")
                
                # Crawl all pagination links
                pages_crawled = 1
                for page_url in pagination_links:  # Process all pagination links
                    try:
                        logger.info(f"Crawling page: {page_url}")
                        page_result = await self.crawler.arun(
                            url=page_url,
                            bypass_cache=True,
                            verbose=True
                        )
                        
                        if page_result.success:
                            page_articles = self._extract_article_links(page_result.html, base_url)
                            article_links.extend(page_articles)
                            logger.info(f"Found {len(page_articles)} articles on page {pages_crawled + 1}")
                            pages_crawled += 1
                            
                            # Add delay to avoid rate limiting
                            await asyncio.sleep(2)
                            
                    except Exception as e:
                        logger.error(f"Error crawling page {page_url}: {str(e)}")
                        continue
                
                # Process articles immediately as we find them
                for article_data in article_links:  # Process all articles
                    try:
                        article_url = article_data['url']
                        
                        # Check cache
                        if not self.cache.should_scrape_url(article_url):
                            logger.debug(f"Skipping cached article: {article_url}")
                            continue
                        
                        # Create basic article with available metadata
                        article = Article(
                            url=article_url,
                            title=article_data.get('title', 'Unknown Title'),
                            author=article_data.get('author'),
                            date=None,  # We'll parse this later
                            content='',  # Will be populated after crawl
                            category=category,
                            source=urlparse(base_url).netloc,
                            excerpt=article_data.get('excerpt')
                        )
                        
                        # Immediately save the article with basic metadata
                        if self.storage:
                            self.storage.append_articles([article])
                            logger.info(f"Added article to storage: {article.title}")
                        
                        # Crawl article content asynchronously
                        article_result = await self.crawler.arun(
                            url=article_url,
                            bypass_cache=True,
                            verbose=True
                        )
                        
                        if article_result.success and article_result.markdown:
                            # Update article with full content
                            article.content = article_result.markdown
                            article.title = article_data.get('title') or article_result.metadata.get('title', article.title)
                            article.author = article_data.get('author') or article_result.metadata.get('author', article.author)
                            
                            # Clean content
                            article.clean_content()
                            
                            # Skip if content is too short
                            if not article.content or len(article.content) < 100:
                                logger.debug(f"Skipping article (too short): {article.title}")
                                continue
                            
                            # Update the article in storage with full content
                            if self.storage:
                                self.storage.append_articles([article])
                                logger.info(f"Updated article with content: {article.title}")
                            
                            # Add delay to avoid rate limiting
                            await asyncio.sleep(1)
                            
                    except Exception as e:
                        logger.error(f"Error crawling article {article_url}: {str(e)}")
                        continue
                
                return articles
                
            except Exception as e:
                logger.error(f"Error crawling {base_url}: {str(e)}")
                return []

    async def crawl_page(self, url: str, category: str, session_id: str) -> List[Article]:
        """Crawl a single page for articles."""
        articles = []
        
        # Get domain and check if we should scrape
        domain = urlparse(url).netloc
        if not self.cache.should_scrape_domain(domain, timeout_minutes=60):
            logger.debug(f"Skipping {domain} - recently crawled")
            return articles
            
        # Check if URL is already cached
        if not self.cache.should_scrape_url(url):
            logger.debug(f"Skipping {url} - already in cache")
            return articles
            
        # Check for no results
        no_results = await self._check_no_results(url, session_id)
        if no_results:
            return articles
            
        # Configure extraction
        config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            extraction_strategy=self._get_llm_strategy(),
            css_selector=ARTICLE_SELECTORS['content'],
            session_id=session_id
        )
        config.browser_config = self.browser_config
        result = await self.crawler.arun(
            url=url,
            config=config
        )
        
        if not (result.success and result.extracted_content):
            print(f"Error crawling {url}: {result.error_message}")
            return articles
            
        # Process extracted content
        try:
            extracted_data = json.loads(result.extracted_content)
            if not extracted_data:
                return articles
                
            for data in extracted_data:
                title = data.get('title')
                
                # Skip if we've seen this title from this domain
                if not self.cache.should_scrape_url(url, title):
                    continue
                    
                # Create article with minimal metadata
                article = Article(
                    title=title,
                    url=url,
                    category=category,
                    source=urlparse(url).netloc
                )
                
                # Add to cache
                self.cache.add_article(url, title, category)
                
                # Save article immediately if storage is provided
                if self.storage:
                    self.storage.append_articles([article])
                    
                articles.append(article)
                    
                articles.append(article)
                
        except Exception as e:
            print(f"Error processing content from {url}: {str(e)}")
            
        # Add successful URLs to cache
        for article in articles:
            self.cache.add_url(article.url)
        return articles
        
    async def crawl_source(self, start_url: str, category: str, max_articles: int = 10) -> List[Article]:
        """Crawl a news source for articles."""
        session_id = f"news_{category}_{urlparse(start_url).netloc}"
        articles = []
        page = 1
        
        with tqdm(total=max_articles, desc=f"Crawling {urlparse(start_url).netloc}") as pbar:
            while len(articles) < max_articles:
                url = f"{start_url}?page={page}" if page > 1 else start_url
                
                new_articles = await self.crawl_page(url, category, session_id)
                if not new_articles:
                    break
                    
                articles.extend(new_articles[:max_articles - len(articles)])
                pbar.update(len(new_articles))
                page += 1
                
        return articles[:max_articles]
        
    def _get_pagination_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract pagination/archive links from the page."""
        pagination_links = set()
        # Common pagination selectors
        pagination_selectors = [
            '.pagination a',
            '.pager a',
            '.pages a',
            'a[href*="/page/"]',
            'a[href*="/archive/"]',
            'a[href*="/news/archive/"]',
            '.nav-links a',
            '.next',
            '.load-more',
            # Add more specific selectors
            'a[href*="page="]',  # Common query param style
            'a[href*="offset="]',
            'a[href*="p="]',
            '.pagination__next',
            '.pagination__page',
            '.pagination-next',
            '.pagination-item',
            'a.next',
            'link[rel="next"]',
            # Common text-based pagination links
            'a:contains("Next")',
            'a:contains("More")',
            'a:contains("Load More")',
            'button:contains("Load More")',
            '.infinite-scroll-component'
        ]
        
        for selector in pagination_selectors:
            for link in soup.select(selector):
                href = link.get('href')
                if href:
                    # Convert relative URLs to absolute
                    full_url = urljoin(base_url, href)
                    # Only include links from the same domain
                    if urlparse(full_url).netloc == urlparse(base_url).netloc:
                        pagination_links.add(full_url)
        
        return list(pagination_links)

    def _extract_article_content(self, html: str) -> str:
        """Extract the main content from an article page."""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove unwanted elements
        for element in soup.find_all(['script', 'style', 'nav', 'header', 'footer', 'iframe']):
            element.decompose()
        
        # Common article content selectors
        content_selectors = [
            'article',
            '.article-content',
            '.post-content',
            '.entry-content',
            '.story-content',
            '.article-body',
            '.story-body',
            '.main-content',
            '[itemprop="articleBody"]',
            '.content-article'
        ]
        
        # Try to find the main content
        for selector in content_selectors:
            content = soup.select_one(selector)
            if content:
                # Clean the content
                for tag in content.find_all(['a', 'button', 'div', 'aside']):
                    if any(cls in (tag.get('class', []) or []) for cls in ['share', 'social', 'related', 'newsletter', 'ad', 'advertisement']):
                        tag.decompose()
                
                # Get text and clean it
                text = content.get_text(separator='\n', strip=True)
                # Remove extra whitespace and newlines
                text = re.sub(r'\n\s*\n', '\n', text)
                text = re.sub(r'\s+', ' ', text)
                return text.strip()
        
        return ''

    def _extract_article_links(self, html: str, base_url: str) -> List[Dict[str, str]]:
        """Extract article links and metadata from HTML."""
        soup = BeautifulSoup(html, 'html.parser')
        articles = []
        
        # Common article containers
        article_selectors = [
            # Basic article containers
            'article',  # Common article tag
            '.post',    # Common post class
            '.story',   # Common story class
            '.entry',   # Common entry class
            '.article', # Common article class
            
            # Common news site containers
            '.news-item',
            '.feed-item',
            '.list-item',
            '.card',
            '.content-item',
            '.media',
            '.item',
            '.result',
            
            # News site specific selectors
            '.nytimes-article',
            '.reuters-article',
            '.wsj-article',
            '.wapo-article',
            '.cnn-article',
            '.fox-article',
            '.bbc-article',
            
            # Article variations
            '.article-card',
            '.news-article',
            '.blog-post',
            '.feed-entry',
            '.stream-item',
            '.grid-item',
            '.teaser',
            '.headline',
            '.story-card',
            
            # Attribute-based selectors
            '[itemtype*="Article"]',
            '[itemtype*="NewsArticle"]',
            '[itemtype*="BlogPosting"]',
            '[role="article"]',
            '[data-testid*="article"]',
            '[data-component*="article"]',
            '[class*="article"]',
            '[class*="story"]',
            
            # Link-based selectors
            'a[href*="/article/"]',
            'a[href*="/story/"]',
            'a[href*="/news/"]'
        ]
        
        # Find all potential article containers
        for selector in article_selectors:
            containers = soup.select(selector)
            for container in containers:
                article_data = {}
                
                # Find link and title
                link_tag = container.find('a')
                if not link_tag or not link_tag.get('href'):
                    continue
                    
                href = link_tag['href']
                full_url = urljoin(base_url, href)
                
                # Skip non-http(s) URLs and external domains
                if not full_url.startswith(('http://', 'https://')) or \
                   urlparse(full_url).netloc != urlparse(base_url).netloc:
                    continue
                    
                article_data['url'] = full_url
                article_data['title'] = link_tag.get_text(strip=True) or container.find('h1', recursive=True).get_text(strip=True) if container.find('h1', recursive=True) else ''
                
                # Try to find author
                author_selectors = [
                    '.author',
                    '.byline',
                    '[rel="author"]',
                    '.writer'
                ]
                for author_sel in author_selectors:
                    author_tag = container.select_one(author_sel)
                    if author_tag:
                        article_data['author'] = author_tag.get_text(strip=True)
                        break
                        
                # Try to find date
                date_selectors = [
                    'time',
                    '.date',
                    '.published',
                    '.timestamp'
                ]
                for date_sel in date_selectors:
                    date_tag = container.select_one(date_sel)
                    if date_tag:
                        article_data['date'] = date_tag.get('datetime', date_tag.get_text(strip=True))
                        break
                        
                # Try to find summary/excerpt
                summary_selectors = [
                    '.excerpt',
                    '.summary',
                    '.description',
                    'p'
                ]
                for summary_sel in summary_selectors:
                    summary_tag = container.select_one(summary_sel)
                    if summary_tag:
                        article_data['excerpt'] = summary_tag.get_text(strip=True)
                        break
                        
                articles.append(article_data)
                
        return articles
        
    async def crawl_multiple(self, urls: Dict[str, List[str]], articles_per_source: int = 100, sites_per_category: int = 50, max_pages: int = 20) -> List[Article]:
        """Crawl multiple sources and categories with improved concurrency."""
        all_articles = []
        
        # Increase concurrent requests
        semaphore = asyncio.Semaphore(10)  # Allow 10 concurrent requests
        
        # Initialize browser if needed
        await self.initialize()
        
        # Create tasks for all sources across all categories
        tasks = []
        for category, source_urls in urls.items():
            # Process all sites in the category
            logger.info(f"Processing {len(source_urls)} sites for category: {category}")
            
            for base_url in source_urls:
                task = asyncio.create_task(self._crawl_source_with_semaphore(
                    semaphore, base_url, category, articles_per_source, max_pages
                ))
                tasks.append(task)
        
        # Process tasks as they complete
        for task in asyncio.as_completed(tasks):
            try:
                articles = await task
                if articles:
                    # Save articles immediately
                    if self.storage:
                        self.storage.append_articles(articles)
                    all_articles.extend(articles)
                    logger.info(f"Added {len(articles)} new articles")
            except Exception as e:
                logger.error(f"Error crawling source: {str(e)}")
                
        return all_articles
                        
    async def _analyze_with_llm(self, content: str) -> ArticleAnalysis:
        """Analyze article content with LLM."""
        try:
            # Use DeepSeek to analyze the content
            prompt = f"""Analyze this article content and provide:
            1. Main topic
            2. Overall sentiment (positive, negative, or neutral)
            3. Key points (up to 3)
            4. Any potential bias
            
            Content: {content[:2000]}..."""  # Limit content length
            
            # TODO: Implement actual LLM call here
            # For now, return placeholder analysis
            return ArticleAnalysis(
                main_topic="Technology",
                sentiment="neutral",
                key_points=["Point 1", "Point 2", "Point 3"],
                bias="None detected"
            )
            
        except Exception as e:
            print(f"Error analyzing with LLM: {str(e)}")
            traceback.print_exc()
            return ArticleAnalysis(
                main_topic="Unknown",
                sentiment="unknown",
                key_points=[],
                bias="Analysis failed"
            )
            
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig

