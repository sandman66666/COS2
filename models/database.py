"""
Database Manager
===============
Simple database manager for the contact enrichment system.
"""

import asyncio
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)

class EmailObject:
    """Simple email object that mimics database model"""
    def __init__(self, email_data: Dict):
        self.id = email_data.get('id')
        self.sender = email_data.get('sender', '')
        self.recipients = email_data.get('recipients', [])
        self.subject = email_data.get('subject', '')
        self.body_text = email_data.get('body_text', '')
        self.body_html = email_data.get('body_html', '')
        self.email_date = email_data.get('email_date')

class DatabaseManager:
    """
    Simple database manager for development and testing
    """
    
    def __init__(self):
        # In-memory storage for development
        self.users = {}
        self.emails = {}
        self.contacts = {}
        self.enrichments = {}
    
    def get_user_emails(self, user_id: int, limit: int = 1000) -> List[EmailObject]:
        """
        Get user's emails for content analysis
        
        Args:
            user_id: User ID
            limit: Maximum number of emails to return
            
        Returns:
            List of EmailObject instances
        """
        user_emails = self.emails.get(user_id, [])
        # Convert dict emails to EmailObject instances
        email_objects = [EmailObject(email_dict) for email_dict in user_emails[:limit]]
        return email_objects
    
    async def store_contact_enrichment(self, user_id: int, email: str, enrichment_data: Dict):
        """
        Store contact enrichment result
        
        Args:
            user_id: User ID
            email: Contact email
            enrichment_data: Enrichment result data
        """
        if user_id not in self.enrichments:
            self.enrichments[user_id] = {}
        
        self.enrichments[user_id][email.lower()] = {
            **enrichment_data,
            'stored_at': datetime.utcnow().isoformat()
        }
        
        logger.info(f"Stored enrichment for {email} (user {user_id})")
    
    async def get_contact_enrichment(self, user_id: int, email: str) -> Optional[Dict]:
        """
        Get stored contact enrichment
        
        Args:
            user_id: User ID
            email: Contact email
            
        Returns:
            Stored enrichment data or None
        """
        user_enrichments = self.enrichments.get(user_id, {})
        return user_enrichments.get(email.lower())
    
    def create_or_update_contact(self, user_id: int, contact_data: Dict) -> Dict:
        """
        Create or update a contact
        
        Args:
            user_id: User ID
            contact_data: Contact information
            
        Returns:
            Updated contact data
        """
        if user_id not in self.contacts:
            self.contacts[user_id] = {}
        
        email = contact_data.get('email', '').lower()
        if email:
            existing = self.contacts[user_id].get(email, {})
            updated = {
                **existing,
                **contact_data,
                'updated_at': datetime.utcnow().isoformat()
            }
            self.contacts[user_id][email] = updated
            return updated
        
        return contact_data
    
    def get_contact(self, user_id: int, email: str) -> Optional[Dict]:
        """
        Get a contact by email
        
        Args:
            user_id: User ID
            email: Contact email
            
        Returns:
            Contact data or None
        """
        user_contacts = self.contacts.get(user_id, {})
        return user_contacts.get(email.lower())
    
    def add_sample_emails(self, user_id: int, sample_emails: List[Dict]):
        """
        Add sample emails for testing (development only)
        
        Args:
            user_id: User ID
            sample_emails: List of sample email data
        """
        if user_id not in self.emails:
            self.emails[user_id] = []
        
        self.emails[user_id].extend(sample_emails)
        logger.info(f"Added {len(sample_emails)} sample emails for user {user_id}")

# Global database manager instance
_db_manager = None

def get_db_manager() -> DatabaseManager:
    """
    Get the global database manager instance
    
    Returns:
        DatabaseManager instance
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
        # Auto-setup sample data for testing (development only)
        if os.getenv('ENV') != 'production':
            setup_sample_data(1)  # Setup for default test user
    return _db_manager

# Convenience functions
def setup_sample_data(user_id: int = 1):
    """
    Set up sample data for testing the enrichment system
    
    Args:
        user_id: User ID to set up data for
    """
    db = get_db_manager()
    
    # Sample emails with rich signatures and content for testing
    sample_emails = [
        {
            'id': 1,
            'sender': 'john.doe@techcorp.com',
            'recipients': ['user@company.com'],
            'subject': 'Re: Project Update',
            'body_text': '''Hi there,

Thanks for the update on the project. I've reviewed the latest changes and they look great.

Let's schedule a follow-up meeting next week to discuss the next steps.

Best regards,
John Doe
Senior Software Engineer
TechCorp Solutions
Phone: +1 (555) 123-4567
Email: john.doe@techcorp.com
www.techcorp.com

---
This email contains confidential information.''',
            'email_date': datetime.utcnow()
        },
        {
            'id': 2,
            'sender': 'jane.smith@startup.io',
            'recipients': ['user@company.com'],
            'subject': 'Partnership Proposal',
            'body_text': '''Hello,

I hope this email finds you well. I'm reaching out regarding a potential partnership opportunity between our companies.

Our startup specializes in AI-driven analytics and I believe there could be great synergy with your team.

Would you be available for a call this week to discuss further?

Best,
Jane Smith
Co-Founder & CTO
StartupAI Inc.
Mobile: +1 (555) 987-6543
jane@startup.io
https://startup.ai

StartupAI Inc. | Revolutionizing Analytics
456 Innovation Drive, Tech City, CA 94000''',
            'email_date': datetime.utcnow()
        },
        {
            'id': 3,
            'sender': 'ceo@bigcompany.com',
            'recipients': ['user@company.com'],
            'subject': 'Strategic Initiative Discussion',
            'body_text': '''Dear Team,

I wanted to share some thoughts on our Q4 strategic initiatives and get your input on the technology roadmap.

Our focus areas include:
- Cloud migration
- AI/ML implementation  
- Customer experience enhancement

Looking forward to our discussion at the board meeting.

Regards,
Sarah Johnson
Chief Executive Officer
BigCompany Corp
Direct: +1 (555) 555-0123
sarah.johnson@bigcompany.com

BigCompany Corp | Fortune 500 Leader
1234 Corporate Blvd, Suite 500
Business City, ST 12345
www.bigcompany.com''',
            'email_date': datetime.utcnow()
        },
        {
            'id': 4,
            'sender': 'john.doe@techcorp.com',
            'recipients': ['user@company.com'],
            'subject': 'Follow-up on Python ML project',
            'body_text': '''Hi again,

I wanted to follow up on our discussion about the machine learning project. I've been working extensively with Python and TensorFlow for the past 5 years and would love to share some insights.

Our team at TechCorp has successfully deployed several ML models in production, particularly in the areas of natural language processing and predictive analytics.

Would you like to set up a call to discuss the technical architecture?

Best,
John Doe
Senior Software Engineer | Machine Learning Team
TechCorp Solutions
Direct: +1 (555) 123-4567''',
            'email_date': datetime.utcnow()
        }
    ]
    
    db.add_sample_emails(user_id, sample_emails)
    logger.info(f"Sample data setup complete for user {user_id}") 