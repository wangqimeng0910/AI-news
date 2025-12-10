#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
抓取当前 AI 研究相关的重要信息源：
- OpenAI News（官方新闻与研究相关动态）
- Google DeepMind（研究 & 产品）
- arXiv: cs.LG / cs.CL / cs.AI（机器学习、NLP、通用 AI）

输出：
1）终端可读的摘要
2）保存到 ai_research_feed.json，供后续分析使用
"""

import json
import re
from datetime import datetime, timezone
from typing import Dict, Any, List

import feedparser

# ========= 配置区：信息源列表 =========

SOURCES: List[Dict[str, Any]] = [
    {
        "id": "openai_news",
        "name": "OpenAI News",
        "type": "rss",
        # 官方 RSS：用于跟踪 OpenAI 的最新动态（包括技术、产品、合作等）
        "url": "https://openai.com/news/rss.xml",
        "category": "company",
        "max_items": 5,
    },
    {
        "id": "deepmind_news",
        "name": "Google DeepMind",
        "type": "rss",
        # Google DeepMind 在 Google 官方博客下的 RSS
        # 若未来失效，只需在这里替换为最新的 RSS 地址
        "url": "https://blog.google/technology/google-deepmind/rss/",
        "category": "company",
        "max_items": 5,
    },
    {
        "id": "arxiv_cs_lg",
        "name": "arXiv cs.LG (Machine Learning)",
        "type": "rss",
        "url": "https://export.arxiv.org/rss/cs.LG",
        "category": "arxiv",
        "max_items": 5,
    },
    {
        "id": "arxiv_cs_cl",
        "name": "arXiv cs.CL (Computation and Language)",
        "type": "rss",
        "url": "https://export.arxiv.org/rss/cs.CL",
        "category": "arxiv",
        "max_items": 5,
    },
    {
        "id": "arxiv_cs_ai",
        "name": "arXiv cs.AI (Artificial Intelligence)",
        "type": "rss",
        "url": "https://export.arxiv.org/rss/cs.AI",
        "category": "arxiv",
        "max_items": 5,
    },
]


# ========= 工具函数 =========

def strip_html(text: str) -> str:
    """简单去掉 HTML 标签，保留纯文本。"""
    if not text:
        return ""
    # 去掉标签
    text = re.sub(r"<[^>]+>", " ", text)
    # 压缩多余空白
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def format_dt(dt_struct) -> str:
    """把 feedparser 的时间结构转成 ISO8601 字符串；如果没有就返回空串。"""
    if not dt_struct:
        return ""
    try:
        dt = datetime(*dt_struct[:6], tzinfo=timezone.utc)
        return dt.isoformat()
    except Exception:
        return ""


def fetch_rss_source(source: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    拉取单个 RSS 源，返回标准化的条目列表：
    [
      {
        "source_id": ...,
        "source_name": ...,
        "category": "company" / "arxiv",
        "title": ...,
        "link": ...,
        "published": "...",
        "summary": "...",
      },
      ...
    ]
    """
    print(f"[*] Fetching: {source['name']} ({source['url']})")
    feed = feedparser.parse(source["url"])

    if feed.bozo:
        # bozo 为 True 说明解析可能有问题，但有时内容依旧可用
        print(f"[!] Warning: feedparser reported an issue for {source['id']}")

    entries = feed.entries[: source.get("max_items", 5)]
    results: List[Dict[str, Any]] = []

    for entry in entries:
        title = entry.get("title", "").strip()
        link = entry.get("link", "").strip()

        # 尝试获取发布时间
        published_parsed = entry.get("published_parsed") or entry.get("updated_parsed")
        published = format_dt(published_parsed)

        # 摘要，有些 RSS 用 summary，有些用 description
        raw_summary = entry.get("summary") or entry.get("description") or ""
        summary = strip_html(raw_summary)
        if len(summary) > 400:
            summary = summary[:400] + "..."

        item = {
            "source_id": source["id"],
            "source_name": source["name"],
            "category": source.get("category", "unknown"),
            "title": title,
            "link": link,
            "published": published,
            "summary": summary,
        }
        results.append(item)

    print(f"[+] Got {len(results)} items from {source['name']}\n")
    return results


def fetch_all_sources() -> List[Dict[str, Any]]:
    """遍历 SOURCES，拉取所有源的数据。"""
    all_items: List[Dict[str, Any]] = []
    for src in SOURCES:
        if src["type"] == "rss":
            try:
                items = fetch_rss_source(src)
                all_items.extend(items)
            except Exception as e:
                print(f"[x] Error fetching {src['id']}: {e}")
        else:
            # 预留：未来可以支持 html 抓取、API 等
            print(f"[!] Unsupported source type: {src['type']} for {src['id']}")
    return all_items


def print_human_readable(items: List[Dict[str, Any]]) -> None:
    """将抓到的内容按来源打印出来，方便你快速扫一眼。"""
    # 按来源分组
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for item in items:
        key = item["source_name"]
        grouped.setdefault(key, []).append(item)

    print("\n================= AI 研究层最新动态（按来源） =================\n")
    for source_name, src_items in grouped.items():
        print(f"### {source_name}")
        print("-" * (len(source_name) + 4))
        for it in src_items:
            print(f"标题: {it['title']}")
            if it["published"]:
                print(f"时间: {it['published']}")
            print(f"链接: {it['link']}")
            if it["summary"]:
                print(f"摘要: {it['summary']}")
            print()
        print()


def save_to_json(items: List[Dict[str, Any]], path: str = "ai_research_feed.json") -> None:
    """保存为 JSON，方便后续分析 / 喂给大模型做总结。"""
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "count": len(items),
        "items": items,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"[+] Saved {len(items)} items to {path}")


def main():
    items = fetch_all_sources()
    if not items:
        print("[!] No items fetched. Please check your network or RSS URLs.")
        return

    print_human_readable(items)
    save_to_json(items)


if __name__ == "__main__":
    main()
