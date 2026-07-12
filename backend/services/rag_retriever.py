import os
import chromadb
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
from app.core.config import settings

# Thread-safe global for lazy loading of the sentence transformer
_embedding_model = None

def get_embedding_model():
    """Lazy loads and caches the local Sentence Transformer model to save resource startup cost."""
    global _embedding_model
    if _embedding_model is None:
        # Load local lightweight model (approx 90MB)
        _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    return _embedding_model

def get_chroma_client():
    """
    Creates and returns a ChromaDB PersistentClient.
    Ensures the storage directory exists.
    """
    os.makedirs(settings.CHROMA_DB_PATH, exist_ok=True)
    return chromadb.PersistentClient(path=settings.CHROMA_DB_PATH)

def ingest_chunks(project_id: str, document_id: str, filename: str, category: str, chunks: List[str], extra_metadata: Dict[str, Any] = None) -> None:
    """
    Generates embeddings and ingests document chunks into a project-isolated collection.
    Chroma collections enforce alphanumeric characters + underscores, hence uuid sanitization.
    """
    if not chunks:
        return
        
    client = get_chroma_client()
    # Format collection name to meet Chroma alphanumeric + underscore requirements
    collection_name = f"project_{project_id.replace('-', '_')}"
    collection = client.get_or_create_collection(name=collection_name)
    
    model = get_embedding_model()
    embeddings = model.encode(chunks).tolist()
    
    ids = [f"{document_id}_{i}" for i in range(len(chunks))]
    metadatas = []
    for i in range(len(chunks)):
        meta = {
            "project_id": project_id,
            "document_id": document_id,
            "filename": filename,
            "category": category,
            "chunk_index": i
        }
        if extra_metadata:
            meta.update(extra_metadata)
        metadatas.append(meta)
    
    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=chunks,
        metadatas=metadatas
    )

def retrieve_context(project_id: str, query: str, top_k: int = 5) -> List[str]:
    """
    Queries both the project collection and the static knowledge base collection,
    merging and deduplicating matches to create context for agents.
    """
    client = get_chroma_client()
    model = get_embedding_model()
    query_embedding = model.encode([query]).tolist()[0]
    
    retrieved_texts = []
    
    # 1. Query project collection
    project_collection_name = f"project_{project_id.replace('-', '_')}"
    try:
        project_col = client.get_collection(name=project_collection_name)
        project_results = project_col.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        if project_results and "documents" in project_results and project_results["documents"]:
            retrieved_texts.extend(project_results["documents"][0])
    except Exception:
        # Fall back gracefully if the project collection has no items yet
        pass

    # 2. Query shared knowledge base collection
    try:
        kb_col = client.get_collection(name="knowledge_base")
        kb_results = kb_col.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        if kb_results and "documents" in kb_results and kb_results["documents"]:
            retrieved_texts.extend(kb_results["documents"][0])
    except Exception:
        # Fall back gracefully if knowledge base is not populated
        pass
        
    # Deduplicate while preserving relevance rank order
    seen = set()
    deduped_texts = []
    for text in retrieved_texts:
        if text not in seen:
            seen.add(text)
            deduped_texts.append(text)
            
    return deduped_texts[:top_k * 2]
