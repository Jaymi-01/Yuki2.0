import ctypes
import subprocess
from ctypes import wintypes

# Windows MEMORYSTATUSEX for ctypes
class MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ('dwLength', wintypes.DWORD),
        ('dwMemoryLoad', wintypes.DWORD),
        ('ullTotalPhys', ctypes.c_uint64),
        ('ullAvailPhys', ctypes.c_uint64),
        ('ullTotalPageFile', ctypes.c_uint64),
        ('ullAvailPageFile', ctypes.c_uint64),
        ('ullTotalVirtual', ctypes.c_uint64),
        ('ullAvailVirtual', ctypes.c_uint64),
        ('ullAvailExtendedVirtual', ctypes.c_uint64),
    ]

def get_ram_usage():
    try:
        stat = MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(stat)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
        return {
            'load_percent': stat.dwMemoryLoad,
            'total_gb': round(stat.ullTotalPhys / (1024**3), 1),
            'used_gb': round((stat.ullTotalPhys - stat.ullAvailPhys) / (1024**3), 1)
        }
    except Exception:
        return {'load_percent': 0, 'total_gb': 0, 'used_gb': 0}

def get_cpu_usage():
    try:
        cmd = 'powershell -Command "Get-CimInstance Win32_Processor | Select-Object -ExpandProperty LoadPercentage"'
        output = subprocess.check_output(cmd, shell=True).decode().strip()
        if output.isdigit():
            return int(output)
    except Exception:
        pass
    return 0

def get_active_window_title():
    try:
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        buff = ctypes.create_unicode_buffer(length + 1)
        ctypes.windll.user32.GetWindowTextW(hwnd, buff, length + 1)
        return buff.value if buff.value else "Desktop"
    except Exception:
        return "System"
