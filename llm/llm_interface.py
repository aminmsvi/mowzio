import os
from typing import List, Dict

from dotenv import load_dotenv
from openai import OpenAI, APIError, RateLimitError, APIConnectionError

from .memory import WindowBufferedMemory, Memory


class LlmInterface:
    """
    A class to interact with OpenRouter models using the OpenAI Python library.
    """
    def __init__(
        self,
        model: str,
        api_key: str,
        base_url: str,
        system_prompt: str = "You are a helpful assistant.",
        memory_strategy: Memory = WindowBufferedMemory(),
        temperature: float = 0.1,
    ):
        """
        Initializes the OpenRouterChat client.

        Args:
            model: The name of the OpenRouter model to use (e.g., "openai/gpt-3.5-turbo").
            api_key: Your OpenRouter API key. Defaults to the OPENROUTER_API_KEY environment variable.
            base_url: The base URL for the OpenRouter API.
            system_prompt: The initial system prompt to set the context for the model.
            memory_strategy: The strategy to use for storing and retrieving message history.
                            If None, defaults to InMemoryStrategy.
        """
        self.model = model
        self.base_url = base_url
        self.system_prompt_text = system_prompt
        self.system_prompt = {"role": "system", "content": system_prompt}
        self.temperature = temperature

        if not api_key:
            raise ValueError("API key must be provided either as an argument or via OPENROUTER_API_KEY environment variable.")

        self.client = OpenAI(
            base_url=self.base_url,
            api_key=api_key,
        )

        self.memory_strategy = memory_strategy

        # Initialize message history with system prompt if one exists
        if self.system_prompt:
            self.memory_strategy.add_message(self.system_prompt)

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
        user_msg_dict = {"role": "user", "content": user_message}
        self.memory_strategy.add_message(user_msg_dict)

        assistant_response_content = ""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.memory_strategy.get_messages(),
                temperature=self.temperature,
            )

            # Add checks for response and choices
            if response and response.choices:
                # Check message and content existence before accessing
                message = response.choices[0].message
                if message and message.content is not None:
                    assistant_response_content = message.content
                    self.memory_strategy.add_message({"role": "assistant", "content": assistant_response_content})
                else:
                    # Handle case where message or content is None/empty
                    print("Warning: Received response with missing message content.")
                    self.memory_strategy.add_message({"role": "assistant", "content": ""})
            else:
                # Handle case where response or choices are missing
                print("Warning: Received an empty or invalid response from the API.")
                # Append an empty assistant message to keep history consistent
                self.memory_strategy.add_message({"role": "assistant", "content": ""})

            return assistant_response_content

        except (APIError, RateLimitError, APIConnectionError) as e:
            print(f"API Error: {e}")
            self.memory_strategy.remove_last_message()
            raise
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            self.memory_strategy.remove_last_message()
            raise

    def get_message_history(self) -> List[Dict[str, str]]:
        """
        Returns the current message history.

        Returns:
            A list of message dictionaries.
        """
        return self.memory_strategy.get_messages()

    def clear_message_history(self):
        """
        Clears the message history.
        If a system prompt was provided during initialization, it will be retained.
        """
        self.memory_strategy.clear_messages(system_prompt=self.system_prompt)


if __name__ == "__main__":
    load_dotenv()

    try:
        # Initialize the chat client with the memory strategy
        chat_client = LlmInterface(
            model=os.getenv("LLM_INTERFACE_MODEL"),
            api_key=os.getenv("LLM_INTERFACE_API_KEY"),
            base_url=os.getenv("LLM_INTERFACE_BASE_URL"),
            system_prompt="You are a helpful assistant.",
            memory_strategy=WindowBufferedMemory()
        )

        print(f"Chatting with {chat_client.model}. Type 'quit' to exit.")
        while True:
            user_input = input("You: ")
            if user_input.lower() == 'quit':
                break

            response_content = chat_client.chat(user_input)
            print(f"Assistant: {response_content}")

        print("\nMessage History:")
        print(chat_client.get_message_history())


    except ValueError as ve:
        print(f"Configuration Error: {ve}")
    except APIError as ae:
        print(f"OpenRouter API Error: {ae}")
    except Exception as ex:
        print(f"An error occurred: {ex}")