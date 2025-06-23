# intelligence/analysts/technical_analyst.py
"""
Technical Intelligence Analyst
===========================
Specialized analyst for technical insights and technology trends.
Powered by Claude Opus with multi-tenant isolation.
"""

import json
from typing import Dict, List, Optional, Any
from datetime import datetime

from utils.logging import structured_logger as logger
from .base_analyst import BaseAnalyst

class TechnicalIntelligenceAnalyst(BaseAnalyst):
    """
    Technical intelligence analyst
    
    Analyzes communications and documents to extract technical insights,
    identify technology trends, and provide technical strategy recommendations.
    """
    
    def __init__(self, user_id: int, anthropic_api_key: str = None):
        """
        Initialize technical analyst
        
        Args:
            user_id: User ID for multi-tenant isolation
            anthropic_api_key: Optional API key for Claude Opus
        """
        super().__init__(user_id, anthropic_api_key)
        self.analyst_name = "technical_intelligence"
        self.analyst_description = "Technical insights and technology trend analyst"
        
        # Customize Claude parameters
        self.max_tokens = 4000
        self.temperature = 0.1  # Lower temperature for more factual technical analysis
    
    async def generate_intelligence(self, data: Dict) -> Dict:
        """
        Generate technical intelligence from provided data
        
        Args:
            data: Dictionary containing:
                - emails: List of relevant email exchanges
                - (optional) documents: List of technical documents
                - (optional) knowledge_tree: Knowledge tree data
                - (optional) specific_focus: Technical area to focus on
                
        Returns:
            Dictionary with technical insights and recommendations
        """
        # Validate critical inputs
        if not data.get("emails") and not data.get("documents"):
            logger.error(
                "Missing required data for technical analysis",
                user_id=self.user_id
            )
            return {"error": "Insufficient data for technical analysis"}
            
        try:
            # Extract data elements
            emails = data.get("emails", [])
            documents = data.get("documents", [])
            knowledge_tree = data.get("knowledge_tree", {})
            focus_area = data.get("specific_focus", "technology trends")
            
            # Prepare specialized system prompt
            system_prompt = self._create_system_prompt(focus_area)
            
            # Prepare user prompt with data
            user_prompt = self._create_user_prompt(
                emails=emails,
                documents=documents,
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
                "emails": len(emails),
                "documents": len(documents),
                "knowledge_nodes": len(knowledge_tree.get("nodes", [])) if isinstance(knowledge_tree.get("nodes"), list) else 0
            }
            
            return structured_result
            
        except Exception as e:
            logger.error(
                "Error generating technical intelligence",
                error=str(e),
                user_id=self.user_id
            )
            return {"error": f"Technical intelligence generation failed: {str(e)}"}
    
    def _create_system_prompt(self, focus_area: str) -> str:
        """
        Create system prompt for Claude Opus
        
        Args:
            focus_area: Technical area to focus on
            
        Returns:
            System prompt string
        """
        return f"""You are an expert technical intelligence analyst specializing in {focus_area}.

Your task is to analyze communications, documents, and knowledge graphs to extract valuable technical insights, identify technology trends, and provide strategic technical recommendations.

Focus on:
1. Identifying key technical topics and themes in communications
2. Detecting emerging technology trends and innovations
3. Recognizing technical challenges and potential solutions
4. Understanding technical dependencies and relationships
5. Evaluating technical strategies and architectural approaches

Structure your analysis with these sections:
- Technical Summary: Brief overview of key technical findings
- Key Technologies: Analysis of most significant technologies identified
- Technical Trends: Emerging patterns and directional shifts
- Technical Challenges: Identified issues and potential risks
- Recommendations: Actionable technical strategy recommendations

Be precise, evidence-based, and focused on practical technical value.
Base all insights on the provided data and make reasonable technical inferences where appropriate.
Format your response as a combination of concise technical paragraphs and bullet points for readability.

Maintain absolute confidentiality and privacy in your analysis.
Do not include any information that could be considered sensitive or proprietary.
"""
    
    def _create_user_prompt(
        self, 
        emails: List[Dict],
        documents: List[Dict],
        knowledge_tree: Dict,
        focus_area: str
    ) -> str:
        """
        Create user prompt with data for analysis
        
        Args:
            emails: List of relevant email exchanges
            documents: List of technical documents
            knowledge_tree: Knowledge graph data
            focus_area: Area to focus analysis on
            
        Returns:
            Formatted user prompt
        """
        # Limit data volume to fit context window
        max_emails = min(30, len(emails))
        max_documents = min(10, len(documents))
        
        # Select most important emails and documents
        selected_emails = emails[:max_emails]
        selected_documents = documents[:max_documents]
        
        # Format prompt
        prompt = f"""Please analyze the following technical data and provide insights focused on {focus_area}.

## EMAIL COMMUNICATIONS
Here are {len(selected_emails)} relevant email exchanges containing technical discussions:

```json
{self._format_json_for_prompt(selected_emails)}
```
"""

        # Add documents if available
        if selected_documents:
            prompt += f"""
## TECHNICAL DOCUMENTS
Here are {len(selected_documents)} technical documents for analysis:

```json
{self._format_json_for_prompt(selected_documents)}
```
"""

        # Add knowledge tree if available
        if knowledge_tree and knowledge_tree.get("nodes"):
            prompt += f"""
## TECHNICAL KNOWLEDGE GRAPH
Here is a knowledge graph showing technical relationships:

```json
{self._format_json_for_prompt(knowledge_tree)}
```
"""

        # Add specific instructions
        prompt += f"""
Based on this data, please provide:

1. A technical intelligence analysis identifying key technologies, trends, and patterns
2. An assessment of technical approaches and architectural decisions
3. Identification of potential technical challenges or risks
4. Technical strategy recommendations

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
            "technical_summary": "",
            "key_technologies": [],
            "technical_trends": [],
            "technical_challenges": [],
            "recommendations": []
        }
        
        if not response_text:
            return result
            
        # Extract technical summary
        if "Technical Summary" in response_text:
            parts = response_text.split("Technical Summary", 1)
            if len(parts) > 1:
                summary_section = parts[1].split("\n#", 1)[0].split("Key Technologies", 1)[0].strip()
                result["technical_summary"] = summary_section
        
        # Extract key technologies
        if "Key Technologies" in response_text:
            parts = response_text.split("Key Technologies", 1)
            if len(parts) > 1:
                tech_text = parts[1].split("\n#", 1)[0].split("Technical Trends", 1)[0]
                # Extract bullet points
                techs = []
                for line in tech_text.split("\n"):
                    if line.strip().startswith("- ") or line.strip().startswith("* "):
                        techs.append(line.strip()[2:])
                if techs:
                    result["key_technologies"] = techs
                else:
                    result["key_technologies"] = [tech_text.strip()]
        
        # Extract technical trends
        if "Technical Trends" in response_text:
            parts = response_text.split("Technical Trends", 1)
            if len(parts) > 1:
                trends_text = parts[1].split("\n#", 1)[0].split("Technical Challenges", 1)[0]
                # Extract bullet points
                trends = []
                for line in trends_text.split("\n"):
                    if line.strip().startswith("- ") or line.strip().startswith("* "):
                        trends.append(line.strip()[2:])
                if trends:
                    result["technical_trends"] = trends
                else:
                    result["technical_trends"] = [trends_text.strip()]
        
        # Extract technical challenges
        if "Technical Challenges" in response_text:
            parts = response_text.split("Technical Challenges", 1)
            if len(parts) > 1:
                challenges_text = parts[1].split("\n#", 1)[0].split("Recommendations", 1)[0]
                # Extract bullet points
                challenges = []
                for line in challenges_text.split("\n"):
                    if line.strip().startswith("- ") or line.strip().startswith("* "):
                        challenges.append(line.strip()[2:])
                if challenges:
                    result["technical_challenges"] = challenges
                else:
                    result["technical_challenges"] = [challenges_text.strip()]
        
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
        Validate input data for technical analysis
        
        Args:
            input_data: Input data dictionary
            
        Returns:
            Error message if validation fails, None if valid
        """
        if not input_data:
            return "No input data provided"
            
        if not input_data.get("emails") and not input_data.get("documents"):
            return "Missing required data: need either emails or documents"
            
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
        
        if "emails" in input_data:
            emails = input_data["emails"]
            summary["emails_count"] = len(emails)
            
            # Extract technical terms for summary
            tech_terms = set()
            tech_keywords = [
                "api", "architecture", "aws", "cloud", "code", "database", 
                "deployment", "development", "docker", "framework", "github", 
                "infrastructure", "kubernetes", "language", "microservices", 
                "platform", "programming", "python", "repository", "security", 
                "server", "service", "software", "system", "technology"
            ]
            
            for email in emails:
                content = email.get("body", "").lower()
                for term in tech_keywords:
                    if term in content:
                        tech_terms.add(term)
            
            summary["technical_terms"] = list(tech_terms)[:10]  # Top 10 terms
            
        if "documents" in input_data:
            documents = input_data["documents"]
            summary["documents_count"] = len(documents)
            
            # Categorize documents by type
            doc_types = {}
            for doc in documents:
                doc_type = doc.get("type", "unknown")
                doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
                
            summary["document_types"] = doc_types
            
        if "specific_focus" in input_data:
            summary["focus_area"] = input_data["specific_focus"]
            
        return summary
