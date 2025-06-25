"""
Organized Knowledge Store
Stores structured summaries from Phase 1 data organization for fast access by Phase 2 strategic analysis.
Provides efficient storage and retrieval of organized content, communication profiles, and summaries.
"""

import json
import sqlite3
import pickle
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import asdict

from ..intelligence.data_organizer import OrganizedContent, ContentItem, TopicCluster
from ..intelligence.communication_intelligence import CommunicationProfile
from ..intelligence.content_summarizer import ContentSummary, ContactSummary

class OrganizedKnowledgeStore:
    def __init__(self, db_path: str = "data/organized_knowledge.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize database schema for organized knowledge"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Organized content table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS organized_content (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                content_data BLOB,
                metadata TEXT
            )
        ''')
        
        # Topic summaries table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS topic_summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                topic_name TEXT NOT NULL,
                priority_level TEXT,
                business_domain TEXT,
                summary_data BLOB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Contact summaries table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS contact_summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                email TEXT NOT NULL,
                name TEXT,
                company TEXT,
                role TEXT,
                relationship_status TEXT,
                summary_data BLOB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Communication profiles table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS communication_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                email TEXT NOT NULL,
                relationship_status TEXT,
                engagement_score REAL,
                response_rate REAL,
                profile_data BLOB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Strategic analysis results table (for Phase 2 output)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS strategic_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                analysis_type TEXT,
                agent_name TEXT,
                results_data BLOB,
                confidence_score REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_topic ON topic_summaries (user_id, topic_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_contact ON contact_summaries (user_id, email)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_comm ON communication_profiles (user_id, email)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_analysis ON strategic_analysis (user_id, analysis_type)')
        
        conn.commit()
        conn.close()

    def store_organized_content(self, user_id: int, organized_content: OrganizedContent, 
                              topic_summaries: Dict[str, ContentSummary],
                              contact_summaries: Dict[str, ContactSummary]) -> int:
        """Store complete organized content and summaries"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Store main organized content
            content_blob = pickle.dumps(organized_content)
            metadata = json.dumps({
                "total_topics": len(organized_content.topics),
                "total_contacts": len(organized_content.communication_profiles),
                "total_content_items": len(organized_content.content_index),
                "business_domains": list(organized_content.business_domains.keys())
            })
            
            cursor.execute('''
                INSERT INTO organized_content (user_id, content_data, metadata)
                VALUES (?, ?, ?)
            ''', (user_id, content_blob, metadata))
            
            content_id = cursor.lastrowid
            
            # Store topic summaries
            for topic_name, summary in topic_summaries.items():
                summary_blob = pickle.dumps(summary)
                cursor.execute('''
                    INSERT INTO topic_summaries 
                    (user_id, topic_name, priority_level, business_domain, summary_data)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user_id, topic_name, summary.priority_level, 
                     organized_content.topics.get(topic_name, TopicCluster("", [], [], set(), 
                     (datetime.now(), datetime.now()), "general")).business_domain, summary_blob))
            
            # Store contact summaries
            for email, summary in contact_summaries.items():
                summary_blob = pickle.dumps(summary)
                cursor.execute('''
                    INSERT INTO contact_summaries 
                    (user_id, email, name, company, role, relationship_status, summary_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (user_id, email, summary.name, summary.company, 
                     summary.role, summary.relationship_status, summary_blob))
            
            # Store communication profiles
            for email, profile in organized_content.communication_profiles.items():
                profile_blob = pickle.dumps(profile)
                cursor.execute('''
                    INSERT INTO communication_profiles 
                    (user_id, email, relationship_status, engagement_score, response_rate, profile_data)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (user_id, email, profile.relationship_status.value, 
                     profile.engagement_score, profile.response_rate, profile_blob))
            
            conn.commit()
            print(f"✅ Stored organized content for user {user_id} (ID: {content_id})")
            return content_id
            
        except Exception as e:
            conn.rollback()
            print(f"❌ Error storing organized content: {e}")
            raise
        finally:
            conn.close()

    def get_organized_content(self, user_id: int, content_id: Optional[int] = None) -> Optional[OrganizedContent]:
        """Retrieve organized content for user"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            if content_id:
                cursor.execute('''
                    SELECT content_data FROM organized_content 
                    WHERE user_id = ? AND id = ?
                ''', (user_id, content_id))
            else:
                # Get latest content
                cursor.execute('''
                    SELECT content_data FROM organized_content 
                    WHERE user_id = ? ORDER BY created_at DESC LIMIT 1
                ''', (user_id,))
            
            row = cursor.fetchone()
            if row:
                return pickle.loads(row[0])
            return None
            
        finally:
            conn.close()

    def get_topic_summaries(self, user_id: int, priority_filter: Optional[str] = None,
                          business_domain: Optional[str] = None) -> Dict[str, ContentSummary]:
        """Get topic summaries with optional filtering"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            query = '''
                SELECT topic_name, summary_data FROM topic_summaries 
                WHERE user_id = ?
            '''
            params = [user_id]
            
            if priority_filter:
                query += ' AND priority_level = ?'
                params.append(priority_filter)
            
            if business_domain:
                query += ' AND business_domain = ?'
                params.append(business_domain)
            
            query += ' ORDER BY updated_at DESC'
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            summaries = {}
            for topic_name, summary_blob in rows:
                summaries[topic_name] = pickle.loads(summary_blob)
            
            return summaries
            
        finally:
            conn.close()

    def get_contact_summaries(self, user_id: int, relationship_status: Optional[str] = None,
                            role_filter: Optional[str] = None) -> Dict[str, ContactSummary]:
        """Get contact summaries with optional filtering"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            query = '''
                SELECT email, summary_data FROM contact_summaries 
                WHERE user_id = ?
            '''
            params = [user_id]
            
            if relationship_status:
                query += ' AND relationship_status = ?'
                params.append(relationship_status)
            
            if role_filter:
                query += ' AND role = ?'
                params.append(role_filter)
            
            query += ' ORDER BY updated_at DESC'
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            summaries = {}
            for email, summary_blob in rows:
                summaries[email] = pickle.loads(summary_blob)
            
            return summaries
            
        finally:
            conn.close()

    def get_communication_profiles(self, user_id: int) -> Dict[str, CommunicationProfile]:
        """Get all communication profiles for user"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT email, profile_data FROM communication_profiles 
                WHERE user_id = ? ORDER BY engagement_score DESC
            ''', (user_id,))
            
            rows = cursor.fetchall()
            profiles = {}
            for email, profile_blob in rows:
                profiles[email] = pickle.loads(profile_blob)
            
            return profiles
            
        finally:
            conn.close()

    def store_strategic_analysis(self, user_id: int, analysis_type: str, agent_name: str,
                               results: Any, confidence_score: float = 0.0) -> int:
        """Store results from Phase 2 strategic analysis"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            results_blob = pickle.dumps(results)
            cursor.execute('''
                INSERT INTO strategic_analysis 
                (user_id, analysis_type, agent_name, results_data, confidence_score)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, analysis_type, agent_name, results_blob, confidence_score))
            
            analysis_id = cursor.lastrowid
            conn.commit()
            
            print(f"✅ Stored {agent_name} analysis (ID: {analysis_id})")
            return analysis_id
            
        except Exception as e:
            conn.rollback()
            print(f"❌ Error storing strategic analysis: {e}")
            raise
        finally:
            conn.close()

    def get_strategic_analysis(self, user_id: int, analysis_type: Optional[str] = None,
                             agent_name: Optional[str] = None) -> List[Dict]:
        """Get strategic analysis results"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            query = '''
                SELECT analysis_type, agent_name, results_data, confidence_score, created_at
                FROM strategic_analysis WHERE user_id = ?
            '''
            params = [user_id]
            
            if analysis_type:
                query += ' AND analysis_type = ?'
                params.append(analysis_type)
            
            if agent_name:
                query += ' AND agent_name = ?'
                params.append(agent_name)
            
            query += ' ORDER BY created_at DESC'
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            results = []
            for analysis_type, agent_name, results_blob, confidence, created_at in rows:
                results.append({
                    'analysis_type': analysis_type,
                    'agent_name': agent_name,
                    'results': pickle.loads(results_blob),
                    'confidence_score': confidence,
                    'created_at': created_at
                })
            
            return results
            
        finally:
            conn.close()

    def get_summary_stats(self, user_id: int) -> Dict[str, Any]:
        """Get summary statistics for user's organized knowledge"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get latest organized content metadata
            cursor.execute('''
                SELECT metadata FROM organized_content 
                WHERE user_id = ? ORDER BY created_at DESC LIMIT 1
            ''', (user_id,))
            
            metadata_row = cursor.fetchone()
            metadata = json.loads(metadata_row[0]) if metadata_row else {}
            
            # Get topic distribution by priority
            cursor.execute('''
                SELECT priority_level, COUNT(*) FROM topic_summaries 
                WHERE user_id = ? GROUP BY priority_level
            ''', (user_id,))
            
            priority_dist = dict(cursor.fetchall())
            
            # Get relationship status distribution
            cursor.execute('''
                SELECT relationship_status, COUNT(*) FROM contact_summaries 
                WHERE user_id = ? GROUP BY relationship_status
            ''', (user_id,))
            
            relationship_dist = dict(cursor.fetchall())
            
            # Get business domain distribution
            cursor.execute('''
                SELECT business_domain, COUNT(*) FROM topic_summaries 
                WHERE user_id = ? GROUP BY business_domain
            ''', (user_id,))
            
            domain_dist = dict(cursor.fetchall())
            
            # Get high-engagement contacts
            cursor.execute('''
                SELECT COUNT(*) FROM communication_profiles 
                WHERE user_id = ? AND engagement_score > 0.7
            ''', (user_id,))
            
            high_engagement_count = cursor.fetchone()[0]
            
            return {
                **metadata,
                "priority_distribution": priority_dist,
                "relationship_distribution": relationship_dist,
                "domain_distribution": domain_dist,
                "high_engagement_contacts": high_engagement_count,
                "last_updated": metadata_row[0] if metadata_row else None
            }
            
        finally:
            conn.close()

    def cleanup_old_data(self, user_id: int, days_old: int = 30):
        """Clean up old organized content data"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cutoff_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            cutoff_date = cutoff_date.replace(day=cutoff_date.day - days_old)
            
            # Clean up old organized content (keep latest 3)
            cursor.execute('''
                DELETE FROM organized_content 
                WHERE user_id = ? AND created_at < ? 
                AND id NOT IN (
                    SELECT id FROM organized_content 
                    WHERE user_id = ? ORDER BY created_at DESC LIMIT 3
                )
            ''', (user_id, cutoff_date, user_id))
            
            deleted_content = cursor.rowcount
            
            # Clean up old strategic analyses (keep latest 10 of each type)
            cursor.execute('''
                DELETE FROM strategic_analysis 
                WHERE user_id = ? AND created_at < ?
                AND id NOT IN (
                    SELECT id FROM (
                        SELECT id, ROW_NUMBER() OVER (
                            PARTITION BY analysis_type ORDER BY created_at DESC
                        ) as rn FROM strategic_analysis WHERE user_id = ?
                    ) WHERE rn <= 10
                )
            ''', (user_id, cutoff_date, user_id))
            
            deleted_analyses = cursor.rowcount
            
            conn.commit()
            print(f"🧹 Cleaned up {deleted_content} old content items and {deleted_analyses} old analyses")
            
        except Exception as e:
            conn.rollback()
            print(f"❌ Error cleaning up data: {e}")
            raise
        finally:
            conn.close()

    def export_knowledge_base(self, user_id: int, format: str = "json") -> Dict[str, Any]:
        """Export user's knowledge base for backup or analysis"""
        
        # Get all data
        organized_content = self.get_organized_content(user_id)
        topic_summaries = self.get_topic_summaries(user_id)
        contact_summaries = self.get_contact_summaries(user_id)
        communication_profiles = self.get_communication_profiles(user_id)
        strategic_analyses = self.get_strategic_analysis(user_id)
        
        if format == "json":
            # Convert to JSON-serializable format
            export_data = {
                "user_id": user_id,
                "export_timestamp": datetime.now().isoformat(),
                "organized_content": {
                    "topics": {name: asdict(cluster) for name, cluster in organized_content.topics.items()} if organized_content else {},
                    "business_domains": organized_content.business_domains if organized_content else {},
                    "timeline_events": len(organized_content.temporal_timeline) if organized_content else 0
                },
                "topic_summaries": {name: asdict(summary) for name, summary in topic_summaries.items()},
                "contact_summaries": {email: asdict(summary) for email, summary in contact_summaries.items()},
                "communication_profiles": {email: asdict(profile) for email, profile in communication_profiles.items()},
                "strategic_analyses": strategic_analyses
            }
            
            return export_data
        
        else:
            raise ValueError(f"Unsupported export format: {format}") 