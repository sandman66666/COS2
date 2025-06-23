"""
Synchronous Logging API Routes
=============================
API endpoints for step logging system analysis and monitoring
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from flask import Blueprint, request, jsonify, session
from middleware.auth_middleware import require_auth

from utils.step_logger import step_logger
from utils.step_analyzer import step_analyzer, generate_quick_report

# Create blueprint
logging_bp = Blueprint('logging', __name__, url_prefix='/api/logging')

@logging_bp.route('/status', methods=['GET'])
@require_auth
def get_system_status():
    """Get current system status and active operations"""
    try:
        status = step_logger.get_pipeline_status()
        
        return jsonify({
            'success': True,
            'timestamp': datetime.utcnow().isoformat(),
            'status': status,
            'mode': 'synchronous'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@logging_bp.route('/performance-report', methods=['GET'])
@require_auth
def get_performance_report():
    """Get comprehensive performance analysis report"""
    try:
        days_back = int(request.args.get('days_back', 7))
        
        # Generate comprehensive report
        performance_report = step_analyzer.generate_performance_report(days_back)
        bottleneck_analysis = step_analyzer.get_bottleneck_analysis(days_back)
        data_flow_analysis = step_analyzer.get_data_flow_analysis(days_back)
        user_activity = step_analyzer.get_user_activity_analysis(days_back)
        
        return jsonify({
            'success': True,
            'analysis_period_days': days_back,
            'generated_at': datetime.utcnow().isoformat(),
            'performance_report': performance_report,
            'bottleneck_analysis': bottleneck_analysis,
            'data_flow_analysis': data_flow_analysis,
            'user_activity': user_activity,
            'mode': 'synchronous'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@logging_bp.route('/quick-report', methods=['GET'])
@require_auth
def get_quick_report():
    """Get a quick text-based performance report"""
    try:
        days_back = int(request.args.get('days_back', 1))
        report_text = generate_quick_report(days_back)
        
        return jsonify({
            'success': True,
            'report_text': report_text,
            'days_back': days_back,
            'generated_at': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@logging_bp.route('/step-analysis/<step_name>', methods=['GET'])
@require_auth
def get_step_analysis(step_name):
    """Get detailed analysis for a specific step"""
    try:
        hours_back = int(request.args.get('hours_back', 24))
        
        # Get step analysis from logger (in-memory)
        analysis = step_logger.get_step_analysis(step_name, hours_back)
        
        return jsonify({
            'success': True,
            'step_name': step_name,
            'hours_back': hours_back,
            'analysis': analysis,
            'generated_at': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@logging_bp.route('/bottlenecks', methods=['GET'])
@require_auth
def get_bottleneck_analysis():
    """Get bottleneck analysis and optimization recommendations"""
    try:
        days_back = int(request.args.get('days_back', 7))
        analysis = step_analyzer.get_bottleneck_analysis(days_back)
        
        return jsonify({
            'success': True,
            'analysis': analysis,
            'days_back': days_back,
            'generated_at': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@logging_bp.route('/data-flow', methods=['GET'])
@require_auth
def get_data_flow_analysis():
    """Get data flow analysis through the system"""
    try:
        days_back = int(request.args.get('days_back', 7))
        analysis = step_analyzer.get_data_flow_analysis(days_back)
        
        return jsonify({
            'success': True,
            'analysis': analysis,
            'days_back': days_back,
            'generated_at': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@logging_bp.route('/user-activity', methods=['GET'])
@require_auth
def get_user_activity():
    """Get user activity analysis"""
    try:
        days_back = int(request.args.get('days_back', 7))
        analysis = step_analyzer.get_user_activity_analysis(days_back)
        
        return jsonify({
            'success': True,
            'analysis': analysis,
            'days_back': days_back,
            'generated_at': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@logging_bp.route('/recent-completions', methods=['GET'])
@require_auth
def get_recent_completions():
    """Get recent step completions with details"""
    try:
        limit = int(request.args.get('limit', 20))
        
        # Get recent completions from step logger
        recent = list(step_logger.recent_completions)[-limit:]
        
        # Convert to JSON-serializable format
        completions = []
        for step in recent:
            completion = step.to_dict()
            completions.append(completion)
        
        return jsonify({
            'success': True,
            'recent_completions': completions,
            'count': len(completions),
            'requested_limit': limit
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@logging_bp.route('/step-performance-history', methods=['GET'])
@require_auth
def get_step_performance_history():
    """Get performance history for all steps"""
    try:
        # Convert deques to lists for JSON serialization
        history = {}
        for step_name, step_history in step_logger.step_performance_history.items():
            history[step_name] = list(step_history)
        
        return jsonify({
            'success': True,
            'performance_history': history,
            'step_count': len(history),
            'generated_at': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@logging_bp.route('/start-demo-pipeline', methods=['POST'])
@require_auth
def start_demo_pipeline():
    """Start a demo pipeline to generate sample log data"""
    try:
        user_email = session.get('user_id', 'demo@session-42.com')
        
        # Start a demo pipeline
        pipeline_id = step_logger.start_pipeline(
            user_id=user_email,
            pipeline_type="demo_intelligence_pipeline"
        )
        
        return jsonify({
            'success': True,
            'pipeline_id': pipeline_id,
            'message': 'Demo pipeline started',
            'note': 'This pipeline will generate sample step data for testing the logging system'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@logging_bp.route('/demo-pipeline/<pipeline_id>/run-steps', methods=['POST'])
@require_auth
def run_demo_steps(pipeline_id):
    """Run demo steps for testing the logging system"""
    try:
        from utils.step_logger import StepTracker
        import time
        import random
        
        # Demo step data
        demo_steps = [
            {
                'name': 'extract_contacts',
                'input_data': {'emails_to_process': 150, 'filters': ['trusted', 'business']},
                'processing_time': random.uniform(0.5, 2.0),
                'output_data': {'contacts_found': 47, 'trust_scores': [0.8, 0.9, 0.7]}
            },
            {
                'name': 'enrich_contacts', 
                'input_data': {'contacts': 47, 'enrichment_sources': ['email_signatures', 'domain_data']},
                'processing_time': random.uniform(1.0, 3.0),
                'output_data': {'enriched_contacts': 42, 'success_rate': 0.89}
            },
            {
                'name': 'build_knowledge_tree',
                'input_data': {'contacts': 42, 'emails': 150, 'analysis_depth': 'comprehensive'},
                'processing_time': random.uniform(2.0, 5.0),
                'output_data': {'tree_nodes': 89, 'relationships': 156, 'insights': 23}
            },
            {
                'name': 'generate_intelligence',
                'input_data': {'knowledge_tree': 89, 'focus_areas': ['strategic', 'tactical']},
                'processing_time': random.uniform(1.5, 4.0),
                'output_data': {'intelligence_reports': 3, 'action_items': 12}
            }
        ]
        
        # Run demo steps
        completed_steps = []
        for step_info in demo_steps:
            with StepTracker(
                pipeline_id=pipeline_id,
                step_name=step_info['name'],
                input_data=step_info['input_data'],
                tags=['demo', 'testing']
            ) as tracker:
                
                # Simulate processing
                time.sleep(step_info['processing_time'])
                
                # Set output data
                tracker.set_output(step_info['output_data'])
                tracker.add_metric('processing_complexity', random.uniform(0.3, 1.0))
                tracker.add_metric('data_quality_score', random.uniform(0.7, 1.0))
                
                completed_steps.append(step_info['name'])
        
        # Complete the pipeline
        step_logger.complete_pipeline(
            pipeline_id=pipeline_id,
            status="completed",
            global_metrics={
                'demo_mode': True,
                'total_processing_time_s': sum(s['processing_time'] for s in demo_steps),
                'complexity_score': random.uniform(0.5, 0.9)
            }
        )
        
        return jsonify({
            'success': True,
            'pipeline_id': pipeline_id,
            'completed_steps': completed_steps,
            'message': f'Demo pipeline completed with {len(completed_steps)} steps',
            'note': 'Check the performance reports to see the generated data!'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@logging_bp.route('/cleanup-logs', methods=['POST'])
@require_auth
def cleanup_old_logs():
    """Clean up old log files"""
    try:
        step_logger.cleanup_old_logs()
        
        return jsonify({
            'success': True,
            'message': 'Log cleanup completed',
            'retention_days': step_logger.retention_days
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@logging_bp.route('/sample-data', methods=['GET'])
@require_auth
def get_sample_data():
    """Get sample data from recent step executions"""
    try:
        limit = int(request.args.get('limit', 5))
        
        # Get recent completions with sample data
        recent = list(step_logger.recent_completions)[-limit:]
        samples = []
        
        for step in recent:
            if hasattr(step, 'sample_data') and step.sample_data:
                samples.append({
                    'step_name': step.step_name,
                    'step_id': step.step_id,
                    'timestamp': step.end_time.isoformat() if step.end_time else None,
                    'sample_data': step.sample_data,
                    'status': step.status
                })
        
        return jsonify({
            'success': True,
            'sample_data': samples,
            'count': len(samples),
            'sampling_rate': step_logger.sampling_rate,
            'note': f'Sampling {step_logger.sampling_rate*100:.1f}% of data to keep logs manageable'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500 