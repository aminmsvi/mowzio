import math
from typing import Dict

from .tool import Tool, ToolParameter


class CalculatorTool(Tool):
    """A tool for performing mathematical calculations."""

    @property
    def name(self) -> str:
        return "calculator"

    @property
    def description(self) -> str:
        return "Evaluates mathematical expressions. Use this for calculations."

    @property
    def parameters(self) -> Dict[str, ToolParameter]:
        return {
            "expression": ToolParameter(
                type="string", description="The mathematical expression to evaluate"
            )
        }

    def execute(self, expression: str) -> str:
        """
        Safely evaluate a mathematical expression.

        Args:
            expression: A string containing a mathematical expression
                       (e.g., "2 + 2", "sin(0.5) * 10")

        Returns:
            The result of the calculation as a string
        """
        # Define safe functions
        safe_dict = {
            "abs": abs,
            "round": round,
            "max": max,
            "min": min,
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "asin": math.asin,
            "acos": math.acos,
            "atan": math.atan,
            "sqrt": math.sqrt,
            "log": math.log,
            "log10": math.log10,
            "exp": math.exp,
            "pi": math.pi,
            "e": math.e,
        }

        try:
            # Replace common mathematical functions with their safe versions
            cleaned_expr = expression

            # Evaluate the expression in the safe environment
            result = eval(cleaned_expr, {"__builtins__": {}}, safe_dict)
            return str(result)
        except Exception as e:
            return f"Error evaluating expression: {str(e)}"
