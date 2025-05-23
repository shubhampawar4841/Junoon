import requests
from bs4 import BeautifulSoup
import time
import random

class BaseScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def get_page(self, url):
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"Error fetching {url}: {str(e)}")
            return None

    def parse_page(self, html):
        if not html:
            return None
        return BeautifulSoup(html, 'html.parser')

    def delay(self, min_seconds=2, max_seconds=5):
        time.sleep(random.uniform(min_seconds, max_seconds))

    def clean_text(self, text):
        if not text:
            return "N/A"
        return ' '.join(text.strip().split())

    def extract_phone(self, text):
        if not text:
            return "N/A"
        # Basic phone number extraction
        import re
        phone = re.search(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text)
        return phone.group(0) if phone else "N/A"

    def extract_email(self, text):
        if not text:
            return "N/A"
        # Basic email extraction
        import re
        email = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
        return email.group(0) if email else "N/A" 