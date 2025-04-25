import datetime
import zoneinfo

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
        tehran_tz = zoneinfo.ZoneInfo(key='Asia/Tehran')
        now = datetime.datetime.now(tz=tehran_tz)
        return f"The current date and time in Tehran is: {now.strftime('%Y-%m-%d %H:%M:%S')}"
