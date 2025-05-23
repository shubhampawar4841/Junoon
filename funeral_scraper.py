import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import csv
import os
from urllib.parse import urlparse
import logging
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("funeral_data_scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger()

# Create a class to hold all the scraping functionality
class FuneralDataScraper:
    def __init__(self):
        self.data = []
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.setup_selenium()
        
    def setup_selenium(self):
        """Set up Selenium WebDriver with appropriate options"""
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument(f'user-agent={self.headers["User-Agent"]}')
        self.driver = webdriver.Chrome(options=options)
        
    def scrape_funeralwise(self):
        """Scrape funeral home data from funeralwise.com"""
        logger.info("Starting to scrape funeralwise.com")
        
        # Base URL for the directory
        base_url = "https://www.funeralwise.com/funeral-homes/directory/"
        
        try:
            # Get the list of states first
            self.driver.get(base_url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "ul.directory-list li a"))
            )
            
            # Extract state links
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            state_links = soup.select("ul.directory-list li a")
            
            # Process first 3 states for testing (remove this limit for production)
            for state_link in state_links[:3]:  # Testing with first 3 states
                state_url = "https://www.funeralwise.com" + state_link['href']
                state_name = state_link.text.strip()
                logger.info(f"Processing state: {state_name}")
                
                # Visit the state page
                self.driver.get(state_url)
                time.sleep(2)  # Allow page to load
                
                # Extract city links
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                city_links = soup.select("ul.directory-list li a")
                
                # Process first 2 cities per state for testing
                for city_link in city_links[:2]:  # Testing with first 2 cities
                    city_url = "https://www.funeralwise.com" + city_link['href']
                    city_name = city_link.text.strip()
                    logger.info(f"Processing city: {city_name}")
                    
                    # Visit the city page
                    self.driver.get(city_url)
                    time.sleep(2)  # Allow page to load
                    
                    # Extract funeral home listings
                    soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                    business_listings = soup.select("div.listing")
                    
                    for listing in business_listings:
                        try:
                            business_name = listing.select_one("h3 a").text.strip()
                            
                            # Extract address - typically in the second paragraph
                            address_elem = listing.select_one("p:nth-of-type(1)")
                            address = address_elem.text.strip() if address_elem else "N/A"
                            
                            # Extract phone number - typically in the third paragraph
                            phone_elem = listing.select_one("p:nth-of-type(2)")
                            phone = phone_elem.text.strip() if phone_elem else "N/A"
                            
                            # Extract website if available
                            website_elem = listing.select_one("a.website")
                            website = website_elem['href'] if website_elem else "N/A"
                            
                            # Business type classification
                            business_type = self.classify_business_type(business_name, website)
                            
                            # Create data entry
                            entry = {
                                'Business Name': business_name,
                                'Type': business_type,
                                'Address': address,
                                'Phone': phone,
                                'Website': website,
                                'Email': "N/A",  # Need to visit website to extract email
                                'Contact Person': "N/A",  # Often requires deeper website scraping
                                'Social Media': self.extract_social_media(website),
                                'Size': "N/A",  # Requires additional research
                                'Rating': "N/A",  # Removed Google Maps dependency
                                'State': state_name,
                                'City': city_name,
                                'Source': "funeralwise.com"
                            }
                            
                            self.data.append(entry)
                            logger.info(f"Added: {business_name}")
                            
                        except Exception as e:
                            logger.error(f"Error processing listing: {str(e)}")
                
        except Exception as e:
            logger.error(f"Error scraping funeralwise.com: {str(e)}")
            
        logger.info(f"Completed funeralwise.com scraping. Total entries: {len(self.data)}")
        return self.data
    
    def scrape_nfda(self):
        """Scrape funeral home data from nfda.org"""
        logger.info("Starting to scrape nfda.org")
        
        # The NFDA site likely requires form submission to search
        # This is a simplified version that would need expansion
        try:
            self.driver.get("https://nfda.org/funeral-director-finder")
            
            # For testing purposes, search for a specific state
            # In a full implementation, we'd loop through all states
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "state"))
            )
            
            # Select a state (would need to iterate through all states in production)
            # This is conceptual and would need adjustment based on the actual form structure
            self.driver.find_element(By.ID, "state").send_keys("New York")
            self.driver.find_element(By.ID, "search-button").click()
            
            time.sleep(2)  # Wait for results to load
            
            # Parse results
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            results = soup.select("div.result-item")  # Adjust selector based on actual structure
            
            for result in results:
                try:
                    business_name = result.select_one("h3").text.strip()
                    address = result.select_one("p.address").text.strip()
                    phone = result.select_one("p.phone").text.strip()
                    website = result.select_one("a.website")['href'] if result.select_one("a.website") else "N/A"
                    
                    entry = {
                        'Business Name': business_name,
                        'Type': self.classify_business_type(business_name, website),
                        'Address': address,
                        'Phone': phone,
                        'Website': website,
                        'Email': "N/A",
                        'Contact Person': "N/A",
                        'Social Media': self.extract_social_media(website),
                        'Size': "N/A",
                        'Rating': "N/A",  # Removed Google Maps dependency
                        'State': "New York",  # Would be dynamic in full implementation
                        'City': self.extract_city(address),
                        'Source': "nfda.org"
                    }
                    
                    self.data.append(entry)
                    logger.info(f"Added: {business_name}")
                    
                except Exception as e:
                    logger.error(f"Error processing NFDA result: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error scraping nfda.org: {str(e)}")
            
        logger.info(f"Completed nfda.org scraping. Total entries: {len(self.data)}")
        return self.data
    
    def scrape_yelp(self):
        """Scrape funeral home data from Yelp"""
        logger.info("Starting to scrape Yelp")
        
        # Base search URL for funeral homes
        base_url = "https://www.yelp.com/search?find_desc=Funeral+Services&find_loc="
        
        # List of major cities to search in - would expand for full implementation
        cities = [
            "New York, NY",
            "Los Angeles, CA",
            "Chicago, IL"
        ]
        
        try:
            for city in cities:
                logger.info(f"Processing Yelp search for: {city}")
                search_url = base_url + city.replace(" ", "+")
                
                self.driver.get(search_url)
                time.sleep(3)  # Allow page to load and possible AJAX content
                
                # Scroll to load more results
                for _ in range(3):  # Scroll a few times to load more results
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)
                
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                business_listings = soup.select("div.businessName__09f24__EYSZE")
                
                # Extract business data from each listing
                for listing in business_listings:
                    try:
                        name_elem = listing.select_one("a.businessName__09f24__EYSZE span")
                        business_name = name_elem.text.strip() if name_elem else "N/A"
                        
                        # Get the business URL to visit its detailed page
                        link_elem = listing.select_one("a.businessName__09f24__EYSZE")
                        if link_elem and 'href' in link_elem.attrs:
                            business_url = "https://www.yelp.com" + link_elem['href']
                            
                            # Visit the business page for more details
                            self.driver.get(business_url)
                            time.sleep(2)
                            
                            detail_soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                            
                            # Extract address
                            address_elem = detail_soup.select_one("address")
                            address = address_elem.text.strip() if address_elem else "N/A"
                            
                            # Extract phone
                            phone_elem = detail_soup.select_one("p.phone")
                            phone = phone_elem.text.strip() if phone_elem else "N/A"
                            
                            # Extract website if available
                            website_elem = detail_soup.select_one("a.website-link")
                            website = website_elem['href'] if website_elem else "N/A"
                            
                            # Extract rating
                            rating_elem = detail_soup.select_one("div.rating")
                            rating = rating_elem.text.strip() if rating_elem else "N/A"
                            
                            # Create entry
                            entry = {
                                'Business Name': business_name,
                                'Type': self.classify_business_type(business_name, website),
                                'Address': address,
                                'Phone': phone,
                                'Website': website,
                                'Email': "N/A",
                                'Contact Person': "N/A",
                                'Social Media': self.extract_social_media(website),
                                'Size': "N/A",
                                'Rating': rating,
                                'State': city.split(", ")[1],
                                'City': city.split(", ")[0],
                                'Source': "Yelp"
                            }
                            
                            self.data.append(entry)
                            logger.info(f"Added from Yelp: {business_name}")
                    
                    except Exception as e:
                        logger.error(f"Error processing Yelp listing: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error scraping Yelp: {str(e)}")
            
        logger.info(f"Completed Yelp scraping. Total entries: {len(self.data)}")
        return self.data
    
    def scrape_yellowpages(self):
        """Scrape funeral home data from YellowPages"""
        logger.info("Starting to scrape YellowPages")
        
        base_url = "https://www.yellowpages.com/search?search_terms=funeral+homes&geo_location_terms="
        cities = [
            "New York, NY",
            "Los Angeles, CA",
            "Chicago, IL",
            "Houston, TX",
            "Phoenix, AZ"
        ]
        
        try:
            for city in cities:
                logger.info(f"Processing YellowPages search for: {city}")
                search_url = base_url + city.replace(" ", "+")
                
                self.driver.get(search_url)
                time.sleep(3)
                
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                business_listings = soup.select("div.result")
                
                for listing in business_listings:
                    try:
                        # Basic info
                        name_elem = listing.select_one("a.business-name")
                        business_name = name_elem.text.strip() if name_elem else "N/A"
                        
                        # Address
                        address_elem = listing.select_one("div.street-address")
                        address_line1 = address_elem.text.strip() if address_elem else ""
                        locality_elem = listing.select_one("div.locality")
                        locality = locality_elem.text.strip() if locality_elem else ""
                        address = f"{address_line1}, {locality}"
                        
                        # Phone
                        phone_elem = listing.select_one("div.phones")
                        phone = phone_elem.text.strip() if phone_elem else "N/A"
                        
                        # Website
                        website_elem = listing.select_one("a.track-visit-website")
                        website = website_elem['href'] if website_elem and 'href' in website_elem.attrs else "N/A"
                        
                        # Get additional info
                        email = self.extract_email_from_website(website)
                        social_media = self.extract_social_media(website)
                        size = self.get_business_size(business_name, website)
                        
                        # Business type classification
                        business_type = self.classify_business_type(business_name, website)
                        
                        # Create entry
                        entry = {
                            'Business Name': business_name,
                            'Type': business_type,
                            'Address': address,
                            'Phone': phone,
                            'Email': email,
                            'Website': website,
                            'Contact Person': "N/A",  # Would need deeper website scraping
                            'Social Media': social_media,
                            'Size': size,
                            'Rating': "N/A",  # Removed Google Maps dependency
                            'State': city.split(", ")[1],
                            'City': city.split(", ")[0],
                            'Source': "YellowPages"
                        }
                        
                        self.data.append(entry)
                        logger.info(f"Added from YellowPages: {business_name}")
                        
                    except Exception as e:
                        logger.error(f"Error processing YellowPages listing: {str(e)}")
                        
        except Exception as e:
            logger.error(f"Error scraping YellowPages: {str(e)}")
            
        logger.info(f"Completed YellowPages scraping. Total entries: {len(self.data)}")
        return self.data
    
    def classify_business_type(self, business_name, website):
        """Determine the type of funeral business based on name and website"""
        name_lower = business_name.lower()
        website_lower = website.lower() if website != "N/A" else ""
        
        # Check for cremation services
        if "cremation" in name_lower or "crematory" in name_lower or "cremation" in website_lower:
            return "Cremation Service"
        
        # Check for memorial services
        elif "memorial" in name_lower or "memorial" in website_lower:
            if "funeral" in name_lower or "funeral" in website_lower:
                return "Hybrid (Funeral & Memorial)"
            return "Memorial Service"
        
        # Check for mortuary
        elif "mortuary" in name_lower or "mortuary" in website_lower:
            return "Mortuary"
        
        # Check for funeral planners
        elif "planner" in name_lower or "planning" in name_lower:
            return "Funeral Planner"
        
        # Default to funeral home
        else:
            return "Funeral Home"
    
    def extract_city(self, address):
        """Extract city from an address string"""
        # Simple pattern to extract city (would need refinement)
        city_match = re.search(r'([A-Za-z\s]+),\s*[A-Z]{2}', address)
        if city_match:
            return city_match.group(1).strip()
        return "N/A"
    
    def extract_email_from_website(self, website):
        """Extract email from a business website"""
        if website == "N/A":
            return "N/A"
            
        try:
            self.driver.get(website)
            time.sleep(2)  # Allow page to load
            
            # Look for email patterns in the page source
            email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            emails = re.findall(email_pattern, self.driver.page_source)
            
            # Return first valid email found
            return emails[0] if emails else "N/A"
            
        except Exception as e:
            logger.error(f"Error extracting email from {website}: {str(e)}")
            return "N/A"
    
    def extract_social_media(self, website):
        """Extract social media links from a business website"""
        if website == "N/A":
            return "N/A"
            
        social_media = {
            'facebook': None,
            'twitter': None,
            'instagram': None,
            'linkedin': None
        }
        
        try:
            self.driver.get(website)
            time.sleep(2)
            
            # Common social media patterns
            patterns = {
                'facebook': r'facebook\.com/[^"\']+',
                'twitter': r'twitter\.com/[^"\']+',
                'instagram': r'instagram\.com/[^"\']+',
                'linkedin': r'linkedin\.com/[^"\']+'
            }
            
            page_source = self.driver.page_source
            
            for platform, pattern in patterns.items():
                match = re.search(pattern, page_source)
                if match:
                    social_media[platform] = match.group(0)
            
            # Filter out None values and join remaining links
            active_links = [link for link in social_media.values() if link]
            return ", ".join(active_links) if active_links else "N/A"
            
        except Exception as e:
            logger.error(f"Error extracting social media from {website}: {str(e)}")
            return "N/A"
    
    def get_business_size(self, business_name, website):
        """Estimate business size based on available information"""
        size_info = "N/A"
        
        try:
            if website != "N/A":
                self.driver.get(website)
                time.sleep(2)
                
                # Look for size indicators in the page
                size_indicators = [
                    r'(\d+)\s*(?:locations|branches|offices)',
                    r'(\d+)\s*(?:employees|staff)',
                    r'founded in (\d{4})',
                    r'established in (\d{4})'
                ]
                
                page_text = self.driver.page_source.lower()
                
                for pattern in size_indicators:
                    match = re.search(pattern, page_text)
                    if match:
                        if 'location' in pattern or 'branch' in pattern:
                            size_info = f"{match.group(1)} locations"
                        elif 'employee' in pattern:
                            size_info = f"{match.group(1)} employees"
                        elif 'founded' in pattern or 'established' in pattern:
                            size_info = f"Established {match.group(1)}"
                        break
                        
        except Exception as e:
            logger.error(f"Error getting business size for {business_name}: {str(e)}")
            
        return size_info
    
    def remove_duplicates(self):
        """Remove duplicate entries based on business name and address"""
        logger.info("Removing duplicate entries")
        
        df = pd.DataFrame(self.data)
        df['dedup_key'] = df['Business Name'] + '|' + df['Address']
        df_deduped = df.drop_duplicates(subset=['dedup_key'])
        df_deduped = df_deduped.drop('dedup_key', axis=1)
        
        self.data = df_deduped.to_dict('records')
        logger.info(f"After deduplication: {len(self.data)} entries")
        return self.data
    
    def export_to_csv(self, filename="funeral_services_data.csv"):
        """Export the collected data to CSV"""
        logger.info(f"Exporting data to {filename}")
        
        df = pd.DataFrame(self.data)
        df.to_csv(filename, index=False)
        
        logger.info(f"Data exported successfully to {filename}")
        return filename
    
    def run_full_scrape(self):
        """Run the complete scraping process"""
        try:
            # Run each scraper
            self.scrape_funeralwise()
            self.scrape_nfda()
            self.scrape_yelp()
            self.scrape_yellowpages()
            
            # Process and clean data
            self.remove_duplicates()
            
            # Export data
            csv_filename = self.export_to_csv()
            
            logger.info(f"Full scrape completed. Data saved to {csv_filename}")
            logger.info(f"Total entries collected: {len(self.data)}")
            
            return self.data, csv_filename
            
        except Exception as e:
            logger.error(f"Error in full scrape process: {str(e)}")
            
        finally:
            # Clean up
            self.driver.quit()

# Main execution
if __name__ == "__main__":
    scraper = FuneralDataScraper()
    data, filename = scraper.run_full_scrape()
    print(f"Scraping completed. Collected {len(data)} entries. Data saved to {filename}") 