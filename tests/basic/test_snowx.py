"""
Test SnowX provider integration.
"""

import unittest
from unittest.mock import patch, MagicMock
from aider.models import Model
from aider.snowx import SnowXClient, SnowXStreamHandler


class TestSnowX(unittest.TestCase):
    """Test SnowX provider functionality."""
    
    def test_snowx_model_validation(self):
        """Test that SnowX models don't require API keys."""
        model = Model("snowx/gpt-4o")
        env_result = model.validate_environment()
        self.assertTrue(env_result.get("keys_in_environment"))
        self.assertEqual(env_result.get("missing_keys"), [])
        
    def test_snowx_model_info(self):
        """Test that SnowX models have correct metadata."""
        model = Model("snowx/gpt-4o")
        self.assertEqual(model.info.get("litellm_provider"), "snowx")
        self.assertEqual(model.info.get("max_input_tokens"), 128000)
        self.assertEqual(model.info.get("max_output_tokens"), 4096)
        self.assertTrue(model.info.get("supports_vision"))
        
    def test_snowx_o4_mini_high(self):
        """Test that o4-mini-high has reasoning effort set."""
        model = Model("snowx/o4-mini-high")
        self.assertIsNotNone(model.extra_params)
        self.assertIsNotNone(model.extra_params.get("extra_body"))
        self.assertEqual(model.extra_params["extra_body"]["reasoning_effort"], "high")
        
    def test_snowx_reasoning_models(self):
        """Test that reasoning models have correct tags."""
        # MAI-DS-R1 should have think tag
        model = Model("snowx/mai-ds-r1")
        self.assertEqual(model.reasoning_tag, "think")
        
        # DeepSeek-R1 should have think tag
        model = Model("snowx/deepseek-r1")
        self.assertEqual(model.reasoning_tag, "think")
        
    def test_snowx_aliases(self):
        """Test that SnowX aliases work correctly."""
        from aider.models import MODEL_ALIASES
        
        self.assertEqual(MODEL_ALIASES.get("snowx"), "snowx/gpt-4.1")
        self.assertEqual(MODEL_ALIASES.get("snowx-claude"), "snowx/claude-3-5-sonnet")
        self.assertEqual(MODEL_ALIASES.get("snowx-mini"), "snowx/gpt-4.1-mini")
        self.assertEqual(MODEL_ALIASES.get("snowx-o4"), "snowx/o4-mini")
        self.assertEqual(MODEL_ALIASES.get("snowx-r1"), "snowx/deepseek-r1")
        
    def test_snowx_client_model_mapping(self):
        """Test SnowX client model name mapping."""
        client = SnowXClient()
        
        # Test model name mappings
        self.assertEqual(client._get_api_model_name("snowx/gpt-4o"), "gpt-4o")
        self.assertEqual(client._get_api_model_name("snowx/claude-3-5-sonnet"), 
                        "us.anthropic.claude-3-5-sonnet-20241022-v2:0")
        self.assertEqual(client._get_api_model_name("snowx/deepseek-r1"), "DeepSeek-R1")
        
        # Test provider mappings
        self.assertEqual(client._get_provider("gpt-4o"), "GPT")
        self.assertEqual(client._get_provider("us.anthropic.claude-3-5-sonnet-20241022-v2:0"), "BEDROCK")
        self.assertEqual(client._get_provider("DeepSeek-R1"), "FOUNDRY")
        
    def test_snowx_stream_handler_thinking(self):
        """Test SnowX stream handler thinking block processing."""
        handler = SnowXStreamHandler()
        
        # Test content without thinking
        result = handler.process_thinking_content("Hello world")
        self.assertEqual(result["content"], "Hello world")
        self.assertEqual(result["thinking"], "")
        
        # Test content with thinking block
        handler = SnowXStreamHandler()
        result1 = handler.process_thinking_content("Before <think>")
        self.assertEqual(result1["content"], "Before ")
        self.assertEqual(result1["thinking"], "")
        
        result2 = handler.process_thinking_content("thinking content")
        self.assertEqual(result2["content"], "")
        self.assertEqual(result2["thinking"], "thinking content")
        
        result3 = handler.process_thinking_content("</think> After")
        self.assertEqual(result3["content"], " After")
        self.assertEqual(result3["thinking"], "")
        
    @patch('aider.snowx.requests.Session')
    def test_snowx_send_completion(self, mock_session_class):
        """Test that SnowX models use the custom client."""
        # Mock the session
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        # Mock the response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "Test response"
                },
                "finish_reason": "stop"
            }]
        }
        mock_session.post.return_value = mock_response
        
        # Test send_completion with SnowX model
        model = Model("snowx/gpt-4o")
        messages = [{"role": "user", "content": "Hello"}]
        
        hash_obj, response = model.send_completion(
            messages=messages,
            functions=None,
            stream=False
        )
        
        # Verify the request was made
        mock_session.post.assert_called_once()
        call_args = mock_session.post.call_args
        
        # Check URL
        self.assertEqual(call_args[0][0], "https://api.snowx.io/api/portkey/chat/completions")
        
        # Check request body
        request_body = call_args[1]["json"]
        self.assertEqual(request_body["model"], "gpt-4o")
        self.assertEqual(request_body["provider"], "GPT")
        self.assertEqual(len(request_body["messages"]), 1)
        self.assertEqual(request_body["messages"][0]["content"], "Hello")
        
        # Check response
        self.assertEqual(response["choices"][0]["message"]["content"], "Test response")


if __name__ == "__main__":
    unittest.main() 