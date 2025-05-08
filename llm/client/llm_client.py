from typing import List

from openai import OpenAI, APIError, RateLimitError, APIConnectionError

from llm.config import LLmSettings, default_llm_settings
from llm.memory import PersistedWindowBufferMemory, Memory, Message
from llm.memory.in_memory_window_buffer_memory import InMemoryWindowBufferMemory


class LlmClient:
    """
    A class to interact with LLM models using the OpenAI Python library.
    """

    def __init__(
        self,
        llm_settings: LLmSettings = default_llm_settings,
        system_prompt: str = "You are a helpful assistant.",
        memory: Memory = InMemoryWindowBufferMemory(),
        temperature: float = 0.1,
    ):
        """
        Initializes the LLM client.

        Args:
            llm_settings: The LLM settings to use.
            system_prompt: The initial system's prompt to set the context for the model.
            memory: The strategy to use for storing and retrieving message history.
            temperature: The temperature to use for the model.
        """
        self.llm_settings = llm_settings
        self.system_prompt = Message(role="system", content=system_prompt)
        self.temperature = temperature

        self.client = OpenAI(
            base_url=self.llm_settings.base_url,
            api_key=self.llm_settings.api_key,
        )

        self.memory = memory

        # Initialize message history with system prompt if one exists
        if self.system_prompt:
            self.memory.add_message(self.system_prompt)

    def chat(self, user_message: str) -> str:
        """
        Sends a message to the configured OpenRouter model and returns the response.

        Args:
            user_message: The message from the user.

        Returns:
            The model's response content as a string.

        Raises:
            APIError: If the API returns an error.
            RateLimitError: If the API rate limit is exceeded.
            APIConnectionError: If there's an issue connecting to the API.
            Exception: For other unexpected errors.
        """
        user_msg = Message(role="user", content=user_message)
        self.memory.add_message(user_msg)

        assistant_response_content = ""

        try:
            # Convert Message objects to dictionaries for the API
            messages_dict = [msg.to_dict() for msg in self.memory.get_messages()]
            response = self.client.chat.completions.create(
                model=self.llm_settings.model,
                messages=messages_dict,
                temperature=self.temperature,
            )

            # Add checks for response and choices
            if response and response.choices:
                # Check message and content existence before accessing
                message = response.choices[0].message
                if message and message.content is not None:
                    assistant_response_content = message.content
                    self.memory.add_message(
                        Message(role="assistant", content=assistant_response_content)
                    )
                else:
                    # Handle case where message or content is None/empty
                    print("Warning: Received response with missing message content.")
                    self.memory.add_message(Message(role="assistant", content=""))
            else:
                # Handle case where response or choices are missing
                print("Warning: Received an empty or invalid response from the API.")
                # Append an empty assistant message to keep history consistent
                self.memory.add_message(Message(role="assistant", content=""))

            return assistant_response_content

        except (APIError, RateLimitError, APIConnectionError) as e:
            print(f"API Error: {e}")
            self.memory.remove_last_message()
            raise
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            self.memory.remove_last_message()
            raise

    def get_message_history(self) -> List[Message]:
        """
        Returns the current message history.

        Returns:
            A list of Message objects.
        """
        return self.memory.get_messages()

    def clear_message_history(self):
        """
        Clears the message history.
        If a system prompt was provided during initialization, it will be retained.
        """
        self.memory.clear_messages(system_prompt=self.system_prompt)
