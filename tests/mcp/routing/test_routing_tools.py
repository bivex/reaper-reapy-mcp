import pytest
from types import SimpleNamespace
from src.mcp_tools import _setup_routing_tools, FastMCP

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
        routing=SimpleNamespace(
            add_send=lambda *a, **k: 1,
            remove_send=lambda *a, **k: True,
            get_sends=lambda t: [{"dest": 1}],
            get_receives=lambda t: [{"src": 0}],
            set_send_volume=lambda *a, **k: True,
            set_send_pan=lambda *a, **k: True,
            toggle_send_mute=lambda *a, **k: True,
            get_track_routing_info=lambda t: {"sends": [], "receives": []},
            debug_track_routing=lambda t: "ok",
            clear_all_sends=lambda t: True,
            clear_all_receives=lambda t: True,
        )
    )
    mcp = DummyMCP()
    _setup_routing_tools(mcp, controller)
    return mcp, controller

@pytest.mark.parametrize("tool,kwargs", [
    ("add_send", {"source_track": 0, "destination_track": 1, "volume": -6.0}),
    ("remove_send", {"track_index": 0, "send_index": 0}),
    ("get_sends", {"track_index": 0}),
    ("get_receives", {"track_index": 0}),
    ("set_send_volume", {"track_index": 0, "send_index": 0, "volume": -3.0}),
    ("set_send_pan", {"track_index": 0, "send_index": 0, "pan": 0.2}),
    ("toggle_send_mute", {"track_index": 0, "send_index": 0}),
    ("get_track_routing_info", {"track_index": 0}),
    ("debug_track_routing", {"track_index": 0}),
    ("clear_all_sends", {"track_index": 0}),
    ("clear_all_receives", {"track_index": 0}),
])
def test_routing_tools_success(mcp_and_controller, tool, kwargs):
    mcp, _ = mcp_and_controller
    fn = mcp.tools[tool]
    res = fn(None, **kwargs)
    assert isinstance(res, dict)
    assert res.get("status") in {"success", "error"}
    assert "message" in res
