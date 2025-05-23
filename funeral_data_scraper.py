#!/usr/bin/env python3
"""
Funeral Services Data Scraper
for Junoon LLC

This module contains the FuneralDataScraper class for collecting funeral service
provider data from various online sources.
"""

import logging
import pandas as pd
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import random
from typing import List, Dict, Optional, Union

# Configure logging
logger = logging.getLogger(__name__)

class FuneralDataScraper:
    def __init__(self, states: Optional[List[str]] = None, limit_per_source: Optional[int] = None):
        """
        Initialize the funeral data scraper
        
        Args:
            states: List of state abbreviations to limit scraping to
            limit_per_source: Maximum number of businesses to collect per source
        """
        self.states = [state.upper() for state in states] if states else None
        self.limit_per_source = limit_per_source
        self.data = []
        
        # Initialize Selenium WebDriver
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        
        logger.info("FuneralDataScraper initialized")
    
    def run_full_scrape(self):
        """Run scraping from all sources"""
        logger.info("Starting full data collection")
        
        try:
            # Scrape from each source
            self.scrape_funeralwise()
            self.scrape_nfda()
            self.scrape_yelp()
            self.scrape_yellowpages()
            
            # Convert to DataFrame
            self.df = pd.DataFrame(self.data)
            
            logger.info(f"Full scraping complete. Collected {len(self.data)} entries")
            return self.df
            
        except Exception as e:
            logger.error(f"Error in full scraping: {str(e)}")
            raise
    
    def scrape_funeralwise(self):
        """Scrape data from funeralwise.com"""
        logger.info("Scraping funeralwise.com")
        
        try:
            base_url = "https://www.funeralwise.com/funeral-homes/"
            
            # Get list of states if not specified
            states_to_scrape = self.states if self.states else self._get_all_states()
            
            for state in states_to_scrape:
                state_url = f"{base_url}{state.lower()}/"
                logger.info(f"Scraping state: {state}")
                
                try:
                    response = requests.get(state_url)
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Find funeral home listings
                    listings = soup.find_all('div', class_='funeral-home-listing')
                    
                    for listing in listings:
                        try:
                            name = listing.find('h3').text.strip()
                            address = listing.find('div', class_='address').text.strip()
                            phone = listing.find('div', class_='phone').text.strip()
                            website = listing.find('a', class_='website')['href'] if listing.find('a', class_='website') else None
                            
                            self.data.append({
                                'Business Name': name,
                                'Address': address,
                                'Phone': phone,
                                'Website': website,
                                'Source': 'Funeralwise',
                                'State': state
                            })
                            
                            # Check limit
                            if self.limit_per_source and len([d for d in self.data if d['Source'] == 'Funeralwise']) >= self.limit_per_source:
                                break
                                
                        except Exception as e:
                            logger.warning(f"Error processing funeralwise listing: {str(e)}")
                            continue
                    
                    # Random delay between states
                    time.sleep(random.uniform(2, 5))
                    
                except Exception as e:
                    logger.error(f"Error scraping funeralwise state {state}: {str(e)}")
                    continue
            
            logger.info(f"Funeralwise scraping complete. Collected {len([d for d in self.data if d['Source'] == 'Funeralwise'])} entries")
            
        except Exception as e:
            logger.error(f"Error in funeralwise scraping: {str(e)}")
    
    def scrape_nfda(self):
        """Scrape data from nfda.org"""
        logger.info("Scraping nfda.org")
        
        try:
            base_url = "https://www.nfda.org/find-a-funeral-home"
            
            # Get list of states if not specified
            states_to_scrape = self.states if self.states else self._get_all_states()
            
            for state in states_to_scrape:
                state_url = f"{base_url}?state={state}"
                logger.info(f"Scraping state: {state}")
                
                try:
                    self.driver.get(state_url)
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "funeral-home-listing"))
                    )
                    
                    # Find funeral home listings
                    listings = self.driver.find_elements(By.CLASS_NAME, "funeral-home-listing")
                    
                    for listing in listings:
                        try:
                            name = listing.find_element(By.CLASS_NAME, "name").text.strip()
                            address = listing.find_element(By.CLASS_NAME, "address").text.strip()
                            phone = listing.find_element(By.CLASS_NAME, "phone").text.strip()
                            website = listing.find_element(By.CLASS_NAME, "website").get_attribute("href")
                            
                            self.data.append({
                                'Business Name': name,
                                'Address': address,
                                'Phone': phone,
                                'Website': website,
                                'Source': 'NFDA',
                                'State': state
                            })
                            
                            # Check limit
                            if self.limit_per_source and len([d for d in self.data if d['Source'] == 'NFDA']) >= self.limit_per_source:
                                break
                                
                        except Exception as e:
                            logger.warning(f"Error processing NFDA listing: {str(e)}")
                            continue
                    
                    # Random delay between states
                    time.sleep(random.uniform(2, 5))
                    
                except Exception as e:
                    logger.error(f"Error scraping NFDA state {state}: {str(e)}")
                    continue
            
            logger.info(f"NFDA scraping complete. Collected {len([d for d in self.data if d['Source'] == 'NFDA'])} entries")
            
        except Exception as e:
            logger.error(f"Error in NFDA scraping: {str(e)}")
    
    def scrape_yelp(self):
        """Scrape data from Yelp"""
        logger.info("Scraping Yelp")
        
        try:
            # Get list of states if not specified
            states_to_scrape = self.states if self.states else self._get_all_states()
            
            for state in states_to_scrape:
                # Search in major cities of the state
                cities = self._get_major_cities(state)
                
                for city in cities:
                    search_url = f"https://www.yelp.com/search?find_desc=Funeral+Homes&find_loc={city}%2C+{state}"
                    logger.info(f"Scraping city: {city}, {state}")
                    
                    try:
                        self.driver.get(search_url)
                        WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.CLASS_NAME, "businessName"))
                        )
                        
                        # Find business listings
                        listings = self.driver.find_elements(By.CLASS_NAME, "businessName")
                        
                        for listing in listings:
                            try:
                                name = listing.find_element(By.CLASS_NAME, "name").text.strip()
                                address = listing.find_element(By.CLASS_NAME, "address").text.strip()
                                phone = listing.find_element(By.CLASS_NAME, "phone").text.strip()
                                website = listing.find_element(By.CLASS_NAME, "website").get_attribute("href")
                                rating = listing.find_element(By.CLASS_NAME, "rating").get_attribute("aria-label")
                                
                                self.data.append({
                                    'Business Name': name,
                                    'Address': address,
                                    'Phone': phone,
                                    'Website': website,
                                    'Google Rating': rating,
                                    'Source': 'Yelp',
                                    'State': state,
                                    'City': city
                                })
                                
                                # Check limit
                                if self.limit_per_source and len([d for d in self.data if d['Source'] == 'Yelp']) >= self.limit_per_source:
                                    break
                                    
                            except Exception as e:
                                logger.warning(f"Error processing Yelp listing: {str(e)}")
                                continue
                        
                        # Random delay between cities
                        time.sleep(random.uniform(2, 5))
                        
                    except Exception as e:
                        logger.error(f"Error scraping Yelp city {city}: {str(e)}")
                        continue
            
            logger.info(f"Yelp scraping complete. Collected {len([d for d in self.data if d['Source'] == 'Yelp'])} entries")
            
        except Exception as e:
            logger.error(f"Error in Yelp scraping: {str(e)}")
    
    def scrape_yellowpages(self):
        """Scrape data from YellowPages"""
        logger.info("Scraping YellowPages")
        
        try:
            # Get list of states if not specified
            states_to_scrape = self.states if self.states else self._get_all_states()
            
            for state in states_to_scrape:
                # Search in major cities of the state
                cities = self._get_major_cities(state)
                
                for city in cities:
                    search_url = f"https://www.yellowpages.com/search?search_terms=Funeral+Homes&geo_location_terms={city}%2C+{state}"
                    logger.info(f"Scraping city: {city}, {state}")
                    
                    try:
                        self.driver.get(search_url)
                        WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.CLASS_NAME, "result"))
                        )
                        
                        # Find business listings
                        listings = self.driver.find_elements(By.CLASS_NAME, "result")
                        
                        for listing in listings:
                            try:
                                name = listing.find_element(By.CLASS_NAME, "business-name").text.strip()
                                address = listing.find_element(By.CLASS_NAME, "street-address").text.strip()
                                phone = listing.find_element(By.CLASS_NAME, "phone").text.strip()
                                website = listing.find_element(By.CLASS_NAME, "track-visit-website").get_attribute("href")
                                
                                self.data.append({
                                    'Business Name': name,
                                    'Address': address,
                                    'Phone': phone,
                                    'Website': website,
                                    'Source': 'YellowPages',
                                    'State': state,
                                    'City': city
                                })
                                
                                # Check limit
                                if self.limit_per_source and len([d for d in self.data if d['Source'] == 'YellowPages']) >= self.limit_per_source:
                                    break
                                    
                            except Exception as e:
                                logger.warning(f"Error processing YellowPages listing: {str(e)}")
                                continue
                        
                        # Random delay between cities
                        time.sleep(random.uniform(2, 5))
                        
                    except Exception as e:
                        logger.error(f"Error scraping YellowPages city {city}: {str(e)}")
                        continue
            
            logger.info(f"YellowPages scraping complete. Collected {len([d for d in self.data if d['Source'] == 'YellowPages'])} entries")
            
        except Exception as e:
            logger.error(f"Error in YellowPages scraping: {str(e)}")
    
    def _get_all_states(self) -> List[str]:
        """Get list of all US state abbreviations"""
        return [
            'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
            'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
            'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
            'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
            'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
        ]
    
    def _get_major_cities(self, state: str) -> List[str]:
        """Get list of major cities for a given state"""
        # This is a simplified version - you might want to expand this
        major_cities = {
            'CA': ['Los Angeles', 'San Francisco', 'San Diego', 'Sacramento'],
            'NY': ['New York City', 'Buffalo', 'Rochester', 'Syracuse'],
            'TX': ['Houston', 'Dallas', 'Austin', 'San Antonio'],
            'FL': ['Miami', 'Orlando', 'Tampa', 'Jacksonville'],
            # Add more states and their major cities
        }
        return major_cities.get(state, [])
    
    def export_to_csv(self, output_file: str):
        """Export collected data to CSV file"""
        try:
            df = pd.DataFrame(self.data)
            df.to_csv(output_file, index=False)
            logger.info(f"Data exported to {output_file}")
        except Exception as e:
            logger.error(f"Error exporting data: {str(e)}")
            raise
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        try:
            self.driver.quit()
        except:
            pass 