import pandas as pd
import numpy as np
import re
import usaddress
import phonenumbers
import logging
from fuzzywuzzy import fuzz
from collections import defaultdict

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("data_processing.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger()

class FuneralDataProcessor:
    def __init__(self, input_file='funeral_services_data.csv'):
        """Initialize the data processor with an input file path"""
        self.input_file = input_file
        logger.info(f"Initializing data processor with file: {input_file}")
        
        try:
            self.df = pd.read_csv(input_file)
            logger.info(f"Loaded {len(self.df)} rows from {input_file}")
        except Exception as e:
            logger.error(f"Error loading input file: {str(e)}")
            self.df = pd.DataFrame()
    
    def clean_data(self):
        """Perform all cleaning operations on the data"""
        if self.df.empty:
            logger.error("No data to clean")
            return self.df
        
        # Make a copy of the original data
        self.original_df = self.df.copy()
        
        # Run all cleaning functions
        self.standardize_column_names()
        self.remove_duplicates()
        self.clean_business_names()
        self.standardize_addresses()
        self.clean_phone_numbers()
        self.extract_emails()
        self.clean_websites()
        self.fill_missing_business_types()
        self.extract_social_media_links()
        
        # Report on cleaning results
        logger.info(f"Data cleaning complete. Final dataset has {len(self.df)} rows")
        return self.df
    
    def standardize_column_names(self):
        """Ensure consistent column naming"""
        logger.info("Standardizing column names")
        
        # Define standard column names
        standard_columns = {
            'business name': 'Business Name',
            'business_name': 'Business Name',
            'name': 'Business Name',
            'company': 'Business Name',
            'company name': 'Business Name',
            
            'type': 'Type',
            'business type': 'Type',
            'business_type': 'Type',
            'category': 'Type',
            
            'address': 'Address',
            'full address': 'Address',
            'full_address': 'Address',
            'location': 'Address',
            
            'phone': 'Phone',
            'phone number': 'Phone',
            'phone_number': 'Phone',
            'telephone': 'Phone',
            'tel': 'Phone',
            
            'email': 'Email',
            'email address': 'Email',
            'email_address': 'Email',
            'contact email': 'Email',
            
            'website': 'Website',
            'web': 'Website',
            'url': 'Website',
            'web address': 'Website',
            'web_address': 'Website',
            
            'contact': 'Contact Person',
            'contact person': 'Contact Person',
            'contact_person': 'Contact Person',
            'primary contact': 'Contact Person',
            
            'social': 'Social Media',
            'social media': 'Social Media',
            'social_media': 'Social Media',
            'social links': 'Social Media',
            'social_links': 'Social Media',
            
            'size': 'Size',
            'business size': 'Size',
            'company size': 'Size',
            'employees': 'Size',
            
            'rating': 'Google Rating',
            'google rating': 'Google Rating',
            'google_rating': 'Google Rating',
            'review rating': 'Google Rating',
            'stars': 'Google Rating',
            
            'state': 'State',
            'st': 'State',
            'province': 'State',
            
            'city': 'City',
            'town': 'City',
            'locality': 'City',
            
            'source': 'Source',
            'data source': 'Source',
            'data_source': 'Source',
        }
        
        # Create a lowercase mapping for easier matching
        df_columns_lower = {col.lower(): col for col in self.df.columns}
        
        # Track renamed columns
        renamed_columns = {}
        
        # Find and rename columns
        for std_col_lower, std_col in standard_columns.items():
            if std_col_lower in df_columns_lower and std_col != df_columns_lower[std_col_lower]:
                renamed_columns[df_columns_lower[std_col_lower]] = std_col
        
        # Apply renaming
        if renamed_columns:
            self.df = self.df.rename(columns=renamed_columns)
            logger.info(f"Renamed {len(renamed_columns)} columns")
            
        # Ensure all required columns exist, adding empty ones if needed
        required_columns = [
            'Business Name', 'Type', 'Address', 'Phone', 'Email', 'Website',
            'Contact Person', 'Social Media', 'Size', 'Google Rating', 'State', 'City'
        ]
        
        for col in required_columns:
            if col not in self.df.columns:
                self.df[col] = "N/A"
                logger.info(f"Added missing column: {col}")
                
        return self.df
    
    def remove_duplicates(self):
        """Remove duplicate entries"""
        logger.info("Removing duplicate entries")
        
        initial_count = len(self.df)
        
        # First, remove exact duplicates
        self.df = self.df.drop_duplicates()
        logger.info(f"Removed {initial_count - len(self.df)} exact duplicate rows")
        
        # Then, look for fuzzy duplicates by business name and address
        # This requires a bit more sophisticated approach
        
        # Create a function to generate a fuzzy matching key
        def generate_matching_key(row):
            name = str(row['Business Name']).lower()
            # Remove common words that don't help in distinguishing
            name = re.sub(r'\b(funeral|home|services|inc|llc)\b', '', name)
            name = re.sub(r'\s+', ' ', name).strip()
            
            # Get first part of address (usually street address)
            address = str(row['Address']).lower()
            address_parts = address.split(',')[0] if ',' in address else address
            address_clean = re.sub(r'\s+', ' ', address_parts).strip()
            
            return f"{name}|{address_clean}"
        
        # Generate the matching keys
        self.df['matching_key'] = self.df.apply(generate_matching_key, axis=1)
        
        # Group by matching key
        grouped = self.df.groupby('matching_key')
        
        # For each group with more than 1 entry, keep the most complete record
        rows_to_keep = []
        
        for key, group in grouped:
            if len(group) == 1:
                rows_to_keep.append(group.index[0])
            else:
                # Define a completeness score function
                def completeness_score(row):
                    score = 0
                    for col in self.df.columns:
                        if col == 'matching_key':
                            continue
                        val = str(row[col])
                        if val and val != "N/A" and val != "nan":
                            score += 1
                    return score
                
                # Calculate scores
                scores = group.apply(completeness_score, axis=1)
                # Keep the row with highest score
                rows_to_keep.append(scores.idxmax())
        
        # Keep only the selected rows
        self.df = self.df.loc[rows_to_keep]
        
        # Remove the temporary column
        self.df = self.df.drop('matching_key', axis=1)
        
        logger.info(f"After fuzzy deduplication: {len(self.df)} entries")
        logger.info(f"Total removed: {initial_count - len(self.df)} entries")
        
        return self.df
    
    def clean_business_names(self):
        """Clean and standardize business names"""
        logger.info("Cleaning business names")
        
        if 'Business Name' not in self.df.columns:
            logger.warning("Business Name column not found")
            return self.df
        
        # Handle missing values
        self.df['Business Name'] = self.df['Business Name'].fillna("Unknown Business")
        
        # Function to clean business names
        def clean_name(name):
            if pd.isna(name) or name == "N/A":
                return "Unknown Business"
            
            name = str(name).strip()
            
            # Fix capitalization (Title Case)
            name = ' '.join(word.capitalize() for word in name.split())
            
            # Handle common abbreviations
            name = re.sub(r'\bFnrl\b', 'Funeral', name, flags=re.IGNORECASE)
            name = re.sub(r'\bSvc[s]?\b', 'Services', name, flags=re.IGNORECASE)
            name = re.sub(r'\bMem\b', 'Memorial', name, flags=re.IGNORECASE)
            
            # Standardize common endings
            if not re.search(r'(Inc|LLC|Ltd|Co|Corporation|Company)', name, re.IGNORECASE):
                if re.search(r'Funeral Home', name, re.IGNORECASE) or re.search(r'Mortuary', name, re.IGNORECASE):
                    # Names already ending with "Funeral Home" or "Mortuary" are fine
                    pass
                elif re.search(r'Funeral', name, re.IGNORECASE):
                    name += " Home"
                elif re.search(r'Cremation', name, re.IGNORECASE):
                    name += " Services"
            
            return name
        
        # Apply cleaning
        self.df['Business Name'] = self.df['Business Name'].apply(clean_name)
        
        logger.info("Business names cleaned")
        return self.df
    
    def standardize_addresses(self):
        """Standardize address formats"""
        logger.info("Standardizing addresses")
        
        if 'Address' not in self.df.columns:
            logger.warning("Address column not found")
            return self.df
        
        # Function to standardize address format
        def standardize_address(address):
            if pd.isna(address) or address == "N/A":
                return "N/A"
            
            try:
                # Use usaddress to parse the address into components
                address_str = str(address).strip()
                parsed_address, address_type = usaddress.tag(address_str)
                
                # Extract components
                street_number = parsed_address.get('AddressNumber', '')
                street_name = parsed_address.get('StreetName', '')
                street_suffix = parsed_address.get('StreetNamePostType', '')
                unit_type = parsed_address.get('OccupancyType', '')
                unit_number = parsed_address.get('OccupancyIdentifier', '')
                city = parsed_address.get('PlaceName', '')
                state = parsed_address.get('StateName', '')
                zip_code = parsed_address.get('ZipCode', '')
                
                # Reconstruct standardized address
                street_address = f"{street_number} {street_name} {street_suffix}".strip()
                if unit_type and unit_number:
                    street_address += f", {unit_type} {unit_number}"
                
                city_state_zip = ""
                if city:
                    city_state_zip += city
                if state:
                    if city_state_zip:
                        city_state_zip += f", {state}"
                    else:
                        city_state_zip = state
                if zip_code:
                    city_state_zip += f" {zip_code}"
                
                if street_address and city_state_zip:
                    return f"{street_address}, {city_state_zip}"
                elif street_address:
                    return street_address
                elif city_state_zip:
                    return city_state_zip
                else:
                    return address_str
                
            except Exception as e:
                logger.warning(f"Error parsing address '{address}': {str(e)}")
                return str(address).strip()
        
        # Apply standardization
        self.df['Address'] = self.df['Address'].apply(standardize_address)
        
        # Extract state and city from address if those columns are missing or empty
        if 'State' not in self.df.columns or self.df['State'].isna().all():
            logger.info("Extracting state information from addresses")
            
            def extract_state(address):
                if pd.isna(address) or address == "N/A":
                    return "N/A"
                
                # Try to find state abbreviation pattern
                state_match = re.search(r',\s*([A-Z]{2})\s*\d{5}', address)
                if state_match:
                    return state_match.group(1)
                
                state_match = re.search(r',\s*([A-Z]{2}),', address)
                if state_match:
                    return state_match.group(1)
                
                # Try to find full state name pattern
                state_names = {
                    'alabama': 'AL', 'alaska': 'AK', 'arizona': 'AZ', 'arkansas': 'AR',
                    'california': 'CA', 'colorado': 'CO', 'connecticut': 'CT', 'delaware': 'DE',
                    'florida': 'FL', 'georgia': 'GA', 'hawaii': 'HI', 'idaho': 'ID',
                    'illinois': 'IL', 'indiana': 'IN', 'iowa': 'IA', 'kansas': 'KS',
                    'kentucky': 'KY', 'louisiana': 'LA', 'maine': 'ME', 'maryland': 'MD',
                    'massachusetts': 'MA', 'michigan': 'MI', 'minnesota': 'MN', 'mississippi': 'MS',
                    'missouri': 'MO', 'montana': 'MT', 'nebraska': 'NE', 'nevada': 'NV',
                    'new hampshire': 'NH', 'new jersey': 'NJ', 'new mexico': 'NM', 'new york': 'NY',
                    'north carolina': 'NC', 'north dakota': 'ND', 'ohio': 'OH', 'oklahoma': 'OK',
                    'oregon': 'OR', 'pennsylvania': 'PA', 'rhode island': 'RI', 'south carolina': 'SC',
                    'south dakota': 'SD', 'tennessee': 'TN', 'texas': 'TX', 'utah': 'UT',
                    'vermont': 'VT', 'virginia': 'VA', 'washington': 'WA', 'west virginia': 'WV',
                    'wisconsin': 'WI', 'wyoming': 'WY', 'district of columbia': 'DC'
                }
                
                for state_name, abbr in state_names.items():
                    if re.search(f',\\s*{state_name}\\b', address.lower()):
                        return abbr
                
                return "N/A"
            
            self.df['State'] = self.df['Address'].apply(extract_state)
        
        if 'City' not in self.df.columns or self.df['City'].isna().all():
            logger.info("Extracting city information from addresses")
            
            def extract_city(address):
                if pd.isna(address) or address == "N/A":
                    return "N/A"
                
                # Try to find city pattern before state
                city_match = re.search(r',\s*([^,]+),\s*[A-Z]{2}', address)
                if city_match:
                    return city_match.group(1).strip()
                
                # Try simpler pattern
                parts = address.split(',')
                if len(parts) >= 2:
                    return parts[-2].strip()
                
                return "N/A"
            
            self.df['City'] = self.df['Address'].apply(extract_city)
        
        logger.info("Addresses standardized")
        return self.df
    
    def clean_phone_numbers(self):
        """Standardize phone number formats"""
        logger.info("Cleaning phone numbers")
        
        if 'Phone' not in self.df.columns:
            logger.warning("Phone column not found")
            return self.df
        
        # Function to standardize phone numbers
        def standardize_phone(phone):
            if pd.isna(phone) or phone == "N/A":
                return "N/A"
            
            try:
                # Remove non-numeric characters
                digits_only = re.sub(r'\D', '', str(phone))
                
                # Ensure we have enough digits
                if len(digits_only) < 10:
                    return str(phone).strip()  # Return original if can't standardize
                
                # Format with US country code if 11 digits starting with 1
                if len(digits_only) == 11 and digits_only.startswith('1'):
                    digits_only = digits_only[1:]
                
                # Take last 10 digits if too long
                if len(digits_only) > 10:
                    digits_only = digits_only[-10:]
                
                # Format as (XXX) XXX-XXXX
                return f"({digits_only[0:3]}) {digits_only[3:6]}-{digits_only[6:10]}"
                
            except Exception as e:
                logger.warning(f"Error parsing phone number '{phone}': {str(e)}")
                return str(phone).strip()
        
        # Apply standardization
        self.df['Phone'] = self.df['Phone'].apply(standardize_phone)
        
        logger.info("Phone numbers cleaned")
        return self.df
    
    def extract_emails(self):
        """Extract and validate email addresses"""
        logger.info("Extracting and validating emails")
        
        if 'Email' not in self.df.columns:
            logger.warning("Email column not found")
            return self.df
        
        # Function to validate email format
        def validate_email(email):
            if pd.isna(email) or email == "N/A":
                return "N/A"
            
            email_str = str(email).strip().lower()
            
            # Simple regex for email validation
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            
            if re.match(email_pattern, email_str):
                return email_str
            else:
                # Try to extract email from text
                email_match = re.search(email_pattern, email_str)
                if email_match:
                    return email_match.group(0)
                return "N/A"
        
        # Apply validation
        self.df['Email'] = self.df['Email'].apply(validate_email)
        
        logger.info("Emails validated")
        return self.df
    
    def clean_websites(self):
        """Clean and standardize website URLs"""
        logger.info("Cleaning website URLs")
        
        if 'Website' not in self.df.columns:
            logger.warning("Website column not found")
            return self.df
        
        # Function to standardize website URLs
        def standardize_url(url):
            if pd.isna(url) or url == "N/A":
                return "N/A"
            
            url_str = str(url).strip()
            
            # Simple URL validation and standardization
            if not url_str.startswith(('http://', 'https://')):
                url_str = 'http://' + url_str
            
            # Remove trailing slashes
            url_str = url_str.rstrip('/')
            
            # Simple validation
            url_pattern = r'^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/.*)?'
            if re.match(url_pattern, url_str):
                return url_str
            else:
                return "N/A"
        
        # Apply standardization
        self.df['Website'] = self.df['Website'].apply(standardize_url)
        
        logger.info("Website URLs cleaned")
        return self.df
    
    def fill_missing_business_types(self):
        """Fill missing business types based on business name"""
        logger.info("Filling missing business types")
        
        if 'Type' not in self.df.columns or 'Business Name' not in self.df.columns:
            logger.warning("Type or Business Name column not found")
            return self.df
        
        # Function to determine business type from name
        def determine_type(row):
            if pd.notna(row['Type']) and row['Type'] != "N/A":
                return row['Type']
            
            name = str(row['Business Name']).lower()
            
            if 'cremation' in name or 'crematory' in name:
                return "Cremation Service"
            elif 'memorial' in name:
                if 'funeral' in name:
                    return "Hybrid (Funeral & Memorial)"
                return "Memorial Service"
            elif 'mortuary' in name:
                return "Mortuary"
            elif 'cemetery' in name:
                return "Cemetery"
            elif 'chapel' in name:
                return "Funeral Chapel"
            elif 'funeral' in name:
                return "Funeral Home"
            else:
                return "Funeral Services"
        
        # Apply type determination
        self.df['Type'] = self.df.apply(determine_type, axis=1)
        
        logger.info("Business types filled")
        return self.df
    
    def extract_social_media_links(self):
        """Extract social media links from Website or dedicated column"""
        logger.info("Processing social media links")
        
        # This would typically involve visiting each website to extract links
        # For now, we'll just ensure the column exists
        if 'Social Media' not in self.df.columns:
            self.df['Social Media'] = "N/A"
        
        logger.info("Social media processing complete")
        return self.df
    
    def export_to_csv(self, output_file="cleaned_funeral_services_data.csv"):
        """Export processed data to CSV"""
        logger.info(f"Exporting processed data to {output_file}")
        
        try:
            self.df.to_csv(output_file, index=False)
            logger.info(f"Data successfully exported to {output_file}")
            return output_file
        except Exception as e:
            logger.error(f"Error exporting data: {str(e)}")
            return None
    
    def export_to_excel(self, output_file="funeral_services_data.xlsx"):
        """Export processed data to Excel with multiple sheets"""
        logger.info(f"Exporting processed data to Excel: {output_file}")
        
        try:
            # Create Excel writer
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                # Write main data to the first sheet
                self.df.to_excel(writer, sheet_name='All Data', index=False)
                
                # Create state-specific sheets
                for state, state_df in self.df.groupby('State'):
                    if state != "N/A" and len(state_df) > 0:
                        state_name = f"State - {state}"
                        state_df.to_excel(writer, sheet_name=state_name, index=False)
                
                # Create type-specific sheets
                for biz_type, type_df in self.df.groupby('Type'):
                    if biz_type != "N/A" and len(type_df) > 0:
                        type_name = f"Type - {biz_type}"
                        # Limit sheet name length to avoid Excel errors
                        if len(type_name) > 31:
                            type_name = type_name[:31]
                        type_df.to_excel(writer, sheet_name=type_name, index=False)
            
            logger.info(f"Data successfully exported to Excel: {output_file}")
            return output_file
        except Exception as e:
            logger.error(f"Error exporting data to Excel: {str(e)}")
            return None

# Main execution
if __name__ == "__main__":
    processor = FuneralDataProcessor('funeral_services_data.csv')
    processor.clean_data()
    processor.export_to_csv()
    processor.export_to_excel() 