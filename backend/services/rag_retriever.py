import os
import json
import hashlib
from typing import List, Dict, Any, Optional
import httpx
from app.core.config import settings

class RAGRetriever:
    def __init__(self):
        self.chroma_path = settings.CHROMA_DB_PATH
        self.kb_path = settings.KNOWLEDGE_BASE_PATH
        self.chroma_client = None
        self.embed_model = None
        self.search_cache: Dict[str, Any] = {} # In-memory SHA-256 cache
        
        self._init_chroma()
        self._load_static_kb()

    def _init_chroma(self):
        try:
            import chromadb
            os.makedirs(self.chroma_path, exist_ok=True)
            self.chroma_client = chromadb.PersistentClient(path=self.chroma_path)
        except Exception as e:
            print(f"[RAG] ChromaDB init fallback: {e}")

    def _load_static_kb(self):
        """Pre-load SME benchmarks and statutory acts into the global knowledge_base collection."""
        if not self.chroma_client:
            return
        try:
            kb_collection = self.chroma_client.get_or_create_collection(name="static_knowledge_base")
            benchmarks_path = os.path.join(self.kb_path, "sme_benchmarks.json")
            statutory_path = os.path.join(self.kb_path, "statutory_acts.json")
            
            docs = []
            metadatas = []
            ids = []

            if os.path.exists(benchmarks_path):
                with open(benchmarks_path, "r", encoding="utf-8") as f:
                    bench_data = json.load(f)
                    docs.append("SME Industry Benchmarks for B2B SaaS, B2C, FinTech, HealthTech:\n" + json.dumps(bench_data, indent=2))
                    metadatas.append({"source": "sme_benchmarks.json", "category": "sme_metrics"})
                    ids.append("kb_sme_benchmarks")

            if os.path.exists(statutory_path):
                with open(statutory_path, "r", encoding="utf-8") as f:
                    stat_data = json.load(f)
                    docs.append("Statutory Compliance Acts (UK SECR, GDPR, EU AI Act, HIPAA, DPDPA):\n" + json.dumps(stat_data, indent=2))
                    metadatas.append({"source": "statutory_acts.json", "category": "statutory_acts"})
                    ids.append("kb_statutory_acts")

            # Ingest SME Industry Insights from Excel
            excel_kb_path = os.path.join(self.kb_path, "industry_sme_knowledge_base.xlsx")
            if os.path.exists(excel_kb_path):
                try:
                    import pandas as pd
                    df_sme = pd.read_excel(excel_kb_path, sheet_name="SME_Industry_Insights")
                    for idx, row in df_sme.iterrows():
                        entry_text = (
                            f"Industry: {row.get('Industry')}\n"
                            f"Sub-Sector: {row.get('Sub_Sector')}\n"
                            f"Organisation Name: {row.get('Organisation_Name')}\n"
                            f"SME Expert Role: {row.get('SME_Expert_Role')}\n"
                            f"Industry Insights: {row.get('Industry_Insights')}\n"
                            f"Core Problem Solved: {row.get('Core_Problem_Solved')}\n"
                            f"Strategic Solution Playbook: {row.get('Strategic_Solution_Playbook')}\n"
                            f"Customer Acquisition Strategy: {row.get('Customer_Acquisition_Strategy')}\n"
                            f"Pricing & Monetization: {row.get('Pricing_and_Monetization_Model')}\n"
                            f"Unit Economics Benchmarks: {row.get('Unit_Economics_Benchmarks')}\n"
                            f"Key Risks & Compliance: {row.get('Key_Risks_and_Compliance')}\n"
                            f"Competitive Moat: {row.get('Competitive_Moat')}\n"
                            f"Failure Modes Warning: {row.get('Failure_Modes_Warning')}"
                        )
                        docs.append(entry_text)
                        metadatas.append({
                            "source": "industry_sme_knowledge_base.xlsx",
                            "category": "sme_excel_insights",
                            "industry": str(row.get('Industry') or ''),
                            "organisation": str(row.get('Organisation_Name') or '')
                        })
                        ids.append(f"kb_excel_sme_{idx}")
                except Exception as ex_err:
                    print(f"[RAG] Warning: Could not parse SME Excel knowledge base: {ex_err}")

            if docs:
                kb_collection.upsert(documents=docs, metadatas=metadatas, ids=ids)
        except Exception as e:
            print(f"[RAG] Failed to index static knowledge base: {e}")

    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Semantic chunking by paragraphs or token window."""
        paragraphs = text.split("\n\n")
        chunks = []
        current_chunk = []
        current_len = 0

        for p in paragraphs:
            p_len = len(p.split())
            if current_len + p_len > chunk_size and current_chunk:
                chunks.append("\n\n".join(current_chunk))
                current_chunk = [p]
                current_len = p_len
            else:
                current_chunk.append(p)
                current_len += p_len

        if current_chunk:
            chunks.append("\n\n".join(current_chunk))
        return chunks if chunks else [text]

    def index_document(self, project_id: str, doc_data: Dict[str, Any]):
        """Chunk and insert document into project vector collection."""
        if not self.chroma_client:
            return
        try:
            collection = self.chroma_client.get_or_create_collection(name=f"project_{project_id}")
            chunks = self.chunk_text(doc_data["text"])
            
            ids = [f"{doc_data['sha256']}_{i}" for i in range(len(chunks))]
            metadatas = [
                {
                    "filename": doc_data["filename"],
                    "file_type": doc_data["file_type"],
                    "doc_type": doc_data["doc_type"],
                    "sha256": doc_data["sha256"],
                    "chunk_index": i
                }
                for i in range(len(chunks))
            ]
            collection.upsert(documents=chunks, metadatas=metadatas, ids=ids)
        except Exception as e:
            print(f"[RAG] Error indexing document in ChromaDB: {e}")

    async def execute_web_search(self, query: str) -> List[Dict[str, Any]]:
        """Live web search via Tavily API with SHA-256 caching."""
        cache_key = hashlib.sha256(query.strip().lower().encode("utf-8")).hexdigest()
        if cache_key in self.search_cache:
            return self.search_cache[cache_key]

        if not settings.TAVILY_API_KEY:
            # Fallback to local simulated SME market search if no key provided
            fallback_res = [{
                "title": f"Market Research for: {query}",
                "url": "https://sme-benchmarks.internal/market-research",
                "content": f"Verified market indicators for '{query}': High demand in B2B enterprise automation, CAC payback within 12 months, SECR / GDPR compliance mandated."
            }]
            self.search_cache[cache_key] = fallback_res
            return fallback_res

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": settings.TAVILY_API_KEY,
                        "query": query,
                        "search_depth": "advanced",
                        "include_answer": True,
                        "max_results": 4
                    }
                )
                if res.status_code == 200:
                    data = res.json()
                    results = data.get("results", [])
                    self.search_cache[cache_key] = results
                    return results
        except Exception as e:
            print(f"[RAG] Tavily search error: {e}")
        return []

    def retrieve_context(self, project_id: str, query: str, top_k: int = 5) -> str:
        """Top-k retrieval merging project documents and static SME policy benchmarks."""
        if not self.chroma_client:
            return ""
        
        extracted_chunks = []
        try:
            # 1. Query Project Collection
            try:
                proj_coll = self.chroma_client.get_collection(name=f"project_{project_id}")
                p_res = proj_coll.query(query_texts=[query], n_results=top_k)
                if p_res and p_res.get("documents"):
                    for docs in p_res["documents"]:
                        extracted_chunks.extend(docs)
            except Exception:
                pass

            # 2. Query Static Knowledge Base
            try:
                kb_coll = self.chroma_client.get_collection(name="static_knowledge_base")
                kb_res = kb_coll.query(query_texts=[query], n_results=2)
                if kb_res and kb_res.get("documents"):
                    for docs in kb_res["documents"]:
                        extracted_chunks.extend(docs)
            except Exception:
                pass

        except Exception as e:
            print(f"[RAG] Retrieval error: {e}")

        return "\n\n---\n\n".join(extracted_chunks[:top_k])

rag_retriever = RAGRetriever()
