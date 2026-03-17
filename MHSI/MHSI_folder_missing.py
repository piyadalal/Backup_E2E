
import telnetlib
import time

# Telnet connection details
HOST = "172.20.116.184"  # replace with the actual client IP
USER = "root"   # replace with the actual username
PASSWORD = ""

# File prefixes to check for Segment 1, 2, and 3
TARGET_PREFIXES = [
    "events-segment1.db",
    "events-segment2.db",
    "events-segment3.db"
]

# Base directory for search
BASE_DIR = "/mnt/nds/"
MH_DB_FOLDER = "/part_0/FSN_DATA/mhsi_db"

def find_highest_dev_dir(tn):
    find_cmd = f"find {BASE_DIR} -maxdepth 1 -name 'dev_*' | sort -r | head -n 1"
    tn.write(find_cmd.encode('ascii') + b"\n")
    time.sleep(1)
    output = tn.read_very_eager().decode('ascii').strip()
    return output

def check_mhsi_db_exists(tn, dev_path):
    check_cmd = f"test -d {dev_path}{MH_DB_FOLDER} && echo 'mhsi_db exists' || echo 'mhsi_db missing'"
    tn.write(check_cmd.encode('ascii') + b"\n")
    time.sleep(1)
    output = tn.read_very_eager().decode('ascii')
    return 'mhsi_db exists' in output

def check_segment_files(tn, dev_path):
    tn.write(f"cd {dev_path}{MH_DB_FOLDER}\n".encode('ascii'))
    time.sleep(1)
    tn.write(b"ls -l\n")
    time.sleep(1)
    output = tn.read_very_eager().decode('ascii')
    for prefix in TARGET_PREFIXES:
        found = any(line.split()[-1].startswith(prefix) for line in output.splitlines() if line)
        if found:
            print(f"File starting with '{prefix}' is available.")
        else:
            print(f"File starting with '{prefix}' not found.")

def telnet_connect():
    tn = None
    try:
        tn = telnetlib.Telnet(HOST)

        # Log in
        tn.read_until(b"login: ")
        tn.write(USER.encode('ascii') + b"\n")
        tn.read_until(b"Password: ")
        tn.write(PASSWORD.encode('ascii') + b"\n")

        # Find the highest dev directory
        dev_path = find_highest_dev_dir(tn)
        if not dev_path:
            print("No dev_xx directory found.")
            return
        print(f"Found highest dev directory: {dev_path}")

        # Check if mhsi_db exists
        if not check_mhsi_db_exists(tn, dev_path):
            print("The 'mhsi_db' folder is not present in the highest dev directory.")
            return
        print("The 'mhsi_db' folder exists. Proceeding with file checks.")

        # Check segment files
        check_segment_files(tn, dev_path)

        # Optionally run watch (not recommended in scripts, but kept for parity)
        tn.write(b"watch -n 1 d=cumulative ls -l\n")
        time.sleep(1)

        # Stop watch and exit
        tn.write(b"\x03")  # Send Ctrl-C
        tn.write(b"exit\n")
    except Exception as e:
        print(f"Failed to connect or execute commands: {e}")
    finally:
        if tn:
            tn.close()

if __name__ == "__main__":
    telnet_connect()
