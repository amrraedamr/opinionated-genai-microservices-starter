from typing import Protocol, runtime_checkable


@runtime_checkable
class SupportsLLMConfig(Protocol):
    """Settings shape `ModelConfigurations.get_default_for_provider` requires."""

    azure_openai_api_version: str
    azure_openai_llm_endpoint: str
    azure_openai_llm_deployment_name: str
    azure_openai_llm_api_key: str

    openai_llm_endpoint: str
    openai_llm_model: str
    openai_llm_api_key: str


@runtime_checkable
class SupportsEmbeddingConfig(Protocol):
    """Settings shape `EmbeddingConfigurations.get_default_for_provider` requires."""

    azure_openai_api_version: str
    azure_openai_embedding_endpoint: str
    azure_openai_embedding_deployment_name: str
    azure_openai_embedding_api_key: str
    azure_openai_embedding_dimensions: int
    azure_openai_embedding_batch_size: int

    openai_embedding_endpoint: str
    openai_embedding_model: str
    openai_embedding_api_key: str
    openai_embedding_dimensions: int
    openai_embedding_batch_size: int
