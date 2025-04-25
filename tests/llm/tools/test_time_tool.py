import pytest
import datetime
import zoneinfo
from unittest.mock import patch

from llm.tools.time_tool import TimeTool


@pytest.fixture
def time_tool():
    """Fixture to provide a TimeTool instance."""
    return TimeTool()


def test_time_tool_properties(time_tool):
    """Test the basic properties of the TimeTool."""
    assert time_tool.name == "get_current_time"
    assert time_tool.description == "Gets the current date and time."
    assert time_tool.parameters == {}


def test_time_tool_execute(time_tool):
    """Test the execute method with a mocked datetime."""
    # Define a fixed point in time for testing
    fixed_datetime = datetime.datetime(2023, 10, 27, 14, 30, 0)
    tehran_tz = zoneinfo.ZoneInfo(key="Asia/Tehran")
    fixed_datetime_tehran = fixed_datetime.replace(tzinfo=tehran_tz)

    # Mock datetime.datetime.now() to return the fixed time
    with patch('llm.tools.time_tool.datetime') as mock_datetime:
        mock_datetime.datetime.now.return_value = fixed_datetime_tehran
        mock_datetime.datetime.side_effect = lambda *args, **kw: datetime.datetime(*args, **kw)

        # Execute the tool
        result = time_tool.execute()

        # Assert the output format
        expected_output = "The current date and time in Tehran is: 2023-10-27 14:30:00"
        assert result == expected_output

        # Verify that now was called with the correct timezone
        mock_datetime.datetime.now.assert_called_once_with(tz=tehran_tz)