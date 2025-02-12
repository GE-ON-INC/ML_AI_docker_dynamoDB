import asyncio
import argparse
import os
from loguru import logger
from datetime import datetime
from pathlib import Path
import signal
import sys

from crawl_4_ai import NewsCrawler
import sys
from pathlib import Path

# Add parent directory to path for imports
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from utils.article_storage import ArticleStorage
from new_crawler.config import CRAWLER_CONFIG, FILE_CONFIG, NEWS_SOURCES

# Global flag for graceful shutdown
running = True

# Constants
SIMPLE_CSV = 'articles_simple_latest.csv'

def setup_logging():
    """Configure logging with loguru."""
    # Create output directory if it doesn't exist
    log_dir = Path(FILE_CONFIG['log_dir'])
    log_dir.mkdir(exist_ok=True)
    
    # Generate log filenames with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f'crawler_{timestamp}.log'
    error_file = log_dir / f'crawler_{timestamp}.error.log'
    
    # Remove default handler
    logger.remove()
    
    # Add handlers for different log levels and destinations
    logger.add(str(log_file),
               format="{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}",
               level="INFO")
    
    logger.add(str(error_file),
               format="{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}",
               level="ERROR")
    
    logger.add(sys.stderr,
               format="{message}",
               level="INFO")

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global running
    print("\nShutting down gracefully... Please wait for current crawls to complete.")
    running = False

async def run_simple_crawl():
    """Run a simple crawl collecting only title, url, and category."""
    start_time = datetime.now()
    storage = ArticleStorage(base_dir='/Users/jeremylevit/Library/Mobile Documents/com~apple~CloudDocs/ge-on news scraper/new_crawler')
    crawler = NewsCrawler(storage=storage)
    
    logger.info(f"Starting simple crawl at {start_time}")
    logger.info(f"Saving articles to: {FILE_CONFIG['csv_file']}")
    logger.info(f"Sources per category:")
    for category, sources in NEWS_SOURCES.items():
        logger.info(f"  {category.title()}: {len(sources)} sources")
    
    # Get initial article count
    initial_count = storage.get_article_count()
    logger.info(f"Initial article count: {initial_count}")
    
    # Crawl all sources at once for faster processing
    articles = await crawler.crawl_multiple(
        NEWS_SOURCES,
        articles_per_source=CRAWLER_CONFIG['articles_per_source'],
        sites_per_category=CRAWLER_CONFIG['sites_per_category']
    )
    
    end_time = datetime.now()
    duration = end_time - start_time
    logger.info(f"\nSimple crawl completed in {duration}.")
    logger.info(f"Found {len(articles)} articles")
    logger.info(f"Total articles in storage: {storage.get_article_count()}")
    
    return len(articles)

async def run_full_crawl():
    """Run a full crawl collecting all article data including content and analysis."""
    start_time = datetime.now()
    
    # Initialize storage for immediate article saving
    storage = ArticleStorage(base_dir='/Users/jeremylevit/Library/Mobile Documents/com~apple~CloudDocs/ge-on news scraper/new_crawler')
    crawler = NewsCrawler(storage=storage)
    
    logger.info(f"Starting full crawl at {start_time}")
    logger.info(f"Sources per category:")
    for category, sources in NEWS_SOURCES.items():
        logger.info(f"  {category.title()}: {len(sources)} sources")
    
    # Crawl with full content extraction
    articles = await crawler.crawl_multiple(
        NEWS_SOURCES,
        articles_per_source=CRAWLER_CONFIG['articles_per_source'],
        sites_per_category=CRAWLER_CONFIG['sites_per_category'],
        max_pages=10
    )
    
    end_time = datetime.now()
    duration = end_time - start_time
    logger.info(f"Full crawl completed in {duration}. Found {len(articles)} articles.")
    
    return articles

async def run_continuous_crawl(interval_minutes: int = None, mode: str = 'simple'):
    """Run continuous crawls with a specified interval."""
    global running
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    if interval_minutes is None:
        interval_minutes = CRAWLER_CONFIG['default_interval_minutes']
    
    logger.info(f"Starting continuous {mode} crawler with {interval_minutes} minute interval")
    
    while running:
        try:
            if mode == 'simple':
                await run_simple_crawl()
            else:
                await run_full_crawl()
                
            if running:
                logger.info(f"Waiting {interval_minutes} minutes until next crawl...")
                await asyncio.sleep(interval_minutes * 60)
        except Exception as e:
            logger.error(f"Error during crawl: {str(e)}")
            if running:
                await asyncio.sleep(CRAWLER_CONFIG['retry_delay_seconds'])

async def main():
    """Main entry point with command line argument parsing."""
    parser = argparse.ArgumentParser(description='News Crawler')
    parser.add_argument('--mode', choices=['single', 'continuous'], default='single',
                      help='Crawling mode: single run or continuous')
    parser.add_argument('--crawl-type', choices=['simple', 'full'], default='simple',
                      help='Type of crawl: simple (title/url/category) or full (with content)')
    parser.add_argument('--interval', type=int, default=None,
                      help='Interval between crawls in continuous mode (minutes)')
    args = parser.parse_args()
    
    setup_logging()
    
    if args.mode == 'continuous':
        await run_continuous_crawl(args.interval, args.crawl_type)
    else:
        if args.crawl_type == 'simple':
            await run_simple_crawl()
        else:
            await run_full_crawl()

if __name__ == "__main__":
    asyncio.run(main())
