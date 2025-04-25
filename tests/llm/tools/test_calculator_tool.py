import pytest
import math

from llm.tools.calculator_tool import CalculatorTool


@pytest.fixture
def calculator_tool():
    return CalculatorTool()


def test_calculator_tool_properties(calculator_tool):
    assert calculator_tool.name == "calculator"
    assert calculator_tool.description == "Evaluates mathematical expressions. Use this for calculations."
    assert "expression" in calculator_tool.parameters


def test_calculator_tool_simple_arithmetic(calculator_tool):
    assert calculator_tool.execute("2 + 2") == "4"
    assert calculator_tool.execute("10 - 3") == "7"
    assert calculator_tool.execute("5 * 6") == "30"
    assert calculator_tool.execute("10 / 2") == "5.0"


def test_calculator_tool_functions(calculator_tool):
    assert calculator_tool.execute("sin(0)") == "0.0"
    assert calculator_tool.execute("cos(0)") == "1.0"
    assert calculator_tool.execute("sqrt(16)") == "4.0"
    assert calculator_tool.execute("log10(100)") == "2.0"


def test_calculator_tool_constants(calculator_tool):
    assert calculator_tool.execute("pi") == str(math.pi)
    assert calculator_tool.execute("e") == str(math.e)


def test_calculator_tool_combined_expression(calculator_tool):
    assert calculator_tool.execute("sin(pi/2) * 10") == "10.0"
    assert calculator_tool.execute("(5 + 3) * sqrt(4)") == "16.0"


def test_calculator_tool_invalid_expression(calculator_tool):
    result = calculator_tool.execute("invalid_function(1)")
    assert "Error evaluating expression" in result
    assert "not defined" in result


def test_calculator_tool_unsafe_expression(calculator_tool):
    # Test attempts to use disallowed builtins or execute arbitrary code
    result_import = calculator_tool.execute("__import__('os').system('echo unsafe')")
    assert "Error evaluating expression" in result_import

    result_builtin = calculator_tool.execute("open('test.txt')")
    assert "Error evaluating expression" in result_builtin
    assert "not defined" in result_builtin

    result_eval = calculator_tool.execute("eval('1+1')")
    assert "Error evaluating expression" in result_eval
    assert "not defined" in result_eval

def test_calculator_tool_division_by_zero(calculator_tool):
    result = calculator_tool.execute("1 / 0")
    assert "Error evaluating expression: division by zero" in result

def test_calculator_tool_syntax_error(calculator_tool):
    result = calculator_tool.execute("2 +")
    assert "Error evaluating expression: unexpected EOF while parsing" in result or "Error evaluating expression: invalid syntax" in result # Python version differences