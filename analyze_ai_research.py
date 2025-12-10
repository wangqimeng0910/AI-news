from openai import OpenAI
import os
import json
import time

# ========== 配置区域 ==========
API_KEY = "sk-36005373536d433b87e22ef7f23002aa"
MODEL_NAME = "deepseek-v3.2-exp"  # ← 模型常量
INPUT_JSON = "ai_research_feed.json"
OUTPUT_DIR = "analysis_reports"
BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
# ================================================

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)


def analyze_item(text: str) -> str:
    """
    调用 DeepSeek v3.2-exp 深度思考模型（stream + reasoning_content）
    返回完整的模型最终输出内容
    """
    messages = [
        {
            "role": "system",
            "content": "你是一名专业的AI研究分析员，请按科研方式深度分析论文。"
        },
        {
            "role": "user",
            "content": text
        }
    ]

    completion = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        extra_body={"enable_thinking": True},
        stream=True
    )

    print("\n" + "=" * 20 + " 开始深度分析（思考模式） " + "=" * 20)

    final_output = []
    is_answering = False

    for chunk in completion:
        delta = chunk.choices[0].delta

        # 输出思考过程（reasoning_content）
        if hasattr(delta, "reasoning_content") and delta.reasoning_content:
            if not is_answering:
                print(delta.reasoning_content, end="", flush=True)

        # 输出最终内容（content）
        if hasattr(delta, "content") and delta.content:
            if not is_answering:
                print("\n" + "=" * 20 + " 最终分析报告 " + "=" * 20)
                is_answering = True

            print(delta.content, end="", flush=True)
            final_output.append(delta.content)

    print("\n" + "=" * 50 + "\n")

    return "".join(final_output)


def build_prompt(item):
    """ 为每条研究构建模板 prompt """

    return f"""
请你对下面这条 AI 研究/新闻进行深入分析，输出一份结构化的 AI 研究报告：

【研究条目】
标题：{item["title"]}
来源：{item["source_name"]}
发布时间：{item["published"]}
链接：{item["link"]}
摘要：{item["summary"]}

【请输出以下内容】

## 1. 研究背景：它试图解决什么问题？

## 2. 核心方法与原理（通俗解释）

## 3. 创新点（突破点）

## 4. 技术优势

## 5. 局限性 / 风险点

## 6. 应用场景（结合真实业务）

## 7. 行业趋势判断（未来可能的发展方向）

## 8. 给我的产品（AI助手 / 自动化系统）的启发

请用中文分析，并确保内容专业、逻辑清晰。
"""


def save_report(item, report):
    """ 按标题保存 Markdown 深度分析报告 """
    import os

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    safe_title = "".join(c for c in item["title"] if c.isalnum() or c in (" ","_","-")).strip()
    filepath = os.path.join(OUTPUT_DIR, f"{safe_title[:60]}.md")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"[✓] 已生成报告：{filepath}")


def main():
    # 读取 JSON
    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    items = data["items"]
    print(f"检测到 {len(items)} 条研究内容，开始逐条分析...\n")

    for i, item in enumerate(items, start=1):
        print(f"\n============== 分析 {i}/{len(items)}：{item['title']} ==============\n")

        prompt = build_prompt(item)
        report = analyze_item(prompt)

        save_report(item, report)

        time.sleep(1)  # 防止过快触发限流


if __name__ == "__main__":
    main()
