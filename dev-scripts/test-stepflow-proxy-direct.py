#!/usr/bin/env python3
"""
Direct Test Client for StepFlow Proxy Service

This script tests the stepflow-proxy.py workflow directly by calling the Flow API,
bypassing LiteLLM entirely. It tests both streaming and non-streaming modes.

Usage:
    python test-stepflow-proxy-direct.py
    python test-stepflow-proxy-direct.py --stream
    python test-stepflow-proxy-direct.py --model gpt-4o-mini
"""

import os
import sys
import json
import argparse
import requests
from typing import Dict, Any
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Colors for output
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color


def load_env_file(env_path: str = "dev-scripts/.env") -> Dict[str, str]:
    """Load environment variables from .env file"""
    env_vars = {}
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key] = value
    return env_vars


def test_non_streaming(
    access_token: str,
    workflow_id: str,
    model_proxy_api_key: str,
    model: str,
    base_url: str
):
    """Test non-streaming mode"""
    print(f"\n{BLUE}{'='*60}{NC}")
    print(f"{BLUE}Testing Non-Streaming Mode{NC}")
    print(f"{BLUE}{'='*60}{NC}\n")

    # Prepare the request
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "workflow_id": workflow_id,
        "data": {
            "endpoint": "chat_completions",
            "api_key": model_proxy_api_key,
            "request_body": {
                "model": model,
                "messages": [
                    {"role": "user", "content": "Write a haiku about coding"}
                ],
                "temperature": 0.7,
                "max_tokens": 100,
                "stream": False  # ← Non-streaming
            }
        }
    }

    print(f"Request details:")
    print(f"  - Model: {model}")
    print(f"  - Stream: False")
    print(f"  - Endpoint: {base_url}/openapi/v1/workflow/call")
    print(f"  - Workflow ID: {workflow_id}\n")

    try:
        print(f"{YELLOW}Sending request...{NC}\n")

        response = requests.post(
            f"{base_url}/openapi/v1/workflow/call",
            headers=headers,
            json=payload,
            timeout=120
        )

        print(f"Response status: {response.status_code}\n")

        if response.status_code != 200:
            print(f"{RED}✗ FAILED: HTTP {response.status_code}{NC}")
            print(f"Response: {response.text[:500]}")
            return False

        result = response.json()

        # Check workflow execution status
        if result.get("code") != 0:
            error_msg = result.get("msg", "Unknown workflow error")
            print(f"{RED}✗ FAILED: Workflow execution error{NC}")
            print(f"Error: {error_msg}")
            return False

        # Check proxy result
        proxy_result = result["data"]["result"]

        if not proxy_result.get("success"):
            error_msg = proxy_result.get("error", "Unknown error")
            print(f"{RED}✗ FAILED: Proxy request error{NC}")
            print(f"Error: {error_msg}")
            return False

        # Extract and display the response
        print(f"{GREEN}✓ SUCCESS!{NC}\n")

        print(f"Workflow response structure:")
        print(f"  - success: {proxy_result.get('success')}")
        print(f"  - model: {proxy_result.get('model')}")
        print(f"  - error: {proxy_result.get('error')}\n")

        # Extract the actual LLM response
        llm_response = proxy_result.get("response", {})

        if isinstance(llm_response, dict):
            choices = llm_response.get("choices", [])
            if choices:
                content = choices[0].get("message", {}).get("content", "")
                print(f"LLM Response:")
                print(f"  {content}\n")

                usage = llm_response.get("usage", {})
                if usage:
                    print(f"Token Usage:")
                    print(f"  - Prompt tokens: {usage.get('prompt_tokens', 0)}")
                    print(f"  - Completion tokens: {usage.get('completion_tokens', 0)}")
                    print(f"  - Total tokens: {usage.get('total_tokens', 0)}\n")
            else:
                print(f"LLM Response (full): {json.dumps(llm_response, indent=2)}\n")
        else:
            print(f"LLM Response: {llm_response}\n")

        return True

    except requests.exceptions.Timeout:
        print(f"{RED}✗ FAILED: Request timeout{NC}")
        return False
    except Exception as e:
        print(f"{RED}✗ FAILED: {type(e).__name__}: {e}{NC}")
        import traceback
        traceback.print_exc()
        return False


def test_streaming(
    access_token: str,
    workflow_id: str,
    model_proxy_api_key: str,
    model: str,
    base_url: str
):
    """Test streaming mode with real-time token display"""
    print(f"\n{BLUE}{'='*60}{NC}")
    print(f"{BLUE}Testing Streaming Mode (Real-Time){NC}")
    print(f"{BLUE}{'='*60}{NC}\n")

    # Prepare the request
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "workflow_id": workflow_id,
        "data": {
            "endpoint": "chat_completions",
            "api_key": model_proxy_api_key,
            "request_body": {
                "model": model,
                "messages": [
                    {"role": "user", "content": "Write a haiku about coding"}
                ],
                "temperature": 0.7,
                "max_tokens": 100,
                "stream": True  # ← Streaming
            }
        }
    }

    print(f"Request details:")
    print(f"  - Model: {model}")
    print(f"  - Stream: True")
    print(f"  - Endpoint: {base_url}/openapi/v1/workflow/call")
    print(f"  - Workflow ID: {workflow_id}\n")

    try:
        print(f"{YELLOW}Sending streaming request...{NC}\n")

        response = requests.post(
            f"{base_url}/openapi/v1/workflow/call",
            headers=headers,
            json=payload,
            timeout=120
        )

        print(f"Response status: {response.status_code}\n")

        if response.status_code != 200:
            print(f"{RED}✗ FAILED: HTTP {response.status_code}{NC}")
            print(f"Response: {response.text[:500]}")
            return False

        result = response.json()

        # Check workflow execution status
        if result.get("code") != 0:
            error_msg = result.get("msg", "Unknown workflow error")
            print(f"{RED}✗ FAILED: Workflow execution error{NC}")
            print(f"Error: {error_msg}")
            return False

        # Check proxy result
        proxy_result = result["data"]["result"]

        if not proxy_result.get("success"):
            error_msg = proxy_result.get("error", "Unknown error")
            print(f"{RED}✗ FAILED: Proxy request error{NC}")
            print(f"Error: {error_msg}")
            return False

        # For streaming, the response should be raw SSE text
        print(f"{GREEN}✓ SUCCESS!{NC}\n")

        print(f"Workflow response structure:")
        print(f"  - success: {proxy_result.get('success')}")
        print(f"  - model: {proxy_result.get('model')}")
        print(f"  - error: {proxy_result.get('error')}\n")

        # Extract the SSE stream response
        sse_response = proxy_result.get("response", "")

        print(f"SSE Stream Response (Real-Time Display):")
        print(f"{'-'*60}")
        print(f"{YELLOW}[Streaming tokens as they arrive...]{NC}\n")

        if isinstance(sse_response, str):
            # Parse and display SSE chunks in real-time
            lines = sse_response.split('\n')
            chunk_count = 0
            full_content = []
            usage_info = None
            import time

            for line in lines:
                if line.startswith('data:'):
                    chunk_count += 1
                    json_str = line[5:].strip()  # Remove 'data:' prefix

                    if json_str == '[DONE]':
                        print(f"\n\n{YELLOW}[DONE]{NC}")
                        continue

                    try:
                        chunk_data = json.loads(json_str)

                        # Check for usage information in this chunk
                        chunk_usage = chunk_data.get("usage", {})
                        if chunk_usage and chunk_usage.get("total_tokens", 0) > 0:
                            usage_info = chunk_usage

                        # Extract delta content
                        choices = chunk_data.get("choices", [])
                        if choices:
                            delta = choices[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                full_content.append(content)
                                # Print token immediately with flush and small delay to simulate streaming
                                print(f"{GREEN}{content}{NC}", end='', flush=True)
                                time.sleep(0.05)  # Small delay to make streaming visible
                    except json.JSONDecodeError:
                        # Show first chunk as example
                        if chunk_count == 1:
                            print(f"Example chunk: {json_str[:100]}...")

            print(f"\n{'-'*60}")
            print(f"\nStreaming stats:")
            print(f"  - Total chunks received: {chunk_count}")
            print(f"  - Content tokens received: {len(full_content)}")
            print(f"  - Full content assembled: {''.join(full_content)}")

            # Display token usage if found
            if usage_info:
                print(f"\nToken Usage:")
                print(f"  - Prompt tokens: {usage_info.get('prompt_tokens', 0)}")
                print(f"  - Completion tokens: {usage_info.get('completion_tokens', 0)}")
                print(f"  - Total tokens: {usage_info.get('total_tokens', 0)}")

                # Show detailed breakdown if available
                completion_details = usage_info.get('completion_tokens_details', {})
                if completion_details:
                    reasoning = completion_details.get('reasoning_tokens', 0)
                    if reasoning > 0:
                        print(f"  - Reasoning tokens: {reasoning}")

                prompt_details = usage_info.get('prompt_tokens_details', {})
                if prompt_details:
                    cached = prompt_details.get('cached_tokens', 0)
                    if cached > 0:
                        print(f"  - Cached tokens: {cached}")
            else:
                print(f"\n{YELLOW}⚠ No token usage information found in stream{NC}")

            print()
        else:
            # If response is not string, show it as-is
            print(f"Response: {sse_response}\n")

        return True

    except requests.exceptions.Timeout:
        print(f"{RED}✗ FAILED: Request timeout{NC}")
        return False
    except Exception as e:
        print(f"{RED}✗ FAILED: {type(e).__name__}: {e}{NC}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(description='Test StepFlow proxy service directly')
    parser.add_argument('--stream', action='store_true', help='Test streaming mode')
    parser.add_argument('--non-stream', action='store_true', help='Test non-streaming mode')
    parser.add_argument('--model', default='gpt-4o', help='Model name (default: gpt-4o)')
    parser.add_argument('--env-file', default='dev-scripts/.env', help='Path to .env file')
    args = parser.parse_args()

    print(f"\n{BLUE}{'='*60}{NC}")
    print(f"{BLUE}StepFlow Proxy Service Direct Test{NC}")
    print(f"{BLUE}{'='*60}{NC}\n")

    # Load environment variables
    env_vars = load_env_file(args.env_file)

    # Get required credentials
    access_token = env_vars.get('FLOW_ACCESS_TOKEN') or os.getenv('FLOW_ACCESS_TOKEN')
    model_proxy_api_key = env_vars.get('MODEL_PROXY_API_KEY') or os.getenv('MODEL_PROXY_API_KEY')
    workflow_id = env_vars.get('FLOW_WORKFLOW_ID', '1675')
    base_url = env_vars.get('FLOW_BASE_URL', 'https://flow.stepfun-inc.com')

    # Validation
    if not access_token:
        print(f"{RED}Error: FLOW_ACCESS_TOKEN not found in {args.env_file} or environment{NC}")
        sys.exit(1)

    if not model_proxy_api_key:
        print(f"{RED}Error: MODEL_PROXY_API_KEY not found in {args.env_file} or environment{NC}")
        sys.exit(1)

    print(f"Configuration:")
    print(f"  - Model: {args.model}")
    print(f"  - Workflow ID: {workflow_id}")
    print(f"  - Base URL: {base_url}")
    print(f"  - Access Token: {access_token[:20]}...")
    print(f"  - Model Proxy Key: {model_proxy_api_key[:10]}...\n")

    # Determine what to test
    test_both = not args.stream and not args.non_stream

    results = []

    if test_both or args.non_stream:
        success = test_non_streaming(
            access_token=access_token,
            workflow_id=workflow_id,
            model_proxy_api_key=model_proxy_api_key,
            model=args.model,
            base_url=base_url
        )
        results.append(("Non-Streaming", success))

    if test_both or args.stream:
        success = test_streaming(
            access_token=access_token,
            workflow_id=workflow_id,
            model_proxy_api_key=model_proxy_api_key,
            model=args.model,
            base_url=base_url
        )
        results.append(("Streaming", success))

    # Summary
    print(f"\n{BLUE}{'='*60}{NC}")
    print(f"{BLUE}Test Summary{NC}")
    print(f"{BLUE}{'='*60}{NC}\n")

    for test_name, success in results:
        status = f"{GREEN}✓ PASSED{NC}" if success else f"{RED}✗ FAILED{NC}"
        print(f"  {test_name}: {status}")

    all_passed = all(result[1] for result in results)

    print(f"\n{BLUE}{'='*60}{NC}\n")

    if all_passed:
        print(f"{GREEN}All tests passed! 🎉{NC}\n")
        sys.exit(0)
    else:
        print(f"{RED}Some tests failed{NC}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
