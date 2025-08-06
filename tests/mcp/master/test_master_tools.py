import pytest
from types import SimpleNamespace
from src.mcp_tools import setup_mcp_tools, FastMCP

class DummyMCP(FastMCP):
    def __init__(self):
        super().__init__("reaper-reapy-mcp")
        self.tools = {}
    def tool(self, name):
        def decorator(fn):
            self.tools[name] = fn
            return fn
        return decorator

@pytest.fixture
def mcp_and_controller():
    controller = SimpleNamespace(
        master=SimpleNamespace(
            get_master_track=lambda: {"name": "MASTER"},
            set_master_volume=lambda v: True,
            set_master_pan=lambda p: True,
            toggle_master_mute=lambda m=None: True,
            toggle_master_solo=lambda s=None: True,
        )
    )
    mcp = DummyMCP()
    setup_mcp_tools(mcp, controller)
    return mcp, controller

@pytest.mark.parametrize("tool,kwargs", [
    ("get_master_track", {}),
    ("set_master_volume", {"volume": -3.0}),
    ("set_master_pan", {"pan": 0.1}),
    ("toggle_master_mute", {}),
    ("toggle_master_solo", {}),
])
def test_master_tools_success(mcp_and_controller, tool, kwargs):
    mcp, _ = mcp_and_controller
    fn = mcp.tools[tool]
    res = fn(None, **kwargs)
    assert isinstance(res, dict)
    assert res.get("status") in {"success", "error"}
    assert "message" in res
