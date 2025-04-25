import logging
import re
from typing import Dict, Any, List, Optional

from .llm_interface_factory import LlmInterfaceFactory
from .tools import Tool, CalculatorTool, TimeTool
from .prompts.agent_system_prompt import BASE_AGENT_SYSTEM_PROMPT


class Agent:
    """
    An AI agent that can use various tools to accomplish tasks.
    """

    def __init__(self, interface_factory: LlmInterfaceFactory, tools: List[Tool], log_level=logging.INFO):
        """
        Initialize the agent with an LLM interface.

        Args:
            interface_factory: The LLM interface factory to use for generating responses
            tools: A list of tools to use for the agent
            log_level: Logging level (default: logging.INFO)
        """
        # Configure logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(log_level)

        if not self.logger.handlers:
            # Add handler if none exists
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

        self.logger.info("Initializing Agent")
        self.tools: Dict[str, Tool] = {tool.name: tool for tool in tools}
        self.logger.debug(f"Registered tools: {list(self.tools.keys())}")

        # Set up the system prompt with tool usage instructions
        system_prompt = self._create_system_prompt(self.tools)
        self.llm_interface = interface_factory.create(system_prompt)
        self.logger.info("Agent initialized successfully")

    def _create_system_prompt(self, tools: Dict[str, Tool]) -> str:
        """Update the system prompt with current tool definitions."""
        self.logger.debug("Creating system prompt with tool definitions")
        tools_json = []

        for tool in tools.values():
            tools_json.append({
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters
            })

        system_prompt = BASE_AGENT_SYSTEM_PROMPT

        # Add tool descriptions to system prompt
        for tool_json in tools_json:
            system_prompt += f"\n- {tool_json['name']}: {tool_json['description']}"
            system_prompt += "\n  Parameters:"
            for param_name, param_details in tool_json['parameters'].items():
                system_prompt += f"\n  - {param_name}: {param_details['description']}"

        # If no tools are available, add a note
        if not tools_json:
            system_prompt += "\nNo tools are currently available."
            self.logger.warning("No tools available for the agent")

        self.logger.debug(f"System prompt created with {len(tools_json)} tools")
        return system_prompt

    def parse_tool_call(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Parse a tool call from the model's response.

        Args:
            text: The text to parse for a tool call

        Returns:
            A dictionary with the tool name and parameters, or None if no tool call was found
        """
        self.logger.debug("Parsing tool call from response")
        # Look for a tool call in the format ```tool {...} ```
        tool_pattern = r'```tool\s*\n(.*?)\n```'
        match = re.search(tool_pattern, text, re.DOTALL)

        if match:
            try:
                import json
                tool_json = json.loads(match.group(1))
                self.logger.info(f"Tool call detected: {tool_json.get('name')}")
                return {
                    "name": tool_json.get("name"),
                    "parameters": tool_json.get("parameters", {})
                }
            except Exception as e:
                self.logger.error(f"Failed to parse tool JSON: {e}")
                return None

        self.logger.debug("No tool call found in response")
        return None

    def execute_tool(self, tool_call: Dict[str, Any]) -> str:
        """
        Execute a tool based on the parsed tool call.

        Args:
            tool_call: A dictionary with the tool name and parameters

        Returns:
            The result of the tool execution
        """
        tool_name = tool_call.get("name")
        parameters = tool_call.get("parameters", {})
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
        llm_response = self.llm_interface.chat(user_message)
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
        tool_name = tool_call.get("name", "unknown")
        result_message = f"Tool '{tool_name}' returned: {tool_result}"
        self.logger.debug(f"Sending tool result to LLM: {result_message}")

        final_response = self.llm_interface.chat(result_message)
        self.logger.debug(f"Final LLM response: {final_response}")
        return final_response


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    from .memory import WindowBufferedMemory

    load_dotenv()

    # Initialize the LLM interface
    llm_interface_factory = LlmInterfaceFactory(
        model=os.getenv("LLM_INTERFACE_MODEL"),
        api_key=os.getenv("LLM_INTERFACE_API_KEY"),
        base_url=os.getenv("LLM_INTERFACE_BASE_URL"),
        memory_strategy=WindowBufferedMemory()
    )

    # Initialize the agent with DEBUG level for more verbose logging
    agent = Agent(
        interface_factory=llm_interface_factory,
        tools=[CalculatorTool(), TimeTool()],
        log_level=logging.DEBUG
    )

    while True:
        user_input = input("You: ")
        if user_input.lower() == 'quit':
            break

        response = agent.process(user_input)
        print(f"Agent: {response}")
