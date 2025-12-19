from lab1_basic_agent import add_tool, multiply_tool, divide_tool
import pytest


def test_add_tool():
    # StructuredTool wraps the function; call underlying .func
    assert add_tool.func(2, 3) == 5


def test_multiply_tool():
    assert multiply_tool.func(4, 5) == 20


def test_divide_tool():
    assert divide_tool.func(10, 2) == 5


def test_divide_by_zero():
    with pytest.raises(ValueError):
        divide_tool.func(1, 0)
