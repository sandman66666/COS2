"""
Knowledge Tree Orchestrator
Main orchestrator now using Claude Content Consolidation for any content type (emails, documents, slack, tasks, etc.)
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional

from intelligence.c_content_processing.claude_content_consolidator import ClaudeContentConsolidator, ContentItem
from storage.storage_manager import StorageManager

class KnowledgeTreeOrchestrator:
    def __init__(self, claude_api_key: str):
        self.claude_consolidator = ClaudeContentConsolidator(claude_api_key)
        self.storage_manager = StorageManager()

    async def build_complete_knowledge_tree(self, user_email: str, 
                                          force_rebuild: bool = False) -> Dict[str, Any]:
        """
        Main orchestration method using Claude Content Consolidation for all content types
        """
        print("🚀 Starting Claude-Powered Content Knowledge Tree Build Process...")
        
        # Get user from database to get both email and numeric ID
        user = await self.storage_manager.get_user_by_email(user_email)
        if not user:
            raise ValueError(f"User {user_email} not found")
        
        user_id = user['id']  # Numeric ID for storage operations
        
        # Check if we have recent knowledge tree and don't force rebuild
        if not force_rebuild:
            existing_tree = await self._get_existing_tree(user_id)
            if existing_tree and self._is_tree_recent(existing_tree):
                print("✅ Using existing recent knowledge tree")
                return existing_tree

        print("\n" + "="*50)
        print("📄 CLAUDE CONTENT CONSOLIDATION")
        print("="*50)
        
        # Get ALL content for comprehensive analysis
        print("📬 Fetching all content for comprehensive analysis...")
        all_content = await self._collect_all_content(user_email)
        print(f"📊 Retrieved {len(all_content)} total content items")
        
        if not all_content:
            return self._create_empty_tree_response(user_id, user_email)
        
        # Process content with Claude consolidation
        knowledge_tree = await self.claude_consolidator.process_all_content(all_content, user_email)
        
        # Convert to legacy format for compatibility
        legacy_tree = self.claude_consolidator.to_legacy_format(knowledge_tree)
        legacy_tree['user_email'] = user_email
        
        # Store the knowledge tree using numeric user_id
        success = await self.storage_manager.store_knowledge_tree(
            user_id=user_id,
            tree_data=legacy_tree,
            analysis_type="claude_content_consolidation_v3"
        )
        
        if not success:
            raise Exception("Failed to store knowledge tree")
        
        # Combine results for final output
        final_results = {
            'success': True,
            'user_id': user_id,
            'user_email': user_email,
            'knowledge_tree': legacy_tree,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'processing_stats': {
                'total_content_processed': knowledge_tree.metadata.get('total_content_processed', 0),
                'total_batches': knowledge_tree.metadata.get('batch_count', 1),
                'topics_identified': len(knowledge_tree.topics),
                'relationships_analyzed': len(knowledge_tree.relationships),
                'business_domains': len(knowledge_tree.business_domains),
                'timeline_events': len(knowledge_tree.timeline),
                'content_sources': len(knowledge_tree.content_sources)
            },
            'claude_metadata': {
                'model_used': self.claude_consolidator.model,
                'max_chars_per_batch': self.claude_consolidator.max_chars_per_request,
                'processing_method': 'iterative_batch_consolidation',
                'content_types_supported': ['email', 'document', 'slack', 'task', 'meeting', 'note']
            },
            'content_breakdown': knowledge_tree.content_sources
        }
        
        print("\n🎯 Claude Content Knowledge Tree Build Complete!")
        print(f"📊 Processed {final_results['processing_stats']['total_content_processed']} content items")
        print(f"📦 Used {final_results['processing_stats']['total_batches']} Claude batches")
        print(f"🏷️ Identified {final_results['processing_stats']['topics_identified']} topics")
        print(f"🤝 Analyzed {final_results['processing_stats']['relationships_analyzed']} relationships")
        print(f"📄 Content sources: {', '.join(knowledge_tree.content_sources.keys())}")
        
        return final_results

    async def _collect_all_content(self, user_email: str) -> List[ContentItem]:
        """
        Collect all content from various sources and convert to ContentItem format
        """
        all_content = []
        
        # 1. Get emails (current primary source)
        print("📧 Collecting emails...")
        emails = await self.storage_manager.get_emails_for_user(user_email)
        if emails:
            email_content = ClaudeContentConsolidator.from_emails(emails)
            all_content.extend(email_content)
            print(f"  ✅ Added {len(email_content)} emails")
        
        # 2. Get documents (future - placeholder for now)
        print("📄 Collecting documents...")
        try:
            documents = await self._get_documents_for_user(user_email)
            if documents:
                doc_content = ClaudeContentConsolidator.from_documents(documents)
                all_content.extend(doc_content)
                print(f"  ✅ Added {len(doc_content)} documents")
        except Exception as e:
            print(f"  ⚠️ Documents not available yet: {e}")
        
        # 3. Get Slack messages (future - placeholder for now)
        print("💬 Collecting Slack messages...")
        try:
            slack_messages = await self._get_slack_messages_for_user(user_email)
            if slack_messages:
                slack_content = ClaudeContentConsolidator.from_slack_messages(slack_messages)
                all_content.extend(slack_content)
                print(f"  ✅ Added {len(slack_content)} Slack messages")
        except Exception as e:
            print(f"  ⚠️ Slack not available yet: {e}")
        
        # 4. Get tasks/todos (future - placeholder for now)
        print("✅ Collecting tasks...")
        try:
            tasks = await self._get_tasks_for_user(user_email)
            if tasks:
                task_content = self._convert_tasks_to_content(tasks)
                all_content.extend(task_content)
                print(f"  ✅ Added {len(task_content)} tasks")
        except Exception as e:
            print(f"  ⚠️ Tasks not available yet: {e}")
        
        # 5. Get meeting notes (future - placeholder for now)
        print("🤝 Collecting meeting notes...")
        try:
            meetings = await self._get_meetings_for_user(user_email)
            if meetings:
                meeting_content = self._convert_meetings_to_content(meetings)
                all_content.extend(meeting_content)
                print(f"  ✅ Added {len(meeting_content)} meetings")
        except Exception as e:
            print(f"  ⚠️ Meetings not available yet: {e}")
        
        print(f"📋 Total content collected: {len(all_content)} items")
        return all_content

    # Future content source methods (placeholders for extensibility)
    async def _get_documents_for_user(self, user_email: str) -> List[Dict]:
        """Get documents for user (future implementation)"""
        # TODO: Implement document retrieval from Google Drive, Dropbox, etc.
        return []

    async def _get_slack_messages_for_user(self, user_email: str) -> List[Dict]:
        """Get Slack messages for user (future implementation)"""
        # TODO: Implement Slack API integration
        return []

    async def _get_tasks_for_user(self, user_email: str) -> List[Dict]:
        """Get tasks/todos for user (future implementation)"""
        # TODO: Implement task management integration (Todoist, Asana, etc.)
        return []

    async def _get_meetings_for_user(self, user_email: str) -> List[Dict]:
        """Get meeting notes for user (future implementation)"""
        # TODO: Implement meeting notes from calendar, Zoom, etc.
        return []

    def _convert_tasks_to_content(self, tasks: List[Dict]) -> List[ContentItem]:
        """Convert tasks to ContentItem format (future implementation)"""
        # TODO: Implement task to ContentItem conversion
        return []

    def _convert_meetings_to_content(self, meetings: List[Dict]) -> List[ContentItem]:
        """Convert meetings to ContentItem format (future implementation)"""
        # TODO: Implement meeting to ContentItem conversion
        return []

    async def iterate_knowledge_tree(self, user_email: str) -> Dict[str, Any]:
        """
        Iterate/update existing knowledge tree
        For Claude consolidation, this rebuilds with all content since Claude handles incremental analysis
        """
        print("🔄 Starting Knowledge Tree Iteration with Claude Content Consolidation...")
        
        # With Claude consolidation, we can rebuild efficiently since it handles incrementals
        return await self.build_complete_knowledge_tree(user_email, force_rebuild=True)

    async def _get_existing_tree(self, user_id: int) -> Optional[Dict]:
        """Get existing knowledge tree from storage"""
        try:
            return await self.storage_manager.get_latest_knowledge_tree(user_id)
        except:
            return None

    def _is_tree_recent(self, tree: Dict, max_age_hours: int = 24) -> bool:
        """Check if tree is recent enough to skip rebuild"""
        try:
            created_at = tree.get('created_at')
            if not created_at:
                return False
            
            tree_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            age_hours = (datetime.now() - tree_time).total_seconds() / 3600
            
            return age_hours < max_age_hours
        except:
            return False

    def _create_empty_tree_response(self, user_id: int, user_email: str) -> Dict[str, Any]:
        """Create empty tree response when no content found"""
        return {
            'success': True,
            'user_id': user_id,
            'user_email': user_email,
            'knowledge_tree': {
                'user_email': user_email,
                'created_at': datetime.now().isoformat(),
                'version': "3.0_claude_content_consolidation",
                'analysis_depth': "claude_iterative_content_consolidation",
                'contact_count': 0,
                'content_count': 0,
                'entities': [],
                'topics': [],
                'business_domains': {},
                'insights': [],
                'relationships': [],
                'content_sources': {},
                'multidimensional_analysis': {
                    'hierarchical_levels': 0,
                    'topic_count': 0,
                    'relationship_count': 0,
                    'batch_count': 0,
                    'content_source_diversity': 0
                }
            },
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'message': 'No content found for analysis'
        }

    def get_knowledge_tree_status(self, user_email: str) -> Dict[str, Any]:
        """Get status of knowledge tree building process"""
        
        try:
            # Get user from database to get numeric ID
            user = asyncio.run(self.storage_manager.get_user_by_email(user_email))
            if not user:
                return {
                    "user_email": user_email,
                    "has_knowledge_tree": False,
                    "error": f"User {user_email} not found",
                    "processing_method": "claude_content_consolidation"
                }
            
            user_id = user['id']
            tree = self.storage_manager.get_latest_knowledge_tree(user_id)
            has_tree = tree is not None
            
            status = {
                "user_id": user_id,
                "user_email": user_email,
                "has_knowledge_tree": has_tree,
                "last_updated": None,
                "statistics": {},
                "processing_method": "claude_content_consolidation"
            }
            
            if has_tree:
                status["last_updated"] = tree.get("created_at")
                status["statistics"] = {
                    "content_count": tree.get("content_count", 0),
                    "contact_count": tree.get("contact_count", 0),
                    "topic_count": len(tree.get("topics", [])),
                    "business_domains": len(tree.get("business_domains", {})),
                    "claude_batches": tree.get("claude_metadata", {}).get("total_batches", 0),
                    "content_sources": tree.get("content_sources", {}),
                    "content_source_diversity": len(tree.get("content_sources", {}))
                }
                
            return status
            
        except Exception as e:
            return {
                "user_email": user_email,
                "has_knowledge_tree": False,
                "error": str(e),
                "processing_method": "claude_content_consolidation"
            } 