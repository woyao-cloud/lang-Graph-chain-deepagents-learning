from openai import OpenAI

client = OpenAI(
    api_key="sk-723b202be3804cd89fef3970bc92675f",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

response = client.chat.completions.create(
    model="qwen-max",
    messages=[{"role": "user", "content": "你好"}]
)

print(response.choices[0].message.content)