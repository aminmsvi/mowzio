from llm.memory import Memory, PersistedWindowMemory
from .llm_client import LlmClient


class LlmClientFactory:
    """
    Factory class for creating LlmClient instances with pre-configured settings.
    """

    def __init__(
        self,
        model: str,
        api_key: str,
        base_url: str,
        memory: Memory = PersistedWindowMemory(),
    ):
        """
        Initializes the factory with common LLM client parameters.

        Args:
            model: The name of the LLM model to use (e.g., "openai/gpt-3.5-turbo").
            api_key: The API key for the LLM service.
            base_url: The base URL for the LLM API endpoint.
        """
        if not all([model, api_key, base_url]):
            raise ValueError("Model, API key, and base URL must be provided.")
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
        self.memory_strategy = memory

    def create(
        self,
        system_prompt: str,
    ) -> LlmClient:
        """
        Creates a new LlmClient instance with a specific system prompt.

        Args:
            system_prompt: The initial system prompt to set the context for the model.
                           Defaults to "You are a helpful assistant.".

        Returns:
            A configured LlmClient instance.

        Raises:
            ValueError: If the API key is missing during LlmClient initialization
                        (though checked in __init__, LlmClient might re-check).
        """

        # Create and return the LlmClient instance
        return LlmClient(
            model=self.model,
            api_key=self.api_key,
            base_url=self.base_url,
            system_prompt=system_prompt,
            memory=self.memory_strategy,
        )
