
import google.auth
from google.auth.transport.requests import Request
from google.cloud import logging
from google.oauth2 import service_account

# Assuming you have a service account token (as a string)
service_account_token = '4fb3e26e6ba350846767213595b654e96ecbc826'

# Create credentials from the token
#credentials = google.auth.credentials.Credentials(service_account_token)
credentials = service_account.Credentials.from_service_account_file(service_account_token)

# Use the credentials to create a logging client
client = logging.Client(credentials=credentials, project='skyuk-de-pa-tds-int')


# Define the log filter (Modify this based on your log structure)
log_filter = """
resource.type="cloud_function"
severity>=INFO
jsonPayload.payload.source.serialNumber="6763A32629316702"
"""

# Example: Fetch and print logs
entries = client.list_entries()
for entry in entries:
    print('Log entry: {%s}'.format(entry))


# Fetch logs
def fetch_logs():
   for entry in client.list_entries(filter_=log_filter):
       print("Timestamp: {%s}".format(entry.timestamp))
       print("Log: {%s}".format(entry.payload))
       print("-" * 40)

if __name__ == "__main__":
   fetch_logs()