"""
Predictive Relationship Decay System
===================================
Predicts when relationships need maintenance before they deteriorate.
Integrates with behavioral intelligence and communication patterns.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from utils.logging import structured_logger as logger

class DecayRiskLevel(Enum):
    CRITICAL = "critical"  # Immediate action needed (0-3 days)
    HIGH = "high"         # Action needed within days (4-14 days)
    MEDIUM = "medium"     # Monitor closely (15-30 days)
    LOW = "low"           # Healthy relationship (30+ days)

@dataclass
class DecayRisk:
    contact_email: str
    contact_name: str
    risk_level: DecayRiskLevel
    days_until_dormant: int
    last_interaction: datetime
    peak_communication_days: List[int]  # Best days to reach out (0=Monday, 6=Sunday)
    recommended_action: str
    optimal_timing: datetime
    confidence_score: float
    risk_factors: List[str]
    relationship_value: str  # 'high', 'medium', 'low'
    communication_trend: str  # 'warming', 'stable', 'cooling'

class RelationshipDecayPredictor:
    """Predict relationship decay before it happens"""
    
    def __init__(self, storage_manager):
        self.storage_manager = storage_manager
        
        # Decay thresholds by relationship value
        self.decay_thresholds = {
            'high': 14,      # High-value contacts: 14 days before risk
            'medium': 30,    # Regular contacts: 30 days
            'low': 60,       # Casual contacts: 60 days
            'dormant_threshold': 90  # 90 days until marked dormant
        }
    
    async def analyze_relationships_for_user(self, user_id: int) -> List[DecayRisk]:
        """Analyze all relationships for a user and predict decay risks"""
        try:
            # Get all emails for communication pattern analysis
            emails = await self.storage_manager.get_emails_for_user(
                user_id, 
                limit=1000, 
                time_window_days=365
            )
            
            if not emails:
                logger.info(f"No emails found for user {user_id}")
                return []
            
            # Extract unique contacts and analyze each
            contacts = self._extract_contacts_from_emails(emails)
            decay_risks = []
            
            for contact_email, contact_data in contacts.items():
                risk = await self._predict_decay_risk(contact_email, contact_data, emails)
                if risk and risk.risk_level in [DecayRiskLevel.HIGH, DecayRiskLevel.CRITICAL]:
                    decay_risks.append(risk)
            
            # Sort by risk level and days until dormant
            decay_risks.sort(key=lambda x: (
                ['critical', 'high', 'medium', 'low'].index(x.risk_level.value),
                x.days_until_dormant
            ))
            
            logger.info(f"Analyzed {len(contacts)} contacts, found {len(decay_risks)} at risk")
            return decay_risks
            
        except Exception as e:
            logger.error(f"Error analyzing relationships for user {user_id}: {e}")
            return []
    
    def _extract_contacts_from_emails(self, emails: List[Dict]) -> Dict[str, Dict]:
        """Extract contact information from emails"""
        contacts = {}
        
        for email in emails:
            # Get sender and recipients
            sender = email.get('sender', '').lower().strip()
            recipients = []
            
            if email.get('recipient'):
                recipients.append(email['recipient'].lower().strip())
            if email.get('cc'):
                recipients.extend([r.lower().strip() for r in email['cc'].split(',') if r.strip()])
            
            # Process each contact
            all_contacts = [sender] + recipients if sender else recipients
            
            for contact_email in all_contacts:
                if not contact_email or '@' not in contact_email:
                    continue
                
                if contact_email not in contacts:
                    contacts[contact_email] = {
                        'name': self._extract_name_from_email(contact_email),
                        'interactions': [],
                        'last_interaction': None,
                        'total_emails': 0,
                        'sent_to_them': 0,
                        'received_from_them': 0
                    }
                
                # Record interaction
                interaction_date = email.get('timestamp', datetime.now())
                if isinstance(interaction_date, str):
                    interaction_date = datetime.fromisoformat(interaction_date.replace('Z', '+00:00'))
                
                contacts[contact_email]['interactions'].append({
                    'date': interaction_date,
                    'direction': 'sent' if contact_email != sender else 'received',
                    'subject': email.get('subject', ''),
                    'has_response': bool(email.get('thread_id'))  # Simplified response detection
                })
                
                contacts[contact_email]['total_emails'] += 1
                if contact_email != sender:
                    contacts[contact_email]['sent_to_them'] += 1
                else:
                    contacts[contact_email]['received_from_them'] += 1
                
                # Update last interaction
                if (not contacts[contact_email]['last_interaction'] or 
                    interaction_date > contacts[contact_email]['last_interaction']):
                    contacts[contact_email]['last_interaction'] = interaction_date
        
        return contacts
    
    def _extract_name_from_email(self, email: str) -> str:
        """Extract name from email address"""
        if not email or '@' not in email:
            return 'Unknown'
        
        local_part = email.split('@')[0]
        # Convert common patterns to readable names
        name = local_part.replace('.', ' ').replace('_', ' ').replace('-', ' ')
        return ' '.join(word.capitalize() for word in name.split())
    
    async def _predict_decay_risk(self, contact_email: str, contact_data: Dict, all_emails: List[Dict]) -> Optional[DecayRisk]:
        """Predict decay risk for a single contact"""
        try:
            interactions = contact_data.get('interactions', [])
            if len(interactions) < 2:  # Need at least 2 interactions for pattern analysis
                return None
            
            # Sort interactions by date
            interactions.sort(key=lambda x: x['date'])
            
            # Calculate communication patterns
            patterns = self._analyze_communication_patterns(interactions)
            
            # Determine relationship value
            relationship_value = self._assess_relationship_value(contact_data, patterns)
            
            # Calculate risk level and days until dormant
            risk_level, days_until_dormant = self._calculate_risk_level(patterns, relationship_value)
            
            # Skip if relationship is healthy
            if risk_level == DecayRiskLevel.LOW:
                return None
            
            # Generate recommended action
            recommended_action = self._generate_recommendation(
                risk_level, patterns, contact_data, relationship_value
            )
            
            # Calculate optimal reach-out time
            optimal_timing = self._calculate_optimal_timing(patterns, risk_level)
            
            # Identify risk factors
            risk_factors = self._identify_risk_factors(patterns, contact_data)
            
            return DecayRisk(
                contact_email=contact_email,
                contact_name=contact_data.get('name', 'Unknown'),
                risk_level=risk_level,
                days_until_dormant=max(0, days_until_dormant),
                last_interaction=patterns['last_interaction'],
                peak_communication_days=patterns.get('peak_days', [1, 2, 3]),  # Default to Tue-Thu
                recommended_action=recommended_action,
                optimal_timing=optimal_timing,
                confidence_score=patterns['pattern_confidence'],
                risk_factors=risk_factors,
                relationship_value=relationship_value,
                communication_trend=patterns['trend']
            )
            
        except Exception as e:
            logger.error(f"Error predicting decay risk for {contact_email}: {e}")
            return None
    
    def _analyze_communication_patterns(self, interactions: List[Dict]) -> Dict:
        """Analyze communication frequency and patterns"""
        if not interactions:
            return {'pattern_confidence': 0}
        
        # Calculate intervals between communications
        intervals = []
        for i in range(1, len(interactions)):
            interval = (interactions[i]['date'] - interactions[i-1]['date']).days
            intervals.append(max(1, interval))  # Minimum 1 day interval
        
        # Calculate pattern metrics
        avg_interval = sum(intervals) / len(intervals) if intervals else 999
        
        # Detect communication trend
        trend = 'stable'
        if len(intervals) >= 3:
            recent_intervals = intervals[-3:]
            older_intervals = intervals[:-3] if len(intervals) > 3 else intervals[:1]
            
            recent_avg = sum(recent_intervals) / len(recent_intervals)
            older_avg = sum(older_intervals) / len(older_intervals)
            
            if recent_avg > older_avg * 1.5:
                trend = 'cooling'  # Intervals getting longer
            elif recent_avg < older_avg * 0.7:
                trend = 'warming'  # Intervals getting shorter
        
        # Calculate response rate
        responses = sum(1 for interaction in interactions if interaction.get('has_response', False))
        response_rate = responses / len(interactions) if interactions else 0
        
        # Identify peak communication days
        day_counts = {}
        for interaction in interactions:
            day = interaction['date'].weekday()  # 0=Monday, 6=Sunday
            day_counts[day] = day_counts.get(day, 0) + 1
        
        # Get top 3 communication days
        peak_days = sorted(day_counts.keys(), key=lambda x: day_counts[x], reverse=True)[:3]
        
        return {
            'last_interaction': interactions[-1]['date'],
            'average_interval_days': avg_interval,
            'trend': trend,
            'total_interactions': len(interactions),
            'response_rate': response_rate,
            'peak_days': peak_days,
            'pattern_confidence': min(len(interactions) / 10, 1.0),  # More data = higher confidence
            'days_since_last': (datetime.now() - interactions[-1]['date']).days
        }
    
    def _assess_relationship_value(self, contact_data: Dict, patterns: Dict) -> str:
        """Assess the strategic value of a relationship"""
        total_emails = contact_data.get('total_emails', 0)
        response_rate = patterns.get('response_rate', 0)
        avg_interval = patterns.get('average_interval_days', 999)
        
        # Score based on multiple factors
        score = 0
        
        # Email volume (more emails = higher value)
        if total_emails >= 20:
            score += 3
        elif total_emails >= 10:
            score += 2
        elif total_emails >= 5:
            score += 1
        
        # Response rate (higher = more engaged)
        if response_rate >= 0.7:
            score += 2
        elif response_rate >= 0.4:
            score += 1
        
        # Communication frequency (more frequent = higher value)
        if avg_interval <= 7:
            score += 2
        elif avg_interval <= 30:
            score += 1
        
        # Classify based on score
        if score >= 5:
            return 'high'
        elif score >= 3:
            return 'medium'
        else:
            return 'low'
    
    def _calculate_risk_level(self, patterns: Dict, relationship_value: str) -> Tuple[DecayRiskLevel, int]:
        """Calculate decay risk level and days until dormant"""
        days_since_last = patterns.get('days_since_last', 0)
        avg_interval = patterns.get('average_interval_days', 30)
        trend = patterns.get('trend', 'stable')
        
        # Get threshold for this relationship value
        threshold = self.decay_thresholds[relationship_value]
        
        # Adjust threshold based on trend
        if trend == 'cooling':
            threshold *= 0.7  # Tighten threshold for cooling relationships
        elif trend == 'warming':
            threshold *= 1.3  # Relax threshold for warming relationships
        
        # Calculate days until expected dormancy
        expected_next_contact = avg_interval - days_since_last
        days_until_dormant = max(0, threshold - days_since_last + expected_next_contact)
        
        # Determine risk level
        if days_since_last >= threshold * 1.5:
            return DecayRiskLevel.CRITICAL, 0
        elif days_since_last >= threshold:
            return DecayRiskLevel.HIGH, max(0, int(days_until_dormant))
        elif days_since_last >= threshold * 0.7:
            return DecayRiskLevel.MEDIUM, max(0, int(days_until_dormant))
        else:
            return DecayRiskLevel.LOW, max(0, int(days_until_dormant))
    
    def _generate_recommendation(self, risk_level: DecayRiskLevel, patterns: Dict, 
                               contact_data: Dict, relationship_value: str) -> str:
        """Generate specific action recommendation"""
        name = contact_data.get('name', 'contact')
        trend = patterns.get('trend', 'stable')
        response_rate = patterns.get('response_rate', 0)
        
        if risk_level == DecayRiskLevel.CRITICAL:
            if response_rate < 0.3:
                return f"Urgent re-engagement needed: Send valuable content or check-in to {name}"
            else:
                return f"Critical relationship risk: Schedule call or meeting with {name} this week"
                
        elif risk_level == DecayRiskLevel.HIGH:
            if trend == 'cooling':
                return f"Relationship cooling: Send personal update or valuable insight to {name}"
            else:
                return f"Proactive outreach: Touch base with {name} about [shared interest/project]"
        
        else:  # MEDIUM risk
            return f"Monitor and maintain: Add {name} to next newsletter or look for natural touchpoint"
    
    def _calculate_optimal_timing(self, patterns: Dict, risk_level: DecayRiskLevel) -> datetime:
        """Calculate optimal time to reach out"""
        peak_days = patterns.get('peak_days', [1, 2, 3])  # Default to Tue-Thu
        
        # Base timing by risk level
        if risk_level == DecayRiskLevel.CRITICAL:
            base_date = datetime.now() + timedelta(days=1)  # Tomorrow
        elif risk_level == DecayRiskLevel.HIGH:
            base_date = datetime.now() + timedelta(days=3)  # Within 3 days
        else:
            base_date = datetime.now() + timedelta(days=7)  # Within a week
        
        # Find next optimal day
        for i in range(7):  # Look up to 7 days ahead
            check_date = base_date + timedelta(days=i)
            if check_date.weekday() in peak_days and check_date.weekday() < 5:  # Weekday
                # Set to 10 AM on optimal day
                return check_date.replace(hour=10, minute=0, second=0, microsecond=0)
        
        return base_date  # Fallback to base date
    
    def _identify_risk_factors(self, patterns: Dict, contact_data: Dict) -> List[str]:
        """Identify specific risk factors"""
        factors = []
        
        trend = patterns.get('trend', 'stable')
        days_since_last = patterns.get('days_since_last', 0)
        avg_interval = patterns.get('average_interval_days', 30)
        response_rate = patterns.get('response_rate', 0)
        
        if trend == 'cooling':
            factors.append("Communication frequency declining")
        
        if response_rate < 0.3:
            factors.append("Low response rate")
        
        if days_since_last > avg_interval * 2:
            factors.append(f"No contact for {days_since_last} days (2x normal interval)")
        
        if contact_data.get('total_emails', 0) > 20 and days_since_last > 30:
            factors.append("High-engagement relationship at risk")
        
        if patterns.get('total_interactions', 0) < 5:
            factors.append("Limited interaction history")
        
        return factors
    
    def get_decay_summary(self, decay_risks: List[DecayRisk]) -> Dict:
        """Get summary statistics for decay risks"""
        if not decay_risks:
            return {
                'total_at_risk': 0,
                'by_risk_level': {},
                'by_relationship_value': {},
                'average_days_until_dormant': 0
            }
        
        # Group by risk level
        by_risk = {}
        for risk in decay_risks:
            level = risk.risk_level.value
            if level not in by_risk:
                by_risk[level] = 0
            by_risk[level] += 1
        
        # Group by relationship value
        by_value = {}
        for risk in decay_risks:
            value = risk.relationship_value
            if value not in by_value:
                by_value[value] = 0
            by_value[value] += 1
        
        avg_days = sum(risk.days_until_dormant for risk in decay_risks) / len(decay_risks)
        
        return {
            'total_at_risk': len(decay_risks),
            'by_risk_level': by_risk,
            'by_relationship_value': by_value,
            'average_days_until_dormant': round(avg_days, 1),
            'generated_at': datetime.now().isoformat()
        } 