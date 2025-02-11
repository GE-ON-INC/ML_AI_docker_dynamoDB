import csv
import json
import logging
from typing import List, Dict, Any

from models.article import Article
from config import OUTPUT_FILE

def save_to_csv(articles: List[Article], filename: str = OUTPUT_FILE):
    """Save articles to CSV file."""
    if not articles:
        logging.warning("No articles to save")
        return
        
    # Convert articles to dictionaries
    article_dicts = [article.dict() for article in articles]
    
    # Get all possible fields from all articles
    fieldnames = set()
    for article in article_dicts:
        fieldnames.update(article.keys())
    
    # Write to CSV
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=sorted(fieldnames))
        writer.writeheader()
        writer.writerows(article_dicts)
        
    logging.info(f"Saved {len(articles)} articles to {filename}")

def save_to_json(articles: List[Article], filename: str = 'news_articles.json'):
    """Save articles to JSON file."""
    if not articles:
        logging.warning("No articles to save")
        return
        
    # Convert articles to dictionaries
    article_dicts = [article.dict() for article in articles]
    
    # Write to JSON
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(article_dicts, f, indent=2, ensure_ascii=False)
        
    logging.info(f"Saved {len(articles)} articles to {filename}")

def get_stats(articles: List[Article]) -> Dict[str, Any]:
    """Get statistics about the scraped articles."""
    if not articles:
        return {"total": 0}
        
    stats = {
        "total": len(articles),
        "by_category": {},
        "by_source": {},
        "with_author": sum(1 for a in articles if a.author),
        "with_publish_date": sum(1 for a in articles if a.publish_date),
        "with_content": sum(1 for a in articles if a.content)
    }
    
    # Count by category
    for article in articles:
        stats["by_category"][article.category] = stats["by_category"].get(article.category, 0) + 1
        stats["by_source"][article.source] = stats["by_source"].get(article.source, 0) + 1
    
    return stats

def print_stats(stats: Dict[str, Any]):
    """Print statistics in a readable format."""
    print("\nScraping Statistics:")
    print(f"Total Articles: {stats['total']}")
    print("\nArticles by Category:")
    for category, count in stats["by_category"].items():
        print(f"  {category}: {count}")
    print("\nArticles by Source:")
    for source, count in stats["by_source"].items():
        print(f"  {source}: {count}")
    print(f"\nArticles with author: {stats['with_author']}")
    print(f"Articles with publish date: {stats['with_publish_date']}")
    print(f"Articles with content: {stats['with_content']}")

def deduplicate_articles(articles: List[Article]) -> List[Article]:
    """Remove duplicate articles based on URL."""
    seen_urls = set()
    unique_articles = []
    
    for article in articles:
        if article.url not in seen_urls:
            seen_urls.add(article.url)
            unique_articles.append(article)
            
    return unique_articles
