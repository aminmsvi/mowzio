import datetime

from .tool import Tool


class TimeTool(Tool):
    """A tool to get the current date and time."""

    @property
    def name(self) -> str:
        """The name of the tool."""
        return "get_current_time"

    @property
    def description(self) -> str:
        """A description of what the tool does."""
        return "Gets the current date and time."

    def execute(self) -> str:
        """Execute the tool to get the current time.

        Returns:
            A string representing the current date and time.
        """
        now = datetime.datetime.now()
        return f"The current date and time is: {now.strftime('%Y-%m-%d %H:%M:%S')}"
