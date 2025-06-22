# api/webhook_routes.py
import json
import asyncio
from flask import Blueprint, request, jsonify
from datetime import datetime

from utils.logging import structured_logger as logger
from integrations.slack_integration import handle_slack_webhook
from intelligence.incremental_knowledge_system import IncrementalKnowledgeSystem
from auth.auth_utils import get_current_user

webhook_bp = Blueprint('webhooks', __name__, url_prefix='/api/webhooks')

@webhook_bp.route('/slack/events', methods=['POST'])
async def slack_events_webhook():
    """
    Slack Events API webhook handler
    
    Receives real-time Slack events and updates knowledge tree incrementally.
    This enables instant processing of strategic discussions, new contacts, etc.
    """
    try:
        # Verify Slack request signature here in production
        event_data = request.get_json()
        
        # Handle Slack challenge verification
        if 'challenge' in event_data:
            return jsonify({'challenge': event_data['challenge']})
        
        # Extract event information
        event = event_data.get('event', {})
        team_id = event_data.get('team_id')
        
        # Map team_id to user_id (would be stored in database)
        user_id = await _get_user_id_from_slack_team(team_id)
        if not user_id:
            logger.warning(f"⚠️ No user found for Slack team: {team_id}")
            return jsonify({'status': 'ignored', 'reason': 'unknown_team'})
        
        logger.info(f"🔔 Received Slack webhook event: {event.get('type')} for user {user_id}")
        
        # Process event through Slack integration
        knowledge_updates = await handle_slack_webhook(event, user_id)
        
        if knowledge_updates:
            logger.info(f"✅ Knowledge tree updated from Slack event")
            
            # Optionally trigger immediate notifications for high-impact changes
            await _handle_high_impact_updates(user_id, knowledge_updates)
            
            return jsonify({
                'status': 'processed',
                'updates': list(knowledge_updates.keys()),
                'timestamp': datetime.utcnow().isoformat()
            })
        else:
            return jsonify({
                'status': 'processed',
                'updates': [],
                'message': 'No knowledge updates needed'
            })
        
    except Exception as e:
        logger.error(f"❌ Slack webhook processing failed: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@webhook_bp.route('/gmail/push', methods=['POST'])
async def gmail_push_webhook():
    """
    Gmail Push notification webhook
    
    Receives notifications when new emails arrive and processes them incrementally.
    """
    try:
        # Gmail sends push notifications as Pub/Sub messages
        push_data = request.get_json()
        
        if not push_data or 'message' not in push_data:
            return jsonify({'status': 'ignored', 'reason': 'invalid_format'})
        
        # Decode the Pub/Sub message
        import base64
        message_data = json.loads(base64.b64decode(push_data['message']['data']).decode('utf-8'))
        
        user_email = message_data.get('emailAddress')
        history_id = message_data.get('historyId')
        
        # Get user ID from email
        user_id = await _get_user_id_from_email(user_email)
        if not user_id:
            return jsonify({'status': 'ignored', 'reason': 'unknown_user'})
        
        logger.info(f"📧 Gmail push notification received for user {user_id}")
        
        # Fetch new emails and process incrementally
        knowledge_updates = await _process_gmail_push_notification(user_id, history_id)
        
        if knowledge_updates:
            return jsonify({
                'status': 'processed',
                'updates': list(knowledge_updates.keys())
            })
        else:
            return jsonify({
                'status': 'processed', 
                'updates': [],
                'message': 'No new emails requiring knowledge updates'
            })
        
    except Exception as e:
        logger.error(f"❌ Gmail webhook processing failed: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@webhook_bp.route('/manual/new-email', methods=['POST'])
async def manual_new_email_webhook():
    """
    Manual webhook for testing new email processing
    
    Allows manual triggering of incremental email processing for testing.
    """
    try:
        user = get_current_user()  # Get authenticated user
        email_data = request.get_json()
        
        if not email_data:
            return jsonify({'error': 'Email data required'}), 400
        
        logger.info(f"🔧 Manual email processing triggered for user {user.id}")
        
        # Initialize incremental knowledge system
        incremental_system = IncrementalKnowledgeSystem(user.id)
        await incremental_system.initialize()
        
        # Process the email
        knowledge_updates = await incremental_system.process_new_email(email_data)
        
        return jsonify({
            'status': 'processed',
            'updates': knowledge_updates or {},
            'message': 'Email processed successfully' if knowledge_updates else 'No significant changes detected'
        })
        
    except Exception as e:
        logger.error(f"❌ Manual email processing failed: {e}")
        return jsonify({'error': str(e)}), 500

@webhook_bp.route('/calendar/events', methods=['POST']) 
async def calendar_events_webhook():
    """
    Calendar events webhook (Google Calendar, Outlook, etc.)
    
    Processes new calendar events for meeting intelligence and relationship mapping.
    """
    try:
        event_data = request.get_json()
        
        # Extract user identification from calendar event
        user_id = await _get_user_id_from_calendar_event(event_data)
        if not user_id:
            return jsonify({'status': 'ignored', 'reason': 'unknown_user'})
        
        logger.info(f"📅 Calendar event received for user {user_id}")
        
        # Process calendar event for knowledge updates
        knowledge_updates = await _process_calendar_event(user_id, event_data)
        
        return jsonify({
            'status': 'processed',
            'updates': knowledge_updates or {}
        })
        
    except Exception as e:
        logger.error(f"❌ Calendar webhook processing failed: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@webhook_bp.route('/test/trigger-update', methods=['POST'])
async def test_trigger_update():
    """
    Test endpoint to demonstrate incremental updates
    """
    try:
        user = get_current_user()
        test_data = request.get_json()
        
        test_type = test_data.get('type', 'email')
        
        if test_type == 'email':
            # Simulate new email
            fake_email = {
                'id': f"test_email_{datetime.utcnow().timestamp()}",
                'sender': test_data.get('sender', 'test@example.com'),
                'subject': test_data.get('subject', 'Test Strategic Discussion'),
                'body_text': test_data.get('content', 'This is a test email about our Q4 roadmap planning and competitive analysis.'),
                'created_at': datetime.utcnow().isoformat()
            }
            
            incremental_system = IncrementalKnowledgeSystem(user.id)
            await incremental_system.initialize()
            
            updates = await incremental_system.process_new_email(fake_email)
            
        elif test_type == 'slack':
            # Simulate Slack message
            fake_slack = {
                'channel': test_data.get('channel', 'strategy'),
                'user': test_data.get('user', 'U123456'),
                'text': test_data.get('content', 'We need to discuss our competitive positioning for next quarter.'),
                'ts': str(datetime.utcnow().timestamp())
            }
            
            updates = await handle_slack_webhook(fake_slack, user.id)
            
        else:
            return jsonify({'error': 'Invalid test type'}), 400
        
        return jsonify({
            'status': 'test_completed',
            'test_type': test_type,
            'updates': updates or {},
            'message': f'Test {test_type} processed successfully'
        })
        
    except Exception as e:
        logger.error(f"❌ Test trigger failed: {e}")
        return jsonify({'error': str(e)}), 500

# Helper functions

async def _get_user_id_from_slack_team(team_id: str) -> Optional[int]:
    """Get user ID from Slack team ID"""
    # In production, this would query database for user with this Slack team
    # For now, return hardcoded user ID for testing
    if team_id:  # Any team ID maps to user 1 for testing
        return 1
    return None

async def _get_user_id_from_email(email: str) -> Optional[int]:
    """Get user ID from email address"""
    # Query database for user with this email
    # For testing, return user 1 if email matches
    if email == 'Sandman@session-42.com':
        return 1
    return None

async def _get_user_id_from_calendar_event(event_data: Dict) -> Optional[int]:
    """Extract user ID from calendar event"""
    # Implementation would depend on calendar provider
    return 1  # Default for testing

async def _process_gmail_push_notification(user_id: int, history_id: str) -> Optional[Dict]:
    """Process Gmail push notification and fetch new emails"""
    try:
        # This would:
        # 1. Use Gmail API to fetch emails since history_id
        # 2. Process each new email through incremental system
        # 3. Return combined updates
        
        logger.info(f"📧 Processing Gmail push for user {user_id}, history: {history_id}")
        
        # Simulate processing
        incremental_system = IncrementalKnowledgeSystem(user_id)
        await incremental_system.initialize()
        
        # In real implementation, fetch actual new emails here
        # For now, return None to indicate no updates
        return None
        
    except Exception as e:
        logger.error(f"❌ Gmail push processing failed: {e}")
        return None

async def _process_calendar_event(user_id: int, event_data: Dict) -> Optional[Dict]:
    """Process calendar event for knowledge updates"""
    try:
        # Extract meeting participants, topics, etc.
        # Update relationship mapping and meeting intelligence
        
        attendees = event_data.get('attendees', [])
        subject = event_data.get('summary', '')
        
        logger.info(f"📅 Processing calendar event: {subject} with {len(attendees)} attendees")
        
        # Process through incremental system
        incremental_system = IncrementalKnowledgeSystem(user_id)
        await incremental_system.initialize()
        
        # Convert calendar event to email-like format for processing
        calendar_as_email = {
            'id': f"calendar_{event_data.get('id', datetime.utcnow().timestamp())}",
            'sender': event_data.get('organizer', {}).get('email', ''),
            'subject': f"Meeting: {subject}",
            'body_text': f"Meeting scheduled: {subject}. Attendees: {', '.join([a.get('email', '') for a in attendees])}",
            'created_at': event_data.get('start', {}).get('dateTime', datetime.utcnow().isoformat())
        }
        
        updates = await incremental_system.process_new_email(calendar_as_email)
        
        if updates:
            # Add calendar-specific metadata
            updates['calendar_metadata'] = {
                'event_type': 'meeting',
                'attendee_count': len(attendees),
                'duration': event_data.get('duration'),
                'location': event_data.get('location')
            }
        
        return updates
        
    except Exception as e:
        logger.error(f"❌ Calendar event processing failed: {e}")
        return None

async def _handle_high_impact_updates(user_id: int, knowledge_updates: Dict):
    """Handle high-impact knowledge updates with notifications"""
    try:
        # Check if any updates are high-impact
        high_impact_types = ['strategic_insights', 'new_topics', 'strategic_discussion']
        
        has_high_impact = any(update_type in knowledge_updates for update_type in high_impact_types)
        
        if has_high_impact:
            logger.info(f"🚨 High-impact knowledge update detected for user {user_id}")
            
            # In production, this could:
            # 1. Send push notification to mobile app
            # 2. Send email summary
            # 3. Update dashboard with alert
            # 4. Trigger additional analysis
            
            # For now, just log the significant update
            update_summary = []
            for update_type, data in knowledge_updates.items():
                if update_type in high_impact_types:
                    update_summary.append(f"{update_type}: {len(data) if isinstance(data, dict) else 1} items")
            
            logger.info(f"📊 High-impact updates: {', '.join(update_summary)}")
            
    except Exception as e:
        logger.error(f"❌ Failed to handle high-impact updates: {e}") 