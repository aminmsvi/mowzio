import logging
import re
from typing import Dict, List, Optional

from llm.client import LlmClient
from llm.memory import Memory
from llm.memory.in_memory_window_buffer_memory import \
    InMemoryWindowBufferMemory

from .config import LLmSettings, default_llm_settings
from .prompts.tool_usage_prompt import TOOL_USAGE_PROMPT
from .tools import Tool
from .tools.tool import ToolCall


class Agent:
    """
    An AI agent that can use various tools to carry out tasks.
    """

    def __init__(
        self,
        tools: List[Tool] = [],
        llm_settings: LLmSettings = default_llm_settings,
        system_prompt: str = "You are a helpful assistant.",
        memory: Memory = InMemoryWindowBufferMemory(),
    ):
        """
        Initialize the agent with an LLM client.

        Args:
            llm_settings: The LLM settings to use.
            system_prompt: The initial system's prompt to set the context for the model.
            memory: The strategy to use for storing and retrieving message history.
            tools: A list of tools to use for the agent
        """
        # Configure logging
        self.memory = memory
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        self.logger.info("Initializing Agent")
        self.tools: Dict[str, Tool] = {tool.name: tool for tool in tools}
        self.logger.debug(f"Registered tools: {list(self.tools.keys())}")

        # Set up the system prompt with tool usage instructions
        system_prompt = self._create_system_prompt(
            tools=self.tools,
            system_prompt=system_prompt,
        )
        self.llm_client = LlmClient(
            llm_settings=llm_settings,
            system_prompt=system_prompt,
            memory=memory,
        )
        self.logger.info("Agent initialized successfully")

    def _create_system_prompt(self, tools: Dict[str, Tool], system_prompt: str) -> str:
        """Update the system prompt with current tool definitions."""
        self.logger.debug("Creating system prompt with tool definitions")
        tools_json = []

        if len(tools) == 0:
            return system_prompt

        for tool in tools.values():
            tools_json.append(
                {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": {
                        param_name: param.to_dict()
                        for param_name, param in tool.parameters.items()
                    },
                }
            )

        prompt = f"{system_prompt}\n{TOOL_USAGE_PROMPT}"

        # Add tool descriptions to system prompt
        for tool_json in tools_json:
            prompt += f"\n- {tool_json['name']}: {tool_json['description']}"
            prompt += "\n  Parameters:"
            for param_name, param_details in tool_json["parameters"].items():
                prompt += f"\n  - {param_name}: {param_details['description']}"

        # If no tools are available, add a note
        if not tools_json:
            prompt += "\nNo tools are currently available."
            self.logger.warning("No tools available for the agent")

        self.logger.debug(f"System prompt created with {len(tools_json)} tools")
        return prompt

    def parse_tool_call(self, text: str) -> Optional[ToolCall]:
        """
        Parse a tool call from the model's response.

        Args:
            text: The text to parse for a tool call

        Returns:
            A ToolCall object, or None if no tool call was found
        """
        self.logger.debug("Parsing tool call from response")
        # Look for a tool call in the format ```tool {...} ```
        tool_pattern = r"```tool\s*\n(.*?)\n```"
        match = re.search(tool_pattern, text, re.DOTALL)

        if match:
            try:
                import json

                tool_json = json.loads(match.group(1))
                self.logger.info(f"Tool call detected: {tool_json.get('name')}")
                return ToolCall(
                    name=tool_json.get("name"),
                    parameters=tool_json.get("parameters", {}),
                )
            except Exception as e:
                self.logger.error(f"Failed to parse tool JSON: {e}")
                return None

        self.logger.debug("No tool call found in response")
        return None

    def execute_tool(self, tool_call: ToolCall) -> str:
        """
        Execute a tool based on the parsed tool call.

        Args:
            tool_call: A ToolCall object with the tool name and parameters

        Returns:
            The result of the tool execution
        """
        tool_name = tool_call.name
        parameters = tool_call.parameters
        self.logger.info(f"Executing tool: {tool_name} with parameters: {parameters}")

        if tool_name not in self.tools:
            error_msg = f"Error: Tool '{tool_name}' not found."
            self.logger.error(error_msg)
            return error_msg

        try:
            result = self.tools[tool_name].execute(**parameters)
            self.logger.debug(f"Tool execution result: {result}")
            return result
        except Exception as e:
            error_msg = f"Error executing tool '{tool_name}': {str(e)}"
            self.logger.error(f"Tool execution failed: {e}", exc_info=True)
            return error_msg

    def process(self, user_message: str) -> str:
        """
        Process a user message and generate a response.

        Args:
            user_message: The user's message

        Returns:
            The agent's response after potentially using tools
        """
        self.logger.info("Processing user message")
        self.logger.debug(f"User message: {user_message}")

        # Get the LLM's initial response
        llm_response = self.llm_client.chat(user_message)
        self.logger.debug(f"Initial LLM response: {llm_response}")

        # Check if the response contains a tool call
        tool_call = self.parse_tool_call(llm_response)

        # If no tool call, return the response as is
        if not tool_call:
            self.logger.info("No tool call detected, returning response as is")
            return llm_response

        # Execute the tool
        tool_result = self.execute_tool(tool_call)

        # Send the tool result back to the LLM
        tool_name = tool_call.name
        result_message = f"Tool '{tool_name}' returned: {tool_result}"
        self.logger.debug(f"Sending tool result to LLM: {result_message}")

        final_response = self.llm_client.chat(result_message)
        self.logger.debug(f"Final LLM response: {final_response}")
        return final_response
