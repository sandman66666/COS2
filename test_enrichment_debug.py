#!/usr/bin/env python3
"""
Debug Enrichment Test - Find the 0% success rate issue
"""

import asyncio
import sys
import os
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_enrichment():
    try:
        from intelligence.d_enrichment.contact_enrichment_service import ContactEnrichmentService
        
        test_contact = {
            'email': 'amit@session-42.com',
            'domain': 'session-42.com',
            'frequency': 33
        }
        
        user_id = 1
        claude_api_key = os.getenv('ANTHROPIC_API_KEY')
        
        print("🧪 ENRICHMENT DEBUG TEST")
        print(f"📧 Contact: {test_contact['email']}")
        print(f"🧠 Claude API Key: {'✅ Available' if claude_api_key else '❌ Missing'}")
        print(f"🔑 Claude Model: {os.getenv('CLAUDE_MODEL', 'Not set')}")
        
        # Test enrichment service
        print("\n🔧 Creating ContactEnrichmentService...")
        enrichment_service = ContactEnrichmentService(
            user_id=user_id,
            storage_manager=None,
            claude_api_key=claude_api_key
        )
        
        print("🔧 Initializing ContactEnrichmentService...")
        await enrichment_service.initialize()
        
        # Test if Black Belt is available
        if hasattr(enrichment_service, 'black_belt_adapter'):
            print("✅ Black Belt Adapter found")
            adapter = enrichment_service.black_belt_adapter
            
            print(f"🔧 Adapter initialized: {adapter is not None}")
            print(f"🔧 Adapter has claude_api_key: {hasattr(adapter, 'claude_api_key') and adapter.claude_api_key}")
            print(f"🔧 Adapter has claude_client: {hasattr(adapter, 'claude_client') and adapter.claude_client}")
            
            # Test Claude API if available
            if adapter and adapter.claude_client:
                print("🧠 Testing Claude API...")
                try:
                    client = adapter.claude_client
                    response = client.messages.create(
                        model="claude-opus-4-20250514",
                        max_tokens=50,
                        messages=[{"role": "user", "content": "Say 'test successful'"}]
                    )
                    print(f"✅ Claude Response: {response.content[0].text}")
                    
                    # Now test the actual enrichment
                    print("\n🏢 Testing actual enrichment...")
                    enrichment_result = await adapter.enhance_contact_enrichment(
                        test_contact['email'],
                        test_contact,
                        []
                    )
                    
                    if enrichment_result:
                        print(f"✅ Enrichment SUCCESS!")
                        print(f"🎯 Confidence: {enrichment_result.get('confidence_score', 'N/A')}")
                        print(f"📊 Sources: {enrichment_result.get('data_sources', [])}")
                    else:
                        print("❌ Enrichment returned None")
                        
                except Exception as e:
                    print(f"❌ Claude/Enrichment Error: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print("❌ Claude client not available after initialization")
                if adapter:
                    print(f"   - API key present: {bool(adapter.claude_api_key)}")
                    print(f"   - Client object: {adapter.claude_client}")
                
        else:
            print("❌ Black Belt Adapter not found")
            
        print("🏁 Test complete!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_enrichment()) 