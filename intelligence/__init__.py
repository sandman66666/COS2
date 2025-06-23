"""
Strategic Intelligence System - Flow-Based Organization

This module is organized by the strategic intelligence pipeline flow:

a. Core Infrastructure (a_core/)
   - claude_analysis.py: Core Claude API integration
   
b. Data Collection & Organization (b_data_collection/) 
   - gmail/: Gmail API integration & email processing
     - client.py: Gmail API client
     - analyzer.py: Email analysis & contact extraction
     - email_processor.py: Email content processing
   - data_organizer.py: Multi-source content aggregation
   - communication_intelligence.py: Email analysis & relationship status
   - behavioral_intelligence_system.py: Communication patterns
   
c. Content Processing & Summarization (c_content_processing/)
   - content_summarizer.py: Lightweight content summaries
   - claude_content_consolidator.py: Claude-powered content consolidation
   
d. Enrichment & Augmentation (d_enrichment/)
   - enhanced_enrichment.py: Contact enrichment analysis
   - contact_enrichment_integration.py: Enrichment orchestration
   - web_enrichment/: External data source integration
   
e. Strategic Analysis (e_strategic_analysis/)
   - strategic_analyzer.py: Strategic analysis orchestration
   - ceo_strategic_intelligence_system.py: CEO intelligence endpoints
   - analysts/: Specialized analyst modules
   
f. Knowledge Integration (f_knowledge_integration/)
   - knowledge_tree_orchestrator.py: Main pipeline orchestrator
   - advanced_knowledge_system.py: Legacy knowledge system
   - knowledge_tree/: Knowledge tree building modules
   
g. Real-time Updates & Alerts (g_realtime_updates/)
   - incremental_knowledge_system.py: Live data updates
   - tactical_alerts_system.py: Alert generation & management
   - web_search_integration.py: External research integration
   
future/: Future Features
   - calendar/: Calendar intelligence (planned)
   - predictions/: Predictive analytics (planned)

Complete Intelligence Pipeline Flow:
    Gmail Data → Organization → Processing → Enrichment → Analysis → Integration → Updates
    
Usage:
    Import specific modules from their flow-based directories:
    from intelligence.b_data_collection.gmail.client import GmailClient
    from intelligence.a_core.claude_analysis import KnowledgeTreeBuilder
    from intelligence.f_knowledge_integration.knowledge_tree_orchestrator import KnowledgeTreeOrchestrator
""" 