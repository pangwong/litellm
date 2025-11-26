"""
Test StepFlow streaming support
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

os.environ["STEPFLOW_API_KEY"] = "2kZ2irJpqrVk94Fa3rRZkTW4kWYTX0K6qlWribKEkFmjbcoiQIeP7L0F9Kb5SJ1qA"

import asyncio
from litellm import acompletion

async def test_streaming():
    print("Testing stepflow/gpt-4o with streaming...")
    print("-" * 60)

    try:
        response = await acompletion(
            model="stepflow/gpt-4o",
            messages=[{"role": "user", "content": "Count from 1 to 5, one number per line"}],
            api_base="https://api.stepfun.com",
            temperature=0.7,
            max_tokens=100,
            stream=True,
        )

        print("✅ Streaming started successfully!")
        print("\nReceived chunks:")
        print("-" * 60)

        full_response = ""
        async for chunk in response:
            if hasattr(chunk, 'choices') and len(chunk.choices) > 0:
                content = chunk.choices[0].delta.content or ""
                if content:
                    print(content, end="", flush=True)
                    full_response += content

        print("\n" + "-" * 60)
        print(f"\n✅ Complete response received: {len(full_response)} chars")
        print(f"Response: {full_response}")

    except Exception as e:
        print(f"❌ ERROR: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_streaming())
