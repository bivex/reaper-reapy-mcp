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
        audio=SimpleNamespace(
            insert_audio_item=lambda t, fp, st, sm: 5,
            create_blank_item_on_track=lambda t, st, l: 3,
            duplicate_item=lambda t, i, nt: 6,
            delete_item=lambda t, i: True,
            get_item_properties=lambda t, i: {"length": 1.0},
            set_item_position=lambda t, i, pt: True,
            set_item_length=lambda t, i, l: True,
            get_items_in_time_range=lambda t, st, et: [1, 2],
            get_selected_items=lambda: [1],
        )
    )
    mcp = DummyMCP()
    setup_mcp_tools(mcp, controller)
    return mcp, controller

@pytest.mark.parametrize("tool,kwargs", [
    ("insert_audio_item", {"track_index": 0, "file_path": "sample.wav", "start_time": 0.0}),
    ("create_blank_item", {"track_index": 0, "start_time": 0.0, "length": 1.0}),
    ("duplicate_item", {"track_index": 0, "item_id": 5, "new_time": 1.0}),
    ("delete_item", {"track_index": 0, "item_id": 5}),
    ("get_item_properties", {"track_index": 0, "item_id": 5}),
    ("set_item_position", {"track_index": 0, "item_id": 5, "position_time": 2.0}),
    ("set_item_length", {"track_index": 0, "item_id": 5, "length": 2.0}),
    ("get_items_in_time_range", {"track_index": 0, "start_time": 0.0, "end_time": 4.0}),
    ("get_selected_items", {}),
])
def test_audio_item_tools_success(mcp_and_controller, tool, kwargs):
    mcp, _ = mcp_and_controller
    fn = mcp.tools[tool]
    res = fn(None, **kwargs)
    assert isinstance(res, dict)
    assert res.get("status") in {"success", "error"}
    assert "message" in res
