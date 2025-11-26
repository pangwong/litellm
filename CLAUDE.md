# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Installation
- `make install-dev` - Install core development dependencies
- `make install-proxy-dev` - Install proxy development dependencies with full feature set
- `make install-test-deps` - Install all test dependencies
- `make install-dev-ci` - Install dev dependencies (CI-compatible, pins OpenAI version)
- `make install-proxy-dev-ci` - Install proxy dev dependencies (CI-compatible)

### Testing
- `make test` - Run all tests
- `make test-unit` - Run unit tests (tests/test_litellm) with 4 parallel workers
- `make test-integration` - Run integration tests (excludes unit tests)
- `make test-unit-helm` - Run helm unit tests
- `make test-llm-translation` - Run all LLM provider translation tests
- `make test-llm-translation-single FILE=test_filename.py` - Run specific provider test
- `pytest tests/` - Direct pytest execution
- `poetry run pytest tests/path/to/test_file.py -v` - Run specific test file
- `poetry run pytest tests/path/to/test_file.py::test_function -v` - Run specific test

### Code Quality
- `make lint` - Run all linting (Ruff, MyPy, Black, circular imports, import safety)
- `make format` - Apply Black code formatting
- `make format-check` - Check Black code formatting without modifying (matches CI)
- `make lint-ruff` - Run Ruff linting only
- `make lint-mypy` - Run MyPy type checking only
- `make lint-black` - Check Black formatting (matches CI)
- `make check-circular-imports` - Check for circular imports
- `make check-import-safety` - Check import safety

## Architecture Overview

LiteLLM is a unified interface for 100+ LLM providers with two main components:

### Core Library (`litellm/`)
- **Main entry point**: `litellm/main.py` - Contains core completion() function (6,458 lines)
- **Router system**: `litellm/router.py` (7,753 lines) + `litellm/router_utils/` - Load balancing and fallback logic
- **Provider implementations**: `litellm/llms/` - 98 provider subdirectories, each with their own implementation
- **Base provider classes**: `litellm/llms/base_llm/` - Base classes for chat, completion, embedding, image generation, etc.
- **Type definitions**: `litellm/types/` - Pydantic v2 models and type hints
- **Integrations**: `litellm/integrations/` - 22+ third-party observability, caching, logging integrations
- **Caching**: `litellm/caching/` - Multiple cache backends (Redis, in-memory, S3, Azure Blob, GCS, disk, etc.)
- **Cost calculation**: `litellm/cost_calculator.py` - Token counting and cost tracking
- **Exception handling**: `litellm/exceptions.py` + `litellm/litellm_core_utils/exception_mapping_utils.py` - Provider error mapping to OpenAI format
- **Logging**: `litellm/_logging.py` + `litellm/litellm_core_utils/litellm_logging.py` - Comprehensive logging infrastructure

### Proxy Server (`litellm/proxy/`)
- **Main server**: `proxy_server.py` - FastAPI application
- **Request routing**: `route_llm_request.py` - Core request processing logic
- **Authentication**: `auth/` - API key management, JWT, OAuth2
- **Database**: `db/` - Prisma ORM with PostgreSQL/SQLite support
- **Management endpoints**: `management_endpoints/` - Admin APIs for keys, teams, models, users
- **Pass-through endpoints**: `pass_through_endpoints/` - Provider-specific API forwarding
- **Guardrails**: `guardrails/` - Safety and content filtering hooks
- **Hooks system**: `hooks/` - Custom hooks for request/response processing
- **UI Dashboard**: Served from `_experimental/out/` (Next.js build)

### Router Strategies (`litellm/router_strategy/`)
Available routing algorithms for load balancing:
- `lowest_cost.py` - Minimize API spend
- `lowest_latency.py` - Optimize for speed based on historical latency
- `least_busy.py` - Balance load across deployments
- `lowest_tpm_rpm.py` / `lowest_tpm_rpm_v2.py` - Respect rate limits (tokens/requests per minute)
- `simple_shuffle.py` - Round-robin distribution
- `tag_based_routing.py` - Route by custom tags
- `budget_limiter.py` - Enforce budget constraints

## Key Patterns

### Provider Implementation
Each provider in `litellm/llms/<provider>/` typically has:
- `__init__.py` - Main completion/embedding/image_generation functions
- `transformation.py` - Input/output format transformations to/from OpenAI format
- `common_utils.py` - Provider-specific utilities
- Base classes inherited from `litellm/llms/base_llm/`
- Support for both sync and async operations
- Streaming response handling
- Function calling support where applicable

### Model Name Format
Models use the format `provider/model-name`:
- `openai/gpt-4` - OpenAI GPT-4
- `anthropic/claude-sonnet-4-20250514` - Anthropic Claude
- `azure/gpt-4` - Azure OpenAI
- `bedrock/anthropic.claude-v2` - AWS Bedrock

### Error Handling
- Provider-specific exceptions mapped to OpenAI-compatible errors in `litellm/exceptions.py`
- Standard exception types: `AuthenticationError`, `RateLimitError`, `TimeoutError`, `BadRequestError`, etc.
- Fallback logic handled by Router system with configurable retry strategies
- Comprehensive logging through `litellm/_logging.py` and integration callbacks

### Configuration
- **Proxy server**: YAML config files (see `proxy/example_config_yaml/` for templates)
- **Environment variables**: API keys and settings (e.g., `OPENAI_API_KEY`, `LITELLM_MODE`, `LITELLM_LOG_LEVEL`)
- **Database schema**: Managed via Prisma (`proxy/schema.prisma`)
- **Router config**: Defined in YAML with model_list, routing_strategy, fallback_strategy

### Custom Callbacks & Logging
Use `CustomLogger` interface in `litellm/integrations/custom_logger.py`:
```python
from litellm.integrations.custom_logger import CustomLogger

class MyLogger(CustomLogger):
    def log_pre_api_call(self, model, messages, kwargs): pass
    def log_post_api_call(self, kwargs, response, start_time, end_time): pass
    def log_stream_event(self, kwargs, response, start_time, end_time): pass
    def log_success_event(self, kwargs, response, start_time, end_time): pass
    def log_failure_event(self, kwargs, response, start_time, end_time): pass

litellm.callbacks = [MyLogger()]
```

## Development Notes

### Code Style
- Uses Black formatter (configured in `pyproject.toml`)
- Ruff linter (configured in `ruff.toml`)
- MyPy type checker with `--ignore-missing-imports`
- Pydantic v2 for data validation
- Async/await patterns throughout
- Type hints required for all public APIs
- Python 3.8.1+ minimum version

### Testing Strategy
- **Unit tests**: `tests/test_litellm/` (~15,000 tests) - Run with 4 parallel workers
- **Provider translation tests**: `tests/llm_translation/test_<provider>/` - One directory per provider
- **Proxy tests**: `tests/proxy_unit_tests/` - FastAPI endpoint testing
- **Router tests**: `tests/router_unit_tests/` - Load balancing and fallback logic
- **Security tests**: `tests/proxy_security_tests/` - Authentication and authorization
- **Load tests**: `tests/load_tests/` - Performance and stress testing
- **Integration tests**: `tests/logging_callback_tests/`, `tests/guardrails_tests/`, etc.
- **Documentation tests**: `tests/documentation_tests/` - Circular import checks, import safety

### Adding a New Provider
1. Create directory: `litellm/llms/your_provider/`
2. Implement `__init__.py` with completion/embedding/image_generation functions
3. Add `transformation.py` for input/output format conversion
4. Register provider in `litellm/litellm_core_utils/get_llm_provider_logic.py`
5. Add provider-specific types in `litellm/types/llms/`
6. Create tests in `tests/llm_translation/test_your_provider/`
7. Update `litellm/constants.py` if needed for model lists or defaults

### Database Migrations
- Prisma handles schema migrations automatically
- Schema defined in `litellm/proxy/schema.prisma`
- Migration files auto-generated with `prisma migrate dev`
- Always test migrations against both PostgreSQL and SQLite
- Migrations published via `publish-migrations.yml` workflow

### Enterprise Features
- Enterprise-specific code in `enterprise/` directory
- Optional features enabled via environment variables
- Separate licensing and authentication for enterprise features
- Enterprise package installed separately: `cd enterprise && poetry run pip install -e .`

### CI/CD Workflows (`.github/workflows/`)
Key workflows to be aware of:
- `main.yml` - PR tests and lint checks
- `test-linting.yml` - Code quality checks (must pass)
- `llm-translation-testing.yml` - Provider translation tests
- `load_test.yml` - Performance testing
- `ghcr_deploy.yml` - Docker image builds
- `publish-migrations.yml` - Database migration publishing
- `auto_update_price_and_context_window.yml` - Model metadata updates

### Important Configuration Files
- `pyproject.toml` - Poetry dependencies and package config (extras: proxy, caching, semantic-router, mlflow)
- `ruff.toml` - Ruff linting configuration
- `Makefile` - Common development commands
- `litellm/constants.py` - Runtime configuration constants, feature flags, model lists
- `.github/workflows/` - CI/CD pipeline definitions

### Package Management
- Uses Poetry for dependency management
- Core dependencies in main dependencies section
- Optional dependencies in `[tool.poetry.extras]`: `proxy`, `caching`, `semantic-router`, `mlflow`, etc.
- Development dependencies in `[tool.poetry.group.dev.dependencies]`
- Pin OpenAI version to `1.99.5` in CI environments for stability

## Local Development Workflow

### Quick Development Setup (`dev-scripts/`)
For rapid iteration without Docker builds:

**One-time setup:**
```bash
make install-proxy-dev
poetry run prisma generate
./dev-scripts/start-db.sh  # Starts PostgreSQL container
```

**Daily development:**
```bash
./dev-scripts/start-backend.sh  # Restart after code changes
# Or with custom config:
./dev-scripts/start-backend.sh --config /path/to/config.yaml
```

### Development Scripts
- `start-db.sh` - Start PostgreSQL database (run once, stays running)
- `stop-db.sh` - Stop database (data preserved)
- `reset-db.sh` - Delete all data and start fresh
- `start-backend.sh` - Start proxy server only (most used for development)
- `start-full-dev.sh` - Start backend + frontend dev server (for UI work)
- `build-ui.sh` - Build UI for production (Next.js in `litellm/proxy/_experimental/`)
- `verify-setup.sh` - Validate environment and dependencies
- `setup.sh` - Interactive first-time setup wizard

### Environment Variables for Development
```bash
export DATABASE_URL="postgresql://llmproxy:dbpassword9090@localhost:5432/litellm"
export STORE_MODEL_IN_DB="True"  # Enable UI model management
export LITELLM_MODE="DEV"
export LITELLM_LOG_LEVEL="DEBUG"
```

**Important:** Always run `poetry run prisma generate` after installing dependencies or updating schema.

### UI Development
- Frontend source: `litellm/proxy/_experimental/` (Next.js app)
- Built output: `litellm/proxy/_experimental/out/` (served by FastAPI)
- Development mode: `cd litellm/proxy/_experimental && npm run dev` (port 3000)
- Production build: `./dev-scripts/build-ui.sh`
- Backend serves UI from `/out` directory at runtime

## StepFlow Provider Implementation

The StepFlow provider (`litellm/llms/stepflow/`) demonstrates workflow-based LLM gateway patterns:

### Architecture
- **Workflow Integration**: Routes requests through StepFlow workflow platform
- **Buffered Streaming**: Handles workflow platform's buffered SSE response format
- **Custom Stream Wrapper**: `StepFlowCustomStreamWrapper` in `chat/transformation.py`
  - Parses complete SSE streams from buffered workflow responses
  - Prevents duplicate emissions with `_content_emitted` state flag
  - Consolidates multiple workflow events into single response

### Key Implementation Details
- Models format: `stepflow/provider-model-name` (e.g., `stepflow/gpt-4o`, `stepflow/claude-haiku-4-5-20251001`)
- Environment variables: `STEPFLOW_API_BASE`, `STEPFLOW_API_KEY`
- Supports 11+ providers through unified workflow interface
- Test suite: `tests/llm_translation/test_stepflow/`
- Testing script: `dev-scripts/test-all-models.py` validates model compatibility

### Workflow Platform Behavior
- Platform buffers entire LLM response before returning as SSE stream
- Not true real-time streaming - response is collected first, then streamed
- Multiple SSE events may contain same buffered response
- Custom wrapper handles deduplication and content extraction
