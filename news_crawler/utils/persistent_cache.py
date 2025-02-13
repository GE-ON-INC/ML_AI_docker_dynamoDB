import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict
from urllib.parse import urlparse
import json
from loguru import logger

class PersistentArticleCache:
    """Persistent cache system using SQLite for tracking scraped articles."""
    
    def __init__(self, db_path: str = "cache/article_cache.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self.init_db()
        
    def init_db(self):
        """Initialize SQLite database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS articles (
                    url TEXT PRIMARY KEY,
                    title TEXT,
                    domain TEXT,
                    category TEXT,
                    first_seen TIMESTAMP,
                    last_updated TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS domain_stats (
                    domain TEXT PRIMARY KEY,
                    last_crawl TIMESTAMP,
                    success_count INTEGER DEFAULT 0,
                    error_count INTEGER DEFAULT 0,
                    avg_articles_per_crawl REAL DEFAULT 0.0,
                    metadata TEXT
                )
            """)
            
            # Create indexes for faster lookups
            conn.execute("CREATE INDEX IF NOT EXISTS idx_domain ON articles(domain)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_category ON articles(category)")
            conn.commit()
    
    def should_scrape_url(self, url: str, title: Optional[str] = None) -> bool:
        """
        Check if a URL should be scraped based on cache.
        
        Args:
            url: The URL to check
            title: Optional title to check for similar articles
            
        Returns:
            bool: True if the article should be scraped
        """
        with sqlite3.connect(self.db_path) as conn:
            # Check exact URL match
            result = conn.execute(
                "SELECT url FROM articles WHERE url = ?",
                (url,)
            ).fetchone()
            
            if result:
                return False
                
            # If title provided, check for similar titles from same domain
            if title:
                domain = urlparse(url).netloc
                result = conn.execute("""
                    SELECT url FROM articles 
                    WHERE domain = ? AND title = ?
                    """, (domain, title)
                ).fetchone()
                
                if result:
                    return False
                    
            return True
    
    def should_scrape_domain(self, domain: str, timeout_minutes: int = 60) -> bool:
        """
        Check if a domain should be scraped based on last crawl time and performance metrics.
        
        Args:
            domain: The domain to check
            timeout_minutes: Minimum minutes between crawls
            
        Returns:
            bool: True if the domain should be scraped
        """
        with sqlite3.connect(self.db_path) as conn:
            result = conn.execute(
                "SELECT last_crawl, error_count FROM domain_stats WHERE domain = ?",
                (domain,)
            ).fetchone()
            
            if not result:
                return True
                
            last_crawl, error_count = result
            last_crawl_time = datetime.fromisoformat(last_crawl)
            
            # Add exponential backoff for domains with errors
            if error_count > 0:
                timeout_minutes *= min(error_count, 5)  # Max 5x backoff
                
            return datetime.now() - last_crawl_time > timedelta(minutes=timeout_minutes)
    
    def add_article(self, url: str, title: str, category: str):
        """Add an article to the cache."""
        domain = urlparse(url).netloc
        now = datetime.now().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO articles 
                (url, title, domain, category, first_seen, last_updated)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (url, title, domain, category, now, now))
    
    def update_domain_stats(self, domain: str, success: bool, articles_count: int = 0, metadata: Dict = None):
        """Update domain crawl statistics."""
        now = datetime.now().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            if success:
                conn.execute("""
                    INSERT INTO domain_stats 
                    (domain, last_crawl, success_count, avg_articles_per_crawl, metadata)
                    VALUES (?, ?, 1, ?, ?)
                    ON CONFLICT(domain) DO UPDATE SET
                        last_crawl = ?,
                        success_count = success_count + 1,
                        avg_articles_per_crawl = (avg_articles_per_crawl + ?) / 2,
                        metadata = ?
                """, (domain, now, articles_count, json.dumps(metadata or {}),
                     now, articles_count, json.dumps(metadata or {})))
            else:
                conn.execute("""
                    INSERT INTO domain_stats (domain, last_crawl, error_count)
                    VALUES (?, ?, 1)
                    ON CONFLICT(domain) DO UPDATE SET
                        last_crawl = ?,
                        error_count = error_count + 1
                """, (domain, now, now))
    
    def get_domain_stats(self, domain: str) -> Dict:
        """Get statistics for a domain."""
        with sqlite3.connect(self.db_path) as conn:
            result = conn.execute(
                "SELECT * FROM domain_stats WHERE domain = ?",
                (domain,)
            ).fetchone()
            
            if result:
                return {
                    "domain": result[0],
                    "last_crawl": result[1],
                    "success_count": result[2],
                    "error_count": result[3],
                    "avg_articles_per_crawl": result[4],
                    "metadata": json.loads(result[5]) if result[5] else {}
                }
            return None
    
    def get_all_urls(self) -> List[str]:
        """Get all cached URLs."""
        with sqlite3.connect(self.db_path) as conn:
            return [row[0] for row in conn.execute("SELECT url FROM articles").fetchall()]
    
    def clear(self):
        """Clear all cache data."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM articles")
            conn.execute("DELETE FROM domain_stats")
            conn.commit()
