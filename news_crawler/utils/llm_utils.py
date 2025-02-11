import os
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import logging

import google.generativeai as genai
from deepseek import DeepSeekAPI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class LLMBase(ABC):
    """Base class for LLM implementations."""
    
    @abstractmethod
    def analyze_article(self, content: str) -> Dict:
        """Analyze article content and return structured information."""
        pass
    
    @abstractmethod
    def generate_summary(self, content: str) -> str:
        """Generate a concise summary of the article."""
        pass
    
    @abstractmethod
    def extract_topics(self, content: str) -> List[str]:
        """Extract main topics from the article."""
        pass

class GeminiLLM(LLMBase):
    """Gemini implementation of LLM interface."""
    
    def __init__(self):
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        
    def analyze_article(self, content: str) -> Dict:
        """Analyze article content using Gemini."""
        prompt = f"""
        Analyze this article and extract the following information in JSON format:
        - main_topic: The primary topic of the article
        - subtopics: List of subtopics discussed
        - key_points: List of main points
        - sentiment: Overall sentiment (positive, negative, neutral)
        - bias: Any detected bias in reporting
        
        Article content:
        {content}
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logging.error(f"Error analyzing article with Gemini: {str(e)}")
            return {}
            
    def generate_summary(self, content: str) -> str:
        """Generate a concise summary using Gemini."""
        prompt = f"""
        Generate a concise 2-3 sentence summary of this article:
        {content}
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logging.error(f"Error generating summary with Gemini: {str(e)}")
            return ""
            
    def extract_topics(self, content: str) -> List[str]:
        """Extract main topics using Gemini."""
        prompt = f"""
        Extract 3-5 main topics from this article as a comma-separated list:
        {content}
        """
        
        try:
            response = self.model.generate_content(prompt)
            topics = [t.strip() for t in response.text.split(',')]
            return topics
        except Exception as e:
            logging.error(f"Error extracting topics with Gemini: {str(e)}")
            return []

class DeepSeekLLM(LLMBase):
    """DeepSeek implementation of LLM interface."""
    
    def __init__(self):
        api_key = os.getenv('DEEPSEEK_API_KEY')
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY not found in environment variables")
            
        self.client = DeepSeekAPI(api_key)
        
    def analyze_article(self, content: str) -> Dict:
        """Analyze article content using DeepSeek."""
        prompt = f"""
        Analyze this article and extract the following information in JSON format:
        - main_topic: The primary topic of the article
        - subtopics: List of subtopics discussed
        - key_points: List of main points
        - sentiment: Overall sentiment (positive, negative, neutral)
        - bias: Any detected bias in reporting
        
        Article content:
        {content}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        except Exception as e:
            logging.error(f"Error analyzing article with DeepSeek: {str(e)}")
            return {}
            
    def generate_summary(self, content: str) -> str:
        """Generate a concise summary using DeepSeek."""
        prompt = f"""
        Generate a concise 2-3 sentence summary of this article:
        {content}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        except Exception as e:
            logging.error(f"Error generating summary with DeepSeek: {str(e)}")
            return ""
            
    def extract_topics(self, content: str) -> List[str]:
        """Extract main topics using DeepSeek."""
        prompt = f"""
        Extract 3-5 main topics from this article as a comma-separated list:
        {content}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}]
            )
            topics = [t.strip() for t in response.choices[0].message.content.split(',')]
            return topics
        except Exception as e:
            logging.error(f"Error extracting topics with DeepSeek: {str(e)}")
            return []

def get_llm(provider: str = 'gemini') -> LLMBase:
    """Factory function to get the appropriate LLM instance."""
    if provider.lower() == 'gemini':
        return GeminiLLM()
    elif provider.lower() == 'deepseek':
        return DeepSeekLLM()
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")
