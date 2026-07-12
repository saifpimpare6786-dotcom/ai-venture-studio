import os
import sys

# Add backend directory to Python sys.path so we can import services and app modules
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

# Set environment variable mock for ChromaDB path if not set
os.environ["CHROMA_DB_PATH"] = os.environ.get("CHROMA_DB_PATH", os.path.join(backend_dir, "chroma_db_test"))

from services.document_parser import extract_text, chunk_text
from services.rag_retriever import ingest_chunks, retrieve_context, get_chroma_client

def run_pipeline_verification():
    print("=== AI Venture Studio Document Processing Pipeline Verification ===")
    
    # 1. Setup mock docs directory
    mock_dir = os.path.join(backend_dir, "tests", "mock_docs")
    os.makedirs(mock_dir, exist_ok=True)
    
    txt_path = os.path.join(mock_dir, "business_concept.txt")
    csv_path = os.path.join(mock_dir, "financial_metrics.csv")
    
    # Write mock TXT file
    print("Generating mock text document...")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(
            "EcoSphere Ventures is a modern sustainable tech startup focused on carbon accounting.\n"
            "Our primary mission is to simplify carbon tracking for small and medium enterprises (SMEs).\n"
            "We provide a cloud-based dashboard integrating utility data, transport logs, and supply chain records.\n"
            "By offering an automated carbon reporting pipeline, we save SMEs up to 80 hours of manual data entry.\n"
            "The market size is growing rapidly with new green regulations coming into play globally.\n"
        )
        
    # Write mock CSV file
    print("Generating mock CSV spreadsheet...")
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write(
            "Year,Revenue,CO2_Reduction_Tons,Active_Clients\n"
            "2026,120000,500,25\n"
            "2027,350000,1800,80\n"
            "2028,850000,5000,210\n"
        )
        
    project_id = "test-project-123"
    
    # 2. Verify TXT processing
    print("\nProcessing TXT document...")
    txt_text = extract_text(txt_path, "business_concept.txt")
    print(f"Extracted TXT content length: {len(txt_text)} characters")
    txt_chunks = chunk_text(txt_text, chunk_size=20, overlap=5)
    print(f"Generated {len(txt_chunks)} chunks from TXT.")
    
    print("Ingesting TXT chunks into ChromaDB...")
    ingest_chunks(
        project_id=project_id,
        document_id="doc-txt-999",
        filename="business_concept.txt",
        category="Market Research",
        chunks=txt_chunks
    )
    print("Ingestion complete.")

    # 3. Verify CSV processing
    print("\nProcessing CSV document...")
    csv_text = extract_text(csv_path, "financial_metrics.csv")
    print(f"Extracted CSV content length: {len(csv_text)} characters")
    csv_chunks = chunk_text(csv_text, chunk_size=30, overlap=5)
    print(f"Generated {len(csv_chunks)} chunks from CSV.")
    
    print("Ingesting CSV chunks into ChromaDB...")
    ingest_chunks(
        project_id=project_id,
        document_id="doc-csv-888",
        filename="financial_metrics.csv",
        category="Financial Statements",
        chunks=csv_chunks
    )
    print("Ingestion complete.")
    
    # 4. Verify Context Retrieval
    print("\nTesting Context Retrieval (RAG Query)...")
    query = "carbon accounting for SMEs and EcoSphere Ventures"
    print(f"Query: '{query}'")
    context = retrieve_context(project_id=project_id, query=query, top_k=3)
    
    print("\nMatched Context Chunks retrieved:")
    for idx, chunk in enumerate(context):
        print(f"[{idx + 1}] {chunk.strip()}")
        
    # Assert we got some matches
    if len(context) > 0:
        print("\nSUCCESS: Document processing, embedding model loading, and ChromaDB retrieval verified successfully!")
    else:
        print("\nFAILURE: No matching chunks retrieved.")
        sys.exit(1)

if __name__ == "__main__":
    run_pipeline_verification()
