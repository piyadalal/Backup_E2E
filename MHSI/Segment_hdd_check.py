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

# Commands to find the highest dev and check files
commands = [
    "find " + BASE_DIR + " -maxdepth 1 -name 'dev_*' "
                         "| sort -r | head -n 1",
    "cd {dev_path}/part_0/FSN_DATA/mhsi_db",
    "ls -l",
    "watch -n 1 d=cumulative ls -l"
]

# Telnet connection function
def telnet_connect():
    try:
        tn = telnetlib.Telnet(HOST)

        # Log in
        tn.read_until(b"login: ")
        tn.write(USER.encode('ascii') + b"\n")
        tn.read_until(b"Password: ")
        tn.write(PASSWORD.encode('ascii') + b"\n")

        # Find the highest dev directory (dev_18 or dev_19)
        tn.write(commands[0].encode('ascii') + b"\n")
        time.sleep(1)  # Wait for the command to execute

        # Read the output to get the highest dev directory
        output = tn.read_very_eager().decode('ascii')
        dev_path = output.strip()  # Get the first result which should be the highest dev_XX directory

        if not dev_path:
            print("No dev_xx directory found.")
            tn.close()
            return

        print("Found highest dev directory: " + dev_path)

        # Navigate to the directory for segments
        tn.write("cd " + dev_path + MH_DB_FOLDER + "\n")
        time.sleep(1)  # Wait for the directory change

        # Execute ls -l and watch commands
        for command in commands[2:]:
            tn.write(command.encode('ascii') + b"\n")
            time.sleep(1)  # Adjust sleep time if needed

        # Read the output of the "ls -l" command
        output = tn.read_very_eager().decode('ascii')

        # Check if segment files 1-3 are present
        for prefix in TARGET_PREFIXES:
            if any(line.split()[-1].startswith(prefix) for line in output.splitlines()):
                print("File starting with '" + prefix + "' is available.")
            else:
                print("File starting with '" + prefix + "' not found.")

        # Close the connection after running Ctrl-C to stop the watch
        tn.write(b"\x03")  # Send Ctrl-C
        tn.write(b"exit\n")
        tn.close()

    except Exception as e:
        print("Failed to connect or execute commands: " + str(e))

if __name__ == "__main__":
    telnet_connect()
