import logging
from app.rag.chroma_client import rag_store

logger = logging.getLogger("search_agent")

def run_semantic_email_search(query: str, limit: int = 5) -> str:
    """Searches indexed emails and returns matching contexts."""
    try:
        hits = rag_store.search_emails(query, limit)
        if not hits:
            return "No matching emails found in the semantic vector store."
            
        md = "### Semantic Search Results:\n"
        for idx, hit in enumerate(hits):
            md += f"\n**Result #{idx+1}**: {hit['subject']} (From: {hit['sender']})\n"
            md += f"> {hit['document'][:250]}...\n"
        return md
    except Exception as e:
        logger.error(f"RAG search failed: {e}")
        return "Failed to complete semantic search."
