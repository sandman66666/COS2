# gmail/client.py
"""
Gmail API Client
===============
Connect to Gmail API and retrieve emails for processing.
Multi-tenant support for separate user Gmail accounts.
"""

import base64
import email
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import googleapiclient.errors

from config.constants import EmailMetadata, TrustTiers, MAX_EMAILS_PER_REQUEST
from config.settings import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
from utils.logging import structured_logger as logger
from auth.gmail_auth import gmail_auth
from storage.storage_manager import get_storage_manager

class GmailClient:
    """Gmail API Client with multi-tenant user isolation"""
    
    def __init__(self, user_id: int = None, credentials: Credentials = None):
        """
        Initialize Gmail client for a specific user
        
        Args:
            user_id: User ID for multi-tenant isolation
            credentials: Optional pre-loaded credentials
        """
        self.user_id = user_id
        self.credentials = credentials
        self.service = None
    
    async def connect(self, storage_manager=None) -> bool:
        """
        Connect to Gmail API with user credentials
        
        Args:
            storage_manager: Optional storage manager instance
            
        Returns:
            True if connection successful
        """
        try:
            if not self.credentials and self.user_id:
                # First try to get credentials from session (for when DB is not available)
                from flask import session
                oauth_credentials = session.get('oauth_credentials')
                
                if oauth_credentials:
                    # Create credentials from session data
                    self.credentials = Credentials(
                        token=oauth_credentials.get('access_token'),
                        refresh_token=oauth_credentials.get('refresh_token'),
                        token_uri=oauth_credentials.get('token_uri', "https://oauth2.googleapis.com/token"),
                        client_id=oauth_credentials.get('client_id'),
                        client_secret=oauth_credentials.get('client_secret'),
                        scopes=oauth_credentials.get('scopes', [])
                    )
                    
                    # Set expiry if available
                    if oauth_credentials.get('expiry'):
                        self.credentials.expiry = datetime.fromtimestamp(oauth_credentials['expiry'])
                    
                    logger.info("Using OAuth credentials from session", user_id=self.user_id)
                
                else:
                    # Fall back to database credentials if available
                    if storage_manager:
                        try:
                            self.credentials = await gmail_auth.get_valid_credentials(self.user_id, storage_manager)
                        except Exception as db_error:
                            logger.warning("Failed to get credentials from database", error=str(db_error))
                    
                    if not self.credentials:
                        logger.error("No valid Gmail credentials", user_id=self.user_id)
                        return False
            
            # Build Gmail API service
            self.service = build('gmail', 'v1', credentials=self.credentials)
            logger.info("Connected to Gmail API", user_id=self.user_id)
            return True
            
        except Exception as e:
            logger.error("Gmail API connection error", error=str(e), user_id=self.user_id)
            return False
    
    async def get_sent_emails(
        self,
        max_results: int = 500,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict]:
        """
        Get sent emails from user's Gmail account
        
        Args:
            max_results: Maximum number of emails to retrieve
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            List of sent email messages
        """
        if not self.service:
            if not await self.connect():
                return []
        
        try:
            # Build query for sent emails
            query = "in:sent"
            
            # Add date filters if specified
            if start_date:
                query += f" after:{start_date.strftime('%Y/%m/%d')}"
            if end_date:
                query += f" before:{end_date.strftime('%Y/%m/%d')}"
            
            # Get list of sent messages (IDs only)
            results = []
            next_page_token = None
            total_retrieved = 0
            
            while total_retrieved < max_results:
                # Determine how many to request in this batch
                batch_size = min(MAX_EMAILS_PER_REQUEST, max_results - total_retrieved)
                
                # Make API call to get message IDs
                messages_response = self.service.users().messages().list(
                    userId='me',
                    q=query,
                    maxResults=batch_size,
                    pageToken=next_page_token
                ).execute()
                
                messages = messages_response.get('messages', [])
                
                if not messages:
                    break
                
                # Get full message details in parallel
                for msg in messages:
                    message_id = msg['id']
                    
                    # Get full message
                    msg_data = self.service.users().messages().get(
                        userId='me',
                        id=message_id,
                        format='full'
                    ).execute()
                    
                    # Parse email content
                    parsed_email = self._parse_message(msg_data)
                    if parsed_email:
                        results.append(parsed_email)
                    
                # Update counters
                total_retrieved += len(messages)
                
                # Check if there are more pages
                next_page_token = messages_response.get('nextPageToken')
                if not next_page_token:
                    break
                
                # Throttle requests to avoid quota issues
                time.sleep(0.1)
            
            logger.info(
                "Retrieved sent emails", 
                user_id=self.user_id,
                count=len(results)
            )
            
            return results
            
        except googleapiclient.errors.HttpError as e:
            logger.error("Gmail API error", error=str(e), user_id=self.user_id)
            return []
            
        except Exception as e:
            logger.error("Error retrieving sent emails", error=str(e))
            return []
    
    def _parse_message(self, msg_data: Dict) -> Optional[Dict]:
        """
        Parse Gmail message into structured format
        
        Args:
            msg_data: Raw message data from Gmail API
            
        Returns:
            Parsed message dictionary or None if parsing fails
        """
        try:
            # Extract headers
            headers = {}
            for header in msg_data.get('payload', {}).get('headers', []):
                name = header.get('name', '').lower()
                value = header.get('value', '')
                headers[name] = value
            
            # Extract basic metadata
            message_id = msg_data.get('id')
            thread_id = msg_data.get('threadId')
            
            # Get email addresses
            to_addresses = self._parse_email_addresses(headers.get('to', ''))
            from_address = self._parse_email_addresses(headers.get('from', ''))[0] if self._parse_email_addresses(headers.get('from', '')) else ''
            cc_addresses = self._parse_email_addresses(headers.get('cc', ''))
            bcc_addresses = self._parse_email_addresses(headers.get('bcc', ''))
            
            # Extract subject and date
            subject = headers.get('subject', '(No Subject)')
            date_str = headers.get('date', '')
            
            # Parse date
            try:
                # First try ISO format (which is what we're getting from Gmail API)
                if 'T' in date_str and ('+' in date_str or '-' in date_str[-6:] or date_str.endswith('Z')):
                    date_sent = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                else:
                    # Fall back to RFC 2822 format (traditional email headers)
                    date_sent = email.utils.parsedate_to_datetime(date_str)
            except:
                # Fallback to current time if parsing fails
                date_sent = datetime.utcnow()
            
            # Extract message body
            body_text = ""
            body_html = ""
            
            if 'payload' in msg_data and 'parts' in msg_data['payload']:
                for part in msg_data['payload']['parts']:
                    if part.get('mimeType') == 'text/plain' and 'body' in part and 'data' in part['body']:
                        body_text = base64.urlsafe_b64decode(
                            part['body']['data'].encode('ASCII')).decode('utf-8', errors='replace')
                    elif part.get('mimeType') == 'text/html' and 'body' in part and 'data' in part['body']:
                        body_html = base64.urlsafe_b64decode(
                            part['body']['data'].encode('ASCII')).decode('utf-8', errors='replace')
            elif 'payload' in msg_data and 'body' in msg_data['payload'] and 'data' in msg_data['payload']['body']:
                # Handle single-part messages
                data = msg_data['payload']['body']['data']
                if msg_data['payload'].get('mimeType') == 'text/plain':
                    body_text = base64.urlsafe_b64decode(data.encode('ASCII')).decode('utf-8', errors='replace')
                elif msg_data['payload'].get('mimeType') == 'text/html':
                    body_html = base64.urlsafe_b64decode(data.encode('ASCII')).decode('utf-8', errors='replace')
            
            # Create structured message
            parsed_message = {
                EmailMetadata.MESSAGE_ID: message_id,
                EmailMetadata.THREAD_ID: thread_id,
                EmailMetadata.FROM: from_address,
                EmailMetadata.TO: to_addresses,
                EmailMetadata.CC: cc_addresses,
                EmailMetadata.BCC: bcc_addresses,
                EmailMetadata.SUBJECT: subject,
                EmailMetadata.DATE: date_sent.isoformat(),
                EmailMetadata.BODY_TEXT: body_text,
                EmailMetadata.BODY_HTML: body_html,
                EmailMetadata.HEADERS: headers,
                EmailMetadata.IS_SENT: True,
                # Additional fields for our system
                'timestamp': date_sent.timestamp(),
                'processed_at': datetime.utcnow().isoformat(),
                'raw_size': len(str(msg_data))
            }
            
            return parsed_message
            
        except Exception as e:
            logger.error(
                "Error parsing Gmail message", 
                message_id=msg_data.get('id', 'unknown'),
                error=str(e)
            )
            return None
    
    def _parse_email_addresses(self, address_string: str) -> List[str]:
        """
        Parse email addresses from Gmail header string
        
        Args:
            address_string: String containing email addresses
            
        Returns:
            List of email addresses
        """
        if not address_string:
            return []
            
        try:
            # Parse addresses using email module
            addresses = email.utils.getaddresses([address_string])
            
            # Extract just the email part
            email_addresses = []
            for name, addr in addresses:
                if addr and '@' in addr:
                    email_addresses.append(addr.lower())
            
            return email_addresses
            
        except Exception as e:
            logger.error(f"Error parsing email addresses: {str(e)}")
            return []

    async def get_messages(
        self,
        query: str = "",
        max_results: int = 100,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict]:
        """
        Get messages from user's Gmail account with query
        
        Args:
            query: Gmail search query (e.g., 'after:2023/01/01')
            max_results: Maximum number of emails to retrieve
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            List of email messages
        """
        if not self.service:
            if not await self.connect():
                return []
        
        try:
            # Build search query
            search_query = query
            
            # Add date filters if specified and not already in query
            if start_date and 'after:' not in search_query:
                search_query += f" after:{start_date.strftime('%Y/%m/%d')}"
            if end_date and 'before:' not in search_query:
                search_query += f" before:{end_date.strftime('%Y/%m/%d')}"
            
            # Get list of messages (IDs only)
            results = []
            next_page_token = None
            total_retrieved = 0
            
            while total_retrieved < max_results:
                # Determine how many to request in this batch
                batch_size = min(MAX_EMAILS_PER_REQUEST, max_results - total_retrieved)
                
                # Make API call to get message IDs
                messages_response = self.service.users().messages().list(
                    userId='me',
                    q=search_query,
                    maxResults=batch_size,
                    pageToken=next_page_token
                ).execute()
                
                messages = messages_response.get('messages', [])
                
                if not messages:
                    break
                
                # Get full message details
                for msg in messages:
                    message_id = msg['id']
                    
                    # Get full message
                    msg_data = self.service.users().messages().get(
                        userId='me',
                        id=message_id,
                        format='full'
                    ).execute()
                    
                    # Parse email content
                    parsed_email = self._parse_message(msg_data)
                    if parsed_email:
                        results.append(parsed_email)
                    
                # Update counters
                total_retrieved += len(messages)
                
                # Check if there are more pages
                next_page_token = messages_response.get('nextPageToken')
                if not next_page_token:
                    break
                
                # Throttle requests to avoid quota issues
                time.sleep(0.1)
            
            logger.info(
                "Retrieved messages", 
                user_id=self.user_id,
                count=len(results),
                query=search_query
            )
            
            return results
            
        except googleapiclient.errors.HttpError as e:
            logger.error("Gmail API error", error=str(e), user_id=self.user_id)
            return []
            
        except Exception as e:
            logger.error("Error retrieving messages", error=str(e))
            return []

    def parse_message(self, msg_data: Dict) -> Optional[Dict]:
        """
        Public method to parse Gmail message into structured format
        (Alias for _parse_message for external use)
        
        Args:
            msg_data: Raw message data from Gmail API
            
        Returns:
            Parsed message dictionary or None if parsing fails
        """
        return self._parse_message(msg_data)
