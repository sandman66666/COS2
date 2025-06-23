# integrations/slack_integration.py
import json
import asyncio
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
import aiohttp
from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.webhook.async_client import AsyncWebhookClient

from utils.logging import structured_logger as logger
from intelligence.g_realtime_updates.incremental_knowledge_system import IncrementalKnowledgeSystem, DataSource
from config.settings import SLACK_BOT_TOKEN, SLACK_SIGNING_SECRET

class SlackKnowledgeIntegration:
    """
    Slack integration for real-time knowledge tree updates
    
    PRIVACY & FILTERING:
    - Only processes messages from strategic channels
    - Only analyzes messages with strategic keywords
    - Skips casual conversations, personal chats, and irrelevant content
    - Respects user privacy by filtering out non-business content
    
    Features:
    1. Smart channel filtering (only strategic channels)
    2. Keyword-based content filtering
    3. Thread analysis for project updates
    4. Strategic discussion detection
    """
    
    def __init__(self, user_id: int, slack_bot_token: str):
        self.user_id = user_id
        self.slack_client = AsyncWebClient(token=slack_bot_token)
        self.knowledge_system = IncrementalKnowledgeSystem(user_id)
        
        # Smart filtering configuration
        self.monitored_channels: Set[str] = set()
        self.processed_messages: Set[str] = set()
        self.strategic_channels: Set[str] = {
            'strategy', 'leadership', 'exec', 'executive', 'board',
            'planning', 'roadmap', 'vision', 'goals', 'objectives',
            'competitive', 'market', 'partnerships', 'business-dev',
            'product-strategy', 'eng-leadership'
        }
        self.excluded_channels: Set[str] = {
            'random', 'general', 'off-topic', 'lunch', 'coffee',
            'personal', 'social', 'memes', 'funny', 'casual',
            'water-cooler', 'announcements', 'birthday', 'holiday'
        }
        
    async def initialize(self):
        """Initialize Slack integration"""
        logger.info(f"🔗 Initializing Slack integration for user {self.user_id}")
        
        await self.knowledge_system.initialize()
        
        # Test Slack connection
        try:
            auth_response = await self.slack_client.auth_test()
            logger.info(f"✅ Connected to Slack workspace: {auth_response['team']}")
            
            # Auto-discover strategic channels
            await self._discover_strategic_channels()
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to Slack: {e}")
            raise
        
        logger.info("✅ Slack integration initialized")
    
    async def process_slack_event(self, event_data: Dict) -> Optional[Dict]:
        """
        Process incoming Slack webhook event with smart filtering
        
        Args:
            event_data: Slack event data from webhook
            
        Returns:
            Knowledge tree updates or None if filtered out
        """
        event_type = event_data.get('type')
        
        if event_type == 'message':
            return await self._process_message_event(event_data)
        elif event_type == 'channel_created':
            return await self._process_channel_created(event_data)
        elif event_type == 'member_joined_channel':
            return await self._process_member_joined(event_data)
        else:
            logger.debug(f"💬 Ignoring Slack event type: {event_type}")
            return None
    
    async def _process_message_event(self, message_data: Dict) -> Optional[Dict]:
        """Process a Slack message with comprehensive filtering"""
        
        # FILTER 1: Skip bot messages and message updates
        if message_data.get('bot_id') or message_data.get('subtype') == 'message_changed':
            logger.debug("🤖 Skipping bot message or message update")
            return None
        
        # FILTER 2: Skip if already processed
        channel = message_data.get('channel')
        ts = message_data.get('ts')
        message_id = f"{channel}:{ts}"
        
        if message_id in self.processed_messages:
            logger.debug(f"♻️ Message {message_id} already processed, skipping")
            return None
        
        # FILTER 3: Channel-based filtering
        channel_filter_result = await self._should_process_channel_message(channel, message_data)
        if not channel_filter_result['should_process']:
            logger.debug(f"🚫 Channel filtering: {channel_filter_result['reason']}")
            self.processed_messages.add(message_id)  # Track as processed to avoid re-checking
            return None
        
        # FILTER 4: Content-based filtering
        content_filter_result = await self._should_process_message_content(message_data)
        if not content_filter_result['should_process']:
            logger.debug(f"🚫 Content filtering: {content_filter_result['reason']}")
            self.processed_messages.add(message_id)
            return None
        
        # FILTER 5: Strategic relevance check
        strategic_relevance = await self._assess_strategic_relevance(message_data)
        if strategic_relevance < 0.3:  # Below minimum threshold
            logger.debug(f"📊 Low strategic relevance ({strategic_relevance:.2f}), skipping")
            self.processed_messages.add(message_id)
            return None
        
        # MESSAGE PASSES ALL FILTERS - Process it
        user = message_data.get('user')
        logger.info(f"✅ Processing strategic Slack message from {user} in #{channel_filter_result.get('channel_name', channel)} (relevance: {strategic_relevance:.2f})")
        
        # Enrich message data with channel context
        enriched_message = await self._enrich_slack_message(message_data)
        
        # Process through incremental knowledge system
        knowledge_updates = await self.knowledge_system.process_new_slack_message(enriched_message)
        
        self.processed_messages.add(message_id)
        
        # If this is a strategic discussion, trigger deeper analysis
        if strategic_relevance > 0.7:  # High strategic relevance
            strategic_updates = await self._analyze_strategic_discussion(enriched_message)
            if knowledge_updates:
                knowledge_updates['strategic_discussion'] = strategic_updates
            else:
                knowledge_updates = {'strategic_discussion': strategic_updates}
        
        return knowledge_updates
    
    async def _discover_strategic_channels(self):
        """Auto-discover strategic channels in the workspace"""
        try:
            # Get list of channels
            response = await self.slack_client.conversations_list(
                types="public_channel,private_channel",
                limit=200
            )
            
            strategic_count = 0
            for channel in response['channels']:
                channel_name = channel['name'].lower()
                channel_purpose = channel.get('purpose', {}).get('value', '').lower()
                
                if await self._should_monitor_channel(channel_name, channel_purpose):
                    self.monitored_channels.add(channel['id'])
                    strategic_count += 1
                    logger.debug(f"📌 Monitoring strategic channel: #{channel_name}")
            
            logger.info(f"🎯 Auto-discovered {strategic_count} strategic channels to monitor")
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to auto-discover channels: {e}")
    
    async def _should_process_channel_message(self, channel_id: str, message_data: Dict) -> Dict:
        """Determine if we should process messages from this channel"""
        try:
            # Get channel info
            channel_info = await self.slack_client.conversations_info(channel=channel_id)
            channel_name = channel_info['channel']['name'].lower()
            
            # Check if explicitly excluded
            if any(excluded in channel_name for excluded in self.excluded_channels):
                return {
                    'should_process': False,
                    'reason': f'Channel #{channel_name} is in excluded list',
                    'channel_name': channel_name
                }
            
            # Check if it's a strategic channel
            is_strategic = any(strategic in channel_name for strategic in self.strategic_channels)
            is_monitored = channel_id in self.monitored_channels
            
            if is_strategic or is_monitored:
                return {
                    'should_process': True,
                    'reason': f'Strategic channel #{channel_name}',
                    'channel_name': channel_name
                }
            
            # Check channel purpose for strategic indicators
            channel_purpose = channel_info['channel'].get('purpose', {}).get('value', '').lower()
            strategic_indicators = ['strategy', 'planning', 'roadmap', 'vision', 'competitive', 'business']
            
            if any(indicator in channel_purpose for indicator in strategic_indicators):
                self.monitored_channels.add(channel_id)  # Add to monitoring
                return {
                    'should_process': True,
                    'reason': f'Strategic purpose in #{channel_name}',
                    'channel_name': channel_name
                }
            
            return {
                'should_process': False,
                'reason': f'Channel #{channel_name} not strategic',
                'channel_name': channel_name
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to check channel {channel_id}: {e}")
            return {
                'should_process': False,
                'reason': 'Channel check failed',
                'channel_name': 'unknown'
            }
    
    async def _should_process_message_content(self, message_data: Dict) -> Dict:
        """Determine if message content is strategically relevant"""
        text = message_data.get('text', '').lower()
        
        # Skip very short messages (likely not strategic)
        if len(text.strip()) < 10:
            return {
                'should_process': False,
                'reason': 'Message too short'
            }
        
        # Skip common casual patterns
        casual_patterns = [
            'lol', 'haha', 'thanks', 'good morning', 'good night',
            'lunch?', 'coffee?', 'how was your weekend',
            'happy birthday', 'congratulations', 'nice work',
            'see you tomorrow', 'have a great day'
        ]
        
        if any(pattern in text for pattern in casual_patterns):
            return {
                'should_process': False,
                'reason': 'Casual conversation detected'
            }
        
        # Check for strategic keywords
        strategic_keywords = [
            'strategy', 'roadmap', 'vision', 'goals', 'objectives',
            'partnership', 'acquisition', 'funding', 'investment',
            'competitive', 'market', 'opportunity', 'threat',
            'decision', 'priority', 'budget', 'resource',
            'milestone', 'deadline', 'launch', 'product',
            'customer', 'revenue', 'growth', 'metrics'
        ]
        
        strategic_keyword_count = sum(1 for keyword in strategic_keywords if keyword in text)
        
        if strategic_keyword_count >= 1:
            return {
                'should_process': True,
                'reason': f'Contains {strategic_keyword_count} strategic keywords'
            }
        
        # Check for business entities (company names, products)
        business_indicators = [
            'project', 'client', 'customer', 'proposal', 'contract',
            'meeting', 'presentation', 'demo', 'poc', 'pilot'
        ]
        
        if any(indicator in text for indicator in business_indicators):
            return {
                'should_process': True,
                'reason': 'Business context detected'
            }
        
        return {
            'should_process': False,
            'reason': 'No strategic content detected'
        }
    
    async def _assess_strategic_relevance(self, message_data: Dict) -> float:
        """Assess strategic relevance score (0.0-1.0)"""
        text = message_data.get('text', '').lower()
        score = 0.0
        
        # High-impact strategic keywords
        high_impact_keywords = [
            'strategy', 'vision', 'roadmap', 'acquisition', 'partnership',
            'competitive', 'market share', 'revenue', 'funding'
        ]
        
        # Medium-impact keywords
        medium_impact_keywords = [
            'goals', 'objectives', 'priority', 'decision', 'budget',
            'milestone', 'deadline', 'launch', 'product', 'customer'
        ]
        
        # Score based on keyword presence
        high_impact_count = sum(1 for keyword in high_impact_keywords if keyword in text)
        medium_impact_count = sum(1 for keyword in medium_impact_keywords if keyword in text)
        
        score += high_impact_count * 0.3
        score += medium_impact_count * 0.2
        
        # Boost score for longer, detailed messages
        if len(text) > 100:
            score += 0.2
        if len(text) > 300:
            score += 0.2
        
        # Boost score for messages with mentions (likely directed discussions)
        if '@' in text:
            score += 0.1
        
        # Boost score for messages with questions (likely strategic discussions)
        if '?' in text:
            score += 0.1
        
        return min(1.0, score)  # Cap at 1.0
    
    async def _process_channel_created(self, event_data: Dict) -> Optional[Dict]:
        """Process new channel creation"""
        channel = event_data.get('channel', {})
        channel_name = channel.get('name', '')
        creator = channel.get('creator')
        purpose = channel.get('purpose', {}).get('value', '')
        
        logger.info(f"📁 New Slack channel created: #{channel_name}")
        
        # Check if this is a strategic channel we should monitor
        if await self._should_monitor_channel(channel_name, purpose):
            self.monitored_channels.add(channel.get('id'))
            
            return {
                'new_channel': {
                    'name': channel_name,
                    'creator': creator,
                    'purpose': purpose,
                    'monitoring': True,
                    'strategic_relevance': await self._assess_channel_strategic_relevance(channel_name, purpose)
                }
            }
        
        return None
    
    async def _process_member_joined(self, event_data: Dict) -> Optional[Dict]:
        """Process member joining channel"""
        user = event_data.get('user')
        channel = event_data.get('channel')
        
        # If it's a strategic channel, this could be significant
        if channel in self.monitored_channels:
            try:
                channel_info = await self.slack_client.conversations_info(channel=channel)
                user_info = await self.slack_client.users_info(user=user)
                
                return {
                    'strategic_network_change': {
                        'type': 'member_joined_strategic_channel',
                        'user': user_info['user']['name'],
                        'user_email': user_info['user']['profile'].get('email'),
                        'channel': channel_info['channel']['name'],
                        'timestamp': datetime.utcnow().isoformat()
                    }
                }
            except Exception as e:
                logger.warning(f"⚠️ Failed to process member join: {e}")
        
        return None
    
    # Helper methods for strategic analysis
    async def _classify_strategic_discussion(self, messages: List[Dict]) -> str:
        """Classify the type of strategic discussion"""
        combined_text = ' '.join([msg.get('text', '') for msg in messages]).lower()
        
        if any(word in combined_text for word in ['roadmap', 'planning', 'timeline']):
            return 'strategic_planning'
        elif any(word in combined_text for word in ['decision', 'choose', 'decide']):
            return 'decision_making'
        elif any(word in combined_text for word in ['partnership', 'deal', 'agreement']):
            return 'partnership_discussion'
        elif any(word in combined_text for word in ['competitive', 'market', 'competitor']):
            return 'competitive_intelligence'
        else:
            return 'general_strategic'
    
    async def _extract_key_participants(self, messages: List[Dict]) -> List[Dict]:
        """Extract key participants from thread"""
        participants = {}
        
        for msg in messages:
            user = msg.get('user')
            if user and user not in participants:
                participants[user] = {
                    'user_id': user,
                    'message_count': 0,
                    'first_message': msg.get('ts'),
                    'last_message': msg.get('ts')
                }
            
            if user in participants:
                participants[user]['message_count'] += 1
                participants[user]['last_message'] = msg.get('ts')
        
        # Sort by message count (engagement level)
        return sorted(participants.values(), key=lambda x: x['message_count'], reverse=True)
    
    async def _extract_decisions(self, messages: List[Dict]) -> List[str]:
        """Extract decisions from thread"""
        decisions = []
        decision_keywords = ['decided', 'decision', 'we will', 'agreed', 'resolved']
        
        for msg in messages:
            text = msg.get('text', '').lower()
            for keyword in decision_keywords:
                if keyword in text:
                    decisions.append(text[:200])  # Capture decision context
                    break
        
        return decisions
    
    async def _extract_action_items(self, messages: List[Dict]) -> List[str]:
        """Extract action items from thread"""
        action_items = []
        action_keywords = ['todo', 'action item', 'will do', 'responsible', 'deadline', 'by when']
        
        for msg in messages:
            text = msg.get('text', '').lower()
            for keyword in action_keywords:
                if keyword in text:
                    action_items.append(text[:200])
                    break
        
        return action_items
    
    async def _extract_timeline_mentions(self, messages: List[Dict]) -> List[str]:
        """Extract timeline mentions from thread"""
        timelines = []
        timeline_keywords = ['by', 'deadline', 'timeline', 'schedule', 'date', 'when', 'month', 'week']
        
        for msg in messages:
            text = msg.get('text', '').lower()
            for keyword in timeline_keywords:
                if keyword in text:
                    timelines.append(text[:200])
                    break
        
        return timelines
    
    async def _extract_stakeholder_mentions(self, messages: List[Dict]) -> List[str]:
        """Extract stakeholder mentions from thread"""
        stakeholders = []
        
        for msg in messages:
            text = msg.get('text', '')
            # Look for @mentions and company names
            import re
            mentions = re.findall(r'<@(\w+)>', text)
            stakeholders.extend(mentions)
        
        return list(set(stakeholders))  # Remove duplicates
    
    async def _should_monitor_channel(self, channel_name: str, purpose: str) -> bool:
        """Determine if we should monitor this channel"""
        strategic_indicators = [
            'strategy', 'planning', 'exec', 'leadership', 'board',
            'roadmap', 'vision', 'goals', 'competitive', 'market'
        ]
        
        combined_text = (channel_name + ' ' + purpose).lower()
        return any(indicator in combined_text for indicator in strategic_indicators)
    
    async def _assess_channel_strategic_relevance(self, channel_name: str, purpose: str) -> float:
        """Assess strategic relevance score (0.0-1.0)"""
        strategic_words = ['strategy', 'exec', 'leadership', 'planning', 'roadmap']
        combined_text = (channel_name + ' ' + purpose).lower()
        
        relevance_score = 0.0
        for word in strategic_words:
            if word in combined_text:
                relevance_score += 0.2
        
        return min(1.0, relevance_score)

    async def _analyze_strategic_discussion(self, message_data: Dict) -> Dict:
        """Perform deeper analysis of strategic discussions"""
        
        channel = message_data.get('channel')
        thread_ts = message_data.get('thread_ts') or message_data.get('ts')
        
        # Get full thread context for strategic analysis
        thread_messages = []
        try:
            if thread_ts:
                response = await self.slack_client.conversations_replies(
                    channel=channel,
                    ts=thread_ts,
                    limit=50
                )
                thread_messages = response['messages']
                
        except Exception as e:
            logger.warning(f"⚠️ Failed to get thread context: {e}")
            thread_messages = [message_data]
        
        # Analyze thread for strategic insights
        strategic_analysis = {
            'discussion_type': await self._classify_strategic_discussion(thread_messages),
            'key_participants': await self._extract_key_participants(thread_messages),
            'decisions_made': await self._extract_decisions(thread_messages),
            'action_items': await self._extract_action_items(thread_messages),
            'timeline_mentions': await self._extract_timeline_mentions(thread_messages),
            'stakeholder_mentions': await self._extract_stakeholder_mentions(thread_messages)
        }
        
        return strategic_analysis
    
    async def _enrich_slack_message(self, message_data: Dict) -> Dict:
        """Enrich Slack message with additional context"""
        enriched = message_data.copy()
        
        channel_id = message_data.get('channel')
        user_id = message_data.get('user')
        
        try:
            # Get channel info
            if channel_id:
                channel_info = await self.slack_client.conversations_info(channel=channel_id)
                enriched['channel_name'] = channel_info['channel']['name']
                enriched['channel_purpose'] = channel_info['channel'].get('purpose', {}).get('value', '')
        
            # Get user info
            if user_id:
                user_info = await self.slack_client.users_info(user=user_id)
                enriched['user_name'] = user_info['user']['name']
                enriched['user_title'] = user_info['user']['profile'].get('title', '')
                enriched['user_email'] = user_info['user']['profile'].get('email', '')
                
        except Exception as e:
            logger.warning(f"⚠️ Failed to enrich Slack message context: {e}")
        
        return enriched
    
    async def _is_strategic_discussion(self, message_data: Dict) -> bool:
        """Determine if this message is part of a strategic discussion"""
        text = message_data.get('text', '').lower()
        channel_name = message_data.get('channel_name', '').lower()
        
        # Strategic keywords
        strategic_keywords = [
            'strategy', 'roadmap', 'vision', 'goals', 'objectives',
            'partnership', 'acquisition', 'funding', 'investment',
            'competitive', 'market', 'opportunity', 'threat',
            'decision', 'priority', 'budget', 'resource'
        ]
        
        # Strategic channels
        strategic_channels = [
            'leadership', 'strategy', 'exec', 'board', 'planning',
            'roadmap', 'vision', 'goals', 'executive'
        ]
        
        has_strategic_keywords = any(keyword in text for keyword in strategic_keywords)
        is_strategic_channel = any(channel in channel_name for channel in strategic_channels)
        
        return has_strategic_keywords or is_strategic_channel

# Webhook handler for Flask route
async def handle_slack_webhook(event_data: Dict, user_id: int) -> Optional[Dict]:
    """
    Handle incoming Slack webhook and process for knowledge updates
    
    Args:
        event_data: Slack event payload
        user_id: User ID for knowledge system
        
    Returns:
        Knowledge updates or None
    """
    try:
        # Initialize Slack integration (would be cached in production)
        slack_integration = SlackKnowledgeIntegration(user_id, SLACK_BOT_TOKEN)
        await slack_integration.initialize()
        
        # Process the event
        updates = await slack_integration.process_slack_event(event_data)
        
        if updates:
            logger.info(f"✅ Slack event processed with knowledge updates: {len(updates)} sections")
        else:
            logger.debug("💬 Slack event processed but no knowledge updates needed")
        
        return updates
        
    except Exception as e:
        logger.error(f"❌ Failed to process Slack webhook: {e}")
        return None 