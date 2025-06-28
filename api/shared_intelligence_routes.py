"""
Shared Intelligence API Routes
=============================
API endpoints for managing the global contact intelligence system
with shared web intelligence and private user context.
"""

from flask import Blueprint, request, jsonify, session
from datetime import datetime
import asyncio
import logging

from middleware.auth_middleware import require_auth
from storage.storage_manager_sync import get_storage_manager_sync
from storage.global_contact_intelligence import GlobalContactIntelligenceManager
from utils.logging import structured_logger as logger

# Create blueprint
shared_intelligence_bp = Blueprint('shared_intelligence', __name__, url_prefix='/api/shared-intelligence')

@shared_intelligence_bp.route('/stats', methods=['GET'])
@require_auth
def get_shared_intelligence_stats():
    """Get statistics about the shared intelligence system"""
    try:
        user_email = session.get('user_id', 'test@session-42.com')
        
        # Create a temporary storage manager to access global intelligence
        storage_manager = get_storage_manager_sync()
        
        # Run async function in sync context
        async def get_stats():
            global_intelligence = GlobalContactIntelligenceManager(storage_manager)
            await global_intelligence.initialize()
            return await global_intelligence.get_enrichment_stats()
        
        # Run in event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        stats = loop.run_until_complete(get_stats())
        loop.close()
        
        return jsonify({
            'success': True,
            'stats': stats,
            'user_email': user_email,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting shared intelligence stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@shared_intelligence_bp.route('/contact/<email>', methods=['GET'])
@require_auth
def get_shared_contact_intelligence(email):
    """Get shared intelligence for a specific contact"""
    try:
        user_email = session.get('user_id', 'test@session-42.com')
        
        # Get user info
        storage_manager = get_storage_manager_sync()
        user = storage_manager.get_user_by_email(user_email)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        user_id = user['id']
        
        # Run async function in sync context
        async def get_intelligence():
            global_intelligence = GlobalContactIntelligenceManager(storage_manager)
            await global_intelligence.initialize()
            
            shared_record = await global_intelligence.get_shared_intelligence(email)
            has_user_context = await global_intelligence.get_user_context(user_id, email) is not None
            
            return shared_record, has_user_context
        
        # Run in event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        shared_record, has_user_context = loop.run_until_complete(get_intelligence())
        loop.close()
        
        if shared_record:
            return jsonify({
                'success': True,
                'shared_intelligence': {
                    'email': shared_record.email,
                    'confidence_score': shared_record.confidence_score,
                    'verification_count': shared_record.verification_count,
                    'data_sources': shared_record.data_sources,
                    'last_updated': shared_record.last_web_update.isoformat(),
                    'quality_score': shared_record.calculate_quality_score(),
                    'is_fresh': shared_record.is_fresh(),
                    'engagement_success_rate': shared_record.engagement_success_rate,
                    'user_contributions': len(shared_record.user_contributions),
                    'web_intelligence_preview': {
                        'person_data_keys': list(shared_record.web_intelligence.get('person_data', {}).keys()),
                        'company_data_keys': list(shared_record.web_intelligence.get('company_data', {}).keys()),
                        'intelligence_modules': list(shared_record.web_intelligence.keys())
                    }
                },
                'has_user_context': has_user_context
            })
        else:
            return jsonify({
                'success': True,
                'shared_intelligence': None,
                'message': f'No shared intelligence found for {email}',
                'has_user_context': has_user_context
            })
        
    except Exception as e:
        logger.error(f"Error getting shared intelligence for {email}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@shared_intelligence_bp.route('/update-engagement', methods=['POST'])
@require_auth
def update_engagement_success():
    """Update engagement success rates for shared learning"""
    try:
        user_email = session.get('user_id', 'test@session-42.com')
        request_data = request.get_json() or {}
        
        email = request_data.get('email')
        meeting_requested = request_data.get('meeting_requested', False)
        meeting_accepted = request_data.get('meeting_accepted', False)
        
        if not email:
            return jsonify({
                'success': False,
                'error': 'Email is required'
            }), 400
        
        # Get user info
        storage_manager = get_storage_manager_sync()
        user = storage_manager.get_user_by_email(user_email)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        user_id = user['id']
        
        # Run async function in sync context
        async def update_engagement():
            global_intelligence = GlobalContactIntelligenceManager(storage_manager)
            await global_intelligence.initialize()
            
            await global_intelligence.update_engagement_success(
                email, user_id, meeting_requested, meeting_accepted
            )
        
        # Run in event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(update_engagement())
        loop.close()
        
        return jsonify({
            'success': True,
            'message': f'Updated engagement success for {email}',
            'user_id': user_id,
            'meeting_requested': meeting_requested,
            'meeting_accepted': meeting_accepted
        })
        
    except Exception as e:
        logger.error(f"Error updating engagement success: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@shared_intelligence_bp.route('/user-context/<email>', methods=['GET'])
@require_auth
def get_user_contact_context(email):
    """Get user-specific context for a contact"""
    try:
        user_email = session.get('user_id', 'test@session-42.com')
        
        # Get user info
        storage_manager = get_storage_manager_sync()
        user = storage_manager.get_user_by_email(user_email)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        user_id = user['id']
        
        # Run async function in sync context
        async def get_context():
            global_intelligence = GlobalContactIntelligenceManager(storage_manager)
            await global_intelligence.initialize()
            
            return await global_intelligence.get_user_context(user_id, email)
        
        # Run in event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        user_context = loop.run_until_complete(get_context())
        loop.close()
        
        if user_context:
            return jsonify({
                'success': True,
                'user_context': {
                    'user_id': user_context.user_id,
                    'email': user_context.email,
                    'relationship_stage': user_context.relationship_stage,
                    'communication_style': user_context.communication_style,
                    'last_contact_date': user_context.last_contact_date.isoformat() if user_context.last_contact_date else None,
                    'engagement_history_length': len(user_context.engagement_history),
                    'personal_notes': user_context.personal_notes,
                    'custom_approach': user_context.custom_approach,
                    'meeting_requests_sent': user_context.meeting_requests_sent,
                    'meeting_requests_accepted': user_context.meeting_requests_accepted,
                    'response_rate': user_context.response_rate,
                    'email_patterns': user_context.email_patterns
                }
            })
        else:
            return jsonify({
                'success': True,
                'user_context': None,
                'message': f'No user context found for {email}'
            })
        
    except Exception as e:
        logger.error(f"Error getting user context for {email}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@shared_intelligence_bp.route('/cache-performance', methods=['GET'])
@require_auth
def get_cache_performance():
    """Get cache hit/miss statistics for the shared intelligence system"""
    try:
        user_email = session.get('user_id', 'test@session-42.com')
        
        # This would typically come from the enrichment service metrics
        # For now, return a basic structure
        return jsonify({
            'success': True,
            'cache_performance': {
                'cache_hits': 0,
                'fresh_scrapes': 0,
                'user_contexts_created': 0,
                'cross_user_validations': 0,
                'cache_hit_rate': 0.0,
                'time_saved_estimate_minutes': 0,
                'cost_savings_estimate_usd': 0.0
            },
            'message': 'Cache performance tracking will be available after enrichment runs',
            'user_email': user_email
        })
        
    except Exception as e:
        logger.error(f"Error getting cache performance: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@shared_intelligence_bp.route('/health', methods=['GET'])
def health_check():
    """Health check for shared intelligence system"""
    try:
        storage_manager = get_storage_manager_sync()
        
        # Test database connectivity
        async def test_system():
            global_intelligence = GlobalContactIntelligenceManager(storage_manager)
            await global_intelligence.initialize()
            
            # Get basic stats to test system
            stats = await global_intelligence.get_enrichment_stats()
            return stats
        
        # Run in event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        stats = loop.run_until_complete(test_system())
        loop.close()
        
        return jsonify({
            'success': True,
            'status': 'healthy',
            'system_info': {
                'global_contacts': stats.get('global_intelligence', {}).get('total_contacts', 0),
                'active_users': stats.get('user_contexts', {}).get('active_users', 0),
                'cached_contacts': stats.get('hot_cache', {}).get('cached_contacts', 0)
            },
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Shared intelligence health check failed: {e}")
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500 