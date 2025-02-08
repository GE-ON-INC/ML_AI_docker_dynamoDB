import requests
from bs4 import BeautifulSoup
import csv

# Function to scrape articles from a news website
def scrape_articles(url, category, limit=10):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    articles = []
    count = 0

    for item in soup.find_all('article'):
        if count >= limit:  # Stop scraping after reaching the limit
            break

        # Safely extract the title (fallback tags: h2 -> h3 -> p)
        title_tag = item.find('h2') or item.find('h3') or item.find('p')
        title = title_tag.get_text().strip() if title_tag else "No Title"

        # Safely extract the URL (handle relative URLs)
        link_tag = item.find('a')
        link = link_tag['href'] if link_tag and 'href' in link_tag.attrs else "No Link"
        if link.startswith('/'):  # Handle relative URLs
            link = url.rstrip('/') + link

        # Append the article details
        articles.append({'description': title, 'url': link, 'category': category})
        count += 1

    return articles

# URLs and their corresponding categories
news_sources = [
    # Sports
    {'url': 'https://www.espn.com', 'category': 'sports'},
    {'url': 'https://www.bbc.com/sport', 'category': 'sports'},
    {'url': 'https://www.skysports.com', 'category': 'sports'},
    {'url': 'https://bleacherreport.com', 'category': 'sports'},
    {'url': 'https://www.si.com', 'category': 'sports'},

    # Politics
    {'url': 'https://www.cnn.com/politics', 'category': 'politics'},
    {'url': 'https://www.bbc.com/news/politics', 'category': 'politics'},
    {'url': 'https://thehill.com', 'category': 'politics'},
    {'url': 'https://www.politico.com', 'category': 'politics'},
    {'url': 'https://www.reuters.com/politics', 'category': 'politics'},

    # Weather
    {'url': 'https://weather.com/news', 'category': 'weather'},
    {'url': 'https://www.bbc.com/weather', 'category': 'weather'},
    {'url': 'https://www.accuweather.com/en/weather-news', 'category': 'weather'},
    {'url': 'https://www.noaa.gov/news', 'category': 'weather'},
    {'url': 'https://www.weather.gov/news', 'category': 'weather'},

    # Finance
    {'url': 'https://www.bloomberg.com', 'category': 'finance'},
    {'url': 'https://www.cnbc.com/finance/', 'category': 'finance'},
    {'url': 'https://www.reuters.com/finance', 'category': 'finance'},
    {'url': 'https://finance.yahoo.com', 'category': 'finance'},
    {'url': 'https://www.wsj.com/news/business', 'category': 'finance'},

    # Music
    {'url': 'https://www.rollingstone.com/music', 'category': 'music'},
    {'url': 'https://www.billboard.com', 'category': 'music'},
    {'url': 'https://pitchfork.com', 'category': 'music'},
    {'url': 'https://www.nme.com', 'category': 'music'},
    {'url': 'https://consequence.net', 'category': 'music'},

    # General News (All Categories)
    {'url': 'https://www.bbc.com/news', 'category': 'general'},
    {'url': 'https://www.theguardian.com', 'category': 'general'},
    {'url': 'https://www.nytimes.com', 'category': 'general'},
    {'url': 'https://www.reuters.com', 'category': 'general'},
    {'url': 'https://www.aljazeera.com', 'category': 'general'}
]

all_articles = []
for source in news_sources:
    articles = scrape_articles(source['url'], source['category'])
    all_articles.extend(articles)

# Write to CSV
with open('news_articles.csv', 'w', newline='') as csvfile:
    fieldnames = ['description', 'url', 'category']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for article in all_articles:
        writer.writerow(article)