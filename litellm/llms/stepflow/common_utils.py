"""
StepFlow Provider Common Utilities
"""

from litellm.llms.base_llm.chat.transformation import BaseLLMException

# StepFlow API endpoint
API_BASE = "https://api.stepfun.com"
WORKFLOW_ENDPOINT = "/v1/workflows/everraising_model_proxy_full"


class StepFlowError(BaseLLMException):
    """
    Exception raised for StepFlow API errors
    """

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(status_code=status_code, message=message)
