import json
from typing import Dict, Any

import promptkit.http as http

# 为清晰起见,将 Output 定义为字典类型
Output = Dict

# ===== 配置区域 - 内部 LLM 服务 URL =====
INTERNAL_BASE_URL = "https://models-proxy.stepfun-inc.com/v1"
# ==============================================


async def main(args: Args) -> Output:
    """
    LLM 代理节点 - 将 OpenAI 兼容的 API 请求转发到内部 LLM 服务

    输入参数 (通过 args.params):
        - endpoint: API 端点 ("chat_completions" 或 "embeddings")
        - api_key: 内部服务的 API 密钥
        - request_body: OpenAI 格式的请求体

    返回:
        包含代理响应的字典
    """
    # 初始化返回结构 - 平台会根据这个结构识别输出字段
    ret: Output = {"success": False, "error": "", "response": None, "model": "", "content": ""}

    try:
        # 1. 从 args.params 提取参数
        endpoint = args.params.get("endpoint", "chat_completions")
        api_key = args.params.get("api_key", "")
        request_body = args.params.get("request_body", {})

        # 2. 验证必需参数
        if not api_key:
            ret["error"] = "api_key 是必需参数"
            return ret

        if not request_body:
            ret["error"] = "request_body 是必需参数"
            return ret

        # 3. 如果 request_body 是字符串,解析为字典
        if isinstance(request_body, str):
            try:
                request_body = json.loads(request_body)
            except json.JSONDecodeError as e:
                ret["error"] = f"request_body 格式无效: {str(e)}"
                return ret

        # 4. 构建目标 URL
        endpoint_map = {"chat_completions": "/chat/completions", "embeddings": "/embeddings"}

        if endpoint not in endpoint_map:
            ret["error"] = f"不支持的端点: {endpoint}"
            return ret

        base_url = INTERNAL_BASE_URL.rstrip("/")
        target_url = f"{base_url}{endpoint_map[endpoint]}"

        # 5. 准备请求头
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

        # 6. Enable or disable streaming based on request
        # Keep the stream parameter from the original request
        stream_enabled = request_body.get("stream", False)

        # 7. Use promptkit.http to send request to internal LLM service
        async with http.fetch("POST", target_url, headers=headers, body=request_body, timeout=300) as response:
            # 8. Handle response
            if response.status != 200:
                error_text = await response.atext()
                ret["error"] = f"Internal service error: HTTP {response.status}, {error_text[:200]}"
                return ret

            # 9. For streaming responses, stream chunks using aiter_lines()
            if stream_enabled:
                # Set initial success state
                ret["success"] = True
                ret["error"] = ""
                ret["model"] = request_body.get("model", "unknown")
                ret["content"] = ""

                # Collect all SSE chunks into a list, then join them
                # The workflow platform will return this as response
                chunks = []
                async for line in response.aiter_lines():
                    if line:
                        chunks.append(line)

                # Join all chunks with newlines to preserve SSE format
                ret["response"] = '\n'.join(chunks)
                return ret

            # 10. For non-streaming, parse JSON and update all fields
            response_json = await response.ajson()

            ret["success"] = True
            ret["error"] = ""
            ret["response"] = response_json
            ret["model"] = response_json.get("model", "unknown")

            # Extract content - support chat completions format
            choices = response_json.get("choices", [])
            if choices:
                message = choices[0].get("message", {})
                ret["content"] = message.get("content", "")
            else:
                ret["content"] = ""

            return ret

    except Exception as e:
        ret["error"] = f"处理失败: {str(e)}"
        return ret
