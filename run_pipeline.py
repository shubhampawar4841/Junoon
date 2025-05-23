#!/usr/bin/env python3
"""
Funeral Services Data Collection and Processing Pipeline
for Junoon LLC

This script orchestrates the entire data collection and processing pipeline,
including scraping data from various sources and cleaning/processing the collected data.
"""

import os
import logging
import argparse
from datetime import datetime
from funeral_data_scraper import FuneralDataScraper
from funeral_data_processor import FuneralDataProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pipeline.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Funeral Services Data Pipeline')
    parser.add_argument('--skip-scraping', action='store_true',
                      help='Skip the scraping phase and use existing data')
    parser.add_argument('--raw-data', type=str, default='funeral_services_data.csv',
                      help='Path to raw data file (if skipping scraping)')
    parser.add_argument('--output-dir', type=str, default='output',
                      help='Directory to store output files')
    parser.add_argument('--states', type=str, nargs='+',
                      help='List of states to scrape (e.g., NY CA TX)')
    parser.add_argument('--limit', type=int, default=None,
                      help='Limit number of businesses per source')
    return parser.parse_args()

def setup_output_directory(output_dir):
    """Create output directory if it doesn't exist"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logger.info(f"Created output directory: {output_dir}")

def run_pipeline(args):
    """Run the complete data collection and processing pipeline"""
    try:
        # Setup output directory
        setup_output_directory(args.output_dir)
        
        # Generate timestamp for file naming
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Phase 1: Data Collection
        if not args.skip_scraping:
            logger.info("Starting data collection phase")
            scraper = FuneralDataScraper(states=args.states, limit_per_source=args.limit)
            df = scraper.run_full_scrape()
            
            # Save raw data
            raw_data_file = os.path.join(args.output_dir, f'raw_data_{timestamp}.csv')
            df.to_csv(raw_data_file, index=False)
            logger.info(f"Raw data saved to: {raw_data_file}")
        else:
            logger.info(f"Using existing data from: {args.raw_data}")
            raw_data_file = args.raw_data
        
        # Phase 2: Data Processing
        logger.info("Starting data processing phase")
        processor = FuneralDataProcessor(input_file=raw_data_file)
        cleaned_data = processor.clean_data()
        
        # Phase 3: Generate Output Files
        logger.info("Generating output files")
        
        # Save processed CSV
        processed_csv = os.path.join(args.output_dir, f'processed_data_{timestamp}.csv')
        processor.export_to_csv(processed_csv)
        
        # Save Excel file with multiple sheets
        excel_file = os.path.join(args.output_dir, f'funeral_services_data_{timestamp}.xlsx')
        processor.export_to_excel(excel_file)
        
        # Generate summary report
        summary_file = os.path.join(args.output_dir, f'summary_report_{timestamp}.txt')
        generate_summary_report(cleaned_data, summary_file)
        
        logger.info("Pipeline completed successfully")
        logger.info(f"Output files are in: {args.output_dir}")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        raise

def generate_summary_report(df, output_file):
    """Generate a summary report of the collected data"""
    with open(output_file, 'w') as f:
        f.write("Funeral Services Data Collection Summary\n")
        f.write("=====================================\n\n")
        
        # Total businesses
        f.write(f"Total Businesses: {len(df)}\n\n")
        
        # Breakdown by state
        f.write("Breakdown by State:\n")
        state_counts = df['State'].value_counts()
        for state, count in state_counts.items():
            f.write(f"{state}: {count}\n")
        f.write("\n")
        
        # Breakdown by business type
        f.write("Breakdown by Business Type:\n")
        type_counts = df['Type'].value_counts()
        for biz_type, count in type_counts.items():
            f.write(f"{biz_type}: {count}\n")
        f.write("\n")
        
        # Data completeness
        f.write("Data Completeness:\n")
        total_cells = len(df) * len(df.columns)
        non_empty_cells = df.count().sum()
        completeness = (non_empty_cells / total_cells) * 100
        f.write(f"Overall completeness: {completeness:.1f}%\n")
        
        # Column-wise completeness
        f.write("\nColumn-wise completeness:\n")
        for column in df.columns:
            non_empty = df[column].count()
            percentage = (non_empty / len(df)) * 100
            f.write(f"{column}: {percentage:.1f}%\n")

if __name__ == "__main__":
    args = parse_arguments()
    run_pipeline(args) 