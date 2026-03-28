# backend/test_query.py
import sys
sys.path.insert(0, ".")
import chromadb
from chromadb.config import Settings
from app.services.vector_store import vector_service

client = chromadb.PersistentClient(
    path="./chroma_db",
    settings=Settings(anonymized_telemetry=False)
)

kb_id = 6
collection = client.get_collection(f"kb_{kb_id}")

# 直接用 collection.query 测试，绕过 LangChain 层
emb_wrapper = vector_service._emb_wrapper
query = "斯华AIWindows客户端手册"
vec = emb_wrapper._sync_embed_query(query)

results = collection.query(
    query_embeddings=[vec],
    n_results=10,
    include=["metadatas", "documents", "distances"]
)

print(f"Query: {query!r}\n")
for i, (doc, meta, dist) in enumerate(zip(
    results["documents"][0],
    results["metadatas"][0],
    results["distances"][0]
)):
    import math
    sim = math.exp(-dist)
    print(f"[{i+1}] sim={sim:.4f} dist={dist:.4f}")
    print(f"     file={meta.get('filename')!r}")
    print(f"     content={doc[:80]!r}\n")