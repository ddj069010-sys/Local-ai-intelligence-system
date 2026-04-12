"""
System Monitor Tool (Autonomous)
- Extracts real-time CPU, RAM, and Disk metrics.
- Usage: Display local system health.
"""
import psutil
import platform
import os

def check_health():
    """Returns a formatted system health state."""
    cpu_usage = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # OS detail for context
    system = platform.system()
    release = platform.release()
    
    output = [
        "### [SYSTEM MONITOR DATA (REAL-TIME)]",
        f"OS: {system} {release}",
        f"CPU Load: {cpu_usage}%",
        f"Memory: {memory.percent}% used ({memory.available // (1024**2)}MB free)",
        f"Storage: {disk.percent}% used ({disk.free // (1024**3)}GB free)"
    ]
    
    return "\n".join(output)

if __name__ == "__main__":
    # The ToolRouter can pass arguments here if needed
    print(check_health())
