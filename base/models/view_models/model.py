from base.models.definitions.model import ProviderType
from base.models.view_models import BaseModel

# from base.services.configuration.keyvault_config import KeyvaultConfig
from base.services.configuration.local_config import LocalConfig


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
                api_host=LocalConfig.get("openai_llm_endpoint"),
                api_key=LocalConfig.get("openai_llm_api_key"),
                model_name=LocalConfig.get("openai_llm_model"),
                api_type=ProviderType.OPENAI,
                api_retries=2,
                wait_time=1.0,
            )
        elif provider == ProviderType.AZURE_OPENAI:
            return ModelConfigurations(
                api_host=LocalConfig.get("azure_openai_llm_endpoint"),
                api_key=LocalConfig.get("azure_openai_llm_api_key"),
                model_name=LocalConfig.get("azure_openai_llm_deployment_name"),
                api_type=ProviderType.AZURE_OPENAI,
                api_version=LocalConfig.get("azure_openai_api_version"),
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
                api_host=LocalConfig.get("openai_embedding_endpoint"),
                api_key=LocalConfig.get("openai_embedding_api_key"),
                model_name=LocalConfig.get("openai_embedding_model"),
                api_type=ProviderType.OPENAI,
                batch_size=LocalConfig.get_int("openai_embedding_batch_size", 2048),
                dimensions=LocalConfig.get_int("openai_embedding_dimensions", 1536),
            )
        elif provider == ProviderType.AZURE_OPENAI:
            return EmbeddingConfigurations(
                api_host=LocalConfig.get("azure_openai_embedding_endpoint"),
                api_key=LocalConfig.get("azure_openai_embedding_api_key"),
                model_name=LocalConfig.get("azure_openai_embedding_deployment_name"),
                api_type=ProviderType.AZURE_OPENAI,
                api_version=LocalConfig.get("azure_openai_api_version"),
                batch_size=LocalConfig.get_int(
                    "azure_openai_embedding_batch_size", 2048
                ),
                dimensions=LocalConfig.get_int(
                    "azure_openai_embedding_dimensions", 3072
                ),
            )
        else:
            raise ValueError(f"Unsupported provider type: {provider}")
