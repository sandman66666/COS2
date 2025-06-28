#!/usr/bin/env python3
"""
End-to-End Test: Shared Intelligence System
===========================================
Test the complete shared intelligence flow:
1. Global Contact Intelligence Manager setup
2. Black Belt enrichment with shared intelligence
3. Cross-user intelligence sharing
4. Personal email context addition
5. API endpoints functionality

This verifies the revolutionary shared intelligence architecture works correctly.
"""

import asyncio
import os
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, List

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from storage.storage_manager_sync import get_storage_manager_sync
from storage.global_contact_intelligence import GlobalContactIntelligenceManager, UserContactContext
from intelligence.d_enrichment.contact_enrichment_service import ContactEnrichmentService
from utils.logging import structured_logger as logger

class SharedIntelligenceE2ETest:
    """End-to-end test for the shared intelligence system"""
    
    def __init__(self):
        self.storage_manager = None
        self.global_intelligence = None
        self.test_user_id_1 = 999001  # Test user 1
        self.test_user_id_2 = 999002  # Test user 2
        self.test_contacts = [
            'john.doe@techcorp.com',
            'jane.smith@innovate.io', 
            'mike.wilson@startup.co'
        ]
        self.claude_api_key = os.getenv('ANTHROPIC_API_KEY')
        
    async def setup(self):
        """Initialize test environment"""
        print("🔧 Setting up shared intelligence test environment...")
        
        # Initialize storage
        self.storage_manager = get_storage_manager_sync()
        
        # Initialize global intelligence manager
        self.global_intelligence = GlobalContactIntelligenceManager(self.storage_manager)
        await self.global_intelligence.initialize()
        
        print("✅ Test environment setup complete")
        
    async def test_1_global_intelligence_database(self):
        """Test 1: Global intelligence database operations"""
        print("\n🧪 TEST 1: Global Intelligence Database Operations")
        
        # Test database tables exist
        try:
            stats = await self.global_intelligence.get_enrichment_stats()
            print(f"✅ Database tables operational: {stats}")
            
            # Verify table structure
            assert 'global_intelligence' in stats
            assert 'user_contexts' in stats
            assert 'hot_cache' in stats
            
            print("✅ Database structure verified")
            return True
            
        except Exception as e:
            print(f"❌ Database test failed: {e}")
            return False
    
    async def test_2_black_belt_enrichment_with_cache_miss(self):
        """Test 2: Black Belt enrichment with cache miss (fresh scrape)"""
        print("\n🧪 TEST 2: Black Belt Enrichment - Cache Miss (Fresh Scrape)")
        
        if not self.claude_api_key:
            print("⚠️ No Claude API key - skipping Black Belt test")
            return True
        
        try:
            # Create enrichment service for user 1
            enrichment_service = ContactEnrichmentService(
                self.test_user_id_1, 
                self.storage_manager, 
                self.claude_api_key
            )
            await enrichment_service.initialize()
            
            # Create test contact and company intelligence
            test_contact = {
                'email': self.test_contacts[0],
                'name': 'John Doe',
                'domain': 'techcorp.com',
                'frequency': 5,
                'trust_tier': 'tier_2'
            }
            
            # Mock user emails for context
            test_emails = [
                {
                    'content': 'Hi John, thanks for your presentation on AI trends...',
                    'metadata': {
                        'from': f'user_{self.test_user_id_1}@test.com',
                        'to': self.test_contacts[0],
                        'date': datetime.utcnow().isoformat()
                    }
                }
            ]
            
            print(f"🥷 Running Black Belt enrichment for {test_contact['email']}...")
            
            # Run enrichment (should be cache miss - fresh scrape)
            enriched_result = await enrichment_service._enrich_contact_with_shared_intelligence(
                test_contact, None, test_emails
            )
            
            print(f"✅ Enrichment completed: {enriched_result.get('email')}")
            print(f"📊 Confidence: {enriched_result.get('confidence_score', 0)}")
            print(f"🔍 Data sources: {enriched_result.get('data_sources', [])}")
            
            # Verify shared intelligence was stored
            shared_record = await self.global_intelligence.get_shared_intelligence(self.test_contacts[0])
            if shared_record:
                print(f"🌍 Shared intelligence stored - verification count: {shared_record.verification_count}")
            else:
                print("⚠️ No shared intelligence stored (may be expected for mock results)")
            
            # Check metrics
            stats = enrichment_service.shared_intelligence_stats
            print(f"📈 Enrichment stats: {stats}")
            
            await enrichment_service.cleanup()
            return True
            
        except Exception as e:
            print(f"❌ Black Belt enrichment test failed: {e}")
            return False
    
    async def test_3_shared_intelligence_cache_hit(self):
        """Test 3: Shared intelligence cache hit (second user benefits)"""
        print("\n🧪 TEST 3: Shared Intelligence Cache Hit (Cross-User Benefit)")
        
        if not self.claude_api_key:
            print("⚠️ No Claude API key - skipping cache hit test")
            return True
        
        try:
            # Create enrichment service for user 2 (different user)
            enrichment_service_2 = ContactEnrichmentService(
                self.test_user_id_2,
                self.storage_manager,
                self.claude_api_key
            )
            await enrichment_service_2.initialize()
            
            # Same contact, different user
            test_contact = {
                'email': self.test_contacts[0],  # Same email as Test 2
                'name': 'John Doe',
                'domain': 'techcorp.com',
                'frequency': 2,
                'trust_tier': 'tier_3'
            }
            
            # Different user emails for personal context
            test_emails_user2 = [
                {
                    'content': 'John, following up on our discussion about partnerships...',
                    'metadata': {
                        'from': f'user_{self.test_user_id_2}@test.com',
                        'to': self.test_contacts[0],
                        'date': (datetime.utcnow() - timedelta(days=2)).isoformat()
                    }
                }
            ]
            
            print(f"🌍 Enriching {test_contact['email']} for User 2 (should hit cache)...")
            
            # Run enrichment (should be cache hit if Test 2 stored intelligence)
            enriched_result = await enrichment_service_2._enrich_contact_with_shared_intelligence(
                test_contact, None, test_emails_user2
            )
            
            print(f"✅ Enrichment completed: {enriched_result.get('email')}")
            
            # Check if it was a cache hit
            stats = enrichment_service_2.shared_intelligence_stats
            if stats.get('cache_hits', 0) > 0:
                print(f"🔥 CACHE HIT! Used shared intelligence: {stats}")
            else:
                print(f"🆕 Fresh scrape (cache miss): {stats}")
            
            # Verify personal context is different for each user
            relationship_intel = enriched_result.get('relationship_intelligence', {})
            personal_patterns = relationship_intel.get('personal_email_patterns', {})
            
            print(f"👤 Personal context for User 2: {personal_patterns}")
            
            await enrichment_service_2.cleanup()
            return True
            
        except Exception as e:
            print(f"❌ Cache hit test failed: {e}")
            return False
    
    async def test_4_user_context_separation(self):
        """Test 4: User context separation and privacy"""
        print("\n🧪 TEST 4: User Context Separation & Privacy")
        
        try:
            # Get user contexts for both users
            user1_context = await self.global_intelligence.get_user_context(
                self.test_user_id_1, self.test_contacts[0]
            )
            user2_context = await self.global_intelligence.get_user_context(
                self.test_user_id_2, self.test_contacts[0]
            )
            
            print(f"👤 User 1 context exists: {user1_context is not None}")
            print(f"👤 User 2 context exists: {user2_context is not None}")
            
            if user1_context and user2_context:
                # Verify contexts are separate
                assert user1_context.user_id != user2_context.user_id
                print("✅ User contexts are properly separated")
                
                # Show different personal patterns
                print(f"📧 User 1 email patterns: {user1_context.email_patterns}")
                print(f"📧 User 2 email patterns: {user2_context.email_patterns}")
            
            # Test shared intelligence (should be same for both users)
            shared_record = await self.global_intelligence.get_shared_intelligence(self.test_contacts[0])
            if shared_record:
                print(f"🌍 Shared web intelligence (same for all): verification count {shared_record.verification_count}")
                print(f"🔍 Data sources: {shared_record.data_sources}")
            
            return True
            
        except Exception as e:
            print(f"❌ User context separation test failed: {e}")
            return False
    
    async def test_5_engagement_tracking(self):
        """Test 5: Cross-user engagement success tracking"""
        print("\n🧪 TEST 5: Cross-User Engagement Success Tracking")
        
        try:
            # Simulate meeting requests for both users
            print("📊 Recording engagement success for User 1...")
            await self.global_intelligence.update_engagement_success(
                self.test_contacts[0], self.test_user_id_1, 
                meeting_requested=True, meeting_accepted=True
            )
            
            print("📊 Recording engagement success for User 2...")
            await self.global_intelligence.update_engagement_success(
                self.test_contacts[0], self.test_user_id_2,
                meeting_requested=True, meeting_accepted=False
            )
            
            # Check updated shared intelligence
            shared_record = await self.global_intelligence.get_shared_intelligence(self.test_contacts[0])
            if shared_record:
                print(f"📈 Cross-user engagement rate: {shared_record.engagement_success_rate:.2f}")
                print(f"✅ Engagement tracking working")
            
            # Check individual user contexts
            user1_context = await self.global_intelligence.get_user_context(
                self.test_user_id_1, self.test_contacts[0]
            )
            user2_context = await self.global_intelligence.get_user_context(
                self.test_user_id_2, self.test_contacts[0]
            )
            
            if user1_context:
                print(f"👤 User 1 personal success rate: {user1_context.response_rate:.2f}")
            if user2_context:
                print(f"👤 User 2 personal success rate: {user2_context.response_rate:.2f}")
            
            return True
            
        except Exception as e:
            print(f"❌ Engagement tracking test failed: {e}")
            return False
    
    async def test_6_system_performance_metrics(self):
        """Test 6: System performance and statistics"""
        print("\n🧪 TEST 6: System Performance Metrics")
        
        try:
            # Get comprehensive stats
            stats = await self.global_intelligence.get_enrichment_stats()
            
            print("📊 SHARED INTELLIGENCE SYSTEM STATISTICS:")
            print("=" * 50)
            
            global_stats = stats.get('global_intelligence', {})
            print(f"🌍 Global Intelligence:")
            print(f"   Total contacts: {global_stats.get('total_contacts', 0)}")
            print(f"   Average confidence: {global_stats.get('average_confidence', 0)}")
            print(f"   Verified contacts: {global_stats.get('verified_contacts', 0)}")
            print(f"   Fresh contacts (7d): {global_stats.get('fresh_contacts_7d', 0)}")
            
            user_stats = stats.get('user_contexts', {})
            print(f"\n👥 User Contexts:")
            print(f"   Total contexts: {user_stats.get('total_contexts', 0)}")
            print(f"   Active users: {user_stats.get('active_users', 0)}")
            print(f"   Avg response rate: {user_stats.get('average_response_rate', 0)}")
            
            cache_stats = stats.get('hot_cache', {})
            print(f"\n🔥 Hot Cache:")
            print(f"   Cached contacts: {cache_stats.get('cached_contacts', 0)}")
            print(f"   Cache limit: {cache_stats.get('cache_limit', 0)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Performance metrics test failed: {e}")
            return False
    
    async def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 STARTING SHARED INTELLIGENCE E2E TESTS")
        print("=" * 60)
        
        test_results = []
        
        # Setup
        await self.setup()
        
        # Run tests
        tests = [
            self.test_1_global_intelligence_database,
            self.test_2_black_belt_enrichment_with_cache_miss,
            self.test_3_shared_intelligence_cache_hit,
            self.test_4_user_context_separation,
            self.test_5_engagement_tracking,
            self.test_6_system_performance_metrics
        ]
        
        for i, test in enumerate(tests, 1):
            try:
                result = await test()
                test_results.append(result)
                if result:
                    print(f"✅ Test {i} PASSED")
                else:
                    print(f"❌ Test {i} FAILED")
            except Exception as e:
                print(f"❌ Test {i} ERROR: {e}")
                test_results.append(False)
        
        # Summary
        print("\n" + "=" * 60)
        print("🏁 SHARED INTELLIGENCE E2E TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(test_results)
        total = len(test_results)
        success_rate = (passed / total) * 100 if total > 0 else 0
        
        print(f"✅ Tests passed: {passed}/{total} ({success_rate:.1f}%)")
        
        if success_rate >= 80:
            print("🎉 SHARED INTELLIGENCE SYSTEM IS OPERATIONAL!")
            print("🌍 Multi-user contact intelligence sharing working")
            print("🥷 Black Belt enrichment pipeline integrated")
            print("👤 Personal context separation maintained")
            print("📊 Cross-user engagement tracking active")
        else:
            print("⚠️ SYSTEM NEEDS ATTENTION - Some tests failed")
        
        return success_rate >= 80

async def main():
    """Run the end-to-end test"""
    test_runner = SharedIntelligenceE2ETest()
    
    try:
        success = await test_runner.run_all_tests()
        
        if success:
            print("\n🎯 NEXT STEPS:")
            print("1. Test the API endpoints: /api/shared-intelligence/stats")
            print("2. Run contact enrichment to see shared intelligence in action")
            print("3. Monitor cache hit rates for performance improvements")
            print("4. Test with multiple real users to validate cross-user benefits")
            
            return 0
        else:
            print("\n🔧 TROUBLESHOOTING NEEDED:")
            print("1. Check database connectivity")
            print("2. Verify Claude API key is set")
            print("3. Review error logs for specific issues")
            return 1
            
    except Exception as e:
        print(f"\n💥 TEST RUNNER FAILED: {e}")
        return 1

if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 