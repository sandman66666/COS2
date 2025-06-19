"""
Knowledge Tree Model for Strategic Intelligence System
=====================================================
Represents hierarchical knowledge graphs for strategic intelligence.
"""

import uuid
import json
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Set, Union

from storage.postgres_client import PostgresClient
from storage.graph_client import GraphClient
from storage.vector_client import VectorClient


@dataclass
class KnowledgeSource:
    """Source information for a knowledge node"""
    source_type: str  # email, linkedin, analysis, etc.
    source_id: str
    timestamp: datetime
    confidence: float = 1.0


@dataclass
class KnowledgeRelation:
    """Relation between knowledge nodes"""
    target_node_id: str
    relation_type: str
    weight: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class KnowledgeNode:
    """
    Knowledge node in the strategic intelligence knowledge tree
    Represents a piece of information, insight, or prediction
    """
    
    def __init__(
        self,
        user_id: str,
        node_id: Optional[str] = None,
        node_type: str = "fact",  # fact, inference, prediction
        content: str = "",
        sources: List[KnowledgeSource] = None,
        parent_id: Optional[str] = None,
        relations: List[KnowledgeRelation] = None,
        tags: Set[str] = None,
        metadata: Dict[str, Any] = None,
        vector_embedding: Optional[List[float]] = None
    ):
        self.user_id = user_id
        self.node_id = node_id or str(uuid.uuid4())
        self.node_type = node_type
        self.content = content
        self.sources = sources or []
        self.parent_id = parent_id
        self.relations = relations or []
        self.tags = tags or set()
        self.metadata = metadata or {}
        self.vector_embedding = vector_embedding
        
        # System metadata
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.confidence_score = None
        self.relevance_score = None
        self.importance_score = None
        
        # Topic/Category classification
        self.category = None
        self.subcategory = None
        self.topics = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert knowledge node to dictionary for storage"""
        return {
            "user_id": self.user_id,
            "node_id": self.node_id,
            "node_type": self.node_type,
            "content": self.content,
            "parent_id": self.parent_id,
            "sources": [
                {
                    "source_type": source.source_type,
                    "source_id": source.source_id,
                    "timestamp": source.timestamp.isoformat(),
                    "confidence": source.confidence
                }
                for source in self.sources
            ],
            "relations": [
                {
                    "target_node_id": relation.target_node_id,
                    "relation_type": relation.relation_type,
                    "weight": relation.weight,
                    "metadata": relation.metadata
                }
                for relation in self.relations
            ],
            "tags": list(self.tags),
            "metadata": self.metadata,
            "vector_embedding": self.vector_embedding,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "confidence_score": self.confidence_score,
            "relevance_score": self.relevance_score,
            "importance_score": self.importance_score,
            "category": self.category,
            "subcategory": self.subcategory,
            "topics": self.topics
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KnowledgeNode':
        """Create a KnowledgeNode instance from dictionary data"""
        node = cls(
            user_id=data["user_id"],
            node_id=data["node_id"],
            node_type=data["node_type"],
            content=data["content"],
            parent_id=data.get("parent_id")
        )
        
        # Sources
        if "sources" in data:
            node.sources = [
                KnowledgeSource(
                    source_type=source["source_type"],
                    source_id=source["source_id"],
                    timestamp=datetime.fromisoformat(source["timestamp"]),
                    confidence=source.get("confidence", 1.0)
                )
                for source in data["sources"]
            ]
        
        # Relations
        if "relations" in data:
            node.relations = [
                KnowledgeRelation(
                    target_node_id=relation["target_node_id"],
                    relation_type=relation["relation_type"],
                    weight=relation.get("weight", 1.0),
                    metadata=relation.get("metadata", {})
                )
                for relation in data["relations"]
            ]
        
        # Other fields
        node.tags = set(data.get("tags", []))
        node.metadata = data.get("metadata", {})
        node.vector_embedding = data.get("vector_embedding")
        
        if data.get("created_at"):
            node.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("updated_at"):
            node.updated_at = datetime.fromisoformat(data["updated_at"])
            
        node.confidence_score = data.get("confidence_score")
        node.relevance_score = data.get("relevance_score")
        node.importance_score = data.get("importance_score")
        node.category = data.get("category")
        node.subcategory = data.get("subcategory")
        node.topics = data.get("topics", [])
        
        return node
    
    def save(
        self, 
        postgres_client: PostgresClient, 
        graph_client: Optional[GraphClient] = None,
        vector_client: Optional[VectorClient] = None
    ) -> bool:
        """
        Save knowledge node to databases
        
        Args:
            postgres_client: PostgreSQL client
            graph_client: Optional Neo4j graph client
            vector_client: Optional vector client
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Update timestamp
            self.updated_at = datetime.utcnow()
            
            # Convert to dictionary for storage
            node_dict = self.to_dict()
            
            # Store in PostgreSQL
            postgres_client.upsert(
                table="knowledge_nodes",
                data=node_dict,
                key_fields=["user_id", "node_id"]
            )
            
            # Store in graph database if available
            if graph_client:
                # Create or update knowledge node
                properties = {
                    "node_id": self.node_id,
                    "node_type": self.node_type,
                    "content": self.content,
                    "created_at": self.created_at.isoformat(),
                    "importance_score": self.importance_score,
                    "confidence_score": self.confidence_score
                }
                
                # Remove None values
                properties = {k: v for k, v in properties.items() if v is not None}
                
                # Create the node
                graph_client.create_or_update_node(
                    label="KnowledgeNode",
                    properties=properties,
                    primary_key="node_id"
                )
                
                # Add parent relationship if exists
                if self.parent_id:
                    graph_client.create_relationship(
                        start_label="KnowledgeNode",
                        start_properties={"node_id": self.node_id},
                        relationship_type="CHILD_OF",
                        end_label="KnowledgeNode",
                        end_properties={"node_id": self.parent_id}
                    )
                
                # Add all other relationships
                for relation in self.relations:
                    rel_properties = {
                        "weight": relation.weight
                    }
                    rel_properties.update(relation.metadata)
                    
                    graph_client.create_relationship(
                        start_label="KnowledgeNode",
                        start_properties={"node_id": self.node_id},
                        relationship_type=relation.relation_type,
                        end_label="KnowledgeNode",
                        end_properties={"node_id": relation.target_node_id},
                        properties=rel_properties
                    )
            
            # Store in vector database if available and embedding exists
            if vector_client and self.vector_embedding:
                metadata = {
                    "node_id": self.node_id,
                    "node_type": self.node_type,
                    "user_id": self.user_id,
                    "created_at": self.created_at.isoformat()
                }
                
                if self.category:
                    metadata["category"] = self.category
                    
                if self.topics:
                    metadata["topics"] = json.dumps(self.topics[:5])  # Limit topics for metadata
                
                vector_client.upsert(
                    collection=f"knowledge_nodes_{self.user_id}",
                    ids=[self.node_id],
                    embeddings=[self.vector_embedding],
                    metadatas=[metadata],
                    documents=[self.content]
                )
                
            return True
            
        except Exception as e:
            from utils.logging import get_logger
            logger = get_logger(__name__)
            logger.error(f"Error saving knowledge node {self.node_id}: {str(e)}")
            return False
    
    def add_relation(self, target_node_id: str, relation_type: str, weight: float = 1.0, metadata: Dict = None) -> None:
        """
        Add a relation to another knowledge node
        
        Args:
            target_node_id: ID of target node
            relation_type: Type of relation
            weight: Relation weight/strength
            metadata: Additional relation metadata
        """
        # Check if relation already exists
        for relation in self.relations:
            if relation.target_node_id == target_node_id and relation.relation_type == relation_type:
                # Update existing relation
                relation.weight = weight
                relation.metadata.update(metadata or {})
                return
        
        # Add new relation
        self.relations.append(KnowledgeRelation(
            target_node_id=target_node_id,
            relation_type=relation_type,
            weight=weight,
            metadata=metadata or {}
        ))
        
        self.updated_at = datetime.utcnow()
    
    def add_source(self, source_type: str, source_id: str, confidence: float = 1.0) -> None:
        """
        Add a source to this knowledge node
        
        Args:
            source_type: Type of source
            source_id: ID of source
            confidence: Confidence in this source
        """
        # Check if source already exists
        for source in self.sources:
            if source.source_type == source_type and source.source_id == source_id:
                # Update existing source
                source.confidence = confidence
                source.timestamp = datetime.utcnow()
                return
        
        # Add new source
        self.sources.append(KnowledgeSource(
            source_type=source_type,
            source_id=source_id,
            timestamp=datetime.utcnow(),
            confidence=confidence
        ))
        
        self.updated_at = datetime.utcnow()
    
    def calculate_scores(self) -> None:
        """Calculate confidence, relevance, and importance scores"""
        # This is a placeholder for more sophisticated scoring logic
        
        # Confidence based on sources
        source_confidences = [source.confidence for source in self.sources]
        if source_confidences:
            self.confidence_score = sum(source_confidences) / len(source_confidences)
        else:
            self.confidence_score = 0.5  # Default confidence
        
        # Importance based on relations
        if self.relations:
            self.importance_score = min(1.0, len(self.relations) / 10)  # More relations = more important
        else:
            self.importance_score = 0.3  # Default importance
        
        # Relevance would require more context
        self.relevance_score = 0.5  # Default relevance
