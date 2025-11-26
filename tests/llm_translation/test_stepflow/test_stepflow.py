"""
Test StepFlow Provider Integration

This test file verifies that the StepFlow provider is properly integrated into LiteLLM.
To run these tests with real API calls, set the following environment variables:
- STEPFLOW_API_KEY or FLOW_EXTERNAL_TOKEN: Your StepFlow bearer token
- MODEL_PROXY_API_KEY (optional): API key for the inner model provider

Example usage:
    export STEPFLOW_API_KEY="Bearer_xxx"
    export MODEL_PROXY_API_KEY="sk-xxx"

    # Run chat completion test
    python tests/llm_translation/test_stepflow/test_completion.py

    # Run embedding test
    python tests/llm_translation/test_stepflow/test_embedding.py
"""

import os
import sys

# Add the litellm directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

import litellm
from litellm import completion, embedding


def test_stepflow_chat_completion():
    """
    Test StepFlow chat completion

    This test requires:
    - STEPFLOW_API_KEY or FLOW_EXTERNAL_TOKEN environment variable
    - MODEL_PROXY_API_KEY environment variable (optional)
    """
    print("=" * 60)
    print("Testing StepFlow Chat Completion")
    print("=" * 60)

    # Check for API key
    api_key = os.getenv("STEPFLOW_API_KEY") or os.getenv("FLOW_EXTERNAL_TOKEN")
    if not api_key:
        print("❌ Missing STEPFLOW_API_KEY or FLOW_EXTERNAL_TOKEN environment variable")
        print("   Skipping test...")
        return

    print(f"✓ API key found: {api_key[:20]}...")

    # Test with a simple model
    model = "stepflow/claude-sonnet-4-20250514"
    messages = [{"role": "user", "content": "Say hello in 5 words"}]

    print(f"\n🔄 Calling completion with model: {model}")
    print(f"   Messages: {messages}")

    try:
        response = completion(
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=50,
        )

        print("\n✅ Response received successfully!")
        print(f"   Model: {response.model}")
        print(f"   Content: {response.choices[0].message.content}")
        print(f"   Usage: {response.usage}")
        print("\n🎉 StepFlow chat completion test PASSED!")

    except Exception as e:
        print(f"\n❌ Error during completion: {e}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        print("\n💥 StepFlow chat completion test FAILED!")


def test_stepflow_embedding():
    """
    Test StepFlow embeddings

    This test requires:
    - STEPFLOW_API_KEY or FLOW_EXTERNAL_TOKEN environment variable
    - MODEL_PROXY_API_KEY environment variable (optional)
    """
    print("\n" + "=" * 60)
    print("Testing StepFlow Embeddings")
    print("=" * 60)

    # Check for API key
    api_key = os.getenv("STEPFLOW_API_KEY") or os.getenv("FLOW_EXTERNAL_TOKEN")
    if not api_key:
        print("❌ Missing STEPFLOW_API_KEY or FLOW_EXTERNAL_TOKEN environment variable")
        print("   Skipping test...")
        return

    print(f"✓ API key found: {api_key[:20]}...")

    # Test with an embedding model
    model = "stepflow/text-embedding-3-small"
    input_text = ["Hello world", "Embedding test"]

    print(f"\n🔄 Calling embedding with model: {model}")
    print(f"   Input: {input_text}")

    try:
        response = embedding(
            model=model,
            input=input_text,
        )

        print("\n✅ Response received successfully!")
        print(f"   Model: {response.model}")
        print(f"   Data items: {len(response.data)}")
        print(f"   First embedding dimension: {len(response.data[0].embedding)}")
        print(f"   Usage: {response.usage}")
        print("\n🎉 StepFlow embedding test PASSED!")

    except Exception as e:
        print(f"\n❌ Error during embedding: {e}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        print("\n💥 StepFlow embedding test FAILED!")


def test_provider_detection():
    """Test that stepflow/ prefix is correctly detected"""
    print("\n" + "=" * 60)
    print("Testing Provider Detection")
    print("=" * 60)

    from litellm.litellm_core_utils.get_llm_provider_logic import get_llm_provider

    model = "stepflow/claude-sonnet-4-20250514"
    print(f"\n🔍 Testing model: {model}")

    try:
        provider_info = get_llm_provider(model=model)
        detected_provider = provider_info[1]

        print(f"   Detected provider: {detected_provider}")

        if detected_provider == "stepflow":
            print("✅ Provider detection works correctly!")
            print("\n🎉 Provider detection test PASSED!")
        else:
            print(f"❌ Expected 'stepflow' but got '{detected_provider}'")
            print("\n💥 Provider detection test FAILED!")

    except Exception as e:
        print(f"❌ Error during provider detection: {e}")
        import traceback
        traceback.print_exc()
        print("\n💥 Provider detection test FAILED!")


if __name__ == "__main__":
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "StepFlow Provider Test Suite" + " " * 20 + "║")
    print("╚" + "=" * 58 + "╝")

    # Run provider detection test (doesn't need API key)
    test_provider_detection()

    # Run API tests (require API key)
    test_stepflow_chat_completion()
    test_stepflow_embedding()

    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60 + "\n")
