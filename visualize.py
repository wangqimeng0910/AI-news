import json
from collections import Counter
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from wordcloud import WordCloud
import os
import markdown


INPUT_JSON = "ai_research_feed.json"
ANALYSIS_DIR = "analysis_reports"
TEMPLATE_DIR = "templates"
OUTPUT_HTML = "dashboard/index.html"


def build_wordcloud(items):
    """从摘要生成词云"""
    text = " ".join([i["summary"] for i in items])
    wc = WordCloud(
        font_path="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # 推荐使用中文字体，更稳定
        width=1000,
        height=600,
        background_color="white"
    )
    wc.generate(text)
    wc.to_file("wordcloud.png")
    print("已生成词云 → wordcloud.png")


def build_summary(items):
    """统计来源数量"""
    sources = Counter([i["source_name"] for i in items])
    return {
        "count": len(items),
        "sources": dict(sources)
    }


def load_analysis_content(title):
    """根据文章标题匹配 analysis_reports 下的分析文件"""
    safe_filename = title.replace("/", "_") + ".md"
    path = os.path.join(ANALYSIS_DIR, safe_filename)

    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            md_text = f.read()
            # 转换为 HTML
            return markdown.markdown(md_text)
    else:
        return "<p>（暂无分析报告）</p>"


def enrich_items_with_analysis(items):
    """为每条 item 加上分析后的内容"""
    enriched = []
    for item in items:
        enriched.append({
            "title": item["title"],
            "link": item["link"],
            "analysis": load_analysis_content(item["title"])
        })
    return enriched


def render_dashboard(items, summary):
    """渲染 HTML"""
    if not os.path.exists("dashboard"):
        os.makedirs("dashboard")

    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template("dashboard.html")

    output_html = template.render(
        date=str(datetime.now())[:10],
        summary=summary,
        items=items
    )

    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(output_html)

    print(f"可视化面板已生成 → {OUTPUT_HTML}")


def main():
    # 读取 feed 数据
    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    items = data["items"]

    # 分析统计
    summary = build_summary(items)

    # 构建词云
    build_wordcloud(items)

    # 加载分析文件
    items_with_analysis = enrich_items_with_analysis(items)

    # 输出 HTML
    render_dashboard(items_with_analysis, summary)


if __name__ == "__main__":
    main()
