from typing import List, Dict, Any
from app.rag.chroma_client import rag_store
from app.database.db import log_agent_action

def vector_search(query: str, limit: int = 5) -> Dict[str, Any]:
    """
    Performs semantic search across all indexed emails using ChromaDB.
    Useful for queries like 'Find recruiter emails' or 'Show billing issues'.
    """
    try:
        results = rag_store.search_emails(query, limit)
        log_agent_action("SearchAgent", "vector_search", f"Searched vector store for: {query}")
        return {"success": True, "data": results}
    except Exception as e:
        return {"success": False, "error": str(e)}
