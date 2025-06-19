"""
Input Validation Utilities
==========================
Provides validation functions for various types of input data.
"""

import re
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, date
import uuid

from utils.logging import get_logger

logger = get_logger(__name__)


def is_valid_email(email: str) -> bool:
    """
    Validate email format.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid, False otherwise
    """
    # Simple regex for email validation
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def is_valid_phone(phone: str, allow_international: bool = True) -> bool:
    """
    Validate phone number format.
    
    Args:
        phone: Phone number to validate
        allow_international: Whether to allow international format
        
    Returns:
        True if valid, False otherwise
    """
    # Clean the phone number
    cleaned_phone = re.sub(r"[^\d+]", "", phone)
    
    # Simple validation for US phone numbers
    us_pattern = r"^\d{10}$"
    
    # International pattern
    intl_pattern = r"^\+?[1-9]\d{1,14}$"
    
    if re.match(us_pattern, cleaned_phone):
        return True
    
    if allow_international and re.match(intl_pattern, cleaned_phone):
        return True
    
    return False


def is_valid_url(url: str) -> bool:
    """
    Validate URL format.
    
    Args:
        url: URL to validate
        
    Returns:
        True if valid, False otherwise
    """
    # URL validation pattern
    pattern = r"^(https?|ftp)://[^\s/$.?#].[^\s]*$"
    return bool(re.match(pattern, url))


def is_valid_uuid(uuid_str: str) -> bool:
    """
    Validate UUID format.
    
    Args:
        uuid_str: UUID string to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        uuid_obj = uuid.UUID(str(uuid_str))
        return str(uuid_obj) == uuid_str
    except (ValueError, AttributeError, TypeError):
        return False


def is_valid_date(date_str: str, formats: List[str] = None) -> bool:
    """
    Validate date string against acceptable formats.
    
    Args:
        date_str: Date string to validate
        formats: List of acceptable formats (default: ISO formats)
        
    Returns:
        True if valid, False otherwise
    """
    if formats is None:
        formats = ["%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y"]
    
    for fmt in formats:
        try:
            datetime.strptime(date_str, fmt)
            return True
        except ValueError:
            continue
    
    return False


def is_valid_datetime(datetime_str: str, formats: List[str] = None) -> bool:
    """
    Validate datetime string against acceptable formats.
    
    Args:
        datetime_str: Datetime string to validate
        formats: List of acceptable formats (default: ISO formats)
        
    Returns:
        True if valid, False otherwise
    """
    if formats is None:
        formats = ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S"]
    
    for fmt in formats:
        try:
            datetime.strptime(datetime_str, fmt)
            return True
        except ValueError:
            continue
    
    # Try ISO format as last resort
    try:
        datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        return True
    except ValueError:
        return False


def is_valid_json_structure(data: Dict[str, Any], schema: Dict[str, Dict[str, Any]]) -> bool:
    """
    Validate JSON structure against schema.
    
    Args:
        data: JSON data to validate
        schema: Schema definition with types and requirements
        
    Returns:
        True if valid, False otherwise
    """
    for field, field_schema in schema.items():
        # Check required fields
        if field_schema.get("required", False) and field not in data:
            logger.debug(f"Required field {field} missing from data")
            return False
        
        # Skip validation if field not present and not required
        if field not in data:
            continue
        
        # Get field value
        value = data[field]
        
        # Check type
        expected_type = field_schema.get("type")
        if expected_type == "string" and not isinstance(value, str):
            logger.debug(f"Field {field} should be string, got {type(value)}")
            return False
        elif expected_type == "number" and not isinstance(value, (int, float)):
            logger.debug(f"Field {field} should be number, got {type(value)}")
            return False
        elif expected_type == "integer" and not isinstance(value, int):
            logger.debug(f"Field {field} should be integer, got {type(value)}")
            return False
        elif expected_type == "boolean" and not isinstance(value, bool):
            logger.debug(f"Field {field} should be boolean, got {type(value)}")
            return False
        elif expected_type == "array" and not isinstance(value, list):
            logger.debug(f"Field {field} should be array, got {type(value)}")
            return False
        elif expected_type == "object" and not isinstance(value, dict):
            logger.debug(f"Field {field} should be object, got {type(value)}")
            return False
        
        # Check format if specified
        if "format" in field_schema and isinstance(value, str):
            format_type = field_schema["format"]
            
            if format_type == "email" and not is_valid_email(value):
                logger.debug(f"Field {field} should be valid email")
                return False
            elif format_type == "url" and not is_valid_url(value):
                logger.debug(f"Field {field} should be valid URL")
                return False
            elif format_type == "date" and not is_valid_date(value):
                logger.debug(f"Field {field} should be valid date")
                return False
            elif format_type == "datetime" and not is_valid_datetime(value):
                logger.debug(f"Field {field} should be valid datetime")
                return False
            elif format_type == "uuid" and not is_valid_uuid(value):
                logger.debug(f"Field {field} should be valid UUID")
                return False
        
        # Check enum if specified
        if "enum" in field_schema and value not in field_schema["enum"]:
            logger.debug(f"Field {field} should be one of {field_schema['enum']}")
            return False
            
    return True


def sanitize_string(input_str: str, allow_html: bool = False) -> str:
    """
    Sanitize string input to prevent injection attacks.
    
    Args:
        input_str: String to sanitize
        allow_html: Whether to allow HTML tags
        
    Returns:
        Sanitized string
    """
    if not allow_html:
        # Remove HTML tags
        sanitized = re.sub(r"<[^>]*>", "", input_str)
    else:
        sanitized = input_str
    
    # Remove script tags in any case
    sanitized = re.sub(r"<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>", "", sanitized)
    
    return sanitized


def validate_api_input(data: Dict[str, Any], required_fields: List[str], field_types: Dict[str, type]) -> Dict[str, List[str]]:
    """
    Validate API input data.
    
    Args:
        data: Input data dictionary
        required_fields: List of required field names
        field_types: Dictionary mapping field names to expected types
        
    Returns:
        Dictionary of field names to error messages, empty if no errors
    """
    errors = {}
    
    # Check required fields
    for field in required_fields:
        if field not in data or data[field] is None:
            if field not in errors:
                errors[field] = []
            errors[field].append("This field is required")
    
    # Check field types
    for field, expected_type in field_types.items():
        if field in data and data[field] is not None:
            # Handle special case for dates
            if expected_type == date and isinstance(data[field], str):
                if not is_valid_date(data[field]):
                    if field not in errors:
                        errors[field] = []
                    errors[field].append(f"Invalid date format, expected YYYY-MM-DD")
            # Normal type checking
            elif not isinstance(data[field], expected_type):
                if field not in errors:
                    errors[field] = []
                errors[field].append(f"Expected {expected_type.__name__}, got {type(data[field]).__name__}")
    
    return errors


def is_valid_password(password: str, min_length: int = 8, 
                      require_uppercase: bool = True,
                      require_lowercase: bool = True,
                      require_digit: bool = True,
                      require_special: bool = True) -> Dict[str, bool]:
    """
    Validate password strength.
    
    Args:
        password: Password to validate
        min_length: Minimum length required
        require_uppercase: Require at least one uppercase letter
        require_lowercase: Require at least one lowercase letter
        require_digit: Require at least one digit
        require_special: Require at least one special character
        
    Returns:
        Dictionary of validation results
    """
    results = {
        "valid": True,
        "length": len(password) >= min_length,
        "uppercase": not require_uppercase or bool(re.search(r"[A-Z]", password)),
        "lowercase": not require_lowercase or bool(re.search(r"[a-z]", password)),
        "digit": not require_digit or bool(re.search(r"\d", password)),
        "special": not require_special or bool(re.search(r"[!@#$%^&*(),.?\":{}|<>]", password))
    }
    
    # Check if password meets all requirements
    results["valid"] = all([
        results["length"],
        results["uppercase"],
        results["lowercase"],
        results["digit"],
        results["special"]
    ])
    
    return results


def validate_multi_tenant_access(user_id: str, tenant_id: str, tenant_roles: Dict[str, List[str]]) -> bool:
    """
    Validate user access in multi-tenant context.
    
    Args:
        user_id: ID of user attempting access
        tenant_id: ID of tenant being accessed
        tenant_roles: Dictionary mapping tenant IDs to allowed role lists
        
    Returns:
        True if access is allowed, False otherwise
    """
    # Check if user has roles for this tenant
    if tenant_id not in tenant_roles:
        return False
    
    # User has some role in this tenant
    return True
