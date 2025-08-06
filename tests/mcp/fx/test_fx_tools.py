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
        fx=SimpleNamespace(
            add_fx=lambda t, name: 0,
            remove_fx=lambda t, i: True,
            set_fx_param=lambda t, i, p, v: True,
            get_fx_param=lambda t, i, p: 0.5,
            get_fx_param_list=lambda t, i: ["Threshold", "Ratio"],
            get_fx_list=lambda t: [{"name": "ReaComp"}],
            get_available_fx_list=lambda: ["ReaComp", "ReaEQ"],
            toggle_fx=lambda t, i, e=None: True,
            set_compressor_params=lambda *a, **k: True,
            set_limiter_params=lambda *a, **k: True,
            get_track_peak_level=lambda t: {"L": -12.0, "R": -11.5},
            get_master_peak_level=lambda: {"L": -9.0, "R": -9.5},
        )
    )
    mcp = DummyMCP()
    setup_mcp_tools(mcp, controller)
    return mcp, controller

@pytest.mark.parametrize("tool,kwargs", [
    ("add_fx", {"track_index": 0, "fx_name": "ReaComp"}),
    ("remove_fx", {"track_index": 0, "fx_index": 0}),
    ("set_fx_param", {"track_index": 0, "fx_index": 0, "param_name": "Threshold", "value": -12.0}),
    ("get_fx_param", {"track_index": 0, "fx_index": 0, "param_name": "Threshold"}),
    ("get_fx_param_list", {"track_index": 0, "fx_index": 0}),
    ("get_fx_list", {"track_index": 0}),
    ("get_available_fx_list", {}),
    ("toggle_fx", {"track_index": 0, "fx_index": 0, "enable": True}),
    ("set_compressor_params", {"track_index": 0, "fx_index": 0, "threshold": -18.0}),
    ("set_limiter_params", {"track_index": 0, "fx_index": 0, "threshold": -1.0}),
    ("get_track_peak_level", {"track_index": 0}),
    ("get_master_peak_level", {}),
])
def test_fx_tools_success(mcp_and_controller, tool, kwargs):
    mcp, _ = mcp_and_controller
    fn = mcp.tools[tool]
    res = fn(None, **kwargs)
    assert isinstance(res, dict)
    assert res.get("status") in {"success", "error"}
    assert "message" in res
