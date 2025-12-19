from lab1_basic_agent_working import CalculatorAgent, add_tool, multiply_tool, divide_tool


def test_tools():
    assert add_tool.func(2, 3) == 5
    assert multiply_tool.func(4, 5) == 20
    assert divide_tool.func(10, 2) == 5


def test_fallback_eval():
    agent = CalculatorAgent(api_key=None)
    assert "5.0" in agent.run("(2 + 3)") or "5" in agent.run("(2 + 3)")
    assert "25" in agent.run("5 * 5")


def test_divide_by_zero_tool():
    try:
        divide_tool.func(1, 0)
        assert False, "Expected ValueError"
    except ValueError:
        assert True