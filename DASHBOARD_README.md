# Strategic Intelligence System - Manual Test Dashboard

## Overview

This dashboard provides a comprehensive manual testing interface for the Strategic Intelligence System. It allows you to test each step of the complete flow, from sent email analysis to advanced intelligence generation.

## Accessing the Dashboard

1. Start the application:
   ```bash
   python app.py
   ```

2. Open your browser and navigate to:
   ```
   http://localhost:5000/dashboard
   ```

## Complete Flow Testing

The dashboard is organized into 6 main steps that follow the complete intelligence pipeline:

### Step 1: Sent Email Contact Import
**Purpose**: Extract trusted contacts from sent emails
**Files Involved**:
- `gmail/analyzer.py` - SentEmailAnalyzer class
- `gmail/client.py` - GmailClient for API access
- `api/routes.py` - `/api/gmail/analyze-sent` endpoint
- `storage/postgres_client.py` - Contact storage

**What it does**:
- Analyzes sent emails to identify trusted contacts
- Calculates engagement scores and trust tiers
- Stores contact information in PostgreSQL

### Step 2: Contact List Presentation
**Purpose**: View and filter extracted contacts
**Files Involved**:
- `api/routes.py` - `/api/contacts` endpoint
- `storage/postgres_client.py` - Contact retrieval
- `models/contact.py` - Contact data model

**What it does**:
- Displays all extracted contacts
- Allows filtering by trust tier
- Shows contact details (frequency, domain, engagement score)

### Step 3: Contact Augmentation
**Purpose**: Enrich contacts with web data
**Files Involved**:
- `intelligence/web_enrichment/enrichment_orchestrator.py`
- `intelligence/web_enrichment/linkedin_scraper.py`
- `intelligence/web_enrichment/twitter_scraper.py`
- `intelligence/web_enrichment/company_scraper.py`

**What it does**:
- Scrapes LinkedIn profiles for professional information
- Gathers Twitter data for social insights
- Collects company information and industry data
- Enhances contact profiles with external data

### Step 4: Email Import
**Purpose**: Import emails based on trusted contacts
**Files Involved**:
- `gmail/email_processor.py` - Email processing logic
- `gmail/client.py` - Gmail API wrapper
- `api/routes.py` - `/api/emails/sync` endpoint
- `storage/postgres_client.py` - Email storage

**What it does**:
- Imports emails from trusted contacts only
- Processes email content and metadata
- Stores emails with vector embeddings for semantic search

### Step 5: Knowledge Tree Creation
**Purpose**: Build intelligence from collected data
**Files Involved**:
- `intelligence/claude_analysis.py` - Claude AI analysis
- `intelligence/knowledge_tree/tree_builder.py`
- `intelligence/analysts/base_analyst.py`
- `api/intelligence_routes.py` - Intelligence endpoints

**What it does**:
- Runs 5 specialized Claude analysts in parallel
- Builds hierarchical knowledge tree
- Creates relationship graphs in Neo4j
- Generates vector embeddings for similarity search

### Step 6: Advanced Features
**Purpose**: Generate predictions, insights, and advanced intelligence
**Files Involved**:
- `intelligence/predictions/prediction_engine.py`
- `intelligence/calendar/calendar_intelligence.py`
- `api/intelligence_routes.py`
- `intelligence/deep_augmentation.py`

**What it does**:
- **Predictions**: Generate AI-powered predictions about relationships and opportunities
- **Insights**: Extract actionable insights from the knowledge tree
- **Relationships**: Visualize and analyze relationship networks
- **Deep Augmentation**: Perform advanced knowledge tree augmentation

## Testing Instructions

1. **Start with Step 1**: Click "Analyze Sent Emails" to extract contacts
2. **Review Contacts**: Use Step 2 to view and filter the extracted contacts
3. **Enrich Data**: Use Step 3 to add web data to contacts
4. **Import Emails**: Use Step 4 to import emails from trusted contacts
5. **Build Intelligence**: Use Step 5 to create the knowledge tree
6. **Explore Advanced Features**: Use Step 6 to test predictions, insights, and relationships

## System Status

The dashboard includes a system health check that monitors:
- PostgreSQL database connectivity
- Neo4j graph database status
- Redis cache health
- ChromaDB vector database status

## Error Handling

Each step includes comprehensive error handling:
- API call failures are displayed with detailed error messages
- Loading states show when operations are in progress
- Status badges indicate success, failure, or pending states

## File Structure

The dashboard references these key files in the system:

```
strategic-intelligence-system/
├── app.py                      # Main Flask application
├── static/
│   └── dashboard.html         # This dashboard file
├── api/
│   ├── routes.py              # Main API endpoints
│   └── intelligence_routes.py # Intelligence endpoints
├── gmail/
│   ├── analyzer.py            # Sent email analysis
│   ├── client.py              # Gmail API client
│   └── email_processor.py     # Email processing
├── intelligence/
│   ├── web_enrichment/        # Contact enrichment
│   ├── analysts/              # Claude AI analysts
│   ├── knowledge_tree/        # Knowledge tree building
│   ├── predictions/           # Prediction engine
│   └── calendar/              # Calendar intelligence
└── storage/
    └── postgres_client.py     # Database operations
```

## Troubleshooting

If you encounter issues:

1. **Check System Health**: Use the system health check to verify all services are running
2. **Review Error Messages**: Each step displays detailed error information
3. **Check Logs**: Monitor the application logs for detailed error information
4. **Verify Authentication**: Ensure you're authenticated with Gmail before testing

## Next Steps

After testing the complete flow:

1. Review the generated knowledge tree and insights
2. Explore the relationship visualizations
3. Test the prediction capabilities
4. Validate the contact enrichment data
5. Check the email import results

This dashboard provides a comprehensive way to validate the entire Strategic Intelligence System pipeline and ensure all components are working correctly together. 