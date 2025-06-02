"""
SnowX API client for aider.

This module provides integration with the SnowX API service, which offers
various AI models without requiring API keys.
"""

import json
import time
from typing import Any, Dict, List, Optional, Generator
import requests

from aider.dump import dump  # noqa: F401
from aider.models import model_info_manager


class SnowXStreamHandler:
    """Handles streaming responses from SnowX API."""
    
    def __init__(self):
        self.buffer = ""
        self.full_response = ""
        self.thinking_content = ""
        self.regular_content = ""
        self.is_in_thinking_block = False
        self.thinking_buffer = ""
        
    def process_line(self, line: str) -> Optional[Dict]:
        """Process a single line from the streaming response."""
        line = line.strip()
        if not line or not line.startswith('data: '):
            return None
            
        if line == 'data: [DONE]':
            return {"done": True}
            
        try:
            json_data = line[6:]  # Remove 'data: ' prefix
            return json.loads(json_data)
        except json.JSONDecodeError:
            return None
            
    def process_thinking_content(self, text: str) -> Dict[str, str]:
        """Process text to separate thinking blocks from regular content."""
        
        self.thinking_buffer += text
        result = {"content": "", "thinking": ""}
        
        while True:
            if not self.is_in_thinking_block:
                # Look for opening <think> tag
                think_start = self.thinking_buffer.find('<think>')
                if think_start != -1:
                    # Add content before <think> to regular content
                    before_think = self.thinking_buffer[:think_start]
                    if before_think:
                        self.regular_content += before_think
                        self.full_response += before_think
                        result["content"] = before_think
                    
                    # Remove processed content and enter thinking mode
                    self.thinking_buffer = self.thinking_buffer[think_start + 7:]
                    self.is_in_thinking_block = True
                    continue
                
                # No thinking block found, add all content to regular response
                if self.thinking_buffer:
                    self.regular_content += self.thinking_buffer
                    self.full_response += self.thinking_buffer
                    result["content"] = self.thinking_buffer
                    self.thinking_buffer = ""
                break
                
            else:
                # Look for closing </think> tag
                think_end = self.thinking_buffer.find('</think>')
                if think_end != -1:
                    # Add content before </think> to thinking content
                    thinking_text = self.thinking_buffer[:think_end]
                    if thinking_text:
                        self.thinking_content += thinking_text
                        result["thinking"] = thinking_text
                    
                    # Remove processed content and exit thinking mode
                    self.thinking_buffer = self.thinking_buffer[think_end + 8:]
                    self.is_in_thinking_block = False
                    continue
                
                # Still in thinking block, add content to thinking
                if self.thinking_buffer:
                    self.thinking_content += self.thinking_buffer
                    result["thinking"] = self.thinking_buffer
                    self.thinking_buffer = ""
                break
                
        return result


class SnowXClient:
    """Client for interacting with SnowX API."""
    
    BASE_URL = "https://api.snowx.io/api/portkey/chat/completions"
    
    # Map SnowX model names to their API names
    MODEL_MAP = {
        "snowx/gpt-4o": "gpt-4o",
        "snowx/gpt-4.1": "gpt-4.1",
        "snowx/gpt-4.1-mini": "gpt-4.1-mini",
        "snowx/gpt-4.1-nano": "gpt-4.1-nano",
        "snowx/o4-mini": "o4-mini",
        "snowx/o4-mini-high": "o4-mini",  # Uses o4-mini with high reasoning effort
        "snowx/claude-opus-4": "us.anthropic.claude-opus-4-20250514-v1:0",
        "snowx/claude-sonnet-4": "us.anthropic.claude-sonnet-4-20250514-v1:0",
        "snowx/claude-3-7-sonnet": "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
        "snowx/claude-3-5-sonnet": "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
        "snowx/grok-3": "grok-3",
        "snowx/grok-3-mini": "grok-3-mini",
        "snowx/mai-ds-r1": "MAI-DS-R1",
        "snowx/llama-maverick": "Llama-4-Maverick-17B-128E-Instruct-FP8",
        "snowx/deepseek-r1": "DeepSeek-R1",
        "snowx/deepseek-v3": "DeepSeek-V3",
    }
    
    # Map model to provider
    PROVIDER_MAP = {
        "gpt-4o": "GPT",
        "gpt-4.1": "GPT",
        "gpt-4.1-mini": "GPT",
        "gpt-4.1-nano": "GPT",
        "o4-mini": "GPT",
        "us.anthropic.claude-opus-4-20250514-v1:0": "BEDROCK",
        "us.anthropic.claude-sonnet-4-20250514-v1:0": "BEDROCK",
        "us.anthropic.claude-3-7-sonnet-20250219-v1:0": "BEDROCK",
        "us.anthropic.claude-3-5-sonnet-20241022-v2:0": "BEDROCK",
        "grok-3": "FOUNDRY",
        "grok-3-mini": "FOUNDRY",
        "MAI-DS-R1": "FOUNDRY",
        "Llama-4-Maverick-17B-128E-Instruct-FP8": "FOUNDRY",
        "DeepSeek-R1": "FOUNDRY",
        "DeepSeek-V3": "FOUNDRY",
    }
    
    def __init__(self):
        self.session = requests.Session()
        
    def _get_api_model_name(self, model: str) -> str:
        """Get the API model name from the aider model name."""
        return self.MODEL_MAP.get(model, model)
        
    def _get_provider(self, api_model: str) -> str:
        """Get the provider for the given API model."""
        return self.PROVIDER_MAP.get(api_model, "GPT")
        
    def _convert_messages(self, messages: List[Dict]) -> List[Dict]:
        """Convert litellm message format to SnowX format."""
        snowx_messages = []
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            # Handle image content
            if isinstance(content, list):
                snowx_content = []
                for item in content:
                    if item.get("type") == "text":
                        snowx_content.append({
                            "type": "text",
                            "text": item.get("text", "")
                        })
                    elif item.get("type") == "image_url":
                        image_url = item.get("image_url", {})
                        url = image_url.get("url", "")
                        snowx_content.append({
                            "type": "image_url",
                            "image_url": {"url": url}
                        })
                
                snowx_msg = {
                    "role": role,
                    "content": snowx_content
                }
            else:
                snowx_msg = {
                    "role": role,
                    "content": content
                }
                
            # Add tool call info if present
            if "tool_calls" in msg:
                snowx_msg["tool_calls"] = msg["tool_calls"]
            if "tool_call_id" in msg:
                snowx_msg["tool_call_id"] = msg["tool_call_id"]
                snowx_msg["role"] = "tool"
                if "name" in msg:
                    snowx_msg["name"] = msg["name"]
                    
            snowx_messages.append(snowx_msg)
            
        return snowx_messages
        
    def _convert_tools(self, tools: Optional[List[Dict]]) -> Optional[List[Dict]]:
        """Convert litellm tools format to SnowX format."""
        if not tools:
            return None
            
        snowx_tools = []
        for tool in tools:
            if tool.get("type") == "function":
                func = tool.get("function", {})
                snowx_tool = {
                    "type": "function",
                    "function": {
                        "name": func.get("name"),
                        "description": func.get("description", ""),
                        "parameters": func.get("parameters", {})
                    }
                }
                snowx_tools.append(snowx_tool)
                
        return snowx_tools if snowx_tools else None
        
    def create_completion(
        self,
        model: str,
        messages: List[Dict],
        stream: bool = False,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict]] = None,
        tool_choice: Optional[Dict] = None,
        extra_body: Optional[Dict] = None,
        **kwargs
    ) -> Any:
        """Create a completion using SnowX API."""
        
        api_model = self._get_api_model_name(model)
        provider = self._get_provider(api_model)
        
        # Convert messages to SnowX format
        snowx_messages = self._convert_messages(messages)
        
        # Build request body
        request_body = {
            "model": api_model,
            "provider": provider,
            "messages": snowx_messages,
            "stream": stream,
            "agent": "default"
        }
        
        # Get max tokens from model info if not provided
        if max_tokens:
            request_body["max_tokens"] = max_tokens
        else:
            # Get model info from metadata
            try:
                model_info = model_info_manager.get_model_info(model)
                default_max_tokens = model_info.get("max_tokens") or model_info.get("max_output_tokens")
                
                # Special handling for o4-mini models
                if model.startswith("snowx/o4-mini"):
                    # o4-mini uses max_completion_tokens instead of max_tokens
                    request_body["max_completion_tokens"] = default_max_tokens or 100000
                else:
                    request_body["max_tokens"] = default_max_tokens or 4096
            except Exception:
                # Fallback to hardcoded defaults if model info not found
                if model.startswith("snowx/o4-mini"):
                    request_body["max_completion_tokens"] = 100000
                else:
                    request_body["max_tokens"] = 4096
                
        # Handle o4-mini specific parameters
        if model != "snowx/o4-mini" and model != "snowx/o4-mini-high":
            request_body["temperature"] = temperature
            request_body["top_p"] = kwargs.get("top_p", 0.9)
            
        # Handle reasoning effort for o4-mini-high
        if model == "snowx/o4-mini-high":
            if extra_body and "reasoning_effort" in extra_body:
                request_body["reasoning_effort"] = extra_body["reasoning_effort"]
            else:
                request_body["reasoning_effort"] = "high"
                
        # Add tools if provided
        if tools:
            request_body["tools"] = self._convert_tools(tools)
        if tool_choice:
            request_body["tool_choice"] = tool_choice
            
        try:
            if stream:
                # Streaming request
                response = self.session.post(
                    self.BASE_URL,
                    json=request_body,
                    headers={"Content-Type": "application/json"},
                    stream=True
                )
                
                if response.status_code != 200:
                    error_text = response.text
                    raise Exception(f"SnowX API error (status {response.status_code}): {error_text}")
                    
                return self._handle_streaming_response(response, model)
            else:
                # Non-streaming request
                response = self.session.post(
                    self.BASE_URL,
                    json=request_body,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code != 200:
                    error_text = response.text
                    raise Exception(f"SnowX API error (status {response.status_code}): {error_text}")
                    
                data = response.json()
                return self._convert_response(data)
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"SnowX network error: {str(e)}")
            
    def _handle_streaming_response(self, response: requests.Response, model: str) -> Generator[Dict, None, None]:
        """Handle streaming response and yield chunks."""
        
        handler = SnowXStreamHandler()
        
        for line in response.iter_lines():
            if not line:
                continue
                
            line_str = line.decode('utf-8')
            data = handler.process_line(line_str)
            
            if not data:
                continue
                
            if data.get("done"):
                break
                
            # Convert to litellm streaming format
            chunk = {
                "id": data.get("id", f"snowx-{int(time.time())}"),
                "object": "chat.completion.chunk", 
                "created": data.get("created", int(time.time())),
                "model": data.get("model", model),
                "choices": []
            }
            
            for choice in data.get("choices", []):
                delta = choice.get("delta", {})
                chunk_choice = {
                    "index": choice.get("index", 0),
                    "delta": {},
                    "finish_reason": choice.get("finish_reason")
                }
                
                if "content" in delta and delta["content"]:
                    # Process thinking content
                    processed = handler.process_thinking_content(delta["content"])
                    if processed["content"]:
                        chunk_choice["delta"]["content"] = processed["content"]
                    # Note: We don't yield thinking content separately in litellm format
                    
                if "tool_calls" in delta:
                    chunk_choice["delta"]["tool_calls"] = delta["tool_calls"]
                    
                chunk["choices"].append(chunk_choice)
                
            if chunk["choices"] and (chunk["choices"][0]["delta"] or chunk["choices"][0]["finish_reason"]):
                # Convert to object for consistency
                class StreamChunk:
                    def __init__(self, data):
                        self.__dict__.update(data)
                        # Convert nested dicts to objects
                        if hasattr(self, 'choices'):
                            self.choices = [self._dict_to_obj(choice) for choice in self.choices]
                            
                    def _dict_to_obj(self, d):
                        if isinstance(d, dict):
                            obj = type('obj', (object,), {})()
                            for k, v in d.items():
                                setattr(obj, k, self._dict_to_obj(v))
                            return obj
                        elif isinstance(d, list):
                            return [self._dict_to_obj(item) for item in d]
                        else:
                            return d
                            
                yield StreamChunk(chunk)
                
    def _convert_response(self, data: Dict) -> Dict:
        """Convert SnowX response to litellm format."""
        
        # Basic response structure
        response = {
            "id": data.get("id", f"snowx-{int(time.time())}"),
            "object": "chat.completion",
            "created": data.get("created", int(time.time())),
            "model": data.get("model", ""),
            "choices": []
        }
        
        # Convert choices
        for choice in data.get("choices", []):
            message = choice.get("message", {})
            
            converted_choice = {
                "index": choice.get("index", 0),
                "message": {
                    "role": "assistant",
                    "content": message.get("content")
                },
                "finish_reason": choice.get("finish_reason", "stop")
            }
            
            # Add tool calls if present
            if "tool_calls" in message:
                converted_choice["message"]["tool_calls"] = message["tool_calls"]
                
            response["choices"].append(converted_choice)
            
        # Add usage if available
        if "usage" in data:
            response["usage"] = data["usage"]
            
        # Convert to object-like structure that litellm expects
        class Response:
            def __init__(self, data):
                self.__dict__.update(data)
                # Convert nested dicts to objects
                if hasattr(self, 'choices'):
                    self.choices = [self._dict_to_obj(choice) for choice in self.choices]
                if hasattr(self, 'usage'):
                    self.usage = self._dict_to_obj(self.usage)
                    
            def _dict_to_obj(self, d):
                if isinstance(d, dict):
                    obj = type('obj', (object,), {})()
                    for k, v in d.items():
                        setattr(obj, k, self._dict_to_obj(v))
                    return obj
                elif isinstance(d, list):
                    return [self._dict_to_obj(item) for item in d]
                else:
                    return d
                    
        return Response(response)


# Synchronous wrapper for SnowX client
def create_snowx_completion(
    model: str,
    messages: List[Dict],
    stream: bool = False,
    **kwargs
) -> Any:
    """Create a completion using SnowX API."""
    
    client = SnowXClient()
    return client.create_completion(
        model=model,
        messages=messages,
        stream=stream,
        **kwargs
    ) 