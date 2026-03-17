import socket

def send_as_command(ip_stb, port):
    # Create a socket object
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # Connect to the STB on the specified port
        s.connect((ip_stb, port))
        print(f"Connected to {ip_stb}:{port}")

        # If the AS command is simply to open communication, we can send a dummy message.
        # Modify this if the command requires specific content
        message = "hello"  # Placeholder for actual AS command if needed
        s.send(message.encode('utf-8'))

        # Optionally receive any response from the STB
        response = s.recv(1024)
        print(f"Response from STB: {response.decode('utf-8')}")

    except socket.error as e:
        print(f"Failed to connect or send command: {e}")

    finally:
        # Close the socket
        s.close()

# Replace with your actual STB IP
ip_stb = '172.20.116.184'  # Example IP, replace with your STB's IP
port = 5800  # This is the port for VNC, replace with the relevant port

# Send the AS command
send_as_command(ip_stb, port)