"""
LLM客户端封装
统一使用OpenAI格式调用
"""

import json
import re
from typing import Optional, Dict, Any, List
from openai import OpenAI

from ..config import Config


class LLMClient:
    """LLM客户端"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 600.0
    ):
        self.api_key = api_key or Config.LLM_API_KEY
        self.base_url = base_url or Config.LLM_BASE_URL
        self.model = model or Config.LLM_MODEL_NAME
        self.timeout = timeout

        if not self.api_key:
            raise ValueError("LLM_API_KEY 未配置")

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout
        )
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: Optional[Dict] = None
    ) -> str:
        """
        发送聊天请求
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            response_format: 响应格式（如JSON模式）
            
        Returns:
            模型响应文本
        """
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        if response_format:
            kwargs["response_format"] = response_format

        # 添加 timeout 参数
        kwargs["timeout"] = self.timeout

        try:
            response = self.client.chat.completions.create(**kwargs)
        except Exception as e:
            raise Exception(f"LLM调用失败: {str(e)}")
        content = response.choices[0].message.content
        # 部分模型（如MiniMax M2.5）会在content中包含<thinking>思考内容，需要移除
        content = re.sub(r'<thinking>[\s\S]*?</thinking>', '', content).strip()
        return content

    def chat_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ):
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
            "timeout": self.timeout,
        }
        try:
            stream = self.client.chat.completions.create(**kwargs)
        except Exception as e:
            raise Exception(f"LLM 流式调用失败: {str(e)}")

        thinking = False
        for chunk in stream:
            delta = chunk.choices[0].delta
            if not delta.content:
                continue
            text = delta.content
            if "<think" in text or "<thinking" in text:
                thinking = True
                continue
            if thinking:
                if "</think" in text or "</thinking" in text:
                    thinking = False
                continue
            yield text

    def chat_json(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """
        发送聊天请求并返回JSON

        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数

        Returns:
            解析后的JSON对象
        """
        # 尝试使用 JSON 模式，如果不支持则回退到普通模式
        try:
            response = self.chat(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"}
            )
        except Exception as e:
            # 如果 JSON 模式不被支持，回退到普通模式
            import logging
            logging.warning(f"JSON 模式不被支持，回退到普通模式: {e}")
            response = self.chat(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

        # 清理markdown代码块标记
        cleaned_response = response.strip()
        cleaned_response = re.sub(r'^```(?:json)?\s*\n?', '', cleaned_response, flags=re.IGNORECASE)
        cleaned_response = re.sub(r'\n?```\s*$', '', cleaned_response)
        cleaned_response = cleaned_response.strip()

        # 尝试解析 JSON
        try:
            return json.loads(cleaned_response)
        except json.JSONDecodeError as e:
            # 如果 JSON 被截断，尝试修复
            import logging
            logging.warning(f"JSON 解析失败，尝试修复截断的 JSON: {e}")

            # 尝试找到最后一个完整的对象并截断
            # 统计大括号，找到最后一个完整的对象
            brace_count = 0
            last_valid_pos = 0
            in_string = False
            escape_next = False

            for i, char in enumerate(cleaned_response):
                if escape_next:
                    escape_next = False
                    continue
                if char == '\\':
                    escape_next = True
                    continue
                if char == '"' and not escape_next:
                    in_string = not in_string
                    continue
                if in_string:
                    continue

                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        last_valid_pos = i + 1

            if last_valid_pos > 0:
                fixed_response = cleaned_response[:last_valid_pos]
                # 添加缺失的闭合括号
                open_braces = fixed_response.count('{')
                close_braces = fixed_response.count('}')
                for _ in range(open_braces - close_braces):
                    fixed_response += '}'

                try:
                    fixed_data = json.loads(fixed_response)
                    logging.info(f"成功修复截断的 JSON，原始长度: {len(cleaned_response)}, 修复后长度: {len(fixed_response)}")
                    return fixed_data
                except json.JSONDecodeError:
                    pass

            # 如果修复失败，抛出原始错误
            raise ValueError(f"LLM返回的JSON格式无效（可能被截断）: {e}\n原始内容（前500字符）: {cleaned_response[:500]}...")

