"""
Quick test to debug stepflow/gpt-4o specifically
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

os.environ["STEPFLOW_API_KEY"] = "2kZ2irJpqrVk94Fa3rRZkTW4kWYTX0K6qlWribKEkFmjbcoiQIeP7L0F9Kb5SJ1qA"

import litellm
from litellm import completion
from litellm.litellm_core_utils.get_llm_provider_logic import get_llm_provider

# First test provider detection
model = "stepflow/gpt-4o"
provider_info = get_llm_provider(model=model)
print(f"Provider detection result: {provider_info}")
print(f"Detected provider: {provider_info[1]}")
print("-" * 60)

litellm.set_verbose = True

print("Testing stepflow/gpt-4o model...")
print("-" * 60)

try:
    response = completion(
        model="stepflow/gpt-4o",
        messages=[{"role": "user", "content": "Say hi"}],
        api_base="https://api.stepfun.com",
        temperature=0.7,
        max_tokens=20,
    )

    print("✅ SUCCESS!")
    print(f"Model: {response.model}")
    print(f"Content: {response.choices[0].message.content}")
    print(f"Usage: {response.usage}")

except Exception as e:
    print(f"❌ ERROR: {e}")
    print(f"Error type: {type(e).__name__}")
    import traceback
    traceback.print_exc()
