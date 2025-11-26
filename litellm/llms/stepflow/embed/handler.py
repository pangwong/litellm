"""
StepFlow Embeddings Handler
"""

import os
from typing import Any, List, Optional, Union

import httpx

from litellm.llms.custom_httpx.http_handler import (
    AsyncHTTPHandler,
    HTTPHandler,
    _get_httpx_client,
    get_async_httpx_client,
)
from litellm.types.utils import Embedding, EmbeddingResponse, LlmProviders, Usage

from ..common_utils import API_BASE, WORKFLOW_ENDPOINT, StepFlowError


class StepFlowEmbedding:
    """
    Handler for StepFlow embeddings via workflow API
    """

    def _make_sync_call(
        self,
        client: Optional[HTTPHandler],
        timeout: Optional[Union[float, httpx.Timeout]],
        api_base: str,
        headers: dict,
        data: dict,
    ) -> dict:
        """Make synchronous HTTP call to StepFlow API"""
        if client is None or not isinstance(client, HTTPHandler):
            _params = {}
            if timeout is not None:
                if isinstance(timeout, float) or isinstance(timeout, int):
                    timeout = httpx.Timeout(timeout)
                _params["timeout"] = timeout
            client = _get_httpx_client(_params)

        try:
            response = client.post(url=api_base, headers=headers, json=data)
            response.raise_for_status()
        except httpx.HTTPStatusError as err:
            error_code = err.response.status_code
            raise StepFlowError(status_code=error_code, message=err.response.text)
        except httpx.TimeoutException:
            raise StepFlowError(status_code=408, message="Timeout error occurred.")

        return response.json()

    async def _make_async_call(
        self,
        client: Optional[AsyncHTTPHandler],
        timeout: Optional[Union[float, httpx.Timeout]],
        api_base: str,
        headers: dict,
        data: dict,
    ) -> dict:
        """Make asynchronous HTTP call to StepFlow API"""
        if client is None or not isinstance(client, AsyncHTTPHandler):
            _params = {}
            if timeout is not None:
                if isinstance(timeout, float) or isinstance(timeout, int):
                    timeout = httpx.Timeout(timeout)
                _params["timeout"] = timeout
            client = get_async_httpx_client(
                params=_params, llm_provider=LlmProviders.OPENAI
            )

        try:
            response = await client.post(url=api_base, headers=headers, json=data)
            response.raise_for_status()
        except httpx.HTTPStatusError as err:
            error_code = err.response.status_code
            raise StepFlowError(status_code=error_code, message=err.response.text)
        except httpx.TimeoutException:
            raise StepFlowError(status_code=408, message="Timeout error occurred.")

        return response.json()

    def _transform_response(
        self,
        workflow_response: dict,
        model: str,
    ) -> EmbeddingResponse:
        """
        Transform StepFlow workflow response into OpenAI-compatible format

        StepFlow returns:
        {
            "code": 0,
            "msg": "success",
            "data": {
                "result": {
                    "success": true,
                    "response": {<openai_format_embedding_response>},
                    "model": "..."
                }
            }
        }
        """
        # Check workflow execution status
        if workflow_response.get("code") != 0:
            error_msg = workflow_response.get("msg", "Unknown workflow error")
            raise StepFlowError(
                status_code=500,
                message=f"StepFlow workflow execution failed: {error_msg}"
            )

        # Extract workflow result
        workflow_result = workflow_response.get("data", {}).get("result", {})

        # Check LLM request success
        if not workflow_result.get("success", True):
            error_msg = workflow_result.get("error", "Unknown embedding error")
            raise StepFlowError(
                status_code=500,
                message=f"StepFlow embedding request failed: {error_msg}"
            )

        # Get the actual embedding response (OpenAI format)
        embedding_response = workflow_result.get("response", {})

        # Extract embeddings data
        data_list = embedding_response.get("data", [])
        embeddings = []
        for item in data_list:
            embedding = Embedding(
                embedding=item.get("embedding", []),
                index=item.get("index", 0),
                object="embedding",
            )
            embeddings.append(embedding)

        # Extract usage
        usage_data = embedding_response.get("usage", {})
        usage = Usage(
            prompt_tokens=usage_data.get("prompt_tokens", 0),
            completion_tokens=usage_data.get("completion_tokens", 0),
            total_tokens=usage_data.get("total_tokens", 0),
        )

        # Build response
        response = EmbeddingResponse(
            model=model,
            data=embeddings,
            usage=usage,
        )

        return response

    def embedding(
        self,
        model: str,
        input: Union[str, List[str]],
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        timeout: Optional[Union[float, httpx.Timeout]] = None,
        logging_obj: Any = None,
        model_response: Optional[EmbeddingResponse] = None,
        optional_params: Optional[dict] = None,
        client: Optional[Union[HTTPHandler, AsyncHTTPHandler]] = None,
        aembedding: bool = False,
        litellm_params: Optional[dict] = None,
        **kwargs,
    ):
        """
        Create embeddings via StepFlow workflow API

        Args:
            model: Model name with "stepflow/" prefix
            input: Text or list of texts to embed
            api_key: StepFlow bearer token
            api_base: API base URL (default: https://api.stepfun.com)
            timeout: Request timeout
            optional_params: Additional parameters
            client: HTTP client instance
            aembedding: Whether to return async coroutine
            litellm_params: LiteLLM parameters
        """
        optional_params = optional_params or {}

        # Get StepFlow bearer token
        bearer_token = api_key or os.getenv("STEPFLOW_API_KEY") or os.getenv("FLOW_EXTERNAL_TOKEN")
        if not bearer_token:
            raise ValueError(
                "Missing StepFlow API key. Provide via api_key parameter, "
                "STEPFLOW_API_KEY or FLOW_EXTERNAL_TOKEN environment variable."
            )

        # Setup headers
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {bearer_token}",
        }

        # Get API base
        base_url = api_base or API_BASE
        api_url = f"{base_url}{WORKFLOW_ENDPOINT}"

        # Strip "stepflow/" prefix from model name
        actual_model = model.replace("stepflow/", "")

        # Get model proxy API key (for the inner provider)
        model_proxy_api_key = optional_params.pop("model_proxy_api_key", None) or os.getenv("MODEL_PROXY_API_KEY", "")

        # Build OpenAI-compatible request body
        request_body = {
            "model": actual_model,
            "input": input,
            **optional_params,
        }

        # Wrap in StepFlow workflow format
        data = {
            "input": {
                "endpoint": "embeddings",
                "api_key": model_proxy_api_key,
                "model": actual_model,
                "request_body": request_body,
            }
        }

        # Make the API call
        if aembedding:
            return self._async_embedding(
                client=client,
                timeout=timeout,
                api_base=api_url,
                headers=headers,
                data=data,
                model=model,
            )
        else:
            workflow_response = self._make_sync_call(
                client=client,
                timeout=timeout,
                api_base=api_url,
                headers=headers,
                data=data,
            )

            # Transform and return response
            return self._transform_response(
                workflow_response=workflow_response,
                model=model,
            )

    async def _async_embedding(
        self,
        client: Optional[AsyncHTTPHandler],
        timeout: Optional[Union[float, httpx.Timeout]],
        api_base: str,
        headers: dict,
        data: dict,
        model: str,
    ) -> EmbeddingResponse:
        """Async version of embedding"""
        workflow_response = await self._make_async_call(
            client=client,
            timeout=timeout,
            api_base=api_base,
            headers=headers,
            data=data,
        )

        # Transform and return response
        return self._transform_response(
            workflow_response=workflow_response,
            model=model,
        )


# Create singleton instance
stepflow_embedding = StepFlowEmbedding()
