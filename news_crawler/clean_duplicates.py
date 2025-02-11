import csv
from pathlib import Path
from urllib.parse import urlparse
from loguru import logger
from typing import List, Dict

from models.article import Article
from utils.data_utils import deduplicate_articles, get_stats, print_stats
from utils.standardize_csv import standardize_csv

def process_csv():
    input_file = "articles_simple_latest.csv"
    temp_file = "articles_temp_standardized.csv"
    output_file = "articles_cleaned.csv"
    
    # First standardize the CSV
    logger.info("Standardizing CSV...")
    standardize_csv(input_file, temp_file)
    
    # Read standardized articles
    articles: List[Article] = []
    with open(temp_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='|')
        for row in reader:
            # Extract source from URL
            url = row.get('url', '')
            source = urlparse(url).netloc if url else 'unknown'
            
            # Include required source field for Article model
            article_data = {
                'title': row.get('title', ''),
                'url': url,
                'category': row.get('category', ''),
                'source': source  # Required by Article model
            }
            articles.append(Article(**article_data))
    
    # Remove duplicates
    logger.info(f"Found {len(articles)} articles before deduplication")
    unique_articles = deduplicate_articles(articles)
    logger.info(f"Found {len(unique_articles)} articles after deduplication")
    
    # Get and print statistics
    stats = get_stats(unique_articles)
    print_stats(stats)
    
    # Save deduplicated articles with only title, url, category
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['title', 'url', 'category'], delimiter='|')
        writer.writeheader()
        for article in unique_articles:
            writer.writerow({
                'title': article.title,
                'url': article.url,
                'category': article.category
            })
    
    # Clean up temp file
    Path(temp_file).unlink()
    logger.info(f"Saved cleaned articles to {output_file}")

if __name__ == "__main__":
    process_csv()
