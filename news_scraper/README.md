# AI-Powered News Article Scraper

A high-performance news article scraper powered by AI that can fetch and analyze articles from major news sources. It uses Crawl4AI and DeepSeek for intelligent crawling and content analysis, combined with async HTTP requests for optimal performance.

## Features

### Core Features
- AI-powered content extraction and analysis using DeepSeek
- Intelligent crawling with Crawl4AI integration
- Asynchronous scraping for high performance
- Smart duplicate detection and removal
- Comprehensive error handling and logging
- Progress tracking with tqdm

### Supported News Sources
Includes major news outlets such as:
- Yahoo News
- NBC News
- CNN
- Forbes
- New York Times
- Reuters
- Fox News
- NPR
- Bloomberg
- And many more!

## Setup

You can run this project either directly with Python or using Docker.

### Option 1: Direct Python Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Set up your environment variables:
```bash
cp .env.example .env  # Create from example if available
```
Add your API keys and configuration to the `.env` file.

### Option 2: Docker Setup

1. Make sure you have Docker and Docker Compose installed

2. Set up your environment variables:
```bash
cp .env.example .env  # Create from example if available
```

3. Build and run with Docker Compose:
```bash
docker-compose up --build
```

The scraper will run in a container with proper volume mapping for output and logs.

## Usage

### Basic Usage
```bash
python crawl_4_ai.py
```

### What it Does
1. Crawls configured news sources using AI-powered extraction
2. Analyzes and categorizes articles using DeepSeek
3. Removes duplicate content
4. Saves processed articles to CSV format

### Project Structure
- `crawl_4_ai.py`: Main crawler implementation
- `config.py`: News sources and selector configurations
- `models/`: Data models and schemas
- `utils/`: Helper functions and utilities

## Output Format

The script generates a CSV file with comprehensive article data:

### Article Data
- Title and description
- Source URL
- Publication date
- Category
- Content analysis
- Timestamp of extraction

## Dependencies

Key dependencies include:
- `crawl4ai`: AI-powered web crawling
- `beautifulsoup4`: HTML parsing
- `python-dotenv`: Environment management
- `tqdm`: Progress tracking
- Additional requirements in `requirements.txt`

## Error Handling

- Robust error handling with detailed logging
- Automatic retry mechanism with exponential backoff
- Graceful degradation for failed sources
- Proxy support to avoid rate limiting

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - feel free to use and modify as needed.

## Customization

You can modify the `sources` dictionary in the `NewsArticleScraper` class to add or remove news sources for each category.
