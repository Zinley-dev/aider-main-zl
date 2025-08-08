#!/usr/bin/env python3
"""Test script for Snowx GPT-5 model support."""

import json

# Test configuration for GPT-5 models
test_models = [
    {
        "model": "snowx/gpt-5",
        "api_name": "gpt-5-chat",
        "provider": "FOUNDRY"
    },
    {
        "model": "snowx/gpt-5-mini",
        "api_name": "gpt-5-mini",
        "provider": "FOUNDRY"
    },
    {
        "model": "snowx/gpt-5-nano",
        "api_name": "gpt5-nano",
        "provider": "FOUNDRY"
    }
]

print("Testing Snowx GPT-5 Model Configuration")
print("=" * 40)

# Check snowx.py mappings
print("\n1. Checking snowx.py model mappings...")
with open("/Users/khoinguyen/Desktop/aider-main-zl/aider/snowx.py", "r") as f:
    content = f.read()
    for test in test_models:
        model_map = f'"{test["model"]}": "{test["api_name"]}"'
        provider_map = f'"{test["api_name"]}": "{test["provider"]}"'
        
        if model_map in content:
            print(f"✓ {test['model']} -> {test['api_name']} mapping found")
        else:
            print(f"✗ {test['model']} -> {test['api_name']} mapping NOT found")
            
        if provider_map in content:
            print(f"✓ {test['api_name']} -> {test['provider']} provider mapping found")
        else:
            print(f"✗ {test['api_name']} -> {test['provider']} provider mapping NOT found")

# Check model-metadata.json
print("\n2. Checking model-metadata.json...")
with open("/Users/khoinguyen/Desktop/aider-main-zl/aider/resources/model-metadata.json", "r") as f:
    metadata = json.load(f)
    for test in test_models:
        if test["model"] in metadata:
            print(f"✓ {test['model']} found in metadata")
            model_data = metadata[test["model"]]
            print(f"  - max_tokens: {model_data.get('max_tokens')}")
            print(f"  - litellm_provider: {model_data.get('litellm_provider')}")
        else:
            print(f"✗ {test['model']} NOT found in metadata")

# Check model-settings.yml
print("\n3. Checking model-settings.yml...")
with open("/Users/khoinguyen/Desktop/aider-main-zl/aider/resources/model-settings.yml", "r") as f:
    content = f.read()
    for test in test_models:
        setting_line = f"- name: {test['model']}"
        if setting_line in content:
            print(f"✓ {test['model']} found in settings")
        else:
            print(f"✗ {test['model']} NOT found in settings")

print("\n" + "=" * 40)
print("Configuration test complete!")
print("\nTo use the new models with aider:")
print("  aider --model snowx/gpt-5")
print("  aider --model snowx/gpt-5-mini")
print("  aider --model snowx/gpt-5-nano")