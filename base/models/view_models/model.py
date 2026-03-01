from base.models.definitions.model import ProviderType
from base.models.view_models import BaseModel


class ModelConfigurations(BaseModel):
    api_host: str | None = None
    api_key: str | None = None
    deployment_name: str | None = None
    model_name: str | None = None
    api_version: str | None = None
    api_type: ProviderType | None = None
    api_retries: int | None = None
    wait_time: float | None = None


class EmbeddingConfigurations(BaseModel):
    api_host: str | None = None
    api_key: str | None = None
    deployment_name: str | None = None
    model_name: str | None = None
    api_version: str | None = None
    api_type: ProviderType | None = None
    batch_size: int = 2048
    dimensions: int | None = None
