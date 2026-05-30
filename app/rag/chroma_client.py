import os
import logging
from typing import List, Dict, Any

logger = logging.getLogger("rag_chroma")

class RAGVectorStore:
    """
    RAG Vector Store wrapping ChromaDB with local persistence.
    Includes fallback keyword search mechanics for robustness.
    """
    def __init__(self):
        self.use_fallback = False
        self.collection = None
        self.fallback_db = [] # Holds list of Dicts for manual search fallback
        
        try:
            import chromadb
            from chromadb.config import Settings
            
            # Setup persistent client
            self.client = chromadb.PersistentClient(path="chroma_db")
            self.collection = self.client.get_or_create_collection(
                name="emails_collection",
                metadata={"hnsw:space": "cosine"}
            )
            logger.info("ChromaDB persistent client initialized successfully")
        except Exception as e:
            logger.warning(f"ChromaDB failed to initialize. Falling back to Keyword RAG search: {e}")
            self.use_fallback = True

    def add_email(
        self,
        email_id: int,
        subject: str,
        sender: str,
        body: str,
        summary: str
    ):
        """Indexes email contents for semantic search retrieval."""
        doc_text = f"Subject: {subject}\nSender: {sender}\nSummary: {summary}\nBody: {body}"
        
        # Add to fallback database regardless
        self.fallback_db.append({
            "email_id": email_id,
            "subject": subject,
            "sender": sender,
            "text": doc_text
        })
        
        if not self.use_fallback and self.collection:
            try:
                self.collection.add(
                    documents=[doc_text],
                    metadatas=[{"email_id": email_id, "subject": subject, "sender": sender}],
                    ids=[f"email_{email_id}"]
                )
                logger.info(f"Email ID {email_id} successfully added to ChromaDB")
            except Exception as e:
                logger.error(f"Failed to add to ChromaDB: {e}. Indexing to local fallback.")

    def search_emails(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Performs search (semantic via ChromaDB or fallback via term-matching)."""
        if not self.use_fallback and self.collection:
            try:
                results = self.collection.query(
                    query_texts=[query],
                    n_results=limit
                )
                
                hits = []
                if results and "documents" in results and results["documents"]:
                    documents = results["documents"][0]
                    metadatas = results["metadatas"][0] if "metadatas" in results else [{}] * len(documents)
                    ids = results["ids"][0] if "ids" in results else [""] * len(documents)
                    
                    for idx, doc in enumerate(documents):
                        hits.append({
                            "vector_id": ids[idx],
                            "email_id": metadatas[idx].get("email_id") if metadatas[idx] else None,
                            "subject": metadatas[idx].get("subject") if metadatas[idx] else "Unknown",
                            "sender": metadatas[idx].get("sender") if metadatas[idx] else "Unknown",
                            "document": doc
                        })
                return hits
            except Exception as e:
                logger.error(f"Semantic search failed: {e}. Running fallback keyword search.")
                
        # Fallback keyword matching
        hits = []
        query_words = set(query.lower().split())
        
        scored_records = []
        for item in self.fallback_db:
            score = 0
            text_lower = item["text"].lower()
            for word in query_words:
                if word in text_lower:
                    score += 1
            if score > 0:
                scored_records.append((score, item))
                
        # Sort by match score desc
        scored_records.sort(key=lambda x: x[0], reverse=True)
        
        for score, item in scored_records[:limit]:
            hits.append({
                "vector_id": f"email_{item['email_id']}",
                "email_id": item["email_id"],
                "subject": item["subject"],
                "sender": item["sender"],
                "document": item["text"]
            })
            
        return hits

# Instantiate singleton RAG client
rag_store = RAGVectorStore()
