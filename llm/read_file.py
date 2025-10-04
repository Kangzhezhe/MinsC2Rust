import pdfplumber
import docx
import sys
import re

def read_pdf(file_path):
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

def read_docx(file_path):
    doc = docx.Document(file_path)
    # 将每个段落转换为 markdown 格式
    md_lines = []
    for para in doc.paragraphs:
        style = para.style.name.lower()
        text = para.text.strip()
        if not text:
            continue
        if style.startswith('heading'):
            # 标题转换为 markdown 标题
            level = ''.join(filter(str.isdigit, style))
            level = int(level) if level else 1
            md_lines.append('#' * level + ' ' + text)
        else:
            md_lines.append(text)
    return '\n'.join(md_lines)

def read_md(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def read_txt(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    return text

def read_file(file_path):
    if file_path.endswith('.pdf'):
        text = read_pdf(file_path)
        return text
    elif file_path.endswith('.docx'):
        return read_docx(file_path)
    elif file_path.endswith('.md'):
        return read_md(file_path)
    elif file_path.endswith('.txt'):
        return read_txt(file_path)
    else:
        return read_txt(file_path)
        # raise ValueError("不支持的文件格式")

def split_by_markdown_heading(document_content):
    """
    只以'# '或'## '等markdown标题为段落起始，返回每个以标题开头的段落
    """
    lines = document_content.splitlines()
    paragraphs = []
    current_para = ""
    for line in lines:
        if line.strip().startswith("#"):
            if current_para:
                paragraphs.append(current_para.strip())
            current_para = line
        else:
            if current_para:
                current_para += "\n" + line
            else:
                current_para = line
    if current_para:
        paragraphs.append(current_para.strip())
    paragraphs = [p for p in paragraphs if p.strip().startswith("#")]
    return paragraphs

def smart_split(content, max_len=1000, window_expand=200, overlap=100, return_reasons=False):
    """
    智能分块：优先级分割
    1. 标题级别（#数越少优先，且尽量靠近max_len）
    2. 数字+.（数字越小优先，且尽量靠近max_len）
    3. 双换行
    4. 句号分割（支持中英文句号）
    5. 暴力分块
    :param content: str
    :param max_len: int
    :param window_expand:  int，默认max_len的一半
    :param overlap: int，分块重叠长度
    :param return_reasons: bool，是否返回分块原因
    :return: List[str] 或 List[(str, reason)]
    """

    # if window_expand is None:
    #     window_expand = max_len // 2

    pieces = []
    split_reasons = []
    start = 0
    content_len = len(content)
    while start < content_len:
        if content_len - start <= max_len:
            pieces.append(content[start:].strip())
            split_reasons.append("结尾")
            break

        window_size = min(max_len + window_expand, content_len - start)
        window = content[start:start+window_size]
        left = max(0, max_len - window_expand)
        right = min(window_size, max_len + window_expand)

        # 1. 标题分割，#数越少优先，且尽量靠近max_len
        title_matches = list(re.finditer(r'(^|\n)(#+) ', window))
        title_candidates = []
        for m in title_matches:
            pos = m.start(0) + (1 if m.group(1) else 0)
            if left < pos <= right:
                level = len(m.group(2))
                title_candidates.append((level, -abs(pos-max_len), pos))  # level优先，距离max_len近优先
        if title_candidates:
            title_candidates.sort()
            split_pos = start + title_candidates[0][2]
            pieces.append(content[start:split_pos].strip())
            split_reasons.append(f"标题级别（#={title_candidates[0][0]}）")
            start = max(split_pos - overlap, start)  # 支持overlap
            continue

        # 2. 数字+.分割，数字小优先，且尽量靠近max_len
        num_matches = list(re.finditer(r'\n(\d+)\.', window))
        num_candidates = []
        for m in num_matches:
            pos = m.start(0) + 1
            if left < pos <= right:
                num = int(m.group(1))
                num_candidates.append((num, -abs(pos-max_len), pos))
        if num_candidates:
            num_candidates.sort()
            split_pos = start + num_candidates[0][2]
            pieces.append(content[start:split_pos].strip())
            split_reasons.append(f"数字小标题级别+.（数字={num_candidates[0][0]}）")
            start = max(split_pos - overlap, start)
            continue

        # 3. 双换行，尽量靠近max_len
        para_pos = -1
        for i in range(right, left, -1):
            if i < len(window) and window[i-2:i] == '\n\n':
                para_pos = i-2
                break
        if para_pos > 0:
            split_pos = start + para_pos + 2
            pieces.append(content[start:split_pos].strip())
            split_reasons.append("双换行")
            start = max(split_pos - overlap, start)
            continue

        # 4. 句号分割（支持中英文句号），尽量靠近max_len
        period_pos = -1
        for i in range(right, left, -1):
            if i < len(window) and window[i-1] in ('。', '.','}',';'):
                period_pos = i-1
                break
        if period_pos > 0:
            split_pos = start + period_pos + 1
            pieces.append(content[start:split_pos].strip())
            split_reasons.append("句号分割")
            start = max(split_pos - overlap, start)
            continue

        # 5. 暴力分块
        split_pos = start + max_len
        pieces.append(content[start:split_pos].strip())
        split_reasons.append("暴力分块")
        start = max(split_pos - overlap, start)

    if return_reasons:
        return [( p, r) for idx, (p, r) in enumerate(zip(pieces, split_reasons)) if p]
    else:
        return [ p for idx, p in enumerate(pieces) if p]

def main():
    if len(sys.argv) < 2:
        print("请在命令行中输入文档路径，例如：python read_file.py 文件路径")
        return
    file_path = sys.argv[1]
    try:
        content = read_file(file_path)
        print("原始内容：\n")
        print(content[:500] + "\n...")  # 只打印前500字符
        print("\n智能分块如下：\n")
        pieces = smart_split(content,max_len=1000, return_reasons=True)
        for idx, (piece, reason) in enumerate(pieces):
            print(f"[块{idx+1} 长度{len(piece)}]（依据：{reason}）:\n{piece}\n------")

        # pieces = split_by_markdown_heading(content)
        # for idx, piece in enumerate(pieces):
        #     print(f"[块{idx+1} 长度{len(piece)}]:\n{piece}\n------")

    except Exception as e:
        print(f"读取文档时出错：{e}")

if __name__ == "__main__":
    main()