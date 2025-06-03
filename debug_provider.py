#!/usr/bin/env python3
"""Debug script to test provider detection and loading."""

from gitwise.config import load_config
from gitwise.llm.providers import detect_provider_from_config, get_provider_with_fallback

def debug_provider():
    print("🔍 Debugging Provider Detection\n")
    
    try:
        # Load config
        config = load_config()
        print("1. Configuration loaded:")
        print(f"   llm_backend: {config.get('llm_backend')}")
        print(f"   provider: {config.get('provider')}")
        print(f"   google_api_key: {'***' if config.get('google_api_key') else 'None'}")
        
        # Test provider detection
        print("\n2. Provider detection:")
        detected = detect_provider_from_config(config)
        print(f"   Detected provider: {detected}")
        
        # Test provider instantiation  
        print("\n3. Provider instantiation:")
        provider = get_provider_with_fallback(config)
        print(f"   Provider class: {provider.__class__.__name__}")
        print(f"   Provider name: {provider.provider_name}")
        print(f"   Model: {provider.get_model()}")
        
        # Test basic LLM call
        print("\n4. Test LLM call:")
        response = provider.get_response("Say 'Provider test successful!' and nothing else.")
        print(f"   Response: {response}")
        
        print("\n✅ All tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_provider() 