"""
Intelligence Routes
=================
Routes for accessing insights, predictions, and calendar intelligence
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, List, Optional
import logging
from datetime import datetime, timedelta
from models.user import User
from middleware.auth_middleware import get_current_user
from intelligence.calendar.calendar_intelligence import CalendarIntelligenceEngine
from intelligence.predictions.prediction_engine import PredictiveIntelligenceEngine
from intelligence.knowledge_tree.augmentation_engine import KnowledgeTreeAugmentationEngine
from intelligence.claude_analysis import KnowledgeTreeBuilder
from intelligence.deep_augmentation import DeepAugmentationEngine
from storage.storage_manager import StorageManager

router = APIRouter(prefix="/api/intelligence", tags=["intelligence"])
logger = logging.getLogger(__name__)

# Initialize dependencies (these would typically be injected)
storage = StorageManager()
augmentation_engine = KnowledgeTreeAugmentationEngine(storage)
knowledge_tree_builder = KnowledgeTreeBuilder.get_instance()
deep_augmentation_engine = DeepAugmentationEngine.get_instance()

@router.get("/calendar/meetings")
async def get_upcoming_meetings(
    days: int = Query(7, description="Days ahead to analyze"),
    user: User = Depends(get_current_user)
):
    """
    Get upcoming meetings with contextual intelligence and insights.
    """
    try:
        # The actual instance would be injected through dependency injection
        # Here we create it temporarily with required dependencies
        from services.claude_client import claude_client
        calendar_engine = CalendarIntelligenceEngine(storage, claude_client)
        
        meetings = await calendar_engine.analyze_upcoming_meetings(
            user_id=user.id,
            days_ahead=days
        )
        
        return {
            "success": True,
            "count": len(meetings),
            "meetings": [meeting.__dict__ for meeting in meetings]
        }
    except Exception as e:
        logger.exception(f"Error analyzing upcoming meetings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/calendar/brief/{event_id}")
async def get_meeting_brief(
    event_id: str,
    user: User = Depends(get_current_user)
):
    """
    Get formatted meeting brief for a specific calendar event.
    """
    try:
        from services.claude_client import claude_client
        calendar_engine = CalendarIntelligenceEngine(storage, claude_client)
        
        # First retrieve the meeting context
        meeting = await calendar_engine.get_meeting_context(
            user_id=user.id,
            event_id=event_id
        )
        
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        
        # Generate the brief
        brief = calendar_engine.format_meeting_brief(meeting)
        
        return {
            "success": True,
            "event_id": event_id,
            "brief": brief
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error generating meeting brief: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/predictions")
async def get_predictions(
    limit: int = Query(10, description="Maximum number of predictions"),
    user: User = Depends(get_current_user)
):
    """
    Get AI-generated predictions based on user's data.
    """
    try:
        # Retrieve the knowledge tree for the user
        knowledge_tree = await storage.get_knowledge_tree(user_id=user.id)
        
        if not knowledge_tree:
            return {
                "success": True,
                "message": "No knowledge tree found. Need more data to generate predictions.",
                "predictions": []
            }
        
        # Generate predictions using the engine
        from services.claude_client import claude_client
        prediction_engine = PredictiveIntelligenceEngine(storage, claude_client)
        
        predictions = await prediction_engine.generate_predictions(
            user_id=user.id,
            knowledge_tree=knowledge_tree
        )
        
        return {
            "success": True,
            "count": len(predictions),
            "predictions": [prediction.__dict__ for prediction in predictions]
        }
    except Exception as e:
        logger.exception(f"Error generating predictions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/insights")
async def get_actionable_insights(
    limit: int = Query(5, description="Maximum number of insights"),
    user: User = Depends(get_current_user)
):
    """
    Get actionable insights derived from predictions.
    """
    try:
        # First get the predictions
        knowledge_tree = await storage.get_knowledge_tree(user_id=user.id)
        
        if not knowledge_tree:
            return {
                "success": True,
                "message": "No knowledge tree found. Need more data to generate insights.",
                "insights": []
            }
        
        # Generate predictions and then insights
        from services.claude_client import claude_client
        prediction_engine = PredictiveIntelligenceEngine(storage, claude_client)
        
        predictions = await prediction_engine.generate_predictions(
            user_id=user.id,
            knowledge_tree=knowledge_tree
        )
        
        # Get user context for better insight personalization
        user_context = await storage.get_user_context(user_id=user.id)
        
        # Convert predictions to actionable insights
        insights = await prediction_engine.generate_actionable_insights(
            predictions=predictions,
            user_context=user_context
        )
        
        # Limit the number of insights
        insights = insights[:limit]
        
        return {
            "success": True,
            "count": len(insights),
            "insights": [insight.__dict__ for insight in insights]
        }
    except Exception as e:
        logger.exception(f"Error generating actionable insights: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/knowledge-tree")
async def get_knowledge_tree(
    user: User = Depends(get_current_user)
):
    """
    Get the user's knowledge tree (personal knowledge graph).
    """
    try:
        knowledge_tree = await storage.get_knowledge_tree(user_id=user.id)
        
        if not knowledge_tree:
            return {
                "success": True,
                "message": "Knowledge tree not found or not yet built",
                "knowledge_tree": {}
            }
        
        return {
            "success": True,
            "knowledge_tree": knowledge_tree
        }
    except Exception as e:
        logger.exception(f"Error retrieving knowledge tree: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/relationships")
async def get_relationship_graph(
    limit: int = Query(50, description="Maximum number of relationships"),
    user: User = Depends(get_current_user)
):
    """
    Get relationship graph with interaction data.
    """
    try:
        relationships = await augmentation_engine.get_relationship_graph(
            user_id=user.id,
            limit=limit
        )
        
        return {
            "success": True,
            "count": len(relationships),
            "relationships": relationships
        }
    except Exception as e:
        logger.exception(f"Error retrieving relationship graph: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/build-knowledge-tree")
async def build_knowledge_tree(
    time_window_days: int = Query(30, description="Days to include in analysis"),
    user: User = Depends(get_current_user)
):
    """
    Build knowledge tree using Claude analysts on user's email data.
    """
    try:
        # Start the knowledge tree building process
        knowledge_tree = await knowledge_tree_builder.build_knowledge_tree(
            user_id=user.id,
            time_window_days=time_window_days
        )
        
        if not knowledge_tree:
            raise HTTPException(status_code=500, detail="Failed to build knowledge tree")
        
        return {
            "success": True,
            "message": "Knowledge tree successfully built",
            "knowledge_tree_summary": {
                "time_window": knowledge_tree.get("time_window", {}),
                "insight_count": sum(len(insights) for insights in knowledge_tree.get("insights", {}).values()),
                "relationship_count": len(knowledge_tree.get("relationships", [])),
                "topic_count": len(knowledge_tree.get("topics", [])),
                "entity_count": len(knowledge_tree.get("entities", []))
            }
        }
    except Exception as e:
        logger.exception(f"Error building knowledge tree: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/augment-knowledge-tree")
async def augment_knowledge_tree(
    user: User = Depends(get_current_user)
):
    """
    Perform deep augmentation on an existing knowledge tree.
    """
    try:
        # First, retrieve the existing knowledge tree
        knowledge_tree = await storage.get_knowledge_tree(user_id=user.id)
        
        if not knowledge_tree:
            raise HTTPException(
                status_code=404, 
                detail="Knowledge tree not found. Please build a knowledge tree first."
            )
        
        # Get emails for augmentation
        emails = await storage.get_user_emails(
            user_id=user.id, 
            limit=1000,  # Reasonable limit for processing
            days_back=knowledge_tree.get("time_window", {}).get("days", 30)
        )
        
        # Perform deep augmentation
        augmented_tree = await deep_augmentation_engine.augment_knowledge_tree(
            knowledge_tree=knowledge_tree,
            emails=emails
        )
        
        # Save the augmented tree
        await storage.save_augmented_knowledge_tree(user_id=user.id, augmented_tree=augmented_tree)
        
        return {
            "success": True,
            "message": "Knowledge tree successfully augmented",
            "augmentation_summary": {
                "original_tree_size": len(json.dumps(knowledge_tree)),
                "augmented_tree_size": len(json.dumps(augmented_tree)),
                "augmentation_metadata": augmented_tree.get("augmentation_metadata", {}),
                "hidden_connections_count": len(augmented_tree.get("hidden_connections", []))
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error augmenting knowledge tree: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/augmented-knowledge-tree")
async def get_augmented_knowledge_tree(
    user: User = Depends(get_current_user)
):
    """
    Get the deeply augmented knowledge tree with additional context and connections.
    """
    try:
        augmented_tree = await storage.get_augmented_knowledge_tree(user_id=user.id)
        
        if not augmented_tree:
            return {
                "success": True,
                "message": "Augmented knowledge tree not found. Please run augmentation first.",
                "augmented_tree": {}
            }
        
        return {
            "success": True,
            "augmented_tree": augmented_tree
        }
    except Exception as e:
        logger.exception(f"Error retrieving augmented knowledge tree: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/hidden-connections")
async def get_hidden_connections(
    limit: int = Query(20, description="Maximum number of hidden connections"),
    user: User = Depends(get_current_user)
):
    """
    Get hidden connections discovered by deep augmentation.
    """
    try:
        augmented_tree = await storage.get_augmented_knowledge_tree(user_id=user.id)
        
        if not augmented_tree or "hidden_connections" not in augmented_tree:
            return {
                "success": True,
                "message": "No hidden connections found. Please run augmentation first.",
                "connections": []
            }
        
        # Get the top connections by strength
        connections = sorted(
            augmented_tree["hidden_connections"], 
            key=lambda c: c.get("strength", 0), 
            reverse=True
        )[:limit]
        
        return {
            "success": True,
            "count": len(connections),
            "connections": connections
        }
    except Exception as e:
        logger.exception(f"Error retrieving hidden connections: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/relationships/{person_id}")
async def get_relationship_details(
    person_id: str,
    user: User = Depends(get_current_user)
):
    """
    Get detailed information about a specific relationship.
    """
    try:
        relationship = await augmentation_engine.get_relationship_details(
            user_id=user.id,
            person_id=person_id
        )
        
        if not relationship:
            raise HTTPException(status_code=404, detail="Relationship not found")
        
        return {
            "success": True,
            "relationship": relationship
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error retrieving relationship details: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
