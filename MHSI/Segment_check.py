import telnetlib
import time

# Telnet connection details
HOST = "172.20.116.184"  # replace with the actual client IP
USER = "root"   # replace with the actual username
PASSWORD = ""  # replace with the actual password


# File prefix to check
TARGET_PREFIX = "events-segment0.db"

# Commands
commands = [
    "cd /tmp/sim_ram/mhsi_db",
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

        # Execute commands
        for command in commands:
            tn.write(command.encode('ascii') + b"\n")
            time.sleep(1)  # Adjust sleep time if needed to wait for the command to execute

        # Read the output of the "ls -l" command after the watch command
        output = tn.read_very_eager().decode('ascii')

        # Check if any file starts with the target prefix
        lines = output.splitlines()
        for line in lines:
            if TARGET_PREFIX in line:
                parts = line.split()  # assuming the filename is the last part of each line
                filename = parts[-1] if parts else ''
                if filename.startswith(TARGET_PREFIX):
                    print("File starting with '" + TARGET_PREFIX + "' is available: " + filename)
                    break
        else:
            print("No file starting with '" + TARGET_PREFIX + "' found.")

        # Close the connection
        tn.write(b"exit\n")
        tn.close()

    except Exception as e:
        print("Failed to connect or execute commands: " + str(e))

if __name__ == "__main__":
    telnet_connect()
