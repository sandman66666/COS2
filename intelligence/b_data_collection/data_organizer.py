"""
Data Organization System
Multi-source content aggregation and lightweight organization before expensive strategic analysis.
Consolidates emails, Slack messages, documents and prepares clean summaries for Claude agents.
"""

import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict

from .communication_intelligence import CommunicationIntelligenceAnalyzer, CommunicationProfile

@dataclass
class ContentItem:
    id: str
    type: str  # "email", "slack", "document"
    source: str
    timestamp: datetime
    participants: List[str]
    subject: str
    content: str
    metadata: Dict
    topics: List[str] = None
    urgency_score: float = 0.0
    business_relevance: float = 0.0

@dataclass
class TopicCluster:
    name: str
    keywords: List[str]
    content_items: List[str]  # IDs
    participants: Set[str]
    timeline: Tuple[datetime, datetime]
    business_domain: str
    priority_score: float = 0.0

@dataclass
class OrganizedContent:
    topics: Dict[str, TopicCluster]
    communication_profiles: Dict[str, CommunicationProfile]
    content_index: Dict[str, ContentItem]
    business_domains: Dict[str, List[str]]  # domain -> topic names
    relationship_matrix: Dict[str, Dict[str, float]]  # contact -> contact -> strength
    temporal_timeline: List[Tuple[datetime, str, str]]  # (time, event_type, content_id)

class DataOrganizationSystem:
    def __init__(self):
        self.comm_analyzer = CommunicationIntelligenceAnalyzer()
        
        # Business domain keywords for categorization
        self.business_domains = {
            "ai_technology": ["ai", "artificial intelligence", "machine learning", "llm", "gpt", "claude", "model", "algorithm"],
            "music_industry": ["music", "audio", "sound", "artist", "song", "album", "streaming", "spotify", "licensing"],
            "venture_capital": ["funding", "investment", "series a", "series b", "vc", "venture", "equity", "valuation"],
            "legal_compliance": ["legal", "law", "contract", "agreement", "ip", "intellectual property", "copyright", "patent"],
            "business_development": ["partnership", "collaboration", "deal", "business", "revenue", "growth", "market"],
            "product_development": ["product", "feature", "development", "engineering", "technical", "api", "platform"],
            "marketing_sales": ["marketing", "sales", "customer", "user", "acquisition", "conversion", "campaign"],
            "finance_operations": ["finance", "accounting", "budget", "cost", "expense", "operations", "hr"]
        }
        
        # Topic extraction patterns
        self.topic_patterns = [
            r"project\s+(\w+)",
            r"(\w+)\s+integration",
            r"(\w+)\s+partnership",
            r"(\w+)\s+acquisition",
            r"(\w+)\s+launch",
            r"meeting\s+about\s+(\w+)",
            r"discussion\s+on\s+(\w+)"
        ]
        
        # Urgency indicators
        self.urgency_keywords = {
            "high": ["urgent", "asap", "immediate", "emergency", "critical", "deadline"],
            "medium": ["soon", "priority", "important", "needed", "follow up"],
            "low": ["fyi", "when possible", "eventually", "later"]
        }

    def organize_content(self, emails: List[Dict], slack_messages: List[Dict] = None, 
                        documents: List[Dict] = None) -> OrganizedContent:
        """
        Main orchestration method: organize all content sources into structured summaries
        """
        print("📊 Starting data organization phase...")
        
        # Step 1: Convert all content to standardized format
        content_items = self._standardize_content(emails, slack_messages or [], documents or [])
        print(f"📝 Standardized {len(content_items)} content items")
        
        # Step 2: Analyze communication patterns
        communication_profiles = self.comm_analyzer.analyze_email_thread(emails)
        print(f"🤝 Analyzed communication patterns for {len(communication_profiles)} contacts")
        
        # Step 3: Extract topics and themes
        topics = self._extract_topics(content_items)
        print(f"🏷️ Identified {len(topics)} topic clusters")
        
        # Step 4: Categorize by business domains
        business_domains = self._categorize_by_domains(topics)
        print(f"🏢 Categorized into {len(business_domains)} business domains")
        
        # Step 5: Build relationship matrix
        relationship_matrix = self._build_relationship_matrix(content_items, communication_profiles)
        print(f"🕸️ Built relationship matrix for {len(relationship_matrix)} contacts")
        
        # Step 6: Create temporal timeline
        timeline = self._create_temporal_timeline(content_items)
        print(f"⏰ Created timeline with {len(timeline)} events")
        
        # Step 7: Index content for fast lookup
        content_index = {item.id: item for item in content_items}
        
        organized_content = OrganizedContent(
            topics=topics,
            communication_profiles=communication_profiles,
            content_index=content_index,
            business_domains=business_domains,
            relationship_matrix=relationship_matrix,
            temporal_timeline=timeline
        )
        
        print("✅ Data organization phase complete!")
        return organized_content

    def _standardize_content(self, emails: List[Dict], slack_messages: List[Dict], 
                           documents: List[Dict]) -> List[ContentItem]:
        """Convert all content sources to standardized ContentItem format"""
        items = []
        
        # Process emails
        for email in emails:
            item = ContentItem(
                id=f"email_{email.get('id', len(items))}",
                type="email",
                source="gmail",
                timestamp=datetime.fromisoformat(email.get('created_at', datetime.now().isoformat())),
                participants=self._extract_participants(email),
                subject=email.get('subject', ''),
                content=email.get('content', ''),
                metadata={
                    'sender': email.get('sender', ''),
                    'recipients': email.get('recipients', []),
                    'thread_id': email.get('thread_id', ''),
                    'gmail_id': email.get('gmail_id', '')
                }
            )
            
            # Calculate urgency and business relevance
            item.urgency_score = self._calculate_urgency_score(item.content, item.subject)
            item.business_relevance = self._calculate_business_relevance(item.content, item.subject)
            item.topics = self._extract_content_topics(item.content, item.subject)
            
            items.append(item)
        
        # Process Slack messages (if provided)
        for message in slack_messages:
            item = ContentItem(
                id=f"slack_{message.get('id', len(items))}",
                type="slack",
                source="slack",
                timestamp=datetime.fromtimestamp(float(message.get('ts', 0))),
                participants=[message.get('user', '')],
                subject=f"#{message.get('channel', 'unknown')}",
                content=message.get('text', ''),
                metadata={
                    'channel': message.get('channel', ''),
                    'user': message.get('user', ''),
                    'thread_ts': message.get('thread_ts', '')
                }
            )
            
            item.urgency_score = self._calculate_urgency_score(item.content, item.subject)
            item.business_relevance = self._calculate_business_relevance(item.content, item.subject)
            item.topics = self._extract_content_topics(item.content, item.subject)
            
            items.append(item)
        
        # Process documents (if provided)
        for doc in documents:
            item = ContentItem(
                id=f"doc_{doc.get('id', len(items))}",
                type="document",
                source=doc.get('source', 'unknown'),
                timestamp=datetime.fromisoformat(doc.get('created_at', datetime.now().isoformat())),
                participants=doc.get('authors', []),
                subject=doc.get('title', ''),
                content=doc.get('content', ''),
                metadata={
                    'file_type': doc.get('file_type', ''),
                    'size': doc.get('size', 0),
                    'path': doc.get('path', '')
                }
            )
            
            item.urgency_score = self._calculate_urgency_score(item.content, item.subject)
            item.business_relevance = self._calculate_business_relevance(item.content, item.subject)
            item.topics = self._extract_content_topics(item.content, item.subject)
            
            items.append(item)
        
        return items

    def _extract_participants(self, email: Dict) -> List[str]:
        """Extract all participants from email"""
        participants = []
        
        sender = email.get('sender', '')
        if sender:
            participants.append(sender.lower())
        
        recipients = email.get('recipients', [])
        for recipient in recipients:
            if recipient and recipient.lower() not in participants:
                participants.append(recipient.lower())
        
        return participants

    def _calculate_urgency_score(self, content: str, subject: str) -> float:
        """Calculate urgency score (0-1) based on content and subject"""
        text = (content + " " + subject).lower()
        
        high_score = sum(2 for keyword in self.urgency_keywords["high"] if keyword in text)
        medium_score = sum(1 for keyword in self.urgency_keywords["medium"] if keyword in text)
        low_score = sum(-0.5 for keyword in self.urgency_keywords["low"] if keyword in text)
        
        total_score = high_score + medium_score + low_score
        
        # Normalize to 0-1 range
        return max(0, min(1, total_score / 5))

    def _calculate_business_relevance(self, content: str, subject: str) -> float:
        """Calculate business relevance score (0-1) based on content"""
        text = (content + " " + subject).lower()
        
        relevance_score = 0
        total_domains = 0
        
        for domain, keywords in self.business_domains.items():
            domain_score = sum(1 for keyword in keywords if keyword in text)
            if domain_score > 0:
                relevance_score += min(domain_score, 3)  # Cap per domain
                total_domains += 1
        
        # Base relevance + domain diversity bonus
        base_relevance = min(relevance_score / 10, 0.8)
        diversity_bonus = min(total_domains * 0.05, 0.2)
        
        return base_relevance + diversity_bonus

    def _extract_content_topics(self, content: str, subject: str) -> List[str]:
        """Extract topics from content using pattern matching"""
        text = content + " " + subject
        topics = []
        
        # Extract topics using regex patterns
        for pattern in self.topic_patterns:
            matches = re.findall(pattern, text.lower())
            topics.extend(matches)
        
        # Extract business domain topics
        for domain, keywords in self.business_domains.items():
            for keyword in keywords:
                if keyword in text.lower():
                    topics.append(keyword)
        
        # Remove duplicates and return top topics
        unique_topics = list(set(topics))
        return unique_topics[:5]  # Limit to top 5 topics per content

    def _extract_topics(self, content_items: List[ContentItem]) -> Dict[str, TopicCluster]:
        """Extract and cluster topics from all content"""
        topic_content = defaultdict(list)
        topic_participants = defaultdict(set)
        topic_timestamps = defaultdict(list)
        
        # Group content by topics
        for item in content_items:
            for topic in item.topics or []:
                topic_content[topic].append(item.id)
                topic_participants[topic].update(item.participants)
                topic_timestamps[topic].append(item.timestamp)
        
        # Create topic clusters
        topics = {}
        for topic_name, content_ids in topic_content.items():
            if len(content_ids) >= 2:  # Only topics with multiple mentions
                timestamps = topic_timestamps[topic_name]
                
                cluster = TopicCluster(
                    name=topic_name,
                    keywords=[topic_name],  # Can be expanded with related keywords
                    content_items=content_ids,
                    participants=topic_participants[topic_name],
                    timeline=(min(timestamps), max(timestamps)),
                    business_domain=self._classify_business_domain(topic_name),
                    priority_score=self._calculate_topic_priority(content_ids, content_items)
                )
                
                topics[topic_name] = cluster
        
        return topics

    def _classify_business_domain(self, topic: str) -> str:
        """Classify topic into business domain"""
        topic_lower = topic.lower()
        
        for domain, keywords in self.business_domains.items():
            if any(keyword in topic_lower for keyword in keywords):
                return domain
        
        return "general"

    def _calculate_topic_priority(self, content_ids: List[str], content_items: List[ContentItem]) -> float:
        """Calculate priority score for topic based on content characteristics"""
        relevant_items = [item for item in content_items if item.id in content_ids]
        
        if not relevant_items:
            return 0.0
        
        # Factors: recency, urgency, business relevance, participant count
        avg_urgency = sum(item.urgency_score for item in relevant_items) / len(relevant_items)
        avg_relevance = sum(item.business_relevance for item in relevant_items) / len(relevant_items)
        
        # Recency score (more recent = higher score)
        latest_timestamp = max(item.timestamp for item in relevant_items)
        days_old = (datetime.now() - latest_timestamp).days
        recency_score = max(0, 1 - (days_old / 30))  # Decay over 30 days
        
        # Participant diversity
        all_participants = set()
        for item in relevant_items:
            all_participants.update(item.participants)
        participant_score = min(len(all_participants) / 10, 1.0)
        
        # Combined priority score
        priority = (avg_urgency * 0.3 + avg_relevance * 0.3 + 
                   recency_score * 0.2 + participant_score * 0.2)
        
        return priority

    def _categorize_by_domains(self, topics: Dict[str, TopicCluster]) -> Dict[str, List[str]]:
        """Categorize topics by business domains"""
        domains = defaultdict(list)
        
        for topic_name, cluster in topics.items():
            domain = cluster.business_domain
            domains[domain].append(topic_name)
        
        return dict(domains)

    def _build_relationship_matrix(self, content_items: List[ContentItem], 
                                 communication_profiles: Dict[str, CommunicationProfile]) -> Dict[str, Dict[str, float]]:
        """Build relationship strength matrix between contacts"""
        matrix = defaultdict(lambda: defaultdict(float))
        
        # Use communication profiles for base relationship strength
        for email, profile in communication_profiles.items():
            matrix[email][email] = profile.engagement_score
        
        # Add co-occurrence relationships
        for item in content_items:
            participants = item.participants
            if len(participants) > 1:
                # Add relationship strength for participants in same conversation
                for i, participant1 in enumerate(participants):
                    for participant2 in participants[i+1:]:
                        # Weight by business relevance and recency
                        weight = item.business_relevance * 0.1
                        matrix[participant1][participant2] += weight
                        matrix[participant2][participant1] += weight
        
        return dict(matrix)

    def _create_temporal_timeline(self, content_items: List[ContentItem]) -> List[Tuple[datetime, str, str]]:
        """Create chronological timeline of events"""
        timeline = []
        
        for item in content_items:
            event_type = f"{item.type}_received" if item.type == "email" else f"{item.type}_activity"
            timeline.append((item.timestamp, event_type, item.id))
        
        # Sort by timestamp
        timeline.sort(key=lambda x: x[0])
        
        return timeline

    def get_summary_statistics(self, organized_content: OrganizedContent) -> Dict:
        """Generate summary statistics for organized content"""
        return {
            "total_content_items": len(organized_content.content_index),
            "total_topics": len(organized_content.topics),
            "total_contacts": len(organized_content.communication_profiles),
            "business_domains": len(organized_content.business_domains),
            "established_relationships": sum(1 for profile in organized_content.communication_profiles.values() 
                                           if profile.relationship_status.value in ["established", "ongoing"]),
            "attempted_relationships": sum(1 for profile in organized_content.communication_profiles.values() 
                                         if profile.relationship_status.value == "attempted"),
            "timeline_span_days": (organized_content.temporal_timeline[-1][0] - 
                                 organized_content.temporal_timeline[0][0]).days if organized_content.temporal_timeline else 0
        } 