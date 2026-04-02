from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict


class CalculatorError(Exception):
    """Base error for calculator failures."""


class InvalidOperationError(CalculatorError):
    """Raised when the requested operation is unknown."""


class DivisionByZeroError(CalculatorError):
    """Raised when division by zero is attempted."""


@dataclass(frozen=True)
class Tool:
    """Represents a calculator tool the agent can call."""

    name: str
    description: str
    execute: Callable[[float, float], float]


def add(a: float, b: float) -> float:
    return a + b


def subtract(a: float, b: float) -> float:
    return a - b


def multiply(a: float, b: float) -> float:
    return a * b


def divide(a: float, b: float) -> float:
    if b == 0:
        raise DivisionByZeroError("Cannot divide by zero.")
    return a / b


def power(a: float, b: float) -> float:
    return a**b


def modulus(a: float, b: float) -> float:
    if b == 0:
        raise DivisionByZeroError("Cannot take modulus by zero.")
    return a % b


def get_tool_registry() -> Dict[str, Tool]:
    """Returns all available tools by canonical operation name."""

    return {
        "add": Tool("add", "Adds two numbers.", add),
        "subtract": Tool("subtract", "Subtracts second number from first.", subtract),
        "multiply": Tool("multiply", "Multiplies two numbers.", multiply),
        "divide": Tool("divide", "Divides first number by second.", divide),
        "power": Tool("power", "Raises first number to the second number.", power),
        "modulus": Tool("modulus", "Returns remainder of first divided by second.", modulus),
    }
