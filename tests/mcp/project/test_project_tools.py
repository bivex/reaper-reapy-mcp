import pytest
from types import SimpleNamespace
from src.mcp_tools import _setup_project_tools, _setup_marker_tools, FastMCP

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
        project=SimpleNamespace(
            set_tempo=lambda bpm: True,
            get_tempo=lambda: 120.0,
            clear_project=lambda: True,
        ),
        marker=SimpleNamespace(
            create_region=lambda st, et, n: True,
            delete_region=lambda idx: True,
            create_marker=lambda t, n: True,
            delete_marker=lambda idx: True,
        ),
    )
    mcp = DummyMCP()
    _setup_project_tools(mcp, controller)
    _setup_marker_tools(mcp, controller)
    return mcp, controller

@pytest.mark.parametrize("tool,kwargs", [
    ("set_tempo", {"bpm": 128.0}),
    ("get_tempo", {}),
    ("clear_project", {}),
    ("create_region", {"start_time": 0.0, "end_time": 4.0, "name": "Verse"}),
    ("delete_region", {"region_index": 0}),
    ("create_marker", {"time": 1.0, "name": "Hit"}),
    ("delete_marker", {"marker_index": 0}),
])
def test_project_tools_success(mcp_and_controller, tool, kwargs):
    mcp, _ = mcp_and_controller
    fn = mcp.tools[tool]
    res = fn(None, **kwargs)
    assert isinstance(res, dict)
    assert res.get("status") in {"success", "error"}
    assert "message" in res
