# Start reapy server from within REAPER
# This must be run as a REAPER ReaScript

# Simple version that just sets external state to enable the server
RPR_SetExtState("reapy", "server_port", "2306", 1)
RPR_SetExtState("reapy", "distant_api_enabled", "1", 1)

# Show message
RPR_ShowMessageBox(
    "Reapy server configuration set!\n\nPort: 2306\nRestart REAPER for changes to take effect.",
    "Reapy Server",
    0,
)
