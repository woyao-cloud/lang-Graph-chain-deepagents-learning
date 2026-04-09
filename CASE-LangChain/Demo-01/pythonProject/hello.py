
import os
import string
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.prebuilt import create_react_agent
from langchain.tools import tool

# 1. 设置环境变量，指向阿里云 DashScope
os.environ["OPENAI_API_KEY"] = "sk-723b202be3804cd89fef3970bc92675f"
os.environ["OPENAI_API_BASE"] = "https://dashscope.aliyuncs.com/compatible-mode/v1"

# 2. 初始化 Qwen 模型
# 将 model 参数设置为您想要的 Qwen 版本，例如 qwen-max
llm = ChatOpenAI(
    model="qwen-max",
    temperature=0.7
)

# 3. 定义工具TavilySearchResults(max_results=2)
tools = [getWeather]

@tool
def getWeather() -> string:
    """Get weather  for a city.

    Args:
        city: string
-
    """
    return "sunny"

# 4. 创建 Agent
agent_executor = create_react_agent(llm, tools)

# 5. 运行
response = agent_executor.invoke({
    "messages": [("user", "今天北京的天气怎么样？")]
})

print(response["messages"][-1].content)