# config/constants.py
"""
System-wide constants for the Strategic Intelligence System
"""

# Vector dimensions for embeddings
EMBEDDING_DIMENSION = 1536

# Contact trust tiers
class TrustTier:
    TIER_1 = "tier_1"  # Direct, frequent communication (sent emails)
    TIER_2 = "tier_2"  # Direct, infrequent communication
    TIER_3 = "tier_3"  # Indirect communication (CC'd, etc.)
    
    # Alternative names for compatibility
    HIGH = "tier_1"
    MEDIUM = "tier_2"
    LOW = "tier_3"

# Alias for backward compatibility
TrustTiers = TrustTier

# Trust thresholds for contact scoring
TRUST_THRESHOLD_HIGH = 10.0
TRUST_THRESHOLD_MEDIUM = 5.0
    
# Minimum email frequency to consider a contact trusted (Tier 1)
MIN_SENT_EMAILS_FOR_TRUST = 3

# Maximum emails per API request
MAX_EMAILS_PER_REQUEST = 100

# Domains to ignore during analysis
DOMAINS_TO_IGNORE = [
    'noreply', 'no-reply', 'donotreply', 'do-not-reply',
    'notifications', 'alerts', 'updates', 'newsletter',
    'support', 'help', 'info', 'admin', 'system'
]

# Maximum domains to track per user
MAX_DOMAINS_PER_USER = 50

# Time periods for intelligence analysis (in days)
ANALYSIS_PERIODS = {
    "recent": 30,
    "quarterly": 90,
    "biannual": 180,
    "annual": 365
}

# Claude analyst types
class AnalystType:
    BUSINESS = "business"
    RELATIONSHIP = "relationship"
    TECHNICAL = "technical"
    MARKET = "market"
    PREDICTIVE = "predictive"

# Email metadata keys
class EmailMetadata:
    MESSAGE_ID = "message_id"
    THREAD_ID = "thread_id"
    FROM = "from"
    TO = "to"
    CC = "cc"
    BCC = "bcc"
    DATE = "date"
    SUBJECT = "subject"
    BODY_TEXT = "body_text"
    BODY_HTML = "body_html"
    HEADERS = "headers"
    IS_SENT = "is_sent"

# Alias for backward compatibility
EmailMetadataKeys = EmailMetadata

# Knowledge tree node types
class NodeType:
    PERSON = "person"
    ORGANIZATION = "organization"
    PROJECT = "project"
    TOPIC = "topic"
    EVENT = "event"
    DECISION = "decision"

# Cache TTL values (in seconds)
class CacheTTL:
    SHORT = 300       # 5 minutes
    MEDIUM = 3600     # 1 hour
    LONG = 86400      # 24 hours
    VERY_LONG = 604800  # 1 week
