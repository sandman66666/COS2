"""
Email Model for Strategic Intelligence System
============================================
Represents email data and provides methods for email analysis and classification.
"""

import hashlib
import json
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Set

from storage.postgres_client import PostgresClient
from storage.vector_client import VectorClient


@dataclass
class EmailMetadata:
    """Metadata extracted from an email"""
    subject: str
    sender: str
    sender_email: str
    recipient_emails: List[str]
    cc_emails: List[str] = field(default_factory=list)
    bcc_emails: List[str] = field(default_factory=list)
    date: datetime = None
    importance: str = "normal"
    thread_id: Optional[str] = None
    reply_to_id: Optional[str] = None
    has_attachments: bool = False
    is_draft: bool = False


@dataclass
class EmailAttachment:
    """Email attachment metadata"""
    filename: str
    content_type: str
    size: int
    attachment_id: str
    content_hash: Optional[str] = None


class Email:
    """Email model representing a single email message"""
    
    def __init__(
        self,
        user_id: str,
        email_id: str,
        metadata: EmailMetadata,
        body_text: str,
        body_html: Optional[str] = None,
        attachments: List[EmailAttachment] = None,
        vector_embedding: Optional[List[float]] = None
    ):
        self.user_id = user_id
        self.email_id = email_id
        self.metadata = metadata
        self.body_text = body_text
        self.body_html = body_html
        self.attachments = attachments or []
        self.vector_embedding = vector_embedding
        
        # Computed properties
        self._content_hash = None
        self._contacts_extracted = False
        self._sentiment_score = None
        self._topics = None
        self._action_items = None
        
    @property
    def content_hash(self) -> str:
        """Generate a content hash for email deduplication"""
        if not self._content_hash:
            content = f"{self.metadata.subject}|{self.body_text}"
            self._content_hash = hashlib.sha256(content.encode()).hexdigest()
        return self._content_hash
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert email to dictionary for storage"""
        return {
            "user_id": self.user_id,
            "email_id": self.email_id,
            "metadata": {
                "subject": self.metadata.subject,
                "sender": self.metadata.sender,
                "sender_email": self.metadata.sender_email,
                "recipient_emails": self.metadata.recipient_emails,
                "cc_emails": self.metadata.cc_emails,
                "bcc_emails": self.metadata.bcc_emails,
                "date": self.metadata.date.isoformat() if self.metadata.date else None,
                "importance": self.metadata.importance,
                "thread_id": self.metadata.thread_id,
                "reply_to_id": self.metadata.reply_to_id,
                "has_attachments": self.metadata.has_attachments,
                "is_draft": self.metadata.is_draft
            },
            "body_text": self.body_text,
            "body_html": self.body_html,
            "content_hash": self.content_hash,
            "attachments": [
                {
                    "filename": att.filename,
                    "content_type": att.content_type,
                    "size": att.size,
                    "attachment_id": att.attachment_id,
                    "content_hash": att.content_hash
                }
                for att in self.attachments
            ],
            "vector_embedding": self.vector_embedding,
            "sentiment_score": self._sentiment_score,
            "topics": self._topics,
            "action_items": self._action_items,
            "created_at": datetime.utcnow().isoformat()
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Email':
        """Create an Email instance from dictionary data"""
        metadata = EmailMetadata(
            subject=data["metadata"]["subject"],
            sender=data["metadata"]["sender"],
            sender_email=data["metadata"]["sender_email"],
            recipient_emails=data["metadata"]["recipient_emails"],
            cc_emails=data["metadata"].get("cc_emails", []),
            bcc_emails=data["metadata"].get("bcc_emails", []),
            date=datetime.fromisoformat(data["metadata"]["date"]) if data["metadata"].get("date") else None,
            importance=data["metadata"].get("importance", "normal"),
            thread_id=data["metadata"].get("thread_id"),
            reply_to_id=data["metadata"].get("reply_to_id"),
            has_attachments=data["metadata"].get("has_attachments", False),
            is_draft=data["metadata"].get("is_draft", False)
        )
        
        attachments = []
        for att_data in data.get("attachments", []):
            attachment = EmailAttachment(
                filename=att_data["filename"],
                content_type=att_data["content_type"],
                size=att_data["size"],
                attachment_id=att_data["attachment_id"],
                content_hash=att_data.get("content_hash")
            )
            attachments.append(attachment)
        
        email = cls(
            user_id=data["user_id"],
            email_id=data["email_id"],
            metadata=metadata,
            body_text=data["body_text"],
            body_html=data.get("body_html"),
            attachments=attachments,
            vector_embedding=data.get("vector_embedding")
        )
        
        # Set computed properties if available
        email._sentiment_score = data.get("sentiment_score")
        email._topics = data.get("topics")
        email._action_items = data.get("action_items")
        email._content_hash = data.get("content_hash")
        
        return email
    
    def save(self, postgres_client: PostgresClient, vector_client: VectorClient = None) -> bool:
        """
        Save email to database
        
        Args:
            postgres_client: PostgreSQL client
            vector_client: Optional vector client for embedding storage
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert to dictionary for storage
            email_dict = self.to_dict()
            
            # Store in PostgreSQL
            postgres_client.upsert(
                table="emails",
                data=email_dict,
                key_fields=["user_id", "email_id"]
            )
            
            # Store in vector database if embedding is available
            if vector_client and self.vector_embedding:
                vector_client.upsert(
                    collection=f"emails_{self.user_id}",
                    ids=[self.email_id],
                    embeddings=[self.vector_embedding],
                    metadatas=[{
                        "email_id": self.email_id,
                        "subject": self.metadata.subject,
                        "sender_email": self.metadata.sender_email,
                        "date": self.metadata.date.isoformat() if self.metadata.date else None,
                        "content_hash": self.content_hash
                    }],
                    documents=[self.body_text]
                )
                
            return True
            
        except Exception as e:
            from utils.logging import get_logger
            logger = get_logger(__name__)
            logger.error(f"Error saving email {self.email_id}: {str(e)}")
            return False
    
    def extract_action_items(self) -> List[Dict[str, Any]]:
        """Extract action items from email using NLP"""
        # This would be implemented with an AI model
        # For now, return placeholder
        return []
    
    def extract_topics(self) -> List[str]:
        """Extract main topics from email content"""
        # This would be implemented with an AI model
        # For now, return placeholder
        return []
    
    def analyze_sentiment(self) -> float:
        """Analyze sentiment of email content"""
        # This would be implemented with an AI model
        # For now, return neutral sentiment
        return 0.0
    
    def extract_contacts(self) -> Set[str]:
        """Extract contact emails mentioned in email content"""
        # Simple regex-based extraction 
        import re
        
        # Combine all text fields
        all_text = f"{self.metadata.subject} {self.body_text}"
        
        # Basic email regex pattern
        email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
        
        # Find all emails
        found_emails = set(re.findall(email_pattern, all_text))
        
        # Add known contacts from metadata
        found_emails.update([self.metadata.sender_email])
        found_emails.update(self.metadata.recipient_emails)
        found_emails.update(self.metadata.cc_emails)
        
        return found_emails
