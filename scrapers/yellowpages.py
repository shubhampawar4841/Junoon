from .base_scraper import BaseScraper
import re
from bs4 import BeautifulSoup
import time

class YellowPagesScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.yellowpages.com/search?search_terms=funeral+homes&geo_location_terms="
        # Using a few cities for demonstration. Can expand this list.
        self.cities = [
            "New York, NY",
            "Los Angeles, CA", 
            "Chicago, IL",
            "Houston, TX",
            "Phoenix, AZ"
        ]

    def scrape(self):
        all_data = []
        for city in self.cities:
            search_url = self.base_url + city.replace(" ", "+")
            print(f"Scraping YellowPages for {city}...")
            html = self.get_page(search_url)
            if html:
                soup = self.parse_page(html)
                if soup:
                    # Find business listings - Updated based on typical YP structure
                    listings = soup.select("div.result, div.search-results div.v-card, article.result, div.organic")
                    
                    for listing in listings:
                        # Get business page URL for detailed info
                        business_url = self.extract_business_url(listing)
                        if business_url:
                            print(f"  Fetching details from: {business_url}")
                            business_html = self.get_page(business_url)
                            if business_html:
                                business_soup = self.parse_page(business_html)
                                if business_soup:
                                    data = self.extract_business_details(business_soup)
                                    if data and data.get('Business Name') != "N/A":
                                        data['City'] = city.split(', ')[0].strip()
                                        data['State'] = city.split(', ')[1].strip()
                                        data['Source'] = 'YellowPages'
                                        all_data.append(data)
                        
                        # Also try to extract basic data from search results
                        basic_data = self.extract_listing_data(listing)
                        if basic_data and basic_data.get('Business Name') != "N/A":
                            basic_data['City'] = city.split(', ')[0].strip()
                            basic_data['State'] = city.split(', ')[1].strip()
                            basic_data['Source'] = 'YellowPages'
                            all_data.append(basic_data)
                        
                        self.delay(1)  # Short delay between requests
            
            self.delay(2)  # Longer delay between cities
        
        return all_data

    def extract_business_url(self, listing):
        """Extract the URL to the individual business page"""
        try:
            # Look for business name link
            business_link = listing.select_one("h3 a, h2 a, a.business-name, .n a")
            if business_link and 'href' in business_link.attrs:
                href = business_link['href']
                if href.startswith('/'):
                    return f"https://www.yellowpages.com{href}"
                elif href.startswith('http'):
                    return href
            return None
        except:
            return None

    def extract_business_details(self, soup):
        """Extract detailed info from individual business page"""
        try:
            # Initialize data
            data = {
                'Business Name': "N/A",
                'Type': "Funeral Service", 
                'Address': "N/A",
                'Phone': "N/A",
                'Email': "N/A",
                'Website': "N/A",
                'Contact Person': "N/A",
                'Social Media': "N/A",
                'Size': "N/A",
                'Rating': "N/A",
                'Services': "N/A",
                'Payment Methods': "N/A",
                'Neighborhoods': "N/A",
                'Description': "N/A"
            }

            # Extract Business Name
            name_selectors = ["h1", ".business-name", "h1.fn", ".fn"]
            for selector in name_selectors:
                name_elem = soup.select_one(selector)
                if name_elem:
                    data['Business Name'] = self.clean_text(name_elem.get_text())
                    break

            # Extract Phone Number
            phone_selectors = [".phones", ".phone", ".business-phone"]
            for selector in phone_selectors:
                phone_elem = soup.select_one(selector)
                if phone_elem:
                    phone_text = phone_elem.get_text()
                    data['Phone'] = self.extract_phone(phone_text)
                    if data['Phone'] != "N/A":
                        break

            # Extract Address
            address_parts = []
            street = soup.select_one(".street-address")
            locality = soup.select_one(".locality")
            region = soup.select_one(".region")  
            postal = soup.select_one(".postal-code")
            
            if street: address_parts.append(self.clean_text(street.get_text()))
            if locality: address_parts.append(self.clean_text(locality.get_text()))
            if region: address_parts.append(self.clean_text(region.get_text()))
            if postal: address_parts.append(self.clean_text(postal.get_text()))
            
            if address_parts:
                data['Address'] = ", ".join(address_parts)

            # Extract Email - Based on your HTML structure
           email_elem = soup.select_one("a.email-business, .email-link, [href^='mailto:']")
if email_elem and 'href' in email_elem.attrs:
    data['Email'] = email_elem['href'].replace('mailto:', '')

            # Extract Website - Based on your HTML structure  
            website_elem = soup.select_one("dd.weblinks a")
            if website_elem and 'href' in website_elem.attrs:
                data['Website'] = website_elem['href']

            # Extract BBB Rating - Based on your HTML structure
            rating_elem = soup.select_one("dd.bbb-rating span.bbb-no-link")
            if rating_elem:
                data['Rating'] = self.clean_text(rating_elem.get_text())

            # Extract Services - Based on your HTML structure
            services_elem = soup.select_one("dd.features-services")
            if services_elem:
                service_spans = services_elem.select("span")
                if service_spans:
                    services = [span.get_text().strip().rstrip(',') for span in service_spans]
                    data['Services'] = ", ".join(services[:15])  # Limit to first 15
                    data['Size'] = len(services)

            # Extract Payment Methods - Based on your HTML structure
            payment_elem = soup.select_one("dd.payment")
            if payment_elem:
                data['Payment Methods'] = self.clean_text(payment_elem.get_text())

            # Extract Neighborhoods - Based on your HTML structure
            neighborhoods_elem = soup.select_one("dd.neighborhoods")
            if neighborhoods_elem:
                neighborhood_links = neighborhoods_elem.select("a")
                if neighborhood_links:
                    neighborhoods = [a.get_text().strip() for a in neighborhood_links]
                    data['Neighborhoods'] = ", ".join(neighborhoods)

            # Extract Social Media - Based on your HTML structure
            social_elem = soup.select_one("dd.social-links")
            if social_elem:
                social_links = []
                for link in social_elem.select("a[href]"):
                    href = link['href']
                    if any(domain in href.lower() for domain in ['facebook.com', 'twitter.com', 'instagram.com', 'linkedin.com', 'yelp.com', 'foursquare.com']):
                        social_links.append(href)
                if social_links:
                    data['Social Media'] = " | ".join(social_links)

            # Extract General Info/Description
            general_info_elem = soup.select_one("dd.general-info")
            if general_info_elem:
                description = self.clean_text(general_info_elem.get_text())
                data['Description'] = description[:300] + "..." if len(description) > 300 else description

            # Extract Categories for Type
            categories_elem = soup.select_one("dd.categories")
            if categories_elem:
                category_links = categories_elem.select("a")
                if category_links:
                    data['Type'] = self.clean_text(category_links[0].get_text())

            return data

        except Exception as e:
            print(f"Error extracting business details: {str(e)}")
            return None

    def extract_listing_data(self, listing):
        """Extract basic data from search results listing"""
        try:
            data = {
                'Business Name': "N/A",
                'Type': "Funeral Service",
                'Address': "N/A", 
                'Phone': "N/A",
                'Email': "N/A",
                'Website': "N/A",
                'Contact Person': "N/A",
                'Social Media': "N/A",
                'Size': "N/A",
                'Rating': "N/A",
                'Services': "N/A",
                'Payment Methods': "N/A",
                'Neighborhoods': "N/A",
                'Description': "N/A"
            }

            # Extract Business Name from search results
            name_elem = listing.select_one("h3 a, h2 a, a.business-name, .n a")
            if name_elem:
                data['Business Name'] = self.clean_text(name_elem.get_text())

            # Extract Phone from search results
            phone_elem = listing.select_one(".phones, .phone")
            if phone_elem:
                data['Phone'] = self.extract_phone(phone_elem.get_text())

            # Extract Address from search results
            address_elem = listing.select_one(".adr, .address")
            if address_elem:
                data['Address'] = self.clean_text(address_elem.get_text())

            # Extract Rating from search results
            rating_elem = listing.select_one(".rating, .stars")
            if rating_elem:
                data['Rating'] = self.clean_text(rating_elem.get_text())

            return data

        except Exception as e:
            print(f"Error extracting listing data: {str(e)}")
            return None

    def extract_phone(self, text):
        """Extract phone number from text using regex"""
        if not text:
            return "N/A"
        
        # Remove common non-phone text
        text = re.sub(r'Phone|phone|Tel|tel|Call|call', '', text)
        
        # Common phone number patterns
        phone_patterns = [
            r'\(\d{3}\)\s*\d{3}[-.\s]?\d{4}',     # (123) 456-7890
            r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b', # 123-456-7890 or 123.456.7890
            r'\b\d{10}\b',                        # 1234567890
            r'\+1[-.\s]?\d{3}[-.\s]?\d{3}[-.\s]?\d{4}', # +1-123-456-7890
        ]
        
        for pattern in phone_patterns:
            match = re.search(pattern, text)
            if match:
                phone = match.group(0).strip()
                # Clean up the phone number
                phone = re.sub(r'[^\d\(\)\-\.\s\+]', '', phone)
                return phone
        
        return "N/A"

    def clean_text(self, text):
        """Clean and normalize text"""
        if not text:
            return ""
        
        # Remove extra whitespace and newlines
        cleaned = re.sub(r'\s+', ' ', text).strip()
        
        # Remove HTML entities
        cleaned = cleaned.replace('&amp;', '&')
        cleaned = cleaned.replace('&lt;', '<')
        cleaned = cleaned.replace('&gt;', '>')
        cleaned = cleaned.replace('&quot;', '"')
        
        return cleaned