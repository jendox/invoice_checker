from abc import ABC, abstractmethod

from app.schemas.internal import ClassificationResult


class LLMClassifier(ABC):
    @abstractmethod
    async def classify(
        self,
        description_raw: str,
        description_normalized: str,
        amount: str,
        bank_name: str,
    ) -> ClassificationResult | None:
        ...


class MockLLMClassifier(LLMClassifier):
    """Placeholder for future OpenAI/local LLM integration."""

    async def classify(
        self,
        description_raw: str,
        description_normalized: str,
        amount: str,
        bank_name: str,
    ) -> ClassificationResult | None:
        return None
