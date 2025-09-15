#!/usr/bin/env python3
"""
Simple test script to verify AI connectivity for R2R Financial Close.
Tests both Azure OpenAI and standard OpenAI configurations.
"""

import sys
from pathlib import Path

# Add src to path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from r2r.ai.infra import openai_enabled, call_openai_json
from r2r.config import load_settings_with_env

def test_ai_connection():
    print("=== R2R AI Connection Test ===\n")
    
    # Load settings
    settings = load_settings_with_env()
    print(f"AI Mode: {settings.ai_mode}")
    print(f"Network allowed: {settings.r2r_allow_network}")
    print(f"Azure OpenAI endpoint: {settings.azure_openai_endpoint}")
    print(f"Azure OpenAI deployment: {settings.azure_openai_chat_deployment}")
    print(f"OpenAI API key configured: {'Yes' if settings.openai_api_key else 'No'}")
    print(f"Azure OpenAI API key configured: {'Yes' if settings.azure_openai_api_key else 'No'}")
    print()
    
    # Check if AI is enabled
    if not openai_enabled():
        print("❌ AI is not enabled. Check your configuration:")
        print("   - Ensure R2R_ALLOW_NETWORK=true")
        print("   - Add OPENAI_API_KEY or AZURE_OPENAI_API_KEY to .env")
        return False
    
    print("✅ AI is enabled. Testing connection...")
    
    # Simple test prompt
    test_prompt = """
    Analyze this simple financial data and provide a brief summary:
    - Revenue: $100,000
    - Expenses: $80,000
    - Net Income: $20,000
    
    Respond with a JSON object containing:
    {
        "summary": "brief analysis",
        "status": "healthy/concerning",
        "key_metric": "profit margin percentage"
    }
    """
    
    try:
        result = call_openai_json(
            prompt=test_prompt,
            system="You are a financial analyst. Provide concise, accurate analysis."
        )
        
        print("✅ AI connection successful!")
        print("Response:")
        print(f"  Summary: {result.get('summary', 'N/A')}")
        print(f"  Status: {result.get('status', 'N/A')}")
        print(f"  Key Metric: {result.get('key_metric', 'N/A')}")
        return True
        
    except Exception as e:
        print(f"❌ AI connection failed: {str(e)}")
        
        if "403" in str(e) and "Virtual Network" in str(e):
            print("\n💡 Troubleshooting:")
            print("   - Azure OpenAI firewall is blocking your IP")
            print("   - Try adding OPENAI_API_KEY=sk-... to .env for testing")
            print("   - Contact IT to add your IP to Azure OpenAI allowlist")
        elif "401" in str(e):
            print("\n💡 Troubleshooting:")
            print("   - API key is invalid or expired")
            print("   - Check your .env file configuration")
        else:
            print(f"\n💡 Error details: {e}")
        
        return False

if __name__ == "__main__":
    success = test_ai_connection()
    sys.exit(0 if success else 1)
