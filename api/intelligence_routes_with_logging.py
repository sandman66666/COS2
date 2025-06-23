"""
Enhanced Intelligence Routes with Step Logging
==============================================
Example of how to integrate step logging into intelligence pipeline operations
"""

import json
import time
from datetime import datetime
from typing import Dict, List, Optional

from flask import Blueprint, request, jsonify, session
from middleware.auth_middleware import require_auth

from utils.step_logger import step_logger, StepTracker
from utils.logging import structured_logger as logger
from storage.storage_manager_sync import get_storage_manager_sync

# Create blueprint
intelligence_logging_bp = Blueprint('intelligence_logging', __name__, url_prefix='/api/intelligence-logged')

@intelligence_logging_bp.route('/full-pipeline', methods=['POST'])
@require_auth
def run_full_intelligence_pipeline_with_logging():
    """Run full intelligence pipeline with comprehensive step logging"""
    try:
        user_email = session.get('user_id', 'demo@session-42.com')
        
        # Get request parameters
        data = request.get_json() or {}
        days_back = data.get('days_back', 30)
        force_refresh = data.get('force_refresh', False)
        
        # Start pipeline logging
        pipeline_id = step_logger.start_pipeline(
            user_id=user_email,
            pipeline_type="full_intelligence_pipeline",
            session_id=session.get('session_id', f"session_{int(time.time())}")
        )
        
        logger.info("Starting logged intelligence pipeline", 
                   pipeline_id=pipeline_id, user_email=user_email)
        
        # Initialize storage
        storage_manager = get_storage_manager_sync()
        user = storage_manager.get_user_by_email(user_email)
        if not user:
            user = storage_manager.create_user(user_email, user_email)
        
        user_id = user['id']
        pipeline_results = {}
        
        # STEP 1: Extract Contacts with Logging
        with StepTracker(
            pipeline_id=pipeline_id,
            step_name="extract_contacts",
            input_data={"days_back": days_back, "force_refresh": force_refresh},
            dependencies=[],
            tags=["data_collection", "contacts"]
        ) as tracker:
            
            logger.info("Step 1: Extracting contacts with logging")
            
            # Simulate contact extraction
            time.sleep(1.0)  # Simulate processing time
            
            # Mock contact extraction results
            contacts_data = {
                'contacts_found': 45,
                'trust_tiers': {'tier_1': 12, 'tier_2': 18, 'tier_3': 15},
                'domains_analyzed': 23,
                'extraction_method': 'gmail_analysis'
            }
            
            # Store results in storage
            storage_manager.store_trusted_contacts(user_id, [
                {
                    'email': f'contact{i}@example.com',
                    'name': f'Contact {i}',
                    'trust_tier': 'tier_1' if i < 12 else 'tier_2' if i < 30 else 'tier_3',
                    'frequency': 10 - (i % 10),
                    'domain': f'example{i%5}.com'
                }
                for i in range(45)
            ])
            
            tracker.set_output(contacts_data)
            tracker.add_metric('extraction_efficiency', 0.89)
            tracker.add_metric('data_quality_score', 0.92)
            
            pipeline_results['contacts'] = contacts_data
        
        # STEP 2: Enrich Contacts with Logging
        with StepTracker(
            pipeline_id=pipeline_id,
            step_name="enrich_contacts",
            input_data=contacts_data,
            dependencies=["extract_contacts"],
            tags=["enrichment", "external_data"]
        ) as tracker:
            
            logger.info("Step 2: Enriching contacts with logging")
            
            # Simulate enrichment processing
            time.sleep(1.5)
            
            enrichment_data = {
                'contacts_enriched': 38,
                'success_rate': 0.84,
                'enrichment_sources': ['email_signatures', 'domain_intelligence', 'linkedin'],
                'avg_confidence_score': 0.78
            }
            
            tracker.set_output(enrichment_data)
            tracker.add_metric('api_calls_made', 114)
            tracker.add_metric('cache_hit_rate', 0.23)
            tracker.add_metric('enrichment_cost_usd', 2.34)
            
            pipeline_results['enrichment'] = enrichment_data
        
        # STEP 3: Build Knowledge Tree with Logging
        with StepTracker(
            pipeline_id=pipeline_id,
            step_name="build_knowledge_tree",
            input_data={
                'contacts': contacts_data,
                'enriched_data': enrichment_data,
                'analysis_depth': 'comprehensive'
            },
            dependencies=["extract_contacts", "enrich_contacts"],
            tags=["ai_processing", "knowledge_synthesis"]
        ) as tracker:
            
            logger.info("Step 3: Building knowledge tree with logging")
            
            # Simulate knowledge tree building
            time.sleep(2.0)
            
            knowledge_tree_data = {
                'tree_nodes': 156,
                'relationships_mapped': 234,
                'business_domains': 12,
                'strategic_insights': 18,
                'tree_depth': 4,
                'analysis_confidence': 0.86
            }
            
            # Store knowledge tree
            storage_manager.store_knowledge_tree(
                user_id=user_id,
                tree_data=knowledge_tree_data,
                analysis_type="logged_comprehensive"
            )
            
            tracker.set_output(knowledge_tree_data)
            tracker.add_metric('ai_processing_tokens', 45678)
            tracker.add_metric('knowledge_complexity_score', 0.74)
            tracker.add_metric('synthesis_accuracy', 0.91)
            
            pipeline_results['knowledge_tree'] = knowledge_tree_data
        
        # STEP 4: Generate Strategic Intelligence with Logging
        with StepTracker(
            pipeline_id=pipeline_id,
            step_name="generate_strategic_intelligence",
            input_data=knowledge_tree_data,
            dependencies=["build_knowledge_tree"],
            tags=["ai_analysis", "strategic_output"]
        ) as tracker:
            
            logger.info("Step 4: Generating strategic intelligence with logging")
            
            # Simulate intelligence generation
            time.sleep(1.8)
            
            intelligence_data = {
                'intelligence_reports': 3,
                'action_items': 14,
                'strategic_recommendations': 8,
                'risk_assessments': 5,
                'opportunity_matrix': {
                    'high_impact': 6,
                    'medium_impact': 9,
                    'low_impact': 12
                }
            }
            
            tracker.set_output(intelligence_data)
            tracker.add_metric('analysis_depth', 'comprehensive')
            tracker.add_metric('strategic_value_score', 0.88)
            tracker.add_metric('actionability_score', 0.82)
            
            pipeline_results['intelligence'] = intelligence_data
        
        # Complete pipeline with global metrics
        global_metrics = {
            'total_contacts_processed': 45,
            'total_enrichments': 38,
            'knowledge_nodes_created': 156,
            'intelligence_outputs': 3,
            'overall_quality_score': 0.87,
            'processing_efficiency': 0.84,
            'cost_effectiveness': 0.91
        }
        
        step_logger.complete_pipeline(
            pipeline_id=pipeline_id,
            status="completed",
            global_metrics=global_metrics
        )
        
        logger.info("Logged intelligence pipeline completed successfully", 
                   pipeline_id=pipeline_id, global_metrics=global_metrics)
        
        return jsonify({
            'success': True,
            'pipeline_id': pipeline_id,
            'message': 'Full intelligence pipeline completed with comprehensive logging',
            'results': pipeline_results,
            'global_metrics': global_metrics,
            'logging_features': {
                'step_tracking': 'enabled',
                'performance_monitoring': 'active',
                'data_sampling': f'{step_logger.sampling_rate*100:.1f}%',
                'analysis_available': True
            },
            'next_steps': [
                'View performance analysis at /api/logging/performance-report',
                'Check step details at /api/logging/recent-completions',
                'Get bottleneck analysis at /api/logging/bottlenecks'
            ]
        })
        
    except Exception as e:
        # Log pipeline failure
        if 'pipeline_id' in locals():
            step_logger.complete_pipeline(pipeline_id, status="failed", 
                                        global_metrics={'error': str(e)})
        
        logger.error("Logged intelligence pipeline failed", error=str(e))
        return jsonify({
            'success': False,
            'error': str(e),
            'pipeline_id': locals().get('pipeline_id'),
            'note': 'Check /api/logging/status for pipeline details'
        }), 500

@intelligence_logging_bp.route('/individual-step', methods=['POST'])
@require_auth
def run_individual_step_with_logging():
    """Run a single intelligence step with detailed logging"""
    try:
        user_email = session.get('user_id', 'demo@session-42.com')
        
        # Get request parameters
        data = request.get_json() or {}
        step_name = data.get('step_name', 'extract_contacts')
        input_data = data.get('input_data', {})
        
        # Start a single-step pipeline
        pipeline_id = step_logger.start_pipeline(
            user_id=user_email,
            pipeline_type=f"individual_{step_name}",
            session_id=session.get('session_id', f"session_{int(time.time())}")
        )
        
        # Run the requested step with logging
        with StepTracker(
            pipeline_id=pipeline_id,
            step_name=step_name,
            input_data=input_data,
            tags=["individual", "on_demand"]
        ) as tracker:
            
            # Simulate step processing based on step type
            if step_name == 'extract_contacts':
                time.sleep(1.2)
                output_data = {
                    'contacts_found': 23,
                    'processing_method': 'gmail_api',
                    'quality_score': 0.85
                }
                tracker.add_metric('api_calls', 45)
                
            elif step_name == 'enrich_contacts':
                time.sleep(2.1)
                output_data = {
                    'enriched_contacts': 18,
                    'success_rate': 0.78,
                    'data_sources_used': 3
                }
                tracker.add_metric('external_api_cost', 1.23)
                
            elif step_name == 'build_knowledge_tree':
                time.sleep(3.5)
                output_data = {
                    'tree_nodes': 67,
                    'relationships': 89,
                    'insights_generated': 12
                }
                tracker.add_metric('ai_tokens_used', 23456)
                
            else:
                time.sleep(1.0)
                output_data = {
                    'generic_output': True,
                    'processing_time': 1.0
                }
            
            tracker.set_output(output_data)
            tracker.add_metric('step_complexity', len(str(input_data)))
        
        # Complete single-step pipeline
        step_logger.complete_pipeline(
            pipeline_id=pipeline_id,
            status="completed",
            global_metrics={
                'single_step_mode': True,
                'step_executed': step_name
            }
        )
        
        return jsonify({
            'success': True,
            'pipeline_id': pipeline_id,
            'step_name': step_name,
            'output_data': output_data,
            'message': f'Individual step "{step_name}" completed with logging',
            'analysis_tip': f'View step analysis at /api/logging/step-analysis/{step_name}'
        })
        
    except Exception as e:
        logger.error("Individual step with logging failed", error=str(e), step_name=step_name)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@intelligence_logging_bp.route('/benchmark-performance', methods=['POST'])
@require_auth
def benchmark_step_performance():
    """Run performance benchmarks for different steps"""
    try:
        user_email = session.get('user_id', 'demo@session-42.com')
        
        # Get request parameters
        data = request.get_json() or {}
        iterations = data.get('iterations', 5)
        step_name = data.get('step_name', 'extract_contacts')
        
        benchmark_results = []
        
        for i in range(iterations):
            # Start benchmark pipeline
            pipeline_id = step_logger.start_pipeline(
                user_id=user_email,
                pipeline_type=f"benchmark_{step_name}",
                session_id=f"benchmark_{int(time.time())}_{i}"
            )
            
            # Run benchmark step
            with StepTracker(
                pipeline_id=pipeline_id,
                step_name=step_name,
                input_data={"benchmark_iteration": i, "total_iterations": iterations},
                tags=["benchmark", "performance_test"]
            ) as tracker:
                
                # Simulate variable processing times
                import random
                base_time = {'extract_contacts': 1.0, 'enrich_contacts': 2.0, 
                           'build_knowledge_tree': 3.0}.get(step_name, 1.5)
                actual_time = base_time + random.uniform(-0.3, 0.7)
                time.sleep(actual_time)
                
                output_data = {
                    'benchmark_iteration': i,
                    'simulated_processing_time': actual_time,
                    'performance_score': random.uniform(0.7, 0.95)
                }
                
                tracker.set_output(output_data)
                tracker.add_metric('benchmark_mode', True)
                tracker.add_metric('iteration_number', i)
                
                benchmark_results.append({
                    'iteration': i,
                    'duration_ms': actual_time * 1000,
                    'pipeline_id': pipeline_id
                })
            
            # Complete benchmark pipeline
            step_logger.complete_pipeline(
                pipeline_id=pipeline_id,
                status="completed",
                global_metrics={'benchmark_iteration': i}
            )
        
        # Calculate benchmark statistics
        durations = [r['duration_ms'] for r in benchmark_results]
        benchmark_stats = {
            'step_name': step_name,
            'iterations': iterations,
            'avg_duration_ms': sum(durations) / len(durations),
            'min_duration_ms': min(durations),
            'max_duration_ms': max(durations),
            'std_deviation': (sum((d - sum(durations)/len(durations))**2 for d in durations) / len(durations))**0.5,
            'performance_consistency': 1.0 - ((max(durations) - min(durations)) / sum(durations) * len(durations))
        }
        
        return jsonify({
            'success': True,
            'benchmark_results': benchmark_results,
            'benchmark_statistics': benchmark_stats,
            'message': f'Performance benchmark for "{step_name}" completed',
            'analysis_note': 'Check /api/logging/performance-report to see aggregated performance data'
        })
        
    except Exception as e:
        logger.error("Performance benchmark failed", error=str(e))
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500 