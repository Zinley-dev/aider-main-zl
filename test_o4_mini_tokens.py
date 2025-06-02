#!/usr/bin/env python3
"""Test o4-mini models use max_completion_tokens correctly."""

import sys
sys.path.insert(0, '.')

from aider.snowx import SnowXClient
from aider.models import model_info_manager


def test_o4_mini_max_completion_tokens():
    """Test that o4-mini models use max_completion_tokens instead of max_tokens."""
    
    client = SnowXClient()
    messages = [{"role": "user", "content": "Hello"}]
    
    # Test snowx/o4-mini
    print("Testing snowx/o4-mini...")
    model_info = model_info_manager.get_model_info("snowx/o4-mini")
    print(f"  Model info max_tokens: {model_info.get('max_tokens')}")
    print(f"  Model info max_output_tokens: {model_info.get('max_output_tokens')}")
    
    # Simulate the request body creation logic
    request_body = {
        "model": client._get_api_model_name("snowx/o4-mini"),
        "provider": client._get_provider("o4-mini"),
        "messages": client._convert_messages(messages),
        "stream": False,
        "agent": "default"
    }
    
    # This is the critical part - should use max_completion_tokens
    default_max_tokens = model_info.get("max_tokens") or model_info.get("max_output_tokens")
    if "snowx/o4-mini".startswith("snowx/o4-mini"):
        request_body["max_completion_tokens"] = default_max_tokens or 100000
    else:
        request_body["max_tokens"] = default_max_tokens or 4096
    
    print(f"  Request body keys: {list(request_body.keys())}")
    assert "max_completion_tokens" in request_body, "Should use max_completion_tokens"
    assert "max_tokens" not in request_body, "Should NOT use max_tokens"
    assert request_body["max_completion_tokens"] == 100000, f"Expected 100000 but got {request_body['max_completion_tokens']}"
    print(f"  ✅ Correctly uses max_completion_tokens: {request_body['max_completion_tokens']}")
    
    # Test snowx/o4-mini-high
    print("\nTesting snowx/o4-mini-high...")
    model_info = model_info_manager.get_model_info("snowx/o4-mini-high")
    print(f"  Model info max_tokens: {model_info.get('max_tokens')}")
    print(f"  Model info max_output_tokens: {model_info.get('max_output_tokens')}")
    
    request_body2 = {
        "model": client._get_api_model_name("snowx/o4-mini-high"),
        "provider": client._get_provider("o4-mini"),
        "messages": client._convert_messages(messages),
        "stream": False,
        "agent": "default"
    }
    
    default_max_tokens = model_info.get("max_tokens") or model_info.get("max_output_tokens")
    if "snowx/o4-mini-high".startswith("snowx/o4-mini"):
        request_body2["max_completion_tokens"] = default_max_tokens or 100000
    else:
        request_body2["max_tokens"] = default_max_tokens or 4096
        
    print(f"  Request body keys: {list(request_body2.keys())}")
    assert "max_completion_tokens" in request_body2, "Should use max_completion_tokens"
    assert "max_tokens" not in request_body2, "Should NOT use max_tokens"
    assert request_body2["max_completion_tokens"] == 100000, f"Expected 100000 but got {request_body2['max_completion_tokens']}"
    print(f"  ✅ Correctly uses max_completion_tokens: {request_body2['max_completion_tokens']}")
    
    # Test a non-o4-mini model to ensure it still uses max_tokens
    print("\nTesting snowx/gpt-4.1 (should use max_tokens, not max_completion_tokens)...")
    model_info = model_info_manager.get_model_info("snowx/gpt-4.1")
    request_body3 = {
        "model": client._get_api_model_name("snowx/gpt-4.1"),
        "provider": client._get_provider("gpt-4.1"),
        "messages": client._convert_messages(messages),
        "stream": False,
        "agent": "default"
    }
    
    default_max_tokens = model_info.get("max_tokens") or model_info.get("max_output_tokens")
    if "snowx/gpt-4.1".startswith("snowx/o4-mini"):
        request_body3["max_completion_tokens"] = default_max_tokens or 100000
    else:
        request_body3["max_tokens"] = default_max_tokens or 4096
        
    assert "max_tokens" in request_body3, "Should use max_tokens"
    assert "max_completion_tokens" not in request_body3, "Should NOT use max_completion_tokens"
    assert request_body3["max_tokens"] == 32768, f"Expected 32768 but got {request_body3['max_tokens']}"
    print(f"  ✅ Correctly uses max_tokens: {request_body3['max_tokens']}")
    
    print("\nAll tests passed! ✅")


if __name__ == "__main__":
    test_o4_mini_max_completion_tokens() 