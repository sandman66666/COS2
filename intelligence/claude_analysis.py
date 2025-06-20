# File: intelligence/claude_analysis.py
"""
Specialized Claude Opus 4 Analysts for Knowledge Tree Construction
================================================================
Multiple specialized AI analysts that process emails in parallel
"""

import asyncio
import anthropic
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import json
import logging
from config.settings import ANTHROPIC_API_KEY

logger = logging.getLogger(__name__)

@dataclass
class AnalysisResult:
    """Result from a specialized Claude analyst"""
    analyst_type: str
    insights: Dict
    confidence: float
    evidence: List[Dict]
    relationships: List[Dict]
    topics: List[str]
    entities: List[Dict]

class BaseClaudeAnalyst:
    """Base class for specialized Claude analysts"""
    
    def __init__(self, analyst_type: str, model: str = None):
        self.analyst_type = analyst_type
        self.model = model or "claude-3-opus-20240229"
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        
    async def analyze_emails(self, emails: List[Dict], context: Dict = None) -> AnalysisResult:
        """Analyze a batch of emails with specialized focus"""
        raise NotImplementedError("Subclasses must implement analyze_emails")
    
    def _prepare_email_context(self, emails: List[Dict]) -> str:
        """Prepare email context for Claude"""
        context_parts = []
        for email in emails[:50]:  # Limit to prevent token overflow
            context_parts.append(f"""
Email ID: {email.get('id')}
Date: {email.get('email_date')}
From: {email.get('sender')} 
To: {email.get('recipients')}
Subject: {email.get('subject')}
Body: {email.get('body_text', '')[:1000]}...
---
""")
        return "\n".join(context_parts)

class BusinessStrategyAnalyst(BaseClaudeAnalyst):
    """Analyzes emails for strategic business decisions and rationale"""
    
    def __init__(self):
        super().__init__("business_strategy")
        self.analysis_prompt = """You are an expert in strategic thinking and business worldview modeling. 

Your task is NOT to simply categorize business information, but to understand HOW this person thinks about business strategy and what their unique strategic philosophy reveals about their worldview.

Analyze these emails to understand:

1. STRATEGIC MENTAL MODELS: What frameworks do they use to think about business decisions?
2. VALUE CREATION PHILOSOPHY: How do they conceptualize value creation and business success?
3. RISK AND OPPORTUNITY LENS: How do they perceive and evaluate risks vs opportunities?
4. DECISION ARCHITECTURE: What factors consistently drive their strategic decisions?
5. COMPETITIVE WORLDVIEW: How do they think about competition, differentiation, and market positioning?
6. STAKEHOLDER PHILOSOPHY: How do they conceptualize relationships with customers, partners, employees?

Focus on understanding their UNIQUE perspective on business - the mental models and frameworks that make them distinctive. Look for the "why behind the why" in their strategic thinking.

For each insight, provide:
- The underlying belief or framework driving their approach
- How this manifests in their communications and decisions  
- What this reveals about their unique worldview
- Evidence from specific emails
- Confidence level and strategic significance

This should feel revelatory - like you understand their strategic DNA in a way that even they might find insightful."""

    async def analyze_emails(self, emails: List[Dict], context: Dict = None) -> AnalysisResult:
        """Extract strategic business intelligence"""
        try:
            email_context = self._prepare_email_context(emails)
            
            response = await asyncio.to_thread(
                self.client.messages.create,
                model=self.model,
                max_tokens=4000,
                temperature=0.3,
                messages=[{
                    "role": "user",
                    "content": f"{self.analysis_prompt}\n\nEmails to analyze:\n{email_context}"
                }]
            )
            
            # Parse Claude's response
            result = self._parse_analysis_response(response.content[0].text)
            
            return AnalysisResult(
                analyst_type=self.analyst_type,
                insights=result,
                confidence=0.85,
                evidence=self._extract_evidence(result, emails),
                relationships=result.get('key_relationships', []),
                topics=self._extract_topics(result),
                entities=self._extract_entities(result)
            )
            
        except Exception as e:
            logger.error(f"Business strategy analysis error: {str(e)}")
            return AnalysisResult(
                analyst_type=self.analyst_type,
                insights={},
                confidence=0.0,
                evidence=[],
                relationships=[],
                topics=[],
                entities=[]
            )
    
    def _parse_analysis_response(self, response_text: str) -> Dict:
        """Parse Claude's JSON response"""
        try:
            # Extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            
            # If no JSON, create structured response from text
            return {
                "strategic_mental_models": self._extract_section(response_text, "STRATEGIC MENTAL MODELS"),
                "value_creation_philosophy": self._extract_section(response_text, "VALUE CREATION PHILOSOPHY"),
                "risk_opportunity_lens": self._extract_section(response_text, "RISK AND OPPORTUNITY LENS"),
                "decision_architecture": self._extract_section(response_text, "DECISION ARCHITECTURE"),
                "competitive_worldview": self._extract_section(response_text, "COMPETITIVE WORLDVIEW"),
                "stakeholder_philosophy": self._extract_section(response_text, "STAKEHOLDER PHILOSOPHY"),
                "raw_analysis": response_text
            }
        except Exception as e:
            logger.error(f"Failed to parse business analysis response: {str(e)}")
            return {"raw_analysis": response_text}
    
    def _extract_section(self, text: str, section_name: str) -> str:
        """Extract a specific section from the response"""
        lines = text.split('\n')
        in_section = False
        section_content = []
        
        for line in lines:
            if section_name.lower() in line.lower():
                in_section = True
                continue
            elif in_section and any(keyword in line.lower() for keyword in ['mental models', 'philosophy', 'lens', 'architecture', 'worldview']):
                break
            elif in_section:
                section_content.append(line)
        
        return '\n'.join(section_content).strip()
    
    def _extract_evidence(self, insights: Dict, emails: List[Dict]) -> List[Dict]:
        """Extract supporting evidence from emails"""
        evidence = []
        
        # Extract key terms from insights for searching
        search_terms = []
        for category, content in insights.items():
            if isinstance(content, str):
                # Extract significant words (length > 3, not common words)
                words = [word.strip('.,!?;:').lower() for word in content.split() 
                        if len(word) > 3 and word.lower() not in ['this', 'that', 'with', 'from', 'they', 'them', 'will', 'have', 'been', 'were', 'was']]
                search_terms.extend(words[:5])  # Top 5 words per category
        
        # Search for evidence in emails
        for email in emails[:20]:  # Check first 20 emails for performance
            email_content = f"{email.get('subject', '')} {email.get('body_text', '')}"
            email_content_lower = email_content.lower()
            
            # Count matches
            matches = sum(1 for term in search_terms if term in email_content_lower)
            
            if matches > 0:
                # Extract relevant excerpt
                sentences = email_content.split('.')
                relevant_sentences = []
                for sentence in sentences:
                    if any(term in sentence.lower() for term in search_terms):
                        relevant_sentences.append(sentence.strip())
                        if len(relevant_sentences) >= 2:  # Max 2 sentences
                            break
                
                evidence.append({
                    'email_id': email.get('id'),
                    'date': email.get('email_date'),
                    'sender': email.get('sender'),
                    'subject': email.get('subject'),
                    'excerpt': '. '.join(relevant_sentences)[:200] + '...' if len('. '.join(relevant_sentences)) > 200 else '. '.join(relevant_sentences),
                    'relevance_score': matches / len(search_terms) if search_terms else 0,
                    'match_count': matches
                })
        
        # Sort by relevance and return top 5
        evidence.sort(key=lambda x: x['relevance_score'], reverse=True)
        return evidence[:5]
    
    def _extract_topics(self, insights: Dict) -> List[str]:
        """Extract key topics from insights"""
        topics = set()
        
        for category, content in insights.items():
            # Add category as topic
            topics.add(category.replace('_', ' ').title())
            
            if isinstance(content, str):
                # Extract potential topics from content
                words = content.split()
                for i, word in enumerate(words):
                    word = word.strip('.,!?;:').lower()
                    if len(word) > 4:  # Longer words more likely to be topics
                        topics.add(word.title())
                    
                    # Look for capitalized words/phrases that might be topics
                    if word[0].isupper() and len(word) > 3:
                        topics.add(word)
                        
                    # Look for phrases (adjacent capitalized words)
                    if i < len(words) - 1:
                        next_word = words[i + 1].strip('.,!?;:')
                        if word[0].isupper() and next_word and next_word[0].isupper():
                            topics.add(f"{word} {next_word}")
            
            elif isinstance(content, list):
                for item in content:
                    if isinstance(item, dict):
                        for key, value in item.items():
                            topics.add(key.replace('_', ' ').title())
                            if isinstance(value, str) and len(value.split()) <= 3:
                                topics.add(value)
                    elif isinstance(item, str):
                        topics.add(item)
        
        # Filter out very common words and return list
        common_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'between', 'among'}
        filtered_topics = [topic for topic in topics if topic.lower() not in common_words and len(topic) > 2]
        
        return list(set(filtered_topics))[:20]  # Return top 20 unique topics
    
    def _extract_entities(self, insights: Dict) -> List[Dict]:
        """Extract entities (people, companies, projects) from insights"""
        entities = []
        
        for category, content in insights.items():
            if isinstance(content, str):
                # Look for patterns that might be entities
                words = content.split()
                
                for i, word in enumerate(words):
                    word_clean = word.strip('.,!?;:')
                    
                    # Look for capitalized words (potential proper nouns)
                    if word_clean and word_clean[0].isupper() and len(word_clean) > 2:
                        entity_type = "unknown"
                        
                        # Try to classify entity type based on context
                        context = ' '.join(words[max(0, i-2):i+3]).lower()
                        
                        if any(indicator in context for indicator in ['company', 'corp', 'inc', 'ltd', 'llc', 'organization']):
                            entity_type = "company"
                        elif any(indicator in context for indicator in ['project', 'initiative', 'program', 'system', 'platform']):
                            entity_type = "project"
                        elif any(indicator in context for indicator in ['person', 'team', 'manager', 'director', 'ceo', 'cto']):
                            entity_type = "person"
                        elif word_clean.endswith(('.com', '.org', '.net', '.io')):
                            entity_type = "website"
                        elif '@' in word_clean:
                            entity_type = "email"
                        
                        entities.append({
                            'name': word_clean,
                            'type': entity_type,
                            'context': context,
                            'source_category': category,
                            'confidence': 0.7 if entity_type != "unknown" else 0.3
                        })
                
                # Look for email addresses
                import re
                email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                emails_found = re.findall(email_pattern, content)
                for email in emails_found:
                    entities.append({
                        'name': email,
                        'type': 'email',
                        'context': content[max(0, content.find(email)-50):content.find(email)+50],
                        'source_category': category,
                        'confidence': 0.9
                    })
                
                # Look for URLs
                url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
                urls_found = re.findall(url_pattern, content)
                for url in urls_found:
                    entities.append({
                        'name': url,
                        'type': 'url',
                        'context': content[max(0, content.find(url)-50):content.find(url)+50],
                        'source_category': category,
                        'confidence': 0.9
                    })
        
        # Deduplicate entities by name and return top 10
        seen_names = set()
        unique_entities = []
        for entity in entities:
            if entity['name'].lower() not in seen_names:
                seen_names.add(entity['name'].lower())
                unique_entities.append(entity)
                if len(unique_entities) >= 10:
                    break
        
        return unique_entities

class RelationshipDynamicsAnalyst(BaseClaudeAnalyst):
    """Maps relationship dynamics and influence patterns"""
    
    def __init__(self):
        super().__init__("relationship_dynamics")
        self.analysis_prompt = """You are an expert in interpersonal dynamics and relationship intelligence. 

Your task is NOT to simply map who talks to whom, but to understand this person's RELATIONSHIP PHILOSOPHY and how they think about human connections.

Analyze these emails to understand:

1. RELATIONSHIP MENTAL MODEL: How do they conceptualize professional relationships and their purpose?
2. INFLUENCE PHILOSOPHY: How do they think about influence, persuasion, and social dynamics?
3. TRUST ARCHITECTURE: How do they build, maintain, and leverage trust?
4. COMMUNICATION PATTERNS: What do their communication styles reveal about their relationship approach?
5. NETWORK STRATEGY: How do they think about building and maintaining their professional network?
6. COLLABORATION WORLDVIEW: What are their beliefs about teamwork, leadership, and collaboration?

Focus on understanding their unique approach to relationships - the underlying beliefs and frameworks that guide how they connect with others.

Look for:
- Patterns in how they build rapport and establish connections
- Their approach to managing different types of relationships
- How they handle conflict, disagreement, or difficult conversations
- What they prioritize in professional relationships
- How they leverage relationships for mutual value creation

This should reveal their "relationship DNA" - the core principles that guide how they think about and manage human connections."""

    async def analyze_emails(self, emails: List[Dict], context: Dict = None) -> AnalysisResult:
        """Map relationship dynamics and influence patterns"""
        try:
            email_context = self._prepare_email_context(emails)
            
            response = await asyncio.to_thread(
                self.client.messages.create,
                model=self.model,
                max_tokens=4000,
                temperature=0.25,
                messages=[{
                    "role": "user",
                    "content": f"{self.analysis_prompt}\n\nEmails to analyze:\n{email_context}"
                }]
            )
            
            # Parse Claude's response
            result = self._parse_relationship_response(response.content[0].text)
            
            return AnalysisResult(
                analyst_type=self.analyst_type,
                insights=result,
                confidence=0.85,
                evidence=self._extract_evidence(result, emails),
                relationships=result.get('relationship_networks', []),
                topics=self._extract_topics(result),
                entities=self._extract_entities(result)
            )
            
        except Exception as e:
            logger.error(f"Relationship dynamics analysis error: {str(e)}")
            return AnalysisResult(
                analyst_type=self.analyst_type,
                insights={},
                confidence=0.0,
                evidence=[],
                relationships=[],
                topics=[],
                entities=[]
            )
    
    def _parse_relationship_response(self, response_text: str) -> Dict:
        """Parse relationship analysis response"""
        return {
            "relationship_mental_model": self._extract_section(response_text, "RELATIONSHIP MENTAL MODEL"),
            "influence_philosophy": self._extract_section(response_text, "INFLUENCE PHILOSOPHY"),
            "trust_architecture": self._extract_section(response_text, "TRUST ARCHITECTURE"),
            "communication_patterns": self._extract_section(response_text, "COMMUNICATION PATTERNS"),
            "network_strategy": self._extract_section(response_text, "NETWORK STRATEGY"),
            "collaboration_worldview": self._extract_section(response_text, "COLLABORATION WORLDVIEW"),
            "raw_analysis": response_text
        }
    
    def _extract_section(self, text: str, section_name: str) -> str:
        """Extract a specific section from the response"""
        lines = text.split('\n')
        in_section = False
        section_content = []
        
        for line in lines:
            if section_name.lower() in line.lower():
                in_section = True
                continue
            elif in_section and any(keyword in line.lower() for keyword in ['mental model', 'philosophy', 'architecture', 'patterns', 'strategy', 'worldview']):
                break
            elif in_section:
                section_content.append(line)
        
        return '\n'.join(section_content).strip()
    
    def _extract_evidence(self, insights: Dict, emails: List[Dict]) -> List[Dict]:
        """Extract supporting evidence from emails"""
        evidence = []
        
        # Extract key terms from insights for searching
        search_terms = []
        for category, content in insights.items():
            if isinstance(content, str):
                # Extract significant words (length > 3, not common words)
                words = [word.strip('.,!?;:').lower() for word in content.split() 
                        if len(word) > 3 and word.lower() not in ['this', 'that', 'with', 'from', 'they', 'them', 'will', 'have', 'been', 'were', 'was']]
                search_terms.extend(words[:5])  # Top 5 words per category
        
        # Search for evidence in emails
        for email in emails[:20]:  # Check first 20 emails for performance
            email_content = f"{email.get('subject', '')} {email.get('body_text', '')}"
            email_content_lower = email_content.lower()
            
            # Count matches
            matches = sum(1 for term in search_terms if term in email_content_lower)
            
            if matches > 0:
                # Extract relevant excerpt
                sentences = email_content.split('.')
                relevant_sentences = []
                for sentence in sentences:
                    if any(term in sentence.lower() for term in search_terms):
                        relevant_sentences.append(sentence.strip())
                        if len(relevant_sentences) >= 2:  # Max 2 sentences
                            break
                
                evidence.append({
                    'email_id': email.get('id'),
                    'date': email.get('email_date'),
                    'sender': email.get('sender'),
                    'subject': email.get('subject'),
                    'excerpt': '. '.join(relevant_sentences)[:200] + '...' if len('. '.join(relevant_sentences)) > 200 else '. '.join(relevant_sentences),
                    'relevance_score': matches / len(search_terms) if search_terms else 0,
                    'match_count': matches
                })
        
        # Sort by relevance and return top 5
        evidence.sort(key=lambda x: x['relevance_score'], reverse=True)
        return evidence[:5]
    
    def _extract_topics(self, insights: Dict) -> List[str]:
        """Extract key topics from insights"""
        topics = set()
        
        for category, content in insights.items():
            # Add category as topic
            topics.add(category.replace('_', ' ').title())
            
            if isinstance(content, str):
                # Extract potential topics from content
                words = content.split()
                for i, word in enumerate(words):
                    word = word.strip('.,!?;:').lower()
                    if len(word) > 4:  # Longer words more likely to be topics
                        topics.add(word.title())
                    
                    # Look for capitalized words/phrases that might be topics
                    if word[0].isupper() and len(word) > 3:
                        topics.add(word)
                        
                    # Look for phrases (adjacent capitalized words)
                    if i < len(words) - 1:
                        next_word = words[i + 1].strip('.,!?;:')
                        if word[0].isupper() and next_word and next_word[0].isupper():
                            topics.add(f"{word} {next_word}")
            
            elif isinstance(content, list):
                for item in content:
                    if isinstance(item, dict):
                        for key, value in item.items():
                            topics.add(key.replace('_', ' ').title())
                            if isinstance(value, str) and len(value.split()) <= 3:
                                topics.add(value)
                    elif isinstance(item, str):
                        topics.add(item)
        
        # Filter out very common words and return list
        common_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'between', 'among'}
        filtered_topics = [topic for topic in topics if topic.lower() not in common_words and len(topic) > 2]
        
        return list(set(filtered_topics))[:20]  # Return top 20 unique topics
    
    def _extract_entities(self, insights: Dict) -> List[Dict]:
        """Extract entities (people, companies, projects) from insights"""
        entities = []
        
        for category, content in insights.items():
            if isinstance(content, str):
                # Look for patterns that might be entities
                words = content.split()
                
                for i, word in enumerate(words):
                    word_clean = word.strip('.,!?;:')
                    
                    # Look for capitalized words (potential proper nouns)
                    if word_clean and word_clean[0].isupper() and len(word_clean) > 2:
                        entity_type = "unknown"
                        
                        # Try to classify entity type based on context
                        context = ' '.join(words[max(0, i-2):i+3]).lower()
                        
                        if any(indicator in context for indicator in ['company', 'corp', 'inc', 'ltd', 'llc', 'organization']):
                            entity_type = "company"
                        elif any(indicator in context for indicator in ['project', 'initiative', 'program', 'system', 'platform']):
                            entity_type = "project"
                        elif any(indicator in context for indicator in ['person', 'team', 'manager', 'director', 'ceo', 'cto']):
                            entity_type = "person"
                        elif word_clean.endswith(('.com', '.org', '.net', '.io')):
                            entity_type = "website"
                        elif '@' in word_clean:
                            entity_type = "email"
                        
                        entities.append({
                            'name': word_clean,
                            'type': entity_type,
                            'context': context,
                            'source_category': category,
                            'confidence': 0.7 if entity_type != "unknown" else 0.3
                        })
                
                # Look for email addresses
                import re
                email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                emails_found = re.findall(email_pattern, content)
                for email in emails_found:
                    entities.append({
                        'name': email,
                        'type': 'email',
                        'context': content[max(0, content.find(email)-50):content.find(email)+50],
                        'source_category': category,
                        'confidence': 0.9
                    })
                
                # Look for URLs
                url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
                urls_found = re.findall(url_pattern, content)
                for url in urls_found:
                    entities.append({
                        'name': url,
                        'type': 'url',
                        'context': content[max(0, content.find(url)-50):content.find(url)+50],
                        'source_category': category,
                        'confidence': 0.9
                    })
        
        # Deduplicate entities by name and return top 10
        seen_names = set()
        unique_entities = []
        for entity in entities:
            if entity['name'].lower() not in seen_names:
                seen_names.add(entity['name'].lower())
                unique_entities.append(entity)
                if len(unique_entities) >= 10:
                    break
        
        return unique_entities

class TechnicalEvolutionAnalyst(BaseClaudeAnalyst):
    """Tracks technical decisions and architecture evolution"""
    
    def __init__(self):
        super().__init__("technical_evolution")
        self.analysis_prompt = """You are an expert in technical thinking and technology philosophy.

Your task is NOT to simply catalog technical decisions, but to understand this person's TECHNICAL WORLDVIEW and how they think about technology's role in solving problems.

Analyze these emails to understand:

1. TECHNICAL PHILOSOPHY: What are their core beliefs about technology and its role?
2. PROBLEM-SOLVING APPROACH: How do they approach technical challenges and solution design?
3. INNOVATION MINDSET: How do they think about new technologies, adoption, and risk?
4. ARCHITECTURE THINKING: What principles guide their technical architecture decisions?
5. TECHNOLOGY LEADERSHIP: How do they think about leading technical teams and decisions?
6. TECHNICAL STRATEGY: How do they connect technical choices to business outcomes?

Focus on understanding their unique technical perspective - the mental models and principles that make their technical approach distinctive.

Look for:
- Patterns in how they evaluate and adopt new technologies
- Their approach to balancing innovation with stability
- How they think about technical debt and long-term architecture
- Their philosophy on technical team management and culture
- How they connect technical decisions to business strategy

This should reveal their "technical DNA" - the core frameworks that guide their technology thinking."""

    async def analyze_emails(self, emails: List[Dict], context: Dict = None) -> AnalysisResult:
        """Extract technical decisions and evolution patterns"""
        try:
            email_context = self._prepare_email_context(emails)
            
            response = await asyncio.to_thread(
                self.client.messages.create,
                model=self.model,
                max_tokens=4000,
                temperature=0.2,
                messages=[{
                    "role": "user",
                    "content": f"{self.analysis_prompt}\n\nEmails to analyze:\n{email_context}"
                }]
            )
            
            # Parse Claude's response
            result = self._parse_technical_response(response.content[0].text)
            
            return AnalysisResult(
                analyst_type=self.analyst_type,
                insights=result,
                confidence=0.85,
                evidence=self._extract_evidence(result, emails),
                relationships=result.get('technical_relationships', []),
                topics=self._extract_topics(result),
                entities=self._extract_entities(result)
            )
            
        except Exception as e:
            logger.error(f"Technical evolution analysis error: {str(e)}")
            return AnalysisResult(
                analyst_type=self.analyst_type,
                insights={},
                confidence=0.0,
                evidence=[],
                relationships=[],
                topics=[],
                entities=[]
            )
    
    def _parse_technical_response(self, response_text: str) -> Dict:
        """Parse technical analysis response"""
        try:
            # Try to extract JSON if present
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        # Fallback to structured response
        return {
            "technical_philosophy": self._extract_section(response_text, "TECHNICAL PHILOSOPHY"),
            "problem_solving_approach": self._extract_section(response_text, "PROBLEM-SOLVING APPROACH"),
            "innovation_mindset": self._extract_section(response_text, "INNOVATION MINDSET"),
            "architecture_thinking": self._extract_section(response_text, "ARCHITECTURE THINKING"),
            "technology_leadership": self._extract_section(response_text, "TECHNOLOGY LEADERSHIP"),
            "technical_strategy": self._extract_section(response_text, "TECHNICAL STRATEGY"),
            "raw_analysis": response_text
        }
    
    def _extract_section(self, text: str, section_name: str) -> str:
        """Extract a specific section from the response"""
        lines = text.split('\n')
        in_section = False
        section_content = []
        
        for line in lines:
            if section_name.lower() in line.lower():
                in_section = True
                continue
            elif in_section and any(keyword in line.lower() for keyword in ['philosophy', 'approach', 'mindset', 'thinking', 'leadership', 'strategy']):
                break
            elif in_section:
                section_content.append(line)
        
        return '\n'.join(section_content).strip()
    
    def _extract_evidence(self, insights: Dict, emails: List[Dict]) -> List[Dict]:
        """Extract supporting evidence from emails"""
        evidence = []
        
        # Extract key terms from insights for searching
        search_terms = []
        for category, content in insights.items():
            if isinstance(content, str):
                # Extract significant words (length > 3, not common words)
                words = [word.strip('.,!?;:').lower() for word in content.split() 
                        if len(word) > 3 and word.lower() not in ['this', 'that', 'with', 'from', 'they', 'them', 'will', 'have', 'been', 'were', 'was']]
                search_terms.extend(words[:5])  # Top 5 words per category
        
        # Search for evidence in emails
        for email in emails[:20]:  # Check first 20 emails for performance
            email_content = f"{email.get('subject', '')} {email.get('body_text', '')}"
            email_content_lower = email_content.lower()
            
            # Count matches
            matches = sum(1 for term in search_terms if term in email_content_lower)
            
            if matches > 0:
                # Extract relevant excerpt
                sentences = email_content.split('.')
                relevant_sentences = []
                for sentence in sentences:
                    if any(term in sentence.lower() for term in search_terms):
                        relevant_sentences.append(sentence.strip())
                        if len(relevant_sentences) >= 2:  # Max 2 sentences
                            break
                
                evidence.append({
                    'email_id': email.get('id'),
                    'date': email.get('email_date'),
                    'sender': email.get('sender'),
                    'subject': email.get('subject'),
                    'excerpt': '. '.join(relevant_sentences)[:200] + '...' if len('. '.join(relevant_sentences)) > 200 else '. '.join(relevant_sentences),
                    'relevance_score': matches / len(search_terms) if search_terms else 0,
                    'match_count': matches
                })
        
        # Sort by relevance and return top 5
        evidence.sort(key=lambda x: x['relevance_score'], reverse=True)
        return evidence[:5]
    
    def _extract_topics(self, insights: Dict) -> List[str]:
        """Extract key topics from insights"""
        topics = set()
        
        for category, content in insights.items():
            # Add category as topic
            topics.add(category.replace('_', ' ').title())
            
            if isinstance(content, str):
                # Extract potential topics from content
                words = content.split()
                for i, word in enumerate(words):
                    word = word.strip('.,!?;:').lower()
                    if len(word) > 4:  # Longer words more likely to be topics
                        topics.add(word.title())
                    
                    # Look for capitalized words/phrases that might be topics
                    if word[0].isupper() and len(word) > 3:
                        topics.add(word)
                        
                    # Look for phrases (adjacent capitalized words)
                    if i < len(words) - 1:
                        next_word = words[i + 1].strip('.,!?;:')
                        if word[0].isupper() and next_word and next_word[0].isupper():
                            topics.add(f"{word} {next_word}")
            
            elif isinstance(content, list):
                for item in content:
                    if isinstance(item, dict):
                        for key, value in item.items():
                            topics.add(key.replace('_', ' ').title())
                            if isinstance(value, str) and len(value.split()) <= 3:
                                topics.add(value)
                    elif isinstance(item, str):
                        topics.add(item)
        
        # Filter out very common words and return list
        common_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'between', 'among'}
        filtered_topics = [topic for topic in topics if topic.lower() not in common_words and len(topic) > 2]
        
        return list(set(filtered_topics))[:20]  # Return top 20 unique topics
    
    def _extract_entities(self, insights: Dict) -> List[Dict]:
        """Extract entities (people, companies, projects) from insights"""
        entities = []
        
        for category, content in insights.items():
            if isinstance(content, str):
                # Look for patterns that might be entities
                words = content.split()
                
                for i, word in enumerate(words):
                    word_clean = word.strip('.,!?;:')
                    
                    # Look for capitalized words (potential proper nouns)
                    if word_clean and word_clean[0].isupper() and len(word_clean) > 2:
                        entity_type = "unknown"
                        
                        # Try to classify entity type based on context
                        context = ' '.join(words[max(0, i-2):i+3]).lower()
                        
                        if any(indicator in context for indicator in ['company', 'corp', 'inc', 'ltd', 'llc', 'organization']):
                            entity_type = "company"
                        elif any(indicator in context for indicator in ['project', 'initiative', 'program', 'system', 'platform']):
                            entity_type = "project"
                        elif any(indicator in context for indicator in ['person', 'team', 'manager', 'director', 'ceo', 'cto']):
                            entity_type = "person"
                        elif word_clean.endswith(('.com', '.org', '.net', '.io')):
                            entity_type = "website"
                        elif '@' in word_clean:
                            entity_type = "email"
                        
                        entities.append({
                            'name': word_clean,
                            'type': entity_type,
                            'context': context,
                            'source_category': category,
                            'confidence': 0.7 if entity_type != "unknown" else 0.3
                        })
                
                # Look for email addresses
                import re
                email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                emails_found = re.findall(email_pattern, content)
                for email in emails_found:
                    entities.append({
                        'name': email,
                        'type': 'email',
                        'context': content[max(0, content.find(email)-50):content.find(email)+50],
                        'source_category': category,
                        'confidence': 0.9
                    })
                
                # Look for URLs
                url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
                urls_found = re.findall(url_pattern, content)
                for url in urls_found:
                    entities.append({
                        'name': url,
                        'type': 'url',
                        'context': content[max(0, content.find(url)-50):content.find(url)+50],
                        'source_category': category,
                        'confidence': 0.9
                    })
        
        # Deduplicate entities by name and return top 10
        seen_names = set()
        unique_entities = []
        for entity in entities:
            if entity['name'].lower() not in seen_names:
                seen_names.add(entity['name'].lower())
                unique_entities.append(entity)
                if len(unique_entities) >= 10:
                    break
        
        return unique_entities

class MarketIntelligenceAnalyst(BaseClaudeAnalyst):
    """Identifies market signals and competitive intelligence"""
    
    def __init__(self):
        super().__init__("market_intelligence")
        self.analysis_prompt = """You are an expert in market thinking and competitive worldview modeling.

Your task is NOT to simply identify market trends, but to understand this person's MARKET PHILOSOPHY and how they think about competitive dynamics and opportunity creation.

Analyze these emails to understand:

1. MARKET WORLDVIEW: How do they conceptualize markets, competition, and value creation?
2. OPPORTUNITY RECOGNITION: What patterns do they use to identify and evaluate opportunities?
3. COMPETITIVE INTELLIGENCE: How do they think about competitors and competitive advantage?
4. CUSTOMER PHILOSOPHY: What are their beliefs about customer needs and behavior?
5. TIMING AND MARKET DYNAMICS: How do they think about market timing and momentum?
6. STRATEGIC POSITIONING: How do they approach market positioning and differentiation?

Focus on understanding their unique market perspective - the mental models and frameworks that guide their market thinking.

Look for:
- Patterns in how they identify and evaluate market opportunities
- Their approach to competitive analysis and strategy
- How they think about customer segments and needs
- Their philosophy on market timing and entry strategies
- How they connect market insights to strategic decisions

This should reveal their "market DNA" - the core frameworks that guide their market intelligence and strategic thinking."""

    async def analyze_emails(self, emails: List[Dict], context: Dict = None) -> AnalysisResult:
        """Extract market intelligence and opportunities"""
        try:
            email_context = self._prepare_email_context(emails)
            
            response = await asyncio.to_thread(
                self.client.messages.create,
                model=self.model,
                max_tokens=4000,
                temperature=0.2,
                messages=[{
                    "role": "user",
                    "content": f"{self.analysis_prompt}\n\nEmails to analyze:\n{email_context}"
                }]
            )
            
            # Parse Claude's response
            result = self._parse_market_response(response.content[0].text)
            
            return AnalysisResult(
                analyst_type=self.analyst_type,
                insights=result,
                confidence=0.85,
                evidence=self._extract_evidence(result, emails),
                relationships=result.get('market_relationships', []),
                topics=self._extract_topics(result),
                entities=self._extract_entities(result)
            )
            
        except Exception as e:
            logger.error(f"Market intelligence analysis error: {str(e)}")
            return AnalysisResult(
                analyst_type=self.analyst_type,
                insights={},
                confidence=0.0,
                evidence=[],
                relationships=[],
                topics=[],
                entities=[]
            )
    
    def _parse_market_response(self, response_text: str) -> Dict:
        """Parse market analysis response"""
        try:
            # Try to extract JSON if present
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        # Fallback to structured response
        return {
            "market_worldview": self._extract_section(response_text, "MARKET WORLDVIEW"),
            "opportunity_recognition": self._extract_section(response_text, "OPPORTUNITY RECOGNITION"),
            "competitive_intelligence": self._extract_section(response_text, "COMPETITIVE INTELLIGENCE"),
            "customer_philosophy": self._extract_section(response_text, "CUSTOMER PHILOSOPHY"),
            "timing_market_dynamics": self._extract_section(response_text, "TIMING AND MARKET DYNAMICS"),
            "strategic_positioning": self._extract_section(response_text, "STRATEGIC POSITIONING"),
            "raw_analysis": response_text
        }
    
    def _extract_section(self, text: str, section_name: str) -> str:
        """Extract a specific section from the response"""
        lines = text.split('\n')
        in_section = False
        section_content = []
        
        for line in lines:
            if section_name.lower() in line.lower():
                in_section = True
                continue
            elif in_section and any(keyword in line.lower() for keyword in ['worldview', 'recognition', 'intelligence', 'philosophy', 'dynamics', 'positioning']):
                break
            elif in_section:
                section_content.append(line)
        
        return '\n'.join(section_content).strip()
    
    def _extract_evidence(self, insights: Dict, emails: List[Dict]) -> List[Dict]:
        """Extract supporting evidence from emails"""
        evidence = []
        
        # Extract key terms from insights for searching
        search_terms = []
        for category, content in insights.items():
            if isinstance(content, str):
                # Extract significant words (length > 3, not common words)
                words = [word.strip('.,!?;:').lower() for word in content.split() 
                        if len(word) > 3 and word.lower() not in ['this', 'that', 'with', 'from', 'they', 'them', 'will', 'have', 'been', 'were', 'was']]
                search_terms.extend(words[:5])  # Top 5 words per category
        
        # Search for evidence in emails
        for email in emails[:20]:  # Check first 20 emails for performance
            email_content = f"{email.get('subject', '')} {email.get('body_text', '')}"
            email_content_lower = email_content.lower()
            
            # Count matches
            matches = sum(1 for term in search_terms if term in email_content_lower)
            
            if matches > 0:
                # Extract relevant excerpt
                sentences = email_content.split('.')
                relevant_sentences = []
                for sentence in sentences:
                    if any(term in sentence.lower() for term in search_terms):
                        relevant_sentences.append(sentence.strip())
                        if len(relevant_sentences) >= 2:  # Max 2 sentences
                            break
                
                evidence.append({
                    'email_id': email.get('id'),
                    'date': email.get('email_date'),
                    'sender': email.get('sender'),
                    'subject': email.get('subject'),
                    'excerpt': '. '.join(relevant_sentences)[:200] + '...' if len('. '.join(relevant_sentences)) > 200 else '. '.join(relevant_sentences),
                    'relevance_score': matches / len(search_terms) if search_terms else 0,
                    'match_count': matches
                })
        
        # Sort by relevance and return top 5
        evidence.sort(key=lambda x: x['relevance_score'], reverse=True)
        return evidence[:5]
    
    def _extract_topics(self, insights: Dict) -> List[str]:
        """Extract key topics from insights"""
        topics = set()
        
        for category, content in insights.items():
            # Add category as topic
            topics.add(category.replace('_', ' ').title())
            
            if isinstance(content, str):
                # Extract potential topics from content
                words = content.split()
                for i, word in enumerate(words):
                    word = word.strip('.,!?;:').lower()
                    if len(word) > 4:  # Longer words more likely to be topics
                        topics.add(word.title())
                    
                    # Look for capitalized words/phrases that might be topics
                    if word[0].isupper() and len(word) > 3:
                        topics.add(word)
                        
                    # Look for phrases (adjacent capitalized words)
                    if i < len(words) - 1:
                        next_word = words[i + 1].strip('.,!?;:')
                        if word[0].isupper() and next_word and next_word[0].isupper():
                            topics.add(f"{word} {next_word}")
            
            elif isinstance(content, list):
                for item in content:
                    if isinstance(item, dict):
                        for key, value in item.items():
                            topics.add(key.replace('_', ' ').title())
                            if isinstance(value, str) and len(value.split()) <= 3:
                                topics.add(value)
                    elif isinstance(item, str):
                        topics.add(item)
        
        # Filter out very common words and return list
        common_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'between', 'among'}
        filtered_topics = [topic for topic in topics if topic.lower() not in common_words and len(topic) > 2]
        
        return list(set(filtered_topics))[:20]  # Return top 20 unique topics
    
    def _extract_entities(self, insights: Dict) -> List[Dict]:
        """Extract entities (people, companies, projects) from insights"""
        entities = []
        
        for category, content in insights.items():
            if isinstance(content, str):
                # Look for patterns that might be entities
                words = content.split()
                
                for i, word in enumerate(words):
                    word_clean = word.strip('.,!?;:')
                    
                    # Look for capitalized words (potential proper nouns)
                    if word_clean and word_clean[0].isupper() and len(word_clean) > 2:
                        entity_type = "unknown"
                        
                        # Try to classify entity type based on context
                        context = ' '.join(words[max(0, i-2):i+3]).lower()
                        
                        if any(indicator in context for indicator in ['company', 'corp', 'inc', 'ltd', 'llc', 'organization']):
                            entity_type = "company"
                        elif any(indicator in context for indicator in ['project', 'initiative', 'program', 'system', 'platform']):
                            entity_type = "project"
                        elif any(indicator in context for indicator in ['person', 'team', 'manager', 'director', 'ceo', 'cto']):
                            entity_type = "person"
                        elif word_clean.endswith(('.com', '.org', '.net', '.io')):
                            entity_type = "website"
                        elif '@' in word_clean:
                            entity_type = "email"
                        
                        entities.append({
                            'name': word_clean,
                            'type': entity_type,
                            'context': context,
                            'source_category': category,
                            'confidence': 0.7 if entity_type != "unknown" else 0.3
                        })
                
                # Look for email addresses
                import re
                email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                emails_found = re.findall(email_pattern, content)
                for email in emails_found:
                    entities.append({
                        'name': email,
                        'type': 'email',
                        'context': content[max(0, content.find(email)-50):content.find(email)+50],
                        'source_category': category,
                        'confidence': 0.9
                    })
                
                # Look for URLs
                url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
                urls_found = re.findall(url_pattern, content)
                for url in urls_found:
                    entities.append({
                        'name': url,
                        'type': 'url',
                        'context': content[max(0, content.find(url)-50):content.find(url)+50],
                        'source_category': category,
                        'confidence': 0.9
                    })
        
        # Deduplicate entities by name and return top 10
        seen_names = set()
        unique_entities = []
        for entity in entities:
            if entity['name'].lower() not in seen_names:
                seen_names.add(entity['name'].lower())
                unique_entities.append(entity)
                if len(unique_entities) >= 10:
                    break
        
        return unique_entities

class PredictiveAnalyst(BaseClaudeAnalyst):
    """Analyzes patterns to predict future outcomes and opportunities"""
    
    def __init__(self):
        super().__init__("predictive_analysis")
        self.analysis_prompt = """You are an expert in predictive thinking and future-oriented worldview modeling.

Your task is NOT to simply make predictions, but to understand this person's PREDICTIVE PHILOSOPHY and how they think about the future and uncertainty.

Analyze these emails to understand:

1. FUTURE THINKING: How do they conceptualize the future and plan for uncertainty?
2. PATTERN RECOGNITION: What patterns do they use to anticipate future developments?
3. RISK ASSESSMENT: How do they think about and prepare for potential risks?
4. OPPORTUNITY ANTICIPATION: How do they identify and position for future opportunities?
5. DECISION TIMING: How do they think about timing decisions and market moves?
6. SCENARIO PLANNING: How do they approach planning for multiple possible futures?

Focus on understanding their unique predictive perspective - the mental models and frameworks that guide their future thinking.

Look for:
- Patterns in how they anticipate and prepare for change
- Their approach to managing uncertainty and unknown risks
- How they think about timing and strategic positioning
- Their philosophy on scenario planning and contingency thinking
- How they balance short-term execution with long-term vision

This should reveal their "predictive DNA" - the core frameworks that guide their forward-looking strategic thinking."""

    async def analyze_emails(self, emails: List[Dict], context: Dict = None) -> AnalysisResult:
        """Generate predictions based on patterns"""
        try:
            email_context = self._prepare_email_context(emails)
            
            response = await asyncio.to_thread(
                self.client.messages.create,
                model=self.model,
                max_tokens=4000,
                temperature=0.3,
                messages=[{
                    "role": "user",
                    "content": f"{self.analysis_prompt}\n\nEmails to analyze:\n{email_context}"
                }]
            )
            
            # Parse Claude's response
            result = self._parse_predictive_response(response.content[0].text)
            
            return AnalysisResult(
                analyst_type=self.analyst_type,
                insights=result,
                confidence=0.85,
                evidence=self._extract_evidence(result, emails),
                relationships=result.get('predictive_relationships', []),
                topics=self._extract_topics(result),
                entities=self._extract_entities(result)
            )
            
        except Exception as e:
            logger.error(f"Predictive analysis error: {str(e)}")
            return AnalysisResult(
                analyst_type=self.analyst_type,
                insights={},
                confidence=0.0,
                evidence=[],
                relationships=[],
                topics=[],
                entities=[]
            )
    
    def _parse_predictive_response(self, response_text: str) -> Dict:
        """Parse predictive analysis response"""
        try:
            # Try to extract JSON if present
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        # Fallback to structured response
        return {
            "future_thinking": self._extract_section(response_text, "FUTURE THINKING"),
            "pattern_recognition": self._extract_section(response_text, "PATTERN RECOGNITION"),
            "risk_assessment": self._extract_section(response_text, "RISK ASSESSMENT"),
            "opportunity_anticipation": self._extract_section(response_text, "OPPORTUNITY ANTICIPATION"),
            "decision_timing": self._extract_section(response_text, "DECISION TIMING"),
            "scenario_planning": self._extract_section(response_text, "SCENARIO PLANNING"),
            "raw_analysis": response_text
        }
    
    def _extract_section(self, text: str, section_name: str) -> str:
        """Extract a specific section from the response"""
        lines = text.split('\n')
        in_section = False
        section_content = []
        
        for line in lines:
            if section_name.lower() in line.lower():
                in_section = True
                continue
            elif in_section and any(keyword in line.lower() for keyword in ['thinking', 'recognition', 'assessment', 'anticipation', 'timing', 'planning']):
                break
            elif in_section:
                section_content.append(line)
        
        return '\n'.join(section_content).strip()
    
    def _extract_evidence(self, insights: Dict, emails: List[Dict]) -> List[Dict]:
        """Extract supporting evidence from emails"""
        evidence = []
        
        # Extract key terms from insights for searching
        search_terms = []
        for category, content in insights.items():
            if isinstance(content, str):
                # Extract significant words (length > 3, not common words)
                words = [word.strip('.,!?;:').lower() for word in content.split() 
                        if len(word) > 3 and word.lower() not in ['this', 'that', 'with', 'from', 'they', 'them', 'will', 'have', 'been', 'were', 'was']]
                search_terms.extend(words[:5])  # Top 5 words per category
        
        # Search for evidence in emails
        for email in emails[:20]:  # Check first 20 emails for performance
            email_content = f"{email.get('subject', '')} {email.get('body_text', '')}"
            email_content_lower = email_content.lower()
            
            # Count matches
            matches = sum(1 for term in search_terms if term in email_content_lower)
            
            if matches > 0:
                # Extract relevant excerpt
                sentences = email_content.split('.')
                relevant_sentences = []
                for sentence in sentences:
                    if any(term in sentence.lower() for term in search_terms):
                        relevant_sentences.append(sentence.strip())
                        if len(relevant_sentences) >= 2:  # Max 2 sentences
                            break
                
                evidence.append({
                    'email_id': email.get('id'),
                    'date': email.get('email_date'),
                    'sender': email.get('sender'),
                    'subject': email.get('subject'),
                    'excerpt': '. '.join(relevant_sentences)[:200] + '...' if len('. '.join(relevant_sentences)) > 200 else '. '.join(relevant_sentences),
                    'relevance_score': matches / len(search_terms) if search_terms else 0,
                    'match_count': matches
                })
        
        # Sort by relevance and return top 5
        evidence.sort(key=lambda x: x['relevance_score'], reverse=True)
        return evidence[:5]
    
    def _extract_topics(self, insights: Dict) -> List[str]:
        """Extract key topics from insights"""
        topics = set()
        
        for category, content in insights.items():
            # Add category as topic
            topics.add(category.replace('_', ' ').title())
            
            if isinstance(content, str):
                # Extract potential topics from content
                words = content.split()
                for i, word in enumerate(words):
                    word = word.strip('.,!?;:').lower()
                    if len(word) > 4:  # Longer words more likely to be topics
                        topics.add(word.title())
                    
                    # Look for capitalized words/phrases that might be topics
                    if word[0].isupper() and len(word) > 3:
                        topics.add(word)
                        
                    # Look for phrases (adjacent capitalized words)
                    if i < len(words) - 1:
                        next_word = words[i + 1].strip('.,!?;:')
                        if word[0].isupper() and next_word and next_word[0].isupper():
                            topics.add(f"{word} {next_word}")
            
            elif isinstance(content, list):
                for item in content:
                    if isinstance(item, dict):
                        for key, value in item.items():
                            topics.add(key.replace('_', ' ').title())
                            if isinstance(value, str) and len(value.split()) <= 3:
                                topics.add(value)
                    elif isinstance(item, str):
                        topics.add(item)
        
        # Filter out very common words and return list
        common_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'between', 'among'}
        filtered_topics = [topic for topic in topics if topic.lower() not in common_words and len(topic) > 2]
        
        return list(set(filtered_topics))[:20]  # Return top 20 unique topics
    
    def _extract_entities(self, insights: Dict) -> List[Dict]:
        """Extract entities (people, companies, projects) from insights"""
        entities = []
        
        for category, content in insights.items():
            if isinstance(content, str):
                # Look for patterns that might be entities
                words = content.split()
                
                for i, word in enumerate(words):
                    word_clean = word.strip('.,!?;:')
                    
                    # Look for capitalized words (potential proper nouns)
                    if word_clean and word_clean[0].isupper() and len(word_clean) > 2:
                        entity_type = "unknown"
                        
                        # Try to classify entity type based on context
                        context = ' '.join(words[max(0, i-2):i+3]).lower()
                        
                        if any(indicator in context for indicator in ['company', 'corp', 'inc', 'ltd', 'llc', 'organization']):
                            entity_type = "company"
                        elif any(indicator in context for indicator in ['project', 'initiative', 'program', 'system', 'platform']):
                            entity_type = "project"
                        elif any(indicator in context for indicator in ['person', 'team', 'manager', 'director', 'ceo', 'cto']):
                            entity_type = "person"
                        elif word_clean.endswith(('.com', '.org', '.net', '.io')):
                            entity_type = "website"
                        elif '@' in word_clean:
                            entity_type = "email"
                        
                        entities.append({
                            'name': word_clean,
                            'type': entity_type,
                            'context': context,
                            'source_category': category,
                            'confidence': 0.7 if entity_type != "unknown" else 0.3
                        })
                
                # Look for email addresses
                import re
                email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                emails_found = re.findall(email_pattern, content)
                for email in emails_found:
                    entities.append({
                        'name': email,
                        'type': 'email',
                        'context': content[max(0, content.find(email)-50):content.find(email)+50],
                        'source_category': category,
                        'confidence': 0.9
                    })
                
                # Look for URLs
                url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
                urls_found = re.findall(url_pattern, content)
                for url in urls_found:
                    entities.append({
                        'name': url,
                        'type': 'url',
                        'context': content[max(0, content.find(url)-50):content.find(url)+50],
                        'source_category': category,
                        'confidence': 0.9
                    })
        
        # Deduplicate entities by name and return top 10
        seen_names = set()
        unique_entities = []
        for entity in entities:
            if entity['name'].lower() not in seen_names:
                seen_names.add(entity['name'].lower())
                unique_entities.append(entity)
                if len(unique_entities) >= 10:
                    break
        
        return unique_entities

class KnowledgeTreeBuilder:
    """Builds comprehensive knowledge tree from email analysis"""
    
    # Make this available as a singleton for easy import in routes
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        self.analysts = {
            'business_strategy': BusinessStrategyAnalyst(),
            'relationship_dynamics': RelationshipDynamicsAnalyst(),
            'technical_evolution': TechnicalEvolutionAnalyst(),
            'market_intelligence': MarketIntelligenceAnalyst(),
            'predictive': PredictiveAnalyst()
        }
        
    async def build_knowledge_tree(self, user_id: int, time_window_days: int = 30) -> Dict:
        """Build comprehensive knowledge tree from emails"""
        from models.database import get_db_manager
        
        try:
            db_manager = get_db_manager()
            
            # Get emails for time window
            emails = self._get_emails_for_window(user_id, time_window_days)
            
            if not emails:
                logger.warning(f"No emails found for user {user_id} in {time_window_days} day window")
                return {'status': 'no_data'}
            
            logger.info(f"Building knowledge tree from {len(emails)} emails")
            
            # Run all analysts in parallel
            analysis_tasks = []
            for analyst_name, analyst in self.analysts.items():
                task = analyst.analyze_emails(emails)
                analysis_tasks.append(task)
            
            # Wait for all analyses to complete
            results = await asyncio.gather(*analysis_tasks)
            
            # Merge results into knowledge tree
            knowledge_tree = self._merge_analysis_results(results)
            
            # Add temporal context
            knowledge_tree['time_window'] = {
                'days': time_window_days,
                'email_count': len(emails),
                'analysis_timestamp': datetime.utcnow().isoformat()
            }
            
            # Save to database
            self._save_knowledge_tree(user_id, knowledge_tree)
            
            return knowledge_tree
            
        except Exception as e:
            logger.error(f"Knowledge tree building error: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
    def _get_emails_for_window(self, user_id: int, days: int) -> List[Dict]:
        """Get emails within time window - using real emails, not mock data"""
        from models.database import get_db_manager
        from datetime import datetime, timedelta
        
        db_manager = get_db_manager()
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get emails - this should now use real data since we fixed the OAuth issue
        emails = db_manager.get_user_emails(user_id, limit=1000)
        
        # Filter by date
        filtered_emails = []
        for email in emails:
            if email.email_date and email.email_date > cutoff_date:
                filtered_emails.append(email.to_dict())
        
        logger.info(f"Retrieved {len(filtered_emails)} real emails for knowledge tree analysis")
        return filtered_emails
    
    def _merge_analysis_results(self, results: List[AnalysisResult]) -> Dict:
        """Merge results from all analysts into unified knowledge tree"""
        knowledge_tree = {
            'insights': {},
            'relationships': [],
            'topics': set(),
            'entities': [],
            'predictions': [],
            'evidence_map': {},
            'worldview_synthesis': {}
        }
        
        for result in results:
            # Merge insights by analyst type
            knowledge_tree['insights'][result.analyst_type] = result.insights
            
            # Aggregate relationships
            knowledge_tree['relationships'].extend(result.relationships)
            
            # Collect all topics
            knowledge_tree['topics'].update(result.topics)
            
            # Aggregate entities
            knowledge_tree['entities'].extend(result.entities)
            
            # Map evidence to insights
            for evidence in result.evidence:
                insight_id = evidence.get('insight_id')
                if insight_id:
                    knowledge_tree['evidence_map'][insight_id] = evidence
        
        # Convert set to list for JSON serialization
        knowledge_tree['topics'] = list(knowledge_tree['topics'])
        
        # Deduplicate and rank entities
        knowledge_tree['entities'] = self._deduplicate_entities(knowledge_tree['entities'])
        
        # Create worldview synthesis from all insights
        knowledge_tree['worldview_synthesis'] = self._synthesize_worldview_insights(knowledge_tree['insights'])
        
        return knowledge_tree
    
    def _synthesize_worldview_insights(self, insights: Dict) -> Dict:
        """Synthesize insights from all analysts into coherent worldview"""
        synthesis = {
            "core_philosophies": {},
            "cross_domain_patterns": [],
            "strategic_frameworks": {},
            "unique_perspectives": [],
            "synthesis_confidence": 0.8
        }
        
        # Extract core philosophies from each domain
        for analyst_type, insight_data in insights.items():
            if isinstance(insight_data, dict):
                philosophies = {}
                for key, value in insight_data.items():
                    if 'philosophy' in key.lower() or 'worldview' in key.lower() or 'thinking' in key.lower():
                        philosophies[key] = value
                synthesis["core_philosophies"][analyst_type] = philosophies
        
        return synthesis
    
    def _deduplicate_entities(self, entities: List[Dict]) -> List[Dict]:
        """Deduplicate and merge entity information"""
        entity_map = {}
        
        for entity in entities:
            key = (entity.get('type'), entity.get('name'))
            if key in entity_map:
                # Merge information
                existing = entity_map[key]
                existing['mentions'] = existing.get('mentions', 0) + 1
                existing['contexts'].extend(entity.get('contexts', []))
            else:
                entity['mentions'] = 1
                entity['contexts'] = entity.get('contexts', [])
                entity_map[key] = entity
        
        return list(entity_map.values())
    
    def _save_knowledge_tree(self, user_id: int, knowledge_tree: Dict):
        """Save knowledge tree to database"""
        try:
            from storage.storage_manager import StorageManager
            storage_manager = StorageManager()
            
            # Store as JSON in the database
            storage_manager.save_knowledge_tree(user_id, knowledge_tree)
            
            # Also index the knowledge tree in vector database for semantic search
            knowledge_tree_str = json.dumps(knowledge_tree)
            storage_manager.index_knowledge_tree(user_id, knowledge_tree_str)
            
            logger.info(f"Knowledge tree saved for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to save knowledge tree: {str(e)}")
            return False