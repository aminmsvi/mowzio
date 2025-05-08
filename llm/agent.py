import logging
import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from .client.llm_client_factory import LlmClientFactory
from .prompts.agent_system_prompt import AGENT_SYSTEM_PROMPT
from .tools import Tool
from .tools.tool import ToolCall
from .tools import CalculatorTool, TimeTool


class Agent:
    """
    An AI agent that can use various tools to accomplish tasks.
    """

    def __init__(
        self,
        client_factory: LlmClientFactory,
        tools: List[Tool],
    ):
        """
        Initialize the agent with an LLM client.

        Args:
            client_factory: The LLM client factory to use for generating responses
            tools: A list of tools to use for the agent
        """
        # Configure logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        self.logger.info("Initializing Agent")
        self.tools: Dict[str, Tool] = {tool.name: tool for tool in tools}
        self.logger.debug(f"Registered tools: {list(self.tools.keys())}")

        # Set up the system prompt with tool usage instructions
        system_prompt = self._create_system_prompt(self.tools)
        self.llm_client = client_factory.create(system_prompt)
        self.logger.info("Agent initialized successfully")

    def _create_system_prompt(self, tools: Dict[str, Tool]) -> str:
        """Update the system prompt with current tool definitions."""
        self.logger.debug("Creating system prompt with tool definitions")
        tools_json = []

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

        system_prompt = AGENT_SYSTEM_PROMPT

        # Add tool descriptions to system prompt
        for tool_json in tools_json:
            system_prompt += f"\n- {tool_json['name']}: {tool_json['description']}"
            system_prompt += "\n  Parameters:"
            for param_name, param_details in tool_json["parameters"].items():
                system_prompt += f"\n  - {param_name}: {param_details['description']}"

        # If no tools are available, add a note
        if not tools_json:
            system_prompt += "\nNo tools are currently available."
            self.logger.warning("No tools available for the agent")

        self.logger.debug(f"System prompt created with {len(tools_json)} tools")
        return system_prompt

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


if __name__ == "__main__":
    from dotenv import load_dotenv
    from .memory import PersistedWindowMemory
    from app.config import settings

    load_dotenv()

    # Initialize the LLM client
    llm_client_factory = LlmClientFactory(
        model=settings.LLM_CLIENT_MODEL,
        api_key=settings.LLM_CLIENT_API_KEY,
        base_url=settings.LLM_CLIENT_BASE_URL,
        memory=PersistedWindowMemory(),
    )

    # Initialize the agent with DEBUG level for more verbose logging
    agent = Agent(
        client_factory=llm_client_factory,
        tools=[CalculatorTool(), TimeTool()],
    )

    while True:
        user_input = input("You: ")
        if user_input.lower() == "quit":
            break

        response = agent.process(user_input)
        print(f"Agent: {response}")
