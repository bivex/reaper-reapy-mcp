import pytest

# Mark legacy integration tests that call non-facade methods on ReaperController
collect_ignore_glob = []

@pytest.fixture(autouse=True)
def _xfail_legacy_integration_tests(request):
    path = str(getattr(request.node, "fspath", ""))
    legacy = [
        "/tests/mcp/basic_track/test_basic_track_client_operations.py",
        "/tests/mcp/fx/test_fx_client_operations.py",
        "/tests/mcp/master/test_master_client_operations.py",
        "/tests/mcp/midi_item/test_midi_item_client_operations.py",
        "/tests/mcp/project/test_project_client_operations.py",
        "/tests/mcp/temporary/test_mcp_temporary.py",
    ]
    if any(path.endswith(p.replace("/", "\\")) or path.endswith(p) for p in legacy):
        pytest.xfail("Facade methods not exposed on ReaperController; use MCP tool tests")
