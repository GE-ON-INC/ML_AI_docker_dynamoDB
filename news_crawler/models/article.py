from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, HttpUrl, Field
import re

class ArticleAnalysis(BaseModel):
    """LLM analysis of an article."""
    main_topic: str = Field(..., description="The primary topic of the article")
    subtopics: List[str] = Field(default_factory=list, description="List of subtopics discussed")
    key_points: List[str] = Field(default_factory=list, description="List of main points from the article")
    sentiment: str = Field(..., description="Overall sentiment (positive, negative, neutral)")
    bias: Optional[str] = Field(None, description="Any detected bias in reporting")

class Article(BaseModel):
    """Represents a news article with its metadata and analysis."""
    # Basic metadata
    title: str = Field(..., description="The title/headline of the article")
    url: HttpUrl = Field(..., description="The URL where the article can be found")
    category: str = Field(..., description="The category of the article (e.g., sports, politics)")
    source: str = Field(..., description="The source website of the article")
    timestamp: datetime = Field(default_factory=datetime.now, description="When the article was scraped")
    
    # Article content
    content: Optional[str] = Field(None, description="The main content of the article if available")
    excerpt: Optional[str] = Field(None, description="Brief summary or excerpt of the article")
    author: Optional[str] = Field(None, description="The author of the article if available")
    publish_date: Optional[datetime] = Field(None, description="When the article was published if available")
    
    # LLM-generated fields
    summary: Optional[str] = Field(None, description="LLM-generated summary of the article")
    topics: Optional[List[str]] = Field(None, description="Main topics extracted by LLM")
    analysis: Optional[ArticleAnalysis] = Field(None, description="Detailed LLM analysis of the article")
    
    def clean_content(self) -> None:
        """Clean article content."""
        if not self.content:
            return
            
        # Remove URLs and markdown links
        self.content = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', self.content)
        self.content = re.sub(r'https?://\S+', '', self.content)
        
        # Remove extra whitespace
        self.content = re.sub(r'\s+', ' ', self.content)
        self.content = self.content.strip()
        
    def to_dict(self) -> dict:
        """Convert to clean dictionary for export."""
        return {
            'url': str(self.url),
            'title': self.title,
            'author': self.author,
            'date': self.publish_date.isoformat() if self.publish_date else None,
            'content': self.content,
            'category': self.category,
            'source': self.source,
            'main_topic': self.analysis.main_topic if self.analysis else None,
            'sentiment': self.analysis.sentiment if self.analysis else None,
            'key_points': ', '.join(self.analysis.key_points) if self.analysis and self.analysis.key_points else None,
            'bias': self.analysis.bias if self.analysis else None,
            'summary': self.summary,
            'topics': ', '.join(self.topics) if self.topics else None
        }
        
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
