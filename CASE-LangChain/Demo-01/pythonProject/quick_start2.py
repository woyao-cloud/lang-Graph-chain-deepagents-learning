# demo_langgraph_qwen.py
# Minimal LangGraph + Qwen demo (Python)

import os
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

# Option A: 从环境变量读取（推荐）
# 在 shell 中：
# export OPENAI_API_KEY="您的_DASHSCOPE_API_KEY"
# export OPENAI_API_BASE="https://dashscope.aliyuncs.com/compatible-mode/v1"

# Option B: 或在代码中直接传入（仅测试用）
api_key = os.getenv("OPENAI_API_KEY", "sk-723b202be3804cd89fef3970bc92675f")
api_base = os.getenv("OPENAI_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")

# 初始化 Qwen（通过 OpenAI 兼容接口）
llm = ChatOpenAI(
    api_key=api_key,
    base_url=api_base,    # 指向 DashScope 的 OpenAI 兼容 URL
    model="qwen-max",     # 或 "qwen-turbo" / 您有权限的模型名
    temperature=0.2
)

# 创建一个最简单的 React 风格 agent（不带外部工具）
agent_executor = create_react_agent(llm, tools=[])

# 示例调用 —— 发送用户消息并打印模型回复
call_payload = {"messages": [("user", "请简要介绍杭州有哪些值得去的景点？")]}
result = agent_executor.invoke(call_payload)

# langgraph 返回的结构里通常包含 messages；这里打印最后一条回复
print(result["messages"][-1].content)