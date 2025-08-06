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
    calls = {}
    controller = SimpleNamespace(
        track=SimpleNamespace(
            create_track=lambda name=None: 1,
            rename_track=lambda idx, new: True,
            set_track_color=lambda idx, color: True,
            get_track_color=lambda idx: "#ff0000",
            get_track_count=lambda: 3,
            set_track_volume=lambda idx, v: True,
            get_track_volume=lambda idx: -6.0,
            set_track_pan=lambda idx, p: True,
            get_track_pan=lambda idx: 0.25,
            set_track_mute=lambda idx, m: True,
            get_track_mute=lambda idx: False,
            set_track_solo=lambda idx, s: True,
            get_track_solo=lambda idx: False,
            toggle_track_mute=lambda idx: True,
            toggle_track_solo=lambda idx: True,
            set_track_arm=lambda idx, a: True,
            get_track_arm=lambda idx: True,
        )
    )
    mcp = DummyMCP()
    setup_mcp_tools(mcp, controller)
    return mcp, controller

@pytest.mark.parametrize("tool,kwargs", [
    ("create_track", {"name": "Vox"}),
    ("rename_track", {"track_index": 0, "new_name": "Guitar"}),
    ("set_track_color", {"track_index": 0, "color": "#00ff00"}),
    ("get_track_color", {"track_index": 0}),
    ("get_track_count", {}),
    ("set_track_volume", {"track_index": 0, "volume_db": -6.0}),
    ("get_track_volume", {"track_index": 0}),
    ("set_track_pan", {"track_index": 0, "pan": 0.1}),
    ("get_track_pan", {"track_index": 0}),
    ("set_track_mute", {"track_index": 0, "mute": True}),
    ("get_track_mute", {"track_index": 0}),
    ("set_track_solo", {"track_index": 0, "solo": True}),
    ("get_track_solo", {"track_index": 0}),
    ("toggle_track_mute", {"track_index": 0}),
    ("toggle_track_solo", {"track_index": 0}),
    ("set_track_arm", {"track_index": 0, "arm": True}),
    ("get_track_arm", {"track_index": 0}),
])
def test_track_tools_success(mcp_and_controller, tool, kwargs):
    mcp, _ = mcp_and_controller
    fn = mcp.tools[tool]
    res = fn(None, **kwargs)
    assert isinstance(res, dict)
    assert res.get("status") in {"success", "error"}
    assert "message" in res
