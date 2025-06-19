"""
Knowledge Tree Builder
=====================
Constructs and manages knowledge trees from multiple data sources.
"""

from typing import Dict, List, Optional, Any, Set, Tuple
import uuid
from datetime import datetime

from models.knowledge_tree import KnowledgeNode, RelationType
from models.email import Email
from models.contact import Contact
from utils.logging import get_logger
from utils.helpers import extract_entities_from_text

logger = get_logger(__name__)


class KnowledgeTreeBuilder:
    """
    Responsible for building and managing knowledge trees from various data sources.
    """
    
    def __init__(self, user_id: str):
        """
        Initialize the tree builder.
        
        Args:
            user_id: ID of the user owning this knowledge tree
        """
        self.user_id = user_id
        
    def create_root_node(self, title: str, description: str = None) -> KnowledgeNode:
        """
        Create a root node for a new knowledge tree.
        
        Args:
            title: Title of the knowledge tree
            description: Optional description
            
        Returns:
            Root knowledge node
        """
        content = description or f"Root node for knowledge tree: {title}"
        
        root_node = KnowledgeNode(
            user_id=self.user_id,
            content=content,
            node_type="ROOT",
            tags=["root", title.lower().replace(" ", "-")],
            metadata={"title": title}
        )
        
        # Save the node
        root_node.save()
        
        logger.info(f"Created root node {root_node.node_id} for knowledge tree: {title}")
        return root_node
        
    def extract_from_email(self, email_id: str, parent_node_id: Optional[str] = None) -> List[KnowledgeNode]:
        """
        Extract knowledge from an email and add to the tree.
        
        Args:
            email_id: ID of the email to process
            parent_node_id: Optional parent node to attach to
            
        Returns:
            List of created knowledge nodes
        """
        # Load email
        email = Email.load(self.user_id, email_id)
        if not email:
            logger.error(f"Email not found: {email_id}")
            return []
            
        # Create facts from email content
        nodes = []
        
        # Create a node for the email itself
        email_node = KnowledgeNode(
            user_id=self.user_id,
            content=f"Email from {email.sender} about: {email.subject}",
            node_type="FACT",
            tags=["email", "communication"],
            metadata={
                "email_id": email_id,
                "sender": email.sender,
                "subject": email.subject,
                "date": email.date.isoformat() if email.date else None
            }
        )
        
        # Add email as source
        source_ref = {
            "source_id": email_id,
            "source_type": "email",
            "timestamp": datetime.utcnow().isoformat()
        }
        email_node.add_source(source_ref)
        
        # Save the node
        email_node.save()
        nodes.append(email_node)
        
        # Connect to parent if provided
        if parent_node_id:
            parent_node = KnowledgeNode.load(self.user_id, parent_node_id)
            if parent_node:
                parent_node.add_relation(
                    target_id=email_node.node_id, 
                    relation_type="CONTAINS",
                    metadata={"created_at": datetime.utcnow().isoformat()}
                )
                parent_node.save()
        
        # Extract key points from email body
        key_points = self._extract_key_points(email.body)
        
        # Create nodes for key points
        for point in key_points:
            point_node = KnowledgeNode(
                user_id=self.user_id,
                content=point["content"],
                node_type="FACT",
                confidence=point.get("confidence", 0.9),
                tags=point.get("tags", []),
                metadata={"extracted_from": email_id}
            )
            
            # Add email as source
            point_node.add_source(source_ref)
            
            # Save the node
            point_node.save()
            nodes.append(point_node)
            
            # Link to email node
            email_node.add_relation(
                target_id=point_node.node_id,
                relation_type="CONTAINS",
                metadata={"created_at": datetime.utcnow().isoformat()}
            )
            
        # Save email node with all its relations
        email_node.save()
        
        logger.info(f"Extracted {len(nodes)} knowledge nodes from email {email_id}")
        return nodes
    
    def extract_from_contact(self, contact_id: str, parent_node_id: Optional[str] = None) -> List[KnowledgeNode]:
        """
        Extract knowledge from a contact and add to the tree.
        
        Args:
            contact_id: ID of the contact to process
            parent_node_id: Optional parent node to attach to
            
        Returns:
            List of created knowledge nodes
        """
        # Load contact
        contact = Contact.load(self.user_id, contact_id)
        if not contact:
            logger.error(f"Contact not found: {contact_id}")
            return []
            
        nodes = []
        
        # Create a node for the contact
        contact_node = KnowledgeNode(
            user_id=self.user_id,
            content=f"Contact: {contact.name}",
            node_type="FACT",
            tags=["contact", "person"],
            metadata={
                "contact_id": contact_id,
                "name": contact.name,
                "email": contact.email,
                "organization": contact.organization,
                "title": contact.title
            }
        )
        
        # Add contact as source
        source_ref = {
            "source_id": contact_id,
            "source_type": "contact",
            "timestamp": datetime.utcnow().isoformat()
        }
        contact_node.add_source(source_ref)
        
        # Save the node
        contact_node.save()
        nodes.append(contact_node)
        
        # Connect to parent if provided
        if parent_node_id:
            parent_node = KnowledgeNode.load(self.user_id, parent_node_id)
            if parent_node:
                parent_node.add_relation(
                    target_id=contact_node.node_id, 
                    relation_type="RELATES_TO",
                    metadata={"created_at": datetime.utcnow().isoformat()}
                )
                parent_node.save()
        
        # Extract key facts about contact
        if contact.notes:
            key_facts = self._extract_key_points(contact.notes)
            
            # Create nodes for key facts
            for fact in key_facts:
                fact_node = KnowledgeNode(
                    user_id=self.user_id,
                    content=fact["content"],
                    node_type="FACT",
                    confidence=fact.get("confidence", 0.8),
                    tags=["contact-info"] + fact.get("tags", []),
                    metadata={"extracted_from": contact_id}
                )
                
                # Add contact as source
                fact_node.add_source(source_ref)
                
                # Save the node
                fact_node.save()
                nodes.append(fact_node)
                
                # Link to contact node
                contact_node.add_relation(
                    target_id=fact_node.node_id,
                    relation_type="RELATES_TO",
                    metadata={"created_at": datetime.utcnow().isoformat()}
                )
        
        # Save contact node with all relations
        contact_node.save()
        
        logger.info(f"Extracted {len(nodes)} knowledge nodes from contact {contact_id}")
        return nodes
        
    def merge_nodes(self, source_node_ids: List[str], new_content: str) -> KnowledgeNode:
        """
        Merge multiple nodes into a new consolidated node.
        
        Args:
            source_node_ids: IDs of nodes to merge
            new_content: Content for the merged node
            
        Returns:
            New consolidated node
        """
        # Load all source nodes
        source_nodes = []
        for node_id in source_node_ids:
            node = KnowledgeNode.load(self.user_id, node_id)
            if node:
                source_nodes.append(node)
                
        if not source_nodes:
            logger.error("No valid source nodes found for merging")
            return None
            
        # Collect tags from all source nodes
        all_tags = set()
        for node in source_nodes:
            all_tags.update(node.tags)
            
        # Create merged node
        merged_node = KnowledgeNode(
            user_id=self.user_id,
            content=new_content,
            node_type="INFERRED",
            tags=list(all_tags),
            metadata={"merged_from": source_node_ids}
        )
        
        # Add all original sources
        for node in source_nodes:
            for source in node.sources:
                merged_node.add_source(source)
        
        # Save the merged node
        merged_node.save()
        
        # Add relations from source nodes to merged node
        for node in source_nodes:
            node.add_relation(
                target_id=merged_node.node_id,
                relation_type="MERGED_INTO",
                metadata={"created_at": datetime.utcnow().isoformat()}
            )
            node.save()
            
        logger.info(f"Merged {len(source_nodes)} nodes into new node {merged_node.node_id}")
        return merged_node
        
    def get_tree_structure(self, root_node_id: str, max_depth: int = 5) -> Dict[str, Any]:
        """
        Get the structure of a knowledge tree starting from a root node.
        
        Args:
            root_node_id: ID of the root node
            max_depth: Maximum depth to traverse
            
        Returns:
            Dictionary representing the tree structure
        """
        # Load root node
        root_node = KnowledgeNode.load(self.user_id, root_node_id)
        if not root_node:
            logger.error(f"Root node not found: {root_node_id}")
            return {}
            
        # Keep track of visited nodes to avoid cycles
        visited = set()
        
        def build_subtree(node_id: str, depth: int) -> Dict[str, Any]:
            if depth > max_depth or node_id in visited:
                return None
                
            visited.add(node_id)
            node = KnowledgeNode.load(self.user_id, node_id)
            if not node:
                return None
                
            # Get outgoing relations
            relations = node.get_relations()
            
            # Build children recursively
            children = []
            for relation in relations:
                child_tree = build_subtree(relation['target_id'], depth + 1)
                if child_tree:
                    children.append({
                        "relation": relation['relation_type'],
                        "child": child_tree
                    })
            
            # Create node representation
            node_data = {
                "id": node.node_id,
                "content": node.content,
                "type": node.node_type,
                "tags": node.tags,
                "confidence": node.confidence
            }
            
            if children:
                node_data["children"] = children
                
            return node_data
            
        # Start building from root
        tree = build_subtree(root_node_id, 1)
        
        return tree
        
    def _extract_key_points(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract key points from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of key points with content, confidence, and tags
        """
        # In a real implementation, this would use NLP to extract key points
        # For now, we'll use a simple approach based on paragraphs
        
        # Split into paragraphs and filter empty ones
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        key_points = []
        
        for i, paragraph in enumerate(paragraphs[:3]):  # Limit to first 3 paragraphs
            # Simple heuristic: first sentence as key point
            sentences = paragraph.split('.')
            if sentences:
                first_sentence = sentences[0].strip()
                if len(first_sentence) > 10:  # Minimum length check
                    # Extract entities from the paragraph
                    entities = extract_entities_from_text(paragraph)
                    
                    # Create tags from entities
                    tags = []
                    if entities.get("emails"):
                        tags.append("has-email")
                    if entities.get("urls"):
                        tags.append("has-url")
                    if entities.get("dates"):
                        tags.append("has-date")
                    
                    key_points.append({
                        "content": first_sentence,
                        "confidence": 0.8,
                        "tags": tags
                    })
        
        return key_points
