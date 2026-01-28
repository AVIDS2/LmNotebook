
import chromadb
from chromadb.utils import embedding_functions
import os

def test_chroma():
    print("Testing ChromaDB...")
    client = chromadb.EphemeralClient()
    
    # Use a basic embedding function
    # Note: On first run this might download the model
    emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="BAAI/bge-small-zh-v1.5")
    
    collection = client.create_collection(name="test", embedding_function=emb_fn)
    
    collection.add(
        documents=["这是关于勾股定理的笔记", "这是关于拉格朗日中值定理的笔记"],
        metadatas=[{"source": "note1"}, {"source": "note2"}],
        ids=["id1", "id2"]
    )
    
    results = collection.query(
        query_texts=["给我讲讲数学定理"],
        n_results=2
    )
    
    print("Search results:")
    for i, doc in enumerate(results['documents'][0]):
        print(f"{i+1}. {doc} (Metadata: {results['metadatas'][0][i]})")

if __name__ == "__main__":
    test_chroma()
