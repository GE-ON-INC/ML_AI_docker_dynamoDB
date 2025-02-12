import csv
import sys
from pathlib import Path
from loguru import logger

def has_minimum_words(title: str, min_words: int = 3) -> bool:
    """Check if title has at least the minimum number of words."""
    # Split by any whitespace and remove empty strings
    words = [w for w in title.split() if w.strip()]
    return len(words) >= min_words

def standardize_csv(input_file: str, output_file: str = None, min_title_words: int = 3):
    """
    Standardize CSV file to use '|' as separator and clean up the data.
    Filters out titles with fewer than min_title_words words.
    
    Args:
        input_file: Path to input CSV file
        output_file: Path to output CSV file. If None, will use input filename with '_standardized' suffix
        min_title_words: Minimum number of words required in title (default: 3)
    """
    if output_file is None:
        input_path = Path(input_file)
        output_file = str(input_path.parent / f"{input_path.stem}_standardized{input_path.suffix}")
    
    try:
        # Read the input CSV - try both | and , as delimiters
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
            delimiter = '|' if '|' in content.split('\n')[0] else ','
            
        with open(input_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            rows = list(reader)
        
        # Clean and standardize the data
        cleaned_rows = []
        skipped_count = 0
        for row in rows:
            title = row['title'].strip()
            # Only include rows with titles that have minimum word count
            if has_minimum_words(title, min_title_words):
                cleaned_row = {
                    'title': title,
                    'url': row['url'].strip(),
                    'category': row['category'].strip()
                }
                cleaned_rows.append(cleaned_row)
            else:
                skipped_count += 1
        
        # Write the output CSV with '|' separator
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['title', 'url', 'category'], delimiter='|')
            writer.writeheader()
            writer.writerows(cleaned_rows)
        
        logger.info(f"Successfully standardized CSV. Output saved to: {output_file}")
        logger.info(f"Processed {len(cleaned_rows)} rows, skipped {skipped_count} rows with fewer than {min_title_words} words")
        
    except Exception as e:
        logger.error(f"Error standardizing CSV: {str(e)}")
        raise

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python standardize_csv.py <input_file> [output_file]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    standardize_csv(input_file, output_file)
