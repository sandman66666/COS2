"""
System Routes
=============
System utilities and testing endpoints
"""

import asyncio
import random
from datetime import datetime
from flask import Blueprint, request, jsonify
from utils.db import get_db_connection
from utils.auth import require_auth
from utils.logging import structured_logger as logger
import os

# Import the services we'll test
from intelligence.d_enrichment.contact_enrichment_service import ContactEnrichmentService
from intelligence.f_knowledge_integration.knowledge_tree_orchestrator import KnowledgeTreeOrchestrator
from intelligence.e_strategic_analysis.strategic_analyzer import StrategicAnalyzer

system_bp = Blueprint('system', __name__)

@system_bp.route('/sanity-fast-test', methods=['POST'])
@require_auth
def sanity_fast_test():
    """
    Sanity Fast Test - End-to-End Pipeline Test with 2 Contacts
    
    This test:
    1. Gets 2 contacts from database
    2. Fetches emails related to those contacts
    3. Augments/enriches the 2 contacts
    4. Builds knowledge tree
    5. Runs strategic intelligence analysis
    
    Returns comprehensive test results
    """
    async def _run_sanity_test():
        try:
            user_id = request.user_id
            user_email = request.user_email
            
            logger.info(f"🧪 Starting Sanity Fast Test for user {user_email}")
            
            start_time = datetime.utcnow()
            test_results = {
                'success': True,
                'user_id': user_id,
                'user_email': user_email,
                'start_time': start_time.isoformat(),
                'steps_completed': [],
                'test_data': {},
                'performance_metrics': {},
                'errors': []
            }
            
            # STEP 1: Get 2 sample contacts from database
            logger.info("🧪 Step 1: Getting sample contacts from database")
            step1_start = datetime.utcnow()
            
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    # Get 2 contacts with highest frequency for better test data
                    cursor.execute("""
                        SELECT id, email, domain, frequency, name, trust_tier, metadata
                        FROM contacts 
                        WHERE user_id = %s 
                        ORDER BY frequency DESC 
                        LIMIT 2
                    """, [user_id])
                    
                    sample_contacts = []
                    for row in cursor.fetchall():
                        contact = {
                            'id': row[0],
                            'email': row[1],
                            'domain': row[2],
                            'frequency': row[3],
                            'name': row[4] or '',
                            'trust_tier': row[5],
                            'metadata': row[6] or {}
                        }
                        sample_contacts.append(contact)
            
            if len(sample_contacts) < 2:
                return {
                    'success': False,
                    'error': f'Insufficient contacts for test. Found {len(sample_contacts)}, need at least 2.',
                    'suggestion': 'Run "Sync Emails" and "Extract Contacts" steps first to populate contacts.'
                }, 400
            
            step1_duration = (datetime.utcnow() - step1_start).total_seconds()
            test_results['steps_completed'].append('get_contacts')
            test_results['test_data']['sample_contacts'] = sample_contacts
            test_results['performance_metrics']['step1_contacts_duration'] = step1_duration
            
            logger.info(f"✅ Step 1 complete: Found {len(sample_contacts)} contacts in {step1_duration:.2f}s")
            
            # STEP 2: Get sample emails related to these contacts
            logger.info("🧪 Step 2: Getting sample emails related to contacts")
            step2_start = datetime.utcnow()
            
            sample_emails = []
            contact_emails = [contact['email'] for contact in sample_contacts]
            
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    # Get emails from/to these contacts
                    for contact_email in contact_emails:
                        cursor.execute("""
                            SELECT id, subject, sender_email, recipient_emails, metadata, date_received
                            FROM emails 
                            WHERE user_id = %s 
                            AND (sender_email = %s OR recipient_emails LIKE %s)
                            ORDER BY date_received DESC
                            LIMIT 2
                        """, [user_id, contact_email, f'%{contact_email}%'])
                        
                        for row in cursor.fetchall():
                            email = {
                                'id': row[0],
                                'subject': row[1],
                                'sender_email': row[2],
                                'recipient_emails': row[3],
                                'metadata': row[4] or {},
                                'date_received': row[5].isoformat() if row[5] else None
                            }
                            sample_emails.append(email)
            
            step2_duration = (datetime.utcnow() - step2_start).total_seconds()
            test_results['steps_completed'].append('get_emails')
            test_results['test_data']['sample_emails'] = sample_emails
            test_results['performance_metrics']['step2_emails_duration'] = step2_duration
            
            logger.info(f"✅ Step 2 complete: Found {len(sample_emails)} related emails in {step2_duration:.2f}s")
            
            # STEP 3: Run contact enrichment on the 2 contacts
            logger.info("🧪 Step 3: Running contact enrichment/augmentation")
            step3_start = datetime.utcnow()
            
            try:
                # Initialize enrichment service
                enrichment_service = ContactEnrichmentService(
                    user_id=user_id,
                    storage_manager=None,  # Use default database connection
                    claude_api_key=os.getenv('ANTHROPIC_API_KEY')  # Get from env
                )
                
                # Initialize the service
                await enrichment_service.initialize()
                
                # Run enrichment on the 2 contacts
                enrichment_results = await enrichment_service.enrich_contacts_batch(
                    contacts=sample_contacts,
                    user_emails=sample_emails
                )
                
                step3_duration = (datetime.utcnow() - step3_start).total_seconds()
                test_results['steps_completed'].append('augment_contacts')
                test_results['test_data']['enrichment_results'] = {
                    'total_processed': enrichment_results.get('total_processed', 0),
                    'successful_count': enrichment_results.get('successful_count', 0),
                    'failed_count': enrichment_results.get('failed_count', 0),
                    'success_rate': enrichment_results.get('success_rate', 0),
                    'enriched_contacts': enrichment_results.get('enriched_contacts', [])[:2]  # Limit output
                }
                test_results['performance_metrics']['step3_enrichment_duration'] = step3_duration
                
                logger.info(f"✅ Step 3 complete: Enriched {enrichment_results.get('successful_count', 0)}/{len(sample_contacts)} contacts in {step3_duration:.2f}s")
                
            except Exception as e:
                error_msg = f"Contact enrichment failed: {str(e)}"
                test_results['errors'].append(error_msg)
                logger.error(f"❌ Step 3 failed: {error_msg}")
            
            # STEP 4: Build knowledge tree
            logger.info("🧪 Step 4: Building knowledge tree")
            step4_start = datetime.utcnow()
            
            try:
                # Initialize knowledge tree orchestrator
                knowledge_orchestrator = KnowledgeTreeOrchestrator(user_id)
                
                # Build knowledge tree with our test data
                tree_result = await knowledge_orchestrator.build_comprehensive_tree(
                    contacts=sample_contacts,
                    emails=sample_emails,
                    limit_nodes=10  # Limit for fast test
                )
                
                step4_duration = (datetime.utcnow() - step4_start).total_seconds()
                test_results['steps_completed'].append('build_knowledge_tree')
                test_results['test_data']['knowledge_tree'] = {
                    'success': tree_result.get('success', False),
                    'nodes_created': tree_result.get('nodes_created', 0),
                    'relationships_mapped': tree_result.get('relationships_mapped', 0),
                    'tree_summary': tree_result.get('tree_summary', '')
                }
                test_results['performance_metrics']['step4_tree_duration'] = step4_duration
                
                logger.info(f"✅ Step 4 complete: Built knowledge tree with {tree_result.get('nodes_created', 0)} nodes in {step4_duration:.2f}s")
                
            except Exception as e:
                error_msg = f"Knowledge tree building failed: {str(e)}"
                test_results['errors'].append(error_msg)
                logger.error(f"❌ Step 4 failed: {error_msg}")
            
            # STEP 5: Run strategic intelligence analysis
            logger.info("🧪 Step 5: Running strategic intelligence analysis")
            step5_start = datetime.utcnow()
            
            try:
                # Initialize strategic analyzer
                strategic_analyzer = StrategicAnalyzer(user_id)
                
                # Run strategic analysis on our test data
                analysis_result = await strategic_analyzer.generate_comprehensive_analysis(
                    contacts=sample_contacts,
                    emails=sample_emails,
                    limit_insights=5  # Limit for fast test
                )
                
                step5_duration = (datetime.utcnow() - step5_start).total_seconds()
                test_results['steps_completed'].append('strategic_analysis')
                test_results['test_data']['strategic_analysis'] = {
                    'success': analysis_result.get('success', False),
                    'insights_generated': analysis_result.get('insights_generated', 0),
                    'strategic_recommendations': analysis_result.get('strategic_recommendations', [])[:3],  # Limit output
                    'analysis_summary': analysis_result.get('analysis_summary', '')
                }
                test_results['performance_metrics']['step5_analysis_duration'] = step5_duration
                
                logger.info(f"✅ Step 5 complete: Generated {analysis_result.get('insights_generated', 0)} insights in {step5_duration:.2f}s")
                
            except Exception as e:
                error_msg = f"Strategic analysis failed: {str(e)}"
                test_results['errors'].append(error_msg)
                logger.error(f"❌ Step 5 failed: {error_msg}")
            
            # Calculate total test duration
            total_duration = (datetime.utcnow() - start_time).total_seconds()
            test_results['end_time'] = datetime.utcnow().isoformat()
            test_results['total_duration'] = total_duration
            test_results['performance_metrics']['total_test_duration'] = total_duration
            
            # Generate summary
            steps_completed = len(test_results['steps_completed'])
            total_steps = 5
            success_rate = (steps_completed / total_steps) * 100
            
            test_results['summary'] = f"Completed {steps_completed}/{total_steps} steps ({success_rate:.0f}%) in {total_duration:.1f}s"
            
            if test_results['errors']:
                test_results['summary'] += f" with {len(test_results['errors'])} errors"
                test_results['success'] = False
            
            logger.info(f"🧪 Sanity Fast Test complete: {test_results['summary']}")
            
            return test_results, 200
            
        except Exception as e:
            logger.error(f"🧪 Sanity Fast Test failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'test_incomplete': True
            }, 500
    
    # Run the async function in sync context
    try:
        result, status_code = asyncio.run(_run_sanity_test())
        return jsonify(result), status_code
    except Exception as e:
        logger.error(f"🧪 Sanity Fast Test wrapper failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Test execution failed: {str(e)}',
            'test_incomplete': True
        }), 500

@system_bp.route('/flush', methods=['POST'])
@require_auth
def flush_database():
    """
    Flush all user data from database
    """
    try:
        user_id = request.user_id
        
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Delete user data in correct order to avoid foreign key constraints
                tables = ['contacts', 'emails', 'knowledge_nodes', 'strategic_insights']
                
                for table in tables:
                    cursor.execute(f"DELETE FROM {table} WHERE user_id = %s", [user_id])
                
                conn.commit()
        
        logger.info(f"🗑️ Database flushed for user {request.user_email}")
        
        return jsonify({
            'success': True,
            'message': 'Database flushed successfully'
        })
        
    except Exception as e:
        logger.error(f"Database flush failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500 