
from httpAPI import HTTPapi

stbIP = ''  # Define the stbIP variable
url = "as/system/status"
stbURL = "http://%s:9005/%s" % (stbIP, url)

# Make an HTTP POST request
response = HTTPapi.httpPost(stbURL)
print("HTTP POST Response:", response)

# Optionally, make a WebSocket request
ws_url = "ws://%s:9005/%s" % (stbIP, url)
ws_response = HTTPapi.getWSdata(ws_url)
print("WebSocket Response:", ws_response)
