import os
from typing import List, Dict

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# 初始化DeepSeek客户端
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)


def call_llm(prompt: str, model: str = "deepseek-chat", temperature: float = 0.1) -> str:
    """
    调用DeepSeek LLM生成响应
    
    Args:
        prompt: 提示词
        model: 模型名称，默认使用deepseek-chat
        temperature: 温度参数，控制输出的随机性
    
    Returns:
        LLM生成的响应文本
    """
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=2000
        )
        content = response.choices[0].message.content
        if content is None:
            raise ValueError("LLM返回了空响应")
        return content
    except Exception as e:
        print(f"LLM调用失败: {e}")
        raise


def call_llm_with_history(messages: List[Dict[str, str]], model: str = "deepseek-chat",
                          temperature: float = 0.1) -> str:
    """
    调用DeepSeek LLM，支持对话历史
    
    Args:
        messages: 消息历史列表
        model: 模型名称
        temperature: 温度参数
    
    Returns:
        LLM生成的响应文本
    """
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,  # type: ignore
            temperature=temperature,
            max_tokens=2000
        )
        content = response.choices[0].message.content
        if content is None:
            raise ValueError("LLM返回了空响应")
        return content
    except Exception as e:
        print(f"LLM调用失败: {e}")
        raise


if __name__ == "__main__":
    # 测试LLM调用
    test_prompt = "请生成一个简单的SQL查询来获取用户表中的所有记录"
    result = call_llm(test_prompt)
    print(f"测试结果: {result}")
