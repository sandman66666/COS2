# intelligence/analysts/business_analyst.py
"""
Business Intelligence Analyst
==========================
Specialized analyst for business insights and strategic recommendations.
Powered by Claude Opus with multi-tenant isolation.
"""

import json
from typing import Dict, List, Optional, Any
from datetime import datetime

from utils.logging import structured_logger as logger
from intelligence.analysts.base_analyst import BaseAnalyst

class BusinessIntelligenceAnalyst(BaseAnalyst):
    """
    Business intelligence analyst
    
    Analyzes contact and email data to extract business insights,
    relationships, and strategic opportunities.
    """
    
    def __init__(self, user_id: int, anthropic_api_key: str = None):
        """
        Initialize business analyst
        
        Args:
            user_id: User ID for multi-tenant isolation
            anthropic_api_key: Optional API key for Claude Opus
        """
        super().__init__(user_id, anthropic_api_key)
        self.analyst_name = "business_intelligence"
        self.analyst_description = "Business strategy and relationship analyst"
        
        # Customize Claude parameters
        self.max_tokens = 4000
        self.temperature = 0.2  # Lower temperature for more factual/strategic responses
    
    async def generate_intelligence(self, data: Dict) -> Dict:
        """
        Generate business intelligence from provided data
        
        Args:
            data: Dictionary containing:
                - contacts: List of enriched contact data
                - emails: List of relevant email exchanges
                - (optional) knowledge_tree: Knowledge tree data
                - (optional) specific_focus: Area of business to focus on
                
        Returns:
            Dictionary with business insights and recommendations
        """
        # Validate critical inputs
        if not data.get("contacts") and not data.get("emails"):
            logger.error(
                "Missing required data for business analysis",
                user_id=self.user_id
            )
            return {"error": "Insufficient data for business analysis"}
            
        try:
            # Extract data elements
            contacts = data.get("contacts", [])
            emails = data.get("emails", [])
            knowledge_tree = data.get("knowledge_tree", {})
            focus_area = data.get("specific_focus", "general business strategy")
            
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
                "Error generating business intelligence",
                error=str(e),
                user_id=self.user_id
            )
            return {"error": f"Business intelligence generation failed: {str(e)}"}
    
    def _create_system_prompt(self, focus_area: str) -> str:
        """
        Create system prompt for Claude Opus
        
        Args:
            focus_area: Area to focus analysis on
            
        Returns:
            System prompt string
        """
        return f"""You are an expert business intelligence analyst specializing in {focus_area}.

Your task is to analyze communication data, contact information, and knowledge graphs to extract valuable business insights and strategic recommendations.

Focus on:
1. Identifying key business relationships and their strategic importance
2. Detecting business opportunities and potential collaborations
3. Recognizing competitive threats and market positioning
4. Understanding organizational dynamics and decision-making patterns
5. Uncovering professional networks and spheres of influence

Structure your analysis with these sections:
- Executive Summary: Brief, high-impact overview of key findings
- Key Relationships: Analysis of most valuable business connections
- Strategic Opportunities: Business possibilities identified from the data
- Competitive Landscape: Market positioning and competitive dynamics
- Recommendations: Actionable strategic steps based on your analysis

Be concise, insightful, and focused on practical business value. 
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
        prompt = f"""Please analyze the following business data and provide strategic intelligence insights focused on {focus_area}.

## CONTACTS DATA
I'm providing information about {len(selected_contacts)} business contacts with their enriched profiles:

```json
{self._format_json_for_prompt(selected_contacts)}
```

## EMAIL COMMUNICATIONS
Here are {len(selected_emails)} relevant email exchanges that provide context on business relationships:

```json
{self._format_json_for_prompt(selected_emails)}
```
"""

        # Add knowledge tree if available
        if knowledge_tree and knowledge_tree.get("nodes"):
            prompt += f"""
## KNOWLEDGE RELATIONSHIPS
Here is a knowledge graph showing relationships between entities:

```json
{self._format_json_for_prompt(knowledge_tree)}
```
"""

        # Add specific instructions
        prompt += f"""
Based on this data, please provide:

1. An insightful business intelligence analysis
2. Strategic opportunities identified from these communications
3. Key relationship insights and their business implications
4. Actionable recommendations for business advantage

Focus specifically on {focus_area} aspects and organize your response according to the structure in your instructions.
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
            "executive_summary": "",
            "key_relationships": [],
            "strategic_opportunities": [],
            "competitive_landscape": "",
            "recommendations": []
        }
        
        if not response_text:
            return result
            
        # Extract executive summary
        if "Executive Summary" in response_text:
            parts = response_text.split("Executive Summary", 1)
            if len(parts) > 1:
                summary_section = parts[1].split("\n#", 1)[0].split("Key Relationships", 1)[0].strip()
                result["executive_summary"] = summary_section
        
        # Extract key relationships
        if "Key Relationships" in response_text:
            parts = response_text.split("Key Relationships", 1)
            if len(parts) > 1:
                relations_text = parts[1].split("\n#", 1)[0].split("Strategic Opportunities", 1)[0]
                # Extract bullet points
                relations = []
                for line in relations_text.split("\n"):
                    if line.strip().startswith("- ") or line.strip().startswith("* "):
                        relations.append(line.strip()[2:])
                if relations:
                    result["key_relationships"] = relations
                else:
                    result["key_relationships"] = [relations_text.strip()]
        
        # Extract strategic opportunities
        if "Strategic Opportunities" in response_text:
            parts = response_text.split("Strategic Opportunities", 1)
            if len(parts) > 1:
                opps_text = parts[1].split("\n#", 1)[0].split("Competitive Landscape", 1)[0]
                # Extract bullet points
                opps = []
                for line in opps_text.split("\n"):
                    if line.strip().startswith("- ") or line.strip().startswith("* "):
                        opps.append(line.strip()[2:])
                if opps:
                    result["strategic_opportunities"] = opps
                else:
                    result["strategic_opportunities"] = [opps_text.strip()]
        
        # Extract competitive landscape
        if "Competitive Landscape" in response_text:
            parts = response_text.split("Competitive Landscape", 1)
            if len(parts) > 1:
                landscape = parts[1].split("\n#", 1)[0].split("Recommendations", 1)[0].strip()
                result["competitive_landscape"] = landscape
        
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
        Validate input data for business analysis
        
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
            summary["contact_companies"] = list(set(
                c.get("company", "") for c in contacts 
                if c.get("company")
            ))[:5]  # List up to 5 unique companies
            
        if "emails" in input_data:
            emails = input_data["emails"]
            summary["emails_count"] = len(emails)
            summary["email_date_range"] = {
                "oldest": min((e.get("date", "") for e in emails), default="unknown"),
                "newest": max((e.get("date", "") for e in emails), default="unknown")
            }
            
        if "specific_focus" in input_data:
            summary["focus_area"] = input_data["specific_focus"]
            
        if "knowledge_tree" in input_data:
            tree = input_data["knowledge_tree"]
            summary["knowledge_nodes"] = len(tree.get("nodes", []))
            summary["knowledge_edges"] = len(tree.get("edges", []))
            
        return summary
