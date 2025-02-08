# ML_AI_docker_dynamoDB
Project: ML_AI_Docker_DynamoDB

Description

This project demonstrates the integration of web scraping, DynamoDB setup (using Docker), and data processing using Python. The repository includes scripts for scraping news articles from various websites, storing the scraped data in a local DynamoDB instance, and using Docker to containerize the setup.

Repository Contents

1. docker-compose.yml

This file defines the Docker setup for a local DynamoDB instance.

Service Name: dbDYNAMODB

Image: amazon/dynamodb-local

Ports: Exposes the local DynamoDB on port 8000.

Volume Mapping: Maps the local folder dynamodb-data to /data inside the container to persist data.

Command:

To start the DynamoDB container:

docker-compose up

To stop the container:

docker-compose down

2. scrapping_articles.py

This script scrapes articles from news websites, categorizes them, and saves the data to a CSV file (news_articles.csv).

Libraries Used: requests, BeautifulSoup, csv

News Categories:

Sports

Politics

Weather

Finance

Music

Key Functionality:

Scrapes up to 10 articles per website.

Handles relative URLs and missing data gracefully.

Outputs a CSV file with the following columns:

description: Title of the article.

url: Link to the article.

category: Article category.

3. test.py

This script interacts with the DynamoDB instance to create a table, populate it with the scraped data from news_articles.csv, and scan the table to retrieve all stored items.

Key Steps:

Create a DynamoDB Table:

Table Name: NewsArticles

Primary Key: url (String type).

Insert Data:

Reads news_articles.csv using pandas and inserts each row as an item into the DynamoDB table.

Scan the Table:

Retrieves and prints all items stored in the table.

Commands to Run:

python test.py

Requirements

All required Python libraries are listed in requirements.txt.

To Install:

pip install -r requirements.txt

Libraries:

boto3: For interacting with DynamoDB.

pandas: For data manipulation.

requests: For making HTTP requests.

BeautifulSoup: For parsing HTML content.

Running the Project

Set Up DynamoDB (Docker):

Ensure Docker is installed and running.

Run:

docker-compose up

Scrape Articles:

Run scrapping_articles.py to scrape articles and generate the CSV:

python scrapping_articles.py

Insert Data into DynamoDB:

Run test.py to create the table, populate it, and retrieve data:

python test.py

View Data:

Use the scan operation in test.py to view all stored articles.

Additional Notes

Local DynamoDB: This project uses a local instance of DynamoDB for development and testing purposes.

Error Handling: Scripts include error handling for common issues such as HTTP request failures and DynamoDB table conflicts.

CSV File: Ensure that news_articles.csv exists in the working directory before running test.py.

Future Improvements

Add support for paginated scraping to handle more articles per website.

Implement AWS-hosted DynamoDB for production use.

Add testing scripts to validate scraping and data insertion processes.