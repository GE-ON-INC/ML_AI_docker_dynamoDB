import json
import os
import re
import csv
from datetime import datetime
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CacheMode,
    CrawlerRunConfig,
    LLMExtractionStrategy,
)
from dotenv import load_dotenv
from tqdm import tqdm

from config import ARTICLE_SELECTORS
from models.article import Article, ArticleAnalysis
from utils import parse_date

# Load environment variables
load_dotenv()

class NewsCrawler:
    """AI-powered news crawler using DeepSeek and Crawl4AI."""
    
    def __init__(self):
        self.browser_config = self._get_browser_config()
        self.crawler = AsyncWebCrawler(browser_config=self.browser_config)
        self.visited_urls = set()
        self.csv_file = None  # Will be set in crawl_multiple if not provided
        
    def _get_browser_config(self) -> BrowserConfig:
        """Get browser configuration for the crawler."""
        return BrowserConfig(
            browser_type="chromium",
            headless=True,
            verbose=True,
            text_mode=True,  # Only load text content
            ignore_https_errors=True  # Handle SSL issues
        )
        
    def _get_llm_strategy(self) -> LLMExtractionStrategy:
        """Get LLM extraction strategy configuration."""
        return LLMExtractionStrategy(
            provider="groq/deepseek-r1-distill-llama-70b",
            api_token=os.getenv("GROQ_API_KEY"),
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
        
    async def crawl_page(self, url: str, category: str, session_id: str) -> List[Article]:
        """Crawl a single page for articles."""
        articles = []
        
        # Skip if already visited
        if url in self.visited_urls:
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
                # Create article
                article = Article(
                    title=data.get('title'),
                    url=url,
                    category=category,
                    source=urlparse(url).netloc,
                    content=data.get('content'),
                    author=data.get('author'),
                    publish_date=data.get('publish_date')
                )
                
                # Add analysis
                if 'main_topic' in data:
                    article.analysis = ArticleAnalysis(
                        main_topic=data['main_topic'],
                        subtopics=data.get('subtopics', []),
                        key_points=data.get('key_points', []),
                        sentiment=data.get('sentiment', 'neutral'),
                        bias=data.get('bias')
                    )
                    
                    # Generate summary from key points
                    if article.analysis.key_points:
                        article.summary = ' '.join(article.analysis.key_points[:2])
                        
                    # Set topics
                    article.topics = [article.analysis.main_topic] + article.analysis.subtopics
                    
                articles.append(article)
                
        except Exception as e:
            print(f"Error processing content from {url}: {str(e)}")
            
        self.visited_urls.add(url)
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
            '.load-more'
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
            'article',  # Common article tag
            '.post',    # Common post class
            '.story',   # Common story class
            '.entry',   # Common entry class
            '.article', # Common article class
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
        
    async def crawl_multiple(self, urls: Dict[str, List[str]], articles_per_source: int = 500, max_pages: int = 10) -> List[Article]:
        """Crawl multiple sources and categories."""
        all_articles = []
        visited_urls = set()
        
        # Use provided CSV file or create a new one
        if not self.csv_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            self.csv_file = f'articles_{timestamp}.csv'
            # Create new file with headers
            with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['title', 'url', 'author', 'date', 'content', 'category', 'source', 'excerpt'])
                writer.writeheader()
        
        async with AsyncWebCrawler(browser_config=self.browser_config) as crawler:
            for category, source_urls in urls.items():
                for base_url in source_urls:
                    try:
                        print(f"\nCrawling {base_url}...")
                        
                        # First get the homepage
                        result = await crawler.arun(
                            url=base_url,
                            bypass_cache=True,
                            verbose=True
                        )
                        
                        if not result.success:
                            print(f"Failed to crawl {base_url}: {result.error_message}")
                            continue
                            
                        # Extract article metadata from homepage
                        article_data_list = self._extract_article_links(result.html, base_url)
                        print(f"Found {len(article_data_list)} potential articles on homepage")
                        
                        # Get pagination links
                        soup = BeautifulSoup(result.html, 'html.parser')
                        pagination_links = self._get_pagination_links(soup, base_url)
                        print(f"Found {len(pagination_links)} pagination links")
                        
                        # Crawl pagination links
                        pages_crawled = 1
                        for page_url in pagination_links[:max_pages-1]:  # -1 because we already crawled homepage
                            try:
                                print(f"Crawling page: {page_url}")
                                page_result = await crawler.arun(
                                    url=page_url,
                                    bypass_cache=True,
                                    verbose=True
                                )
                                
                                if page_result.success:
                                    page_articles = self._extract_article_links(page_result.html, base_url)
                                    article_data_list.extend(page_articles)
                                    print(f"Found {len(page_articles)} articles on page {pages_crawled + 1}")
                                    pages_crawled += 1
                                    
                                    # Add delay to avoid rate limiting
                                    await asyncio.sleep(2)
                                    
                            except Exception as e:
                                print(f"Error crawling page {page_url}: {str(e)}")
                                continue
                        
                        # Crawl each article
                        for article_data in article_data_list[:articles_per_source]:
                            article_url = article_data['url']
                            if article_url in visited_urls:
                                continue
                                
                            try:
                                article_result = await crawler.arun(
                                    url=article_url,
                                    bypass_cache=True,
                                    verbose=True
                                )
                                
                                if article_result.success and article_result.markdown:
                                    # Create article using both homepage metadata and crawled content
                                    article = Article(
                                        url=article_url,
                                        title=article_data.get('title') or article_result.metadata.get('title', 'Unknown Title'),
                                        author=article_data.get('author') or article_result.metadata.get('author'),
                                        date=parse_date(article_data.get('date')) or parse_date(article_result.metadata.get('date')),
                                        content=article_result.markdown,
                                        category=category,
                                        source=urlparse(base_url).netloc,
                                        excerpt=article_data.get('excerpt')
                                    )
                                    
                                    # Clean content
                                    article.clean_content()
                                    
                                    # Skip if content is too short
                                    if not article.content or len(article.content) < 100:
                                        print(f"Skipping article (too short): {article.title}")
                                        continue
                                        
                                    # Analyze with LLM
                                    article.analysis = await self._analyze_with_llm(article.content)
                                    
                                    all_articles.append(article)
                                    visited_urls.add(article_url)
                                    
                                    # Update CSV file with new article
                                    with open(self.csv_file, 'a', newline='', encoding='utf-8') as f:
                                        writer = csv.DictWriter(f, fieldnames=['title', 'url', 'author', 'date', 'content', 'category', 'source', 'excerpt'])
                                        article_dict = {
                                            'title': article.title,
                                            'url': str(article.url),
                                            'author': article.author,
                                            'date': article.publish_date.isoformat() if article.publish_date else None,
                                            'content': article.content,
                                            'category': article.category,
                                            'source': article.source,
                                            'excerpt': article.excerpt
                                        }
                                        writer.writerow(article_dict)
                                    
                                    print(f"Successfully crawled and saved: {article.title} ({len(article.content)} chars)")
                                    
                            except Exception as e:
                                print(f"Error crawling article {article_url}: {str(e)}")
                                continue
                                
                    except Exception as e:
                        print(f"Error crawling source {base_url}: {str(e)}")
                        continue
                    
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

