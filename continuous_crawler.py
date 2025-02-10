import asyncio
import logging
from datetime import datetime
from pathlib import Path
import signal
import sys

from crawl_4_ai import NewsCrawler

# Global flag for graceful shutdown
running = True

def setup_logging():
    """Configure logging to both file and console."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s',
        handlers=[logging.StreamHandler()]
    )

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global running
    print("\nShutting down gracefully... Please wait for current crawls to complete.")
    running = False

async def continuous_crawl(csv_file: str):
    """Continuously crawl news sources with pagination support."""
    news_sources = {
        'sports': [
            'https://www.espn.com',
            'https://sports.yahoo.com',
            'https://www.cbssports.com',
            'https://www.nba.com/news',
            'https://www.mlb.com/news',
            'https://www.nfl.com/news',
            'https://www.skysports.com',
            'https://www.goal.com',
            'https://www.foxsports.com',
            'https://www.nbcsports.com',
            'https://www.sportingnews.com',
            'https://www.si.com',
            'https://bleacherreport.com',
            'https://www.theathletic.com'
        ],
        'business': [
            'https://www.bloomberg.com',
            'https://www.reuters.com/business',
            'https://www.cnbc.com',
            'https://www.wsj.com',
            'https://www.ft.com',
            'https://www.marketwatch.com',
            'https://www.forbes.com',
            'https://www.businessinsider.com',
            'https://www.economist.com',
            'https://finance.yahoo.com',
            'https://www.barrons.com',
            'https://www.investing.com',
            'https://seekingalpha.com',
            'https://www.fool.com'
        ],
        'technology': [
            'https://techcrunch.com',
            'https://www.theverge.com',
            'https://www.wired.com',
            'https://arstechnica.com',
            'https://www.engadget.com'
        ],
        'science': [
            'https://www.sciencemag.org',
            'https://www.nature.com/news',
            'https://www.newscientist.com',
            'https://phys.org',
            'https://www.scientificamerican.com'
        ],
        'world': [
            'https://www.bbc.com/news/world',
            'https://www.aljazeera.com',
            'https://www.dw.com/en/world',
            'https://www.france24.com/en',
            'https://www.reuters.com/world'
        ]
    }
    
    crawler = NewsCrawler()
    crawler.csv_file = csv_file
    
    while running:
        try:
            logging.info(f"\nStarting new crawl cycle at {datetime.now()}")
            
            # Crawl with pagination (up to 10 pages per source, 500 articles per source)
            articles = await crawler.crawl_multiple(
                news_sources,
                articles_per_source=500,
                max_pages=10
            )
            
            logging.info(f"\nFinished crawl cycle. Found {len(articles)} articles")
            logging.info("Waiting 30 minutes before next cycle...")
            
            # Wait 30 minutes before next cycle, but check running flag every 5 seconds
            for _ in range(360):  # 360 * 5 seconds = 30 minutes
                if not running:
                    break
                await asyncio.sleep(5)
                
        except Exception as e:
            logging.error(f"Error during crawl cycle: {str(e)}")
            await asyncio.sleep(60)  # Wait a minute before retrying

async def main():
    """Main entry point for continuous crawler."""
    setup_logging()
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Use existing CSV file
    csv_file = 'articles_20250209_234732.csv'
    
    logging.info("Starting continuous crawler...")
    logging.info("Press Ctrl+C to stop gracefully")
    
    await continuous_crawl(csv_file)
    
    logging.info("Crawler stopped")

if __name__ == "__main__":
    asyncio.run(main())
