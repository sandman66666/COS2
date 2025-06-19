"""
Helper Functions
===============
Common utility functions used across the system.
"""

import os
import re
import time
import json
import hashlib
import random
import string
from typing import Any, Dict, List, Optional, Union, Tuple, Set
from datetime import datetime, timedelta
import calendar

from utils.logging import get_logger

logger = get_logger(__name__)


def generate_random_id(length: int = 16) -> str:
    """
    Generate a random alphanumeric ID.
    
    Args:
        length: Length of the ID
        
    Returns:
        Random alphanumeric ID string
    """
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))


def hash_data(data: Union[str, bytes], salt: str = None) -> str:
    """
    Create a secure hash of data using SHA-256.
    
    Args:
        data: Data to hash
        salt: Optional salt to add
        
    Returns:
        Hex digest of the hash
    """
    # Convert to bytes if string
    if isinstance(data, str):
        data = data.encode('utf-8')
        
    # Add salt if provided
    if salt:
        salt_bytes = salt.encode('utf-8') if isinstance(salt, str) else salt
        data = salt_bytes + data
        
    # Hash the data
    return hashlib.sha256(data).hexdigest()


def extract_entities_from_text(text: str) -> Dict[str, List[str]]:
    """
    Extract potentially meaningful entities from text.
    
    Args:
        text: Text to analyze
        
    Returns:
        Dictionary of entity types and their values
    """
    entities = {
        "emails": [],
        "urls": [],
        "phone_numbers": [],
        "dates": []
    }
    
    # Extract emails
    email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    entities["emails"] = re.findall(email_pattern, text)
    
    # Extract URLs
    url_pattern = r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+"
    entities["urls"] = re.findall(url_pattern, text)
    
    # Extract phone numbers (simple pattern)
    phone_pattern = r"(?<!\d)(?:\+?\d{1,3}[- ]?)?\(?\d{3}\)?[- ]?\d{3}[- ]?\d{4}(?!\d)"
    entities["phone_numbers"] = re.findall(phone_pattern, text)
    
    # Extract dates (simple patterns)
    date_patterns = [
        r"\b\d{1,2}/\d{1,2}/\d{2,4}\b",  # MM/DD/YYYY or DD/MM/YYYY
        r"\b\d{1,2}-\d{1,2}-\d{2,4}\b",   # MM-DD-YYYY or DD-MM-YYYY
        r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{2,4}\b"  # Month DD, YYYY
    ]
    
    for pattern in date_patterns:
        entities["dates"].extend(re.findall(pattern, text))
    
    return entities


def normalize_name(name: str) -> str:
    """
    Normalize a person's name.
    
    Args:
        name: Name to normalize
        
    Returns:
        Normalized name
    """
    # Remove extra spaces
    normalized = ' '.join(name.split())
    
    # Handle empty name
    if not normalized:
        return ""
    
    # Capitalize parts
    parts = normalized.split()
    normalized_parts = []
    
    for part in parts:
        # Handle hyphenated names
        if '-' in part:
            hyphen_parts = part.split('-')
            normalized_parts.append('-'.join(p.capitalize() for p in hyphen_parts))
        else:
            # Handle special prefixes
            if part.lower() in ['mc', 'mac'] and len(parts) > parts.index(part) + 1:
                # This is a prefix, so capitalize it and next part will be handled in the next iteration
                normalized_parts.append(part.capitalize())
            else:
                normalized_parts.append(part.capitalize())
    
    return ' '.join(normalized_parts)


def normalize_email_address(email: str) -> str:
    """
    Normalize an email address to lowercase.
    
    Args:
        email: Email address
        
    Returns:
        Normalized email address
    """
    return email.lower()


def extract_domain_from_email(email: str) -> Optional[str]:
    """
    Extract domain from email address.
    
    Args:
        email: Email address
        
    Returns:
        Domain or None if invalid format
    """
    if '@' not in email:
        return None
    
    return email.split('@')[-1].lower()


def extract_company_from_domain(domain: str) -> str:
    """
    Attempt to extract company name from domain.
    
    Args:
        domain: Email domain
        
    Returns:
        Best guess at company name
    """
    # Remove TLD
    parts = domain.split('.')
    if len(parts) < 2:
        return domain
    
    # Skip common email providers
    common_providers = {
        'gmail', 'yahoo', 'hotmail', 'outlook', 'live', 'aol', 
        'protonmail', 'icloud', 'mail', 'inbox', 'zoho'
    }
    
    if parts[0].lower() in common_providers:
        return ""
    
    # Convert potential company name to title case
    company = parts[0].replace('-', ' ').replace('_', ' ').title()
    
    return company


def compare_name_similarity(name1: str, name2: str) -> float:
    """
    Compare similarity between two names.
    
    Args:
        name1: First name
        name2: Second name
        
    Returns:
        Similarity score between 0.0 and 1.0
    """
    # Normalize names
    name1 = normalize_name(name1).lower()
    name2 = normalize_name(name2).lower()
    
    # Check for exact match
    if name1 == name2:
        return 1.0
    
    # Get sets of words
    words1 = set(name1.split())
    words2 = set(name2.split())
    
    # Calculate Jaccard similarity
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    
    if union == 0:
        return 0.0
        
    return intersection / union


def retry_with_backoff(max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 10.0):
    """
    Decorator for retrying functions with exponential backoff.
    
    Args:
        max_retries: Maximum number of retries
        base_delay: Initial delay between retries
        max_delay: Maximum delay between retries
        
    Returns:
        Decorator function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            retries = 0
            delay = base_delay
            
            while retries <= max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    if retries > max_retries:
                        raise
                        
                    # Calculate delay with exponential backoff and jitter
                    jitter = random.uniform(0.8, 1.2)
                    current_delay = min(delay * jitter, max_delay)
                    
                    logger.warning(
                        f"Retry {retries}/{max_retries} for {func.__name__} "
                        f"after {current_delay:.2f}s due to: {str(e)}"
                    )
                    
                    time.sleep(current_delay)
                    delay *= 2  # Exponential backoff
                    
        return wrapper
    return decorator


def chunks(items: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Split list into chunks of specified size.
    
    Args:
        items: List of items
        chunk_size: Size of each chunk
        
    Returns:
        List of chunks
    """
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]


def parse_date_flexible(date_str: str) -> Optional[datetime]:
    """
    Parse date string with multiple format attempts.
    
    Args:
        date_str: Date string
        
    Returns:
        Parsed datetime or None if parsing failed
    """
    formats = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%m/%d/%Y",
        "%d/%m/%Y",
        "%B %d, %Y",
        "%b %d, %Y",
        "%d %B %Y",
        "%d %b %Y",
        "%Y-%m-%d %H:%M:%S",
        "%Y/%m/%d %H:%M:%S",
        "%m/%d/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M:%S"
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
            
    # Try ISO format
    try:
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except ValueError:
        pass
        
    return None


def date_range(start_date: datetime, end_date: datetime) -> List[datetime]:
    """
    Generate list of dates from start to end.
    
    Args:
        start_date: Start date
        end_date: End date
        
    Returns:
        List of dates
    """
    days = (end_date - start_date).days + 1
    return [start_date + timedelta(days=d) for d in range(days)]


def get_month_start_end(year: int, month: int) -> Tuple[datetime, datetime]:
    """
    Get start and end dates for a month.
    
    Args:
        year: Year
        month: Month (1-12)
        
    Returns:
        Tuple of (start_date, end_date)
    """
    last_day = calendar.monthrange(year, month)[1]
    start_date = datetime(year, month, 1)
    end_date = datetime(year, month, last_day, 23, 59, 59)
    return start_date, end_date


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate string to maximum length.
    
    Args:
        text: String to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text
        
    return text[:max_length - len(suffix)] + suffix


def deep_get(dictionary: Dict[str, Any], keys: List[str], default: Any = None) -> Any:
    """
    Safely get nested dictionary value.
    
    Args:
        dictionary: Dictionary to traverse
        keys: List of keys to traverse in order
        default: Default value if path not found
        
    Returns:
        Value at path or default
    """
    current = dictionary
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current


def deep_set(dictionary: Dict[str, Any], keys: List[str], value: Any) -> Dict[str, Any]:
    """
    Set nested dictionary value, creating path if needed.
    
    Args:
        dictionary: Dictionary to modify
        keys: List of keys forming the path
        value: Value to set
        
    Returns:
        Modified dictionary
    """
    current = dictionary
    for i, key in enumerate(keys[:-1]):
        if key not in current or not isinstance(current[key], dict):
            current[key] = {}
        current = current[key]
    
    current[keys[-1]] = value
    return dictionary


def merge_dicts_deep(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries.
    
    Args:
        dict1: First dictionary
        dict2: Second dictionary (takes precedence)
        
    Returns:
        Merged dictionary
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            # Recursively merge dictionaries
            result[key] = merge_dicts_deep(result[key], value)
        else:
            # Override or add value
            result[key] = value
            
    return result


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
        
    for unit in ['KB', 'MB', 'GB', 'TB']:
        size_bytes /= 1024
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
            
    return f"{size_bytes:.2f} PB"


def detect_language(text: str) -> str:
    """
    Simple language detection by character frequency.
    
    Args:
        text: Text to analyze
        
    Returns:
        ISO 639-1 language code
    """
    # This is a simplified implementation
    # For production use, consider using a proper library like langdetect
    
    # Check for common English characters and patterns
    if len(re.findall(r'[a-zA-Z]', text)) > len(text) * 0.7:
        return "en"
        
    # For other languages, return "unknown"
    return "unknown"
    

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing invalid characters.
    
    Args:
        filename: Filename to sanitize
        
    Returns:
        Sanitized filename
    """
    # Remove invalid characters
    invalid_chars = r'[<>:"/\\|?*]'
    sanitized = re.sub(invalid_chars, '_', filename)
    
    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip('. ')
    
    # Ensure filename is not empty
    if not sanitized:
        sanitized = "unnamed_file"
        
    return sanitized


def build_cache_key(*args, prefix: str = "") -> str:
    """
    Build cache key from multiple arguments.
    
    Args:
        *args: Arguments to include in key
        prefix: Optional prefix
        
    Returns:
        Cache key string
    """
    # Convert all args to strings and join
    parts = [str(arg) for arg in args]
    key = "_".join(parts)
    
    # Add prefix if provided
    if prefix:
        key = f"{prefix}_{key}"
    
    # Hash if too long (Redis keys should be relatively short)
    if len(key) > 200:
        key_hash = hashlib.md5(key.encode('utf-8')).hexdigest()
        key = f"{prefix}_{key_hash}" if prefix else key_hash
    
    return key
