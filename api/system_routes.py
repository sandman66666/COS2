"""
System Routes
=============
System utilities and testing endpoints
"""

import asyncio
import random
from datetime import datetime
from flask import Blueprint, request, jsonify, session
from middleware.auth_middleware import require_auth
from utils.logging import structured_logger as logger
import os

# Import the services we'll test
from intelligence.d_enrichment.contact_enrichment_service import ContactEnrichmentService
from intelligence.f_knowledge_integration.knowledge_tree_orchestrator import KnowledgeTreeOrchestrator
from intelligence.e_strategic_analysis.strategic_analyzer import StrategicAnalysisSystem
from storage.storage_manager_sync import get_storage_manager_sync

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
            user_email = session.get('user_id', 'test@session-42.com')  # Session stores email in 'user_id'
            
            logger.info(f"🧪 Starting Sanity Fast Test for user {user_email}")
            
            start_time = datetime.utcnow()
            test_results = {
                'success': True,
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
            
            storage_manager = get_storage_manager_sync()
            
            # Get user by email
            user = storage_manager.get_user_by_email(user_email)
            if not user:
                return {
                    'success': False,
                    'error': f'User not found: {user_email}',
                    'suggestion': 'Please authenticate and run other pipeline steps first.'
                }, 400
                
            user_id = user['id']
            test_results['user_id'] = user_id
            
            # Get 2 contacts with highest frequency for better test data
            contacts, total = storage_manager.get_contacts(user_id, limit=2)
            
            sample_contacts = []
            for contact in contacts[:2]:  # Ensure we only get 2
                contact_data = {
                    'id': contact['id'],
                    'email': contact['email'],
                    'domain': contact.get('domain', ''),
                    'frequency': contact.get('frequency', 0),
                    'name': contact.get('name', ''),
                    'trust_tier': contact.get('trust_tier', 'tier_3'),
                    'metadata': contact.get('metadata', {})
                }
                sample_contacts.append(contact_data)
            
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
            
            # Get emails from storage manager
            emails, email_total = storage_manager.postgres.get_emails(user_id, limit=10)
            
            sample_emails = []
            contact_emails = [contact['email'] for contact in sample_contacts]
            
            # Filter emails related to our test contacts
            for email in emails:
                try:
                    metadata = email.get('metadata', {})
                    if isinstance(metadata, str):
                        import json
                        metadata = json.loads(metadata)
                    
                    sender = metadata.get('from', '')
                    recipients = metadata.get('to', [])
                    
                    # Check if email is from/to any of our test contacts
                    is_related = False
                    for contact_email in contact_emails:
                        if (contact_email in sender or 
                            any(contact_email in str(recipient) for recipient in recipients)):
                            is_related = True
                            break
                    
                    if is_related or len(sample_emails) < 2:  # Include at least 2 emails
                        email_data = {
                            'id': email['id'],
                            'subject': metadata.get('subject', 'No Subject'),
                            'sender_email': metadata.get('from', ''),
                            'recipient_emails': ', '.join(recipients) if recipients else '',
                            'metadata': metadata,
                            'date_received': email.get('created_at', '').isoformat() if email.get('created_at') else None
                        }
                        sample_emails.append(email_data)
                        
                        if len(sample_emails) >= 4:  # Limit to 4 emails for fast test
                            break
                            
                except Exception as e:
                    logger.warning(f"Error processing email {email.get('id')}: {e}")
                    continue
            
            step2_duration = (datetime.utcnow() - step2_start).total_seconds()
            test_results['steps_completed'].append('get_emails')
            test_results['test_data']['sample_emails'] = sample_emails
            test_results['performance_metrics']['step2_emails_duration'] = step2_duration
            
            logger.info(f"✅ Step 2 complete: Found {len(sample_emails)} related emails in {step2_duration:.2f}s")
            
            # STEP 3: Run contact enrichment (lightweight mode for speed)
            logger.info("🧪 Step 3: Running contact enrichment/augmentation")
            step3_start = datetime.utcnow()
            
            try:
                # Initialize enrichment service and run actual enrichment
                enrichment_service = ContactEnrichmentService(user_id)
                
                # Run enrichment with timeout
                enrichment_results = await asyncio.wait_for(
                    enrichment_service.enrich_contacts_batch(
                        contacts=sample_contacts,
                        user_emails=sample_emails
                    ),
                    timeout=8.0  # 8 second timeout for enrichment
                )
                        
                step3_duration = (datetime.utcnow() - step3_start).total_seconds()
                test_results['steps_completed'].append('augment_contacts')
                test_results['test_data']['enrichment_results'] = {
                    'total_processed': enrichment_results.get('total_processed', 0),
                    'successful_count': enrichment_results.get('successful_count', 0),
                    'failed_count': enrichment_results.get('failed_count', 0),
                    'success_rate': enrichment_results.get('success_rate', 0.0),
                    'sample_enriched': str(enrichment_results)[:300] if enrichment_results else "No results"
                }
                test_results['performance_metrics']['step3_enrichment_duration'] = step3_duration
                
                logger.info(f"✅ Step 3 complete: Enriched {enrichment_results.get('successful_count', 0)}/{enrichment_results.get('total_processed', 0)} contacts in {step3_duration:.2f}s")
                
            except asyncio.TimeoutError:
                step3_duration = (datetime.utcnow() - step3_start).total_seconds()
                test_results['errors'].append('Contact enrichment timeout after 8s - normal for fast test')
                logger.info("⏰ Step 3 timeout: Normal for fast test")
                
            except Exception as e:
                step3_duration = (datetime.utcnow() - step3_start).total_seconds()
                test_results['errors'].append(f"Contact enrichment failed: {str(e)}")
                logger.error(f"❌ Step 3 failed: {str(e)}")
            
            # STEP 4: Build knowledge tree (minimal nodes for speed)
            logger.info("🧪 Step 4: Building knowledge tree (minimal for speed)")
            step4_start = datetime.utcnow()
            
            try:
                # Initialize knowledge tree orchestrator with API key, not user_id
                claude_api_key = os.getenv('ANTHROPIC_API_KEY')
                if not claude_api_key:
                    raise Exception("ANTHROPIC_API_KEY not found in environment")
                    
                knowledge_orchestrator = KnowledgeTreeOrchestrator(claude_api_key)
                
                # Get user email for knowledge tree
                user_email = session.get('user_id', 'test@session-42.com')
                
                # Quick knowledge tree with timeout - using correct parameters
                tree_result = await asyncio.wait_for(
                    knowledge_orchestrator.build_complete_knowledge_tree(
                        user_email=user_email
                        # Note: force_rebuild defaults to False for fast test
                    ),
                    timeout=6.0  # 6 second timeout
                )
                
                step4_duration = (datetime.utcnow() - step4_start).total_seconds()
                test_results['steps_completed'].append('build_knowledge_tree')
                test_results['test_data']['knowledge_tree'] = {
                    'success': tree_result.get('success', False) if tree_result else False,
                    'nodes_created': len(tree_result.get('knowledge_tree', {}).get('topics', {})) if tree_result else 0,
                    'tree_summary': str(tree_result)[:200] if tree_result else "Empty"
                }
                test_results['performance_metrics']['step4_tree_duration'] = step4_duration
                
                logger.info(f"✅ Step 4 complete: Built knowledge tree in {step4_duration:.2f}s")
                
            except asyncio.TimeoutError:
                step4_duration = (datetime.utcnow() - step4_start).total_seconds()
                test_results['errors'].append('Knowledge tree timeout after 6s - normal for fast test')
                logger.info("⏰ Step 4 timeout: Normal for fast test")
                
            except Exception as e:
                step4_duration = (datetime.utcnow() - step4_start).total_seconds()
                test_results['errors'].append(f"Knowledge tree building failed: {str(e)}")
                logger.error(f"❌ Step 4 failed: {str(e)}")
            
            # STEP 5: Generate strategic intelligence (quick analysis)
            logger.info("🧪 Step 5: Running strategic intelligence analysis (quick)")
            step5_start = datetime.utcnow()
            
            try:
                # Initialize strategic analyzer with API key, not user_id
                claude_api_key = os.getenv('ANTHROPIC_API_KEY')
                if not claude_api_key:
                    raise Exception("ANTHROPIC_API_KEY not found in environment")
                    
                strategic_analyzer = StrategicAnalysisSystem(claude_api_key)
                
                # Create minimal context for strategic analysis
                minimal_context = {
                    'established_contacts': [],
                    'attempted_contacts': [],
                    'high_priority_topics': [],
                    'all_topics': [],
                    'all_contacts': [],
                    'business_domains': {},
                    'total_contacts': len(sample_contacts),
                    'engagement_rate': 0.5
                }
                
                # Quick strategic analysis using analyze_strategic_intelligence_from_tree with timeout
                analysis_result = await asyncio.wait_for(
                    strategic_analyzer.analyze_strategic_intelligence_from_tree(
                        user_id=user_id,
                        knowledge_tree=None,  # Minimal knowledge tree for test
                        tree_context=minimal_context
                    ),
                    timeout=5.0  # 5 second timeout
                )
                
                step5_duration = (datetime.utcnow() - step5_start).total_seconds()
                test_results['steps_completed'].append('strategic_analysis')
                test_results['test_data']['strategic_analysis'] = {
                    'success': bool(analysis_result) if analysis_result else False,
                    'insights_generated': analysis_result.get('total_insights', 0) if analysis_result else 0,
                    'analysis_summary': str(analysis_result)[:300] if analysis_result else "No analysis"
                }
                test_results['performance_metrics']['step5_analysis_duration'] = step5_duration
                
                logger.info(f"✅ Step 5 complete: Strategic analysis in {step5_duration:.2f}s")
                
            except asyncio.TimeoutError:
                step5_duration = (datetime.utcnow() - step5_start).total_seconds()
                test_results['errors'].append('Strategic analysis timeout after 5s - normal for fast test')
                logger.info("⏰ Step 5 timeout: Normal for fast test")
                
            except Exception as e:
                step5_duration = (datetime.utcnow() - step5_start).total_seconds()
                test_results['errors'].append(f"Strategic analysis failed: {str(e)}")
                logger.error(f"❌ Step 5 failed: {str(e)}")
            
            # Calculate total test duration
            total_duration = (datetime.utcnow() - start_time).total_seconds()
            test_results['end_time'] = datetime.utcnow().isoformat()
            test_results['total_duration'] = total_duration
            test_results['performance_metrics']['total_test_duration'] = total_duration
            
            # Generate comprehensive progress summary
            steps_completed = len(test_results['steps_completed'])
            total_steps = 5
            success_rate = (steps_completed / total_steps) * 100
            
            # Generate detailed step logs
            step_logs = []
            step_details = [
                {
                    'step': 1,
                    'name': 'Get Sample Contacts',
                    'description': 'Fetch 2 contacts from database with highest frequency',
                    'completed': 'get_contacts' in test_results['steps_completed'],
                    'duration': test_results['performance_metrics'].get('step1_contacts_duration', 0),
                    'result': f"Found {len(test_results['test_data'].get('sample_contacts', []))} contacts" if test_results['test_data'].get('sample_contacts') else "No contacts found"
                },
                {
                    'step': 2,
                    'name': 'Get Related Emails',
                    'description': 'Fetch emails from/to the sample contacts',
                    'completed': 'get_emails' in test_results['steps_completed'],
                    'duration': test_results['performance_metrics'].get('step2_emails_duration', 0),
                    'result': f"Found {len(test_results['test_data'].get('sample_emails', []))} related emails" if test_results['test_data'].get('sample_emails') else "No emails found"
                },
                {
                    'step': 3,
                    'name': 'Contact Enrichment',
                    'description': 'Run enterprise-grade contact augmentation with Claude 4 Opus',
                    'completed': 'augment_contacts' in test_results['steps_completed'],
                    'duration': test_results['performance_metrics'].get('step3_enrichment_duration', 0),
                    'result': f"Processed {test_results['test_data'].get('enrichment_results', {}).get('total_processed', 0)} contacts" if test_results['test_data'].get('enrichment_results') else "Enrichment timeout"
                },
                {
                    'step': 4,
                    'name': 'Knowledge Tree Building',
                    'description': 'Build comprehensive knowledge tree from email content',
                    'completed': 'build_knowledge_tree' in test_results['steps_completed'],
                    'duration': test_results['performance_metrics'].get('step4_tree_duration', 0),
                    'result': f"Created {test_results['test_data'].get('knowledge_tree', {}).get('nodes_created', 0)} knowledge nodes" if test_results['test_data'].get('knowledge_tree') else "Knowledge tree timeout"
                },
                {
                    'step': 5,
                    'name': 'Strategic Intelligence',
                    'description': 'Generate strategic insights and business opportunities',
                    'completed': 'strategic_analysis' in test_results['steps_completed'],
                    'duration': test_results['performance_metrics'].get('step5_analysis_duration', 0),
                    'result': f"Generated {test_results['test_data'].get('strategic_analysis', {}).get('insights_generated', 0)} strategic insights" if test_results['test_data'].get('strategic_analysis') else "Strategic analysis timeout"
                }
            ]
            
            # Create step logs with detailed information
            for step_detail in step_details:
                status = "✅ Completed" if step_detail['completed'] else ("⏰ Timeout" if step_detail['step'] > 2 else "❌ Failed")
                step_logs.append({
                    'step': step_detail['step'],
                    'name': step_detail['name'],
                    'description': step_detail['description'],
                    'status': status,
                    'duration': f"{step_detail['duration']:.2f}s",
                    'result': step_detail['result'],
                    'completed': step_detail['completed']
                })
            
            test_results['step_logs'] = step_logs
            test_results['summary'] = f"Completed {steps_completed}/{total_steps} steps ({success_rate:.0f}%) in {total_duration:.1f}s"
            
            # Add detailed recommendations
            if steps_completed == total_steps:
                test_results['recommendation'] = "🎉 All systems operational! Your intelligence pipeline is working perfectly."
                test_results['health_status'] = "excellent"
            elif steps_completed >= 3:
                test_results['recommendation'] = "✅ Core systems working well. Some advanced features may need optimization."
                test_results['health_status'] = "good"
            elif steps_completed >= 2:
                test_results['recommendation'] = "⚠️ Basic data retrieval working. Advanced intelligence features need attention."
                test_results['health_status'] = "fair"
            else:
                test_results['recommendation'] = "❌ Critical issues detected. Check authentication and database connectivity."
                test_results['health_status'] = "poor"
            
            if test_results['errors']:
                test_results['summary'] += f" with {len(test_results['errors'])} errors"
                test_results['success'] = len(test_results['errors']) == 0
            
            logger.info(f"🧪 Sanity Fast Test complete: {test_results['summary']}")
            
            return test_results
            
        except Exception as e:
            logger.error(f"🧪 Sanity Fast Test failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'test_incomplete': True
            }, 500
    
    # Run the async function in sync context with timeout protection
    try:
        # Add overall timeout to prevent Heroku timeout (30s limit)
        async def _run_with_timeout():
            return await asyncio.wait_for(_run_sanity_test(), timeout=20.0)
        
        result, status_code = asyncio.run(_run_with_timeout())
        return jsonify(result), status_code
        
    except asyncio.TimeoutError:
        logger.warning("🧪 Sanity Fast Test hit 20-second timeout - preventing Heroku timeout")
        return jsonify({
            'success': False,
            'error': 'Test timeout after 20 seconds',
            'message': 'Test was stopped to prevent Heroku timeout',
            'recommendation': 'This timeout indicates the system is working but needs optimization',
            'partial_results': 'Some steps may have completed - check logs for details'
        }), 200  # Return 200 so frontend gets the message
        
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
        user_email = session.get('user_id', 'test@session-42.com')  # Session stores email in 'user_id'
        
        storage_manager = get_storage_manager_sync()
        user = storage_manager.get_user_by_email(user_email)
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
            
        user_id = user['id']
        
        conn = storage_manager.postgres.conn_pool.getconn()
        try:
            cursor = conn.cursor()
            
            # Delete user data in correct order to avoid foreign key constraints
            tables = ['contacts', 'emails', 'knowledge_tree', 'oauth_credentials']
            
            deleted_counts = {}
            for table in tables:
                cursor.execute(f"DELETE FROM {table} WHERE user_id = %s", [user_id])
                deleted_counts[table] = cursor.rowcount
            
            conn.commit()
            
        finally:
            storage_manager.postgres.conn_pool.putconn(conn)
        
        logger.info(f"🗑️ Database flushed for user {user_email}")
        
        return jsonify({
            'success': True,
            'message': 'Database flushed successfully',
            'deleted_counts': deleted_counts,
            'user_id': user_id
        })
        
    except Exception as e:
        logger.error(f"Database flush failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500 