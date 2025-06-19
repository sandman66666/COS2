# storage/graph_client.py
import logging
from typing import Any, Dict, List, Optional
from neo4j import AsyncGraphDatabase
import asyncio

from storage.base_client import BaseStorageClient
from config.settings import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
from utils.logging import structured_logger as logger

class GraphClient(BaseStorageClient):
    """Neo4j client for graph relationships"""
    
    def __init__(self):
        self.uri = NEO4J_URI
        self.user = NEO4J_USER
        self.password = NEO4J_PASSWORD
        self.driver = None
    
    async def connect(self) -> None:
        """Establish connection to Neo4j"""
        try:
            self.driver = AsyncGraphDatabase.driver(
                self.uri, 
                auth=(self.user, self.password),
                max_connection_lifetime=3600
            )
            
            # Verify connection
            await self.driver.verify_connectivity()
            
            # Initialize constraints
            await self._init_constraints()
            
            logger.info("Connected to Neo4j", uri=self.uri)
        except Exception as e:
            logger.error(f"Neo4j connection error: {str(e)}")
            raise
    
    async def disconnect(self) -> None:
        """Close connection to Neo4j"""
        if self.driver:
            await self.driver.close()
            self.driver = None
            logger.info("Disconnected from Neo4j")
    
    async def health_check(self) -> bool:
        """Check if Neo4j is available"""
        try:
            if not self.driver:
                await self.connect()
                
            await self.driver.verify_connectivity()
            return True
        except Exception as e:
            logger.error(f"Neo4j health check failed: {str(e)}")
            return False
    
    async def _init_constraints(self) -> None:
        """Initialize Neo4j constraints and indexes"""
        try:
            async with self.driver.session() as session:
                # Create constraints for Person nodes
                await session.run("""
                    CREATE CONSTRAINT person_email_constraint IF NOT EXISTS
                    FOR (p:Person) REQUIRE p.email IS UNIQUE
                """)
                
                # Create constraints for User nodes
                await session.run("""
                    CREATE CONSTRAINT user_id_constraint IF NOT EXISTS
                    FOR (u:User) REQUIRE u.id IS UNIQUE
                """)
                
                # Create constraints for Organization nodes
                await session.run("""
                    CREATE CONSTRAINT org_name_constraint IF NOT EXISTS
                    FOR (o:Organization) REQUIRE o.name IS UNIQUE
                """)
                
                # Create indexes for performance
                await session.run("""
                    CREATE INDEX person_name_index IF NOT EXISTS
                    FOR (p:Person) ON (p.name)
                """)
                
                await session.run("""
                    CREATE INDEX email_thread_index IF NOT EXISTS
                    FOR (e:Email) ON (e.thread_id)
                """)
                
                logger.info("Neo4j constraints and indexes created")
        except Exception as e:
            logger.error(f"Failed to create Neo4j constraints: {str(e)}")
            raise
    
    async def create_user_node(self, user_id: int, email: str) -> bool:
        """Create or update User node in graph"""
        try:
            async with self.driver.session() as session:
                result = await session.run("""
                    MERGE (u:User {id: $user_id})
                    SET u.email = $email,
                        u.last_updated = timestamp()
                    RETURN u.id as id, u.email as email
                """, user_id=user_id, email=email)
                
                record = await result.single()
                logger.info(f"Created/updated User node", 
                           user_id=record["id"], 
                           email=record["email"])
                return True
        except Exception as e:
            logger.error(f"Failed to create User node: {str(e)}")
            return False
    
    async def build_relationship_graph(
        self, 
        user_id: int, 
        contacts: List[Dict], 
        emails: List[Dict]
    ) -> Dict:
        """
        Build relationship graph between contacts based on email exchanges
        
        This creates:
        1. Person nodes for each contact
        2. Organization nodes based on email domains
        3. SENT_EMAIL_TO relationships between contacts
        4. WORKS_AT relationships between contacts and organizations
        5. COMMUNICATES_WITH relationships with frequency and importance metrics
        """
        try:
            async with self.driver.session() as session:
                # First create all Person nodes for contacts
                for contact in contacts:
                    await session.run("""
                        MERGE (p:Person {email: $email})
                        SET p.name = $name,
                            p.trust_tier = $trust_tier,
                            p.trust_score = $trust_score,
                            p.last_updated = timestamp()
                            
                        WITH p
                        
                        // Connect to user
                        MATCH (u:User {id: $user_id})
                        MERGE (u)-[r:HAS_CONTACT]->(p)
                        SET r.trust_tier = $trust_tier,
                            r.trust_score = $trust_score
                    """, 
                    email=contact['email'],
                    name=contact.get('name', ''),
                    trust_tier=contact.get('trust_tier', 'tier_3'),
                    trust_score=contact.get('trust_score', 0.0),
                    user_id=user_id
                    )
                    
                    # If we have company info, create Organization node
                    if 'company' in contact and contact['company']:
                        await session.run("""
                            MERGE (o:Organization {name: $company})
                            
                            WITH o
                            
                            MATCH (p:Person {email: $email})
                            MERGE (p)-[r:WORKS_AT]->(o)
                            SET r.title = $title,
                                r.last_updated = timestamp()
                        """,
                        email=contact['email'],
                        company=contact['company'],
                        title=contact.get('title', '')
                        )
                
                # Now process emails to create relationships
                email_count = 0
                for email in emails:
                    if 'sender' not in email or 'recipients' not in email:
                        continue
                        
                    sender = email['sender']
                    recipients = email.get('recipients', [])
                    
                    # Skip empty values
                    if not sender or not recipients:
                        continue
                    
                    # Create Email node
                    await session.run("""
                        CREATE (e:Email {
                            id: $id,
                            subject: $subject,
                            date: $date,
                            thread_id: $thread_id,
                            user_id: $user_id
                        })
                        
                        WITH e
                        
                        // Connect sender to email
                        MATCH (s:Person {email: $sender})
                        CREATE (s)-[:SENT]->(e)
                        
                        WITH e
                        
                        // Connect email to recipients
                        UNWIND $recipients as recipient
                        MATCH (r:Person {email: recipient})
                        CREATE (e)-[:RECEIVED_BY]->(r)
                    """,
                    id=email.get('id', ''),
                    subject=email.get('subject', ''),
                    date=email.get('date', ''),
                    thread_id=email.get('thread_id', ''),
                    sender=sender,
                    recipients=recipients,
                    user_id=user_id
                    )
                    
                    # Create direct communication relationships
                    await session.run("""
                        MATCH (s:Person {email: $sender})
                        UNWIND $recipients as recipient
                        MATCH (r:Person {email: recipient})
                        
                        MERGE (s)-[rel:COMMUNICATES_WITH]->(r)
                        ON CREATE SET rel.count = 1, rel.last_email = $date
                        ON MATCH SET rel.count = rel.count + 1, rel.last_email = $date
                    """,
                    sender=sender,
                    recipients=recipients,
                    date=email.get('date', '')
                    )
                    
                    email_count += 1
                
                # Get graph statistics
                result = await session.run("""
                    MATCH (p:Person)-[:COMMUNICATES_WITH]-(other)
                    WHERE exists((p)<-[:HAS_CONTACT]-(:User {id: $user_id}))
                    RETURN 
                        count(distinct p) as contact_count,
                        count(distinct other) as connected_contact_count,
                        count(distinct (p)-[:COMMUNICATES_WITH]-(other)) as relationship_count
                """, user_id=user_id)
                
                stats = await result.single()
                
                return {
                    'emails_processed': email_count,
                    'contacts_added': len(contacts),
                    'total_contacts': stats["contact_count"],
                    'connected_contacts': stats["connected_contact_count"],
                    'relationships': stats["relationship_count"]
                }
                
        except Exception as e:
            logger.error(f"Failed to build relationship graph: {str(e)}")
            raise
    
    async def get_contact_network(self, user_id: int, email: str, depth: int = 2) -> Dict:
        """
        Get network graph for a specific contact
        
        Returns nodes and relationships to visualize the contact's network
        """
        try:
            async with self.driver.session() as session:
                result = await session.run("""
                    // Start with the target person
                    MATCH (p:Person {email: $email})<-[:HAS_CONTACT]-(:User {id: $user_id})
                    
                    // Get their network up to specified depth
                    CALL apoc.path.subgraphAll(p, {
                        relationshipFilter: "COMMUNICATES_WITH",
                        maxLevel: $depth
                    })
                    YIELD nodes, relationships
                    
                    // Return as graph structure
                    RETURN 
                        [n IN nodes | {
                            id: id(n),
                            labels: labels(n),
                            properties: properties(n)
                        }] as nodes,
                        [r IN relationships | {
                            source: id(startNode(r)),
                            target: id(endNode(r)),
                            type: type(r),
                            properties: properties(r)
                        }] as relationships
                """, user_id=user_id, email=email, depth=depth)
                
                record = await result.single()
                
                return {
                    'nodes': record["nodes"],
                    'links': record["relationships"]
                }
                
        except Exception as e:
            logger.error(f"Failed to get contact network: {str(e)}")
            return {'nodes': [], 'links': []}
