#!/usr/bin/env python3
"""Verify consistency between snowx models and their base counterparts."""

import sys
sys.path.insert(0, '.')

from aider.models import Model

def compare_models(snowx_name, base_name, description):
    """Compare key settings between snowx and base models."""
    snowx_model = Model(snowx_name)
    base_model = Model(base_name)
    
    print(f"\n{description}:")
    print(f"  Snowx: {snowx_name}")
    print(f"  Base:  {base_name}")
    
    # Compare key settings
    settings = [
        ('use_temperature', True),
        ('edit_format', True),
        ('use_repo_map', True),
        ('examples_as_sys_msg', True),
        ('accepts_settings', True),
        ('reasoning_tag', False),  # Can be different
        ('extra_params', False),  # Can be different
    ]
    
    all_match = True
    for setting, must_match in settings:
        snowx_val = getattr(snowx_model, setting, None)
        base_val = getattr(base_model, setting, None)
        
        if must_match and snowx_val != base_val:
            print(f"  ❌ {setting}: snowx={snowx_val} vs base={base_val}")
            all_match = False
        else:
            status = "✅" if snowx_val == base_val else "ℹ️"
            print(f"  {status} {setting}: snowx={snowx_val} vs base={base_val}")
    
    return all_match

def main():
    print("Verifying Consistency Between SnowX and Base Models")
    print("="*60)
    
    comparisons = [
        # GPT models
        ("snowx/gpt-4o", "openai/gpt-4o", "GPT-4o"),
        ("snowx/gpt-4.1", "openai/gpt-4.1", "GPT-4.1"),
        ("snowx/o4-mini", "openai/o4-mini", "O4-mini"),
        
        # Claude models
        ("snowx/claude-3-7-sonnet", "anthropic/claude-3-7-sonnet-20250219", "Claude 3.7 Sonnet"),
        ("snowx/claude-3-5-sonnet", "anthropic/claude-3-5-sonnet-20241022", "Claude 3.5 Sonnet"),
        
        # Grok models
        ("snowx/grok-3", "openrouter/x-ai/grok-3-beta", "Grok-3"),
        ("snowx/grok-3-mini", "openrouter/x-ai/grok-3-mini-beta", "Grok-3-mini"),
        
        # Deepseek models
        ("snowx/deepseek-r1", "deepseek/deepseek-reasoner", "DeepSeek R1"),
        ("snowx/deepseek-v3", "deepseek/deepseek-chat", "DeepSeek V3"),
    ]
    
    all_pass = True
    for snowx, base, desc in comparisons:
        if not compare_models(snowx, base, desc):
            all_pass = False
    
    print("\n" + "="*60)
    if all_pass:
        print("✅ All critical settings match!")
    else:
        print("❌ Some critical settings don't match!")
    
    return all_pass

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 