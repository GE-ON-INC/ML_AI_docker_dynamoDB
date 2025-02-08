import boto3
import pandas as pd

csv_file = 'news_articles.csv' 
df = pd.read_csv(csv_file, quotechar='"', escapechar='\\')


# Main function
def main():
    # 1. Create DynamoDB Resource
    ddb = boto3.resource(
        'dynamodb',
        endpoint_url='http://localhost:8000',  # Local DynamoDB
        region_name='us-west-2',              # Dummy region
        aws_access_key_id='dummy',            # Dummy credentials
        aws_secret_access_key='dummy'
    )

    # 2. Create the Table
    table_name = 'NewsArticles'
    try:
        table = ddb.create_table(
            TableName=table_name,
            KeySchema=[
                {'AttributeName': 'url', 'KeyType': 'HASH'}  # Primary key
            ],
            AttributeDefinitions=[
                {'AttributeName': 'url', 'AttributeType': 'S'}  # URL is a String
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        print("Creating table, please wait...")
        table.wait_until_exists()
        print(f"Table '{table_name}' created successfully!")
    except Exception as e:
        print(f"Table '{table_name}' already exists or encountered an error: {e}")

    # 3. Insert Data into the Table
    table = ddb.Table(table_name)
    for _, row in df.iterrows():
        try:
            table.put_item(
                Item={
                    'url': row['url'],  # Primary key
                    'description': row['description'],
                    'category': row['category']
                }
            )
            print(f"Inserted item: {row['url']}")
        except Exception as e:
            print(f"Error inserting item: {e}")

    # 4. Scan the Table
    print("\nScanning the table:")
    scan_response = table.scan()
    items = scan_response['Items']
    for item in items:
        print(item)

if __name__ == "__main__":
    main()