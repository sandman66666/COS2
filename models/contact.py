"""
Contact Model for Strategic Intelligence System
==============================================
Represents contact/person data with enrichment from multiple sources.
"""

import json
import uuid
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Set

from storage.postgres_client import PostgresClient
from storage.graph_client import GraphClient


@dataclass
class ContactSource:
    """Source information for contact data"""
    source_type: str  # email, linkedin, twitter, etc.
    source_id: str
    timestamp: datetime
    confidence: float = 1.0


@dataclass
class ContactProfile:
    """Profile information for a specific platform"""
    platform: str
    url: Optional[str] = None
    username: Optional[str] = None
    profile_id: Optional[str] = None
    bio: Optional[str] = None
    followers_count: Optional[int] = None
    verified: bool = False
    last_updated: Optional[datetime] = None


class Contact:
    """Contact model representing a person with multi-source data"""
    
    def __init__(
        self,
        user_id: str,
        contact_id: Optional[str] = None,
        email: Optional[str] = None,
        name: Optional[str] = None,
        sources: List[ContactSource] = None,
        profiles: Dict[str, ContactProfile] = None
    ):
        self.user_id = user_id
        self.contact_id = contact_id or str(uuid.uuid4())
        self.email = email
        self.name = name
        self.sources = sources or []
        self.profiles = profiles or {}
        
        # Contact details - enriched through various sources
        self.first_name = None
        self.last_name = None
        self.company = None
        self.title = None
        self.department = None
        self.phone = None
        self.location = None
        self.country = None
        self.industry = None
        self.tags = set()
        
        # Relationship metadata
        self.first_contact_date = None
        self.last_contact_date = None
        self.contact_frequency = None
        self.importance_score = None
        self.sentiment_score = None
        self.relationship_strength = None
        
        # System metadata
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.enrichment_status = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert contact to dictionary for storage"""
        return {
            "user_id": self.user_id,
            "contact_id": self.contact_id,
            "email": self.email,
            "name": self.name,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "company": self.company,
            "title": self.title,
            "department": self.department,
            "phone": self.phone,
            "location": self.location,
            "country": self.country,
            "industry": self.industry,
            "tags": list(self.tags),
            "sources": [
                {
                    "source_type": source.source_type,
                    "source_id": source.source_id,
                    "timestamp": source.timestamp.isoformat(),
                    "confidence": source.confidence
                }
                for source in self.sources
            ],
            "profiles": {
                platform: {
                    "platform": profile.platform,
                    "url": profile.url,
                    "username": profile.username,
                    "profile_id": profile.profile_id,
                    "bio": profile.bio,
                    "followers_count": profile.followers_count,
                    "verified": profile.verified,
                    "last_updated": profile.last_updated.isoformat() if profile.last_updated else None
                }
                for platform, profile in self.profiles.items()
            },
            "first_contact_date": self.first_contact_date.isoformat() if self.first_contact_date else None,
            "last_contact_date": self.last_contact_date.isoformat() if self.last_contact_date else None,
            "contact_frequency": self.contact_frequency,
            "importance_score": self.importance_score,
            "sentiment_score": self.sentiment_score,
            "relationship_strength": self.relationship_strength,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "enrichment_status": self.enrichment_status
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Contact':
        """Create a Contact instance from dictionary data"""
        contact = cls(
            user_id=data["user_id"],
            contact_id=data["contact_id"],
            email=data.get("email"),
            name=data.get("name")
        )
        
        # Basic information
        contact.first_name = data.get("first_name")
        contact.last_name = data.get("last_name")
        contact.company = data.get("company")
        contact.title = data.get("title")
        contact.department = data.get("department")
        contact.phone = data.get("phone")
        contact.location = data.get("location")
        contact.country = data.get("country")
        contact.industry = data.get("industry")
        contact.tags = set(data.get("tags", []))
        
        # Sources
        if "sources" in data:
            contact.sources = [
                ContactSource(
                    source_type=source["source_type"],
                    source_id=source["source_id"],
                    timestamp=datetime.fromisoformat(source["timestamp"]),
                    confidence=source.get("confidence", 1.0)
                )
                for source in data["sources"]
            ]
        
        # Profiles
        if "profiles" in data:
            for platform, profile_data in data["profiles"].items():
                contact.profiles[platform] = ContactProfile(
                    platform=profile_data["platform"],
                    url=profile_data.get("url"),
                    username=profile_data.get("username"),
                    profile_id=profile_data.get("profile_id"),
                    bio=profile_data.get("bio"),
                    followers_count=profile_data.get("followers_count"),
                    verified=profile_data.get("verified", False),
                    last_updated=datetime.fromisoformat(profile_data["last_updated"]) 
                    if profile_data.get("last_updated") else None
                )
        
        # Relationship metadata
        if data.get("first_contact_date"):
            contact.first_contact_date = datetime.fromisoformat(data["first_contact_date"])
        if data.get("last_contact_date"):
            contact.last_contact_date = datetime.fromisoformat(data["last_contact_date"])
            
        contact.contact_frequency = data.get("contact_frequency")
        contact.importance_score = data.get("importance_score")
        contact.sentiment_score = data.get("sentiment_score")
        contact.relationship_strength = data.get("relationship_strength")
        
        # System metadata
        if data.get("created_at"):
            contact.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("updated_at"):
            contact.updated_at = datetime.fromisoformat(data["updated_at"])
        contact.enrichment_status = data.get("enrichment_status", {})
        
        return contact
    
    def save(self, postgres_client: PostgresClient, graph_client: GraphClient = None) -> bool:
        """
        Save contact to database and relationship graph
        
        Args:
            postgres_client: PostgreSQL client
            graph_client: Optional Neo4j graph client
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Update timestamp
            self.updated_at = datetime.utcnow()
            
            # Convert to dictionary for storage
            contact_dict = self.to_dict()
            
            # Store in PostgreSQL
            postgres_client.upsert(
                table="contacts",
                data=contact_dict,
                key_fields=["user_id", "contact_id"]
            )
            
            # Store in graph database if available
            if graph_client:
                # Create or update person node
                properties = {
                    "contact_id": self.contact_id,
                    "name": self.name,
                    "email": self.email,
                    "company": self.company,
                    "title": self.title,
                    "importance_score": self.importance_score
                }
                
                # Remove None values
                properties = {k: v for k, v in properties.items() if v is not None}
                
                graph_client.create_or_update_node(
                    label="Person",
                    properties=properties,
                    primary_key="contact_id"
                )
                
                # If we have company info, create company node and relationship
                if self.company:
                    company_props = {"name": self.company}
                    graph_client.create_or_update_node(
                        label="Organization",
                        properties=company_props,
                        primary_key="name"
                    )
                    
                    # Create relationship
                    graph_client.create_relationship(
                        start_label="Person",
                        start_properties={"contact_id": self.contact_id},
                        relationship_type="WORKS_AT",
                        end_label="Organization",
                        end_properties={"name": self.company},
                        properties={"title": self.title}
                    )
                
            return True
            
        except Exception as e:
            from utils.logging import get_logger
            logger = get_logger(__name__)
            logger.error(f"Error saving contact {self.contact_id}: {str(e)}")
            return False
    
    def update_from_enrichment(self, source_type: str, enrichment_data: Dict[str, Any], confidence: float = 0.8) -> None:
        """
        Update contact with data from enrichment sources
        
        Args:
            source_type: Type of source (linkedin, twitter, etc)
            enrichment_data: Dictionary of enriched data
            confidence: Confidence score for this source
        """
        source_id = enrichment_data.get("source_id", f"{source_type}:{datetime.utcnow().isoformat()}")
        
        # Add source if not already present
        source_exists = any(s.source_id == source_id for s in self.sources)
        if not source_exists:
            self.sources.append(ContactSource(
                source_type=source_type,
                source_id=source_id,
                timestamp=datetime.utcnow(),
                confidence=confidence
            ))
        
        # Update basic information if confidence is high enough
        if confidence >= 0.8:
            if "name" in enrichment_data and enrichment_data["name"]:
                self.name = enrichment_data["name"]
            
            if "first_name" in enrichment_data and enrichment_data["first_name"]:
                self.first_name = enrichment_data["first_name"]
                
            if "last_name" in enrichment_data and enrichment_data["last_name"]:
                self.last_name = enrichment_data["last_name"]
                
            if "company" in enrichment_data and enrichment_data["company"]:
                self.company = enrichment_data["company"]
                
            if "title" in enrichment_data and enrichment_data["title"]:
                self.title = enrichment_data["title"]
                
            if "department" in enrichment_data and enrichment_data["department"]:
                self.department = enrichment_data["department"]
                
            if "location" in enrichment_data and enrichment_data["location"]:
                self.location = enrichment_data["location"]
                
            if "country" in enrichment_data and enrichment_data["country"]:
                self.country = enrichment_data["country"]
                
            if "industry" in enrichment_data and enrichment_data["industry"]:
                self.industry = enrichment_data["industry"]
        
        # Add profile if available
        if "profile" in enrichment_data and enrichment_data["profile"]:
            profile_data = enrichment_data["profile"]
            platform = profile_data.get("platform", source_type)
            
            self.profiles[platform] = ContactProfile(
                platform=platform,
                url=profile_data.get("url"),
                username=profile_data.get("username"),
                profile_id=profile_data.get("profile_id"),
                bio=profile_data.get("bio"),
                followers_count=profile_data.get("followers_count"),
                verified=profile_data.get("verified", False),
                last_updated=datetime.utcnow()
            )
        
        # Update tags
        if "tags" in enrichment_data and enrichment_data["tags"]:
            self.tags.update(enrichment_data["tags"])
        
        # Update enrichment status
        self.enrichment_status[source_type] = {
            "timestamp": datetime.utcnow().isoformat(),
            "success": True,
            "confidence": confidence
        }
        
        self.updated_at = datetime.utcnow()
