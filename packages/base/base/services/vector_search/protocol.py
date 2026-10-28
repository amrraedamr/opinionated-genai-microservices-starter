from typing import Protocol, runtime_checkable


@runtime_checkable
class SupportsVectorConfig(Protocol):
    """Settings shape the Qdrant client requires."""

    qdrant_url: str
    qdrant_grpc_port: int
    qdrant_prefer_grpc: bool
    qdrant_timeout: int
    qdrant_api_key: str


@runtime_checkable
class SupportsAzureSearchConfig(Protocol):
    """Settings shape the Azure AI Search client requires."""

    azure_search_endpoint: str
    azure_search_vector_field: str
    azure_search_key_field: str
    azure_search_api_key: str
