import os
import sys

# Add backend directory to Python sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from services.rag_retriever import get_chroma_client

def clean_project(project_id: str):
    print(f"=== Cleaning ChromaDB collection for Project: {project_id} ===")
    client = get_chroma_client()
    collection_name = f"project_{project_id.replace('-', '_')}"
    
    try:
        client.delete_collection(name=collection_name)
        print(f"SUCCESS: Collection '{collection_name}' deleted successfully.")
    except Exception as e:
        print(f"INFO: Collection '{collection_name}' could not be deleted (might not exist): {str(e)}")

if __name__ == "__main__":
    target_project = "0405a85c-9064-4ffc-babe-3d9f9c4fc4a2"
    clean_project(target_project)
