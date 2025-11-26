"""
StepFlow Chat Completion Configuration
"""

import json
import os
import time
import traceback
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

import httpx

from litellm.litellm_core_utils.exception_mapping_utils import exception_type
from litellm.litellm_core_utils.logging_utils import track_llm_api_timing
from litellm.llms.base_llm.chat.transformation import BaseConfig, BaseLLMException
from litellm.llms.custom_httpx.http_handler import (
    AsyncHTTPHandler,
    HTTPHandler,
    _get_httpx_client,
    get_async_httpx_client,
    version,
)
from litellm.types.llms.openai import AllMessageValues
from litellm.types.utils import LlmProviders
from litellm.utils import CustomStreamWrapper, ModelResponse, Usage

from ..common_utils import API_BASE, WORKFLOW_ENDPOINT, StepFlowError

if TYPE_CHECKING:
    from litellm.litellm_core_utils.litellm_logging import Logging as _LiteLLMLoggingObj

    LiteLLMLoggingObj = _LiteLLMLoggingObj
else:
    LiteLLMLoggingObj = Any


# 5 minute timeout for streaming (models may need to load)
STREAMING_TIMEOUT = 60 * 5


class StepFlowChatConfig(BaseConfig):
    """
    Configuration class for StepFlow's workflow-based API interface.

    StepFlow is an LLM gateway that proxies requests to various providers
    (OpenAI, Anthropic, Gemini, etc.) through a workflow-based API.
    """

    def __init__(self) -> None:
        locals_ = locals().copy()
        for key, value in locals_.items():
            if key != "self" and value is not None:
                setattr(self.__class__, key, value)

        # Mark the class as using a custom stream wrapper
        setattr(self.__class__, "has_custom_stream_wrapper", True)

        # Parameter mapping - most OpenAI params are passed through
        self.openai_to_stepflow_param_map = {
            "stream": "stream",  # Streaming IS supported
            "max_tokens": "max_tokens",
            "max_completion_tokens": "max_tokens",
            "temperature": "temperature",
            "top_p": "top_p",
            "n": "n",
            "stop": "stop",
            "presence_penalty": "presence_penalty",
            "frequency_penalty": "frequency_penalty",
            "logit_bias": "logit_bias",
            "logprobs": "logprobs",
            "top_logprobs": "top_logprobs",
            "seed": "seed",
            "tools": "tools",
            "tool_choice": "tool_choice",
            "function_call": "function_call",
            "functions": "functions",
            "response_format": "response_format",
            "max_retries": False,
            "extra_headers": False,
            "parallel_tool_calls": "parallel_tool_calls",
            "audio": False,
            "modalities": False,
            "prediction": False,
            "stream_options": False,
            "web_search_options": False,
        }

    def get_supported_openai_params(self, model: str) -> List[str]:
        """Get list of supported OpenAI parameters"""
        supported_params = []
        for key, value in self.openai_to_stepflow_param_map.items():
            if value:
                supported_params.append(key)
        return supported_params

    def map_openai_params(
        self,
        non_default_params: dict,
        optional_params: dict,
        model: str,
        drop_params: bool,
    ) -> dict:
        """Map OpenAI parameters to StepFlow format"""
        adapted_params = {}
        all_params = {**non_default_params, **optional_params}

        for key, value in all_params.items():
            alias = self.openai_to_stepflow_param_map.get(key)

            if alias is False:
                if drop_params:
                    continue
                raise Exception(f"param `{key}` is not supported on StepFlow")

            if alias is None:
                adapted_params[key] = value
                continue

            adapted_params[alias] = value

        return adapted_params

    def validate_environment(
        self,
        headers: dict,
        model: str,
        messages: List[AllMessageValues],
        optional_params: dict,
        litellm_params: dict,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
    ) -> dict:
        """Validate environment and setup headers"""

        # Get StepFlow bearer token
        # Priority: api_key parameter > STEPFLOW_API_KEY > FLOW_EXTERNAL_TOKEN
        bearer_token = api_key or os.getenv("STEPFLOW_API_KEY") or os.getenv("FLOW_EXTERNAL_TOKEN")

        if not bearer_token:
            raise Exception(
                "Missing StepFlow API key. Provide via api_key parameter, "
                "STEPFLOW_API_KEY or FLOW_EXTERNAL_TOKEN environment variable."
            )

        headers.update({
            "content-type": "application/json",
            "Authorization": f"Bearer {bearer_token}",
            "user-agent": f"litellm/{version}",
        })

        if not messages:
            raise Exception(
                "kwarg `messages` must be an array of messages that follow the openai chat standard"
            )

        return headers

    def get_complete_url(
        self,
        api_base: Optional[str],
        api_key: Optional[str],
        model: str,
        optional_params: dict,
        litellm_params: dict,
        stream: Optional[bool] = None,
    ) -> str:
        """Get the complete API URL"""
        base = api_base or API_BASE
        complete_url = f"{base}{WORKFLOW_ENDPOINT}"

        # Debug logging
        import sys
        print(f"\n[STEPFLOW DEBUG] get_complete_url called:", file=sys.stderr)
        print(f"  - api_base param: {api_base}", file=sys.stderr)
        print(f"  - API_BASE default: {API_BASE}", file=sys.stderr)
        print(f"  - Using base: {base}", file=sys.stderr)
        print(f"  - WORKFLOW_ENDPOINT: {WORKFLOW_ENDPOINT}", file=sys.stderr)
        print(f"  - Final URL: {complete_url}\n", file=sys.stderr)

        return complete_url

    def transform_request(
        self,
        model: str,
        messages: List[AllMessageValues],
        optional_params: dict,
        litellm_params: dict,
        headers: dict,
    ) -> dict:
        """
        Transform OpenAI-style request into StepFlow workflow format

        StepFlow expects:
        {
            "input": {
                "endpoint": "chat_completions",
                "api_key": "<model_proxy_api_key>",
                "model": "<actual_model_name>",
                "request_body": {<openai_format>}
            }
        }
        """
        import sys
        print(f"\n[STEPFLOW DEBUG] transform_request called:", file=sys.stderr)
        print(f"  - Original model: {model}", file=sys.stderr)

        # Strip "stepflow/" prefix from model name
        actual_model = model.replace("stepflow/", "")
        print(f"  - Actual model (after strip): {actual_model}", file=sys.stderr)

        # Get model proxy API key (for the inner provider)
        model_proxy_api_key = optional_params.pop("model_proxy_api_key", None) or os.getenv("MODEL_PROXY_API_KEY", "")
        print(f"  - Model proxy API key: {'***' if model_proxy_api_key else 'None'}", file=sys.stderr)

        # Check if streaming is requested
        stream = optional_params.get("stream", False)
        print(f"  - Stream requested: {stream}", file=sys.stderr)

        # Build OpenAI-compatible request body
        request_body = {
            "model": actual_model,
            "messages": messages,
            **optional_params,
        }

        # Wrap in StepFlow workflow format
        data = {
            "input": {
                "endpoint": "chat_completions",
                "api_key": model_proxy_api_key,
                "model": actual_model,
                "request_body": request_body,
            }
        }

        print(f"  - Request data structure:", file=sys.stderr)
        print(f"    endpoint: {data['input']['endpoint']}", file=sys.stderr)
        print(f"    model: {data['input']['model']}", file=sys.stderr)
        print(f"    messages count: {len(messages)}", file=sys.stderr)
        print(f"    stream: {stream}\n", file=sys.stderr)

        return data

    def transform_response(
        self,
        model: str,
        raw_response: httpx.Response,
        model_response: ModelResponse,
        logging_obj: LiteLLMLoggingObj,
        request_data: dict,
        messages: List[AllMessageValues],
        optional_params: dict,
        litellm_params: dict,
        encoding: Any,
        api_key: Optional[str] = None,
        json_mode: Optional[bool] = None,
    ) -> ModelResponse:
        """
        Transform StepFlow workflow response into OpenAI-compatible format

        StepFlow returns:
        {
            "code": 0,
            "msg": "success",
            "data": {
                "result": {
                    "success": true,
                    "response": {<openai_format>},
                    "model": "..."
                }
            }
        }
        """
        json_response = raw_response.json()

        # Check workflow execution status
        if json_response.get("code") != 0:
            error_msg = json_response.get("msg", "Unknown workflow error")
            raise StepFlowError(
                status_code=raw_response.status_code,
                message=f"StepFlow workflow execution failed: {error_msg}"
            )

        # Extract workflow result
        workflow_result = json_response.get("data", {}).get("result", {})

        # Check LLM request success
        if not workflow_result.get("success", True):
            error_msg = workflow_result.get("error", "Unknown LLM error")
            raise StepFlowError(
                status_code=raw_response.status_code,
                message=f"StepFlow LLM request failed: {error_msg}"
            )

        # Get the actual LLM response (OpenAI format)
        llm_response = workflow_result.get("response", {})

        # Map to ModelResponse
        model_response.model = model
        model_response.created = llm_response.get("created", int(time.time()))

        # Extract choices
        choices = llm_response.get("choices", [])
        if choices:
            first_choice = choices[0]
            message = model_response.choices[0].message
            message.content = first_choice.get("message", {}).get("content", "")
            message.role = first_choice.get("message", {}).get("role", "assistant")

            # Handle tool calls if present
            tool_calls = first_choice.get("message", {}).get("tool_calls")
            if tool_calls:
                message.tool_calls = tool_calls

            # Set finish reason
            model_response.choices[0].finish_reason = first_choice.get("finish_reason", "stop")

        # Extract usage
        usage_data = llm_response.get("usage", {})
        model_response.usage = Usage(
            prompt_tokens=usage_data.get("prompt_tokens", 0),
            completion_tokens=usage_data.get("completion_tokens", 0),
            total_tokens=usage_data.get("total_tokens", 0),
        )

        # Store additional headers
        model_response._hidden_params["additional_headers"] = raw_response.headers

        return model_response

    def get_error_class(
        self, error_message: str, status_code: int, headers: Union[dict, httpx.Headers]
    ) -> BaseLLMException:
        """Return appropriate error class for StepFlow errors"""
        return StepFlowError(status_code=status_code, message=error_message)

    @track_llm_api_timing()
    def get_sync_custom_stream_wrapper(
        self,
        model: str,
        custom_llm_provider: str,
        logging_obj: LiteLLMLoggingObj,
        api_base: str,
        headers: dict,
        data: dict,
        messages: list,
        client: Optional[Union[HTTPHandler, AsyncHTTPHandler]] = None,
        json_mode: Optional[bool] = None,
        signed_json_body: Optional[bytes] = None,
    ) -> "StepFlowCustomStreamWrapper":
        """
        Create a custom stream wrapper for StepFlow streaming responses (sync version).

        StepFlow returns SSE (Server-Sent Events) format with JSON chunks.
        """
        if client is None or isinstance(client, AsyncHTTPHandler):
            client = _get_httpx_client(params={})

        import sys
        print(f"\n[STEPFLOW DEBUG] Starting streaming request (sync)", file=sys.stderr)
        print(f"  - API base: {api_base}", file=sys.stderr)
        print(f"  - Model: {model}\n", file=sys.stderr)

        try:
            response = client.post(
                api_base,
                headers=headers,
                data=json.dumps(data),
                stream=True,
                logging_obj=logging_obj,
                timeout=STREAMING_TIMEOUT,
            )
        except httpx.HTTPStatusError as e:
            raise StepFlowError(
                status_code=e.response.status_code, message=e.response.text
            )

        if response.status_code != 200:
            raise StepFlowError(status_code=response.status_code, message=response.text)

        # Get the line iterator for SSE
        completion_stream = response.iter_lines()

        streaming_response = StepFlowCustomStreamWrapper(
            completion_stream=completion_stream,
            model=model,
            custom_llm_provider=custom_llm_provider,
            logging_obj=logging_obj,
        )
        return streaming_response

    @track_llm_api_timing()
    async def get_async_custom_stream_wrapper(
        self,
        model: str,
        custom_llm_provider: str,
        logging_obj: LiteLLMLoggingObj,
        api_base: str,
        headers: dict,
        data: dict,
        messages: list,
        client: Optional[Union[HTTPHandler, AsyncHTTPHandler]] = None,
        json_mode: Optional[bool] = None,
        signed_json_body: Optional[bytes] = None,
    ) -> "StepFlowCustomStreamWrapper":
        """
        Create a custom stream wrapper for StepFlow streaming responses.

        StepFlow returns SSE (Server-Sent Events) format with JSON chunks.
        """
        if client is None or isinstance(client, HTTPHandler):
            client = get_async_httpx_client(
                llm_provider=LlmProviders.STEPFLOW, params={}
            )

        import sys
        print(f"\n[STEPFLOW DEBUG] Starting streaming request", file=sys.stderr)
        print(f"  - API base: {api_base}", file=sys.stderr)
        print(f"  - Model: {model}\n", file=sys.stderr)

        try:
            response = await client.post(
                api_base,
                headers=headers,
                data=json.dumps(data),
                stream=True,
                logging_obj=logging_obj,
                timeout=STREAMING_TIMEOUT,
            )
        except httpx.HTTPStatusError as e:
            raise StepFlowError(
                status_code=e.response.status_code, message=e.response.text
            )

        if response.status_code != 200:
            raise StepFlowError(status_code=response.status_code, message=response.text)

        # Get the async line iterator for SSE
        completion_stream = response.aiter_lines()

        streaming_response = StepFlowCustomStreamWrapper(
            completion_stream=completion_stream,
            model=model,
            custom_llm_provider=custom_llm_provider,
            logging_obj=logging_obj,
        )
        return streaming_response


class StepFlowCustomStreamWrapper(CustomStreamWrapper):
    """
    Custom stream wrapper for StepFlow streaming responses.

    StepFlow workflow returns SSE chunks where result.response may contain:
    1. A string with the complete SSE stream (non-ideal, buffered workflow response)
    2. Individual parsed OpenAI chunks (ideal, true streaming)
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._content_emitted = False  # Track if we've already emitted the buffered content

    def chunk_creator(self, chunk: str):
        """
        Process each SSE chunk from StepFlow workflow.
        """
        try:
            import sys

            # Debug: Show raw chunk (limited output)
            if chunk and len(chunk) > 10:
                print(f"[STEPFLOW DEBUG] Raw chunk prefix: {repr(chunk[:50])}", file=sys.stderr)

            # Handle empty lines or non-data lines
            if not chunk or not chunk.strip():
                return None

            # Skip event lines (event:keepalive, event:message, etc.)
            if chunk.startswith("event:"):
                return None

            # SSE format: lines starting with "data:" contain JSON
            if not chunk.startswith("data:"):
                return None

            # Remove "data:" prefix
            json_str = chunk[5:].strip()

            # Handle [DONE] message
            if json_str == "[DONE]":
                print(f"[STEPFLOW DEBUG] Received [DONE]", file=sys.stderr)
                return None

            # Handle empty data lines
            if not json_str:
                return None

            # Parse the workflow response
            try:
                workflow_response = json.loads(json_str)
                print(f"[STEPFLOW DEBUG] Parsed keys: {list(workflow_response.keys())}", file=sys.stderr)
            except json.JSONDecodeError as e:
                print(f"[STEPFLOW DEBUG] JSON parse error: {str(e)}", file=sys.stderr)
                return None

            # StepFlow streaming format has result directly
            result = workflow_response.get("result", {})
            if not result:
                return None

            # The workflow response contains the response in result.response
            response_data = result.get("response")
            if not response_data:
                return None

            # Check if response_data is a string (buffered SSE stream) or dict (individual chunk)
            if isinstance(response_data, str):
                # Skip if we've already emitted the buffered content
                if self._content_emitted:
                    print(f"[STEPFLOW DEBUG] Skipping duplicate buffered response", file=sys.stderr)
                    return None

                # The workflow buffered the entire SSE stream
                # We need to parse it and extract the final result to return something
                print(f"[STEPFLOW DEBUG] Parsing buffered SSE stream", file=sys.stderr)
                print(f"[STEPFLOW DEBUG] Response length: {len(response_data)} chars", file=sys.stderr)

                # Parse the SSE stream to extract all content
                lines = response_data.split('\n')
                full_content = []
                final_usage = None
                finish_reason = None

                for line in lines:
                    if line.startswith('data:'):
                        json_str = line[5:].strip()
                        if json_str == '[DONE]':
                            finish_reason = 'stop'
                            continue
                        if not json_str:
                            continue

                        try:
                            chunk_data = json.loads(json_str)
                            choices = chunk_data.get('choices', [])
                            if choices:
                                first_choice = choices[0]
                                # Try delta first (streaming chunks)
                                delta = first_choice.get('delta', {})
                                content = delta.get('content', '')
                                if content:
                                    full_content.append(content)

                                # Check for finish reason
                                chunk_finish = first_choice.get('finish_reason')
                                if chunk_finish:
                                    finish_reason = chunk_finish

                            # Extract usage from the chunk
                            usage = chunk_data.get('usage', {})
                            if usage and usage.get('total_tokens', 0) > 0:
                                final_usage = usage

                        except json.JSONDecodeError:
                            continue

                # Now emit a single chunk with all the content
                if full_content or finish_reason:
                    print(f"[STEPFLOW DEBUG] Emitting buffered content: {len(''.join(full_content))} chars", file=sys.stderr)

                    # Mark that we've emitted the content
                    self._content_emitted = True

                    model_response = self.model_response_creator()

                    complete_text = ''.join(full_content)
                    response_obj = {
                        "text": complete_text,
                        "is_finished": finish_reason is not None,
                        "finish_reason": finish_reason or "",
                    }

                    completion_obj: Dict[str, Any] = {"content": complete_text}

                    # Add usage if we found it
                    if final_usage:
                        from litellm.types.utils import Usage
                        model_response.usage = Usage(
                            prompt_tokens=final_usage.get("prompt_tokens", 0),
                            completion_tokens=final_usage.get("completion_tokens", 0),
                            total_tokens=final_usage.get("total_tokens", 0),
                        )
                        print(f"[STEPFLOW DEBUG] Usage: {final_usage}", file=sys.stderr)

                    return self.return_processed_chunk_logic(
                        completion_obj=completion_obj,
                        model_response=model_response,  # type: ignore
                        response_obj=response_obj,
                    )

                return None

            # Now response_data should be a dict with the OpenAI chunk format
            if not isinstance(response_data, dict):
                print(f"[STEPFLOW DEBUG] Response data is not a dict: {type(response_data)}", file=sys.stderr)
                return None

            # Check if it's a streaming chunk (has delta) or final response (has message)
            choices = response_data.get("choices", [])
            if not choices:
                return None

            first_choice = choices[0]

            # Try to get delta first (streaming), fall back to message (final)
            delta = first_choice.get("delta")
            if delta is None:
                # This is the final complete message, not a streaming chunk
                # For streaming we want delta, not message
                message = first_choice.get("message", {})
                content = message.get("content", "")
                finish_reason = first_choice.get("finish_reason")

                # If this is the final message with finish_reason, return it
                if finish_reason:
                    print(f"[STEPFLOW DEBUG] Final message with finish: {finish_reason}", file=sys.stderr)
                    model_response = self.model_response_creator()
                    response_obj = {
                        "text": "",
                        "is_finished": True,
                        "finish_reason": finish_reason,
                    }
                    completion_obj: Dict[str, Any] = {"content": ""}
                    return self.return_processed_chunk_logic(
                        completion_obj=completion_obj,
                        model_response=model_response,  # type: ignore
                        response_obj=response_obj,
                    )
                return None

            content = delta.get("content", "")
            finish_reason = first_choice.get("finish_reason")

            if content or finish_reason:
                print(f"[STEPFLOW DEBUG] Delta content: {repr(content[:50])}, finish: {finish_reason}", file=sys.stderr)

            # Create response object
            model_response = self.model_response_creator()
            response_obj = {
                "text": content,
                "is_finished": finish_reason is not None,
                "finish_reason": finish_reason or "",
            }

            completion_obj: Dict[str, Any] = {"content": content}

            # Add tool calls if present
            if "tool_calls" in delta:
                completion_obj["tool_calls"] = delta["tool_calls"]

            # Extract usage information from the chunk (usually in the last chunk)
            usage_data = response_data.get("usage")
            if usage_data and isinstance(usage_data, dict):
                # Check if this has actual token counts (not all zeros)
                if (usage_data.get("total_tokens", 0) > 0 or
                    usage_data.get("prompt_tokens", 0) > 0 or
                    usage_data.get("completion_tokens", 0) > 0):
                    print(f"[STEPFLOW DEBUG] Found usage: {usage_data}", file=sys.stderr)
                    from litellm.types.utils import Usage

                    # Extract token details if present
                    prompt_tokens_details = usage_data.get("prompt_tokens_details")
                    completion_tokens_details = usage_data.get("completion_tokens_details")

                    model_response.usage = Usage(
                        prompt_tokens=usage_data.get("prompt_tokens", 0),
                        completion_tokens=usage_data.get("completion_tokens", 0),
                        total_tokens=usage_data.get("total_tokens", 0),
                        prompt_tokens_details=prompt_tokens_details,
                        completion_tokens_details=completion_tokens_details,
                    )

            return self.return_processed_chunk_logic(
                completion_obj=completion_obj,
                model_response=model_response,  # type: ignore
                response_obj=response_obj,
            )

        except StopIteration:
            raise StopIteration
        except Exception as e:
            import traceback
            traceback.print_exc()
            setattr(e, "message", str(e))
            raise exception_type(
                model=self.model,
                custom_llm_provider=self.custom_llm_provider,
                original_exception=e,
            )
