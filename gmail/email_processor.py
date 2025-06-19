"""
Gmail Email Processor Module
===========================
Processes Gmail emails using the Gmail API for analysis and storage.
"""

import os
import base64
from typing import Dict, List, Optional, Any, Tuple, Generator
import time
from datetime import datetime, timedelta
import email
from email.message import Message
from email.header import decode_header

import googleapiclient.discovery
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError

from models.email import Email, EmailAttachment
from storage.postgres_client import PostgresClient
from storage.vector_client import VectorClient
from utils.logging import get_logger

logger = get_logger(__name__)


class GmailEmailProcessor:
    """
    Processes emails from Gmail API.
    
    Handles:
    - Fetching emails with batch processing
    - Email parsing and normalization
    - Conversion to internal Email model
    - Storage in relational and vector databases
    """
    
    def __init__(
        self,
        user_id: str,
        access_token: str,
        postgres_client: PostgresClient,
        vector_client: Optional[VectorClient] = None,
        batch_size: int = 100
    ):
        """
        Initialize Gmail Email Processor.
        
        Args:
            user_id: User ID for multi-tenant support
            access_token: Valid Gmail API access token
            postgres_client: PostgreSQL client for storage
            vector_client: Optional ChromaDB client for vector storage
            batch_size: Batch size for Gmail API requests
        """
        self.user_id = user_id
        self.access_token = access_token
        self.postgres_client = postgres_client
        self.vector_client = vector_client
        self.batch_size = batch_size
        
        # Build Gmail API service
        self.gmail_service = self._build_gmail_service()
        
    def _build_gmail_service(self):
        """
        Build Gmail API service.
        
        Returns:
            Gmail API service
        """
        credentials = Credentials(token=self.access_token)
        return googleapiclient.discovery.build('gmail', 'v1', credentials=credentials)
    
    def fetch_emails(
        self, 
        query: str = None, 
        max_emails: int = 500,
        include_attachments: bool = True
    ) -> List[Email]:
        """
        Fetch emails from Gmail API matching query.
        
        Args:
            query: Gmail search query (None for all emails)
            max_emails: Maximum number of emails to fetch
            include_attachments: Whether to include attachments
            
        Returns:
            List of Email objects
        """
        try:
            # Initial empty list to store emails
            emails = []
            
            # Get message IDs
            message_ids = self._get_message_ids(query, max_emails)
            
            logger.info(f"Found {len(message_ids)} emails for user {self.user_id}")
            
            # Process in batches
            for i in range(0, len(message_ids), self.batch_size):
                batch = message_ids[i:i + self.batch_size]
                batch_emails = self._process_email_batch(batch, include_attachments)
                emails.extend(batch_emails)
                
                logger.info(f"Processed batch of {len(batch)} emails for user {self.user_id}")
                
                # Rate limiting sleep
                if i + self.batch_size < len(message_ids):
                    time.sleep(1)  # Avoid hitting rate limits
            
            return emails
            
        except HttpError as error:
            logger.error(f"Error fetching emails: {str(error)}")
            return []
    
    def _get_message_ids(self, query: str = None, max_emails: int = 500) -> List[str]:
        """
        Get message IDs matching query.
        
        Args:
            query: Gmail search query
            max_emails: Maximum number of emails to fetch
            
        Returns:
            List of message IDs
        """
        message_ids = []
        page_token = None
        
        while len(message_ids) < max_emails:
            try:
                # Request messages list
                result = self.gmail_service.users().messages().list(
                    userId='me',
                    q=query,
                    pageToken=page_token,
                    maxResults=min(max_emails - len(message_ids), 500)  # API max is 500
                ).execute()
                
                # Extract message IDs
                messages = result.get('messages', [])
                if not messages:
                    break
                    
                message_ids.extend([msg['id'] for msg in messages])
                
                # Check if there are more pages
                page_token = result.get('nextPageToken')
                if not page_token:
                    break
                    
            except HttpError as error:
                logger.error(f"Error getting message IDs: {str(error)}")
                break
        
        return message_ids[:max_emails]
    
    def _process_email_batch(self, message_ids: List[str], include_attachments: bool) -> List[Email]:
        """
        Process a batch of emails.
        
        Args:
            message_ids: List of message IDs to process
            include_attachments: Whether to include attachments
            
        Returns:
            List of Email objects
        """
        emails = []
        
        for message_id in message_ids:
            try:
                # Get message data
                message = self.gmail_service.users().messages().get(
                    userId='me',
                    id=message_id,
                    format='full'
                ).execute()
                
                # Parse message
                email_obj = self._parse_email(message, include_attachments)
                if email_obj:
                    emails.append(email_obj)
                    
            except HttpError as error:
                logger.error(f"Error processing email {message_id}: {str(error)}")
                continue
        
        return emails
    
    def _parse_email(self, message: Dict[str, Any], include_attachments: bool) -> Optional[Email]:
        """
        Parse Gmail API message into Email object.
        
        Args:
            message: Gmail API message
            include_attachments: Whether to include attachments
            
        Returns:
            Email object or None if parsing failed
        """
        try:
            # Extract headers
            headers = {}
            for header in message.get('payload', {}).get('headers', []):
                name = header.get('name', '').lower()
                value = header.get('value', '')
                headers[name] = value
            
            # Extract basic metadata
            email_id = message.get('id')
            thread_id = message.get('threadId')
            labels = message.get('labelIds', [])
            internal_date = int(message.get('internalDate', '0')) / 1000  # Convert to seconds
            
            # Extract email parts
            parts = self._get_parts(message.get('payload', {}))
            
            # Get plain text and HTML parts
            plain_text = ''
            html_body = ''
            attachments = []
            
            for part in parts:
                mime_type = part.get('mimeType', '')
                
                if mime_type == 'text/plain':
                    plain_text = self._decode_body(part)
                elif mime_type == 'text/html':
                    html_body = self._decode_body(part)
                elif include_attachments and 'filename' in part and part.get('filename'):
                    # This is an attachment
                    attachment = self._extract_attachment(part)
                    if attachment:
                        attachments.append(attachment)
            
            # Create the Email object
            email_obj = Email(
                user_id=self.user_id,
                email_id=email_id,
                thread_id=thread_id,
                subject=headers.get('subject', ''),
                sender=headers.get('from', ''),
                sender_name=self._extract_name_from_email(headers.get('from', '')),
                recipient=headers.get('to', ''),
                cc=headers.get('cc', ''),
                bcc=headers.get('bcc', ''),
                date=datetime.fromtimestamp(internal_date),
                labels=labels,
                body_text=plain_text,
                body_html=html_body,
                attachments=attachments,
                is_read='UNREAD' not in labels,
                is_sent='SENT' in labels,
                is_draft='DRAFT' in labels,
                is_starred='STARRED' in labels,
                is_important='IMPORTANT' in labels,
                gmail_message_id=message.get('id')
            )
            
            return email_obj
            
        except Exception as e:
            logger.error(f"Error parsing email: {str(e)}")
            return None
    
    def _get_parts(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract all parts from a message payload.
        
        Args:
            payload: Message payload
            
        Returns:
            List of message parts
        """
        parts = []
        
        # Add the main part
        if 'body' in payload:
            parts.append(payload)
        
        # Add sub-parts recursively
        for part in payload.get('parts', []):
            parts.extend(self._get_parts(part))
        
        return parts
    
    def _decode_body(self, part: Dict[str, Any]) -> str:
        """
        Decode message part body.
        
        Args:
            part: Message part
            
        Returns:
            Decoded body text
        """
        try:
            # Check if there's a body
            if not part.get('body', {}).get('data'):
                return ''
            
            # Decode from base64url to UTF-8
            body_data = part['body']['data']
            body_data = body_data.replace('-', '+').replace('_', '/')
            padding = len(body_data) % 4
            if padding:
                body_data += '=' * (4 - padding)
                
            body_bytes = base64.b64decode(body_data)
            
            # Try to decode as UTF-8
            try:
                return body_bytes.decode('utf-8')
            except UnicodeDecodeError:
                # Try other encodings
                for encoding in ['latin-1', 'iso-8859-1', 'windows-1252']:
                    try:
                        return body_bytes.decode(encoding)
                    except UnicodeDecodeError:
                        pass
                        
                # Fallback to latin-1 (should never fail)
                return body_bytes.decode('latin-1', errors='replace')
                
        except Exception as e:
            logger.error(f"Error decoding body: {str(e)}")
            return ''
    
    def _extract_attachment(self, part: Dict[str, Any]) -> Optional[EmailAttachment]:
        """
        Extract attachment data.
        
        Args:
            part: Message part containing attachment
            
        Returns:
            EmailAttachment object or None if extraction failed
        """
        try:
            filename = part.get('filename', '')
            mime_type = part.get('mimeType', '')
            attachment_id = part.get('body', {}).get('attachmentId')
            size = part.get('body', {}).get('size', 0)
            
            # Create attachment without data (which can be fetched on demand)
            attachment = EmailAttachment(
                attachment_id=attachment_id,
                filename=filename,
                mime_type=mime_type,
                size=size
            )
            
            return attachment
            
        except Exception as e:
            logger.error(f"Error extracting attachment: {str(e)}")
            return None
    
    def _extract_name_from_email(self, from_header: str) -> str:
        """
        Extract name from email address header.
        
        Args:
            from_header: From header value
            
        Returns:
            Extracted name or empty string if not found
        """
        if not from_header:
            return ''
            
        # Check for format: "Name" <email@example.com>
        if '<' in from_header and '>' in from_header:
            name = from_header.split('<')[0].strip()
            
            # Remove quotes if present
            if name.startswith('"') and name.endswith('"'):
                name = name[1:-1]
                
            return name
            
        # No name, just email
        return ''
    
    def fetch_attachment(self, email_id: str, attachment_id: str) -> Optional[bytes]:
        """
        Fetch attachment data from Gmail API.
        
        Args:
            email_id: Gmail message ID
            attachment_id: Attachment ID
            
        Returns:
            Attachment data as bytes, or None if failed
        """
        try:
            attachment = self.gmail_service.users().messages().attachments().get(
                userId='me',
                messageId=email_id,
                id=attachment_id
            ).execute()
            
            if 'data' in attachment:
                # Decode attachment data
                data = attachment['data'].replace('-', '+').replace('_', '/')
                padding = len(data) % 4
                if padding:
                    data += '=' * (4 - padding)
                    
                return base64.b64decode(data)
            
            return None
            
        except HttpError as error:
            logger.error(f"Error fetching attachment: {str(error)}")
            return None
    
    def process_and_store_emails(
        self, 
        query: str = None,
        max_emails: int = 500,
        include_attachments: bool = True,
        save_to_vector_db: bool = True
    ) -> int:
        """
        Fetch, process, and store emails.
        
        Args:
            query: Gmail search query
            max_emails: Maximum number of emails to fetch
            include_attachments: Whether to include attachments
            save_to_vector_db: Whether to save to vector database
            
        Returns:
            Number of emails processed
        """
        try:
            # Fetch emails
            emails = self.fetch_emails(query, max_emails, include_attachments)
            
            # Store emails
            count = 0
            for email_obj in emails:
                # Save to PostgreSQL
                success = email_obj.save(
                    postgres_client=self.postgres_client,
                    vector_client=self.vector_client if save_to_vector_db else None
                )
                
                if success:
                    count += 1
            
            logger.info(f"Successfully processed and stored {count} emails for user {self.user_id}")
            return count
            
        except Exception as e:
            logger.error(f"Error processing and storing emails: {str(e)}")
            return 0
            
    def update_email_labels(self, email_id: str, add_labels: List[str] = None, remove_labels: List[str] = None) -> bool:
        """
        Update Gmail labels for an email.
        
        Args:
            email_id: Gmail message ID
            add_labels: Labels to add
            remove_labels: Labels to remove
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Prepare request body
            body = {
                'addLabelIds': add_labels or [],
                'removeLabelIds': remove_labels or []
            }
            
            # Execute the modification
            result = self.gmail_service.users().messages().modify(
                userId='me',
                id=email_id,
                body=body
            ).execute()
            
            # Update in database
            if result and result.get('id') == email_id:
                # Get email from database
                email_data = self.postgres_client.find_one(
                    table='emails',
                    conditions={
                        'user_id': self.user_id,
                        'gmail_message_id': email_id
                    }
                )
                
                if email_data:
                    # Update labels
                    labels = set(email_data.get('labels', []))
                    if add_labels:
                        labels.update(add_labels)
                    if remove_labels:
                        labels.difference_update(remove_labels)
                    
                    # Update database
                    self.postgres_client.update(
                        table='emails',
                        conditions={
                            'user_id': self.user_id,
                            'gmail_message_id': email_id
                        },
                        data={
                            'labels': list(labels),
                            'is_read': 'UNREAD' not in labels,
                            'is_starred': 'STARRED' in labels,
                            'is_important': 'IMPORTANT' in labels
                        }
                    )
            
            return True
            
        except HttpError as error:
            logger.error(f"Error updating email labels: {str(error)}")
            return False
