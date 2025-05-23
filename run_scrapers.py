import pandas as pd
from scrapers.funeralwise import FuneralWiseScraper
from scrapers.nfda import NFDAScraper
from scrapers.yelp import YelpScraper
from scrapers.yellowpages import YellowPagesScraper
import time
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)

def run_scrapers():
    # Initialize scrapers
    scrapers = [
        FuneralWiseScraper(),
        NFDAScraper(),
        YelpScraper(),
        YellowPagesScraper()
    ]

    # Collect data from all sources
    all_data = []
    for scraper in scrapers:
        scraper_name = scraper.__class__.__name__
        logging.info(f"Starting {scraper_name} scraper...")
        try:
            data = scraper.scrape()
            if data:
                all_data.extend(data)
                logging.info(f"Found {len(data)} listings from {scraper_name}")
            else:
                logging.warning(f"No data found from {scraper_name}")
        except Exception as e:
            logging.error(f"Error with {scraper_name}: {str(e)}")
        time.sleep(5)  # Delay between scrapers

    if not all_data:
        logging.error("No data collected from any scraper")
        return

    # Convert to DataFrame
    df = pd.DataFrame(all_data)

    # Remove duplicates based on business name and address
    initial_count = len(df)
    df = df.drop_duplicates(subset=['Business Name', 'Address'])
    final_count = len(df)
    logging.info(f"Removed {initial_count - final_count} duplicate entries")

    # Save to CSV
    output_file = 'funeral_services_data.csv'
    df.to_csv(output_file, index=False)
    logging.info(f"Saved {len(df)} unique listings to {output_file}")

    # Print summary
    print("\nScraping Summary:")
    print(f"Total unique listings: {len(df)}")
    print(f"Sources: {df['Source'].value_counts().to_dict()}")
    print(f"States covered: {df['State'].value_counts().to_dict()}")

if __name__ == "__main__":
    run_scrapers()