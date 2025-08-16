import re
from urllib.parse import urlparse
from typing import Optional

def validate_url(url: str) -> bool:
    """Validate if URL is properly formatted"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def extract_domain(url: str) -> Optional[str]:
    """Extract domain from URL"""
    try:
        return urlparse(url).netloc.lower()
    except:
        return None

def clean_text(text: str) -> str:
    """Clean and normalize text"""
    if not text:
        return ""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    return text

def extract_social_handle(url: str, platform: str) -> Optional[str]:
    """Extract social media handle from URL"""
    if not url:
        return None
        
    patterns = {
        'instagram': r'instagram\.com/([^/?]+)',
        'twitter': r'twitter\.com/([^/?]+)',
        'tiktok': r'tiktok\.com/@?([^/?]+)',
        'facebook': r'facebook\.com/([^/?]+)'
    }
    
    pattern = patterns.get(platform.lower())
    if pattern:
        match = re.search(pattern, url, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return url  # Return full URL if no pattern match
