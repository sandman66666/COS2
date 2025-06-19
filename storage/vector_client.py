# storage/vector_client.py
import chromadb
import logging
from typing import Any, Dict, List, Optional
import os
import uuid
import numpy as np
import json

from storage.base_client import BaseStorageClient
from config.settings import CHROMA_HOST, CHROMA_PORT
from config.constants import EMBEDDING_DIMENSION
from utils.logging import structured_logger as logger

class VectorClient(BaseStorageClient):
    """ChromaDB client for vector embeddings"""
    
    def __init__(self):
        self.host = CHROMA_HOST
        self.port = CHROMA_PORT
        self.client = None
        self.collections = {}
    
    async def connect(self) -> None:
        """Establish connection to ChromaDB"""
        try:
            # Connect to ChromaDB server
            self.client = chromadb.HttpClient(host=self.host, port=self.port)
            logger.info("Connected to ChromaDB", host=self.host, port=self.port)
            
            # Initialize collections
            await self._init_collections()
        except Exception as e:
            logger.error(f"ChromaDB connection error: {str(e)}")
            raise
    
    async def disconnect(self) -> None:
        """Close connection to ChromaDB"""
        # ChromaDB doesn't require explicit connection closing
        self.client = None
        self.collections = {}
        logger.info("Disconnected from ChromaDB")
    
    async def health_check(self) -> bool:
        """Check if ChromaDB is available"""
        try:
            if not self.client:
                await self.connect()
                
            # Try to list collections as health check
            self.client.list_collections()
            return True
        except Exception as e:
            logger.error(f"ChromaDB health check failed: {str(e)}")
            return False
            
    async def _init_collections(self) -> None:
        """Initialize ChromaDB collections"""
        try:
            # Email collection for semantic search
            self.collections['emails'] = self.client.get_or_create_collection(
                name="emails",
                metadata={"description": "Email embeddings for semantic search"}
            )
            
            # Contact collection for similarity matching
            self.collections['contacts'] = self.client.get_or_create_collection(
                name="contacts",
                metadata={"description": "Contact embeddings for similarity"}
            )
            
            # Topic collection for knowledge clustering
            self.collections['topics'] = self.client.get_or_create_collection(
                name="topics",
                metadata={"description": "Topic embeddings for clustering"}
            )
            
            # Insight collection for pattern matching
            self.collections['insights'] = self.client.get_or_create_collection(
                name="insights",
                metadata={"description": "Insight embeddings for discovery"}
            )
            
            logger.info("ChromaDB collections initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB collections: {str(e)}")
            raise
            
    async def store_email_vectors(
        self, 
        user_id: int, 
        emails: List[Dict],
        embeddings: List[List[float]]
    ) -> bool:
        """Store email embeddings for semantic search"""
        try:
            collection = self.collections.get('emails')
            if not collection:
                await self.connect()
                collection = self.collections.get('emails')
                
            # Prepare IDs, embeddings, and metadata
            ids = [f"{user_id}_{email.get('id', str(uuid.uuid4()))}" for email in emails]
            
            # Prepare metadata
            metadatas = []
            documents = []
            
            for email in emails:
                # Extract document text for full-text search
                document = f"{email.get('subject', '')} {email.get('body_text', '')[:1000]}"
                documents.append(document)
                
                # Extract metadata
                metadatas.append({
                    'user_id': str(user_id),
                    'email_id': email.get('id', ''),
                    'sender': email.get('sender', ''),
                    'recipients': ','.join(email.get('recipients', [])),
                    'subject': email.get('subject', ''),
                    'date': email.get('date', ''),
                    'thread_id': email.get('thread_id', '')
                })
            
            # Add to collection
            collection.add(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=documents
            )
            
            logger.info(f"Stored {len(ids)} email vectors", user_id=user_id)
            return True
            
        except Exception as e:
            logger.error(f"Failed to store email vectors: {str(e)}")
            return False
    
    async def search_similar_emails(
        self, 
        user_id: int, 
        embedding: List[float], 
        limit: int = 10
    ) -> List[Dict]:
        """Search for similar emails using vector similarity"""
        try:
            collection = self.collections.get('emails')
            if not collection:
                await self.connect()
                collection = self.collections.get('emails')
            
            # Search by vector similarity
            results = collection.query(
                query_embeddings=[embedding],
                where={"user_id": str(user_id)},
                n_results=limit,
                include=["distances", "metadatas", "documents"]
            )
            
            # Process results
            matches = []
            if results and 'ids' in results and len(results['ids']) > 0:
                for i, doc_id in enumerate(results['ids'][0]):
                    matches.append({
                        'id': doc_id,
                        'distance': results['distances'][0][i] if 'distances' in results else None,
                        'metadata': results['metadatas'][0][i] if 'metadatas' in results else {},
                        'content': results['documents'][0][i] if 'documents' in results else "",
                    })
            
            return matches
            
        except Exception as e:
            logger.error(f"Search similar emails failed: {str(e)}")
            return []
    
    async def store_topic_clusters(
        self, 
        user_id: int, 
        topics: List[Dict],
        embeddings: List[List[float]]
    ) -> bool:
        """Store topic clusters with embeddings"""
        try:
            collection = self.collections.get('topics')
            if not collection:
                await self.connect()
                collection = self.collections.get('topics')
                
            # Prepare IDs, embeddings, and metadata
            ids = [f"{user_id}_{topic.get('id', str(uuid.uuid4()))}" for topic in topics]
            
            # Prepare metadata and documents
            metadatas = []
            documents = []
            
            for topic in topics:
                # Extract document text for search
                document = f"{topic.get('name', '')} {topic.get('description', '')}"
                documents.append(document)
                
                # Extract metadata
                metadatas.append({
                    'user_id': str(user_id),
                    'topic_id': topic.get('id', ''),
                    'name': topic.get('name', ''),
                    'category': topic.get('category', ''),
                    'email_count': topic.get('email_count', 0),
                    'keywords': ','.join(topic.get('keywords', [])),
                })
            
            # Add to collection
            collection.add(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=documents
            )
            
            logger.info(f"Stored {len(ids)} topic clusters", user_id=user_id)
            return True
            
        except Exception as e:
            logger.error(f"Failed to store topic clusters: {str(e)}")
            return False
