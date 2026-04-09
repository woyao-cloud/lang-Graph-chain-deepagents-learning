# demo_fix_deepseek_deepagent.py
import os
from typing import Literal
from tavily import TavilyClient
from langchain_openai import ChatOpenAI
from deepagents import create_deep_agent

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "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")
tavily_client = TavilyClient(api_key=TAVILY_API_KEY)

def internet_search(
    query: str,
    max_results: int = 5,
    topic: Literal["general", "news", "finance"] = "general",
    include_raw_content: bool = False,
):
    """Run a web search via Tavily"""
    return tavily_client.search(
        query,
        max_results=max_results,
        include_raw_content=include_raw_content,
        topic=topic,
    )

research_instructions = """You are an expert researcher. Your job is to conduct thorough research and then write a polished report.

You have access to an internet search tool as your primary means of gathering information.

## `internet_search`

Use this to run an internet search for a given query. You can specify the max number of results to return, the topic, and whether raw content should be included.
"""
api_key = os.getenv("OPENAI_API_KEY", "sk-723b202be3804cd89fef3970bc92675f")
api_base = os.getenv("OPENAI_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")

# --- 关键修复：构造 ChatOpenAI 实例并传入 create_deep_agent ---
llm = ChatOpenAI(
    api_key=api_key,
    base_url=api_base,  # 指向 DashScope 的 OpenAI 兼容 URL
    model="deepseek-v3.2-exp",  # 或 "qwen-turbo" / 您有权限的模型名qwen3-max qwen-max deepseek-v3.2-exp
    temperature=0.2
)

agent = create_deep_agent(
    model=llm,                   # 传入已初始化的 LLM 实例（而不是字符串）
    tools=[internet_search],
    system_prompt=research_instructions,
    # 不要再次传 api_key 给 create_deep_agent，LLM 已包含凭据
)

# 调用 agent
result = agent.invoke({"messages": [{"role": "user", "content": "What is LangGraph?"}]})

print(result["messages"][-1].content)