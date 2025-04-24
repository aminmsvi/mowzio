import os
from dotenv import load_dotenv
from openai import OpenAI, APIError, RateLimitError, APIConnectionError
from typing import Optional, List, Dict

class LlmInterface:
    """
    A class to interact with OpenRouter models using the OpenAI Python library.
    """
    def __init__(
        self,
        model: str,
        api_key: str,
        base_url: str,
        system_prompt: Optional[str] = "You are a helpful assistant.",
    ):
        """
        Initializes the OpenRouterChat client.

        Args:
            model: The name of the OpenRouter model to use (e.g., "openai/gpt-3.5-turbo").
            api_key: Your OpenRouter API key. Defaults to the OPENROUTER_API_KEY environment variable.
            base_url: The base URL for the OpenRouter API.
            system_prompt: The initial system prompt to set the context for the model.
        """
        self.model = model
        self.base_url = base_url
        self.system_prompt = {"role": "system", "content": system_prompt} if system_prompt else None

        if not api_key:
            raise ValueError("API key must be provided either as an argument or via OPENROUTER_API_KEY environment variable.")

        self.client = OpenAI(
            base_url=self.base_url,
            api_key=api_key,
        )
        self._message_history: List[Dict[str, str]] = []
        if self.system_prompt:
            self._message_history.append(self.system_prompt)

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
        self._message_history.append(user_msg_dict)

        assistant_response_content = ""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self._message_history,
            )

            # Add checks for response and choices
            if response and response.choices:
                # Check message and content existence before accessing
                message = response.choices[0].message
                if message and message.content is not None:
                    assistant_response_content = message.content
                    self._message_history.append({"role": "assistant", "content": assistant_response_content})
                else:
                    # Handle case where message or content is None/empty
                    print("Warning: Received response with missing message content.")
                    self._message_history.append({"role": "assistant", "content": ""})
            else:
                # Handle case where response or choices are missing
                print("Warning: Received an empty or invalid response from the API.")
                # Append an empty assistant message to keep history consistent
                self._message_history.append({"role": "assistant", "content": ""})

            return assistant_response_content

        except (APIError, RateLimitError, APIConnectionError) as e:
            # Log the error or handle it more gracefully
            print(f"API Error: {e}")
            # Remove the last user message if API call failed
            self._message_history.pop()
            raise
        except Exception as e:
            # Log unexpected errors
            print(f"An unexpected error occurred: {e}")
            # Remove the last user message if call failed
            self._message_history.pop()
            raise

    def get_message_history(self) -> List[Dict[str, str]]:
        """
        Returns the current message history.

        Returns:
            A list of message dictionaries.
        """
        return self._message_history.copy()

    def clear_message_history(self):
        """
        Clears the message history.

        Args:
            keep_system_prompt: If True, retains the initial system prompt. Defaults to True.
        """
        self._message_history = []
        if self.system_prompt:
            self._message_history.append(self.system_prompt)


if __name__ == "__main__":
    load_dotenv()

    try:
        chat_client = LlmInterface(
            model=os.getenv("LLM_INTERFACE_MODEL"),
            api_key=os.getenv("LLM_INTERFACE_API_KEY"),
            base_url=os.getenv("LLM_INTERFACE_BASE_URL"),
            system_prompt="You are a helpful assistant."
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

        # Example of clearing history
        # chat_client.clear_message_history()
        # print("\nHistory cleared.")
        # print(chat_client.get_message_history())


    except ValueError as ve:
        print(f"Configuration Error: {ve}")
    except APIError as ae:
        print(f"OpenRouter API Error: {ae}")
    except Exception as ex:
        print(f"An error occurred: {ex}")