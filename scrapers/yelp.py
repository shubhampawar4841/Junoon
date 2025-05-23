from .base_scraper import BaseScraper
import re

class YelpScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.yelp.com/search"
        self.states = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", 
                      "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", 
                      "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", 
                      "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", 
                      "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"]
        self.search_terms = ["funeral homes", "cremation services", "memorial services"]

    def scrape(self):
        all_data = []
        for state in self.states:
            for term in self.search_terms:
                search_url = f"{self.base_url}?find_desc={term}&find_loc={state}"
                html = self.get_page(search_url)
                if html:
                    soup = self.parse_page(html)
                    if soup:
                        listings = soup.find_all('div', class_='businessName')
                        for listing in listings:
                            data = self.extract_listing_data(listing)
                            if data:
                                data['State'] = state
                                all_data.append(data)
                self.delay()
        return all_data

    def extract_listing_data(self, listing):
        try:
            name_elem = listing.find('a', class_='businessName')
            address_elem = listing.find('address')
            phone_elem = listing.find('span', class_='phone')
            rating_elem = listing.find('div', class_='rating')
            website_elem = listing.find('a', class_='website')

            return {
                'Business Name': self.clean_text(name_elem.text) if name_elem else "N/A",
                'Type': 'Funeral Home',
                'Address': self.clean_text(address_elem.text) if address_elem else "N/A",
                'Phone': self.extract_phone(phone_elem.text) if phone_elem else "N/A",
                'Website': website_elem['href'] if website_elem else "N/A",
                'Rating': self.clean_text(rating_elem.text) if rating_elem else "N/A",
                'Source': 'Yelp'
            }
        except Exception as e:
            print(f"Error extracting listing data: {str(e)}")
            return None 