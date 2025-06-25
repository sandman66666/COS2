"""
Synchronous PostgreSQL Client for Flask Integration
===================================================
This replaces the async PostgreSQL client to eliminate event loop conflicts
"""

import psycopg2
import psycopg2.pool
import psycopg2.extras
import logging
from typing import Any, Dict, List, Optional, Tuple
import json
from datetime import datetime
import threading

from storage.base_client import BaseStorageClient
from config.settings import (
    POSTGRES_HOST, 
    POSTGRES_PORT, 
    POSTGRES_USER, 
    POSTGRES_PASSWORD,
    POSTGRES_DB
)
from utils.logging import structured_logger as logger

class PostgresClientSync(BaseStorageClient):
    """Synchronous PostgreSQL client for Flask"""
    
    def __init__(self):
        self.host = POSTGRES_HOST
        self.port = POSTGRES_PORT
        self.user = POSTGRES_USER
        self.password = POSTGRES_PASSWORD
        self.database = POSTGRES_DB
        self.conn_pool = None
        self.vector_supported = False
        self._lock = threading.Lock()
        
    def connect(self) -> None:
        """Establish connection pool to PostgreSQL (synchronous)"""
        try:
            with self._lock:
                # Close existing pool if any
                if self.conn_pool:
                    self.conn_pool.closeall()
                
                # Create connection pool
                self.conn_pool = psycopg2.pool.ThreadedConnectionPool(
                    minconn=2,
                    maxconn=10,
                    host=self.host,
                    port=self.port,
                    user=self.user,
                    password=self.password,
                    database=self.database,
                    cursor_factory=psycopg2.extras.RealDictCursor
                )
                
                # Initialize schema
                self._init_schema()
                logger.info("Connected to PostgreSQL database (sync)", 
                           host=self.host, port=self.port, database=self.database)
        except Exception as e:
            logger.error(f"PostgreSQL sync connection error: {str(e)}")
            raise
    
    def disconnect(self) -> None:
        """Close all connections"""
        try:
            with self._lock:
                if self.conn_pool:
                    self.conn_pool.closeall()
                    self.conn_pool = None
                logger.info("Disconnected from PostgreSQL database (sync)")
        except Exception as e:
            logger.error(f"Error disconnecting from PostgreSQL: {str(e)}")
    
    def health_check(self) -> bool:
        """Check if PostgreSQL is available (synchronous)"""
        try:
            if not self.conn_pool:
                self.connect()
            
            conn = self.conn_pool.getconn()
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 as health_check")
                result = cursor.fetchone()
                return result['health_check'] == 1 if result else False
            finally:
                self.conn_pool.putconn(conn)
        except Exception as e:
            logger.error(f"PostgreSQL sync health check failed: {str(e)}")
            return False
    
    def _init_schema(self) -> None:
        """Initialize database schema"""
        conn = None
        try:
            conn = self.conn_pool.getconn()
            cursor = conn.cursor()
            
            # Check for pgvector extension
            try:
                cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
                self.vector_supported = True
                logger.info("Successfully enabled pgvector extension")
            except Exception:
                # Rollback failed extension creation and continue without vector support
                conn.rollback()
                self.vector_supported = False
                logger.info("Running without vector support")
            
            # Create users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    google_id VARCHAR(255) UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    settings JSONB DEFAULT '{}'
                )
            """)
            
            # Create emails table
            if self.vector_supported:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS emails (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER REFERENCES users(id),
                        gmail_id VARCHAR(255) UNIQUE NOT NULL,
                        content TEXT,
                        embedding vector(1536),
                        metadata JSONB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
            else:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS emails (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER REFERENCES users(id),
                        gmail_id VARCHAR(255) UNIQUE NOT NULL,
                        content TEXT,
                        metadata JSONB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
            
            # Create contacts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS contacts (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    email VARCHAR(255) NOT NULL,
                    name VARCHAR(255),
                    trust_tier VARCHAR(20) NOT NULL,
                    trust_score FLOAT,
                    frequency INTEGER DEFAULT 1,
                    last_contact TEXT,
                    domain VARCHAR(255),
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, email)
                )
            """)
            
            # Create knowledge_tree table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_tree (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    tree_data JSONB NOT NULL,
                    analysis_type VARCHAR(100) DEFAULT 'default',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, analysis_type)
                )
            """)
            
            # Create OAuth credentials table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS oauth_credentials (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    provider VARCHAR(50) NOT NULL,
                    access_token TEXT,
                    refresh_token TEXT,
                    token_expiry TIMESTAMP,
                    scopes TEXT[],
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, provider)
                )
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_contacts_user_id ON contacts(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_contacts_trust_tier ON contacts(trust_tier)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_emails_user_id ON emails(user_id)")
            
            conn.commit()
            logger.info("Successfully initialized database schema (sync)")
            
        except Exception as e:
            if conn:
                try:
                    conn.rollback()
                    logger.warning("Rolled back failed schema initialization")
                except Exception:
                    pass
            logger.error(f"Schema initialization error (sync): {str(e)}")
            raise
        finally:
            if conn:
                self.conn_pool.putconn(conn)
    
    def create_user(self, email: str, google_id: str) -> Dict:
        """Create a new user or get existing one (synchronous)"""
        conn = None
        try:
            conn = self.conn_pool.getconn()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (email, google_id)
                VALUES (%s, %s)
                ON CONFLICT (email) DO UPDATE
                SET google_id = %s
                RETURNING id, email, google_id, created_at
            """, (email, google_id, google_id))
            
            row = cursor.fetchone()
            conn.commit()
            
            return {
                'id': row['id'],
                'email': row['email'],
                'google_id': row['google_id'],
                'created_at': row['created_at'].isoformat()
            }
        except Exception as e:
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass
            logger.error(f"Failed to create/get user (sync): {str(e)}")
            raise
        finally:
            if conn:
                self.conn_pool.putconn(conn)
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email (synchronous)"""
        conn = None
        try:
            conn = self.conn_pool.getconn()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, email, google_id, created_at, updated_at
                FROM users WHERE email = %s
            """, (email,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            return {
                'id': row['id'],
                'email': row['email'],
                'google_id': row['google_id'],
                'created_at': row['created_at'].isoformat() if row['created_at'] else None,
                'updated_at': row['updated_at'].isoformat() if row['updated_at'] else None
            }
        except Exception as e:
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass
            logger.error(f"Failed to get user by email (sync): {str(e)}")
            return None
        finally:
            if conn:
                self.conn_pool.putconn(conn)
    
    def store_contacts(self, user_id: int, contacts: List[Dict]) -> int:
        """Store contacts (synchronous)"""
        conn = None
        try:
            conn = self.conn_pool.getconn()
            cursor = conn.cursor()
            count = 0
            
            for contact in contacts:
                # Handle metadata
                metadata = contact.get('metadata', {})
                if isinstance(metadata, dict):
                    metadata = json.dumps(metadata)
                elif metadata is None:
                    metadata = "{}"
                
                cursor.execute("""
                    INSERT INTO contacts (
                        user_id, email, name, trust_tier, trust_score, 
                        frequency, last_contact, domain, metadata
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (user_id, email) DO UPDATE
                    SET 
                        name = EXCLUDED.name,
                        trust_tier = EXCLUDED.trust_tier,
                        trust_score = EXCLUDED.trust_score,
                        frequency = EXCLUDED.frequency,
                        last_contact = EXCLUDED.last_contact,
                        domain = EXCLUDED.domain,
                        metadata = EXCLUDED.metadata,
                        updated_at = CURRENT_TIMESTAMP
                """, (
                    user_id,
                    contact['email'],
                    contact.get('name', ''),
                    contact.get('trust_tier', 'tier_3'),
                    contact.get('trust_score', 0.0),
                    contact.get('frequency', 1),
                    str(contact.get('last_contact', '')),
                    contact.get('domain', ''),
                    metadata
                ))
                count += 1
            
            conn.commit()
            logger.info(f"Successfully stored {count} contacts for user {user_id} (sync)")
            return count
            
        except Exception as e:
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass
            logger.error(f"Failed to store contacts (sync): {str(e)}")
            raise
        finally:
            if conn:
                self.conn_pool.putconn(conn)
    
    def get_contacts(self, user_id: int, trust_tier: str = None, domain: str = None, 
                    limit: int = 100, offset: int = 0) -> Tuple[List[Dict], int]:
        """Get contacts for user (synchronous)"""
        conn = None
        try:
            logger.info(f"DEBUG: About to get connection from pool")
            conn = self.conn_pool.getconn()
            logger.info(f"DEBUG: Got connection from pool: {conn}")
            cursor = conn.cursor()
            logger.info(f"DEBUG: Created cursor: {cursor}")
            
            # Build query conditions
            conditions = ["user_id = %s"]
            params = [user_id]
            
            logger.info(f"DEBUG: Getting contacts for user_id={user_id}, trust_tier={trust_tier}, domain={domain}, limit={limit}, offset={offset}")
            
            if trust_tier:
                conditions.append("trust_tier = %s")
                params.append(trust_tier)
                
            if domain:
                conditions.append("domain = %s")
                params.append(domain)
            
            # Get total count
            count_query = "SELECT COUNT(*) FROM contacts WHERE " + " AND ".join(conditions)
            logger.info(f"DEBUG: Count query: {count_query} with params: {params}")
            
            logger.info(f"DEBUG: About to execute count query")
            cursor.execute(count_query, params)
            logger.info(f"DEBUG: Count query executed successfully")
            
            count_result = cursor.fetchone()
            logger.info(f"DEBUG: Count result raw: {count_result}")
            if count_result is None:
                logger.error(f"DEBUG: Count query returned None - no results")
                total = 0
            else:
                total = count_result['count']  # Use column name instead of index for RealDictCursor
            logger.info(f"DEBUG: Total count result: {total}")
            
            # Get contacts
            query = f"""
                SELECT * FROM contacts 
                WHERE {" AND ".join(conditions)}
                ORDER BY trust_tier ASC, frequency DESC
                LIMIT %s OFFSET %s
            """
            params.extend([limit, offset])
            
            logger.info(f"DEBUG: Main query: {query} with params: {params}")
            cursor.execute(query, params)
            contacts = [dict(row) for row in cursor.fetchall()]
            logger.info(f"DEBUG: Retrieved {len(contacts)} contacts")
            
            return contacts, total
            
        except Exception as e:
            logger.error(f"DEBUG: Exception caught in get_contacts: {type(e).__name__}: {str(e)}")
            logger.error(f"DEBUG: Exception details: {repr(e)}")
            if conn:
                try:
                    conn.rollback()
                    logger.info(f"DEBUG: Successfully rolled back connection")
                except Exception as rollback_error:
                    logger.error(f"DEBUG: Rollback failed: {rollback_error}")
            logger.error(f"Failed to get contacts (sync): {str(e)}")
            return [], 0
        finally:
            if conn:
                try:
                    self.conn_pool.putconn(conn)
                    logger.info(f"DEBUG: Successfully returned connection to pool")
                except Exception as putconn_error:
                    logger.error(f"DEBUG: Failed to return connection to pool: {putconn_error}")
            else:
                logger.error(f"DEBUG: No connection to return to pool")
    
    def store_knowledge_tree(self, user_id: int, tree_data: Dict, analysis_type: str = "default") -> bool:
        """Store knowledge tree (synchronous)"""
        conn = None
        try:
            conn = self.conn_pool.getconn()
            cursor = conn.cursor()
            
            # Check if exists
            cursor.execute("""
                SELECT EXISTS(
                    SELECT 1 FROM knowledge_tree 
                    WHERE user_id = %s AND analysis_type = %s
                )
            """, (user_id, analysis_type))
            
            exists_result = cursor.fetchone()
            exists = exists_result['exists'] if exists_result else False
            
            if exists:
                cursor.execute("""
                    UPDATE knowledge_tree
                    SET tree_data = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = %s AND analysis_type = %s
                """, (json.dumps(tree_data), user_id, analysis_type))
            else:
                cursor.execute("""
                    INSERT INTO knowledge_tree (user_id, tree_data, analysis_type)
                    VALUES (%s, %s, %s)
                """, (user_id, json.dumps(tree_data), analysis_type))
            
            conn.commit()
            return True
            
        except Exception as e:
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass
            logger.error(f"Failed to store knowledge tree (sync): {str(e)}")
            return False
        finally:
            if conn:
                self.conn_pool.putconn(conn)
    
    def get_knowledge_tree(self, user_id: int, analysis_type: str = "default") -> Optional[Dict]:
        """Get knowledge tree (synchronous)"""
        conn = None
        try:
            conn = self.conn_pool.getconn()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT tree_data, created_at, updated_at
                FROM knowledge_tree 
                WHERE user_id = %s AND analysis_type = %s
            """, (user_id, analysis_type))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            try:
                tree_data = json.loads(row['tree_data']) if isinstance(row['tree_data'], str) else row['tree_data']
            except:
                tree_data = row['tree_data']
            
            return tree_data
            
        except Exception as e:
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass
            logger.error(f"Failed to get knowledge tree (sync): {str(e)}")
            return None
        finally:
            if conn:
                self.conn_pool.putconn(conn)

    def get_emails(self, user_id: int, limit: int = 100, offset: int = 0) -> Tuple[List[Dict], int]:
        """Get emails for user (synchronous)"""
        conn = None
        try:
            conn = self.conn_pool.getconn()
            cursor = conn.cursor()
            
            logger.info(f"DEBUG: Getting emails for user_id={user_id}, limit={limit}, offset={offset}")
            
            # Get total count
            cursor.execute("SELECT COUNT(*) FROM emails WHERE user_id = %s", (user_id,))
            count_result = cursor.fetchone()
            if count_result is None:
                total = 0
            else:
                total = count_result['count']  # Use column name instead of index for RealDictCursor
            logger.info(f"DEBUG: Total email count: {total}")
            
            # Get emails
            query = """
                SELECT id, gmail_id, content, metadata, created_at, updated_at
                FROM emails 
                WHERE user_id = %s 
                ORDER BY created_at DESC 
                LIMIT %s OFFSET %s
            """
            logger.info(f"DEBUG: Email query: {query} with params: [{user_id}, {limit}, {offset}]")
            cursor.execute(query, (user_id, limit, offset))
            
            emails = [dict(row) for row in cursor.fetchall()]
            logger.info(f"DEBUG: Retrieved {len(emails)} emails")
            return emails, total
            
        except Exception as e:
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass
            logger.error(f"Failed to get emails (sync): {str(e)}")
            return [], 0
        finally:
            if conn:
                self.conn_pool.putconn(conn)

    def store_email(self, user_id: int, gmail_id: str, content: str, metadata: Dict, timestamp: datetime = None) -> bool:
        """Store a single email (synchronous)"""
        conn = None
        try:
            conn = self.conn_pool.getconn()
            cursor = conn.cursor()
            
            # Handle metadata
            if isinstance(metadata, dict):
                metadata_json = json.dumps(metadata)
            else:
                metadata_json = metadata or "{}"
            
            cursor.execute("""
                INSERT INTO emails (user_id, gmail_id, content, metadata, created_at)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (gmail_id) DO UPDATE
                SET 
                    content = EXCLUDED.content,
                    metadata = EXCLUDED.metadata,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                user_id,
                gmail_id,
                content or '',
                metadata_json,
                timestamp or datetime.utcnow()
            ))
            
            conn.commit()
            return True
            
        except Exception as e:
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass
            logger.error(f"Failed to store email {gmail_id} (sync): {str(e)}")
            return False
        finally:
            if conn:
                self.conn_pool.putconn(conn)

    def get_email_by_gmail_id(self, user_id: int, gmail_id: str) -> Optional[Dict]:
        """Get email by Gmail ID (synchronous)"""
        conn = None
        try:
            conn = self.conn_pool.getconn()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, gmail_id, content, metadata, created_at, updated_at
                FROM emails 
                WHERE user_id = %s AND gmail_id = %s
            """, (user_id, gmail_id))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            return dict(row)
            
        except Exception as e:
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass
            logger.error(f"Failed to get email by gmail_id {gmail_id} (sync): {str(e)}")
            return None
        finally:
            if conn:
                self.conn_pool.putconn(conn)

    def store_contact(self, user_id: int, email: str, name: str = '', trust_tier: str = 'tier_3', 
                     frequency: int = 1, domain: str = '', metadata: Dict = None) -> bool:
        """Store a single contact (synchronous)"""
        conn = None
        try:
            conn = self.conn_pool.getconn()
            cursor = conn.cursor()
            
            # Handle metadata
            if isinstance(metadata, dict):
                metadata_json = json.dumps(metadata)
            elif metadata is None:
                metadata_json = "{}"
            else:
                metadata_json = metadata
            
            cursor.execute("""
                INSERT INTO contacts (user_id, email, name, trust_tier, frequency, domain, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (user_id, email) DO UPDATE
                SET 
                    name = EXCLUDED.name,
                    trust_tier = EXCLUDED.trust_tier,
                    frequency = EXCLUDED.frequency,
                    domain = EXCLUDED.domain,
                    metadata = EXCLUDED.metadata,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                user_id,
                email,
                name or email.split('@')[0],
                trust_tier,
                frequency,
                domain,
                metadata_json
            ))
            
            conn.commit()
            return True
            
        except Exception as e:
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass
            logger.error(f"Failed to store contact {email} (sync): {str(e)}")
            return False
        finally:
            if conn:
                self.conn_pool.putconn(conn)

    def get_contact_by_email(self, user_id: int, email: str) -> Optional[Dict]:
        """Get contact by email (synchronous)"""
        conn = None
        try:
            conn = self.conn_pool.getconn()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, user_id, email, name, trust_tier, trust_score, frequency, 
                       last_contact, domain, metadata, created_at, updated_at
                FROM contacts 
                WHERE user_id = %s AND email = %s
            """, (user_id, email))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            return dict(row)
            
        except Exception as e:
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass
            logger.error(f"Failed to get contact by email {email} (sync): {str(e)}")
            return None
        finally:
            if conn:
                self.conn_pool.putconn(conn)

    def update_contact(self, contact_id: int, **kwargs) -> bool:
        """Update contact fields (synchronous)"""
        conn = None
        try:
            conn = self.conn_pool.getconn()
            cursor = conn.cursor()
            
            # Build update query dynamically
            update_fields = []
            params = []
            
            for field, value in kwargs.items():
                if field == 'metadata' and isinstance(value, dict):
                    value = json.dumps(value)
                update_fields.append(f"{field} = %s")
                params.append(value)
            
            if not update_fields:
                return True  # Nothing to update
            
            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            params.append(contact_id)
            
            cursor.execute(f"""
                UPDATE contacts
                SET {', '.join(update_fields)}
                WHERE id = %s
            """, params)
            
            conn.commit()
            return True
            
        except Exception as e:
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass
            logger.error(f"Failed to update contact {contact_id} (sync): {str(e)}")
            return False
        finally:
            if conn:
                self.conn_pool.putconn(conn)
    
    def update_contact_metadata(self, user_id: int, email: str, new_metadata: Dict) -> bool:
        """Update contact metadata by merging with existing metadata (synchronous)"""
        conn = None
        try:
            conn = self.conn_pool.getconn()
            cursor = conn.cursor()
            
            # Get current contact with metadata
            cursor.execute("""
                SELECT id, metadata FROM contacts 
                WHERE user_id = %s AND email = %s
            """, (user_id, email))
            
            row = cursor.fetchone()
            if not row:
                logger.warning(f"Contact {email} not found for metadata update")
                return False
            
            contact_id = row['id']
            existing_metadata = {}
            
            # Parse existing metadata
            if row['metadata']:
                try:
                    if isinstance(row['metadata'], dict):
                        existing_metadata = row['metadata']
                    else:
                        existing_metadata = json.loads(row['metadata'])
                except Exception:
                    existing_metadata = {}
            
            # Merge metadata
            merged_metadata = {**existing_metadata, **new_metadata}
            
            # Update contact
            cursor.execute("""
                UPDATE contacts
                SET metadata = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (json.dumps(merged_metadata), contact_id))
            
            conn.commit()
            return True
            
        except Exception as e:
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass
            logger.error(f"Failed to update contact metadata for {email} (sync): {str(e)}")
            return False
        finally:
            if conn:
                self.conn_pool.putconn(conn)

    def get_oauth_credentials(self, user_id: int, provider: str) -> Optional[Dict]:
        """Get OAuth credentials for a user and provider (synchronous)"""
        conn = None
        try:
            conn = self.conn_pool.getconn()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT provider, access_token, refresh_token, token_expiry, scopes, metadata
                FROM oauth_credentials 
                WHERE user_id = %s AND provider = %s
            """, (user_id, provider))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            return dict(row)
            
        except Exception as e:
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass
            logger.error(f"Failed to get OAuth credentials for user {user_id} provider {provider} (sync): {str(e)}")
            return None
        finally:
            if conn:
                self.conn_pool.putconn(conn) 