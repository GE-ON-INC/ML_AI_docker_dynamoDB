import asyncio
import logging
from datetime import datetime
from pathlib import Path
import pandas as pd

from crawl_4_ai import NewsCrawler

def setup_logging():
    """Configure logging to both file and console."""
    # Create output directory if it doesn't exist
    output_dir = Path('output')
    output_dir.mkdir(exist_ok=True)
    
    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(message)s'
    )
    
    # Create handlers
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = output_dir / f'crawler_{timestamp}.log'
    error_file = output_dir / f'crawler_{timestamp}.error.log'
    
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(file_formatter)
    
    error_handler = logging.FileHandler(error_file)
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    
    # Configure root logger
    logging.root.setLevel(logging.INFO)
    logging.root.addHandler(file_handler)
    logging.root.addHandler(error_handler)
    logging.root.addHandler(console_handler)

async def main():
    """Main entry point for the news scraper."""
    setup_logging()
    start_time = datetime.now()
    
    # News sources to crawl
    news_sources = {
        'technology': [
            'https://techcrunch.com',
            'https://www.theverge.com',
            'https://www.wired.com',
            'https://arstechnica.com',
            'https://www.engadget.com'
        ],
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
    
    try:
        logging.info("Starting news scraper...")
        crawler = NewsCrawler()
        
        # Crawl all sources (100 articles per source)
        articles = await crawler.crawl_multiple(news_sources, articles_per_source=100)
        
        # Create output directory if it doesn't exist
        output_dir = Path('output')
        output_dir.mkdir(exist_ok=True)
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save as JSON
        json_file = output_dir / f'articles_{timestamp}.json'
        articles_data = [article.to_dict() for article in articles]
        pd.DataFrame(articles_data).to_json(json_file, orient='records', indent=2)
        
        # Save as CSV
        csv_file = output_dir / f'articles_{timestamp}.csv'
        pd.DataFrame(articles_data).to_csv(csv_file, index=False)
        
        # Print statistics
        logging.info(f"\nCrawling completed in {(datetime.now() - start_time).total_seconds():.2f} seconds")
        logging.info(f"Total articles crawled: {len(articles)}")
        logging.info(f"\nResults saved to:")
        logging.info(f"- JSON: {json_file}")
        logging.info(f"- CSV: {csv_file}")
        
        # Print category breakdown
        category_counts = pd.DataFrame(articles_data)['category'].value_counts()
        logging.info("\nArticles by category:")
        for category, count in category_counts.items():
            logging.info(f"- {category}: {count}")
        
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    asyncio.run(main())
