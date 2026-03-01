from enum import StrEnum


class ProviderType(StrEnum):
    AZURE_OPENAI = "azure-openai"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    VLLM = "vllm"
    GROQ = "groq"
    TOGETHER = "together"
    LITELLM = "litellm"
