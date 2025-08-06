# CRUSH.md

Repository quick-reference for agentic coding.

Build/Run
- Start MCP server: uv run -m src.run_mcp_server  |  python -m src.run_mcp_server
- Enable REAPER reapy server (once per REAPER session): python reaper_side_enable_server.py

Tests
- Run all: pytest
- Run a file: pytest tests/controllers/test_track_operations.py
- Run a single test: pytest tests/controllers/test_track_operations.py::test_create_track
- MCP inspector (Windows): tests/test_mcp.bat

Lint/Format/Type
- Lint: flake8
- Format (Black, 88 cols): black .
- Check only: black --check .

Project Conventions
- Python ≥3.10; deps in pyproject.toml; tests use pytest.
- Imports: absolute within src (e.g., from src.controllers.track import track_controller). Avoid wildcard imports.
- Formatting: Black (88), Flake8 (ignore E203,W503), keep functions small (flake8 max-complexity=10).
- Types: Prefer typing for public/controller APIs; use typing.Optional/TypedDict/Protocol as needed; be explicit with return types.
- Naming: snake_case for functions/vars, PascalCase for classes, UPPER_SNAKE for constants.
- Errors: Raise ValueError/TypeError for bad inputs; catch external/reapy calls, return structured success/error objects from controllers; no secret logging.
- Controllers: Use facade src/reaper_controller.ReaperController to delegate to specialized controllers in src/controllers/*.
- Positions: Support time seconds and measure:beat strings where applicable (see README Key Concepts).
- Tests: Keep deterministic; mock REAPER state where needed; target smallest scope (unit over integration).

CI/Editor
- No Cursor/Copilot rule files found; if added later (.cursor/rules/, .cursorrules, .github/copilot-instructions.md), mirror their guidance here.
