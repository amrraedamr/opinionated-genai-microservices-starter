"""Fixtures for base tests.

`base` is a library, so there is no service settings class to import. Tests
that reach a configured subsystem compose the smallest settings that subsystem
needs and register them, exactly as a real service's composition root does.
"""

from base.services.configuration import CoreSettings, configure
from base.services.configuration.mixins import EmbeddingSettingsMixin, LLMSettingsMixin
from base.testing import broker  # noqa: F401


class _TestSettings(CoreSettings, LLMSettingsMixin, EmbeddingSettingsMixin):
    pass


configure(
    _TestSettings(
        service_name="base-tests",
        azure_openai_llm_endpoint="https://example.openai.azure.com",
        azure_openai_llm_deployment_name="gpt-test",
        azure_openai_llm_api_key="sk-test",
        azure_openai_embedding_endpoint="https://example.openai.azure.com",
        azure_openai_embedding_deployment_name="embed-test",
        azure_openai_embedding_api_key="sk-test",
    )
)
