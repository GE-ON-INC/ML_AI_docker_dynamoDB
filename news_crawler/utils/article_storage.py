import csv
from pathlib import Path
from typing import List, Dict, Set
from datetime import datetime
from loguru import logger

class ArticleStorage:
    """Handles storage of articles in CSV format."""
    LATEST_CSV = "articles_simple_latest.csv"
    CLEANED_CSV = "articles_cleaned.csv"
    FIELDNAMES = ["title", "url", "category"]
    MIN_TITLE_WORDS = 3
    
    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)
        self.latest_csv_path = self.base_dir / self.LATEST_CSV
        self.cleaned_csv_path = self.base_dir / self.CLEANED_CSV
        self.existing_urls: Set[str] = set()
        self._load_existing_urls()

    def _load_existing_urls(self):
        """Load existing URLs from both CSV files to avoid duplicates."""
        for csv_path in [self.latest_csv_path, self.cleaned_csv_path]:
            if csv_path.exists():
                try:
                    with open(csv_path, 'r', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        self.existing_urls.update(row['url'] for row in reader)
                except Exception as e:
                    logger.error(f"Error loading URLs from {csv_path}: {e}")

    def append_articles(self, articles: List[Dict]) -> int:
        """
        Append new articles to the latest CSV file.
        Returns the number of articles actually appended.
        """
        if not articles:
            return 0

        new_articles = []
        for article in articles:
            if article['url'] not in self.existing_urls:
                new_articles.append(article)
                self.existing_urls.add(article['url'])

        if not new_articles:
            return 0

        try:
            file_exists = self.latest_csv_path.exists()
            mode = 'a' if file_exists else 'w'
            with open(self.latest_csv_path, mode, newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.FIELDNAMES)
                if not file_exists:
                    writer.writeheader()
                writer.writerows(new_articles)
            
            logger.info(f"Appended {len(new_articles)} articles to {self.latest_csv_path}")
            return len(new_articles)

        except Exception as e:
            logger.error(f"Error appending articles to CSV: {e}")
            return 0

    def clean_duplicates(self):
        """
        Remove duplicate articles based on URL and move to cleaned CSV.
        """
        if not self.latest_csv_path.exists():
            logger.warning("No articles file found to clean")
            return

        try:
            # Read all articles
            with open(self.latest_csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                articles = list(reader)

            # Remove duplicates while preserving order
            seen_urls = set()
            unique_articles = []
            for article in articles:
                if article['url'] not in seen_urls:
                    seen_urls.add(article['url'])
                    unique_articles.append(article)

            # Write unique articles to cleaned file
            with open(self.cleaned_csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.FIELDNAMES)
                writer.writeheader()
                writer.writerows(unique_articles)

            logger.info(f"Cleaned {len(articles) - len(unique_articles)} duplicate articles")
            
            # Clear the latest file but keep the header
            with open(self.latest_csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.FIELDNAMES)
                writer.writeheader()

        except Exception as e:
            logger.error(f"Error cleaning duplicates: {e}")
