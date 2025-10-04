import os
import json
import re
from concurrent.futures import ThreadPoolExecutor
from openai import OpenAI
import requests
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


def get_embeddings(texts, batch_size=10, max_workers=1):
    if not texts:
        return []

    def _embed(batch):
        resp = client.embeddings.create(
            model=embedding_default_model,
            input=batch,
            dimensions=embedding_dimensions,
            encoding_format="float"
        )
        return [item.embedding for item in resp.data]

    batches = [texts[i:i + batch_size] for i in range(0, len(texts), batch_size)]

    if max_workers is None or max_workers <= 1 or len(batches) == 1:
        embeddings = []
        for batch in batches:
            embeddings.extend(_embed(batch))
        return embeddings

    embeddings = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(_embed, batch) for batch in batches]
        for future in futures:
            embeddings.extend(future.result())
    return embeddings


def rerank_documents(query, documents, top_n=None):
    """
    调用 DashScope rerank 接口对检索结果进行重排。

    参数:
        query (str): 检索查询。
        documents (List[str]): 候选文档列表（JSON字符串或纯文本）。
        top_n (int or None): 返回前 top_n 的文档，默认全部。
        endpoint (str or None): rerank 服务地址，默认 DashScope 官方地址。

    返回:
        List[str]: 根据相关性得分排序后的文档列表。
    """
    if not documents:
        return []

    api_key = os.getenv("DASHSCOPE_API_KEY") or embedding_api_key
    endpoint = "https://dashscope.aliyuncs.com/api/v1/services/rerank/text-rerank/text-rerank"
    limit = min(top_n or len(documents), len(documents))

    payload_docs = []
    doc_texts = []
    for idx, doc in enumerate(documents):
        text = doc
        if isinstance(doc, str):
            try:
                doc_json = json.loads(doc)
                text = doc_json.get("content") or doc_json.get("text") or doc
            except json.JSONDecodeError:
                text = doc
        payload_docs.append(text)
        doc_texts.append(doc)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "gte-rerank-v2",
        "input": {
            "query": query,
            "documents": payload_docs
        },
        "parameters": {
            "return_documents": False,
            "top_n": limit
        }
    }

    try:
        response = requests.post(endpoint, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        results = data.get("output", {}).get("results") or data.get("results", [])
        if not results:
            return doc_texts[:limit]
        # 根据返回的 index 重排
        ordered = sorted(results, key=lambda item: item.get("relevance_score", 0), reverse=True)
        reordered_docs = []
        seen_indices = set()
        for item in ordered:
            idx = item.get("index")
            if idx is None or idx in seen_indices or idx >= len(doc_texts):
                continue
            reordered_docs.append(doc_texts[idx])
            seen_indices.add(idx)
        # 如果接口返回的 top_n 少于请求数量，补齐原始顺序
        if len(reordered_docs) < limit:
            for idx, doc in enumerate(doc_texts):
                if idx not in seen_indices and len(reordered_docs) < limit:
                    reordered_docs.append(doc)
        return reordered_docs
    except Exception as exc:
        print(f"rerank 调用失败，返回原始排序: {exc}")
        return doc_texts[:limit]

def search_knowledge_base(
        query,
        persist_dir="rag_chroma_db", 
        collection_name="rag_demo", 
        top_k=10, 
        meta_filter=None,
        use_rerank=False,
        rerank_top_n=5,
        ):
    """
    支持通过meta_filter字典统一过滤的知识库检索。

    参数:
        query (str): 查询问题
        collection: Chroma collection对象
        top_k (int): 返回top_k条
        meta_filter (dict or None): 只检索满足这些元信息的分块，如 {"source_file": "...", "type": "..."}，为None则不限制
        use_rerank (bool): 是否调用 rerank 接口对结果重排。
        rerank_top_n (int or None): 参与重排的候选数量，默认与 top_k 相同。

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
    if not filtered:
        return []

    rerank_candidates = filtered[:max(top_k, rerank_top_n or top_k)]
    if use_rerank:
        reranked = rerank_documents(
            query,
            rerank_candidates,
            top_n=rerank_top_n or len(rerank_candidates),
        )
        return reranked[:top_k]
    return rerank_candidates[:top_k]



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
    chunks = []
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

        if not file_path:
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
            chunks.append({
                "id": chunk_id,
                "text": piece_text,
                "document": chunk_json
            })
            chunk_idx += 1

    if not chunks:
        print("未找到可入库的分块")
        return collection

    embed_batch_size = 10
    max_workers = 8

    all_embeddings = get_embeddings(
        [item["text"] for item in chunks],
        batch_size=embed_batch_size,
        max_workers=max_workers
    )

    for i in range(0, len(chunks), embed_batch_size):
        batch = chunks[i:i + embed_batch_size]
        emb_slice = all_embeddings[i:i + len(batch)]
        collection.add(
            embeddings=emb_slice,
            documents=[item["document"] for item in batch],
            ids=[item["id"] for item in batch]
        )
    print(f"共入库 {chunk_idx} 块")
    return collection


def build_directory_knowledge_base(
    root_dir,
    suffixes,
    persist_dir="rag_chroma_db",
    collection_name="rag_demo",
    max_len=1000,
    overlap=100
):
    """
    递归扫描目录，筛选指定后缀文件并构建知识库。

    参数:
        root_dir (str): 需要遍历的根目录。
        suffixes (Iterable[str] or str): 希望纳入的文件后缀列表，支持带或不带点，如 [".c", "h"].
        persist_dir (str): Chroma本地数据库存储目录，默认"rag_chroma_db"。
        collection_name (str): Collection名称，默认"rag_demo"。
        max_len (int): 分块最大长度，默认1000。
        overlap (int): 分块重叠长度，默认100。

    返回:
        collection: 构建完成的Chroma collection对象。
    """
    if isinstance(suffixes, str):
        suffix_iterable = {suffixes}
    else:
        suffix_iterable = set(suffixes)

    normalized_suffixes = {
        s if s.startswith(".") else f".{s}"
        for s in suffix_iterable
    }

    file_list = []
    for current_root, _, files in os.walk(root_dir):
        for filename in files:
            file_ext = os.path.splitext(filename)[1]
            if file_ext in normalized_suffixes:
                file_path = os.path.join(current_root, filename)
                relative_path = os.path.relpath(file_path, root_dir)
                file_list.append({
                    "file_path": file_path,
                    "file_suffix": file_ext,
                    "relative_path": relative_path
                })

    print(f"在目录 '{root_dir}' 下找到 {len(file_list)} 个匹配后缀 {sorted(normalized_suffixes)} 的文件")

    if not file_list:
        raise ValueError(
            f"未在目录 '{root_dir}' 下找到匹配后缀 {sorted(normalized_suffixes)} 的文件"
        )

    return build_multi_file_knowledge_base(
        file_list,
        persist_dir=persist_dir,
        collection_name=collection_name,
        max_len=max_len,
        overlap=overlap
    )


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

    # file_list = [
    #     {"file_path":"/home/mins/MinsC2Rust/benchmarks/c-algorithm/src/arraylist.c", "type":"c"},
    #     {"file_path":"/home/mins/MinsC2Rust/benchmarks/c-algorithm/src/arraylist.h", "type":"h"},
    # ]

    # collection = build_multi_file_knowledge_base(file_list)

    build_directory_knowledge_base(
        root_dir="/home/mins/MinsC2Rust/benchmarks/c-algorithm",
        suffixes=[".c", ".h"],
        max_len=3000
    )

    while True:
        query = input("请输入你的问题（exit退出）：").strip()
        if query.lower() == "exit":
            break
        docs = search_knowledge_base(
            query,
            collection_name="rag_demo",
            top_k=10,
            use_rerank=True,
            rerank_top_n=3
        )
        print("\n【检索到的知识块】")
        for i, doc in enumerate(docs):
            print(f"Top{i+1}:\n{doc}\n------")
        answer = rag_qa(query, docs)
        print("\n【RAG答案】\n", answer)

if __name__ == "__main__":
    main()