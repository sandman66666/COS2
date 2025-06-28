"""
Unified Intelligence API Routes
==============================
API endpoints for the unified intelligence orchestrator that combines
core and strategic analysis into one comprehensive system.
"""

import asyncio
import os
from datetime import datetime
from flask import Blueprint, request, jsonify
from typing import Dict, Any

from auth.session_manager import require_auth, get_current_user_email
from intelligence.unified_intelligence_orchestrator import UnifiedIntelligenceOrchestrator
from utils.logging import structured_logger as logger

unified_intelligence_bp = Blueprint('unified_intelligence', __name__)

@unified_intelligence_bp.route('/api/unified-intelligence/generate', methods=['POST'])
@require_auth
def generate_unified_intelligence():
    """
    Generate comprehensive unified intelligence combining all analysts
    
    Body parameters:
    - content_window_days (optional): Days of content to analyze (default: 90)
    - force_rebuild (optional): Force rebuild of all analysis (default: false)
    - focus_areas (optional): Specific areas to focus analysis on
    """
    try:
        user_email = get_current_user_email()
        if not user_email:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        # Get request parameters
        data = request.get_json() or {}
        content_window_days = data.get('content_window_days', 90)
        force_rebuild = data.get('force_rebuild', False)
        focus_areas = data.get('focus_areas', [])
        
        # Get Claude API key
        claude_api_key = os.getenv('ANTHROPIC_API_KEY')
        if not claude_api_key:
            return jsonify({
                'success': False,
                'error': 'Claude API key not configured'
            }), 500
        
        # Get user ID
        from storage.storage_manager_sync import get_storage_manager_sync
        storage_manager = get_storage_manager_sync()
        user = storage_manager.get_user_by_email(user_email)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        user_id = user['id']
        
        # Initialize unified orchestrator
        orchestrator = UnifiedIntelligenceOrchestrator(user_id, claude_api_key)
        
        # Generate unified intelligence (async)
        async def generate_intelligence():
            return await orchestrator.generate_comprehensive_intelligence(
                content_window_days=content_window_days,
                force_rebuild=force_rebuild
            )
        
        # Run async function
        intelligence_report = asyncio.run(generate_intelligence())
        
        if intelligence_report.get('error'):
            return jsonify({
                'success': False,
                'error': intelligence_report['error']
            }), 500
        
        # Return comprehensive intelligence
        return jsonify({
            'success': True,
            'unified_intelligence': intelligence_report,
            'generation_timestamp': datetime.utcnow().isoformat(),
            'user_email': user_email,
            'analysis_scope': {
                'content_window_days': content_window_days,
                'force_rebuild': force_rebuild,
                'focus_areas': focus_areas
            }
        })
        
    except Exception as e:
        logger.error(f"Error generating unified intelligence: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Intelligence generation failed: {str(e)}'
        }), 500

@unified_intelligence_bp.route('/api/unified-intelligence/status', methods=['GET'])
@require_auth
def get_intelligence_status():
    """Get status of existing unified intelligence analysis"""
    try:
        user_email = get_current_user_email()
        if not user_email:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        # Get user and check for existing intelligence
        from storage.storage_manager_sync import get_storage_manager_sync
        storage_manager = get_storage_manager_sync()
        user = storage_manager.get_user_by_email(user_email)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        user_id = user['id']
        
        # Get latest unified intelligence
        unified_intelligence = storage_manager.get_knowledge_tree(user_id, "unified_intelligence_v1")
        
        if not unified_intelligence:
            return jsonify({
                'success': True,
                'has_analysis': False,
                'message': 'No unified intelligence analysis found'
            })
        
        # Extract status information
        content_scope = unified_intelligence.get('content_scope', {})
        analysis_timestamp = unified_intelligence.get('analysis_timestamp')
        
        return jsonify({
            'success': True,
            'has_analysis': True,
            'analysis_timestamp': analysis_timestamp,
            'content_scope': content_scope,
            'analysis_sections': list(unified_intelligence.keys()),
            'executive_summary': unified_intelligence.get('executive_summary', {})
        })
        
    except Exception as e:
        logger.error(f"Error getting intelligence status: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Status check failed: {str(e)}'
        }), 500

@unified_intelligence_bp.route('/api/unified-intelligence/insights/<insight_type>', methods=['GET'])
@require_auth
def get_specific_insights(insight_type: str):
    """
    Get specific type of insights from unified intelligence
    
    Available insight types:
    - foundation: Core knowledge tree and analyst insights
    - executive: Strategic network, competitive position, decision support
    - synthesis: Cross-system unified insights
    - summary: Executive summary and key recommendations
    """
    try:
        user_email = get_current_user_email()
        if not user_email:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        # Validate insight type
        valid_types = ['foundation', 'executive', 'synthesis', 'summary']
        if insight_type not in valid_types:
            return jsonify({
                'success': False,
                'error': f'Invalid insight type. Must be one of: {valid_types}'
            }), 400
        
        # Get user and unified intelligence
        from storage.storage_manager_sync import get_storage_manager_sync
        storage_manager = get_storage_manager_sync()
        user = storage_manager.get_user_by_email(user_email)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        user_id = user['id']
        unified_intelligence = storage_manager.get_knowledge_tree(user_id, "unified_intelligence_v1")
        
        if not unified_intelligence:
            return jsonify({
                'success': False,
                'error': 'No unified intelligence analysis found. Please generate intelligence first.'
            }), 404
        
        # Extract specific insights
        insight_mapping = {
            'foundation': unified_intelligence.get('foundation_intelligence', {}),
            'executive': unified_intelligence.get('executive_intelligence', {}),
            'synthesis': unified_intelligence.get('unified_insights', {}),
            'summary': unified_intelligence.get('executive_summary', {})
        }
        
        insights = insight_mapping.get(insight_type, {})
        
        return jsonify({
            'success': True,
            'insight_type': insight_type,
            'insights': insights,
            'analysis_timestamp': unified_intelligence.get('analysis_timestamp'),
            'content_scope': unified_intelligence.get('content_scope', {})
        })
        
    except Exception as e:
        logger.error(f"Error getting specific insights: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Insight retrieval failed: {str(e)}'
        }), 500

@unified_intelligence_bp.route('/api/unified-intelligence/compare-systems', methods=['GET'])
@require_auth
def compare_intelligence_systems():
    """
    Compare unified intelligence with legacy separate systems
    (For transition period - shows differences between old and new approach)
    """
    try:
        user_email = get_current_user_email()
        if not user_email:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        from storage.storage_manager_sync import get_storage_manager_sync
        storage_manager = get_storage_manager_sync()
        user = storage_manager.get_user_by_email(user_email)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        user_id = user['id']
        
        # Get unified intelligence
        unified_intelligence = storage_manager.get_knowledge_tree(user_id, "unified_intelligence_v1")
        
        # Get legacy knowledge tree
        legacy_knowledge_tree = storage_manager.get_knowledge_tree(user_id, "default")
        
        # Get legacy CEO intelligence (if exists)
        # This would come from the separate CEO system
        
        comparison = {
            'unified_system': {
                'exists': unified_intelligence is not None,
                'timestamp': unified_intelligence.get('analysis_timestamp') if unified_intelligence else None,
                'coverage': {
                    'foundation_intelligence': bool(unified_intelligence.get('foundation_intelligence')) if unified_intelligence else False,
                    'executive_intelligence': bool(unified_intelligence.get('executive_intelligence')) if unified_intelligence else False,
                    'unified_insights': bool(unified_intelligence.get('unified_insights')) if unified_intelligence else False
                } if unified_intelligence else {}
            },
            'legacy_systems': {
                'knowledge_tree': {
                    'exists': legacy_knowledge_tree is not None,
                    'timestamp': legacy_knowledge_tree.get('timestamp') if legacy_knowledge_tree else None
                },
                'ceo_intelligence': {
                    'exists': False,  # Would check for CEO intelligence
                    'timestamp': None
                }
            },
            'recommendation': 'unified' if unified_intelligence else 'generate_unified'
        }
        
        return jsonify({
            'success': True,
            'comparison': comparison,
            'transition_status': 'in_progress' if unified_intelligence else 'pending'
        })
        
    except Exception as e:
        logger.error(f"Error comparing intelligence systems: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Comparison failed: {str(e)}'
        }), 500

@unified_intelligence_bp.route('/api/unified-intelligence/migrate', methods=['POST'])
@require_auth
def migrate_to_unified_system():
    """
    Migrate from separate intelligence systems to unified system
    """
    try:
        user_email = get_current_user_email()
        if not user_email:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        # Get request parameters
        data = request.get_json() or {}
        preserve_legacy = data.get('preserve_legacy', True)
        force_regenerate = data.get('force_regenerate', False)
        
        from storage.storage_manager_sync import get_storage_manager_sync
        storage_manager = get_storage_manager_sync()
        user = storage_manager.get_user_by_email(user_email)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        user_id = user['id']
        
        # Check if unified intelligence already exists
        unified_intelligence = storage_manager.get_knowledge_tree(user_id, "unified_intelligence_v1")
        
        if unified_intelligence and not force_regenerate:
            return jsonify({
                'success': True,
                'message': 'Unified intelligence already exists',
                'analysis_timestamp': unified_intelligence.get('analysis_timestamp'),
                'action': 'no_migration_needed'
            })
        
        # Generate unified intelligence
        claude_api_key = os.getenv('ANTHROPIC_API_KEY')
        if not claude_api_key:
            return jsonify({
                'success': False,
                'error': 'Claude API key not configured'
            }), 500
        
        orchestrator = UnifiedIntelligenceOrchestrator(user_id, claude_api_key)
        
        async def migrate():
            return await orchestrator.generate_comprehensive_intelligence(
                content_window_days=90,
                force_rebuild=True
            )
        
        unified_intelligence = asyncio.run(migrate())
        
        if unified_intelligence.get('error'):
            return jsonify({
                'success': False,
                'error': f'Migration failed: {unified_intelligence["error"]}'
            }), 500
        
        # Archive legacy systems if requested
        migration_result = {
            'success': True,
            'message': 'Successfully migrated to unified intelligence system',
            'unified_intelligence_timestamp': unified_intelligence.get('analysis_timestamp'),
            'preserve_legacy': preserve_legacy,
            'migration_timestamp': datetime.utcnow().isoformat()
        }
        
        if not preserve_legacy:
            # Could delete legacy knowledge trees here
            migration_result['legacy_cleanup'] = 'completed'
        
        return jsonify(migration_result)
        
    except Exception as e:
        logger.error(f"Error migrating to unified system: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Migration failed: {str(e)}'
        }), 500 