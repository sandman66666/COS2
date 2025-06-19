# intelligence/analysts/relationship_analyst.py
"""
Relationship Intelligence Analyst
==============================
Specialized analyst for relationship patterns and interpersonal dynamics.
Powered by Claude Opus with multi-tenant isolation.
"""

import json
from typing import Dict, List, Optional, Any
from datetime import datetime

from utils.logging import structured_logger as logger
from intelligence.analysts.base_analyst import BaseAnalyst

class RelationshipIntelligenceAnalyst(BaseAnalyst):
    """
    Relationship intelligence analyst
    
    Analyzes communication patterns, sentiment, and interpersonal dynamics
    to provide insights on professional relationships and network leverage.
    """
    
    def __init__(self, user_id: int, anthropic_api_key: str = None):
        """
        Initialize relationship analyst
        
        Args:
            user_id: User ID for multi-tenant isolation
            anthropic_api_key: Optional API key for Claude Opus
        """
        super().__init__(user_id, anthropic_api_key)
        self.analyst_name = "relationship_intelligence"
        self.analyst_description = "Relationship dynamics and network analysis specialist"
        
        # Customize Claude parameters
        self.max_tokens = 4000
        self.temperature = 0.25  # Slightly higher for insights on human dynamics
    
    async def generate_intelligence(self, data: Dict) -> Dict:
        """
        Generate relationship intelligence from provided data
        
        Args:
            data: Dictionary containing:
                - contacts: List of enriched contact data
                - emails: List of relevant email exchanges
                - (optional) knowledge_tree: Knowledge tree data
                - (optional) specific_focus: Relationship area or person to focus on
                
        Returns:
            Dictionary with relationship insights and recommendations
        """
        # Validate critical inputs
        if not data.get("contacts") and not data.get("emails"):
            logger.error(
                "Missing required data for relationship analysis",
                user_id=self.user_id
            )
            return {"error": "Insufficient data for relationship analysis"}
            
        try:
            # Extract data elements
            contacts = data.get("contacts", [])
            emails = data.get("emails", [])
            knowledge_tree = data.get("knowledge_tree", {})
            focus_area = data.get("specific_focus", "key relationships")
            
            # Prepare specialized system prompt
            system_prompt = self._create_system_prompt(focus_area)
            
            # Prepare user prompt with data
            user_prompt = self._create_user_prompt(
                contacts=contacts,
                emails=emails,
                knowledge_tree=knowledge_tree,
                focus_area=focus_area
            )
            
            # Run Claude Opus analysis
            result_text = await self._run_claude_analysis(system_prompt, user_prompt)
            
            # Extract structured components
            structured_result = self._parse_claude_response(result_text)
            
            # Add metadata
            structured_result["focus_area"] = focus_area
            structured_result["analysis_timestamp"] = datetime.utcnow().isoformat()
            structured_result["data_points_analyzed"] = {
                "contacts": len(contacts),
                "emails": len(emails),
                "knowledge_nodes": len(knowledge_tree.get("nodes", [])) if isinstance(knowledge_tree.get("nodes"), list) else 0
            }
            
            return structured_result
            
        except Exception as e:
            logger.error(
                "Error generating relationship intelligence",
                error=str(e),
                user_id=self.user_id
            )
            return {"error": f"Relationship intelligence generation failed: {str(e)}"}
    
    def _create_system_prompt(self, focus_area: str) -> str:
        """
        Create system prompt for Claude Opus
        
        Args:
            focus_area: Area to focus analysis on
            
        Returns:
            System prompt string
        """
        return f"""You are an expert relationship intelligence analyst specializing in interpersonal dynamics and professional networks.

Your task is to analyze communication patterns, sentiment in emails, and network connections to extract valuable insights about relationship dynamics and provide strategic recommendations for relationship management.

Focus on:
1. Identifying key relationship patterns and communication styles
2. Analyzing sentiment and emotional dynamics in communications
3. Detecting relationship strengths, weaknesses, and potential issues
4. Mapping spheres of influence and network leverage points
5. Recognizing trust levels and reciprocity in relationships

Structure your analysis with these sections:
- Key Relationship Insights: Overview of most significant relationship patterns
- Network Analysis: Mapping of connections, influence, and relationship clusters
- Communication Patterns: Analysis of communication styles, frequency, and effectiveness
- Relationship Opportunities: Areas to strengthen or leverage relationships
- Recommendations: Actionable steps to improve relationship outcomes

Be nuanced, empathetic, and practical in your analysis. Recognize the complexity of human relationships while providing clear, actionable insights.
Base all insights on the provided data and make reasonable inferences where appropriate.
Format your response as a combination of concise paragraphs and bullet points for readability.

Maintain absolute confidentiality and privacy in your analysis.
Do not include any information that could be considered sensitive or proprietary.
"""
    
    def _create_user_prompt(
        self, 
        contacts: List[Dict], 
        emails: List[Dict],
        knowledge_tree: Dict,
        focus_area: str
    ) -> str:
        """
        Create user prompt with data for analysis
        
        Args:
            contacts: List of enriched contact data
            emails: List of relevant email exchanges
            knowledge_tree: Knowledge graph data
            focus_area: Area to focus analysis on
            
        Returns:
            Formatted user prompt
        """
        # Limit data volume to fit context window
        max_contacts = min(50, len(contacts))
        max_emails = min(30, len(emails))
        
        # Select most important contacts and emails
        selected_contacts = contacts[:max_contacts]
        selected_emails = emails[:max_emails]
        
        # Format prompt
        prompt = f"""Please analyze the following relationship data and provide insights focused on {focus_area}.

## CONTACTS DATA
I'm providing information about {len(selected_contacts)} professional contacts with their profiles:

```json
{self._format_json_for_prompt(selected_contacts)}
```

## EMAIL COMMUNICATIONS
Here are {len(selected_emails)} relevant email exchanges that provide context on relationship dynamics:

```json
{self._format_json_for_prompt(selected_emails)}
```
"""

        # Add knowledge tree if available
        if knowledge_tree and knowledge_tree.get("nodes"):
            prompt += f"""
## RELATIONSHIP NETWORK
Here is a knowledge graph showing connections between people and entities:

```json
{self._format_json_for_prompt(knowledge_tree)}
```
"""

        # Add specific instructions
        prompt += f"""
Based on this data, please provide:

1. An insightful analysis of key relationship dynamics
2. Network analysis showing spheres of influence and connection patterns
3. Communication style analysis for key relationships
4. Opportunities to strengthen or leverage important relationships
5. Actionable recommendations for better relationship outcomes

Focus specifically on {focus_area} and organize your response according to the structure in your instructions.
"""

        return prompt
    
    def _parse_claude_response(self, response_text: str) -> Dict:
        """
        Parse Claude's response into structured components
        
        Args:
            response_text: Raw response from Claude
            
        Returns:
            Structured response dictionary
        """
        # Default structure
        result = {
            "key_relationship_insights": "",
            "network_analysis": "",
            "communication_patterns": [],
            "relationship_opportunities": [],
            "recommendations": []
        }
        
        if not response_text:
            return result
            
        # Extract key relationship insights
        if "Key Relationship Insights" in response_text:
            parts = response_text.split("Key Relationship Insights", 1)
            if len(parts) > 1:
                insights_section = parts[1].split("\n#", 1)[0].split("Network Analysis", 1)[0].strip()
                result["key_relationship_insights"] = insights_section
        
        # Extract network analysis
        if "Network Analysis" in response_text:
            parts = response_text.split("Network Analysis", 1)
            if len(parts) > 1:
                network_section = parts[1].split("\n#", 1)[0].split("Communication Patterns", 1)[0].strip()
                result["network_analysis"] = network_section
        
        # Extract communication patterns
        if "Communication Patterns" in response_text:
            parts = response_text.split("Communication Patterns", 1)
            if len(parts) > 1:
                patterns_text = parts[1].split("\n#", 1)[0].split("Relationship Opportunities", 1)[0]
                # Extract bullet points
                patterns = []
                for line in patterns_text.split("\n"):
                    if line.strip().startswith("- ") or line.strip().startswith("* "):
                        patterns.append(line.strip()[2:])
                if patterns:
                    result["communication_patterns"] = patterns
                else:
                    result["communication_patterns"] = [patterns_text.strip()]
        
        # Extract relationship opportunities
        if "Relationship Opportunities" in response_text:
            parts = response_text.split("Relationship Opportunities", 1)
            if len(parts) > 1:
                opps_text = parts[1].split("\n#", 1)[0].split("Recommendations", 1)[0]
                # Extract bullet points
                opps = []
                for line in opps_text.split("\n"):
                    if line.strip().startswith("- ") or line.strip().startswith("* "):
                        opps.append(line.strip()[2:])
                if opps:
                    result["relationship_opportunities"] = opps
                else:
                    result["relationship_opportunities"] = [opps_text.strip()]
        
        # Extract recommendations
        if "Recommendations" in response_text:
            parts = response_text.split("Recommendations", 1)
            if len(parts) > 1:
                recs_text = parts[1].strip()
                # Extract bullet points
                recs = []
                for line in recs_text.split("\n"):
                    if line.strip().startswith("- ") or line.strip().startswith("* "):
                        recs.append(line.strip()[2:])
                if recs:
                    result["recommendations"] = recs
                else:
                    result["recommendations"] = [recs_text.strip()]
        
        # Add full text as fallback
        result["full_analysis"] = response_text
        
        return result
    
    def _validate_input(self, input_data: Dict) -> Optional[str]:
        """
        Validate input data for relationship analysis
        
        Args:
            input_data: Input data dictionary
            
        Returns:
            Error message if validation fails, None if valid
        """
        if not input_data:
            return "No input data provided"
            
        if not input_data.get("contacts") and not input_data.get("emails"):
            return "Missing required data: need either contacts or emails"
            
        return None
    
    def _summarize_input(self, input_data: Dict) -> Dict:
        """
        Create summary of input data
        
        Args:
            input_data: Input data dictionary
            
        Returns:
            Input data summary
        """
        summary = {}
        
        if "contacts" in input_data:
            contacts = input_data["contacts"]
            summary["contacts_count"] = len(contacts)
            
            # Count contacts by company
            companies = {}
            for contact in contacts:
                company = contact.get("company", "Unknown")
                companies[company] = companies.get(company, 0) + 1
                
            summary["company_distribution"] = dict(sorted(
                companies.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:5])  # Top 5 companies
            
        if "emails" in input_data:
            emails = input_data["emails"]
            summary["emails_count"] = len(emails)
            
            # Calculate communication frequency
            freq_by_person = {}
            for email in emails:
                sender = email.get("sender", "Unknown")
                freq_by_person[sender] = freq_by_person.get(sender, 0) + 1
                
                for recipient in email.get("recipients", []):
                    freq_by_person[recipient] = freq_by_person.get(recipient, 0) + 1
                    
            summary["top_communicators"] = dict(sorted(
                freq_by_person.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:5])  # Top 5 communicators
            
        if "specific_focus" in input_data:
            summary["focus_area"] = input_data["specific_focus"]
            
        if "knowledge_tree" in input_data:
            tree = input_data["knowledge_tree"]
            summary["relationship_nodes"] = len(tree.get("nodes", []))
            summary["relationship_connections"] = len(tree.get("edges", []))
            
        return summary
