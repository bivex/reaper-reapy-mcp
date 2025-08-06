import pytest

pytestmark = pytest.mark.xfail(reason="Facade methods not exposed on ReaperController; use MCP tools instead")
