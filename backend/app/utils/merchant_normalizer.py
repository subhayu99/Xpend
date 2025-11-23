"""
Merchant name normalization utilities.
Cleans up messy merchant names from bank statements.
"""
import re
from typing import Optional

class MerchantNormalizer:
    """Normalize merchant names from transaction descriptions"""
    
    # Common prefixes to remove
    PREFIXES = [
        r'^UPI/',
        r'^NEFT/',
        r'^IMPS/',
        r'^RTGS/',
        r'^POS/',
        r'^ATM/',
        r'^CR/',
        r'^DR/',
        r'^TRF/',
    ]
    
    # Common suffixes/patterns to remove
    SUFFIXES = [
        r'\*[A-Z]+\d*$',  # *DELHI, *BANGALORE123
        r'-\d+$',          # -123
        r'\s+\d{6,}$',     # Transaction IDs
        r'/[A-Z0-9]+$',    # /PAYTM, /PHONEPE
        r'@[a-z]+$',       # @paytm, @ybl
    ]
    
    # Merchant-specific patterns
    MERCHANT_PATTERNS = {
        r'SWIGGY': 'Swiggy',
        r'ZOMATO': 'Zomato',
        r'AMAZON': 'Amazon',
        r'FLIPKART': 'Flipkart',
        r'UBER': 'Uber',
        r'OLA': 'Ola',
        r'NETFLIX': 'Netflix',
        r'PRIME\s*VIDEO': 'Amazon Prime',
        r'SPOTIFY': 'Spotify',
        r'PAYTM': 'Paytm',
        r'PHONEPE': 'PhonePe',
        r'GPAY|GOOGLE\s*PAY': 'Google Pay',
        r'BIGBASKET': 'BigBasket',
        r'GROFERS|BLINKIT': 'Blinkit',
        r'DUNZO': 'Dunzo',
        r'ZEPTO': 'Zepto',
        r'MYNTRA': 'Myntra',
        r'AJIO': 'Ajio',
        r'NYKAA': 'Nykaa',
        r'BOOKMYSHOW|BMS': 'BookMyShow',
        r'IRCTC': 'IRCTC',
        r'MAKEMYTRIP|MMT': 'MakeMyTrip',
        r'GOIBIBO': 'Goibibo',
        r'AIRTEL': 'Airtel',
        r'JIO': 'Jio',
        r'VODAFONE|VI': 'Vi',
    }
    
    @staticmethod
    def normalize(description: str) -> Optional[str]:
        """
        Extract and normalize merchant name from transaction description.
        
        Args:
            description: Raw transaction description
            
        Returns:
            Normalized merchant name or None if couldn't extract
        """
        if not description:
            return None
            
        # Start with the original description
        merchant = description.strip()
        
        # Remove common prefixes
        for prefix in MerchantNormalizer.PREFIXES:
            merchant = re.sub(prefix, '', merchant, flags=re.IGNORECASE)
        
        # Remove common suffixes
        for suffix in MerchantNormalizer.SUFFIXES:
            merchant = re.sub(suffix, '', merchant)
        
        # Clean up whitespace
        merchant = ' '.join(merchant.split())
        
        # Try to match known merchants
        for pattern, name in MerchantNormalizer.MERCHANT_PATTERNS.items():
            if re.search(pattern, merchant, re.IGNORECASE):
                return name
        
        # If no match, return cleaned version
        # Capitalize first letter of each word
        merchant = merchant.title()
        
        # Remove special characters but keep spaces and hyphens
        merchant = re.sub(r'[^a-zA-Z0-9\s\-]', '', merchant)
        
        # Final cleanup
        merchant = ' '.join(merchant.split())
        
        return merchant if merchant else None
    
    @staticmethod
    def extract_merchant_name(description: str) -> str:
        """
        Extract merchant name, falling back to description if normalization fails.
        
        Args:
            description: Raw transaction description
            
        Returns:
            Merchant name (normalized if possible, otherwise cleaned description)
        """
        normalized = MerchantNormalizer.normalize(description)
        return normalized if normalized else description[:50]  # Limit length
