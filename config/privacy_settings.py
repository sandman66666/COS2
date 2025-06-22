"""
Privacy and filtering configuration for the Strategic Intelligence System

This module provides granular control over what data gets processed,
ensuring user privacy and compliance with data protection regulations.
"""

from typing import Dict, List, Set, Optional
from enum import Enum
from dataclasses import dataclass, field

class PrivacyLevel(Enum):
    """Privacy levels for data processing"""
    MINIMAL = "minimal"        # Only explicit strategic channels
    BALANCED = "balanced"      # Strategic + some business channels  
    COMPREHENSIVE = "comprehensive"  # All business-related content

class DataSourceType(Enum):
    """Types of data sources"""
    EMAIL = "email"
    SLACK = "slack"
    CALENDAR = "calendar" 
    DOCUMENTS = "documents"

@dataclass
class PrivacySettings:
    """User privacy settings for data processing"""
    
    # Overall privacy level
    privacy_level: PrivacyLevel = PrivacyLevel.BALANCED
    
    # Data source permissions
    enabled_sources: Set[DataSourceType] = field(default_factory=lambda: {
        DataSourceType.EMAIL, 
        DataSourceType.SLACK
    })
    
    # Slack-specific settings
    slack_settings: Dict = field(default_factory=lambda: {
        'process_dms': False,           # Don't process direct messages
        'process_private_channels': True,   # Process private strategic channels
        'excluded_channels': {          # Never process these channels
            'random', 'general', 'off-topic', 'social', 'lunch',
            'coffee', 'memes', 'personal', 'water-cooler',
            'announcements', 'birthday', 'holiday', 'fun'
        },
        'required_strategic_keywords': 1,  # Minimum strategic keywords needed
        'minimum_message_length': 10,      # Skip very short messages
        'minimum_relevance_score': 0.3     # Strategic relevance threshold
    })
    
    # Email-specific settings  
    email_settings: Dict = field(default_factory=lambda: {
        'process_personal_emails': False,   # Only business emails
        'excluded_domains': {               # Skip emails from these domains
            'noreply.com', 'notifications.com', 'marketing.com'
        },
        'minimum_relevance_score': 0.2      # Lower threshold for emails
    })
    
    # Contact enrichment settings
    contact_settings: Dict = field(default_factory=lambda: {
        'enable_web_scraping': True,        # Allow web research
        'enable_linkedin_lookup': False,    # Disable LinkedIn by default
        'store_personal_details': False,    # Only business context
        'confidence_threshold': 0.5         # Minimum confidence for storage
    })
    
    # Data retention settings
    retention_settings: Dict = field(default_factory=lambda: {
        'knowledge_tree_retention_days': 90,   # Keep knowledge trees for 90 days
        'raw_message_retention_days': 30,      # Keep raw messages for 30 days
        'contact_data_retention_days': 365,    # Keep contact data for 1 year
        'auto_cleanup_enabled': True           # Automatically cleanup old data
    })

class PrivacyManager:
    """Manages privacy settings and data filtering"""
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.settings = self._load_user_privacy_settings()
    
    def _load_user_privacy_settings(self) -> PrivacySettings:
        """Load user's privacy settings from database"""
        # In production, this would load from database
        # For now, return default settings
        return PrivacySettings()
    
    def should_process_slack_message(self, channel_name: str, message_content: str, 
                                   is_dm: bool = False, is_private: bool = False) -> Dict:
        """Determine if a Slack message should be processed based on privacy settings"""
        
        # Check if Slack processing is enabled
        if DataSourceType.SLACK not in self.settings.enabled_sources:
            return {
                'should_process': False,
                'reason': 'Slack processing disabled in privacy settings'
            }
        
        # Check DM policy
        if is_dm and not self.settings.slack_settings['process_dms']:
            return {
                'should_process': False,
                'reason': 'Direct message processing disabled'
            }
        
        # Check private channel policy
        if is_private and not self.settings.slack_settings['process_private_channels']:
            return {
                'should_process': False,
                'reason': 'Private channel processing disabled'
            }
        
        # Check excluded channels
        excluded_channels = self.settings.slack_settings['excluded_channels']
        if any(excluded in channel_name.lower() for excluded in excluded_channels):
            return {
                'should_process': False,
                'reason': f'Channel #{channel_name} is in user exclusion list'
            }
        
        # Check message length
        min_length = self.settings.slack_settings['minimum_message_length']
        if len(message_content.strip()) < min_length:
            return {
                'should_process': False,
                'reason': f'Message too short (minimum {min_length} characters)'
            }
        
        # Check strategic keyword requirement
        strategic_keywords = [
            'strategy', 'roadmap', 'vision', 'goals', 'objectives',
            'partnership', 'acquisition', 'funding', 'competitive',
            'market', 'decision', 'priority', 'budget', 'project',
            'customer', 'revenue', 'milestone', 'deadline'
        ]
        
        required_keywords = self.settings.slack_settings['required_strategic_keywords']
        found_keywords = sum(1 for keyword in strategic_keywords 
                           if keyword in message_content.lower())
        
        if found_keywords < required_keywords:
            return {
                'should_process': False,
                'reason': f'Insufficient strategic keywords ({found_keywords}/{required_keywords})'
            }
        
        return {
            'should_process': True,
            'reason': 'Passed all privacy filters'
        }
    
    def should_process_email(self, sender_email: str, subject: str, content: str) -> Dict:
        """Determine if an email should be processed based on privacy settings"""
        
        # Check if email processing is enabled
        if DataSourceType.EMAIL not in self.settings.enabled_sources:
            return {
                'should_process': False,
                'reason': 'Email processing disabled in privacy settings'
            }
        
        # Check excluded domains
        excluded_domains = self.settings.email_settings['excluded_domains']
        sender_domain = sender_email.split('@')[1] if '@' in sender_email else ''
        
        if sender_domain in excluded_domains:
            return {
                'should_process': False,
                'reason': f'Sender domain {sender_domain} is excluded'
            }
        
        # Check for personal vs business context
        if not self.settings.email_settings['process_personal_emails']:
            personal_indicators = [
                'personal', 'family', 'friend', 'vacation', 'birthday',
                'wedding', 'party', 'weekend', 'dinner', 'movie'
            ]
            
            combined_text = (subject + ' ' + content[:200]).lower()
            if any(indicator in combined_text for indicator in personal_indicators):
                return {
                    'should_process': False,
                    'reason': 'Personal email content detected'
                }
        
        return {
            'should_process': True,
            'reason': 'Passed all privacy filters'
        }
    
    def should_enrich_contact(self, contact_email: str, confidence_score: float) -> Dict:
        """Determine if contact enrichment should be performed"""
        
        # Check confidence threshold
        min_confidence = self.settings.contact_settings['confidence_threshold']
        if confidence_score < min_confidence:
            return {
                'should_enrich': False,
                'reason': f'Confidence {confidence_score:.2f} below threshold {min_confidence}'
            }
        
        # Check web scraping permission
        if not self.settings.contact_settings['enable_web_scraping']:
            return {
                'should_enrich': False,
                'reason': 'Web scraping disabled in privacy settings'
            }
        
        return {
            'should_enrich': True,
            'reason': 'Contact enrichment approved'
        }
    
    def get_data_retention_policy(self) -> Dict:
        """Get data retention policy for cleanup processes"""
        return {
            'knowledge_tree_days': self.settings.retention_settings['knowledge_tree_retention_days'],
            'raw_message_days': self.settings.retention_settings['raw_message_retention_days'],
            'contact_data_days': self.settings.retention_settings['contact_data_retention_days'],
            'auto_cleanup': self.settings.retention_settings['auto_cleanup_enabled']
        }
    
    def update_privacy_settings(self, new_settings: Dict) -> bool:
        """Update user's privacy settings"""
        try:
            # Validate and update settings
            if 'privacy_level' in new_settings:
                self.settings.privacy_level = PrivacyLevel(new_settings['privacy_level'])
            
            if 'slack_settings' in new_settings:
                self.settings.slack_settings.update(new_settings['slack_settings'])
            
            if 'email_settings' in new_settings:
                self.settings.email_settings.update(new_settings['email_settings'])
            
            # Save to database in production
            self._save_privacy_settings()
            
            return True
        except Exception as e:
            return False
    
    def _save_privacy_settings(self):
        """Save privacy settings to database"""
        # In production, save to database
        pass
    
    def get_privacy_summary(self) -> Dict:
        """Get a summary of current privacy settings"""
        return {
            'privacy_level': self.settings.privacy_level.value,
            'enabled_sources': [source.value for source in self.settings.enabled_sources],
            'slack_filtering': {
                'process_dms': self.settings.slack_settings['process_dms'],
                'excluded_channels': len(self.settings.slack_settings['excluded_channels']),
                'relevance_threshold': self.settings.slack_settings['minimum_relevance_score']
            },
            'email_filtering': {
                'process_personal': self.settings.email_settings['process_personal_emails'],
                'excluded_domains': len(self.settings.email_settings['excluded_domains'])
            },
            'contact_enrichment': {
                'web_scraping': self.settings.contact_settings['enable_web_scraping'],
                'linkedin_lookup': self.settings.contact_settings['enable_linkedin_lookup']
            },
            'data_retention': {
                'knowledge_trees': f"{self.settings.retention_settings['knowledge_tree_retention_days']} days",
                'raw_messages': f"{self.settings.retention_settings['raw_message_retention_days']} days"
            }
        }

# Default privacy configurations for different user types
PRIVACY_PRESETS = {
    'privacy_focused': PrivacySettings(
        privacy_level=PrivacyLevel.MINIMAL,
        enabled_sources={DataSourceType.EMAIL},
        slack_settings={
            'process_dms': False,
            'process_private_channels': False,
            'minimum_relevance_score': 0.7,
            'required_strategic_keywords': 2
        },
        contact_settings={
            'enable_web_scraping': False,
            'enable_linkedin_lookup': False,
            'store_personal_details': False
        }
    ),
    
    'balanced': PrivacySettings(
        privacy_level=PrivacyLevel.BALANCED
        # Uses default settings
    ),
    
    'comprehensive': PrivacySettings(
        privacy_level=PrivacyLevel.COMPREHENSIVE,
        enabled_sources={DataSourceType.EMAIL, DataSourceType.SLACK, DataSourceType.CALENDAR},
        slack_settings={
            'process_dms': True,
            'process_private_channels': True,
            'minimum_relevance_score': 0.2,
            'required_strategic_keywords': 0
        },
        contact_settings={
            'enable_web_scraping': True,
            'enable_linkedin_lookup': True,
            'store_personal_details': True
        }
    )
} 