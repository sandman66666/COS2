# intelligence/incremental_knowledge_system.py
import json
import asyncio
from typing import Dict, List, Optional, Set, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from utils.logging import structured_logger as logger
from config.settings import ANTHROPIC_API_KEY
from intelligence.f_knowledge_integration.advanced_knowledge_system import AdvancedKnowledgeSystem
from intelligence.b_data_collection.behavioral_intelligence_system import BehavioralIntelligenceSystem

class ChangeType(Enum):
    """Types of changes that can trigger knowledge updates"""
    NEW_EMAIL = "new_email"
    NEW_CONTACT = "new_contact" 
    NEW_TOPIC = "new_topic"
    TOPIC_EVOLUTION = "topic_evolution"
    RELATIONSHIP_CHANGE = "relationship_change"
    NEW_DATA_SOURCE = "new_data_source"

class DataSource(Enum):
    """Supported data sources for knowledge tree"""
    EMAIL = "email"
    SLACK = "slack"
    TEAMS = "teams"
    LINKEDIN = "linkedin"
    CALENDAR = "calendar"
    DOCUMENTS = "documents"

@dataclass
class KnowledgeChange:
    """Represents a detected change in knowledge"""
    change_id: str
    change_type: ChangeType
    data_source: DataSource
    source_id: str  # email_id, slack_message_id, etc.
    detected_at: datetime
    impact_score: float  # 0.0-1.0 how significant this change is
    affected_topics: List[str]
    affected_contacts: List[str]
    change_summary: str
    metadata: Dict[str, Any]

class IncrementalKnowledgeSystem:
    """
    Intelligent incremental knowledge tree system that:
    1. Detects when new data requires knowledge updates
    2. Performs targeted analysis only on changed/new content
    3. Merges new insights with existing knowledge tree
    4. Supports multiple data sources (Email, Slack, etc.)
    """
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.knowledge_system = AdvancedKnowledgeSystem(user_id)
        
        # ADD: Automatic behavioral intelligence
        self.behavioral_system = BehavioralIntelligenceSystem(user_id)
        
        # Track processed content to detect changes
        self.processed_emails: Set[str] = set()
        self.processed_slack_messages: Set[str] = set()
        self.topic_fingerprints: Dict[str, str] = {}  # topic -> content hash
        self.contact_states: Dict[str, Dict] = {}  # email -> last known state
        
        # Change detection settings
        self.similarity_threshold = 0.85
        self.importance_threshold = 0.3
        
    async def initialize(self):
        """Initialize the incremental system with existing knowledge state"""
        logger.info(f"🔄 Initializing incremental knowledge system for user {self.user_id}")
        
        # Load existing knowledge tree to understand current state
        await self._load_existing_knowledge_state()
        
        # Initialize change detection indices
        await self._build_change_detection_indices()
        
        logger.info("✅ Incremental knowledge system initialized")
    
    async def process_new_email(self, email_data: Dict) -> Optional[Dict]:
        """Process new email with automatic behavioral intelligence"""
        
        logger.info(f"📧 Processing new email incrementally for user {self.user_id}")
        
        # 1. Automatic behavioral analysis (no opt-in needed)
        behavioral_insights = await self.behavioral_system.analyze_message_for_behavioral_insights(
            email_data, data_source="email"
        )
        
        if behavioral_insights:
            logger.info(f"🧠 Behavioral insights extracted for {behavioral_insights.get('contact_email', 'unknown')}")
        
        # 2. Detect change type
        change_type = await self._detect_change_type(email_data, DataSource.EMAIL)
        
        # 3. Process based on change type
        knowledge_updates = None
        if change_type == ChangeType.NEW_TOPIC:
            knowledge_updates = await self._process_new_topic(email_data, DataSource.EMAIL)
        elif change_type == ChangeType.TOPIC_EVOLUTION:
            knowledge_updates = await self._process_topic_evolution(email_data, DataSource.EMAIL)
        elif change_type == ChangeType.RELATIONSHIP_CHANGE:
            knowledge_updates = await self._process_relationship_change(email_data, DataSource.EMAIL)
        
        # 4. Combine knowledge and behavioral updates
        if behavioral_insights or knowledge_updates:
            combined_result = {
                'change_type': change_type.value,
                'knowledge_updates': knowledge_updates,
                'behavioral_insights': behavioral_insights,
                'processed_at': datetime.utcnow().isoformat()
            }
            
            # 5. Update contact with behavioral profile
            if behavioral_insights:
                await self._update_contact_behavioral_profile(behavioral_insights)
            
            return combined_result
        
        return None
    
    async def process_new_slack_message(self, slack_data: Dict) -> Optional[Dict]:
        """Process new Slack message with automatic behavioral intelligence"""
        
        logger.info(f"💬 Processing new Slack message incrementally for user {self.user_id}")
        
        # 1. Automatic behavioral analysis
        behavioral_insights = await self.behavioral_system.analyze_message_for_behavioral_insights(
            slack_data, data_source="slack"
        )
        
        if behavioral_insights:
            logger.info(f"🧠 Slack behavioral insights for {behavioral_insights.get('contact_email', 'unknown')}")
        
        # 2. Detect change type
        change_type = await self._detect_change_type(slack_data, DataSource.SLACK)
        
        # 3. Process based on change type
        knowledge_updates = None
        if change_type == ChangeType.NEW_TOPIC:
            knowledge_updates = await self._process_new_topic(slack_data, DataSource.SLACK)
        elif change_type == ChangeType.TOPIC_EVOLUTION:
            knowledge_updates = await self._process_topic_evolution(slack_data, DataSource.SLACK)
        elif change_type == ChangeType.RELATIONSHIP_CHANGE:
            knowledge_updates = await self._process_relationship_change(slack_data, DataSource.SLACK)
        
        # 4. Combine results
        if behavioral_insights or knowledge_updates:
            combined_result = {
                'change_type': change_type.value,
                'knowledge_updates': knowledge_updates,
                'behavioral_insights': behavioral_insights,
                'processed_at': datetime.utcnow().isoformat()
            }
            
            # 5. Update contact behavioral profile
            if behavioral_insights:
                await self._update_contact_behavioral_profile(behavioral_insights)
            
            return combined_result
        
        return None
    
    async def _detect_email_changes(self, email_data: Dict) -> List[KnowledgeChange]:
        """Detect what knowledge changes this email represents"""
        changes = []
        
        # 1. NEW CONTACT DETECTION
        sender = email_data.get('sender') or email_data.get('from', '')
        if sender and sender not in self.contact_states:
            changes.append(KnowledgeChange(
                change_id=f"new_contact_{datetime.utcnow().timestamp()}",
                change_type=ChangeType.NEW_CONTACT,
                data_source=DataSource.EMAIL,
                source_id=email_data.get('id', ''),
                detected_at=datetime.utcnow(),
                impact_score=0.7,  # New contacts are significant
                affected_topics=[],
                affected_contacts=[sender],
                change_summary=f"New contact discovered: {sender}",
                metadata={'email_subject': email_data.get('subject', '')}
            ))
        
        # 2. NEW TOPIC DETECTION
        subject = email_data.get('subject', '').lower()
        content = email_data.get('body_text', '').lower()
        
        # Use simple keyword detection for topic classification
        potential_topics = await self._extract_potential_topics(subject, content)
        
        for topic in potential_topics:
            if topic not in self.topic_fingerprints:
                changes.append(KnowledgeChange(
                    change_id=f"new_topic_{datetime.utcnow().timestamp()}_{topic}",
                    change_type=ChangeType.NEW_TOPIC,
                    data_source=DataSource.EMAIL,
                    source_id=email_data.get('id', ''),
                    detected_at=datetime.utcnow(),
                    impact_score=0.8,  # New topics are very significant
                    affected_topics=[topic],
                    affected_contacts=[sender] if sender else [],
                    change_summary=f"New topic discovered: {topic}",
                    metadata={'keywords': potential_topics[topic]}
                ))
        
        # 3. TOPIC EVOLUTION DETECTION
        for topic in potential_topics:
            if topic in self.topic_fingerprints:
                # Check if this email adds new context to existing topic
                new_context = content[:500]  # Sample for comparison
                existing_fingerprint = self.topic_fingerprints[topic]
                
                if await self._content_represents_evolution(topic, new_context, existing_fingerprint):
                    changes.append(KnowledgeChange(
                        change_id=f"topic_evolution_{datetime.utcnow().timestamp()}_{topic}",
                        change_type=ChangeType.TOPIC_EVOLUTION,
                        data_source=DataSource.EMAIL,
                        source_id=email_data.get('id', ''),
                        detected_at=datetime.utcnow(),
                        impact_score=0.6,  # Evolution is moderately significant
                        affected_topics=[topic],
                        affected_contacts=[sender] if sender else [],
                        change_summary=f"Topic evolution detected: {topic}",
                        metadata={'new_context_sample': new_context[:200]}
                    ))
        
        return changes
    
    async def _process_incremental_changes(self, changes: List[KnowledgeChange]) -> Dict:
        """Process detected changes and update knowledge tree incrementally"""
        
        if not changes:
            return {}
        
        logger.info(f"🔄 Processing {len(changes)} incremental changes")
        
        # Group changes by type for efficient processing
        changes_by_type = {}
        for change in changes:
            if change.change_type not in changes_by_type:
                changes_by_type[change.change_type] = []
            changes_by_type[change.change_type].append(change)
        
        updated_sections = {}
        
        # Process new contacts
        if ChangeType.NEW_CONTACT in changes_by_type:
            contact_updates = await self._process_new_contacts(changes_by_type[ChangeType.NEW_CONTACT])
            updated_sections['contacts'] = contact_updates
        
        # Process new topics
        if ChangeType.NEW_TOPIC in changes_by_type:
            topic_updates = await self._process_new_topics(changes_by_type[ChangeType.NEW_TOPIC])
            updated_sections['topics'] = topic_updates
        
        # Process topic evolution
        if ChangeType.TOPIC_EVOLUTION in changes_by_type:
            evolution_updates = await self._process_topic_evolution(changes_by_type[ChangeType.TOPIC_EVOLUTION])
            if 'topics' not in updated_sections:
                updated_sections['topics'] = {}
            updated_sections['topics'].update(evolution_updates)
        
        # Generate strategic insights only for significant changes
        high_impact_changes = [c for c in changes if c.impact_score > 0.7]
        if high_impact_changes:
            strategic_updates = await self._generate_incremental_strategic_insights(high_impact_changes)
            updated_sections['strategic_insights'] = strategic_updates
        
        return updated_sections
    
    async def _process_new_contacts(self, contact_changes: List[KnowledgeChange]) -> Dict:
        """Process new contact discoveries"""
        new_contacts = {}
        
        for change in contact_changes:
            contact_email = change.affected_contacts[0] if change.affected_contacts else None
            if not contact_email:
                continue
                
            # Run targeted contact enrichment
            logger.info(f"👤 Running targeted enrichment for new contact: {contact_email}")
            
            # This would integrate with the existing enrichment system
            enrichment_result = await self._enrich_new_contact(contact_email, change.metadata)
            
            new_contacts[contact_email] = {
                'discovered_at': change.detected_at.isoformat(),
                'source': change.data_source.value,
                'enrichment': enrichment_result,
                'change_id': change.change_id
            }
        
        return new_contacts
    
    async def _process_new_topics(self, topic_changes: List[KnowledgeChange]) -> Dict:
        """Process new topic discoveries"""
        new_topics = {}
        
        for change in topic_changes:
            topic = change.affected_topics[0] if change.affected_topics else None
            if not topic:
                continue
                
            logger.info(f"📝 Analyzing new topic: {topic}")
            
            # Run targeted Claude analysis for this specific topic
            topic_analysis = await self._analyze_new_topic(topic, change)
            
            new_topics[topic] = {
                'discovered_at': change.detected_at.isoformat(),
                'source': change.data_source.value,
                'analysis': topic_analysis,
                'change_id': change.change_id
            }
            
            # Update topic fingerprint for future change detection
            self.topic_fingerprints[topic] = await self._generate_topic_fingerprint(topic, topic_analysis)
        
        return new_topics
    
    async def _process_topic_evolution(self, evolution_changes: List[KnowledgeChange]) -> Dict:
        """Process topic evolution updates"""
        evolved_topics = {}
        
        for change in evolution_changes:
            topic = change.affected_topics[0] if change.affected_topics else None
            if not topic:
                continue
                
            logger.info(f"📈 Analyzing topic evolution: {topic}")
            
            # Run targeted analysis for the evolution
            evolution_analysis = await self._analyze_topic_evolution(topic, change)
            
            evolved_topics[topic] = {
                'evolved_at': change.detected_at.isoformat(),
                'source': change.data_source.value,
                'evolution_analysis': evolution_analysis,
                'change_id': change.change_id
            }
            
            # Update topic fingerprint
            self.topic_fingerprints[topic] = await self._generate_topic_fingerprint(topic, evolution_analysis)
        
        return evolved_topics
    
    async def _convert_slack_to_email_format(self, slack_data: Dict) -> Dict:
        """Convert Slack message to email-like format for processing"""
        return {
            'id': f"slack_{slack_data.get('channel')}_{slack_data.get('ts')}",
            'sender': slack_data.get('user', ''),
            'subject': f"Slack: #{slack_data.get('channel', 'unknown')}",
            'body_text': slack_data.get('text', ''),
            'created_at': datetime.fromtimestamp(float(slack_data.get('ts', 0))).isoformat(),
            'metadata': {
                'slack_channel': slack_data.get('channel'),
                'slack_thread_ts': slack_data.get('thread_ts'),
                'slack_user': slack_data.get('user')
            }
        }
    
    # Helper methods (simplified for brevity)
    async def _load_existing_knowledge_state(self):
        """Load existing knowledge tree to understand current state"""
        # Implementation would load from database
        pass
    
    async def _build_change_detection_indices(self):
        """Build indices for efficient change detection"""
        # Implementation would build topic/contact tracking
        pass
    
    async def _extract_potential_topics(self, subject: str, content: str) -> Dict[str, List[str]]:
        """Extract potential topics from email content"""
        # Simplified topic extraction - could use Claude for better results
        topics = {}
        
        # Example topic patterns
        if any(word in subject.lower() for word in ['project', 'proposal', 'plan']):
            topics['project_management'] = ['project', 'proposal', 'plan']
        
        if any(word in content.lower() for word in ['meeting', 'schedule', 'calendar']):
            topics['meetings'] = ['meeting', 'schedule', 'calendar'] 
            
        if any(word in content.lower() for word in ['budget', 'cost', 'price', 'financial']):
            topics['financial'] = ['budget', 'cost', 'price', 'financial']
        
        return topics
    
    async def _content_represents_evolution(self, topic: str, new_content: str, existing_fingerprint: str) -> bool:
        """Determine if new content represents significant evolution of a topic"""
        # Simplified - could use semantic similarity
        return len(new_content) > 100 and topic.lower() in new_content.lower()
    
    async def _enrich_new_contact(self, contact_email: str, metadata: Dict) -> Dict:
        """Run targeted enrichment for new contact"""
        # Integration point with existing enrichment system
        return {'status': 'enriched', 'confidence': 0.8}
    
    async def _analyze_new_topic(self, topic: str, change: KnowledgeChange) -> Dict:
        """Run targeted Claude analysis for new topic"""
        return {'topic': topic, 'analysis': 'New topic analysis results'}
    
    async def _analyze_topic_evolution(self, topic: str, change: KnowledgeChange) -> Dict:
        """Run targeted analysis for topic evolution"""
        return {'topic': topic, 'evolution': 'Topic evolution analysis results'}
    
    async def _generate_topic_fingerprint(self, topic: str, analysis: Dict) -> str:
        """Generate fingerprint for topic change detection"""
        return f"{topic}_{datetime.utcnow().timestamp()}"
    
    async def _generate_incremental_strategic_insights(self, changes: List[KnowledgeChange]) -> Dict:
        """Generate strategic insights for significant changes"""
        return {'insights': f'Strategic insights for {len(changes)} significant changes'}
    
    async def _update_change_tracking(self, changes: List[KnowledgeChange], updated_sections: Dict):
        """Update internal tracking state"""
        for change in changes:
            if change.change_type == ChangeType.NEW_CONTACT:
                for contact in change.affected_contacts:
                    self.contact_states[contact] = {'last_seen': change.detected_at.isoformat()} 
    
    async def _update_contact_behavioral_profile(self, behavioral_insights: Dict):
        """Update contact database with behavioral intelligence"""
        try:
            contact_email = behavioral_insights.get('contact_email')
            if not contact_email:
                return
            
            # Get existing contact or create new one
            # This integrates with the existing contact enrichment system
            
            behavioral_data = {
                'communication_style': behavioral_insights.get('behavioral_summary', {}).get('communication_style'),
                'influence_level': behavioral_insights.get('behavioral_summary', {}).get('influence_level'),
                'confidence_score': behavioral_insights.get('behavioral_summary', {}).get('confidence_score'),
                'timing_intelligence': behavioral_insights.get('timing_intelligence', {}),
                'communication_intelligence': behavioral_insights.get('communication_intelligence', {}),
                'professional_intelligence': behavioral_insights.get('professional_intelligence', {}),
                'last_behavioral_update': datetime.utcnow().isoformat()
            }
            
            # Store in contact enrichment data
            logger.info(f"💾 Updating contact behavioral profile: {contact_email}")
            
            # In production, this would update the contact database
            # For now, log the behavioral augmentation
            logger.info(f"🎯 Behavioral profile updated for {contact_email}: {behavioral_data.get('communication_style', 'unknown')} style, {behavioral_data.get('influence_level', 'unknown')} influence")
            
        except Exception as e:
            logger.error(f"❌ Failed to update contact behavioral profile: {e}")
    
    async def _detect_change_type(self, data: Dict, data_source: DataSource) -> ChangeType:
        """Detect the type of change based on the data"""
        # Implementation would depend on the specific data source and its structure
        # For now, a placeholder implementation
        return ChangeType.NEW_TOPIC  # Placeholder, actual implementation needed
    
    async def _process_new_topic(self, data: Dict, data_source: DataSource) -> Dict:
        """Process a new topic discovery"""
        # Implementation would depend on the specific data source and its structure
        # For now, a placeholder implementation
        return {'topic': 'New Topic', 'analysis': 'Topic analysis results'}  # Placeholder, actual implementation needed
    
    async def _process_topic_evolution(self, data: Dict, data_source: DataSource) -> Dict:
        """Process topic evolution"""
        # Implementation would depend on the specific data source and its structure
        # For now, a placeholder implementation
        return {'topic': 'Topic Evolution', 'evolution': 'Topic evolution analysis results'}  # Placeholder, actual implementation needed
    
    async def _process_relationship_change(self, data: Dict, data_source: DataSource) -> Dict:
        """Process a relationship change"""
        # Implementation would depend on the specific data source and its structure
        # For now, a placeholder implementation
        return {'relationship': 'New Relationship', 'analysis': 'Relationship analysis results'}  # Placeholder, actual implementation needed 