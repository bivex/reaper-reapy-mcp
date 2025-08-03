import reapy

try:
    reapy.connect()
    project = reapy.Project()
    print("Connected to project:", project.name)
    is_connected = reapy.is_connected()
except Exception as e:
    print(f"Connection verification failed: {e}")
