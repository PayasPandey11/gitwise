#!/usr/bin/env python3
"""Debug script to test the router integration."""

def debug_router():
    print("🔍 Debugging Router Integration\n")
    
    try:
        # Test the router directly
        from gitwise.llm.router import get_llm_response
        
        print("1. Testing router with get_llm_response:")
        response = get_llm_response("Say 'Router test successful!' and nothing else.")
        print(f"   Response: {response}")
        
        print("\n✅ Router test passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Router Error: {e}")
        
        # Let's also test the internal function
        try:
            print("\n2. Testing _get_online_llm_response directly:")
            from gitwise.llm.router import _get_online_llm_response
            response = _get_online_llm_response("Say 'Internal router test successful!' and nothing else.")
            print(f"   Response: {response}")
        except Exception as e2:
            print(f"   Internal router error: {e2}")
            import traceback
            traceback.print_exc()
        
        return False

if __name__ == "__main__":
    debug_router() 