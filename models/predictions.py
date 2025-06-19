"""
Predictions Model for Strategic Intelligence System
=================================================
Represents predictive intelligence insights and trajectories.
"""

import uuid
import json
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Set, Union

from storage.postgres_client import PostgresClient
from storage.graph_client import GraphClient
from storage.vector_client import VectorClient


@dataclass
class PredictionSource:
    """Source information for a prediction"""
    source_type: str  # analysis, knowledgeNode, model, etc.
    source_id: str
    timestamp: datetime
    weight: float = 1.0


@dataclass
class PredictionOutcome:
    """Possible outcome for a prediction"""
    outcome_id: str
    description: str
    probability: float
    impact: float  # 0-1 scale
    happened: Optional[bool] = None
    resolution_date: Optional[datetime] = None


class Prediction:
    """
    Prediction model representing a strategic intelligence forecast
    """
    
    def __init__(
        self,
        user_id: str,
        prediction_id: Optional[str] = None,
        entity_id: Optional[str] = None,  # Contact ID or org ID the prediction is about
        entity_type: str = "contact",  # contact, organization, market, etc.
        prediction_type: str = "relationship",  # relationship, market, technical, business
        description: str = "",
        context: str = "",
        sources: List[PredictionSource] = None,
        outcomes: List[PredictionOutcome] = None,
        due_date: Optional[datetime] = None,
        tags: Set[str] = None,
        metadata: Dict[str, Any] = None
    ):
        self.user_id = user_id
        self.prediction_id = prediction_id or str(uuid.uuid4())
        self.entity_id = entity_id
        self.entity_type = entity_type
        self.prediction_type = prediction_type
        self.description = description
        self.context = context
        self.sources = sources or []
        self.outcomes = outcomes or []
        self.due_date = due_date
        self.tags = tags or set()
        self.metadata = metadata or {}
        
        # System metadata
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.confidence_score = None
        self.resolved = False
        self.resolution_date = None
        self.resolution_notes = None
        self.accuracy_score = None  # Set after resolution
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert prediction to dictionary for storage"""
        return {
            "user_id": self.user_id,
            "prediction_id": self.prediction_id,
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "prediction_type": self.prediction_type,
            "description": self.description,
            "context": self.context,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "sources": [
                {
                    "source_type": source.source_type,
                    "source_id": source.source_id,
                    "timestamp": source.timestamp.isoformat(),
                    "weight": source.weight
                }
                for source in self.sources
            ],
            "outcomes": [
                {
                    "outcome_id": outcome.outcome_id,
                    "description": outcome.description,
                    "probability": outcome.probability,
                    "impact": outcome.impact,
                    "happened": outcome.happened,
                    "resolution_date": outcome.resolution_date.isoformat() if outcome.resolution_date else None
                }
                for outcome in self.outcomes
            ],
            "tags": list(self.tags),
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "confidence_score": self.confidence_score,
            "resolved": self.resolved,
            "resolution_date": self.resolution_date.isoformat() if self.resolution_date else None,
            "resolution_notes": self.resolution_notes,
            "accuracy_score": self.accuracy_score
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Prediction':
        """Create a Prediction instance from dictionary data"""
        prediction = cls(
            user_id=data["user_id"],
            prediction_id=data["prediction_id"],
            entity_id=data.get("entity_id"),
            entity_type=data.get("entity_type", "contact"),
            prediction_type=data.get("prediction_type", "relationship"),
            description=data["description"],
            context=data.get("context", "")
        )
        
        # Due date
        if data.get("due_date"):
            prediction.due_date = datetime.fromisoformat(data["due_date"])
        
        # Sources
        if "sources" in data:
            prediction.sources = [
                PredictionSource(
                    source_type=source["source_type"],
                    source_id=source["source_id"],
                    timestamp=datetime.fromisoformat(source["timestamp"]),
                    weight=source.get("weight", 1.0)
                )
                for source in data["sources"]
            ]
        
        # Outcomes
        if "outcomes" in data:
            prediction.outcomes = [
                PredictionOutcome(
                    outcome_id=outcome["outcome_id"],
                    description=outcome["description"],
                    probability=outcome["probability"],
                    impact=outcome["impact"],
                    happened=outcome.get("happened"),
                    resolution_date=datetime.fromisoformat(outcome["resolution_date"]) if outcome.get("resolution_date") else None
                )
                for outcome in data["outcomes"]
            ]
        
        # Other fields
        prediction.tags = set(data.get("tags", []))
        prediction.metadata = data.get("metadata", {})
        
        if data.get("created_at"):
            prediction.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("updated_at"):
            prediction.updated_at = datetime.fromisoformat(data["updated_at"])
            
        prediction.confidence_score = data.get("confidence_score")
        prediction.resolved = data.get("resolved", False)
        
        if data.get("resolution_date"):
            prediction.resolution_date = datetime.fromisoformat(data["resolution_date"])
            
        prediction.resolution_notes = data.get("resolution_notes")
        prediction.accuracy_score = data.get("accuracy_score")
        
        return prediction
    
    def save(
        self, 
        postgres_client: PostgresClient, 
        graph_client: Optional[GraphClient] = None
    ) -> bool:
        """
        Save prediction to databases
        
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
            prediction_dict = self.to_dict()
            
            # Store in PostgreSQL
            postgres_client.upsert(
                table="predictions",
                data=prediction_dict,
                key_fields=["user_id", "prediction_id"]
            )
            
            # Store in graph database if available
            if graph_client:
                # Create or update prediction node
                properties = {
                    "prediction_id": self.prediction_id,
                    "description": self.description,
                    "prediction_type": self.prediction_type,
                    "created_at": self.created_at.isoformat(),
                    "due_date": self.due_date.isoformat() if self.due_date else None,
                    "confidence_score": self.confidence_score,
                    "resolved": self.resolved
                }
                
                # Remove None values
                properties = {k: v for k, v in properties.items() if v is not None}
                
                # Create the node
                graph_client.create_or_update_node(
                    label="Prediction",
                    properties=properties,
                    primary_key="prediction_id"
                )
                
                # Add relationships to entities
                if self.entity_id:
                    # Map entity types to Neo4j node labels
                    entity_labels = {
                        "contact": "Person",
                        "organization": "Organization",
                        "market": "Market",
                        "technology": "Technology"
                    }
                    
                    entity_label = entity_labels.get(self.entity_type, "Entity")
                    entity_key = "contact_id" if self.entity_type == "contact" else "id"
                    
                    graph_client.create_relationship(
                        start_label="Prediction",
                        start_properties={"prediction_id": self.prediction_id},
                        relationship_type="PREDICTS_ABOUT",
                        end_label=entity_label,
                        end_properties={entity_key: self.entity_id}
                    )
                
                # Add relationships to sources
                for source in self.sources:
                    if source.source_type == "knowledgeNode":
                        graph_client.create_relationship(
                            start_label="Prediction",
                            start_properties={"prediction_id": self.prediction_id},
                            relationship_type="DERIVED_FROM",
                            end_label="KnowledgeNode",
                            end_properties={"node_id": source.source_id},
                            properties={"weight": source.weight}
                        )
                
            return True
            
        except Exception as e:
            from utils.logging import get_logger
            logger = get_logger(__name__)
            logger.error(f"Error saving prediction {self.prediction_id}: {str(e)}")
            return False
    
    def add_outcome(self, description: str, probability: float, impact: float) -> str:
        """
        Add a possible outcome to this prediction
        
        Args:
            description: Description of the outcome
            probability: Probability of outcome (0-1)
            impact: Impact of outcome (0-1)
            
        Returns:
            ID of the new outcome
        """
        outcome_id = str(uuid.uuid4())
        
        self.outcomes.append(PredictionOutcome(
            outcome_id=outcome_id,
            description=description,
            probability=probability,
            impact=impact
        ))
        
        self.updated_at = datetime.utcnow()
        return outcome_id
    
    def resolve(self, outcome_id: str, notes: str = None) -> None:
        """
        Resolve a prediction by marking which outcome happened
        
        Args:
            outcome_id: ID of the outcome that happened
            notes: Optional resolution notes
        """
        self.resolved = True
        self.resolution_date = datetime.utcnow()
        self.resolution_notes = notes
        
        # Mark the correct outcome
        correct_probability = 0
        for outcome in self.outcomes:
            if outcome.outcome_id == outcome_id:
                outcome.happened = True
                outcome.resolution_date = datetime.utcnow()
                correct_probability = outcome.probability
            else:
                outcome.happened = False
        
        # Calculate accuracy score
        self.accuracy_score = correct_probability
        
        self.updated_at = datetime.utcnow()
    
    def calculate_confidence(self) -> float:
        """
        Calculate overall confidence score for this prediction
        
        Returns:
            Confidence score (0-1)
        """
        if not self.sources:
            self.confidence_score = 0.5  # Default confidence
        else:
            # Calculate weighted average of source weights
            total_weight = 0
            weighted_sum = 0
            
            for source in self.sources:
                total_weight += source.weight
                weighted_sum += source.weight
                
            self.confidence_score = weighted_sum / total_weight if total_weight > 0 else 0.5
            
        return self.confidence_score
    
    def get_most_likely_outcome(self) -> Optional[PredictionOutcome]:
        """
        Get the most likely outcome for this prediction
        
        Returns:
            Most likely outcome or None
        """
        if not self.outcomes:
            return None
            
        return max(self.outcomes, key=lambda outcome: outcome.probability)
    
    def get_highest_impact_outcome(self) -> Optional[PredictionOutcome]:
        """
        Get the highest impact outcome for this prediction
        
        Returns:
            Highest impact outcome or None
        """
        if not self.outcomes:
            return None
            
        return max(self.outcomes, key=lambda outcome: outcome.impact)
    
    def is_due_soon(self, days: int = 7) -> bool:
        """
        Check if this prediction is due soon
        
        Args:
            days: Number of days to consider "soon"
            
        Returns:
            True if due within specified days
        """
        if not self.due_date:
            return False
            
        return datetime.utcnow() + timedelta(days=days) >= self.due_date
