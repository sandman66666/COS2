"""
Claude Content Consolidator
Accumulates maximum content (emails, documents, slack, tasks, etc.) into Claude requests, builds knowledge tree iteratively
"""

import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum

import anthropic

class ContentType(Enum):
    EMAIL = "email"
    DOCUMENT = "document" 
    SLACK = "slack"
    TASK = "task"
    MEETING = "meeting"
    NOTE = "note"

@dataclass
class ContentItem:
    id: str
    type: ContentType
    title: str
    content: str
    participants: List[str]
    timestamp: datetime
    metadata: Dict
    source: str

@dataclass
class ContentBatch:
    content_items: List[ContentItem]
    total_chars: int
    batch_number: int
    date_range: str
    content_types: Dict[str, int]  # type -> count

@dataclass
class KnowledgeTree:
    topics: Dict[str, Dict]
    relationships: Dict[str, Dict] 
    business_domains: Dict[str, List[str]]
    timeline: List[Dict]
    content_sources: Dict[str, int]  # source -> count
    metadata: Dict

class ClaudeContentConsolidator:
    def __init__(self, claude_api_key: str):
        self.claude_client = anthropic.Anthropic(api_key=claude_api_key)
        self.max_chars_per_request = 180000  # Stay under Claude's 200k context window
        self.model = "claude-3-5-sonnet-20241022"

    async def process_all_content(self, content_items: List[ContentItem], user_email: str) -> KnowledgeTree:
        """
        Main method: Process all content by accumulating into batches and iteratively building tree
        """
        print(f"🚀 Starting Claude Content Consolidation for {len(content_items)} items")
        
        # Step 1: Create optimal batches based on character limits
        batches = self._create_optimal_batches(content_items)
        print(f"📦 Created {len(batches)} optimal batches")
        
        # Step 2: Process first batch to get initial tree structure
        knowledge_tree = await self._process_initial_batch(batches[0], user_email)
        print(f"🌱 Initial tree created with {len(knowledge_tree.topics)} topics")
        
        # Step 3: Iteratively augment with remaining batches
        for i, batch in enumerate(batches[1:], 2):
            print(f"🔄 Processing batch {i}/{len(batches)}...")
            knowledge_tree = await self._augment_tree_with_batch(knowledge_tree, batch, user_email)
            print(f"🌿 Tree now has {len(knowledge_tree.topics)} topics")
            
            # Small delay between requests
            await asyncio.sleep(1)
        
        print(f"✅ Complete! Final tree: {len(knowledge_tree.topics)} topics, {len(knowledge_tree.relationships)} relationships")
        return knowledge_tree

    def _create_optimal_batches(self, content_items: List[ContentItem]) -> List[ContentBatch]:
        """
        Create batches that maximize content per Claude request while staying under character limits
        """
        batches = []
        current_batch = []
        current_chars = 0
        batch_number = 1
        
        # Sort content by timestamp for chronological processing
        sorted_content = sorted(content_items, key=lambda x: x.timestamp)
        
        for item in sorted_content:
            # Calculate content character count
            item_text = self._extract_content_text(item)
            item_chars = len(item_text)
            
            # Check if adding this item would exceed limit
            if current_chars + item_chars > self.max_chars_per_request and current_batch:
                # Save current batch and start new one
                batches.append(self._create_batch(current_batch, batch_number))
                current_batch = []
                current_chars = 0
                batch_number += 1
            
            # Add item to current batch
            current_batch.append(item)
            current_chars += item_chars
        
        # Add final batch if it has content
        if current_batch:
            batches.append(self._create_batch(current_batch, batch_number))
        
        return batches

    def _create_batch(self, content_items: List[ContentItem], batch_number: int) -> ContentBatch:
        """Create a ContentBatch from items"""
        if not content_items:
            return ContentBatch([], 0, batch_number, "Unknown", {})
        
        # Calculate total characters
        total_chars = sum(len(self._extract_content_text(item)) for item in content_items)
        
        # Get date range
        timestamps = [item.timestamp for item in content_items]
        start_date = min(timestamps).strftime("%Y-%m-%d")
        end_date = max(timestamps).strftime("%Y-%m-%d")
        date_range = f"{start_date} to {end_date}"
        
        # Count content types
        content_types = {}
        for item in content_items:
            content_type = item.type.value
            content_types[content_type] = content_types.get(content_type, 0) + 1
        
        return ContentBatch(
            content_items=content_items,
            total_chars=total_chars,
            batch_number=batch_number,
            date_range=date_range,
            content_types=content_types
        )

    def _extract_content_text(self, item: ContentItem) -> str:
        """Extract all text content from item for character counting"""
        participants = ', '.join(item.participants)
        return f"Type: {item.type.value}\nTitle: {item.title}\nParticipants: {participants}\nContent: {item.content}\nSource: {item.source}\n\n"

    async def _process_initial_batch(self, batch: ContentBatch, user_email: str) -> KnowledgeTree:
        """
        Process first batch to create initial knowledge tree structure
        """
        # Prepare content for Claude
        content_text = self._format_content_for_claude(batch.content_items)
        
        # Count content sources
        content_sources = {}
        for item in batch.content_items:
            source = item.source
            content_sources[source] = content_sources.get(source, 0) + 1
        
        content_summary = self._get_content_summary(batch)
        
        prompt = f"""
Analyze this content from {user_email} and create a comprehensive knowledge tree structure.

CONTENT SUMMARY:
{content_summary}

CONTENT TO ANALYZE:
{content_text}

Create a structured knowledge tree with:

1. **TOPICS**: Identify key topics/themes with:
   - Topic name
   - Key participants
   - Business relevance (high/medium/low)
   - Action items extracted
   - Timeline summary
   - Related subtopics
   - Content sources involved

2. **RELATIONSHIPS**: For each person mentioned:
   - Relationship status (ESTABLISHED/ATTEMPTED/ONGOING/DORMANT)
   - Communication frequency
   - Business context
   - Engagement level
   - Content types they appear in

3. **BUSINESS DOMAINS**: Categorize topics into domains:
   - AI/Technology
   - Business Development  
   - Legal/Compliance
   - Finance/Investment
   - Music/Audio
   - Product Development
   - Operations/Admin
   - Personal/Misc

4. **TIMELINE**: Key events and communications in chronological order

Return as JSON with this structure:
{{
    "topics": {{
        "topic_name": {{
            "participants": ["email1", "email2"],
            "business_relevance": "high|medium|low",
            "action_items": ["action1", "action2"],
            "timeline_summary": "description",
            "key_points": ["point1", "point2"],
            "business_domain": "domain_name",
            "content_sources": ["email", "slack", "document"]
        }}
    }},
    "relationships": {{
        "email@domain.com": {{
            "status": "ESTABLISHED|ATTEMPTED|ONGOING|DORMANT",
            "frequency": "high|medium|low", 
            "business_context": "description",
            "engagement_level": 0.0-1.0,
            "topics_involved": ["topic1", "topic2"],
            "content_types": ["email", "slack", "document"]
        }}
    }},
    "business_domains": {{
        "domain_name": ["topic1", "topic2"]
    }},
    "timeline": [
        {{
            "date": "YYYY-MM-DD",
            "event": "description",
            "participants": ["email1"],
            "topic": "topic_name",
            "content_type": "email|document|slack|task"
        }}
    ]
}}

Focus on extracting real business intelligence, relationship dynamics, and strategic insights across all content types.
"""

        try:
            response = await self._call_claude(prompt)
            tree_data = json.loads(response)
            
            return KnowledgeTree(
                topics=tree_data.get('topics', {}),
                relationships=tree_data.get('relationships', {}),
                business_domains=tree_data.get('business_domains', {}),
                timeline=tree_data.get('timeline', []),
                content_sources=content_sources,
                metadata={
                    'created_at': datetime.now().isoformat(),
                    'batch_count': 1,
                    'total_content_processed': len(batch.content_items),
                    'date_range': batch.date_range,
                    'content_types': batch.content_types
                }
            )
            
        except Exception as e:
            print(f"❌ Error processing initial batch: {e}")
            # Return empty tree on error
            return KnowledgeTree(
                topics={}, relationships={}, business_domains={}, timeline=[], 
                content_sources={}, metadata={'error': str(e)}
            )

    async def _augment_tree_with_batch(self, existing_tree: KnowledgeTree, batch: ContentBatch, user_email: str) -> KnowledgeTree:
        """
        Augment existing knowledge tree with new batch of content
        """
        # Prepare content for Claude
        content_text = self._format_content_for_claude(batch.content_items)
        
        # Serialize existing tree for Claude
        existing_tree_json = json.dumps({
            'topics': existing_tree.topics,
            'relationships': existing_tree.relationships,
            'business_domains': existing_tree.business_domains,
            'timeline': existing_tree.timeline[-10:]  # Last 10 timeline items to save space
        }, indent=2)

        content_summary = self._get_content_summary(batch)

        prompt = f"""
You have an existing knowledge tree and new content to analyze.

EXISTING KNOWLEDGE TREE:
{existing_tree_json}

NEW CONTENT SUMMARY:
{content_summary}

NEW CONTENT TO ANALYZE:
{content_text}

Update the knowledge tree by:

1. **AUGMENTING EXISTING TOPICS**: Add new information to existing topics if the content relates to them
2. **CREATING NEW TOPICS**: Create new topics for content that doesn't fit existing ones  
3. **UPDATING RELATIONSHIPS**: Update relationship statuses and engagement levels based on new communications
4. **EXTENDING TIMELINE**: Add new timeline events from this content
5. **REFINING BUSINESS DOMAINS**: Adjust domain categorizations as needed
6. **TRACKING CONTENT SOURCES**: Note which content types contribute to each topic/relationship

Return the COMPLETE UPDATED knowledge tree in the same JSON structure. Include all existing data plus new insights.

The updated tree should:
- Preserve all valuable existing information
- Integrate new content into appropriate topics
- Update relationship statuses based on latest communications
- Maintain chronological timeline order
- Ensure no duplicate or conflicting information
- Track content source diversity

Focus on consolidation and enhancement rather than replacement.
"""

        try:
            response = await self._call_claude(prompt)
            updated_tree_data = json.loads(response)
            
            # Update content sources
            updated_content_sources = existing_tree.content_sources.copy()
            for item in batch.content_items:
                source = item.source
                updated_content_sources[source] = updated_content_sources.get(source, 0) + 1
            
            # Update metadata
            updated_metadata = existing_tree.metadata.copy()
            updated_metadata.update({
                'last_updated': datetime.now().isoformat(),
                'batch_count': updated_metadata.get('batch_count', 1) + 1,
                'total_content_processed': updated_metadata.get('total_content_processed', 0) + len(batch.content_items),
                'latest_date_range': batch.date_range,
                'latest_content_types': batch.content_types
            })
            
            return KnowledgeTree(
                topics=updated_tree_data.get('topics', existing_tree.topics),
                relationships=updated_tree_data.get('relationships', existing_tree.relationships),
                business_domains=updated_tree_data.get('business_domains', existing_tree.business_domains),
                timeline=updated_tree_data.get('timeline', existing_tree.timeline),
                content_sources=updated_content_sources,
                metadata=updated_metadata
            )
            
        except Exception as e:
            print(f"❌ Error augmenting tree with batch {batch.batch_number}: {e}")
            # Return existing tree on error
            return existing_tree

    def _get_content_summary(self, batch: ContentBatch) -> str:
        """Generate summary of content in batch"""
        summary_parts = []
        summary_parts.append(f"Content Items: {len(batch.content_items)}")
        summary_parts.append(f"Date Range: {batch.date_range}")
        
        # Content type breakdown
        type_parts = []
        for content_type, count in batch.content_types.items():
            type_parts.append(f"{count} {content_type}(s)")
        summary_parts.append(f"Types: {', '.join(type_parts)}")
        
        return " | ".join(summary_parts)

    def _format_content_for_claude(self, content_items: List[ContentItem]) -> str:
        """
        Format content for Claude analysis, optimized for space
        """
        formatted_content = []
        
        for i, item in enumerate(content_items, 1):
            participants_str = ', '.join(item.participants)
            content_preview = item.content[:2000] if item.content else "No content"  # Limit to manage size
            
            formatted_item = f"""
CONTENT {i} ({item.type.value.upper()}):
Date: {item.timestamp.strftime('%Y-%m-%d %H:%M')}
Title: {item.title}
Participants: {participants_str}
Source: {item.source}
Content: {content_preview}
---
"""
            formatted_content.append(formatted_item)
        
        return '\n'.join(formatted_content)

    async def _call_claude(self, prompt: str) -> str:
        """
        Call Claude API with retry logic
        """
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.claude_client.messages.create(
                    model=self.model,
                    max_tokens=4000,
                    temperature=0.1,
                    messages=[{
                        "role": "user", 
                        "content": prompt
                    }]
                )
                
                return response.content[0].text
                
            except Exception as e:
                if "overloaded" in str(e).lower() and attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + 1
                    print(f"⏳ Claude overloaded, retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise e

    def to_legacy_format(self, tree: KnowledgeTree) -> Dict:
        """
        Convert to legacy knowledge tree format for compatibility
        """
        # Convert relationships to entities format
        entities = []
        for email, relationship in tree.relationships.items():
            entity = {
                "type": "contact",
                "email": email,
                "relationship_status": relationship.get('status', 'unknown').lower(),
                "engagement_score": relationship.get('engagement_level', 0.0),
                "business_context": relationship.get('business_context', ''),
                "topics_involved": relationship.get('topics_involved', []),
                "communication_frequency": relationship.get('frequency', 'unknown'),
                "content_types": relationship.get('content_types', [])
            }
            entities.append(entity)
        
        # Convert topics to insights format
        insights = []
        for topic_name, topic_data in tree.topics.items():
            insight = {
                "type": "topic_analysis",
                "topic": topic_name,
                "business_relevance": topic_data.get('business_relevance', 'medium'),
                "participants": topic_data.get('participants', []),
                "action_items": topic_data.get('action_items', []),
                "key_points": topic_data.get('key_points', []),
                "content_sources": topic_data.get('content_sources', [])
            }
            insights.append(insight)
        
        return {
            "user_email": tree.metadata.get('user_email', ''),
            "created_at": tree.metadata.get('created_at', datetime.now().isoformat()),
            "version": "3.0_claude_content_consolidation",
            "analysis_depth": "claude_iterative_content_consolidation", 
            "contact_count": len(entities),
            "content_count": tree.metadata.get('total_content_processed', 0),
            "entities": entities,
            "topics": list(tree.topics.keys()),
            "business_domains": tree.business_domains,
            "insights": insights,
            "timeline": tree.timeline,
            "content_sources": tree.content_sources,
            "multidimensional_analysis": {
                "hierarchical_levels": len(tree.business_domains),
                "topic_count": len(tree.topics),
                "relationship_count": len(tree.relationships),
                "batch_count": tree.metadata.get('batch_count', 1),
                "content_source_diversity": len(tree.content_sources)
            },
            "claude_metadata": {
                "processing_method": "iterative_batch_consolidation",
                "total_batches": tree.metadata.get('batch_count', 1),
                "chars_per_batch": self.max_chars_per_request,
                "model_used": self.model,
                "content_types_supported": ["email", "document", "slack", "task", "meeting", "note"]
            }
        }

    # Content transformation helpers for different types
    @staticmethod
    def from_emails(emails: List[Dict]) -> List[ContentItem]:
        """Convert email data to ContentItem format"""
        content_items = []
        
        for email in emails:
            # Extract metadata
            metadata = email.get('metadata', {})
            if isinstance(metadata, str):
                try:
                    metadata = json.loads(metadata)
                except:
                    metadata = {}
            
            # Extract participants
            participants = []
            sender = metadata.get('from', email.get('sender', ''))
            if sender:
                participants.append(sender)
            
            recipients = metadata.get('to', email.get('recipients', []))
            if isinstance(recipients, list):
                participants.extend(recipients)
            elif recipients:
                participants.append(recipients)
            
            # Create ContentItem
            item = ContentItem(
                id=f"email_{email.get('id', email.get('gmail_id', len(content_items)))}",
                type=ContentType.EMAIL,
                title=metadata.get('subject', 'No Subject'),
                content=email.get('content', ''),
                participants=list(set(participants)),  # Remove duplicates
                timestamp=datetime.fromisoformat(email.get('created_at', datetime.now().isoformat())),
                metadata=metadata,
                source="gmail"
            )
            content_items.append(item)
        
        return content_items

    @staticmethod
    def from_documents(documents: List[Dict]) -> List[ContentItem]:
        """Convert document data to ContentItem format"""
        content_items = []
        
        for doc in documents:
            item = ContentItem(
                id=f"doc_{doc.get('id', len(content_items))}",
                type=ContentType.DOCUMENT,
                title=doc.get('title', doc.get('filename', 'Untitled Document')),
                content=doc.get('content', ''),
                participants=doc.get('authors', [doc.get('creator', '')]),
                timestamp=datetime.fromisoformat(doc.get('created_at', datetime.now().isoformat())),
                metadata=doc.get('metadata', {}),
                source=doc.get('source', 'documents')
            )
            content_items.append(item)
        
        return content_items

    @staticmethod
    def from_slack_messages(messages: List[Dict]) -> List[ContentItem]:
        """Convert Slack messages to ContentItem format"""
        content_items = []
        
        for msg in messages:
            item = ContentItem(
                id=f"slack_{msg.get('ts', len(content_items))}",
                type=ContentType.SLACK,
                title=f"#{msg.get('channel', 'unknown')} message",
                content=msg.get('text', ''),
                participants=[msg.get('user', '')],
                timestamp=datetime.fromtimestamp(float(msg.get('ts', 0))),
                metadata={
                    'channel': msg.get('channel', ''),
                    'thread_ts': msg.get('thread_ts', ''),
                    'message_type': msg.get('type', 'message')
                },
                source="slack"
            )
            content_items.append(item)
        
        return content_items 