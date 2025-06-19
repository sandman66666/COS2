"""
Example of Rich Intelligence Data
================================
This is what comprehensive contact enrichment should look like.
"""

# Example: What we SHOULD get for mikey@suno.ai after deep enrichment
rich_intelligence_example = {
    "email": "mikey@suno.ai",
    "basic_info": {
        "name": "Michael Shulman",
        "title": "Co-Founder & CEO",
        "company": "Suno AI",
        "location": "San Francisco, CA",
        "confirmed_identity": True,
        "confidence": 0.95
    },
    
    "personal_intelligence": {
        "biography": {
            "background": "Former Meta AI researcher turned entrepreneur",
            "education": "Stanford University - BS Computer Science, PhD Machine Learning",
            "career_trajectory": "Research Scientist → Meta AI → Founder",
            "notable_achievements": [
                "Led music generation research at Meta",
                "Published 15+ papers on audio ML",
                "Founded Suno AI in 2023"
            ]
        },
        "personality_profile": {
            "communication_style": "Technical but accessible, often uses music metaphors",
            "decision_making": "Data-driven with creative intuition",
            "leadership_style": "Collaborative, believes in democratizing music creation",
            "core_values": ["Creativity", "Accessibility", "Technical Excellence"],
            "interests": ["Electronic music production", "Audio synthesis", "Creative AI"]
        },
        "social_presence": {
            "twitter": {
                "handle": "@mikeyshulman",
                "followers": 12500,
                "bio": "Building AI that helps everyone make music. Co-founder @sunoai",
                "recent_themes": ["AI music generation", "Creative tools", "Music democratization"],
                "posting_frequency": "Daily",
                "engagement_style": "Thoughtful, technical insights with humor"
            },
            "linkedin": {
                "profile_url": "linkedin.com/in/michaelshulman",
                "connections": "2000+",
                "recent_posts": [
                    "Thoughts on the future of AI-generated music",
                    "Why we built Suno to be accessible to everyone",
                    "The intersection of creativity and AI"
                ]
            }
        }
    },
    
    "professional_intelligence": {
        "career_history": [
            {
                "company": "Suno AI",
                "title": "Co-Founder & CEO",
                "duration": "2023 - Present",
                "description": "Building AI music generation platform",
                "key_achievements": [
                    "Raised $125M Series B at $500M valuation",
                    "Scaled to 10M+ users in first year",
                    "Built team of 45 engineers and researchers"
                ]
            },
            {
                "company": "Meta (Facebook)",
                "title": "Research Scientist, AI Audio",
                "duration": "2019 - 2023",
                "description": "Led audio ML research for consumer products",
                "key_projects": [
                    "MusicLM architecture development",
                    "Real-time audio generation systems",
                    "Multimodal audio-visual models"
                ]
            }
        ],
        "expertise_areas": [
            "Audio Machine Learning",
            "Music Information Retrieval", 
            "Generative AI Models",
            "Product Leadership",
            "Startup Scaling"
        ],
        "speaking_engagements": [
            {
                "event": "ICML 2024",
                "topic": "Democratizing Music Creation with AI",
                "date": "2024-07-25"
            },
            {
                "event": "Music Tech Summit",
                "topic": "The Future of AI Music Generation",
                "date": "2024-09-15"
            }
        ]
    },
    
    "company_intelligence": {
        "suno_ai": {
            "overview": {
                "name": "Suno AI",
                "founded": "2023",
                "headquarters": "San Francisco, CA",
                "industry": "AI Music Technology",
                "stage": "Series B",
                "employees": "45-50"
            },
            "financial_data": {
                "total_funding": "$125M",
                "last_round": {
                    "type": "Series B",
                    "amount": "$125M",
                    "date": "2024-05-15",
                    "valuation": "$500M",
                    "lead_investor": "Lightspeed Venture Partners"
                },
                "investors": [
                    "Lightspeed Venture Partners",
                    "NFX",
                    "Khosla Ventures",
                    "Matrix Partners"
                ]
            },
            "product_intelligence": {
                "main_product": "AI-powered song creation platform",
                "key_features": [
                    "Text-to-song generation",
                    "Style transfer",
                    "Collaborative creation tools",
                    "Commercial licensing"
                ],
                "user_metrics": {
                    "registered_users": "10M+",
                    "songs_generated": "50M+",
                    "monthly_active_users": "2M+"
                },
                "competitive_position": "Market leader in consumer AI music generation"
            },
            "technology_stack": {
                "ml_infrastructure": ["PyTorch", "CUDA", "Kubernetes"],
                "audio_processing": ["FFmpeg", "librosa", "torchaudio"],
                "cloud_providers": ["AWS", "Google Cloud"],
                "frontend": ["React", "TypeScript", "WebAudio API"],
                "backend": ["Python", "FastAPI", "PostgreSQL"]
            },
            "market_intelligence": {
                "competitors": [
                    {"name": "Mubert", "strength": "B2B licensing"},
                    {"name": "AIVA", "strength": "Classical music"},
                    {"name": "Boomy", "strength": "Simplicity"}
                ],
                "market_size": "$2.5B AI music market by 2025",
                "growth_trajectory": "300% YoY user growth"
            }
        }
    },
    
    "network_intelligence": {
        "professional_connections": [
            {
                "name": "Fei-Fei Li",
                "relationship": "Former Stanford advisor",
                "connection_strength": "Strong",
                "mutual_connections": 15
            },
            {
                "name": "Yann LeCun", 
                "relationship": "Meta AI colleague",
                "connection_strength": "Strong",
                "mutual_connections": 8
            }
        ],
        "investor_relationships": [
            {
                "investor": "Ravi Mhatre (Lightspeed)",
                "relationship": "Board member",
                "connection_strength": "Very Strong"
            }
        ],
        "industry_influence": {
            "thought_leadership_score": 8.5,
            "media_mentions": 45,
            "conference_speaking": 12,
            "academic_citations": 450
        }
    },
    
    "content_intelligence": {
        "recent_interviews": [
            {
                "publication": "TechCrunch",
                "title": "Suno AI's CEO on the future of music creation",
                "date": "2024-06-01",
                "key_quotes": [
                    "Music shouldn't be limited to those who can play instruments",
                    "AI is democratizing creativity in unprecedented ways"
                ],
                "topics": ["AI democratization", "Creative tools", "Music industry"]
            }
        ],
        "blog_posts": [
            {
                "title": "Why AI Music Generation Matters",
                "platform": "Medium",
                "date": "2024-05-15",
                "themes": ["Accessibility", "Creative AI", "Music democratization"]
            }
        ],
        "podcast_appearances": [
            {
                "show": "The AI Podcast",
                "episode": "Building the Future of Music with AI",
                "date": "2024-07-01",
                "personality_insights": [
                    "Speaks with technical precision but accessible language",
                    "Passionate about music democratization",
                    "Balances optimism with realistic challenges"
                ]
            }
        ],
        "communication_patterns": {
            "preferred_topics": [
                "AI music generation technology",
                "Creative democratization", 
                "Technical innovation",
                "Product development"
            ],
            "speaking_style": "Technical but accessible, uses analogies",
            "key_phrases": [
                "Democratizing creativity",
                "AI as a creative partner",
                "Accessible music creation"
            ]
        }
    },
    
    "strategic_intelligence": {
        "business_priorities": [
            "Scaling user acquisition",
            "Improving model quality",
            "Building creator monetization",
            "Expanding to enterprise"
        ],
        "potential_opportunities": [
            "Partnership with music streaming platforms",
            "Integration with DAWs (Digital Audio Workstations)",
            "Educational institution partnerships",
            "Licensing deals with content creators"
        ],
        "decision_making_style": {
            "approach": "Data-driven with user feedback integration",
            "timeline": "Moves quickly but validates thoroughly",
            "risk_tolerance": "Moderate - balances innovation with stability"
        },
        "meeting_preparation": {
            "recommended_talking_points": [
                "AI music generation technology trends",
                "Democratization of creative tools",
                "Scaling challenges in consumer AI products",
                "Music industry transformation"
            ],
            "potential_interests": [
                "Partnership opportunities",
                "Technical collaboration",
                "Market expansion strategies",
                "Creative AI applications"
            ]
        }
    },
    
    "enrichment_metadata": {
        "confidence_score": 0.92,
        "last_updated": "2024-08-15T10:30:00Z",
        "sources_used": [
            "Crunchbase Pro",
            "LinkedIn Premium",
            "News APIs",
            "Wikipedia",
            "PitchBook",
            "Company website",
            "Social media analysis",
            "Interview transcripts"
        ],
        "next_update_due": "2024-09-15",
        "data_freshness": "High"
    }
}

# This is the level of intelligence we should be providing!
print("Current system confidence: ~0.4-0.6")
print("Target system confidence: ~0.9+")
print("Current data sources: 2-3")
print("Target data sources: 8-12")
print("Current insight depth: Surface level")
print("Target insight depth: Strategic & actionable") 