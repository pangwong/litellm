#!/usr/bin/env python3
"""
Test all configured StepFlow models via LiteLLM proxy completion API.
Generates a detailed report of test results.
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Optional

import httpx


# Configuration
LITELLM_BASE_URL = "http://localhost:4000"
TEST_MESSAGE = "Hello! Please respond with 'Test successful' if you can read this."
TIMEOUT = 120  # 2 minutes timeout per model


class ModelTestResult:
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.success = False
        self.response_time = 0.0
        self.response_text = ""
        self.error_message = ""
        self.status_code = None
        self.usage = {}

    def to_dict(self):
        return {
            "model_name": self.model_name,
            "success": self.success,
            "response_time_seconds": round(self.response_time, 2),
            "response_text": self.response_text[:200] if self.response_text else "",
            "error_message": self.error_message,
            "status_code": self.status_code,
            "usage": self.usage,
        }


async def test_model(model_name: str, client: httpx.AsyncClient) -> ModelTestResult:
    """Test a single model via completion API"""
    result = ModelTestResult(model_name)

    request_body = {
        "model": model_name,
        "messages": [
            {"role": "user", "content": TEST_MESSAGE}
        ],
        "max_tokens": 100,
        "temperature": 0.7,
    }

    print(f"Testing {model_name}...", end=" ", flush=True)

    start_time = time.time()
    try:
        response = await client.post(
            f"{LITELLM_BASE_URL}/chat/completions",
            json=request_body,
            timeout=TIMEOUT,
        )

        result.response_time = time.time() - start_time
        result.status_code = response.status_code

        if response.status_code == 200:
            response_json = response.json()

            # Extract response text
            if "choices" in response_json and response_json["choices"]:
                message = response_json["choices"][0].get("message", {})
                result.response_text = message.get("content", "")

            # Extract usage
            if "usage" in response_json:
                result.usage = response_json["usage"]

            result.success = True
            print(f"✓ OK ({result.response_time:.2f}s)")
        else:
            error_body = response.text
            result.error_message = f"HTTP {response.status_code}: {error_body[:200]}"
            print(f"✗ FAILED - {result.error_message}")

    except httpx.TimeoutException:
        result.response_time = time.time() - start_time
        result.error_message = f"Timeout after {TIMEOUT}s"
        print(f"✗ TIMEOUT")
    except Exception as e:
        result.response_time = time.time() - start_time
        result.error_message = str(e)
        print(f"✗ ERROR - {str(e)[:100]}")

    return result


async def get_available_models(client: httpx.AsyncClient) -> List[str]:
    """Get list of available models from LiteLLM proxy"""
    try:
        response = await client.get(f"{LITELLM_BASE_URL}/models")
        if response.status_code == 200:
            data = response.json()
            models = [m["id"] for m in data.get("data", [])]
            return models
        else:
            print(f"Failed to get models: HTTP {response.status_code}")
            return []
    except Exception as e:
        print(f"Error getting models: {e}")
        return []


async def main():
    """Main test function"""
    print("=" * 80)
    print("LiteLLM StepFlow Models Test Suite")
    print("=" * 80)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"LiteLLM proxy URL: {LITELLM_BASE_URL}")
    print(f"Timeout per model: {TIMEOUT}s")
    print("=" * 80)
    print()

    async with httpx.AsyncClient() as client:
        # Get available models
        print("Fetching available models from proxy...")
        all_models = await get_available_models(client)

        if not all_models:
            print("No models available or failed to fetch model list!")
            return

        # Filter only stepflow models
        stepflow_models = [m for m in all_models if m.startswith("stepflow/")]

        print(f"Found {len(all_models)} total models")
        print(f"Found {len(stepflow_models)} StepFlow models")
        print()

        if not stepflow_models:
            print("No StepFlow models found in the proxy!")
            return

        # Test each model
        results: List[ModelTestResult] = []

        for i, model_name in enumerate(stepflow_models, 1):
            print(f"[{i}/{len(stepflow_models)}] ", end="")
            result = await test_model(model_name, client)
            results.append(result)

            # Small delay between tests
            await asyncio.sleep(0.5)

        print()
        print("=" * 80)
        print("Test Summary")
        print("=" * 80)

        # Calculate statistics
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]

        print(f"Total models tested: {len(results)}")
        print(f"Successful: {len(successful)} ({len(successful)/len(results)*100:.1f}%)")
        print(f"Failed: {len(failed)} ({len(failed)/len(results)*100:.1f}%)")
        print()

        if successful:
            avg_time = sum(r.response_time for r in successful) / len(successful)
            print(f"Average response time (successful): {avg_time:.2f}s")
            print(f"Fastest: {min(r.response_time for r in successful):.2f}s")
            print(f"Slowest: {max(r.response_time for r in successful):.2f}s")
            print()

        # Group by provider
        print("Results by Provider:")
        print("-" * 80)

        providers = {}
        for result in results:
            # Extract provider from model name (after stepflow/)
            model_id = result.model_name.replace("stepflow/", "")

            if model_id.startswith("gpt") or model_id.startswith("o1") or model_id.startswith("o3") or model_id.startswith("o4"):
                provider = "OpenAI"
            elif model_id.startswith("claude"):
                provider = "Anthropic (Claude)"
            elif model_id.startswith("gemini") or model_id.startswith("gemma"):
                provider = "Google (Gemini)"
            elif model_id.startswith("qwen"):
                provider = "Alibaba (Qwen)"
            elif model_id.startswith("deepseek"):
                provider = "DeepSeek"
            elif model_id.startswith("glm"):
                provider = "Zhipu AI (GLM)"
            elif model_id.startswith("grok"):
                provider = "xAI (Grok)"
            elif model_id.startswith("kimi"):
                provider = "Moonshot AI (Kimi)"
            elif model_id.startswith("doubao"):
                provider = "ByteDance (Doubao)"
            elif model_id.startswith("minimax"):
                provider = "MiniMax"
            elif model_id.startswith("llama"):
                provider = "Meta (Llama)"
            else:
                provider = "Other"

            if provider not in providers:
                providers[provider] = {"success": 0, "failed": 0, "models": []}

            if result.success:
                providers[provider]["success"] += 1
            else:
                providers[provider]["failed"] += 1

            providers[provider]["models"].append(result)

        for provider in sorted(providers.keys()):
            stats = providers[provider]
            total = stats["success"] + stats["failed"]
            success_rate = stats["success"] / total * 100 if total > 0 else 0
            print(f"{provider}: {stats['success']}/{total} successful ({success_rate:.1f}%)")

        print()

        # Show failed models
        if failed:
            print("Failed Models:")
            print("-" * 80)
            for result in failed:
                print(f"  {result.model_name}")
                print(f"    Error: {result.error_message}")
                print()

        # Save detailed results to JSON
        report_file = f"test-results-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        report_data = {
            "test_metadata": {
                "timestamp": datetime.now().isoformat(),
                "total_models": len(results),
                "successful": len(successful),
                "failed": len(failed),
                "success_rate": f"{len(successful)/len(results)*100:.1f}%",
            },
            "provider_summary": {
                provider: {
                    "total": stats["success"] + stats["failed"],
                    "successful": stats["success"],
                    "failed": stats["failed"],
                    "success_rate": f"{stats['success']/(stats['success']+stats['failed'])*100:.1f}%" if stats["success"]+stats["failed"] > 0 else "0.0%"
                }
                for provider, stats in providers.items()
            },
            "detailed_results": [r.to_dict() for r in results],
        }

        with open(f"dev-scripts/{report_file}", "w") as f:
            json.dump(report_data, f, indent=2)

        print(f"Detailed results saved to: dev-scripts/{report_file}")
        print()

        # Generate markdown report
        md_report_file = f"test-report-{datetime.now().strftime('%Y%m%d-%H%M%S')}.md"
        with open(f"dev-scripts/{md_report_file}", "w") as f:
            f.write("# LiteLLM StepFlow Models Test Report\n\n")
            f.write(f"**Test Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**LiteLLM Proxy URL:** {LITELLM_BASE_URL}\n\n")

            f.write("## Summary\n\n")
            f.write(f"- **Total Models Tested:** {len(results)}\n")
            f.write(f"- **Successful:** {len(successful)} ({len(successful)/len(results)*100:.1f}%)\n")
            f.write(f"- **Failed:** {len(failed)} ({len(failed)/len(results)*100:.1f}%)\n\n")

            if successful:
                avg_time = sum(r.response_time for r in successful) / len(successful)
                f.write(f"- **Average Response Time:** {avg_time:.2f}s\n")
                f.write(f"- **Fastest Response:** {min(r.response_time for r in successful):.2f}s\n")
                f.write(f"- **Slowest Response:** {max(r.response_time for r in successful):.2f}s\n\n")

            f.write("## Results by Provider\n\n")
            f.write("| Provider | Success | Failed | Total | Success Rate |\n")
            f.write("|----------|---------|--------|-------|-------------|\n")

            for provider in sorted(providers.keys()):
                stats = providers[provider]
                total = stats["success"] + stats["failed"]
                success_rate = stats["success"] / total * 100 if total > 0 else 0
                f.write(f"| {provider} | {stats['success']} | {stats['failed']} | {total} | {success_rate:.1f}% |\n")

            f.write("\n## Detailed Results\n\n")

            for provider in sorted(providers.keys()):
                f.write(f"### {provider}\n\n")

                for result in sorted(providers[provider]["models"], key=lambda x: x.model_name):
                    status = "✓" if result.success else "✗"
                    f.write(f"**{status} {result.model_name}**\n\n")

                    if result.success:
                        f.write(f"- Response Time: {result.response_time:.2f}s\n")
                        if result.usage:
                            f.write(f"- Tokens: {result.usage.get('total_tokens', 'N/A')} total\n")
                        f.write(f"- Response: {result.response_text[:100]}...\n\n")
                    else:
                        f.write(f"- Error: {result.error_message}\n\n")

            if failed:
                f.write("## Failed Models Summary\n\n")
                for result in failed:
                    f.write(f"- **{result.model_name}**: {result.error_message}\n")

        print(f"Markdown report saved to: dev-scripts/{md_report_file}")
        print()
        print("=" * 80)
        print("Test completed!")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
