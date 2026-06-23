from typing import List, Dict

from .config import LLM_API_KEY, LLM_PROVIDER, LLM_MODEL

Paper = Dict


def build_prompt(papers: List[Paper]) -> str:
    prompt = """你是一位导航定位领域的学术助手。请用中文为以下每篇论文生成简短总结（每篇50-100字），
重点关注：本文解决了什么问题？使用什么方法？有什么创新点？
按相关性从高到低排序。先输出3篇最相关的作为"重点推荐"。

论文列表：
"""
    for i, p in enumerate(papers, 1):
        prompt += f"""
{i}. 标题: {p['title']}
   作者: {', '.join(p['authors'][:5])}
   来源: {p['source']}
   摘要: {p.get('abstract', '无摘要')[:500]}
"""
    prompt += "\n请按格式输出：\n## 重点推荐\n...\n## 全部文献\n..."
    return prompt


def parse_summary(text: str) -> str:
    return text.strip()


def summarize(papers: List[Paper]) -> str:
    if not papers:
        return "今日无新文献。"

    if not LLM_API_KEY:
        return _fallback_summary(papers)

    try:
        if LLM_PROVIDER == "gemini":
            return _summarize_gemini(papers)
        elif LLM_PROVIDER == "openai":
            return _summarize_openai(papers)
        else:
            return _fallback_summary(papers)
    except Exception as e:
        error_msg = str(e)
        if "quota" in error_msg.lower() or "429" in error_msg:
            print(f"[WARN] LLM API quota exceeded. Visit https://aistudio.google.com/apikey to check usage.")
        else:
            print(f"[WARN] LLM summarization failed: {e}")
        return _fallback_summary(papers)


def _summarize_gemini(papers: List[Paper]) -> str:
    import google.generativeai as genai

    genai.configure(api_key=LLM_API_KEY)
    model = genai.GenerativeModel(LLM_MODEL)

    prompt = build_prompt(papers)
    resp = model.generate_content(prompt)
    return parse_summary(resp.text)


def _summarize_openai(papers: List[Paper]) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=LLM_API_KEY)
    prompt = build_prompt(papers)

    resp = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    return parse_summary(resp.choices[0].message.content)


def _fallback_summary(papers: List[Paper]) -> str:
    lines = []
    for i, p in enumerate(papers, 1):
        abstract = p.get("abstract", "")
        brief = abstract[:200] + "..." if len(abstract) > 200 else abstract
        lines.append(
            f"{i}. **{p['title']}**\n"
            f"   来源: {p['source']}  |  作者: {', '.join(p['authors'][:3])}\n"
            f"   摘要: {brief}\n"
        )
    return "\n".join(lines)
