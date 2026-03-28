# backend/check_vectors.py  临时排查脚本
import sys
sys.path.insert(0, ".")
import chromadb
from chromadb.config import Settings

client = chromadb.PersistentClient(
    path="./chroma_db",
    settings=Settings(anonymized_telemetry=False)
)

kb_id = 6
collection = client.get_collection(f"kb_{kb_id}")
print(f"Total vectors in kb_{kb_id}: {collection.count()}")

# 查所有文件名
results = collection.get(include=["metadatas"], limit=10000)
filenames = {}
for meta in results["metadatas"]:
    fname = meta.get("filename", "?")
    filenames[fname] = filenames.get(fname, 0) + 1

print("\n各文件向量数量：")
for fname, count in sorted(filenames.items()):
    print(f"  {count:4d} chunks | {fname}")