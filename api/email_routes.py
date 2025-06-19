"""
Email Processing Routes
=====================
Routes for email processing, synchronization, and search functionality.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from typing import Dict, List, Optional
import logging
from models.user import User
from middleware.auth_middleware import get_current_user
from gmail.email_processor import EmailProcessor

router = APIRouter(prefix="/api/emails", tags=["emails"])
logger = logging.getLogger(__name__)

@router.post("/sync")
async def sync_emails(
    background_tasks: BackgroundTasks,
    days: int = Query(30, description="Number of days to sync"),
    user: User = Depends(get_current_user)
):
    """
    Synchronize emails from Gmail for the authenticated user.
    This is a background task that will run asynchronously.
    """
    try:
        # Start email sync in background
        background_tasks.add_task(
            EmailProcessor().sync_emails,
            user_id=user.id,
            days=days
        )
        
        return {
            "success": True,
            "message": f"Email synchronization started for the last {days} days",
            "status": "processing"
        }
    except Exception as e:
        logger.exception(f"Error starting email sync: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/extract-sent")
async def extract_sent_contacts(
    background_tasks: BackgroundTasks,
    days: int = Query(365, description="Number of days to analyze"),
    user: User = Depends(get_current_user)
):
    """
    Extract contacts from sent emails to build trusted network.
    This is a critical component for the intelligence system.
    """
    try:
        # Start contact extraction in background
        background_tasks.add_task(
            EmailProcessor().extract_sent_contacts,
            user_id=user.id,
            days=days
        )
        
        return {
            "success": True,
            "message": f"Contact extraction started from sent emails over the last {days} days",
            "status": "processing"
        }
    except Exception as e:
        logger.exception(f"Error starting contact extraction: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search")
async def search_emails(
    query: str,
    limit: int = Query(10, description="Maximum number of results"),
    offset: int = Query(0, description="Result offset for pagination"),
    user: User = Depends(get_current_user)
):
    """
    Semantic search through emails using vector embeddings.
    """
    try:
        # Perform semantic search
        results = await EmailProcessor().semantic_search(
            user_id=user.id,
            query=query,
            limit=limit,
            offset=offset
        )
        
        return {
            "success": True,
            "count": len(results),
            "results": results
        }
    except Exception as e:
        logger.exception(f"Error during email search: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_email_stats(
    user: User = Depends(get_current_user)
):
    """
    Get email statistics for the authenticated user.
    """
    try:
        stats = await EmailProcessor().get_email_stats(user_id=user.id)
        
        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        logger.exception(f"Error fetching email stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/threads/{thread_id}")
async def get_email_thread(
    thread_id: str,
    user: User = Depends(get_current_user)
):
    """
    Get complete email thread by ID.
    """
    try:
        thread = await EmailProcessor().get_thread(
            user_id=user.id,
            thread_id=thread_id
        )
        
        if not thread:
            raise HTTPException(status_code=404, detail="Thread not found")
        
        return {
            "success": True,
            "thread": thread
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error fetching email thread: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/contacts")
async def get_trusted_contacts(
    limit: int = Query(50, description="Maximum number of contacts"),
    offset: int = Query(0, description="Contact offset for pagination"),
    user: User = Depends(get_current_user)
):
    """
    Get user's trusted contacts extracted from sent emails.
    """
    try:
        contacts = await EmailProcessor().get_trusted_contacts(
            user_id=user.id,
            limit=limit,
            offset=offset
        )
        
        return {
            "success": True,
            "count": len(contacts),
            "contacts": contacts
        }
    except Exception as e:
        logger.exception(f"Error fetching trusted contacts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
