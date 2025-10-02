import os
import json
import re
from openai import OpenAI
import chromadb
from chromadb.utils import embedding_functions
from llm.read_file import read_file, smart_split
from llm.ENV import llm_url, llm_api_key, llm_default_model,embedding_api_key,embedding_url, embedding_default_model,embedding_dimensions
import chromadb
from langchain_openai import ChatOpenAI

# 1. 初始化 DashScope embedding 客户端
client = OpenAI(
    api_key=embedding_api_key,
    base_url=embedding_url
)

def get_embedding(text):
    resp = client.embeddings.create(
        model=embedding_default_model,
        input=text,
        dimensions=embedding_dimensions,
        encoding_format="float"
    )
    return resp.data[0].embedding

def search_knowledge_base(
        query,
        persist_dir="rag_chroma_db", 
        collection_name="rag_demo", 
        top_k=5, 
        meta_filter=None):
    """
    支持通过meta_filter字典统一过滤的知识库检索。

    参数:
        query (str): 查询问题
        collection: Chroma collection对象
        top_k (int): 返回top_k条
        meta_filter (dict or None): 只检索满足这些元信息的分块，如 {"source_file": "...", "type": "..."}，为None则不限制

    返回:
        List[str]: 分块内容列表
    """
    query_emb = get_embedding(query)
    chroma_client = chromadb.PersistentClient(path=persist_dir)
    collection = chroma_client.get_or_create_collection(collection_name)
    results = collection.query(
        query_embeddings=[query_emb],
        n_results=min(top_k * 3, collection.count()),
        include=["documents", "distances"]
    )
    docs = results["documents"][0]
    scores = results["distances"][0] if "distances" in results else [None]*len(docs)

    filtered = []
    for doc, score in zip(docs, scores):
        try:
            doc_json = json.loads(doc)
            meta = doc_json.get("metadata", {})
            meta_ok = True
            if meta_filter is not None and isinstance(meta_filter, dict):
                for k, v in meta_filter.items():
                    meta_value = meta.get(k, "")
                    # 支持正则表达式
                    if isinstance(v, str) and v.startswith("re:"):
                        pattern = v[3:]
                        if not re.search(pattern, str(meta_value)):
                            meta_ok = False
                            break
                    else:
                        if meta_value != v:
                            meta_ok = False
                            break
            if meta_ok:
                filtered.append(doc)
        except Exception:
            if meta_filter is None:
                filtered.append(doc)
    return filtered[:top_k]



def rag_qa(query, docs):
    llm = ChatOpenAI(
        base_url=llm_url,
        api_key=llm_api_key,
        model=llm_default_model,
        temperature=0.2
    )
    context = "\n\n".join(docs)
    prompt = f"""你是知识库问答助手。请根据以下知识内容回答用户问题。\n\n知识内容：\n{context}\n\n用户问题：{query}\n\n请用中文简明回答："""
    result = llm.invoke(prompt)
    # 兼容AIMessage对象和dict
    if hasattr(result, "content"):
        return result.content
    elif isinstance(result, dict) and "content" in result:
        return result["content"]
    else:
        return str(result)


def build_multi_file_knowledge_base(
    file_list, 
    persist_dir="rag_chroma_db", 
    collection_name="rag_demo",
    max_len=1000, 
    overlap=100
):
    """
    构建多文件知识库并存入本地Chroma向量数据库。

    每个分块（chunk）以JSON字符串形式存储，包含两个key：
        - content: 分块正文内容
        - metadata: 分块元信息（包含chunk_id、source_file、start_line、end_line、file_path）

    参数:
        file_list (List[str]): 需要入库的文件路径列表或者字典列表（包含file_path和其他元信息）。
        persist_dir (str): Chroma本地数据库存储目录，默认"rag_chroma_db"。
        max_len (int): 分块最大长度，默认1000。
        overlap (int): 分块重叠长度，默认100。

    返回:
        collection: 构建完成的Chroma collection对象。

    示例:
        file_list = ["a.docx", "b.docx"]
        collection = build_multi_file_knowledge_base(file_list)
    """
    
    chroma_client = chromadb.PersistentClient(path=persist_dir)
    collection = chroma_client.get_or_create_collection(collection_name)
    all_ids = collection.get()['ids']
    if all_ids:
        collection.delete(ids=all_ids)

    chunk_idx = 0
    for file_item in file_list:
        # 支持字符串或字典
        if isinstance(file_item, str):
            file_path = file_item
            extra_meta = {}
        elif isinstance(file_item, dict):
            file_path = file_item.get("file_path")
            extra_meta = {k: v for k, v in file_item.items() if k != "file_path"}
        else:
            continue

        content = read_file(file_path)
        lines = content.splitlines()
        start_char = 0
        line_starts = [0]
        for line in lines:
            start_char += len(line) + 1
            line_starts.append(start_char)
        pieces = smart_split(content, max_len=max_len, overlap=overlap, return_reasons=False)
        for piece in pieces:
            piece_text = piece
            piece_start = content.find(piece_text)
            piece_end = piece_start + len(piece_text)
            start_line = next((i for i, pos in enumerate(line_starts) if pos > piece_start), len(lines)) - 1
            end_line = next((i for i, pos in enumerate(line_starts) if pos > piece_end), len(lines)) - 1

            chunk_id = f"{os.path.basename(file_path)}_{chunk_idx}"
            metadata = {
                "chunk_id": chunk_id,
                "source_file": os.path.basename(file_path),
                "start_line": f"{start_line}",
                "end_line": f"{end_line}",
                "file_path": file_path,
                **extra_meta  # 其他元信息
            }
            chunk_json = json.dumps({
                "content": piece_text,
                "metadata": metadata
            }, ensure_ascii=False)
            emb = get_embedding(piece_text)
            collection.add(
                embeddings=[emb],
                documents=[chunk_json],
                ids=[chunk_id]
            )
            chunk_idx += 1
    print(f"共入库 {chunk_idx} 块")
    return collection


def show_chroma_collection(
    persist_dir="rag_chroma_db",
    collection_name="rag_demo",
    limit=100,
    meta_filter=None
):
    """
    获取Chroma知识库中的分块内容（支持任意元信息过滤）。

    参数:
        persist_dir (str): Chroma本地数据库存储目录，默认"rag_chroma_db"。
        collection_name (str): Collection名称，默认"rag_demo"。
        limit (int): 最多返回多少条分块，默认100。
        meta_filter (dict or None): 只返回满足这些元信息的分块，如 {"source_file": "...", "type": "..."}。

    返回:
        List[dict]: 满足条件的分块内容（已解析为dict）
    """
    chroma_client = chromadb.PersistentClient(path=persist_dir)
    collection = chroma_client.get_collection(collection_name)
    all_ids = collection.get()['ids']
    results = []
    for i in range(0, min(len(all_ids), limit)):
        doc = collection.get(ids=[all_ids[i]])
        doc_json = json.loads(doc['documents'][0])
        meta = doc_json.get("metadata", {})
        meta_ok = True
        if meta_filter is not None and isinstance(meta_filter, dict):
            for k, v in meta_filter.items():
                meta_value = meta.get(k, "")
                # 支持正则表达式
                if isinstance(v, str) and v.startswith("re:"):
                    pattern = v[3:]
                    if not re.search(pattern, str(meta_value)):
                        meta_ok = False
                        break
                else:
                    if meta_value != v:
                        meta_ok = False
                        break
        if meta_ok:
            results.append(doc_json)
    return results


def main():

    file_list = [
        {"file_path":"/home/mins/MinsC2Rust/benchmarks/c-algorithm/src/arraylist.c", "type":"c"},
        {"file_path":"/home/mins/MinsC2Rust/benchmarks/c-algorithm/src/arraylist.h", "type":"h"},
    ]

    collection = build_multi_file_knowledge_base(file_list)

    while True:
        query = input("请输入你的问题（exit退出）：").strip()
        if query.lower() == "exit":
            break
        docs = search_knowledge_base(query, collection_name="rag_demo")
        print("\n【检索到的知识块】")
        for i, doc in enumerate(docs):
            print(f"Top{i+1}:\n{doc}\n------")
        answer = rag_qa(query, docs)
        print("\n【RAG答案】\n", answer)

if __name__ == "__main__":
    main()