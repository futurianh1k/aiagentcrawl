"""
Calculator Tools

계산기 도구들을 정의합니다.
"""

from typing import Union
from langchain.tools import tool


@tool
def add_tool(x: Union[float, int], y: Union[float, int]) -> float:
    """두 수를 더하는 도구

    Args:
        x: 첫 번째 수
        y: 두 번째 수

    Returns:
        두 수의 합
    """
    try:
        result = float(x) + float(y)
        print(f"덧셈 계산: {x} + {y} = {result}")
        return result
    except (ValueError, TypeError) as e:
        raise ValueError(f"덧셈 계산 오류: {e}")


@tool
def multiply_tool(x: Union[float, int], y: Union[float, int]) -> float:
    """두 수를 곱하는 도구

    Args:
        x: 첫 번째 수
        y: 두 번째 수

    Returns:
        두 수의 곱
    """
    try:
        result = float(x) * float(y)
        print(f"곱셈 계산: {x} * {y} = {result}")
        return result
    except (ValueError, TypeError) as e:
        raise ValueError(f"곱셈 계산 오류: {e}")


@tool
def divide_tool(x: Union[float, int], y: Union[float, int]) -> float:
    """두 수를 나누는 도구

    Args:
        x: 분자
        y: 분모

    Returns:
        나눈 결과

    Raises:
        ValueError: 0으로 나누는 경우
    """
    try:
        y_float = float(y)
        if y_float == 0:
            raise ValueError("0으로 나눌 수 없습니다!")

        result = float(x) / y_float
        print(f"나눗셈 계산: {x} / {y} = {result}")
        return result
    except (ValueError, TypeError) as e:
        raise ValueError(f"나눗셈 계산 오류: {e}")

