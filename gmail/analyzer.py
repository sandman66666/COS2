# gmail/analyzer.py
"""
Gmail Analyzer for Trusted Contacts
==================================
Analyzes sent emails to identify trusted contacts based on communication patterns.
Core innovation: Uses sent emails to identify users' trusted network.
"""

import re
import asyncio
import json
from datetime import datetime, timedelta, timezone
from collections import Counter, defaultdict
from typing import Dict, List, Set, Tuple, Optional, Any

from config.constants import (
    TrustTiers, EmailMetadata, 
    TRUST_THRESHOLD_HIGH, TRUST_THRESHOLD_MEDIUM,
    DOMAINS_TO_IGNORE, MAX_DOMAINS_PER_USER
)
from utils.logging import structured_logger as logger
from gmail.client import GmailClient
from storage.storage_manager import get_storage_manager

class SentEmailAnalyzer:
    """
    Analyzes sent emails to extract trusted contacts and communication patterns
    Ensures proper multi-tenant isolation for user data
    """
    
    def __init__(self, user_id: int, storage_manager=None):
        """
        Initialize analyzer for a specific user
        
        Args:
            user_id: User ID for multi-tenant isolation
            storage_manager: Optional pre-initialized storage manager
        """
        self.user_id = user_id
        self.storage_manager = storage_manager
        self.gmail_client = None
    
    async def initialize(self):
        """Initialize connections and resources"""
        if not self.storage_manager:
            self.storage_manager = await get_storage_manager()
            
        self.gmail_client = GmailClient(user_id=self.user_id)
        await self.gmail_client.connect(self.storage_manager)
    
    async def extract_trusted_contacts(
        self, 
        lookback_days: int = 180,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Extract trusted contacts from sent emails
        
        Args:
            lookback_days: Days to look back for emails
            force_refresh: Force refresh even if cached data exists
            
        Returns:
            Dictionary with extracted contacts and stats
        """
        # Check cache first unless force refresh requested
        if not force_refresh:
            cached_contacts = await self.storage_manager.cache.get_user_data(
                self.user_id, 'trusted_contacts'
            )
            if cached_contacts:
                logger.info(
                    "Using cached trusted contacts", 
                    user_id=self.user_id,
                    count=len(cached_contacts.get('contacts', []))
                )
                return cached_contacts
        
        if not self.gmail_client:
            await self.initialize()
            
        try:
            # Calculate date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=lookback_days)
            
            # Get sent emails
            sent_emails = await self.gmail_client.get_sent_emails(
                max_results=2000,  # Reasonable limit for sent emails
                start_date=start_date,
                end_date=end_date
            )
            
            if not sent_emails:
                logger.warning(
                    "No sent emails found", 
                    user_id=self.user_id,
                    lookback_days=lookback_days
                )
                return {
                    'success': False,
                    'error': 'No sent emails found',
                    'contacts': []
                }
            
            # Process emails to extract contacts
            contacts_data = self._analyze_sent_emails(sent_emails)
            
            # Cache results
            await self.storage_manager.cache.cache_user_data(
                self.user_id, 
                'trusted_contacts',
                contacts_data,
                3600 * 24  # Cache for 24 hours
            )
            
            # Store contacts in database
            if contacts_data.get('contacts'):
                await self.storage_manager.store_trusted_contacts(
                    self.user_id, 
                    contacts_data.get('contacts', [])
                )
            
            return contacts_data
            
        except Exception as e:
            logger.error(
                "Error extracting trusted contacts", 
                user_id=self.user_id,
                error=str(e)
            )
            return {
                'success': False,
                'error': str(e),
                'contacts': []
            }
    
    def _analyze_sent_emails(self, emails: List[Dict]) -> Dict[str, Any]:
        """
        Analyze sent emails to extract trusted contacts
        
        Core innovation: This method implements the key insight that 
        sent emails reveal trusted contacts based on frequency and recency
        
        Args:
            emails: List of sent email messages
            
        Returns:
            Dictionary with contacts and stats
        """
        # Track email counts and most recent communication
        email_counts = Counter()
        last_email_date = {}
        email_subjects = defaultdict(list)
        domains = Counter()
        
        # Process each email
        for email in emails:
            # Get recipients from To, CC, and BCC fields
            recipients = []
            recipients.extend(email.get(EmailMetadata.TO, []))
            recipients.extend(email.get(EmailMetadata.CC, []))
            recipients.extend(email.get(EmailMetadata.BCC, []))
            
            # Extract date and ensure it's timezone-aware
            date_str = email.get(EmailMetadata.DATE)
            try:
                # Parse the date string and ensure it's timezone-aware
                if date_str:
                    # Handle various date formats
                    if 'Z' in date_str:
                        # UTC format with Z
                        email_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    elif '+' in date_str or '-' in date_str[-6:]:
                        # Already has timezone info
                        email_date = datetime.fromisoformat(date_str)
                    else:
                        # No timezone info, assume UTC
                        email_date = datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc)
                else:
                    # No date, use current time
                    email_date = datetime.now(timezone.utc)
                    
                # Double-check timezone awareness
                if email_date.tzinfo is None:
                    email_date = email_date.replace(tzinfo=timezone.utc)
                    
            except (ValueError, TypeError) as e:
                # If parsing fails, use current time in UTC
                logger.warning(f"Failed to parse email date '{date_str}': {e}")
                email_date = datetime.now(timezone.utc)
            
            # Extract subject for context
            subject = email.get(EmailMetadata.SUBJECT, '(No Subject)')
            
            # Process each recipient
            for recipient in recipients:
                # Skip empty or invalid addresses
                if not recipient or '@' not in recipient:
                    continue
                    
                # Extract domain for domain analysis
                domain = recipient.split('@')[1].lower()
                
                # Skip common domain types we don't want to analyze
                if any(ignored in domain for ignored in DOMAINS_TO_IGNORE):
                    continue
                    
                # Update counts and recency
                email_counts[recipient] += 1
                
                # Track most recent email date (ensure timezone-aware comparison)
                if recipient not in last_email_date:
                    last_email_date[recipient] = email_date
                else:
                    # Ensure both dates are timezone-aware before comparison
                    existing_date = last_email_date[recipient]
                    if existing_date.tzinfo is None:
                        existing_date = existing_date.replace(tzinfo=timezone.utc)
                        last_email_date[recipient] = existing_date
                    
                    if email_date > existing_date:
                        last_email_date[recipient] = email_date
                
                # Store subjects (limited to avoid data bloat)
                if len(email_subjects[recipient]) < 5:
                    # Truncate subject if too long
                    trimmed_subject = subject[:80] + ('...' if len(subject) > 80 else '')
                    email_subjects[recipient].append(trimmed_subject)
                
                # Track domains for organization analysis
                domains[domain] += 1
        
        # Build contact list with trust tier assignment
        contacts = []
        
        # Get top domains (limit to control memory usage)
        top_domains = domains.most_common(MAX_DOMAINS_PER_USER)
        
        # Get current time for recency calculations
        current_time = datetime.now(timezone.utc)
        
        # Now build the list of contacts with trust tiers
        for email_address, count in email_counts.most_common():
            # Calculate recency score (higher for more recent emails)
            last_contact_date = last_email_date[email_address]
            
            # Ensure timezone awareness before calculation
            if last_contact_date.tzinfo is None:
                last_contact_date = last_contact_date.replace(tzinfo=timezone.utc)
                last_email_date[email_address] = last_contact_date  # Update stored value too
            
            # Calculate days since last contact
            try:
                days_since = (current_time - last_contact_date).days
                recency_score = max(0, 100 - min(days_since, 100))
            except Exception as e:
                logger.warning(f"Error calculating recency for {email_address}: {e}")
                recency_score = 0
                days_since = 999
            
            # Combined score based on frequency and recency
            combined_score = (count * 0.7) + (recency_score * 0.3)
            
            # Assign trust tier based on score
            trust_tier = TrustTiers.LOW
            if combined_score >= TRUST_THRESHOLD_HIGH:
                trust_tier = TrustTiers.HIGH
            elif combined_score >= TRUST_THRESHOLD_MEDIUM:
                trust_tier = TrustTiers.MEDIUM
            
            # Extract domain for organization grouping
            domain = email_address.split('@')[1].lower()
            
            # Create contact record with timezone-aware ISO string
            contact = {
                'email': email_address,
                'frequency': count,
                'last_contact': last_contact_date.isoformat() if last_contact_date and last_contact_date.tzinfo else None,  # Only create ISO if timezone-aware
                'trust_tier': trust_tier,
                'domain': domain,
                'recent_subjects': email_subjects[email_address],
                'score': round(combined_score, 2),
                'days_since_contact': days_since
            }
            
            # Additional safety check - ensure last_contact is string, not datetime
            if isinstance(contact.get('last_contact'), datetime):
                logger.warning(f"Contact {email_address} has datetime object instead of string - converting")
                dt = contact['last_contact']
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                contact['last_contact'] = dt.isoformat()
            
            contacts.append(contact)
        
        # Return complete analysis
        return {
            'success': True,
            'contacts': contacts,
            'total_sent_emails': len(emails),
            'top_domains': [{"domain": d, "count": c} for d, c in top_domains],
            'trust_tier_counts': {
                'high': sum(1 for c in contacts if c['trust_tier'] == TrustTiers.HIGH),
                'medium': sum(1 for c in contacts if c['trust_tier'] == TrustTiers.MEDIUM),
                'low': sum(1 for c in contacts if c['trust_tier'] == TrustTiers.LOW)
            },
            'analysis_timestamp': datetime.now(timezone.utc).isoformat(),
        }
    
    async def enrich_contacts(self, contacts: List[Dict]) -> List[Dict]:
        """
        Enrich contacts with additional data
        
        Args:
            contacts: List of contact dictionaries
            
        Returns:
            Enriched contact list
        """
        # In a real implementation, this would call the contact enrichment service
        # to get additional data from LinkedIn, etc.
        # For now, we'll just add a placeholder for enrichment status
        
        enriched_contacts = []
        
        for contact in contacts:
            # Clone the contact to avoid modifying the original
            enriched = contact.copy()
            
            # Add enrichment placeholder
            enriched['enrichment_status'] = 'pending'
            enriched['enriched_at'] = None
            
            enriched_contacts.append(enriched)
        
        return enriched_contacts


async def analyze_user_contacts(user_id: int) -> Dict[str, Any]:
    """
    Helper function to analyze contacts for a user
    
    Args:
        user_id: User ID to analyze
        
    Returns:
        Analysis results
    """
    storage_manager = await get_storage_manager()
    analyzer = SentEmailAnalyzer(user_id, storage_manager)
    
    # Extract trusted contacts with default lookback of 180 days
    results = await analyzer.extract_trusted_contacts()
    
    return results
