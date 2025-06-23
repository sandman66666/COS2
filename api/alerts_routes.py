"""
Tactical Alerts API Routes
=========================
API endpoints for real-time tactical alerts and urgent action items.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from pydantic import BaseModel

from auth.auth_manager import get_current_user
from models.user import User
from utils.logging import structured_logger as logger
from intelligence.g_realtime_updates.tactical_alerts_system import (
    get_tactical_alerts_system, TacticalAlert, AlertType, UrgencyLevel
)

router = APIRouter(prefix="/api/alerts", tags=["tactical_alerts"])

class EmailProcessRequest(BaseModel):
    """Request to process email for alerts"""
    email_data: dict

class AlertActionRequest(BaseModel):
    """Request to act on an alert"""
    alert_id: str
    action: str  # acknowledge, dismiss

@router.get("/active")
async def get_active_alerts(
    urgency: Optional[str] = Query(None, description="Filter by urgency level"),
    user: User = Depends(get_current_user)
):
    """
    Get active tactical alerts for the user
    
    Args:
        urgency: Optional urgency filter (critical, high, medium, low)
        user: Current authenticated user
        
    Returns:
        List of active alerts
    """
    try:
        alerts_system = await get_tactical_alerts_system(user.id)
        
        # Parse urgency filter
        urgency_filter = None
        if urgency:
            try:
                urgency_filter = UrgencyLevel(urgency.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid urgency level: {urgency}")
        
        alerts = await alerts_system.get_active_alerts(urgency_filter)
        
        # Convert to serializable format
        alert_data = []
        for alert in alerts:
            alert_data.append({
                "alert_id": alert.alert_id,
                "alert_type": alert.alert_type.value,
                "urgency": alert.urgency.value,
                "title": alert.title,
                "description": alert.description,
                "source_email_id": alert.source_email_id,
                "contact_email": alert.contact_email,
                "deadline": alert.deadline.isoformat() if alert.deadline else None,
                "recommended_actions": alert.recommended_actions,
                "context": alert.context,
                "created_at": alert.created_at.isoformat(),
                "acknowledged": alert.acknowledged,
                "dismissed": alert.dismissed
            })
        
        return {
            "success": True,
            "alerts": alert_data,
            "count": len(alert_data)
        }
        
    except Exception as e:
        logger.error(f"Error getting active alerts: {str(e)}", user_id=user.id)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/summary")
async def get_alerts_summary(user: User = Depends(get_current_user)):
    """
    Get summary of current alerts
    
    Args:
        user: Current authenticated user
        
    Returns:
        Alert summary statistics
    """
    try:
        alerts_system = await get_tactical_alerts_system(user.id)
        summary = await alerts_system.get_alert_summary()
        
        # Convert most urgent alert to serializable format
        if summary.get('most_urgent'):
            most_urgent = summary['most_urgent']
            summary['most_urgent'] = {
                "alert_id": most_urgent.alert_id,
                "title": most_urgent.title,
                "urgency": most_urgent.urgency.value,
                "alert_type": most_urgent.alert_type.value,
                "created_at": most_urgent.created_at.isoformat()
            }
        
        return {
            "success": True,
            "summary": summary
        }
        
    except Exception as e:
        logger.error(f"Error getting alerts summary: {str(e)}", user_id=user.id)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/process-email")
async def process_email_for_alerts(
    request: EmailProcessRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user)
):
    """
    Process an email for urgent alerts
    
    Args:
        request: Email processing request
        background_tasks: Background task manager
        user: Current authenticated user
        
    Returns:
        Processing result
    """
    try:
        alerts_system = await get_tactical_alerts_system(user.id)
        
        # Process email for alerts in background
        background_tasks.add_task(
            alerts_system.process_new_email,
            request.email_data
        )
        
        return {
            "success": True,
            "message": "Email processing started for tactical alerts",
            "email_id": request.email_data.get('email_id')
        }
        
    except Exception as e:
        logger.error(f"Error processing email for alerts: {str(e)}", user_id=user.id)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/acknowledge")
async def acknowledge_alert(
    request: AlertActionRequest,
    user: User = Depends(get_current_user)
):
    """
    Acknowledge an alert
    
    Args:
        request: Alert action request
        user: Current authenticated user
        
    Returns:
        Action result
    """
    try:
        alerts_system = await get_tactical_alerts_system(user.id)
        success = await alerts_system.acknowledge_alert(request.alert_id)
        
        if success:
            return {
                "success": True,
                "message": f"Alert {request.alert_id} acknowledged"
            }
        else:
            raise HTTPException(status_code=404, detail="Alert not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error acknowledging alert: {str(e)}", user_id=user.id)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/dismiss")
async def dismiss_alert(
    request: AlertActionRequest,
    user: User = Depends(get_current_user)
):
    """
    Dismiss an alert
    
    Args:
        request: Alert action request
        user: Current authenticated user
        
    Returns:
        Action result
    """
    try:
        alerts_system = await get_tactical_alerts_system(user.id)
        success = await alerts_system.dismiss_alert(request.alert_id)
        
        if success:
            return {
                "success": True,
                "message": f"Alert {request.alert_id} dismissed"
            }
        else:
            raise HTTPException(status_code=404, detail="Alert not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error dismissing alert: {str(e)}", user_id=user.id)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/critical")
async def get_critical_alerts(user: User = Depends(get_current_user)):
    """
    Get only critical urgency alerts
    
    Args:
        user: Current authenticated user
        
    Returns:
        Critical alerts
    """
    try:
        alerts_system = await get_tactical_alerts_system(user.id)
        alerts = await alerts_system.get_active_alerts(UrgencyLevel.CRITICAL)
        
        # Convert to serializable format
        alert_data = []
        for alert in alerts:
            alert_data.append({
                "alert_id": alert.alert_id,
                "title": alert.title,
                "description": alert.description,
                "contact_email": alert.contact_email,
                "deadline": alert.deadline.isoformat() if alert.deadline else None,
                "recommended_actions": alert.recommended_actions,
                "created_at": alert.created_at.isoformat()
            })
        
        return {
            "success": True,
            "critical_alerts": alert_data,
            "count": len(alert_data)
        }
        
    except Exception as e:
        logger.error(f"Error getting critical alerts: {str(e)}", user_id=user.id)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/by-contact/{contact_email}")
async def get_alerts_by_contact(
    contact_email: str,
    user: User = Depends(get_current_user)
):
    """
    Get alerts related to a specific contact
    
    Args:
        contact_email: Email address of the contact
        user: Current authenticated user
        
    Returns:
        Alerts for the contact
    """
    try:
        alerts_system = await get_tactical_alerts_system(user.id)
        all_alerts = await alerts_system.get_active_alerts()
        
        # Filter by contact
        contact_alerts = [
            alert for alert in all_alerts 
            if alert.contact_email and alert.contact_email.lower() == contact_email.lower()
        ]
        
        # Convert to serializable format
        alert_data = []
        for alert in contact_alerts:
            alert_data.append({
                "alert_id": alert.alert_id,
                "alert_type": alert.alert_type.value,
                "urgency": alert.urgency.value,
                "title": alert.title,
                "description": alert.description,
                "deadline": alert.deadline.isoformat() if alert.deadline else None,
                "recommended_actions": alert.recommended_actions,
                "created_at": alert.created_at.isoformat()
            })
        
        return {
            "success": True,
            "contact_email": contact_email,
            "alerts": alert_data,
            "count": len(alert_data)
        }
        
    except Exception as e:
        logger.error(f"Error getting alerts by contact: {str(e)}", user_id=user.id)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/types")
async def get_alert_types():
    """
    Get available alert types and urgency levels
    
    Returns:
        Available types and levels
    """
    return {
        "success": True,
        "alert_types": [t.value for t in AlertType],
        "urgency_levels": [u.value for u in UrgencyLevel],
        "descriptions": {
            "alert_types": {
                "urgent_response": "Requires immediate response",
                "deadline_approaching": "Deadline is approaching",
                "relationship_risk": "Relationship needs attention",
                "opportunity_window": "Time-sensitive opportunity",
                "action_required": "General action needed",
                "escalation_needed": "Situation requires escalation"
            },
            "urgency_levels": {
                "critical": "Within 24 hours",
                "high": "Within 3 days",
                "medium": "Within 1 week",
                "low": "Within 2 weeks"
            }
        }
    } 