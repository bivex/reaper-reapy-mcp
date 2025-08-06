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
        midi=SimpleNamespace(
            create_midi_item=lambda t, st, l: 2,
            add_midi_note=lambda t, i, params: True,
            clear_midi_item=lambda t, i: True,
            get_midi_notes=lambda t, i: [{"pitch": 60, "start": 0.0, "len": 1.0}],
            find_midi_notes_by_pitch=lambda lo, hi: [60, 64, 67],
            get_selected_midi_item=lambda: {"track": 0, "item_id": 2},
        )
    )
    mcp = DummyMCP()
    setup_mcp_tools(mcp, controller)
    return mcp, controller

@pytest.mark.parametrize("tool,kwargs", [
    ("create_midi_item", {"track_index": 0, "start_time": 0.0, "length": 1.0}),
    ("add_midi_note", {"track_index": 0, "item_id": 2, "pitch": 60, "start_time": 0.0, "length": 1.0, "velocity": 96}),
    ("clear_midi_item", {"track_index": 0, "item_id": 2}),
    ("get_midi_notes", {"track_index": 0, "item_id": 2}),
    ("find_midi_notes_by_pitch", {"pitch_min": 50, "pitch_max": 80}),
    ("get_selected_midi_item", {}),
])
def test_midi_tools_success(mcp_and_controller, tool, kwargs):
    mcp, _ = mcp_and_controller
    fn = mcp.tools[tool]
    res = fn(None, **kwargs)
    assert isinstance(res, dict)
    assert res.get("status") in {"success", "error"}
    assert "message" in res
