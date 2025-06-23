"""
Tactical Alerts API Routes (Flask)
=================================
Flask-compatible API endpoints for real-time tactical alerts and urgent action items.
"""

import asyncio
from flask import Blueprint, request, jsonify, session
from functools import wraps

from utils.logging import structured_logger as logger
from intelligence.g_realtime_updates.tactical_alerts_system import (
    get_tactical_alerts_system, AlertType, UrgencyLevel
)

alerts_bp = Blueprint('alerts', __name__, url_prefix='/api/alerts')

def async_route(f):
    """Decorator to handle async functions in Flask"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapper

def get_current_user_id():
    """Get current user ID from session"""
    user_email = session.get('user_id')
    if not user_email:
        return None
    # For development, we'll use the email as user ID
    # In production, this would query the database
    return user_email

@alerts_bp.route('/active', methods=['GET'])
@async_route
async def get_active_alerts():
    """Get active tactical alerts for the user"""
    try:
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Get urgency filter from query params
        urgency_param = request.args.get('urgency')
        urgency_filter = None
        if urgency_param:
            try:
                urgency_filter = UrgencyLevel(urgency_param.lower())
            except ValueError:
                return jsonify({'error': f'Invalid urgency level: {urgency_param}'}), 400
        
        alerts_system = await get_tactical_alerts_system(user_id)
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
        
        return jsonify({
            "success": True,
            "alerts": alert_data,
            "count": len(alert_data)
        })
        
    except Exception as e:
        logger.error(f"Error getting active alerts: {str(e)}", user_id=user_id)
        return jsonify({'error': str(e)}), 500

@alerts_bp.route('/summary', methods=['GET'])
@async_route
async def get_alerts_summary():
    """Get summary of current alerts"""
    try:
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({'error': 'Authentication required'}), 401
        
        alerts_system = await get_tactical_alerts_system(user_id)
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
        
        return jsonify({
            "success": True,
            "summary": summary
        })
        
    except Exception as e:
        logger.error(f"Error getting alerts summary: {str(e)}", user_id=user_id)
        return jsonify({'error': str(e)}), 500

@alerts_bp.route('/process-email', methods=['POST'])
@async_route
async def process_email_for_alerts():
    """Process an email for urgent alerts"""
    try:
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({'error': 'Authentication required'}), 401
        
        data = request.get_json()
        if not data or 'email_data' not in data:
            return jsonify({'error': 'email_data required'}), 400
        
        email_data = data['email_data']
        alerts_system = await get_tactical_alerts_system(user_id)
        
        # Process email for alerts
        new_alerts = await alerts_system.process_new_email(email_data)
        
        return jsonify({
            "success": True,
            "message": "Email processed for tactical alerts",
            "email_id": email_data.get('email_id'),
            "alerts_generated": len(new_alerts)
        })
        
    except Exception as e:
        logger.error(f"Error processing email for alerts: {str(e)}", user_id=user_id)
        return jsonify({'error': str(e)}), 500

@alerts_bp.route('/acknowledge', methods=['POST'])
@async_route
async def acknowledge_alert():
    """Acknowledge an alert"""
    try:
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({'error': 'Authentication required'}), 401
        
        data = request.get_json()
        if not data or 'alert_id' not in data:
            return jsonify({'error': 'alert_id required'}), 400
        
        alert_id = data['alert_id']
        alerts_system = await get_tactical_alerts_system(user_id)
        success = await alerts_system.acknowledge_alert(alert_id)
        
        if success:
            return jsonify({
                "success": True,
                "message": f"Alert {alert_id} acknowledged"
            })
        else:
            return jsonify({'error': 'Alert not found'}), 404
            
    except Exception as e:
        logger.error(f"Error acknowledging alert: {str(e)}", user_id=user_id)
        return jsonify({'error': str(e)}), 500

@alerts_bp.route('/dismiss', methods=['POST'])
@async_route
async def dismiss_alert():
    """Dismiss an alert"""
    try:
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({'error': 'Authentication required'}), 401
        
        data = request.get_json()
        if not data or 'alert_id' not in data:
            return jsonify({'error': 'alert_id required'}), 400
        
        alert_id = data['alert_id']
        alerts_system = await get_tactical_alerts_system(user_id)
        success = await alerts_system.dismiss_alert(alert_id)
        
        if success:
            return jsonify({
                "success": True,
                "message": f"Alert {alert_id} dismissed"
            })
        else:
            return jsonify({'error': 'Alert not found'}), 404
            
    except Exception as e:
        logger.error(f"Error dismissing alert: {str(e)}", user_id=user_id)
        return jsonify({'error': str(e)}), 500

@alerts_bp.route('/critical', methods=['GET'])
@async_route
async def get_critical_alerts():
    """Get only critical urgency alerts"""
    try:
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({'error': 'Authentication required'}), 401
        
        alerts_system = await get_tactical_alerts_system(user_id)
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
        
        return jsonify({
            "success": True,
            "critical_alerts": alert_data,
            "count": len(alert_data)
        })
        
    except Exception as e:
        logger.error(f"Error getting critical alerts: {str(e)}", user_id=user_id)
        return jsonify({'error': str(e)}), 500

@alerts_bp.route('/by-contact/<contact_email>', methods=['GET'])
@async_route
async def get_alerts_by_contact(contact_email):
    """Get alerts related to a specific contact"""
    try:
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({'error': 'Authentication required'}), 401
        
        alerts_system = await get_tactical_alerts_system(user_id)
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
        
        return jsonify({
            "success": True,
            "contact_email": contact_email,
            "alerts": alert_data,
            "count": len(alert_data)
        })
        
    except Exception as e:
        logger.error(f"Error getting alerts by contact: {str(e)}", user_id=user_id)
        return jsonify({'error': str(e)}), 500

@alerts_bp.route('/types', methods=['GET'])
def get_alert_types():
    """Get available alert types and urgency levels"""
    return jsonify({
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
    }) 