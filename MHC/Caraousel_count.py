import telnetlib
import time

# Telnet connection details
HOST = "172.20.116.184"  # replace with the actual client IP
USER = "root"   # replace with the actual username
PASSWORD = ""

# Container file pattern to search for
CONTAINER_FILE_PATTERN = "ProgramImage_*.nsa"

# Base directory
BASE_DIR = "/mnt/nds/"
TARGET_DIR = "/part_0/FSN_DATA/mhc_syncApp/S_CacheSeedData/"

# Commands to find the highest dev directory and count files
commands = [
    "find " + BASE_DIR + " -maxdepth 1 -name 'dev_*' "
                         "| sort -r | head -n 1",  # Find highest dev
    "cd {dev_path}" + TARGET_DIR,  # Navigate to the target directory
    # Count container files
    "ls " + TARGET_DIR + " | grep '" + CONTAINER_FILE_PATTERN + "' | wc -l"  # Count matching container files
]

# Telnet connection function
def telnet_connect_and_count_files():
    try:
        tn = telnetlib.Telnet(HOST)

        # Log in
        tn.read_until(b"login: ")
        tn.write(USER.encode('ascii') + b"\n")
        tn.read_until(b"Password: ")
        tn.write(PASSWORD.encode('ascii') + b"\n")

        # Wait for the system to reboot (this can be handled in different ways)
        print("Waiting for system to reboot...")
        time.sleep(60)  # Adjust time to wait for the reboot to complete

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

        # Navigate to the directory for mhc_syncApp and S_CacheSeedData
        tn.write("cd " + dev_path + TARGET_DIR + "\n")
        time.sleep(1)  # Wait for the directory change

        # Count the container files
        count_command = "ls | grep '" + CONTAINER_FILE_PATTERN + "' | wc -l"
        tn.write(count_command.encode('ascii') + b"\n")
        time.sleep(1)  # Wait for the count command to execute

        # Read the output and print the count
        output = tn.read_very_eager().decode('ascii')
        count = output.strip()
        print("Number of container files present: " + count)

        # Close the connection
        tn.write(b"exit\n")
        tn.close()

    except Exception as e:
        print("Failed to connect or execute commands: " + str(e))

if __name__ == "__main__":
    telnet_connect_and_count_files()
