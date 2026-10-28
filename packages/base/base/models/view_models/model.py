from base.models.definitions.model import ProviderType
from base.models.view_models import BaseModel
from base.services.configuration import settings


class ModelConfigurations(BaseModel):
    api_host: str | None = None
    api_key: str | None = None
    model_name: str | None = None
    api_version: str | None = None
    api_type: ProviderType | None = None
    api_retries: int | None = None
    wait_time: float | None = None

    @staticmethod
    def get_default_for_provider(provider: ProviderType) -> "ModelConfigurations":
        if provider == ProviderType.OPENAI:
            return ModelConfigurations(
                api_host=settings.openai_llm_endpoint or None,
                api_key=settings.openai_llm_api_key or None,
                model_name=settings.openai_llm_model or None,
                api_type=ProviderType.OPENAI,
                api_retries=2,
                wait_time=1.0,
            )
        elif provider == ProviderType.AZURE_OPENAI:
            return ModelConfigurations(
                api_host=settings.azure_openai_llm_endpoint or None,
                api_key=settings.azure_openai_llm_api_key or None,
                model_name=settings.azure_openai_llm_deployment_name or None,
                api_type=ProviderType.AZURE_OPENAI,
                api_version=settings.azure_openai_api_version or None,
                api_retries=2,
                wait_time=1.0,
            )
        else:
            raise ValueError(f"Unsupported provider type: {provider}")


class EmbeddingConfigurations(BaseModel):
    api_host: str | None = None
    api_key: str | None = None
    model_name: str | None = None
    api_version: str | None = None
    api_type: ProviderType | None = None
    batch_size: int | None = None
    dimensions: int | None = None

    @staticmethod
    def get_default_for_provider(provider: ProviderType) -> "EmbeddingConfigurations":
        if provider == ProviderType.OPENAI:
            return EmbeddingConfigurations(
                api_host=settings.openai_embedding_endpoint or None,
                api_key=settings.openai_embedding_api_key or None,
                model_name=settings.openai_embedding_model or None,
                api_type=ProviderType.OPENAI,
                batch_size=settings.openai_embedding_batch_size,
                dimensions=settings.openai_embedding_dimensions,
            )
        elif provider == ProviderType.AZURE_OPENAI:
            return EmbeddingConfigurations(
                api_host=settings.azure_openai_embedding_endpoint or None,
                api_key=settings.azure_openai_embedding_api_key or None,
                model_name=settings.azure_openai_embedding_deployment_name or None,
                api_type=ProviderType.AZURE_OPENAI,
                api_version=settings.azure_openai_api_version or None,
                batch_size=settings.azure_openai_embedding_batch_size,
                dimensions=settings.azure_openai_embedding_dimensions,
            )
        else:
            raise ValueError(f"Unsupported provider type: {provider}")
