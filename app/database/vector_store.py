import chromadb
from chromadb.utils import embedding_functions
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 1. Initialize the ChromaDB client to save data locally
chroma_client = chromadb.PersistentClient(path="./chroma_data")

# 2. Set up the embedding model to convert text to math
embedding_model = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

# 3. Create the Collection
collection = chroma_client.get_or_create_collection(
    name="finchat_knowledge_base",
    embedding_function=embedding_model
)

# 4. Function to ingest proprietary documents
def add_document(doc_id: str, content: str, metadata: dict):
    collection.upsert(
        ids=[doc_id],
        documents=[content],
        metadatas=[metadata]
    )
    print(f"Success: Added {doc_id} to FinChat Database.")

#Function to split long pdf's into overlapping chunks and batch-upsert into ChromaDB
def ingest_chunked_document(doc_id:int,full_text:str,metadata:dict) -> int:
    #Configure LangChain splitter: 500 chars per chunk, with 50 chars overlap so sentences aren't cut off
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n","\n","."," ",""]
    )

    chunks = text_splitter.split_text(full_text)

    #Prepare batch lists for ChromaDB Upsert
    chunk_ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
    chunk_metadatas = [{**metadata,"chunk_index":i} for i in range(len(chunks))]

    collection.upsert(
        ids=chunk_ids,
        documents=chunks,
        metadatas=chunk_metadatas
    )

    print(f"Success: Upserted {len(chunks)} chunks for {doc_id} into FinChat Database.")
    return len(chunks)

# 5. Function to retrieve documents based on semantic meaning
def search_documents(query: str, top_results: int = 1):
    results = collection.query(
        query_texts=[query],
        n_results=top_results
    )
    return results

# 6. Execution block for local testing
if __name__ == "__main__":
    # Mock ABSA Bank settlement data
    mock_policy = "T+1 Settlement Policy: All ABSA Bank equity trades must be settled within one business day. If reconciliation fails on BaNCS, escalate immediately."
    
    add_document(
        doc_id="doc_001_settlement",
        content=mock_policy,
        metadata={"category": "settlement_processing", "bank": "ABSA"}
    )
    
    print("\nTesting Vector Search for: 'What is the timeframe for equity trades?'")
    search_result = search_documents(query="What is the timeframe for equity trades?")
    print(search_result['documents'])